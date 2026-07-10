"""festvox_core.py -- backend for the Festvox Speech Synthesis GUI.

Pure Python (no Qt) so every tricky part is unit-testable headless. This is
the glue between the GUI and the REAL synthesis engine:

    99_Tools/vocab_forge/synth_diphone.py

which renders concatenative diphone audio from the FestVox-style DBs built by
99_Tools/festvox/utau2festvox.py (dic/diphone_index.json + wav/). No Festival
binary is involved anywhere -- everything runs on plain Windows Python.

Responsibilities:
  * import synth_diphone.py by path (configurable, auto-discovered)
  * read festvox.json (the toolchain config) for voices / defaults
  * GUI config.json load/save (deep-merged over defaults)
  * DiphoneBackend: text -> audio + REAL per-phone segments; phone-list
    re-render (for phoneme overrides typed in the GUI)
  * velocity envelope -> gain application
  * time-stretch DSP for boundary drags (librosa if present, else a numpy
    phase vocoder; `hook` is the seam for swapping in rubberband/SoX/...)
  * WAV / project IO
"""
from __future__ import annotations
import importlib.util
import json
import os
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

import numpy as np

GUI_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------- config
DEFAULT_CONFIG = {
    # path to the toolchain's festvox.json; "" = auto-discover (cwd, next to
    # synth_diphone.py, 99_Tools/festvox/) exactly like synth_diphone's CLI
    "festvox_config": "",
    # folder containing synth_diphone.py; "" = auto (../../vocab_forge)
    "synth_diphone_dir": "",
    # UI label -> synth_diphone language code
    "languages": {"Asaxi": "asaxi", "English": "en", "Japanese": "ja"},
    "default_language": "Asaxi",
    "default_text": "asaxi",
    # extra voicebank DB dirs added from the GUI: name -> path
    # (each must contain dic/diphone_index.json)
    "extra_voicebanks": {},
    "synth_speed": 1.0,
    # real synth_diphone knobs (module constants, applied per render)
    "advanced": {"crossfade_ms": 15.0, "edge_fade_ms": 8.0, "half_ms": 150.0},
    # velocity envelope -> gain on play/export
    "apply_velocity": True,
    "velocity_depth": 1.0,
}


