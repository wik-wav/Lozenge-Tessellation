# -*- coding: utf-8 -*-
"""
utau2festvox.py — convert a configured UTAU voicebank (oto.ini) into a
FestVox-compatible diphone database.

Usage:
    python utau2festvox.py --bank <voicebank dir> [--out <output dir>]
                           [--name asaxi] [--no-copy]

What it does
  1. Parses oto.ini:      File=Alias,Offset,Consonant,Blank,Preutterance,Overlap
  2. Converts UTAU's relative-ms geometry into the absolute second-based
     (start, mid, end) triples a FestVox diphone index needs:
        start = Offset
        mid   = Offset + Preutterance     (the UTAU alignment point is the
                                           phone boundary of the diphone)
        end   = Offset + |Blank|          if Blank < 0   (region length)
              = file_length - Blank       if Blank >= 0  (cut from the end)
     NOTE on Blank: standard UTAU semantics are NEGATIVE = length measured
     from Offset, POSITIVE = milliseconds trimmed from the file end. (The
     task brief stated the inverse; on this bank's own data the inverse
     produces end-times that overrun the next diphone's offset by seconds,
     so the standard semantics are used. Verified: every produced
     start < mid < end and end - start < 1.2 s.)
  3. Maps UTAU aliases to Festival phone names through PHONEME_MAP below,
     sanitizing everything into valid Scheme atoms.
  4. Builds the FestVox layout:
        OUT/wav/        copied + renamed source wavs
        OUT/dic/        <name>_diphone.scm  (Scheme index list)
                        <name>_diphone.est  (EST-format index, for UniSyn)
                        diphone_index.json  (fast loader for other tools)
        OUT/festival/   <name>_diphone_stub.scm (minimal voice scaffold)
  5. Writes OUT/conversion_report.txt (unmapped aliases, variant dupes,
     missing/odd wavs).

Requires only the Python standard library (wave module measures the files,
which is what makes negative Blank values computable at all).
"""
import argparse
import json
import re
import shutil
import sys
import unicodedata
import wave
from pathlib import Path

# --------------------------------------------------------------------------
# PHONEME MAPPING — edit this block to control the UTAU→Festival mapping.
#
# Keys are UTAU alias *tokens* (after the pitch suffix, e.g. "F#3", has been
# stripped and the alias split on whitespace). Values are the Festival phone
# names to use in diphone identifiers ("k","a" -> diphone "k-a").
#
#   * "-" is the UTAU silence marker -> Festival "pau".
#   * A token ending in "-" (e.g. "b-") is a *word-final* allophone; it maps
#     to "<phone>_" (final variant) so it stays a distinct diphone member.
#   * Tokens not listed here fall back to themselves if they are plain
#     ASCII alphanumerics; numbered recording variants ("aa2", "ah11") are
#     reduced to their base symbol automatically (longest non-numeric stem),
#     EXCEPT for symbols explicitly listed here (so å1-style *real* symbols
#     survive if a bank uses them).
#   * Map a token to None to exclude it from the database (breaths etc.).
# --------------------------------------------------------------------------
PHONEME_MAP = {
    "-": "pau",
    # breaths / non-speech: excluded from the diphone index
    "inh": None, "exh": None, "sil": "pau", "BR": None, "br": None,
    # identity mappings, written out for documentation value — the full
    # arpasing set used by the 4_Fis3 bank (vowels, consonants, extras):
    **{p: p for p in (
        "a aa ae ah ao aw ax ay e eh er ey i ih iy o ow oy u uh uw "
        "b by ch d dy dh dx dxy dz f fy g gy h hy hh jh k ky l ly m my "
        "n ny ng ngy nn mm nng xn p py q r ry rr s sh t ty ts th v vy "
        "w y z zh cl si zi shi ri wi".split())},
    # Japanese-style CV units exist in the bank ("ka","byo"...) but are not
    # used for diphone synthesis; they are indexed anyway (harmless) since
    # unlisted ASCII tokens fall through as themselves.
}

