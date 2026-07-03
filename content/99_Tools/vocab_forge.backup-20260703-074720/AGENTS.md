# Agent guide — Asaxi Vocab Forge

How AI agents should add vocabulary to this vault. **Do not write lexicon `.md` files by hand** — use this tool so validation, linking, list updates and derived-terms propagation stay consistent.

## CLI (no server needed; run from this folder, `python3` in sandboxes)

```
python vocab_forge.py schema                  # payload contract
python vocab_forge.py fields                  # valid semantic field names
python vocab_forge.py search <query>
python vocab_forge.py validate <word> <type>  # charset + duplicates + phonotactics
python vocab_forge.py thesaurus --en "joy" --pl "radość"   # synonym/antonym candidates
python vocab_forge.py add --json payload.json            # dry-run preview
python vocab_forge.py add --json payload.json --commit   # write to vault
python vocab_forge.py backfill-derived [--commit]        # retro-fill Derived terms from etymologies
```

## HTTP (when `serve` runs, default http://127.0.0.1:8766)

```
GET  /api/meta /api/schema /api/search?q= /api/links?q=
GET  /api/browse?q=&type=&field=     corpus listing + completion scores (pct of filled fields)
GET  /api/entry?name=<stem>          entry sections + score for editing
GET  /api/infixes                    morphological infixes from the 06A_ notes
POST /api/validate /api/preview /api/commit /api/thesaurus /api/suggest /api/morphcheck
POST /api/entry_update               surgical edit: {name, frontmatter:{gloss_en,gloss_pl}, sections:[{header,content} | {header,delete:true}], dry_run} -> includes resulting "text"
POST /api/entry_delete               {name, dry_run} -> removes file + scrubs list lines; ALWAYS dry_run first, needs human approval
POST /api/linkcheck                  {names:[..]} -> which [[targets]] exist in the vault
POST /api/llm_refine                 {text, lang} -> reverse-dictionary word options (local LLM)
POST /api/llm_related                {mode: synonyms|antonyms, gloss_en, gloss_pl} -> LLM words matched to lexicon
GET  /api/anki_status?word=          image/a1/a2 asset presence   ·   GET /api/asset?name=  serves them
POST /api/asset_upload?name=asaxi-<word>-{image.jpg|a1.mp3|a2.mp3}   raw-body upload
```
`get_entry` responses include an `audit` (nonstandard sections vs the type template).
Deck building: `python build_anki_deck.py --out Asaxi.apkg` (requires genanki).
`entry_update` rewrites only the given sections (unknown headers are appended); a gloss_en change
auto-syncs the entry's lines in list/semantic-field files. Always dry_run first.
`/api/links` powers Obsidian-style [[link]] completion (vault-wide note stems).
`preview`/`commit` accept `"force": true` to override validation errors — only with explicit human approval.

## Payload (same for validate/preview/commit)

```json
{
  "word": "mmbăŕo", "type": "noun", "gloss_en": "festival ground",
  "gloss_pl": "", "ipa": "", "noun_class": "Warm",
  "transitivity": "", "lexical_aspect": "", "animate": "",
  "grammatical_function": "", "particle_type": "", "number_value": "",
  "semantic_fields": ["Smntc_Field The City"],
  "example": "", "example_gloss": "",
  "etymology": "From [[mmbă (noun)|mmbă]] + [[ŕo (root word)|ŕo]]",
  "alt_forms": "", "root_noun": "", "usage_note": "",
  "synonyms": [], "antonyms": [], "derived": [],
  "vocab_expansion_tag": true
}
```

Types: noun | verb-root | verb-u | adjective | root-word | ga-noun | particle | number.

## Required workflow

1. `search` the word and meaning; use `thesaurus` to find related existing words to cross-link.
2. `validate` — fix all errors (phonotactics cite the rule doc); heed near-duplicate warnings.
3. `add` (dry-run) — inspect the markdown AND the planned vault updates (lists, semantic fields, Derived-terms backlinks).
4. `add --commit` when right. Never `--force` without the human's explicit approval.

## Enforced guarantees

- Asaxi-alphabet charset (no plain u/y/q); phonotactic constraints per `22_Phonotactics & Euphony`.
- No silent overwrites; idempotent list/derived updates (already-present lines are never duplicated).
- Entries generated from the vault's own templates.
- Etymology `[[links]]` to existing entries (when the base is contained in the new word) auto-append the new word to those entries' Derived terms.