def _deep_merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config(path: str = "config.json") -> dict:
    """config.json merged over DEFAULT_CONFIG. Missing file -> defaults.
    Legacy keys from the old Festival-based GUI are dropped silently."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return cfg
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"config.json is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise ValueError("config.json must contain a JSON object")
    for legacy in ("festival", "voicebanks", "samplerate"):
        data.pop(legacy, None)
    if isinstance(data.get("languages"), list):   # legacy list form
        data.pop("languages")
    _deep_merge(cfg, data)
    if not cfg.get("languages"):
        raise ValueError("config.json: 'languages' must be a non-empty "
                         "{label: code} object")
    return cfg


def save_config(cfg: dict, path: str) -> None:
    out = {k: cfg[k] for k in DEFAULT_CONFIG if k in cfg}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------- data
@dataclass
class Segment:
    phone: str
    start: float
    end: float

    @property
    def dur(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class Synthesis:
    samples: np.ndarray            # float32 mono, [-1, 1]
    sr: int
    segments: List[Segment] = field(default_factory=list)
    text: str = ""
    lang: str = ""                 # synth_diphone code: asaxi / en / ja
    voicebank: str = ""
    phones: List[str] = field(default_factory=list)
    diphones: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    warning: Optional[str] = None

    @property
    def duration(self) -> float:
        return len(self.samples) / float(self.sr) if self.sr else 0.0


class BackendError(RuntimeError):
    """Raised with a user-actionable message (shown in a dialog)."""


# ---------------------------------------------------------------------- WAV IO
def read_wav(path: str):
    with wave.open(path, "rb") as w:
        sr, n, ch, sw = (w.getframerate(), w.getnframes(),
                         w.getnchannels(), w.getsampwidth())
        raw = w.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sw == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sw} bytes")
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return data.astype(np.float32), sr


def wav_bytes_to_samples(data: bytes):
    """Decode in-memory 16-bit WAV bytes (synth_diphone output) -> float32."""
    import io
    with wave.open(io.BytesIO(data), "rb") as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
    return (np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0), sr


def samples_to_wav_bytes(samples: np.ndarray, sr: int) -> bytes:
    import io
    s = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes((s * 32767.0).astype("<i2").tobytes())
    return buf.getvalue()


def write_wav(path: str, samples: np.ndarray, sr: int) -> None:
    with open(path, "wb") as f:
        f.write(samples_to_wav_bytes(samples, sr))


# ------------------------------------------------------------------------ DSP
def time_stretch(samples: np.ndarray, sr: int, factor: float,
                 hook: Optional[Callable] = None) -> np.ndarray:
    """Stretch audio in time by `factor` (>1 = longer/slower, <1 = shorter),
    preserving pitch. `hook(samples, sr, factor)` overrides the algorithm --
    this is the clean DSP seam to swap in rubberband/SoX/etc."""
    x = np.asarray(samples, dtype=np.float32)
    factor = float(factor)
    if hook is not None:
        return np.asarray(hook(x, sr, factor), dtype=np.float32)
    if x.size < 32 or abs(factor - 1.0) < 1e-3:
        return x
    factor = float(np.clip(factor, 0.25, 4.0))
    try:
        import librosa  # optional, higher quality
        return librosa.effects.time_stretch(x, rate=1.0 / factor).astype(np.float32)
    except Exception:
        return _phase_vocoder(x, factor)


def _phase_vocoder(x: np.ndarray, factor: float, n_fft: int = 1024,
                   hop: int = 256) -> np.ndarray:
    """Compact pitch-preserving phase vocoder. Returns ~factor*len(x) samples."""
    win = np.hanning(n_fft).astype(np.float64)
    xp = np.concatenate([np.zeros(n_fft), x.astype(np.float64), np.zeros(n_fft)])
    n_frames = 1 + (len(xp) - n_fft) // hop
    S = np.empty((n_fft // 2 + 1, n_frames), dtype=np.complex128)
    for i in range(n_frames):
        S[:, i] = np.fft.rfft(win * xp[i * hop:i * hop + n_fft])
    mag, ph = np.abs(S), np.angle(S)
    omega = 2.0 * np.pi * hop * np.arange(n_fft // 2 + 1) / n_fft
    steps = np.arange(0, n_frames - 1, 1.0 / factor)
    out = np.zeros((n_fft // 2 + 1, len(steps)), dtype=np.complex128)
    acc = ph[:, 0].copy()
    for j, t in enumerate(steps):
        i = int(np.floor(t)); frac = t - i
        i2 = min(i + 1, n_frames - 1)
        m = (1.0 - frac) * mag[:, i] + frac * mag[:, i2]
        out[:, j] = m * np.exp(1j * acc)
        dphi = ph[:, i2] - ph[:, i] - omega
        dphi = dphi - 2.0 * np.pi * np.round(dphi / (2.0 * np.pi))
        acc = acc + omega + dphi
    y = np.zeros(len(steps) * hop + n_fft)
    wsum = np.zeros_like(y)
    for j in range(out.shape[1]):
        frame = np.real(np.fft.irfft(out[:, j])) * win
        y[j * hop:j * hop + n_fft] += frame
        wsum[j * hop:j * hop + n_fft] += win ** 2
    wsum[wsum < 1e-6] = 1e-6
    y = (y / wsum)[n_fft:-n_fft] if len(y) > 2 * n_fft else y
    peak = float(np.max(np.abs(y))) or 1.0
    return (y / peak * 0.97).astype(np.float32)


def apply_velocity(samples: np.ndarray, sr: int, nodes, depth: float = 1.0
                   ) -> np.ndarray:
    """Apply the velocity envelope as a time-varying gain.
    nodes: [(t_seconds, v)] with v in [0,1]; v=0.5 is unity gain,
    v=1.0 -> (1+depth)x, v=0.0 -> (1-depth)x. Linear interp between nodes."""
    x = np.asarray(samples, dtype=np.float32)
    if x.size == 0 or not nodes:
        return x
    pts = sorted((float(t), float(v)) for t, v in nodes)
    ts = np.array([p[0] for p in pts])
    vs = np.array([p[1] for p in pts])
    t_axis = np.arange(len(x)) / float(sr)
    v = np.interp(t_axis, ts, vs, left=vs[0], right=vs[-1])
    gain = np.maximum(0.0, 1.0 + float(depth) * (2.0 * v - 1.0))
    return np.clip(x * gain, -1.0, 1.0).astype(np.float32)


# ------------------------------------------------- synth_diphone import glue
_SD = None
_SD_PATH = None


def import_synth_diphone(cfg: dict):
    """Import synth_diphone.py by file path. Search order: config key
    'synth_diphone_dir', then the GUI folder itself, then ../../vocab_forge."""
    global _SD, _SD_PATH
    here = Path(GUI_DIR)
    cands = []
    if cfg.get("synth_diphone_dir"):
        cands.append(Path(cfg["synth_diphone_dir"]))
    cands += [here, here.parent,
              here.parent.parent / "vocab_forge",          # 99_Tools/vocab_forge
              here.parent.parent.parent / "vocab_forge"]
    for d in cands:
        p = Path(d) / "synth_diphone.py"
        if p.is_file():
            if _SD is not None and _SD_PATH == str(p):
                return _SD
            spec = importlib.util.spec_from_file_location("synth_diphone", str(p))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["synth_diphone"] = mod   # so its own imports resolve
            spec.loader.exec_module(mod)
            _SD, _SD_PATH = mod, str(p)
            return mod
    raise BackendError(
        "synth_diphone.py not found.\n\nLooked in:\n  " +
        "\n  ".join(str(Path(d)) for d in cands) +
        "\n\nSet \"synth_diphone_dir\" in the GUI's config.json (or via "
        "Options > Locate synth_diphone.py...) to the folder that contains it "
        "(normally 99_Tools/vocab_forge).")


# ------------------------------------------------------------- diphone backend
class DiphoneBackend:
    """Drives synth_diphone.py: voice inventory from festvox.json, text or
    phone-list synthesis with real per-phone segment timing."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.sd = import_synth_diphone(cfg)
        self.fcfg: dict = {}
        self.fcfg_path: Optional[str] = None
        self._dbs = {}                          # voicebank name -> DiphoneDB
        self.reload_festvox_config()

    # -- festvox.json ---------------------------------------------------------
    def reload_festvox_config(self):
        self._dbs.clear()
        explicit = self.cfg.get("festvox_config") or None
        p = self.sd._find_festvox_config(explicit)
        self.fcfg, self.fcfg_path = {}, None
        if p:
            try:
                self.fcfg = json.loads(Path(p).read_text(encoding="utf-8"))
                self.fcfg_path = str(p)
            except (OSError, json.JSONDecodeError) as e:
                raise BackendError(f"festvox.json unreadable ({p}):\n{e}")

    # -- voice inventory ------------------------------------------------------
    def _voice_dir(self, name: str) -> Optional[Path]:
        voices = self.fcfg.get("voices") or {}
        if name in voices:
            d, _ = self.sd._db_from_config(self.fcfg, name)
            return d
        extra = self.cfg.get("extra_voicebanks") or {}
        if name in extra:
            return Path(extra[name])
        return None

    def voicebanks(self) -> List[dict]:
        """[{name, dir, ok, source}] from festvox.json voices + GUI extras."""
        out, seen = [], set()
        for name in (self.fcfg.get("voices") or {}):
            d = self._voice_dir(name)
            out.append(self._vb_info(name, d, "festvox.json"))
            seen.add(name)
        for name, d in (self.cfg.get("extra_voicebanks") or {}).items():
            if name not in seen:
                out.append(self._vb_info(name, Path(d), "config.json"))
        return out

    @staticmethod
    def _vb_info(name, d, source) -> dict:
        ok = bool(d) and (Path(d) / "dic" / "diphone_index.json").is_file()
        return {"name": name, "dir": str(d) if d else "", "ok": ok,
                "source": source}

    def default_voicebank(self) -> Optional[str]:
        vbs = self.voicebanks()
        want = self.fcfg.get("default_voice")
        for v in vbs:
            if v["name"] == want and v["ok"]:
                return want
        for v in vbs:
            if v["ok"]:
                return v["name"]
        return vbs[0]["name"] if vbs else None

    def add_voicebank_dir(self, path: str) -> str:
        """Register a DB folder chosen in the GUI. Returns its name."""
        p = Path(path)
        if not (p / "dic" / "diphone_index.json").is_file():
            raise BackendError(
                f"Not a diphone DB:\n{p}\n\nExpected dic/diphone_index.json "
                "inside (a folder built by utau2festvox.py).")
        name = p.name or "voicebank"
        self.cfg.setdefault("extra_voicebanks", {})[name] = str(p)
        return name

    def db(self, voicebank: str):
        if voicebank not in self._dbs:
            d = self._voice_dir(voicebank)
            if not d or not (Path(d) / "dic" / "diphone_index.json").is_file():
                raise BackendError(
                    f"Voicebank '{voicebank}' has no diphone DB at:\n"
                    f"  {d or '(no path)'}\n\n"
                    "Fix the path in festvox.json (voices/output_root), or use "
                    "Voicebank > Add voicebank folder... to point at a DB built "
                    "by utau2festvox.py.")
            self._dbs[voicebank] = self.sd.DiphoneDB(Path(d))
        return self._dbs[voicebank]

    def db_size(self, voicebank: str) -> int:
        try:
            return len(self.db(voicebank).index)
        except Exception:
            return 0

    # -- g2p ------------------------------------------------------------------
    def g2p(self, text: str, lang: str) -> List[str]:
        try:
            if lang == "en":
                return self.sd.g2p_english(text)
            if lang in ("ja", "jp"):
                return self.sd.g2p_japanese(text)
            return self.sd.g2p_asaxi(text)
        except (RuntimeError, ValueError) as e:
            raise BackendError(str(e))

    # -- synthesis ------------------------------------------------------------
    def synth(self, text: str, lang: str, voicebank: str,
              speed: float = 1.0) -> Synthesis:
        if not text or not text.strip():
            raise BackendError("No text to synthesize.")
        phones = self.g2p(text, lang)
        if not phones:
            raise BackendError(
                f"No phonemes derived from {text!r} for language '{lang}'.")
        return self.synth_phones(phones, voicebank, speed, text=text, lang=lang)

    def synth_phones(self, phones: List[str], voicebank: str,
                     speed: float = 1.0, text: str = "",
                     lang: str = "") -> Synthesis:
        """Render an explicit phone list -- the path used when the user edits
        the phoneme fields (e.g. overrides 'r' to 'rr') and re-renders."""
        phones = [str(p).strip() for p in phones if str(p).strip()]
        # strip EDGE paus only (render() adds its own); interior "pau" is a
        # legitimate user-inserted pause if the bank has x-pau / pau-y units
        while phones and phones[0] == "pau":
            phones.pop(0)
        while phones and phones[-1] == "pau":
            phones.pop()
        if not phones:
            raise BackendError("Phone list is empty.")
        db = self.db(voicebank)
        adv = self.cfg.get("advanced") or {}
        self.sd.CROSSFADE_MS = float(adv.get("crossfade_ms", 15.0))
        self.sd.EDGE_FADE_MS = float(adv.get("edge_fade_ms", 8.0))
        self.sd.HALF_MS = float(adv.get("half_ms", 150.0))
        try:
            r = self.sd.render(db, phones, speed=speed)
        except ValueError as e:
            raise BackendError(
                f"{e}\n\nThe voicebank has none of the needed diphones. "
                "Check the phoneme spelling against the bank's phone set.")
        samples, sr = wav_bytes_to_samples(r["wav"])
        segs = [Segment(s["phone"], s["start"], s["end"])
                for s in r.get("segments", [])]
        warn = None
        if r["skipped"]:
            warn = ("missing diphones skipped: " + ", ".join(r["skipped"]))
        return Synthesis(samples, sr, segs, text=text, lang=lang,
                         voicebank=voicebank, phones=list(r["phones"]),
                         diphones=list(r["diphones"]),
                         skipped=list(r["skipped"]), warning=warn)

    def synth_output_dir(self) -> str:
        return str(self.fcfg.get("synth_output_dir") or "")

    def default_speed(self) -> float:
        try:
            return float(self.cfg.get("synth_speed")
                         or self.fcfg.get("synth_speed", 1.0))
        except (TypeError, ValueError):
            return 1.0

    def default_lang_code(self) -> str:
        return str(self.fcfg.get("default_lang") or "asaxi")


# ------------------------------------------------------------------- project io
def save_project(path: str, *, text: str, language: str, lang_code: str,
                 voicebank: str, speed: float, segments: List[Segment],
                 phones: List[str], velocity) -> None:
    data = {
        "text": text, "language": language, "lang_code": lang_code,
        "voicebank": voicebank, "speed": float(speed),
        "phones": list(phones),
        "segments": [{"phone": s.phone, "start": s.start, "end": s.end}
                     for s in segments],
        "velocity": [[float(t), float(v)] for t, v in velocity],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_project(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["segments"] = [Segment(s["phone"], s["start"], s["end"])
                        for s in data.get("segments", [])]
    return data
# end of festvox_core
