# Building a FestVox diphone voice from a UTAU bank — full walkthrough

This guide takes you from **a set of recorded samples** to **a working
synthesizer** that speaks **English** (the default), **Asaxi**, and
**Japanese**, start to finish. No prior knowledge of Festival or diphone
synthesis is assumed.

---

## 0. The big picture

```
UTAU voicebank                festvox.json            FestVox_DBs\asaxi_lem\
(wav samples + oto.ini)  ──▶  (you edit paths)  ──▶   (the built database)
        record                    configure                  build
                                                                │
                                                                ▼
                                            synth_diphone.py  /  vocab_forge
                                            (turn text into a .wav)
```

Three moving parts, each in its own place:

| Thing | Where it lives | What it is |
| --- | --- | --- |
| **Voicebank** | `D:\UTAU\voice\…\4_Fis3\` | your recordings + `oto.ini` |
| **Config** | `99_Tools\festvox\festvox.json` | the paths you edit |
| **Builder** | `99_Tools\festvox\utau2festvox.py` | UTAU → FestVox DB |
| **Database** | `E:\Portable_Software\FestVox_DBs\asaxi_lem\` | the built voice |
| **Renderer** | `99_Tools\vocab_forge\synth_diphone.py` | text → speech |

The database lives **outside** the voicebank on purpose — the voicebank stays
clean, and you can keep several built voices side by side in `FestVox_DBs`.

---

## 1. Record the voicebank (in UTAU / OpenUTAU)

You need two things in the bank folder:

1. **`.wav` samples** — 16-bit mono. The Lem bank records long strings of
   phones at one pitch (e.g. `b_rr_ch_rr_d_rr_…F#3.wav`).
2. **`oto.ini`** — the timing map UTAU writes. Each line is:

   ```
   filename.wav=ALIAS,Offset,Consonant,Blank,Preutterance,Overlap
   ```

   The **alias** is what matters for diphones. Use the `phone1 phone2`
   convention — a space-separated pair naming the two sounds the clip
   transitions between:

   ```
   b_rr_…F#3.wav=b rrF#3,1025.3,153.2,-287.5,53.0,22.7
                        └── alias "b rr" (the b→rr diphone) + pitch tag F#3
   ```

   - A **single-token** alias (`rr`) is treated as a steady-state sustain and
     becomes the `rr-rr` diphone.
   - **Silence / breaths:** `-` means silence (→ `pau`); `inh`, `exh`, `br`,
     `BR` are excluded from the database automatically.
   - A trailing dash (`b-`) marks a **word-final** allophone and is kept as a
     distinct unit (`b_`).

> **What "the samples are the same" means for rebuilding:** as long as a new
> recording set uses this same alias scheme and the same `oto.ini` format,
> you rebuild with one command (Step 3) — nothing else changes.

**Aim for full coverage.** For clean synthesis the bank should contain every
`phoneA phoneB` pair you expect to speak, plus `- X` (silence→phone) and
`X -` (phone→silence) for word edges. The Lem bank has all of them (4252
diphones); gaps are covered by fallbacks (see §7) but real recordings sound
better.

---

## 2. Configure `festvox.json`

Open `99_Tools\festvox\festvox.json` and set the paths for your machine:

```json
{
  "output_root": "E:/Portable_Software/FestVox_DBs",
  "synth_output_dir": "E:/Portable_Software/FestVox_DBs/_samples",
  "default_voice": "asaxi_lem",
  "default_lang": "en",

  "voices": {
    "asaxi_lem": {
      "bank": "D:/UTAU/voice/Lem_V4Bi_Civet/4_Fis3",
      "name": "asaxi",
      "copy_wavs": true
    }
  }
}
```

| Field | Meaning |
| --- | --- |
| `output_root` | folder where databases are built. Each voice builds to `output_root/<voice key>` (here `…/FestVox_DBs/asaxi_lem`). |
| `synth_output_dir` | where the standalone renderer drops `.wav` files by default. |
| `default_voice` | which voice the renderer uses when you don't say `--voice`. |
| `default_lang` | language used when you don't pass `--lang` — `en` (default), `asaxi`, or `ja`. |
| `synth_speed` | default pace when you don't pass `--speed`: `1.0` normal, `>1` faster, `<1` slower. |
| `voices` | one entry per voice. `bank` = the UTAU folder; `name` = the phoneset label baked into filenames; `copy_wavs` = copy the audio into the DB (recommended so the DB is self-contained). Optional `out` overrides the build location for that one voice. |

