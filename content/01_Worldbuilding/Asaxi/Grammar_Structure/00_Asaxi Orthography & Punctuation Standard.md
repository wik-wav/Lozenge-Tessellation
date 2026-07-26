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

Asaxi is written exclusively in lower case. This includes:

- the beginning of a sentence;
- names and other proper nouns;
- quoted speech;
- headings written in Asaxi;
- example sentences and isolated words.

The English proper name **Asaxi** keeps its capital letter when it occurs in
English prose. The Asaxi-language form is `asaxi`.

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
| PostScript name | Asaxi Merriweather24pt-Medium |
| Style group | Asaxi Merriweather 24pt Med |
| Family name | Merriweather 24pt |
| Available weight | Medium only |

The vault embeds the font as:

`anki-assets/fonts/AsaxiMerriweather24pt-Medium.ttf`

Its SHA-256 checksum is:

`300F36635987853F4FBB07A68A8C93E48B4EC8AE8386DF2AFA7242D35E8D40CF`

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

- lowercases only fields explicitly identified as Asaxi;
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
