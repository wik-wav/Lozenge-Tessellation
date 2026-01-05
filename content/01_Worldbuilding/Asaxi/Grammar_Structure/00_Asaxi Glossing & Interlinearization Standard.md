---
title: Asaxi Glossing & Interlinearization Standard
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
# Asaxi Glossing & Interlinearization Standard

Navigation:

- [[The Asaxi Language|The Asaxi Language Index]]
- [[index|Index - Homepage]]

## 1. Technical & Formatting Limitations

**Note on Alignment:** Standard linguistic glosses rely on tab-aligned text to match morphemes vertically. Due to the technical limitations of the current editor/software environment, Asaxi glosses are presented using **Markdown Tables**. Each cell corresponds to a distinct phonological word or fused particle group.

## 2. General Rules

1. **Morpheme Boundaries:** Use hyphens `-` to separate distinct morphemes within a word (e.g., prefix-root).
2. **Fused Elements:** Use periods `.` when multiple grammatical functions are fused into a single unsegmentable element (e.g., `SUBJ.DEF.W`).
3. **Grammatical Categories:** Use small caps (simulated here with uppercase) for grammatical codes (e.g., `PST`, `DEF`).
4. **Lexical Roots:** Use lowercase English words for the translation of the root meaning.

## 3. List of Abbreviations

### Noun Classification (Gender)

|Code|Meaning|Asaxi|
|---|---|---|
|**W**|Warm Class|_-nă, onă_|
|**C**|Cold Class|_-nýj, onýj_|
|**N**|Neutral/Indefinite|_anő_|

### Relational Particles (Case Markers)

| Code         | Meaning                                 | Asaxi        |
| ------------ | --------------------------------------- | ------------ |
| **SUBJ**     | Subject (Objective/Marked Nominative)   | _to_         |
| **SUBJ.EMO** | Subjective Subject (Internal/Emotional) | _ă_          |
| **GEN**      | Genitive (Of)                           | _sè_         |
| **DAT**      | Dative (To/For recipient)               | _då_         |
| **ACC**      | Accusative (Direct Object)              | _(Unmarked)_ |
| **INS**      | Instrumental / Causal (By/Using)        | _bă_         |
| **ALL**      | Allative (Towards goal)                 | _ni_         |
| **ABL**      | Ablative (From source)                  | _izo_        |
| **TERM**     | Terminative (Until)                     | _måmå_       |
| **COM**      | Comitative (With)                       | _zá_         |
| **ATT**      | Attributive / Type / Material           | _ga_         |
| **TOP**      | Topic / Passive Patient                 | _dhè_        |
| **REF**      | About / Concerning                      | _ăni_        |

### Determiners

|Code|Meaning|Asaxi|
|---|---|---|
|**DEF**|Definite Article|_onă, onýj_|
|**INDEF**|Indefinite Article|_anő_|
|**SPEC**|Specific Indefinite ("A certain")|_ponă, ponýj_|

### Pronouns

|Code|Meaning|Asaxi|
|---|---|---|
|**1SG**|I|_wo_|
|**2SG**|You|_no_|
|**3SG.M**|He|_xő_|
|**3SG.F**|She|_ko_|
|**3SG.NB**|They (Non-binary/Singular)|_gő_|
|**3SG.INAN**|It|_jo_|
|**1PL**|We|_wa_|
|**2PL**|You (All)|_na_|
|**3PL.M**|They (Male group)|_xa_|
|**3PL.F**|They (Female group)|_ka_|
|**3PL.NB**|They (NB group)|_gja_|
|**3PL.INAN**|They (Things)|_hja_|
|**REFL**|Reflexive|_ni-_ (prefix)|
|**RECIP**|Reciprocal|_gőnigő_|
|**INT**|Interrogative (Who, What, etc.)|_k-_ words|

### Tense (Prefixes)

|Code|Meaning|Asaxi|
|---|---|---|
|**PST**|Simple Past / Perfective|_zè-_|
|**PST.SUBJ**|Subjective/Memoric Past|_sỏ-_|
|**FUT**|Future|_pa-_|
|**IMM**|Immediate (Just now/About to)|_o-_|
|**REM**|Remote / Mythic|_ko-_|
|**PLUP**|Pluperfect / Past-Future|_hù-_|
|**PRES.SUBJ**|Subjective Present (Feeling)|_mi-_|

