"""festvox_core.py -- backend for the Festvox Speech Synthesis GUI.

Pure Python (no Qt) so every tricky part is unit-testable headless:
  * config.json loading (+ deep-merge over sane defaults)
  * REAL Festival synthesis via subprocess, with phoneme-segment extraction
  * graceful demo fallback (synthetic speech-like audio) when Festival is
    absent or errors, so the GUI is always interactive
  * time-stretch DSP (librosa if available, else a numpy phase vocoder)
  * WAV read/write and project save/load
"""
from __future__ import annotations
import glob, json, os, re, shutil, subprocess, tempfile
import wave
from dataclasses import dataclass, field
from typing import List, Optional, Callable

import numpy as np

# --------------------------------------------------------------------- config
DEFAULT_CONFIG = {
    "languages": ["American English", "Mexican Spanish", "Japanese", "Custom JSON"],
    "voicebanks": ["awb_arctic", "kal_diphone", "n_voicebank_custom"],
    "festival": {
        "bin": "festival",
        "voice_map": {
            "awb_arctic": "voice_cmu_us_awb_arctic_clunits",
            "kal_diphone": "voice_kal_diphone",
            "n_voicebank_custom": "voice_kal_diphone",
        },
    },
    "default_text": "Hello, world.",
    "samplerate": 16000,
}


