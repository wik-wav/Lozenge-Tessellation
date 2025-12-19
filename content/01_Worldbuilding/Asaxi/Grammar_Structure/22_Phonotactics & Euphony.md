---
title: 22_Phonotactics & Euphony
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
Navigation:
- [[00_Structural Sets in Asaxi| Back to Structural Sets in Asaxi]]
 
- - - 

## Grammatical Concept: Flow and Constraints

Asaxi places a high priority on **Euphony** (pleasant sound flow). The language strictly regulates how sounds connect, utilizing a system of **Epenthetic Bridges** to resolve hiatus and enforcing strict **Phonotactic Constraints** on what sounds may coexist.

---

## 1. Vowel Hiatus Resolution (The Bridge System)

With one specific exception, the choice of bridge consonant is **arbitrary** or lexically determined.

### A. The Strict Morphological Rule (`-n-`)

**Mandatory** when converting a Noun ending in a vowel into a Derived Verb.

- **Rule:** `[Root-V]` + **n** + `ů`.
- **Example:** `shěso` + `ů` → **shěsonů** (To read).

### B. Common Lexical Bridges (`-w-` / `-x-`)

- **The `-w-` Bridge:** Common in Locative Stacking (`vawo`) and Ga-Compounds (`gamaowo`).
- **The `-x-` Bridge:** Common in Verbal Prefixes (`zèxijo`, `månixåkam`).

### C. I-Stem Coalescence (The "I" Exception)

A specific exception exists for **Verb Roots starting with `i`** (e.g., `ijo`, `ijù`). When a **Prefix** ending in a vowel attaches to an `i-` verb, the standard `-x-` bridge is **omitted**. Instead, the vowels coalesce into a diphthong.

- **Rule:** `[Prefix-V]` + `[Root-i]` → **\[Diphthong\]**
- **Example:** `zè` + `ijù` → **zëjù** (Said).
- **Example:** `no` + `ijo` → **nőjo** (There-see).

**Poetic & Formal Exception:** While coalescence is the standard rule for natural speech, the full bridge form (`-x-`) may be preserved in **poetry**, **song**, or **high-formal register** to maintain syllable count or meter.

- _Standard:_ **zëjo** (2 syllables).
- _Poetic:_ **zèxijo** (3 syllables).

**Constraint (Word Boundary):** This rule applies **only** to prefixes (bound morphemes) within the verbal complex. It does **not** apply across word boundaries between separate parts of speech.

- **Example:** **To jo ijo.** ("It sees.")
    - _Analysis:_ `jo` (Pronoun "It") ends in `o`. `ijo` (Verb "See") starts with `i`.
    - _Result:_ **No Coalescence.** They remain separate words: `jo ijo`. (NOT _jőjo_).

---

## 2. Consonant Mutation & Elision

### A. H-Deletion (`h` Stability)

The glottal fricative `/h/` is weak.

- **Deletion Rule:** If `h` follows a **Consonant** or a **Diphthong**, it is deleted.
    - `ů` + `hè` → **ůè**.
- **Retention Rule:** If `h` follows a **Pure Vowel**, it remains.
    - `dao` + `hè` → **daohè**.

### B. H-Fortition / Assimilation

If a syllable containing the voiced fricative **x** (/ɦ/) is followed by **h**, the `h` hardens into **x**.

- **Rule:** `...xV` + `hV...` → `...xVxV...`
- **Example:** `ná` + `xă` + `hù`... → **náxăxù...**

### C. Devoicing Assimilation

When the voiced consonants precede voiceless ones, they often get devoiced.

