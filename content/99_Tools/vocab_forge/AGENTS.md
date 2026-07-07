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
POST /api/entry_rename               {name, new_name, dry_run} -> renames the file + repoints every [[backlink]] vault-wide (target + matching alias) and fixes the note's own title/heading/Word/script spans; ALWAYS dry_run first
POST /api/rebuild_lists               {dry_run} -> fill + Latin-sort every category List; ga-noun list grouped by the ga-literal/ga-idiomatic tag. CLI: `python vocab_forge.py rebuild-lists [--dry-run]`
POST /api/rank_frequency              {dry_run} -> stamp freq: (1-100) on entries lacking it via wordfreq on single-word glosses (Swadesh/LJ boosted); never overwrites. CLI: `python vocab_forge.py rank-frequency [--dry-run]`
POST /api/llm_frequency               {gloss_en, gloss_pl, usage_note} -> {freq} everyday-frequency estimate (1-100) from the local model
POST /api/linkcheck                  {names:[..]} -> which [[targets]] exist in the vault
POST /api/llm_refine                 {text, lang} -> reverse-dictionary word options (local LLM)
POST /api/llm_related                {mode: synonyms|antonyms, gloss_en, gloss_pl} -> LLM words matched to lexicon
GET  /api/anki_status?name=<stem>    image/a1/a2 asset presence (or ?word=)  ·  GET /api/asset?name=  serves them
POST /api/asset_upload?name=<stem>&slot={image|a1|a2}&ext=<ext>   raw-body upload; on first use the
                     server stamps a permanent `id:` into the entry's front matter and writes <id>-asaxi-<word>-<slot>.<ext>
```
`get_entry` responses include an `audit` (nonstandard sections vs the type template).
Deck building: `python build_anki_deck.py --out Asaxi.apkg` (requires genanki). Cards are keyed by the entry `id` (falls back to word+type when absent), so word renames update the same card.
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
  "ga_kind": "Literal|Idiomatic",  // ga-noun only -> adds ga-literal/ga-idiomatic tag
  // freq: 1-100 lives in front matter (deck/sort order); set via Edit tab or rank-frequency, editable by hand
  "vocab_expansion_tag": true
}
```

Types: noun | verb-root | verb-u | adjective | root-word | ga-noun | particle | number | idiom.
Idioms are saved to `Idioms_Expressions/` (scanned alongside the Lexicon); charset/phonotactic checks are skipped for them. Idiom payloads may add `structure` and `index_page` (header-link target, e.g. `45_Idioms & Fixed Expressions` or `63_Social Formulae ...`).

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

## Polysemy standard (multiple meanings, one file)

All meanings of a word live in **one** entry `.md`. Each sense produces its **own Anki card**, so the format is strict:

- **Frontmatter:** sense 1 uses the legacy keys (`trnsltion. En:` / `trnsltion. Pl:`); every further sense adds numbered keys, in order:
  ```
  trnsltion. En: the right time
  trnsltion. Pl: we właściwy czas
  trnsltion. En 2: just then, at that very moment
  trnsltion. Pl 2: właśnie wtedy
  ```
- **Body:** sense 1's example stays in the legacy `### Example sentence` field; each sense N ≥ 2 gets exactly one `### Example Sentence N` field. **No fluff in example fields** — exactly the sentence and its translation:
  ```
  ### Example Sentence 2

  > **Ămă Nana xő zèxijpù.**
  > "Just then Nana caught sight of him."
  ```
  Commentary, sense discussion and source attributions belong in `### Usage Note`.
- **Payloads:** new polysemous entries pass senses ≥ 2 as `"senses": [{gloss_en, gloss_pl, example, example_gloss}, ...]` (sense 1 = the top-level fields). `entry_update` accepts numbered frontmatter keys: `{"frontmatter": {"gloss_en_2": "...", "gloss_pl_2": "..."}}`; example fields are ordinary sections (`{"header": "Example Sentence 2", "content": "> **...**\n> \"...\""}`).
- **Adjacency rule:** all sense machinery stays grouped in the file — the numbered `trnsltion.` lines sit together in the frontmatter, and every `### Example Sentence N` field sits directly after the previous example field (never separated by unrelated sections). `build_entry`, `entry_update` and the web UI all enforce this placement automatically.
- **Web UI:** both the **Add** and **Edit** tabs have a **“+ add sense”** button (arbitrarily many senses). Add tab: each sense row = EN/PL glosses + example + translation. Edit tab: the sense row holds the glosses, and its `Example Sentence N` field appears among the section editors, docked next to the other example fields; the ✕ on a sense removes its gloss lines and its example field on Save.
- **Deck builder:** `build_anki_deck.py` emits one note per sense. Card front = word + that sense's example sentence (the example disambiguates the sense); back = that sense's meaning + example translation. Sense 1 keeps the entry's legacy guid (scheduling history survives renames *and* the polysemy migration); senses ≥ 2 get `<id>::sN`. A sense without an example gets no card — always supply one.

## Diphone synthesis (Lem 4_Fis3 voice)

`synth_diphone.py` renders audio from the FestVox diphone DB built by
`../festvox/utau2festvox.py`. Set `config.json` → `"festvox_db"` to the
`festvox_db` folder (path or list of candidates; first with
`dic/diphone_index.json` wins).

- **CLI:** `python vocab_forge.py synth "<text>" [--lang asaxi|en] [--out f.wav]`
- **HTTP:** `GET /api/synth?text=&lang=` → `audio/wav`;
  `POST /api/synth_asset {name|word, slot:a1|a2, lang, text?}` renders and
  saves into the entry's Anki asset slot (a2 defaults to the entry's sense-1
  example sentence; a1 defaults to the word).
- **UI:** “♪ synth” button on each audio row of the Anki-assets panel.
- Asaxi g2p follows *00_Phonemes of the Asaxi Language*; English uses
  `cmudict` (arpasing). Pure stdlib otherwise.

