# Festvox Speech Synthesis GUI (PyQt5)

A Windows-XP-styled desktop front-end for **`synth_diphone.py`** — the
pure-Python concatenative diphone engine in `99_Tools/vocab_forge/`. It renders
from the FestVox-style DBs built by `utau2festvox.py` (`dic/diphone_index.json`
+ `wav/`). **No Festival binary is involved** — everything runs on plain
Windows Python.

## Files
- `festvox_gui.py` — the PyQt5 + PyQtGraph GUI.
- `festvox_core.py` — no-Qt glue: imports `synth_diphone.py`, reads
  `festvox.json` for voices, velocity/gain DSP, time-stretch, WAV/project IO.
- `config.json` — GUI settings (see below). Written back automatically.

## Install & run (Windows)
```bat
pip install PyQt5 pyqtgraph numpy
pip install sounddevice   :: optional, best playback (else winsound is used)
pip install librosa       :: optional, higher-quality time-stretch
pip install cmudict       :: only needed for the English front end
python festvox_gui.py
```

## Where everything comes from
- **Engine** — `synth_diphone.py` is auto-found in `99_Tools/vocab_forge/`.
  If you move things, set it via *Options → Locate synth_diphone.py...*
  (stored as `synth_diphone_dir`).
- **Voicebanks** — read from the toolchain's `festvox.json` (`voices` +
  `output_root`, e.g. `asaxi_lem → E:/Portable_Software/FestVox_DBs/asaxi_lem`).
  `festvox.json` is auto-discovered (cwd, next to `synth_diphone.py`,
  `99_Tools/festvox/`); override via *Voicebank → Set festvox.json...*.
  Add any other DB folder with *Voicebank → Add voicebank folder...* — it must
  contain `dic/diphone_index.json`. Broken paths show red "(missing)" with the
  reason in the tooltip.
- **Languages** — the engine's real front ends:
  - **Asaxi** — grapheme→phone rules from the phoneme chart (romanization).
  - **English** — CMU dictionary lookup (`pip install cmudict`); words not in
    the dictionary are reported by name.
  - **Japanese** — kana or Hepburn romaji via the OpenUTAU mapping
    (`en-jap-mapping.yaml`, found next to the engine or in `99_Tools/festvox/`).

## What you can do
- **Generate Audio** — g2p the Text box, pick diphones, concatenate with
  crossfades. The status bar shows phones/diphones/duration and any **missing
  diphones** the bank couldn't supply (details: *Generate → Last render
  details...*).
- **Waveform** — red dashed lines are **real phone boundaries** (from each
  diphone's indexed `mid` point). Drag one and that segment is time-stretched
  (librosa or the built-in phase vocoder; swap DSP via the `hook` parameter of
  `festvox_core.time_stretch`).
- **Phoneme fields** — width-aligned to each segment. Type a different phone
  (e.g. `r` → `rr`), space-separate to insert phones, clear a box to delete
  one, or type `pau` for a mid-word pause. Edited boxes turn yellow; **Enter**
  or **Re-render Phonemes** feeds the edited list straight back through the
  engine. Gray `pau` boxes are the engine's edge silences.
- **Speed** — x0.25–x4 (the engine's actual range). Concatenative pacing: it
  scales how much of each recording is kept, so pitch never changes; slowing
  below ~x1 is capped by what was recorded.
- **Phoneme Velocity** — a gain envelope over the timeline. 0.5 = unity,
  1.0 = louder, 0.0 = silent (scaled by *velocity depth*). Double-click to add
  a node, right-click to remove, drag to shape. Applied on Play/Export when
  *Options → Apply velocity on play/export* is checked.
- **Play / Stop** — sounddevice if installed, else `winsound` (built into
  Windows Python), else Qt Multimedia.
- **Export WAV** — defaults into `festvox.json`'s `synth_output_dir` with an
  auto filename like the CLI's (`asaxi_taki.wav`).
- **Save/Open Project** — text, language, voicebank, speed, the (edited)
  phone list, segments, and velocity nodes. Opening re-renders the saved
  phones, so phoneme overrides survive; boundary re-timings are not re-applied.

## Advanced settings (Options menu)
These map 1:1 to the engine's real knobs (`synth_diphone.py` constants),
applied on every render and saved to `config.json`:

| Setting | Engine constant | Meaning |
|---|---|---|
| Diphone crossfade (ms) | `CROSSFADE_MS` | equal-power join at each seam |
| Utterance edge fade (ms) | `EDGE_FADE_MS` | de-click fade at the ends |
| Phone window (ms/side) | `HALF_MS` | max audio kept per side of each boundary; the speed slider divides this |
| Velocity depth (0–1) | — | how strongly the envelope scales gain |

## config.json keys
`festvox_config` (path to festvox.json, `""` = auto), `synth_diphone_dir`
(`""` = auto), `languages` (label → engine code), `default_language`,
`default_text`, `extra_voicebanks` (name → DB dir, filled by *Add voicebank
folder...*), `synth_speed`, `advanced` (table above), `apply_velocity`,
`velocity_depth`. Every key is settable from the GUI; the file is saved on
change and on exit.

## Troubleshooting
- **"synth_diphone.py not found"** — *Options → Locate synth_diphone.py...*
- **Voicebank red "(missing)"** — the DB path in `festvox.json` /
  `config.json` doesn't contain `dic/diphone_index.json`; fix the path or
  re-run `utau2festvox.py`.
- **"not in CMU dictionary: [...]"** — English front end; `pip install
  cmudict`, and only dictionary words synthesize.
- **Missing diphones in the status bar** — the bank has no unit for that
  transition; the engine skips it (same behavior as the CLI). Check the phone
  spelling against the bank's phone set.
- Engine change note: `synth_diphone.render()` now also returns per-phone
  `"segments"` timing (used for the boundary overlay). Additive — the
  vocab_forge CLI/HTTP callers are unaffected.
