# -*- coding: utf-8 -*-
"""
synth_diphone.py — concatenative diphone synthesis for vocab_forge.

Renders audio from the FestVox-style diphone database produced by
99_Tools/festvox/utau2festvox.py (dic/diphone_index.json + wav/), using the
Lem 4_Fis3 voice. Pure standard library (wave + array); no Festival runtime
needed — the same index the Festival stub loads drives this renderer.

Two front ends share the voice:
  * Asaxi:   grapheme→phone rules derived from
             "00_Phonemes of the Asaxi Language" (romanization → arpasing).
  * English: CMU dictionary lookup (pip install cmudict), stress stripped —
             the bank is arpasing, i.e. lowercase ARPAbet, so English "just
             works" for testing.

DB discovery: config.json key "festvox_db" — a path or list of candidate
paths; the first one containing dic/diphone_index.json wins.
"""
import array
import json
import re
import wave
from pathlib import Path

CROSSFADE_MS = 15          # equal-power join at each diphone seam
EDGE_FADE_MS = 8           # de-click fade at utterance edges
HALF_MS = 150              # max audio kept on each side of the phone
                           # boundary (mid) — trims the recordings' long
                           # vowel sustains to conversational phone lengths

# ------------------------------------------------------------------ database

class DiphoneDB:
    def __init__(self, root: Path):
        self.root = Path(root)
        meta = json.loads((self.root / "dic" / "diphone_index.json")
                          .read_text(encoding="utf-8"))
        self.index = meta["index"]          # name -> [wav, start, mid, end]
        self._cache = {}                    # wav name -> (params, frames)

    def has(self, dip):
        return dip in self.index

    def slice(self, dip, half_ms=HALF_MS):
        """Return (framerate, mono int16 array) for a diphone. `half_ms` caps
        how much audio is kept each side of the phone boundary — smaller =
        shorter phones = faster speech (see `speed` in render())."""
        wav_name, start, mid, end = self.index[dip]
        if wav_name not in self._cache:
            with wave.open(str(self.root / "wav" / wav_name), "rb") as w:
                assert w.getsampwidth() == 2, "expected 16-bit wavs"
                frames = array.array("h")
                frames.frombytes(w.readframes(w.getnframes()))
                if w.getnchannels() == 2:   # downmix, just in case
                    frames = array.array("h", [(frames[i] + frames[i+1]) // 2
                                               for i in range(0, len(frames), 2)])
                self._cache[wav_name] = (w.getframerate(), frames)
        fr, frames = self._cache[wav_name]
        half = half_ms / 1000.0
        s = max(start, mid - half)
        e = min(end, mid + half)
        return fr, frames[int(s * fr):int(e * fr)]


def find_db(cfg) -> Path:
    cands = cfg.get("festvox_db") or []
    if isinstance(cands, str):
        cands = [cands]
    for c in cands:
        p = Path(c)
        if (p / "dic" / "diphone_index.json").exists():
            return p
    raise FileNotFoundError(
        "No diphone DB found. Set \"festvox_db\" in config.json to the "
        "festvox_db folder built by 99_Tools/festvox/utau2festvox.py "
        f"(tried: {cands or 'nothing'})")

# ------------------------------------------------------------- Asaxi g2p

