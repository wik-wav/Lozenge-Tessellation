# UTAU → FestVox diphone conversion + diphone synthesis

> **Diphone build & synth:** see [GUIDE.md](GUIDE.md) for the full
> record → configure → build → synthesize process.
> **Multisyn (unit-selection) upgrade:** see [MULTISYN.md](MULTISYN.md) —
> data budget, Audacity-vs-oto assessment, recording/boundary protocol, and
> the `corpus_extract.py` (recording-script) + `labels2festvox.py` (label) tools.
> **Languages:** default is **English**; `--lang asaxi|en|ja` per call (Japanese via `en-jap-mapping.yaml`).

Turns the **Lem 4_Fis3** UTAU voicebank into a FestVox-style diphone database,
and lets `vocab_forge` speak Asaxi (and English, for testing) from it — no
Festival runtime required.

## 1. Build the database

Config-driven (paths live in `festvox.json`):

```
python utau2festvox.py                     # build every voice in festvox.json
python utau2festvox.py --voice asaxi_lem   # just one
```

One-off (no config):

```
python utau2festvox.py --bank "D:/UTAU/voice/…/4_Fis3" --out "E:/…/FestVox_DBs/asaxi_lem" --name asaxi
```

Databases build to `output_root/<voice>` (default `E:/Portable_Software/FestVox_DBs/…`),
**outside** the voicebank. Each DB dir contains:

```
wav/                         renamed 16-bit source wavs (Scheme-safe names)
dic/asaxi_diphone.scm        Festival index list  (diphone wav start mid end)
dic/asaxi_diphone.est        EST_File index       (for UniSyn / make_lpc)
dic/diphone_index.json       machine index used by the synthesizer
festival/asaxi_diphone_stub.scm   minimal UniSyn voice scaffold
conversion_report.txt        unmapped tokens, variant dupes, bad lines
```

On this bank: **4252 diphones** from 734 wavs, 0 missing, only `-aw11`
(a malformed alias) left unmapped.

### Timing conversion

UTAU stores relative-ms values; FestVox needs absolute seconds:

| FestVox | from UTAU |
| --- | --- |
| **start** | `Offset` |
| **mid** (phone boundary) | `Offset + Preutterance` |
| **end** | `Offset + |Blank|` if `Blank < 0`, else `file_length − Blank` |

The `wave` module measures each file so the negative-`Blank` case (length
measured *from* the offset) is computable at all. Every produced triple
satisfies `start < mid < end`.

> Note: the brief stated the inverse `Blank` sign convention. On this bank's
> real data the inverse overruns the following diphone by whole seconds, so
> standard UTAU semantics are used (documented at the top of the script).

## 2. Defining the phoneme dictionary

Edit **`PHONEME_MAP`** at the top of `utau2festvox.py`. Keys are UTAU alias
*tokens* (the pitch tag like `F#3` is stripped, then the alias is split on
spaces — `"k a F#3"` → tokens `k`, `a`).

- `"k": "k"` — map a token to a Festival phone name (diphone `k-a`).
- `"-": "pau"` — silence.
- `"inh": None` — exclude (breaths, etc.).
- `"b-"` (trailing dash) → word-final allophone `b_`, kept distinct.
- Unlisted plain-ASCII tokens map to themselves; numbered takes (`aa2`,
  `ah11`) collapse to their base symbol automatically.

Everything is sanitized to valid Scheme atoms (ASCII-folded, `[A-Za-z0-9_]`).

## 3. Speaking from vocab_forge

`vocab_forge/config.json` points at the DB (already set):

```json
"festvox_db": ["E:/Portable_Software/FestVox_DBs/asaxi_lem"]
```

Render — standalone (reads `festvox.json`) or via vocab_forge:

```
python synth_diphone.py "Onă Gaksamipỏpỏ"              # standalone, Asaxi
python synth_diphone.py "the velveteen rabbit" --lang en --outdir clips
python vocab_forge.py  synth "Onă Gaksamipỏpỏ"         # via vocab_forge
```

or in the web UI's **Anki assets** panel (Add & Edit tabs) press **♪ synth**
on the *word* or *sentence* audio row to render and store the sample.

Front ends (`synth_diphone.py`):
- **Asaxi** — romanization→arpasing rules from *00_Phonemes of the Asaxi
  Language* (gemination → held `cl`, `C+y` palatal units, digraphs).
- **English** — CMU dictionary (`pip install cmudict`), stress stripped;
  works because the bank is arpasing.

The renderer is pure-stdlib concatenation: it cuts each diphone around its
`mid` boundary (±150 ms), equal-power crossfades the seams, de-clicks the
edges and peak-normalizes. Vowel-quality and Japanese-CV fallbacks cover the
few gaps in the diphone matrix (verified: 0 skipped diphones across the test
set).