Use forward slashes `/` (they work on Windows too). You can list several
voices and build them all at once.

> Tip: the builder and the renderer both auto-find `festvox.json` — they look
> at `--config`, then `$FESTVOX_CONFIG`, then the current folder, then next to
> the script. So editing this one file is enough.

---

## 3. Build the database

From `99_Tools\festvox\`:

```
python utau2festvox.py                 # builds every voice in festvox.json
python utau2festvox.py --voice asaxi_lem   # just one
```

One-off build without touching the config:

```
python utau2festvox.py --bank "D:/UTAU/voice/…/4_Fis3" --out "E:/…/FestVox_DBs/test" --name asaxi
```

You'll see a report like:

```
diphones indexed : 4252
wav files used   : 734
unmapped tokens  : ['-aw11']
```

The result in `E:\Portable_Software\FestVox_DBs\asaxi_lem\`:

```
wav/                       the copied 16-bit samples (renamed to be safe)
dic/asaxi_diphone.scm      Festival index list (diphone wav start mid end)
dic/asaxi_diphone.est      EST index (for real Festival / make_lpc)
dic/diphone_index.json     the index the Python renderer reads
festival/asaxi_diphone_stub.scm   scaffold for a real Festival voice
conversion_report.txt      what was indexed, skipped, or unmapped
```

**Always glance at `conversion_report.txt`.**

- `unmapped tokens` — aliases the builder didn't recognize. A stray one like
  `-aw11` (a typo in the oto) is harmless; a whole phone missing means you
  should add it to `PHONEME_MAP` (see §7) and rebuild.
- `bad oto lines` — malformed lines, **or** timings that came out impossible
  (`start < mid < end` failed). Empty is good.
- `missing wavs` — oto references a file that isn't there.

---

## 4. Point the tools at the database

**Standalone renderer** — nothing to do; it reads `festvox.json` and resolves
`default_voice` → `output_root/asaxi_lem`.

**vocab_forge** — its own `config.json` has a `festvox_db` list; it's already
set to the new location:

```json
"festvox_db": [
  "E:/Portable_Software/FestVox_DBs/asaxi_lem",
  "/sessions/…/FestVox_DBs/asaxi_lem"
]
```

It uses the first path that exists, so you can keep several and reorder. To
switch voices, drop a different DB path at the top of the list.

---

## 5. Synthesize

### Standalone (outside vocab_forge)

From `99_Tools\vocab_forge\`:

```
python synth_diphone.py "the velveteen rabbit"            # English (default)
python synth_diphone.py "Onă Gaksamipỏpỏ" --lang asaxi    # Asaxi
python synth_diphone.py "konnichiwa"       --lang ja      # Japanese
```

Handy options:

```
--lang en|asaxi|ja     language (default: festvox.json "default_lang", = en)
--speed 1.5            pace: >1 faster, <1 slower (default: "synth_speed", = 1.0)
--voice asaxi_lem      pick a voice from festvox.json
--db  "E:/…/some_db"   use a DB directly, ignoring the config
--outdir "E:/…/clips"  where to write (default: synth_output_dir)
--out  "hi.wav"        exact output filename
--config "…/festvox.json"   use a specific config
```

**Speed** is concatenative, not time-stretch: it changes how much of each
recorded phone is used, so it never alters pitch. Faster (`>1`) always works;
slowing (`<1`) is capped by how much audio was actually recorded per phone.
`--speed` overrides the config's `synth_speed` for that one call. Works the
same in `python vocab_forge.py synth … --speed 1.5` and the API
(`/api/synth?…&speed=1.5`).

It prints the phones used, the diphones chosen, and anything skipped (should
be empty), then writes the `.wav`.

### Inside vocab_forge

```
python vocab_forge.py synth "real isn't how you are made"   # English (default)
python vocab_forge.py synth "kozèvkozè" --lang asaxi
```

Or in the web UI's **Anki assets** panel (Add / Edit tabs) press **♪ synth**
on a word or sentence row to render and store the clip on the card (that
button always renders the Asaxi lexeme).

### Languages

- **English** (default) — CMU dictionary; run `pip install cmudict` once.
- **Asaxi** (`--lang asaxi`) — rule-based from *00_Phonemes of the Asaxi
  Language*; no extra library.
- **Japanese** (`--lang ja`) — kana **or** Hepburn romaji, via
  `en-jap-mapping.yaml` in this folder; no extra library. Kanji is not
  handled (needs a morphological analyzer — see `MULTISYN.md`).

Change the everyday default by editing `default_lang` in `festvox.json`.

> **Upgrading to natural (unit-selection) speech?** This tool is *diphone*
> synthesis. For the Multisyn upgrade — how much speech to record, Audacity
> vs `oto.ini` labelling, the recording/boundary protocol, and the
> `corpus_extract.py` / `labels2festvox.py` tools — see **`MULTISYN.md`**.

---

## 6. Rebuilding & adding voices

- **Re-recorded the same bank?** Just run `python utau2festvox.py` again — it
  remeasures every wav and overwrites the DB.
- **A whole new voice?** Add another entry under `voices` in `festvox.json`
  (its own `bank`, a unique key) and build. It lands in
  `output_root/<new key>`. Point `festvox_db` (vocab_forge) or `--voice` at it.

---

## 7. Adding or remapping phonemes

Open the **`PHONEME_MAP`** block at the top of `utau2festvox.py`. Keys are
alias *tokens* (the pitch tag is stripped, the alias split on spaces):

```python
PHONEME_MAP = {
    "-": "pau",              # silence
    "inh": None, "exh": None, # excluded (breaths)
    "k": "k", "a": "a", ...   # map a token to a Festival phone name
}
```

Rules of thumb:

- Unlisted plain-ASCII tokens map to **themselves**, so you only add entries
  for special cases.
- Numbered takes (`aa2`, `ah11`) collapse to their base (`aa`, `ah`)
  automatically.
- Map a token to `None` to **exclude** it (breaths, noise).
- After editing, **rebuild** (Step 3) and re-check the report.

The renderer also has acoustic **fallbacks** (`synth_diphone.py`): missing
`k i` is covered by `k iy` (arpasing convention), Japanese-style CV units fill
other gaps. That's why the test set synthesizes with **0 skipped diphones**
even though not every pair was recorded — but recording the real diphone
always sounds better than a fallback.

---

## 8. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `No festvox.json found` | run from `99_Tools\festvox\`, or pass `--config PATH`, or set `FESTVOX_CONFIG`. |
| `No diphone DB found` (renderer) | build it first (Step 3); check the path in `festvox_db` / `festvox.json` actually exists. |
| Lots of `unmapped tokens` | your bank uses phones not in `PHONEME_MAP` — add them (§7) and rebuild. |
| `bad oto lines` non-empty | malformed oto lines, or a `Blank` sign that made `end ≤ mid`. See the timing note in `utau2festvox.py`. |
| English says `not in CMU dictionary` | that word isn't in cmudict; try another, or spell it phonetically. |
| Robotic / clipped pacing | tune `HALF_MS` (phone length) and `CROSSFADE_MS` at the top of `synth_diphone.py`. |
| Want a real Festival binary voice | use `dic/asaxi_diphone.est` + `festival/…_stub.scm` and run FestVox's `make_lpc` over `wav/`. |

---

## 9. Appendix — how the timing conversion works

UTAU stores **relative milliseconds**; FestVox needs **absolute seconds** with
three points per diphone: where the first phone starts, the boundary between
the two phones, and where the second phone ends.

```
start = Offset
mid   = Offset + Preutterance          (UTAU's alignment point = the boundary)
end   = Offset + |Blank|   if Blank < 0     (length measured from the offset)
      = file_length - Blank if Blank ≥ 0    (milliseconds trimmed off the end)
```

The builder opens each `.wav` with Python's `wave` module to measure
`file_length`, which is the only way to resolve the negative-`Blank` case. It
verifies `start < mid < end` for every entry; anything that fails is reported
as a bad line rather than silently producing garbage audio.

> Note: this bank uses standard UTAU `Blank` semantics (negative = length from
> offset). The math is documented at the top of `utau2festvox.py`.

---

## Old database cleanup

An earlier build left a `festvox_db` folder **inside** the voicebank
(`D:\UTAU\voice\Lem_V4Bi_Civet\4_Fis3\festvox_db`). Nothing points at it
anymore — you can safely delete that folder; the live database is now in
`E:\Portable_Software\FestVox_DBs\asaxi_lem`.