# Romanization → bank phones, longest match first. From the phoneme chart
# (Arpa column) in 00_Phonemes of the Asaxi Language.
_ASAXI_RULES = [
    # trigraphs / digraphs
    ("nŋ", ["nng"]), ("nn", ["nn"]), ("mm", ["mm"]),
    ("ch", ["ch"]), ("sh", ["sh"]), ("dh", ["dh"]), ("jh", ["jh"]),
    ("zh", ["zh"]), ("th", ["th"]), ("dz", ["dz"]),
    ("si", ["sh", "i"]),           # ś may be written "si" (chart)
    ("ni", ["ny", "i"]),           # n+i palatalizes (chart: nasal shift)
    # single letters — vowels
    ("å", ["aw"]), ("ă", ["ay"]), ("ë", ["ey"]), ("ỏ", ["ow"]),
    ("ő", ["oy"]), ("ů", ["uw"]), ("è", ["ax"]), ("ě", ["er"]),
    ("ý", ["ih"]), ("ù", ["u"]), ("á", ["ao"]),
    ("a", ["a"]), ("e", ["e"]), ("i", ["i"]), ("o", ["o"]), ("u", ["u"]),
    # single letters — consonants
    ("ŕ", ["dx"]), ("ń", ["ny"]), ("ś", ["sh"]), ("ŋ", ["ng"]),
    ("'", ["q"]), ("x", ["hh"]), ("c", ["ts"]), ("j", ["y"]),
    ("b", ["b"]), ("d", ["d"]), ("f", ["f"]), ("g", ["g"]), ("h", ["h"]),
    ("k", ["k"]), ("l", ["l"]), ("m", ["m"]), ("n", ["n"]), ("p", ["p"]),
    ("r", ["r"]), ("s", ["s"]), ("t", ["t"]), ("v", ["v"]), ("w", ["w"]),
    ("y", ["y"]), ("z", ["z"]),
]
_STOPS = {"p", "t", "k", "b", "d", "g", "ch", "ts", "dz", "jh"}
# acoustically interchangeable vowel fallbacks (bank gaps: e.g. "k i" was
# recorded as "k iy" per arpasing convention)
ALT_VOWELS = {"i": ("iy", "ih"), "u": ("uw", "uh"), "e": ("eh", "ey"),
              "o": ("ow", "ao"), "a": ("aa", "ah", "ax"),
              "iy": ("i",), "uw": ("u",), "eh": ("e",), "ow": ("o",),
              "aa": ("a",), "ah": ("a",), "ax": ("a",), "ih": ("i",)}
_PALATAL = {c + "y" for c in
            "b d g k m n p r t h l v f ng dx".split()}   # Cy units in the bank


def g2p_asaxi(word: str):
    """Asaxi orthography -> bank phone list."""
    w = word.strip().lower()
    w = re.sub(r"[\s\-–—.,;:!?«»\"()\[\]0-9]+", "", w)
    phones, i = [], 0
    while i < len(w):
        for gr, ph in _ASAXI_RULES:
            if w.startswith(gr, i):
                # gemination: same consonant letter doubled -> held stop
                if (phones and ph[0] == phones[-1] and ph[0] not in
                        ("a", "e", "i", "o", "u")):
                    if ph[0] in _STOPS:
                        phones[-1] = "cl"       # cat [cl] told — held closure
                    else:
                        i += len(gr)            # long continuant: keep single
                        continue
                phones.extend(ph)
                i += len(gr)
                break
        else:
            i += 1                              # unknown mark: skip silently
    # palatalization post-pass: C + y (+V) -> Cy unit where the bank has one
    out, i = [], 0
    while i < len(phones):
        if (i + 1 < len(phones) and phones[i + 1] == "y"
                and phones[i] + "y" in _PALATAL and i + 2 < len(phones)):
            out.append(phones[i] + "y")
            i += 2
        else:
            out.append(phones[i])
            i += 1
    return out

# ----------------------------------------------------------- English g2p

def g2p_english(text: str):
    """English text -> bank phones via the CMU dictionary (arpasing)."""
    try:
        import cmudict
    except ImportError:
        raise RuntimeError("pip install cmudict  (needed for --lang en)")
    d = cmudict.dict()
    phones, missing = [], []
    for word in re.findall(r"[a-zA-Z']+", text.lower()):
        pron = d.get(word)
        if not pron:
            missing.append(word)
            continue
        phones.extend(re.sub(r"\d", "", p).lower() for p in pron[0])
    if missing:
        raise ValueError(f"not in CMU dictionary: {missing}")
    return phones

# ----------------------------------------------------------- Japanese g2p
# Uses the OpenUTAU phonemizer table (en-jap-mapping.yaml): 1247 hiragana +
# 289 katakana graphemes already map to this bank's phone set. Input may be
# kana OR Hepburn romaji (romaji is normalized to kana first). Kanji is NOT
# handled — that needs a morphological analyzer (see MULTISYN.md, Japanese).

_KANA_TABLE = {}   # kana grapheme -> [phones]; lazily loaded from the yaml

def _load_kana_table():
    if _KANA_TABLE:
        return _KANA_TABLE
    here = Path(__file__).resolve().parent
    for c in (here / "en-jap-mapping.yaml",
              here.parent / "festvox" / "en-jap-mapping.yaml"):
        if c.is_file():
            text = c.read_text(encoding="utf-8")
            for g, ph in re.findall(
                    r"grapheme:\s*(\S+)\s*\n\s*phonemes:\s*\[([^\]]*)\]",
                    text):
                if re.search(r"[぀-ゟ゠-ヿ]", g):        # kana only
                    _KANA_TABLE[g] = [x.strip() for x in ph.split(",") if x.strip()]
            break
    if not _KANA_TABLE:
        raise RuntimeError("en-jap-mapping.yaml not found next to synth_diphone.py "
                           "or in ../festvox/ (needed for --lang ja)")
    return _KANA_TABLE

