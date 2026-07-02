# Asaxi Vocab Forge

A local form UI + API for adding vocabulary to the Asaxi lexicon without breaking anything. Pure Python standard library — nothing to install except Python itself.

## Run it

1. Install Python 3.9+ (python.org) if you don't have it.
2. Open a terminal in this folder and run: `python vocab_forge.py serve`
3. Open http://127.0.0.1:8766 in your browser.

## What it does

Three tabs: **Add new** (the full form), **Edit** (open any existing entry, edit per section), and **Search** (browse the whole corpus with filters for word type and semantic field, free-text search over words and translations, and sorting A→Z / Z→A / least- or most-complete-first / by type). Every entry gets a **completion score**: the share of its fields holding real content rather than `x`/`Null`/empty — the Search tab shows it as a bar, the Edit tab lists exactly which fields are missing. Edits are surgical (only changed sections are rewritten; the rest of the note is untouched) and changing an English translation auto-syncs the entry's line in list files and semantic-field pages.

- **Form per word type** — noun, root verb, -ů verb, adjective, root word, ga-noun, particle, number; fields mirror `00_Templates` exactly.
- **Live validation** — Asaxi alphabet check (no plain u/y/q…), duplicate blocking, near-duplicate warnings, and full **phonotactics from `22_Phonotactics & Euphony`**: no plosive codas, no word-final `lv`/`lm`, `l` never after impure vowels, `r` cluster rules (only after ch/jh/k/f/p, never before i except *fri*, never with glides), vowel-nucleus requirement, `-nýj` coda allowed, and the Rule 22.A `-n-` bridge check for noun→-ů-verb derivations. A rule-breaking word can still be added deliberately via the override checkbox (recorded with `--force` semantics).
- **Obsidian-style links** — type `[[` in any text field to get vault-wide note completion, exactly like in Obsidian (arrows + Enter/Tab, Esc to cancel).
- **Auto-IPA** — the `auto` button fills the IPA field from the romanization (palatalization/labialization/gemination rules applied); edit freely afterwards.
- **Thesaurus synonyms/antonyms** — `auto (thesaurus)` matches your EN/PL translations against a built-in bilingual thesaurus plus direct gloss overlap, and finds the corresponding Asaxi words in the vault. Candidates appear as dashed suggestion chips — click one to approve it into the field (hover to see *why* it matched). Editing a translation clears stale suggestions.
- **Derived terms, automatically** — entries you `[[link]]` in the Etymology (and the Root noun field) get the new word appended to *their* “Derived terms” section on commit. Retroactive pass for the whole lexicon: `python vocab_forge.py backfill-derived` (dry-run; add `--commit` to apply). Only morphologically contained bases count (contrast links are ignored).
- **List updates** — type list + semantic-field files, inserted next to semantic siblings when possible, else under `### New additions (unsorted)`; idempotent.
- **Nothing is written blind** — Preview shows the entry file and every planned vault edit first.

### Newer features

- **Link health** — every `[[link]]` shown in previews and under Edit-tab sections is colored: green = target note exists, red dashed = broken. 
- **Edit tab** — Preview button renders the note with pending edits applied (dry-run, nothing written); ✕ deletes a section (with confirmation); "Delete entry…" removes the file *and* scrubs its list/semantic-field lines after a confirmation that lists exactly what goes. The status panel flags **nonstandard fields** (sections not in the type's template) as well as missing ones.
- **Local LLM (Ollama / LM Studio), redone** — no more free-text suggestion buttons. Now: `refine ✦` next to the English translation does a reverse-dictionary lookup on what you typed ("thoughtless superficiality" → *glib*, click to replace); `LLM ✦` next to each thesaurus button asks for synonyms/antonyms of your EN+PL translations and matches them against the lexicon, feeding the same suggestion chips. Every button's tooltip states its exact function; prompts demand comma-separated-words-only output (tuned for small models like Gemma 4B) and the parser salvages format drift.
- **Anki assets** — in the Edit tab, "Check Anki assets" (opt-in) shows whether `anki-assets/` has this word's image, word audio (`asaxi-<word>-a1.mp3`), and sentence audio (`-a2.mp3`). Record straight from the browser (permission prompt is the browser's own; a device picker is provided since browsers don't always offer one) — audio is encoded to mp3 in the page (falls back to webm/ogg if the encoder CDN is unreachable). Images upload via a button and are auto-converted to JPEG 90% unless already JPEG (`asaxi-<word>-image.jpg`).
- **Two scripts** — every entry and template now carries both `asaxi-script` (abugida) and `asaxi-script-alpha` (alphabet) spans; the snippet CSS defines the new class (placeholder font — edit `.obsidian/snippets/fonts.css` when you have real fonts).
- **Anki deck builder** — `build_anki_deck.py` (separate script, needs `pip install genanki`): front = the word in abugida/alphabet/Latin; back = both audios, both scripts, example sentence in all renderings, translations, image. Drop `AsaxiAbugida.ttf` / `AsaxiAlpha.ttf` into `anki-assets/fonts/` to embed real script fonts. `--require-audio` limits to recorded words.

## Files

`vocab_forge.py` (server+CLI) · `forge_core.py` (engine) · `ui.html` (form) · `thesaurus.json` (EN/PL synonym & antonym data — extend freely) · `config.json` · `AGENTS.md`

## Notes

- Lexicon is re-indexed per request; edits made in Obsidian are picked up immediately.
- Known corpus anomalies the validator would reject today: `kupù` (plain u), `mỳdo`/`mỳdonů`/`xỳ` (ỳ), `dok` (plosive coda), `mëjox` (x coda) — plus filename-type inconsistencies like `(Noun)`, `(nouns)`, `(Root Word)`. Left untouched; rename them if/when you wish.