- **Example:** `v` + `k` → **/fk/**.
  `va` + `kozè` → **vkozè**.
    - _Pronunciation:_ /fkozə/ ("In the distant past").
- **Example:** `z` + `p` → **/sp/**.
  `izo` (From) + `pă` (Outside) → **ispă** (Wilderness).

---

## 3. Syllabic Nasals (Nuclei)

The geminated/syllabic nasals **mm**, **nn**, and **nŋ** function phonotactically as **Vowels** (Nuclei).

- **Status:** They occupy the V-slot in a syllable (CV).
- **Assimilation:**
    - `nn` becomes **mm** before Bilabials (`p, b`).
    - `nn` becomes **nŋ** before Velars (`k, g`).
- **Coda Tolerance:**
    - Syllabic nasals **cannot** support plosive codas (`p, t, k, b, d, g`) at the end of a word.
    - _Invalid:_ `kammb`, `kanŋg`.
    - _Valid:_ `kammba`, `kanŋga` (Must be followed by a vowel to break the cluster).

---

## 4. Phonotactic Constraints

### A. Forbidden Codas

- **Plosives (`p, t, k, b, d, g`):** Generally forbidden at the end of a word.
    - _Restriction:_ This prohibition extends to clusters involving Syllabic Nasals (e.g., `kammb` is forbidden).
- **Complex Clusters:** Clusters like `lv` or `lm` cannot end a word (e.g., `ilv` is invalid; `ilva` is valid).

### B. Liquid Constraints (`r` / `l`)

- **The `l` Rule:** The liquid `l` must be adjacent to **Pure Vowels** (`a, i, u, e, o`) only.
    - _Invalid:_ `ýl`, `lý`.
    - _Constraint:_ `l` may appear at the onset of a syllable with impure vowels, but may not _follow_ them (e.g., `lýshko` OK; `lýlo` NO).
- **The `r` Rule:**
    - **Rarity:** `r` is exceedingly rare.
    - **Permitted Clusters:** Only allowed after `ch`, `jh`, `k`, `f`, `p`. (Forbidden: `tr`, `dr`, `sr`, `gr`).
    - **Vowel Restriction:** `r` may **never** be followed by `i`.
        - _Sole Exception:_ **fri** (Valid).
    - **Glide Restriction:** `r` never appears with glides (`w, j`).

### C. Orthographic Enforcements (Spelling Rules)

Certain phonetic combinations result in mandatory orthographic and pronunciation shifts.

|Spelling|IPA Realization|
|---|---|
|**chi**|/tʃi/|
|**dzý**|/dzɪ/|
|**si**|/ɕi/ (Always palatalized)|
|**zi**|/ʑi/ (Always palatalized)|
|**ji**|/ji/|
|**wő**|/woɪ/|
|**shŕa**|/ʃɹ̠˔a/|
## 5. Special Phenomena

### A. The Glottal Stop (`'`)

A distinct consonant (/ʔ/). Orthographically significant.

- **Interaction with `h-` Suffixes (Glottal Elision):** When a word ending in a glottal stop meets a suffix starting with **h**, the glottal stop is deleted.
    - `chěcho'` + `hè` → **chěchohè** (Close it!).
- **Interaction with Particles (Boundary Elision):** If a word ending in a glottal stop is followed immediately by a **Particle** or **Connector** (even if it starts with a consonant), the glottal stop is dropped to maintain flow.
    - **Rule:** `[Word-']` + `[Particle]` → `[Word] [Particle]`
    - **Example:** `tomo'` (Stop) + `kè` (Question) → **tomo kè?** ("Does it stop?").
    - _Note:_ This prevents the "stutter" of a glottal stop followed immediately by another consonant across a grammatical boundary.

### B. Vowel Devoicing

Vowels between voiceless consonants may devoice, creating syllabic fricatives.

- **Example:** `shěso` → **\[ʃ̩so\]**.

## 6. Particle Contraction (Rapid Speech)

In casual or rapid speech, disyllabic compound particles often undergo **Vowel Elision**, where the first vowel is dropped to create a consonant cluster. This is permissible only if the resulting cluster follows Asaxi phonotactic constraints.

**Marking:** Contracted forms are written with an apostrophe (`'`) to indicate the missing vowel.

### Common Contractions

| Original | Meaning        | Contraction | IPA     |
| -------- | -------------- | ----------- | ------- |
| **sèwo** | Because        | **s'wo**    | /swo/   |
| **sèni** | So / Therefore | **s'ni**    | /sni/   |
| **panå** | Not yet        | **p'nå**    | /pnau̯/ |
| **nanå** | Often          | **n'nå**    | /n:au̯/ |
| **hùnå** | Already        | **h'nå**    | /hnau̯/ |
| **vanå** | Still          | **v'nå**    | /vnau̯/ |
**Usage Note:** These contractions are **optional** and register-dependent (Casual/Fast). In formal writing or poetry, the full form is preferred for clarity and meter.

## 7. Special Pronunciation Rules

**A. The Final `ë`** When the vowel **ë** appears at the end of a phrase or word (common in imperatives), it lengthens significantly.

- **IPA:** **/eː/** (Long 'e').
- _Example:_ **shivënwë** → /ɕi.veɪ.ɴweː/

**B. The Nasal-Glide Cluster (`nw`)** When the consonant `n` is followed immediately by `w` (specifically in the `nwë` imperative ending), the nasal shifts to the uvular position.

- **Rule:** `n` + `w` → **/ɴw/**.
- _Example:_ **shivënwë** (Show off!) → /...ɴweː/