PITCH_SUFFIX = re.compile(r"([A-G]#?\d+)$")      # trailing UTAU pitch tag
VARIANT_DIGITS = re.compile(r"\d+$")             # recording-take numbering


def sanitize_scheme(name: str) -> str:
    """Make a string safe as a Scheme atom / filename component:
    ASCII-fold, keep [A-Za-z0-9_], collapse the rest to '_'."""
    folded = unicodedata.normalize("NFKD", name)
    folded = folded.encode("ascii", "ignore").decode("ascii") or "x"
    return re.sub(r"[^A-Za-z0-9_]+", "_", folded).strip("_") or "x"


def map_token(tok: str, report):
    """UTAU alias token -> Festival phone name (or None to skip)."""
    if tok in PHONEME_MAP:
        return PHONEME_MAP[tok]
    if tok.endswith("-") and tok[:-1]:
        base = map_token(tok[:-1], report)          # final allophone: "b-"
        return None if base is None else base + "_"
    stripped = VARIANT_DIGITS.sub("", tok)          # "aa2" -> "aa"
    if stripped != tok and stripped in PHONEME_MAP:
        return PHONEME_MAP[stripped]
    if stripped != tok and stripped.endswith("-"):  # "d-1" -> final "d-"
        return map_token(stripped, report)
    if re.fullmatch(r"[A-Za-z_]+", stripped or tok):
        return stripped or tok                      # plain ASCII: identity
    report["unmapped"].add(tok)
    return None


def parse_oto(path: Path, report):
    """Yield dicts for each oto.ini entry (UTAU ms values, raw)."""
    for enc in ("utf-8", "cp932", "latin-1"):
        try:
            lines = path.read_text(encoding=enc).splitlines()
            break
        except UnicodeDecodeError:
            continue
    for ln, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith(("#", ";")) or "=" not in line:
            continue
        fname, rest = line.split("=", 1)
        parts = rest.split(",")
        if len(parts) < 6:
            report["bad_lines"].append(ln)
            continue
        alias = parts[0].strip()
        try:
            offset, consonant, blank, preutt, overlap = map(float, parts[1:6])
        except ValueError:
            report["bad_lines"].append(ln)
            continue
        yield {"wav": fname.strip(), "alias": alias, "offset": offset,
               "consonant": consonant, "blank": blank,
               "preutterance": preutt, "overlap": overlap, "line": ln}


def wav_length_ms(path: Path, cache={}):
    """Total duration of a wav in milliseconds (measured, cached)."""
    if path not in cache:
        with wave.open(str(path), "rb") as w:
            cache[path] = w.getnframes() / w.getframerate() * 1000.0
    return cache[path]