# Hepburn romaji -> hiragana (gojūon + dakuten + yōon + sokuon/long vowel).
_ROMAJI = {
 "kya":"きゃ","kyu":"きゅ","kyo":"きょ","sha":"しゃ","shu":"しゅ","sho":"しょ",
 "cha":"ちゃ","chu":"ちゅ","cho":"ちょ","nya":"にゃ","nyu":"にゅ","nyo":"にょ",
 "hya":"ひゃ","hyu":"ひゅ","hyo":"ひょ","mya":"みゃ","myu":"みゅ","myo":"みょ",
 "rya":"りゃ","ryu":"りゅ","ryo":"りょ","gya":"ぎゃ","gyu":"ぎゅ","gyo":"ぎょ",
 "ja":"じゃ","ju":"じゅ","jo":"じょ","bya":"びゃ","byu":"びゅ","byo":"びょ",
 "pya":"ぴゃ","pyu":"ぴゅ","pyo":"ぴょ",
 "shi":"し","chi":"ち","tsu":"つ","dzu":"づ",
 "ka":"か","ki":"き","ku":"く","ke":"け","ko":"こ",
 "sa":"さ","su":"す","se":"せ","so":"そ","si":"し",
 "ta":"た","te":"て","to":"と","ti":"ち","tu":"つ",
 "na":"な","ni":"に","nu":"ぬ","ne":"ね","no":"の",
 "ha":"は","hi":"ひ","fu":"ふ","hu":"ふ","he":"へ","ho":"ほ",
 "ma":"ま","mi":"み","mu":"む","me":"め","mo":"も",
 "ya":"や","yu":"ゆ","yo":"よ",
 "ra":"ら","ri":"り","ru":"る","re":"れ","ro":"ろ",
 "wa":"わ","wo":"を","wi":"うぃ","we":"うぇ",
 "ga":"が","gi":"ぎ","gu":"ぐ","ge":"げ","go":"ご",
 "za":"ざ","zi":"じ","ji":"じ","zu":"ず","ze":"ぜ","zo":"ぞ",
 "da":"だ","di":"ぢ","du":"づ","de":"で","do":"ど",
 "ba":"ば","bi":"び","bu":"ぶ","be":"べ","bo":"ぼ",
 "pa":"ぱ","pi":"ぴ","pu":"ぷ","pe":"ぺ","po":"ぽ",
 "fa":"ふぁ","fi":"ふぃ","fe":"ふぇ","fo":"ふぉ",
 "a":"あ","i":"い","u":"う","e":"え","o":"お","n":"ん",
}

def romaji_to_kana(text: str) -> str:
    """Hepburn romaji -> hiragana. Handles sokuon (double consonant -> っ)
    and long vowels (macron/doubled vowel -> ー)."""
    s = text.lower().strip()
    s = (s.replace("ā","aa").replace("ī","ii").replace("ū","uu")
          .replace("ē","ee").replace("ō","ou").replace("â","aa")
          .replace("î","ii").replace("û","uu").replace("ê","ee").replace("ô","ou"))
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if not ch.isalpha():
            out.append(ch); i += 1; continue
        # sokuon: doubled consonant (except n) -> っ
        if (ch not in "aeimoun" and i + 1 < len(s) and s[i+1] == ch):
            out.append("っ"); i += 1; continue
        # syllabic n before consonant/space/end
        if ch == "n" and (i + 1 >= len(s) or s[i+1] not in "aeiouy"):
            out.append("ん"); i += 1; continue
        for L in (3, 2, 1):                       # longest romaji match
            if s[i:i+L] in _ROMAJI:
                out.append(_ROMAJI[s[i:i+L]]); i += L; break
        else:
            i += 1                                # skip unknown
    return "".join(out)

