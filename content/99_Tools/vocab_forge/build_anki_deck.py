# -*- coding: utf-8 -*-
"""
Build an Anki deck (.apkg) from the Asaxi lexicon + anki-assets.

Requires:  pip install genanki
Usage:     python build_anki_deck.py [--out Asaxi.apkg] [--require-audio] [--limit N]

Card layout
  Front: the word in three renderings — abugida script, alphabet script, Latin.
  Back:  word audio + sentence audio, the word in both Asaxi scripts,
         the example sentence in both scripts + Latin, translations, image.

Fonts: drop real script fonts into  anki-assets/fonts/  named
  AsaxiAbugida.ttf  and  AsaxiAlpha.ttf  — they will be embedded in the deck.
Until then the deck falls back to whatever cursive fonts the device has.
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import genanki
except ImportError:
    sys.exit("genanki is not installed. Run:  pip install genanki")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_core as core

CSS = """
.card { background:#1e1e2e; color:#e6e6f0; text-align:center; font-family:"Segoe UI",sans-serif; }
.abugida { font-family:"AsaxiAbugida","Pacifico",cursive; font-size:54px; line-height:1.6; }
.alpha   { font-family:"AsaxiAlpha","Segoe Script",cursive; font-size:40px; line-height:1.6; opacity:.92; }
.latin   { font-size:30px; font-weight:600; color:#c4a7e7; }
.ipa     { color:#9a9ab0; font-size:18px; }
.gloss   { font-size:20px; margin-top:10px; }
.gloss-pl{ font-size:16px; color:#9a9ab0; }
.sentence{ margin-top:14px; }
.sentence .abugida{ font-size:34px; } .sentence .alpha{ font-size:26px; }
.sentence .latin{ font-size:20px; font-weight:400; color:#e6e6f0; }
.sgloss  { font-style:italic; color:#9a9ab0; font-size:16px; }
img { max-width: 320px; border-radius: 10px; margin-top: 12px; }
hr { border-color:#3c3c55; }
@font-face { font-family:"AsaxiAbugida"; src: url("_AsaxiAbugida.ttf"); }
@font-face { font-family:"AsaxiAlpha");  src: url("_AsaxiAlpha.ttf"); }
"""
CSS = CSS.replace('"AsaxiAlpha");', '"AsaxiAlpha";')  # keep template readable above

FRONT = """
<div class="abugida">{{Word}}</div>
<div class="alpha">{{Word}}</div>
<div class="latin">{{Word}}</div>
"""

BACK = """
{{AudioWord}} {{AudioSentence}}
<div class="abugida">{{Word}}</div>
<div class="alpha">{{Word}}</div>
<div class="ipa">{{IPA}}</div>
<div class="gloss">{{GlossEN}}</div>
<div class="gloss-pl">{{GlossPL}}</div>
<hr>
{{#Example}}
<div class="sentence">
  <div class="abugida">{{Example}}</div>
  <div class="alpha">{{Example}}</div>
  <div class="latin">{{Example}}</div>
  <div class="sgloss">{{ExampleGloss}}</div>
</div>
{{/Example}}
{{#Image}}<div>{{Image}}</div>{{/Image}}
"""

MODEL = genanki.Model(
    1607392319001,
    "Asaxi Vocabulary",
    fields=[{"name": f} for f in
            ("Word", "IPA", "GlossEN", "GlossPL", "Example", "ExampleGloss",
             "Image", "AudioWord", "AudioSentence", "Type", "Freq")],
    templates=[{"name": "Asaxi -> meaning", "qfmt": FRONT,
                "afmt": '{{FrontSide}}<hr id="answer">' + BACK}],
    css=CSS,
)


def section(text, header):
    m = re.search(r"(?ms)^###\s+" + re.escape(header) + r"\s*$(.*?)(?=^#{1,6}\s|\Z)", text)
    return m.group(1).strip() if m else ""


def clean_inline(s):
    s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    return s.replace("**", "").replace("*", "").replace("_", "").strip()


def extract_example(text):
    block = section(text, "Example sentence") or section(text, "Example sentence:")
    if not block:
        return "", ""
    sent, gloss = "", ""
    for line in block.splitlines():
        line = line.strip().lstrip("- ").strip()
        if not line or line.lower() in ("x", "null"):
            continue
        if not sent and (line.startswith("**") or not gloss):
            if line.startswith("**"):
                sent = clean_inline(line)
                continue
        if line.startswith("_") or line.startswith("*"):
            gloss = clean_inline(line)
        elif not sent:
            sent = clean_inline(line)
        elif not gloss:
            gloss = clean_inline(line)
    return sent, gloss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Asaxi.apkg")
    ap.add_argument("--require-audio", action="store_true",
                    help="only include words that have the a1 word recording")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cfg = core.load_config()
    lex = core.Lexicon(cfg)
    adir = core.anki_dir(cfg)
    deck = genanki.Deck(2059400110001, "Asaxi")
    media = []

    for f in ("AsaxiAbugida.ttf", "AsaxiAlpha.ttf"):
        fp = adir / "fonts" / f
        if fp.exists():
            tgt = adir / ("_" + f)
            tgt.write_bytes(fp.read_bytes())
            media.append(str(tgt))

    def _eff(e):
        f = e.get("freq")
        if f is not None:
            return f
        wf = core.wordfreq_rating(e.get("gloss_en", ""), e.get("gloss_pl", ""))
        return wf if wf is not None else 0

    n = 0
    # Higher frequency first (top of deck); alphabetical as a tiebreak.
    for e in sorted(lex.entries, key=lambda x: (-_eff(x),
                       -core.gloss_zipf(x.get("gloss_en", ""), x.get("gloss_pl", "")),
                       x["word"].lower())):
        if not e["gloss_en"]:
            continue
        st = core.anki_status(cfg, name=Path(e["path"]).stem)
        if args.require_audio and not st["a1"]:
            continue
        text = Path(e["path"]).read_text(encoding="utf-8")
        ipa = ""
        m = re.search(r"IPA:\s*(/[^\n]+/)", text)
        if m:
            ipa = m.group(1).strip()
        sent, sgloss = extract_example(text)

        img = f'<img src="{st["image"]}">' if st["image"] else ""
        a1 = f"[sound:{st['a1']}]" if st["a1"] else ""
        a2 = f"[sound:{st['a2']}]" if st["a2"] else ""
        for key in ("image", "a1", "a2"):
            if st[key]:
                media.append(str(adir / st[key]))

        note = genanki.Note(model=MODEL, fields=[
            e["word"], ipa, e["gloss_en"], e.get("gloss_pl", ""),
            sent, sgloss, img, a1, a2, e["type_raw"], f"{_eff(e):03d}"],
            guid=genanki.guid_for(e.get("id") or
                                  ("asaxi::" + e["word"] + "::" + e["type_raw"])),
            due=n + 1)   # new-card position: higher frequency first (set Anki new-card order to "Order gathered"/"Order added")
        deck.add_note(note)
        n += 1
        if args.limit and n >= args.limit:
            break

    pkg = genanki.Package(deck)
    pkg.media_files = sorted(set(media))
    pkg.write_to_file(args.out)
    print(f"Wrote {args.out}: {n} notes, {len(set(media))} media files.")
    if not any("Asaxi" in m and m.endswith(".ttf") for m in media):
        print("Note: no script fonts embedded — put AsaxiAbugida.ttf / AsaxiAlpha.ttf "
              "in anki-assets/fonts/ to render the two Asaxi scripts properly.")


if __name__ == "__main__":
    main()
