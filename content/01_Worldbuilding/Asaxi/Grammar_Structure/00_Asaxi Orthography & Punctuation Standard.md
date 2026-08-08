---
title: Asaxi orthography and punctuation standard
tags:
  - Asaxi
  - language
  - orthography
  - style_guide
---
# Asaxi Orthography and Punctuation Standard

This page is the normative writing standard for Asaxi text in the vault,
Vocab Forge, Anki exports, and other generated material.

## Letter Case

Asaxi common vocabulary and grammatical material are written in lower case.
Sentence beginnings, quoted speech, headings written in Asaxi, example
sentences, and isolated common words do not receive automatic capitalization.

The following lexical categories are written in **full capitals**:

- proper nouns and proper names, including personal names;
- place names;
- borrowed terms.

This is whole-token capitalization rather than English-style title case.
Every letter with a case distinction is capitalized, while diacritics and the
phonemic glottal-stop apostrophe are preserved. For example, a personal name
is written `JOHN`, not `John`, and the borrowed term `mimi` is written `MIMI`.
Productive Asaxi material attached within the same orthographic word follows
the word's capital treatment. Mixed-case Asaxi words are therefore
non-standard.

The English proper name **Asaxi** keeps its capital letter when it occurs in
English prose. As a proper name in Asaxi text, it is written `ASAXI`.

Upper-case interlinear gloss abbreviations such as `TOP`, `PST`, and `SOV`
belong to the metalanguage, not to Asaxi orthography, and remain upper case.

## Quotation Marks

Asaxi follows Polish quotation-mark typography:

- primary quotation: `„…”`;
- quotation nested inside a quotation: `‚…’`.

The guillemet forms formerly used in some notes are not part of the Asaxi
standard.

The straight apostrophe `'` is not a quotation mark in Asaxi. It represents
the phonemic glottal stop /ʔ/ and must not be converted to a curly apostrophe.

Example:

- **Asaxi:** no pă „wo pỏpỏ ma, ‚nă xiŕa’ tte.”
- **English:** They said, “I am speaking, ‘do not leave.’”
- **Polish:** Powiedzieli: „Mówię: ‚nie odchodź’”.

The Asaxi, English, and Polish sentences above are plain text. Only their
language labels are bold. Instructional example content and its translations
must never be bold or italic. Editorial styling in a literary work is not an
example-record style and may be retained.

## Example Records

Every dictionary example is stored as one language-separated record:

```yaml
asaxi: ă wo aiŕů.
translation_en: I grieve.
translation_pl: Cierpię.
```

The canonical Markdown rendering is:

```markdown
#### Example 1

- **Asaxi:** ă wo aiŕů.
- **English:** I grieve.
- **Polish:** Cierpię.
```

Additional examples repeat the `#### Example N` group. A sense may have more
than one example, but no field may contain two languages.

## Font

The current alphabet font is a single real Medium weight:

| Name field | Value |
|---|---|
| Full name | Asaxi Merriweather 24pt Medium |
| PostScript name | AsaxiMerriweather24pt-Medium |
| Style group | Asaxi Merriweather 24pt Med |
| Typographic family | Asaxi Merriweather 24pt |
| Typographic subfamily | Medium |
| Available weight | Medium only |

The vault embeds the font as:

`anki-assets/fonts/Asaxi-alphabet-Merriweather24pt-Medium.ttf`

Its SHA-256 checksum is:

`D021B123A7C739CA2C8607AC4CF5A95FBE33ED2D48172B5090BFA25851B27868`

Obsidian loads it through the enabled `fonts.css` snippet. Use the
`asaxi-text` class or `lang="art-x-asaxi"` only on Asaxi text. Font synthesis
is disabled so applications do not invent unavailable bold or italic faces.

The Quartz site embeds the same font bytes at
`quartz/static/fonts/Asaxi-alphabet-Merriweather24pt-Medium.ttf`.
`quartz/styles/custom.scss` applies the face to `asaxi-script-alpha`,
`asaxi-text`, `lang="art-x-asaxi"`, and the lexicon browser's Asaxi headwords.
English and Polish site prose retains the theme typography.

## Editor Behavior

Vocab Forge:

- lowercases ordinary native Asaxi vocabulary and grammatical material;
- preserves or enforces full capitals for entries explicitly classified as
  proper nouns, proper names, place names, or borrowed terms;
- does not guess a lexical case category from capitalization alone during
  legacy migration;
- preserves case in English, Polish, IPA, and explanatory prose;
- keeps Asaxi, English, and Polish examples in separate controls;
- converts legacy quotation marks to the approved Asaxi forms;
- keeps the glottal-stop apostrophe unchanged;
- renders example sentence content without bold or italic markup.

The generated `dictionaries/asaxi.txt` word list supports spell-check tools.
Vocab Forge Asaxi controls additionally disable browser spell-check because
their language is known exactly.

Rebuild the dictionary after vocabulary changes:

```powershell
py -3.14 build_asaxi_dictionary.py
py -3.14 build_asaxi_dictionary.py --check
```

The vault's `cspell.json` loads this list for compatible editors. Obsidian's
built-in spell-check uses `%APPDATA%\obsidian\Custom Dictionary.txt`; merge
the generated spellings into that file while Obsidian is closed, preserving
its existing entries and making a backup first.

## References

- [Polish Academy of Sciences journal guidance on Polish quotation marks](https://journals.pan.pl/kn/137453?language=pl)
- [Interpunkcja.pl overview of Polish quotation-mark forms](https://www.interpunkcja.pl/zasady-interpunkcji/rodzaje-cudzyslowow)