def g2p_japanese(text: str):
    """Japanese (kana or romaji) -> bank phone list."""
    table = _load_kana_table()
    # romaji if it's mostly ASCII letters
    if re.search(r"[A-Za-z]", text) and not re.search(r"[぀-ゟ゠-ヿ]", text):
        text = romaji_to_kana(text)
    phones, i = [], 0
    while i < len(text):
        if text[i] == "っ":                       # sokuon -> held closure
            phones.append("cl"); i += 1; continue
        if text[i] in "ーｰ" and phones:            # chōonpu -> lengthen (repeat)
            phones.append(phones[-1]); i += 1; continue
        for L in (2, 1):                          # yōon like きゃ are 2 chars
            if text[i:i+L] in table:
                phones.extend(table[text[i:i+L]]); i += L; break
        else:
            i += 1                                # punctuation / unknown
    return phones

# ------------------------------------------------------------- rendering

def _xfade(a: array.array, b: array.array, n: int) -> array.array:
    """Concatenate a+b with an n-sample linear crossfade."""
    n = min(n, len(a), len(b))
    if n <= 0:
        a.extend(b)
        return a
    for i in range(n):
        t = i / n
        a[len(a) - n + i] = int(a[len(a) - n + i] * (1 - t) + b[i] * t)
    a.extend(b[n:])
    return a


def render(db: DiphoneDB, phones, out_path=None, speed=1.0):
    """Phone list -> wav bytes (and optionally a file). Diphone selection:
    pau-p1, p1-p2, ..., pn-pau, preferring the bank's word-final allophones
    ("prev-C_") for a final consonant. Missing diphones are skipped with a
    note in the returned report.

    `speed` sets the pace: >1 is faster, <1 is slower (1.0 = normal). It works
    by scaling how much of each recorded phone is kept — this is concatenative,
    not time-stretch, so it never changes pitch, but slowing below ~1.0 is
    capped by the amount of audio actually recorded per phone."""
    speed = max(0.25, min(4.0, float(speed or 1.0)))
    half_ms = HALF_MS / speed                     # slower speed => wider window
    seq = ["pau"] + list(phones) + ["pau"]
    picked, skipped = [], []
    i = 0
    while i < len(seq) - 1:
        x, y = seq[i], seq[i + 1]
        # VCV fallback: some C+V transitions exist only as "prev CV" units
        # (Japanese-style recording) — "u-ki" covers u->k->i in one slice
        if (i + 2 < len(seq) and not db.has(f"{x}-{y}")
                and db.has(f"{x}-{y}{seq[i + 2]}")):
            picked.append(f"{x}-{y}{seq[i + 2]}")
            i += 2
            continue
        # word-final consonant: the bank records "prev C-" as one unit
        if (y != "pau" and i + 2 < len(seq) and seq[i + 2] == "pau"
                and db.has(f"{x}-{y}_")):
            picked.append(f"{x}-{y}_")
            i += 2
            continue
        cands = [f"{x}-{y}"]
        cands += [f"{x}-{y2}" for y2 in ALT_VOWELS.get(y, ())]
        cands += [f"{x2}-{y}" for x2 in ALT_VOWELS.get(x, ())]
        if x == y:
            cands.append(f"{x}-{x}")
        for cand in cands:
            if db.has(cand):
                picked.append(cand)
                break
        else:
            # gap fallback: the bank's Japanese-style CV units ("ki") cover
            # C+V as one sample whose mid is the C/V boundary
            if y != "pau" and db.has(f"{x}{y}-{x}{y}"):
                picked.append(f"{x}{y}-{x}{y}")
            else:
                skipped.append(f"{x}-{y}")
        i += 1

    fr, out = None, array.array("h")
    for dip in picked:
        r, chunk = db.slice(dip, half_ms=half_ms)
        fr = fr or r
        out = _xfade(out, chunk, int(CROSSFADE_MS / 1000 * r))
    if not out:
        raise ValueError(f"nothing rendered (missing diphones: {skipped})")
    edge = int(EDGE_FADE_MS / 1000 * fr)
    for i in range(min(edge, len(out))):
        out[i] = int(out[i] * i / edge)
        out[-1 - i] = int(out[-1 - i] * i / edge)
    # peak-normalize to -3 dB
    peak = max(1, max(out), -min(out))
    gain = min(4.0, 0.707 * 32767 / peak)
    out = array.array("h", [max(-32768, min(32767, int(s * gain)))
                            for s in out])

    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fr)
        w.writeframes(out.tobytes())
    data = buf.getvalue()
    if out_path:
        Path(out_path).write_bytes(data)
    return {"wav": data, "phones": list(phones), "diphones": picked,
            "skipped": skipped, "seconds": round(len(out) / fr, 2),
            "speed": round(speed, 3)}


