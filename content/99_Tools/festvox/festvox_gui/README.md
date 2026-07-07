# Festvox Speech Synthesis GUI (PyQt5)

A Windows-XP-styled desktop front-end for a Festival / Festvox backend:
generate speech, then edit it on a waveform with draggable phoneme boundaries,
editable phoneme fields, and a Vocaloid-style velocity envelope.

## Files
- `festvox_core.py` — no-Qt backend: config, **real Festival** synthesis +
  phoneme-segment extraction, demo fallback, time-stretch DSP, WAV/project IO.
- `festvox_gui.py` — the PyQt5 + PyQtGraph GUI.
- `config.json` — Language / Voicebank menus + Festival voice mapping.

## Install & run
```bash
pip install PyQt5 pyqtgraph numpy
pip install sounddevice        # optional, best playback (else Qt Multimedia)
pip install librosa            # optional, higher-quality time-stretch
python festvox_gui.py
```
Festival itself must be on your PATH for real synthesis (Linux: `apt install
festival festvox-kallpc16k`). **Without Festival the app still runs** — it
falls back to a synthetic demo waveform so you can try the editor immediately.

## Pointing it at your existing voicebanks
Use the **Voicebank** menu (all changes are saved back to `config.json`):

- **Scan installed voices (Festival)** — runs `(voice.list)` and adds every
  voice Festival already knows about to the Voicebank list.
- **Add voice folder...** — browse to a built festvox / Multisyn voice
  directory (the folder that contains `festvox/`). The app reads
  `festvox/*.scm`, auto-detects the `voice_*` function, and at synth time puts
  that folder on Festival's `load-path` and `(load ...)`s its `.scm` — so it
  works even for voices that are **not** installed system-wide.
- **Set Festival binary...** — point to your `festival` executable if it is not
  on PATH.

You can also edit `config.json` by hand. Each `festival.voice_map` value is
either a function name string, e.g.
`"kal_diphone": "voice_kal_diphone"`, or a directory voice:
```json
"my_multisyn": {
  "dir": "/home/you/data/cmu_us_myvoice",
  "voice": "voice_cmu_us_myvoice_multisyn",
  "scm": "festvox/cmu_us_myvoice_multisyn.scm"
}
```
`festival.bin` is the path to the `festival` binary if not on PATH.

Under the hood, "Generate Audio" runs (in batch mode):
```scheme
(voice_kal_diphone)
(Parameter.set 'Duration_Stretch <1/speed>)
(set! u (SynthText "your text"))
(utt.save.wave u "out.wav")
(utt.save.segs u "out.seg")
```
and parses the label file into phoneme segments.

## What you can do
- **Generate Audio** — synth the Text box with the selected voice/speed.
- **Waveform** — blue waveform; **red dashed lines are draggable** phoneme
  boundaries. Drag one and that segment is time-stretched (real phase-vocoder
  DSP in `festvox_core.time_stretch`, or librosa if installed) and the view
  redraws. Swap the DSP by passing a `hook` to `time_stretch`.
- **Phoneme fields** — the boxes under the waveform are width-aligned to each
  segment; edit one to override the phoneme (e.g. `[R]` → `[RR]`). Stored in the
  project and used as the phoneme label.
- **Phoneme Velocity** — drag the orange keyframe nodes to draw a parameter
  curve over the timeline (X-aligned to the waveform); double-click the track to
  add a node.
- **Play / Stop / Export WAV / Save+Open Project** — as labelled.

## Notes / extension points
- Boundary drags edit *output* timing via time-stretch. To instead re-time at
  synthesis, feed target durations back through Festival's `Duration` relation
  and re-synth (hook in `on_generate`).
- The velocity envelope is captured (`EnvelopeGraph.nodes()`); map it to F0,
  gain, or a Festvox parameter in your backend as needed.