### Aspect & Mood (Prefixes/Suffixes/Particles)

| Code       | Meaning                          | Asaxi                           |
| ---------- | -------------------------------- | ------------------------------- |
| **NEG**    | Negation                         | _fů-_ (prefix), _ná_ (particle) |
| **ITER**   | Iterative (Again/Re-)            | _na-_                           |
| **INC**    | Inceptive (Start to)             | _ni-_                           |
| **CESS**   | Cessative (Stop)                 | _tomo'_ (post-verbal)           |
| **DES**    | Desiderative (Want to)           | _jå-_                           |
| **CON**    | Conative (Try to)                | _xè-_                           |
| **IMP**    | Imperative                       | _hè_                            |
| **OPT**    | Optative (Hope/Wish)             | _dăxă, xădăchỏxă_               |
| **POT**    | Potential (Can)                  | _ken_                           |
| **SUBJNC** | Subjunctive (Would/Hypothetical) | _xăxă_                          |
| **COND**   | Conditional (If)                 | _chě_                           |

### Verbal Derivation (Bridges)

*Standardized as `BRG.Type`*

**Note on Notation:** While traditionally called "Mode Infixes" in Asaxi grammar, these morphemes structurally function as **suffixes** (interfixes) appearing between the root and the verbalizer (`Root-Bridge-VBZ`). They are not inserted *inside* the root. Therefore, standard Leipzig hyphens (`-`) are used instead of infix angle brackets (`< >`). The tag `BRG` is used to explicitly label this derivational slot.

**Note on Ambiguity (-x-):** The form **-x-** is used for the Interaction Bridge (`BRG.INTER`) but also functions as a phonological **Epenthetic Bridge** to prevent hiatus (e.g., `ni-x-ijo`). In purely phonological contexts, use the code **`EP`** (see below), not `BRG.INTER`.

| Code          | Meaning                    | Asaxi  |
| ------------- | -------------------------- | ------ |
| **EP**        | Epenthetic (Hiatus Bridge) | `-x-`  |
| **VBZ**       | Verbalizer Suffix          | _-ů_   |
| **BRG.PERF**  | Performance (Function/Use) | _-n-_  |
| **BRG.INTER** | Interaction (Force/Do to)  | _-x-_  |
| **BRG.SEMB**  | Semblance (Act like)       | _-w-_  |
| **BRG.TRANS** | Transformative (Turn into) | _-k-_  |
| **BRG.GEN**   | Generative (Create)        | _-ŕ-_  |
| **BRG.PRIV**  | Privative (Remove)         | _-sh-_ |
| **BRG.SUBJ**  | Subjective (Feel like)     | _-ch-_ |

### Other Common Codes

| Code        | Meaning                      |
| ----------- | ---------------------------- |
| **PL**      | Plural (`-ma`)               |
| **COP**     | Stative Particle (`xiŕa`)    |
| **NEG.COP** | Negative Stative (`nèŕa`)    |
| **PTL**     | Particle (General/Discourse) |
| **Q**       | Question Particle            |
| **AUG**     | Augmentative (`dă-`)         |
| **CMPR**    | Comparative (`na-` / `pù-`)  |
| **SUP**     | Superlative (`nă-` / `nýj-`) |


## 4. Examples

### Example 1: Basic Transitive Sentence

**Asaxi:** _To wo onă gaposhěso ijo._ **Free:** _I see the red book._

| Asaxi         | **To** | **wo** | **onă** | **gaposhěso** | **ijo** |
| ------------- | ------ | ------ | ------- | ------------- | ------- |
| **Morphemes** | to     | wo     | onă     | ga-apo-shěso  | ijo     |
| **Gloss**     | SUBJ   | 1SG    | DEF.W   | ATT-red-book  | see     |

### Example 2: Verbal Negation & Derivation

**Asaxi:** _Wo shěso zènáshěsonů._ **Free:** _I did not read (the) book._

| Asaxi         | **Wo** | **shěso** | **zènáshěsonů**           |
| ------------- | ------ | --------- | ------------------------- |
| **Morphemes** | wo     | shěso     | zè-ná-shěso-n-ů           |
| **Gloss**     | 1SG    | book      | PST-NEG-book-BRG.PERF-VBZ |