def synth_text(cfg, text: str, lang: str = "asaxi", out_path=None, speed=None):
    """One-call front end used by the CLI and the HTTP API. `speed` (>1 faster,
    <1 slower) falls back to cfg['synth_speed'] then 1.0."""
    db = DiphoneDB(find_db(cfg))
    if lang == "en":
        phones = g2p_english(text)
    elif lang in ("ja", "jp"):
        phones = g2p_japanese(text)
    else:
        phones = g2p_asaxi(text)
    if not phones:
        raise ValueError(f"no phonemes derived from {text!r}")
    if speed is None:
        speed = cfg.get("synth_speed", 1.0)
    return render(db, phones, out_path=out_path, speed=speed)


# ------------------------------------------------------------- standalone CLI
# Lets you render audio directly from the DB, outside vocab_forge, driven by
# the same festvox.json the builder uses. See ../festvox/GUIDE.md.

def _find_festvox_config(explicit=None):
    import os
    cands = []
    if explicit:
        cands.append(Path(explicit))
    if os.environ.get("FESTVOX_CONFIG"):
        cands.append(Path(os.environ["FESTVOX_CONFIG"]))
    here = Path(__file__).resolve().parent
    cands += [Path.cwd() / "festvox.json",
              here / "festvox.json",
              here.parent / "festvox" / "festvox.json"]   # 99_Tools/festvox/
    for c in cands:
        if c and c.is_file():
            return c
    return None


def _db_from_config(fcfg, voice=None):
    """Resolve a voice key in festvox.json to its built DB directory."""
    voices = fcfg.get("voices") or {}
    key = voice or fcfg.get("default_voice") or (next(iter(voices), None))
    if key and key in voices and voices[key].get("out"):
        return Path(voices[key]["out"]), key
    root = fcfg.get("output_root") or "."
    return (Path(root) / key if key else None), key


def safe_name(text, maxlen=48):
    """Filesystem-safe slug that KEEPS non-ASCII letters (kana, accented
    Asaxi, etc.) so distinct inputs get distinct filenames. Falls back to a
    short hash only when nothing usable remains (e.g. punctuation only)."""
    s = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE).strip("_")[:maxlen]
    s = s.strip("_")
    if not s:
        import hashlib
        s = "u" + hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return s


def _main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Render text with a diphone voice (Asaxi or English), "
                    "standalone. DB + output dir come from festvox.json unless "
                    "overridden.")
    ap.add_argument("text")
    ap.add_argument("--lang", default=None, choices=["asaxi", "en", "ja"],
                    help="default: festvox.json 'default_lang', else 'en'")
    ap.add_argument("--voice", default=None,
                    help="voice key in festvox.json (default: default_voice)")
    ap.add_argument("--db", default=None,
                    help="path to a built DB dir (overrides --voice/config)")
    ap.add_argument("--config", default=None, help="path to festvox.json")
    ap.add_argument("--out", default=None, help="explicit output wav path")
    ap.add_argument("--outdir", default=None,
                    help="output directory (default: config synth_output_dir "
                         "or current dir); filename auto-generated from text")
    ap.add_argument("--speed", type=float, default=None,
                    help="pace: >1 faster, <1 slower (default: festvox.json "
                         "'synth_speed', else 1.0)")
    a = ap.parse_args()

    fcfg, fp = {}, None
    cf = _find_festvox_config(a.config)
    if cf:
        fcfg = json.loads(cf.read_text(encoding="utf-8"))
        fp = cf

    if a.db:
        db_dir = Path(a.db)
    else:
        db_dir, key = _db_from_config(fcfg, a.voice)
        if not db_dir:
            raise SystemExit("No DB: pass --db, or set voices/output_root in "
                             f"festvox.json (looked at {fp}).")
    cfg = {"festvox_db": [str(db_dir)]}

    lang = a.lang or fcfg.get("default_lang") or "en"
    if a.out:
        out_path = Path(a.out)
    else:
        outdir = Path(a.outdir or fcfg.get("synth_output_dir") or ".")
        outdir.mkdir(parents=True, exist_ok=True)
        out_path = outdir / f"{lang}_{safe_name(a.text)}.wav"

    speed = a.speed if a.speed is not None else fcfg.get("synth_speed", 1.0)
    r = synth_text(cfg, a.text, lang, out_path=str(out_path), speed=speed)
    print(json.dumps({"out": str(out_path), "db": str(db_dir), "speed": speed,
                      "seconds": r["seconds"], "phones": r["phones"],
                      "skipped": r["skipped"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    _main()