def _deep_merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config(path: str = "config.json") -> dict:
    """Load config.json merged over DEFAULT_CONFIG. Missing file -> defaults."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(path, "r", encoding="utf-8") as f:
            _deep_merge(cfg, json.load(f))
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"config.json is not valid JSON: {e}")
    if not cfg.get("languages") or not cfg.get("voicebanks"):
        raise ValueError("config.json must define non-empty 'languages' and 'voicebanks'")
    return cfg


def write_sample_config(path: str = "config.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)


def save_config(cfg: dict, path: str = "config.json") -> None:
    """Persist the public config keys (voicebanks, voice map, festival bin, ...)."""
    keys = ("languages", "voicebanks", "festival", "default_text", "samplerate")
    out = {k: cfg[k] for k in keys if k in cfg}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


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
    voicebank: str = ""
    warning: Optional[str] = None  # set when we fell back to demo audio

    @property
    def duration(self) -> float:
        return len(self.samples) / float(self.sr) if self.sr else 0.0


# ---------------------------------------------------------------------- WAV IO
def read_wav(path: str):
    with wave.open(path, "rb") as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
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


def write_wav(path: str, samples: np.ndarray, sr: int) -> None:
    s = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    pcm = (s * 32767.0).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm)


# ------------------------------------------------------------------------ DSP
def time_stretch(samples: np.ndarray, sr: int, factor: float,
                 hook: Optional[Callable] = None) -> np.ndarray:
    """Stretch audio in time by `factor` (>1 = longer/slower, <1 = shorter),
    preserving pitch. `hook(samples, sr, factor)` overrides the algorithm --
    this is the clean DSP seam to swap in rubberband/SoX/etc.
    """
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


def _phase_vocoder(x: np.ndarray, factor: float, n_fft: int = 1024, hop: int = 256) -> np.ndarray:
    """Compact pitch-preserving phase vocoder. Returns ~factor*len(x) samples."""
    win = np.hanning(n_fft).astype(np.float64)
    xp = np.concatenate([np.zeros(n_fft), x.astype(np.float64), np.zeros(n_fft)])
    n_frames = 1 + (len(xp) - n_fft) // hop
    S = np.empty((n_fft // 2 + 1, n_frames), dtype=np.complex128)
    for i in range(n_frames):
        S[:, i] = np.fft.rfft(win * xp[i * hop:i * hop + n_fft])
    mag, ph = np.abs(S), np.angle(S)
    omega = 2.0 * np.pi * hop * np.arange(n_fft // 2 + 1) / n_fft  # expected phase adv/bin
    steps = np.arange(0, n_frames - 1, 1.0 / factor)  # >1 factor -> more frames -> longer
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


# ------------------------------------------------------------- Festival backend
class FestivalBackend:
    """Wraps the `festival` CLI. Synthesises text -> (wav, phoneme segments).
    Falls back to a synthetic demo so the UI works without Festival installed.
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        fest = cfg.get("festival", {})
        self.bin = fest.get("bin", "festival")
        self.voice_map = fest.get("voice_map", {})
        self.sr = int(cfg.get("samplerate", 16000))

    def available(self) -> bool:
        return shutil.which(self.bin) is not None

    # -- voice resolution ----------------------------------------------------
    @staticmethod
    def _guess_voice_fn(name: str) -> str:
        name = str(name).strip()
        return name if name.startswith("voice_") else "voice_" + name

    def _voice_entry(self, voicebank: str) -> dict:
        """Normalize a voicebank name into {voice, dir, scm}.
        voice_map values may be a Festival function name (str) or a dict
        {"dir": "/path/to/voice", "voice": "voice_fn", "scm": "festvox/x.scm"}."""
        v = self.voice_map.get(voicebank)
        if isinstance(v, dict):
            return {"voice": v.get("voice") or self._guess_voice_fn(voicebank),
                    "dir": v.get("dir"), "scm": v.get("scm")}
        if isinstance(v, str) and v.strip():
            return {"voice": v.strip(), "dir": None, "scm": None}
        return {"voice": self._guess_voice_fn(voicebank), "dir": None, "scm": None}

    @staticmethod
    def _voice_preamble(entry: dict) -> str:
        """Scheme run before the voice call: put a directory voice on load-path
        and load its .scm so voices that aren't installed system-wide resolve."""
        d = entry.get("dir")
        if not d:
            return ""
        d = d.replace("\\", "/").rstrip("/")
        lines = ['(set! load-path (cons "%s/festvox" load-path))' % d,
                 '(set! load-path (cons "%s" load-path))' % d]
        scm = entry.get("scm")
        if scm:
            scm_path = scm if os.path.isabs(scm) else os.path.join(d, scm)
            lines.append('(load "%s")' % scm_path.replace("\\", "/"))
        return "\n".join(lines)

    def list_installed_voices(self) -> list:
        """Ask Festival for the voices it knows about: (voice.list)."""
        if not self.available():
            return []
        scm_path = tempfile.mktemp(suffix=".scm")
        try:
            with open(scm_path, "w", encoding="utf-8") as f:
                f.write("(print (voice.list))\n")
            proc = subprocess.run([self.bin, "-b", scm_path],
                                  capture_output=True, text=True, timeout=60)
            m = re.search(r"\(([^()]*)\)", proc.stdout or "")
            if not m:
                return []
            return [tok.strip() for tok in m.group(1).split() if tok.strip()]
        except Exception:
            return []
        finally:
            try:
                os.remove(scm_path)
            except OSError:
                pass

    def scan_voice_dir(self, path: str) -> dict:
        """Inspect a festvox/Multisyn voice folder -> {name, dir, voice, scm}."""
        path = os.path.abspath(path)
        fx = os.path.join(path, "festvox")
        search = fx if os.path.isdir(fx) else path
        voice_fn, scm_rel = None, None
        for scm in sorted(glob.glob(os.path.join(search, "*.scm"))):
            try:
                txt = open(scm, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            m = re.search(r"\(define\s+\(\s*(voice_[A-Za-z0-9_]+)", txt)
            if not m:
                m = re.search(r"proclaim_voice\s+'?([A-Za-z0-9_]+)", txt)
            if m:
                g = m.group(1)
                voice_fn = g if g.startswith("voice_") else "voice_" + g
                scm_rel = os.path.relpath(scm, path)
                break
        name = os.path.basename(path.rstrip("/\\")) or "voice"
        return {"name": name, "dir": path,
                "voice": voice_fn or self._guess_voice_fn(name), "scm": scm_rel}

    def synth(self, text: str, voicebank: str, speed: float = 1.0) -> Synthesis:
        if not text or not text.strip():
            raise ValueError("No text to synthesize.")
        speed = float(speed) if speed else 1.0
        if self.available():
            try:
                return self._festival_synth(text, voicebank, speed)
            except Exception as e:
                syn = self.demo_synth(text, voicebank, speed)
                syn.warning = f"Festival call failed ({e}); showing demo audio."
                return syn
        syn = self.demo_synth(text, voicebank, speed)
        syn.warning = "Festival not found on PATH; showing demo audio."
        return syn

    # -- real Festival -------------------------------------------------------
    def _festival_synth(self, text: str, voicebank: str, speed: float) -> Synthesis:
        entry = self._voice_entry(voicebank)
        preamble = self._voice_preamble(entry)
        wav_path = tempfile.mktemp(suffix=".wav")
        seg_path = tempfile.mktemp(suffix=".seg")
        scm_path = tempfile.mktemp(suffix=".scm")
        esc = text.replace("\\", "\\\\").replace('"', '\\"')
        dur_stretch = 1.0 / speed if speed else 1.0
        scheme = (
            (preamble + "\n" if preamble else "")
            + f"({entry['voice']})\n"
            + f"(Parameter.set 'Duration_Stretch {dur_stretch:.4f})\n"
            + f'(set! u (SynthText "{esc}"))\n'
            + f'(utt.save.wave u "{wav_path}")\n'
            + f'(utt.save.segs u "{seg_path}")\n'
        )
        try:
            with open(scm_path, "w", encoding="utf-8") as f:
                f.write(scheme)
            proc = subprocess.run([self.bin, "-b", scm_path],
                                  capture_output=True, text=True, timeout=120)
            if not os.path.exists(wav_path):
                raise RuntimeError((proc.stderr or proc.stdout or "no output").strip()[:300])
            samples, sr = read_wav(wav_path)
            segs = self._parse_segs(seg_path) if os.path.exists(seg_path) else []
            if not segs:
                segs = self._even_segments(text, len(samples) / sr)
            return Synthesis(samples, sr, segs, text=text, voicebank=voicebank)
        finally:
            for p in (wav_path, seg_path, scm_path):
                try:
                    os.remove(p)
                except OSError:
                    pass

    @staticmethod
    def _parse_segs(path: str) -> List[Segment]:
        """Parse a Festival/Xwaves label file (from utt.save.segs)."""
        segs: List[Segment] = []
        prev = 0.0
        started = False
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not started:
                    if line.strip() == "#":
                        started = True
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    end = float(parts[0])
                except ValueError:
                    continue
                phone = parts[-1]
                segs.append(Segment(phone, prev, end))
                prev = end
        return segs

    # -- demo fallback -------------------------------------------------------
    def demo_synth(self, text: str, voicebank: str, speed: float = 1.0) -> Synthesis:
        """Synthetic 'speech-like' audio: one segment per alnum char, vowels as
        formant tones, consonants as shaped noise. Enough to drive the editor."""
        sr = self.sr
        rng = np.random.default_rng(abs(hash((text, voicebank))) % (2 ** 32))
        toks = [c for c in text.lower() if c.isalnum()][:48] or ["a"]
        vowels = set("aeiouy")
        seg_objs: List[Segment] = []
        chunks: List[np.ndarray] = []
        t = 0.0
        for c in toks:
            dur = (0.13 if c in vowels else 0.07) / (speed if speed else 1.0)
            n = max(8, int(dur * sr))
            tt = np.arange(n) / sr
            env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.6
            if c in vowels:
                f0 = 110.0 + 12.0 * (ord(c) % 7)
                sig = sum(np.sin(2 * np.pi * f0 * k * tt) / k for k in (1, 2, 3, 4))
                f1 = 500 + 150 * (ord(c) % 5)
                sig += 0.5 * np.sin(2 * np.pi * f1 * tt)
            else:
                sig = rng.standard_normal(n)
                if len(sig) > 4:  # crude low-pass so it isn't pure hiss
                    sig = np.convolve(sig, np.ones(4) / 4, mode="same")
            chunk = (sig * env).astype(np.float32)
            peak = float(np.max(np.abs(chunk))) or 1.0
            chunk = chunk / peak * 0.6
            chunks.append(chunk)
            seg_objs.append(Segment(c.upper(), t, t + n / sr))
            t += n / sr
        samples = np.concatenate(chunks).astype(np.float32)
        return Synthesis(samples, sr, seg_objs, text=text, voicebank=voicebank)

    @staticmethod
    def _even_segments(text: str, duration: float) -> List[Segment]:
        toks = [c for c in text.lower() if c.isalnum()][:48] or ["a"]
        step = duration / len(toks)
        return [Segment(c.upper(), i * step, (i + 1) * step) for i, c in enumerate(toks)]


# ------------------------------------------------------------------- project io
def save_project(path: str, *, text: str, language: str, voicebank: str,
                 speed: float, segments: List[Segment], velocity) -> None:
    data = {
        "text": text, "language": language, "voicebank": voicebank, "speed": speed,
        "segments": [{"phone": s.phone, "start": s.start, "end": s.end} for s in segments],
        "velocity": [[float(t), float(v)] for t, v in velocity],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_project(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["segments"] = [Segment(s["phone"], s["start"], s["end"]) for s in data.get("segments", [])]
    return data