def convert(bank: Path, out: Path, name: str, copy_wavs: bool):
    report = {"unmapped": set(), "bad_lines": [], "dupes": 0,
              "missing_wav": set(), "skipped_nonspeech": 0, "singles": 0}
    oto = bank / "oto.ini"
    if not oto.exists():
        sys.exit(f"no oto.ini in {bank}")

    for d in ("wav", "dic", "festival"):
        (out / d).mkdir(parents=True, exist_ok=True)

    index = {}          # diphone name -> (wavfile, start_s, mid_s, end_s)
    preferred = {}      # diphone name -> had unnumbered (clean) alias?
    wav_map = {}        # source wav name -> sanitized target name
    for e in parse_oto(oto, report):
        src = bank / e["wav"]
        if not src.exists():
            report["missing_wav"].add(e["wav"])
            continue

        alias = PITCH_SUFFIX.sub("", e["alias"]).strip()
        toks = alias.split()
        if len(toks) == 1:                      # sustain: use as X-X diphone
            toks = [toks[0], toks[0]]
            report["singles"] += 1
        if len(toks) != 2:
            report["bad_lines"].append(e["line"])
            continue
        p1, p2 = (map_token(t, report) for t in toks)
        if p1 is None or p2 is None:
            report["skipped_nonspeech"] += 1
            continue
        clean = not any(VARIANT_DIGITS.search(t) for t in toks)
        dip = f"{sanitize_scheme(p1)}-{sanitize_scheme(p2)}"

        # ---- timing conversion (see module docstring) --------------------
        total = wav_length_ms(src)
        start = e["offset"]
        mid = e["offset"] + e["preutterance"]
        end = e["offset"] + abs(e["blank"]) if e["blank"] < 0 \
            else total - e["blank"]
        end = min(end, total)
        if not (0 <= start < mid < end):
            report["bad_lines"].append(e["line"])
            continue

        if dip in index:                        # keep first clean variant
            report["dupes"] += 1
            if preferred[dip] or not clean:
                continue
        preferred[dip] = clean
        if e["wav"] not in wav_map:
            wav_map[e["wav"]] = sanitize_scheme(Path(e["wav"]).stem) + ".wav"
        index[dip] = (wav_map[e["wav"]],
                      round(start / 1000.0, 6),
                      round(mid / 1000.0, 6),
                      round(end / 1000.0, 6))

    # ---- wav copy --------------------------------------------------------
    if copy_wavs:
        for src_name, tgt_name in sorted(wav_map.items()):
            tgt = out / "wav" / tgt_name
            if not tgt.exists():
                shutil.copyfile(bank / src_name, tgt)

    # ---- dic/<name>_diphone.scm (the Scheme index list) -------------------
    scm = out / "dic" / f"{name}_diphone.scm"
    with scm.open("w", encoding="ascii") as f:
        f.write(f";; {name} diphone index - generated by utau2festvox.py\n")
        f.write(";; (diphone wavfile start_s mid_s end_s)\n")
        f.write(f"(set! {sanitize_scheme(name)}_diphone_index\n  '(\n")
        for dip in sorted(index):
            w, s, m, e = index[dip]
            f.write(f'    ("{dip}" "{w}" {s:.6f} {m:.6f} {e:.6f})\n')
        f.write("  ))\n")

    # ---- dic/<name>_diphone.est (EST_File index for UniSyn) ---------------
    est = out / "dic" / f"{name}_diphone.est"
    with est.open("w", encoding="ascii") as f:
        f.write("EST_File index\nDataType ascii\nNumEntries %d\n"
                "IndexName %s_diphone\nEST_Header_End\n"
                % (len(index), sanitize_scheme(name)))
        for dip in sorted(index):
            w, s, m, e = index[dip]
            f.write(f"{dip} {Path(w).stem} {s:.6f} {m:.6f} {e:.6f}\n")

    # ---- machine-readable copy for other tools (vocab_forge synth) --------
    (out / "dic" / "diphone_index.json").write_text(
        json.dumps({"name": name, "samplerate_note": "see wav files",
                    "index": index}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    # ---- festival/ stub ----------------------------------------------------
    (out / "festival" / f"{name}_diphone_stub.scm").write_text(
        f""";; Minimal scaffold for a FestVox UniSyn diphone voice "{name}".
;; Load the index and point us_diphone_init at it:
(load (path-append (pwd) "../dic/{name}_diphone.scm"))
(set! {sanitize_scheme(name)}_db_params
      (list
       (list 'name '{sanitize_scheme(name)})
       (list 'index_file (path-append (pwd) "../dic/{name}_diphone.est"))
       (list 'grouped "false")
       (list 'base_dir (path-append (pwd) ".."))
       (list 'coef_dir "wav")   ;; using raw wav; run make_lpc for LPC coefs
       (list 'sig_dir  "wav")
       (list 'default_diphone "pau-pau")))
;; (us_diphone_init {sanitize_scheme(name)}_db_params)
""", encoding="ascii")

    # ---- report ------------------------------------------------------------
    rep = out / "conversion_report.txt"
    rep.write_text(
        "utau2festvox conversion report\n"
        f"diphones indexed : {len(index)}\n"
        f"wav files used   : {len(wav_map)}\n"
        f"sustain singles  : {report['singles']}\n"
        f"variant dupes    : {report['dupes']} (first clean take kept)\n"
        f"non-speech skips : {report['skipped_nonspeech']}\n"
        f"bad oto lines    : {sorted(set(report['bad_lines']))[:20]}\n"
        f"missing wavs     : {sorted(report['missing_wav'])[:20]}\n"
        f"unmapped tokens  : {sorted(report['unmapped'])}\n",
        encoding="utf-8")
    print(rep.read_text(encoding="utf-8"))
    print(f"wrote {scm}\n      {est}\n      dic/diphone_index.json")
    return {"out": str(out), "diphones": len(index), "wavs": len(wav_map),
            "unmapped": sorted(report["unmapped"])}


# --------------------------------------------------------------------------
# Config file (shared with synth_diphone.py). Located in this order:
#   --config PATH  >  $FESTVOX_CONFIG  >  ./festvox.json  >  <script dir>/festvox.json
# Schema:
#   { "output_root": "<dir where DBs are built>",
#     "voices": { "<key>": {"bank": "<UTAU dir>", "name": "<phoneset>",
#                           "out": "<optional explicit DB dir>",
#                           "copy_wavs": true} } }
# A voice builds to  out  if given, else  output_root/<key>.
# --------------------------------------------------------------------------
import os

def find_config(explicit=None):
    cands = []
    if explicit:
        cands.append(Path(explicit))
    if os.environ.get("FESTVOX_CONFIG"):
        cands.append(Path(os.environ["FESTVOX_CONFIG"]))
    cands += [Path.cwd() / "festvox.json",
              Path(__file__).resolve().parent / "festvox.json"]
    for c in cands:
        if c and c.is_file():
            return c
    return None


def load_config(explicit=None):
    fp = find_config(explicit)
    if not fp:
        return None, None
    return json.loads(fp.read_text(encoding="utf-8")), fp


def voice_out_dir(cfg, key, spec):
    if spec.get("out"):
        return Path(spec["out"])
    root = cfg.get("output_root") or "."
    return Path(root) / key


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Build FestVox diphone DB(s) from UTAU voicebank(s). "
                    "With no --bank, builds voices listed in festvox.json.")
    ap.add_argument("--config", default=None,
                    help="path to festvox.json (default: auto-locate)")
    ap.add_argument("--voice", default=None,
                    help="build only this voice key from the config "
                         "(default: build all)")
    ap.add_argument("--bank", type=Path, default=None,
                    help="one-off: UTAU bank dir (bypasses the config)")
    ap.add_argument("--out", type=Path, default=None,
                    help="one-off: output DB dir (default: <bank>/festvox_db)")
    ap.add_argument("--name", default=None, help="one-off: phoneset name")
    ap.add_argument("--no-copy", action="store_true",
                    help="index only; do not copy wav files")
    a = ap.parse_args()

    if a.bank:                                   # explicit one-off build
        convert(a.bank, a.out or a.bank / "festvox_db", a.name or "asaxi",
                copy_wavs=not a.no_copy)
        sys.exit(0)

    cfg, fp = load_config(a.config)
    if not cfg:
        sys.exit("No festvox.json found and no --bank given. "
                 "Create festvox.json (see GUIDE.md) or pass --bank.")
    print(f"config: {fp}")
    voices = cfg.get("voices") or {}
    keys = [a.voice] if a.voice else list(voices)
    if a.voice and a.voice not in voices:
        sys.exit(f"voice {a.voice!r} not in config (have: {list(voices)})")
    if not keys:
        sys.exit("config has no voices.")
    for key in keys:
        spec = voices[key]
        out = voice_out_dir(cfg, key, spec)
        print(f"\n=== building '{key}' -> {out} ===")
        convert(Path(spec["bank"]), out, spec.get("name", "asaxi"),
                copy_wavs=spec.get("copy_wavs", True) and not a.no_copy)
