---
title: Asaxi Prosody Recording Corpus
tags:
  - Asaxi
  - language
  - prosody
  - corpus
  - recording
---
# Asaxi Prosody Recording Corpus

Navigation:
- [[The Asaxi Language|The Asaxi Language Index]]
- [[61_Prosody, Stress & Intonation|Prosody, Stress and Intonation]]
- [[onă gaksamipỏpỏ (Reader's Text)|Clean reader text]]
- [[onă gaksamipỏpỏ (The Velveteen Rabbit)|Interlinear reader text]]

The generated recording corpus turns the current Asaxi dictionary, grammar
examples, dated elicitation controls, and reader text into a reproducible set
for measuring timing and prosody. It is stored at:

`99_Tools/festvox/corpora/asaxi-prosody-v1`

The human-readable entry point is `reader_corpus.md`. Each item contains:

1. plain Asaxi text to read aloud;
2. an English translation, or a clearly labeled broader source context where
   the source paragraph cannot be split safely;
3. one pitch-accent row per written word;
4. the dictionary or fixed-expression H/L pattern;
5. the current model's utterance-level H/L prediction;
6. separately labeled attested or dictionary reference evidence;
7. an explicit agreement result, source provenance, and any review warning.

H and L label relative mora-level pitch targets. They are not exact
frequencies. A lexical pattern and its sentence realization can differ because
of phrase accent, downstep, focus, deaccenting, or a boundary tone.

## Annotation authority

The manifest keeps prediction and evidence separate.
`pitch_analysis.predicted` always means output from the current rules.
`pitch_analysis.reference.authority: attested` means the reading was
transcribed from the dated elicitation appendix. `dictionary` means the
reference is lexical or fixed-expression data rather than an utterance
recording. The agreement record states which layer was compared.
`model_hypothesis` means the current rules generated the reading and it still
requires recording or linguistic review.

Unknown inflected forms and ambiguous homographs remain marked in the corpus.
They are not silently accepted as ground truth.

The initial model matches all 11 dated controls whose reference has the same
number of H/L values as the written form. The shorthand references for
<span class="asaxi-text">ŕoŕo daohè!</span> and
<span class="asaxi-text">haśùnáhè!</span> each omit one mora-level value, so
they remain preserved and visibly marked `mora_count_mismatch`.

## Recording and alignment

Record the Asaxi line only; the English translation is context and should not
be spoken. Keep microphone position, speaking voice, room, sample rate, and
gain stable. Use the requested recording ID as the WAV basename.

Keep the unedited recording. Store corrected word, mora, and phone boundaries,
measured F0, and review decisions as separate annotation layers linked by the
stable recording ID. This makes it possible to compare later models against
the same speech rather than replacing the evidence.

The corpus is material for fitting and validating a prosody model. Its
existence does not by itself verify acoustic timing, pitch realization, or
naturalness.
