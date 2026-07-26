---
title: 30_Advanced Syntax & Phrase Structure
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
Navigation:
- [[00_Structural Sets in Asaxi| Back to Structural Sets in Asaxi]]
 
- - - 

### Grammatical Concept: The Left-Branching Hierarchy

Asaxi syntax is built on a strict Head-Final logic. In every structure (Noun Phrases, Verb Complexes, Sentences), the “Head” (the core meaning) appears last, while all modifiers branch to the Left. This consistency allows speakers to stack complex descriptions without ambiguity.

### Noun Phrase Constituency Particles (NPCP)

Noun Phrases are governed by the **NPCP Opening Rule**. A Noun Phrase is initiated by a particle—such as a **Case Marker** (`to`, `sè`, `ă`) or a **Determiner** (`onă`, `onýj`, `anő`).

Once an NPCP is invoked, the listener "opens" a mental bracket. Every word that follows is automatically categorized as a modifier of the eventual Head Noun. The first noun encountered that is not followed by a modifier or another NPCP "closes" the bracket as the Head.

- **Logic:** Internal linkers are redundant because the relationship between the modifiers and the head is defined by their position within the NPCP-bounded block.
- **Structural Nesting:** Complex modifiers (like genitives or relative descriptions) are simply placed to the left of the noun they describe.

### Sentence Analysis & Gloss

sè o dănă jalăsháma wo táka. Free Translation: The big birds of the sky wage war with me.

| Asaxi         | sè | o | dă-nă | jalăshá-ma | wo | táka |
| ------------- | ----------- | -------- | --------- | --------------------- | ------ | ----------- |
| **Morphemes** | sè          | o        | dă - nă   | jală-shá - ma         | wo     | táka        |
| **Gloss**     | GEN         | sky      | big-ADJ.W | to.fly-creature- PL   | 1SG    | wage.war    |
| **Function**  | NPCP (Open) | Modifier | Modifier  | **Head Noun (Close)** | Object | Verb (Head) |

---

## 2. The Comparative Block (Correlative Syntax)

When comparing two nouns, Asaxi creates a **Correlative Block**. This entire block functions syntactically as a **Single Argument** (Subject or Object).

**Formula:**

> `[Marker] [Noun A] + [Complement] [Noun B]`

| Marker          | Complement | Logic          |
| --------------- | ---------- | -------------- |
| **bi** (Equal)  | **zá**     | Equal A with B |
| **nani** (More) | **izo**    | Up A from B    |
| **pùni** (Less) | **izo**    | Down A from B  |
**Example (As Subject):**

> [Nani John izo Tom] apa dănă chỏnů. `[More` `John` `than` `Tom]` `apples` `heavily` `eats` "John eats apples more heavily than Tom."

---

## 3. The Verbal Complex (Morpho-Syntax)

The Verb is the gravitational center of the sentence. It builds outwards from the root using a fixed order of prefixes (Morphology) and is followed by a "Tail" of particles (Syntax).

### A. The Prefix Block (Left-Branching)

Modifiers stack from the **outside in**. The outermost prefix has the widest scope.

**Formula:**

> `[Tense]` + `[Negation]` + `[Aspect]` + `[Voice/Mood]` + `[Bridge]` + `[Root]`

#### Logical Example: The Progress Report

**Context:** A teacher is reporting on a lazy student. You want to say: _"By noon, he will not have even started trying to read."_

**The Stack:**

1. **Tense (Future Perfect):** `pazè-` (Will have).
2. **Polarity (Negation):** `ná` (Not).
3. **Aspect (Inceptive):** `ni-` (Start to).
4. **Mood (Conative):** `xè-` (Try to).
5. **Root:** `shěsonů` (Read).

**The Resulting Verb:**

> **pazènánixèshěsonů** `FUT-PAST` `NEG` `START` `TRY` `read`

**The Sentence:**

> måniåkam xő pazènánixèshěsonů. "By the time, he will not have started trying to read."

---

### B. The Post-Verbal Tail (Right-Branching)

This is the only part of the language that branches Right. It handles the **Consequences** (Cessation) and the **Meta-Data** (Questions, Emotions, Logic).

**Formula:**

> `[Verb]` + `(Cessative)` + `(Question)` + `(Discourse)` + `(Connector)`

#### Logical Example: The Clarification

**Context:** Two people are watching John. He puts his book down. One person asks if he stopped, but then notices he picks it up again.

**The Sentence:**

> shěsonů tomo kè ë dzè... `read` `STOP` `QUES` `RIGHT` `BUT`...

**Breakdown:**

1. **shěsonů:** The Action (Reading).
2. **tomo:** The Result (Stop). _"He stops reading."_
3. **kè:** The Inquiry. _"Does he stop reading?"_
4. **ë:** The Appeal for Agreement. _"He stops reading, right?"_
5. **dzè:** The Adversative Switch. _"He stops reading, right? But..."_

---

## 4. The Sentence Structure (Macro-Syntax)

The core sentence follows **SOV**, but includes specific slots for Floating Modifiers and Adverbs.

**Standard Order:**

> `[Time/Place]` + `[Subject]` + `[Frequency]` + `[Object]` + `[Manner]` + `[Verb Complex] + [Tail]`

| Slot             | Content        | Example                           |
| ---------------- | -------------- | --------------------------------- |
| **1. Setting**   | Locative       | **Vashěsokam,** (In the library,) |
| **2. Subject**   | Noun Phrase    | **to wo** (I)                     |
| **3. Frequency** | Time Adverb    | **ximă** (daily)                  |
| **4. Object**    | Noun Phrase    | **shěso** (the book)              |
| **5. Manner**    | Quality Adverb | **gadăchỏnă** (ravenously)       |
| **6. Verb**      | Predicate      | **shěsonů** (read)                |
| **7. Tail**      | Connector      | ŕa... (and...)                |
**Full Sentence:**

> vashěsokam, to wo ximă shěso gadăchỏnă shěsonů ŕa... `in-library` `SUBJ` `1SG` `daily` `book` `ravenously` `read` `AND` "In the library, I daily read the book ravenously, and..."

### Ambiguity Resolution (Pro-drop Contexts)

When pronouns are dropped, Asaxi relies on **Strict Position**.

- **Rule:** The **First Unmarked Noun** is the Subject. The **Second Unmarked Noun** is the Object.
- **Relative Clause Check:** If a verb is followed immediately by a Determiner/Noun, it is a Relative Clause, not the Main Verb.

**Example:**

> onýj [zètopù] shěsa toponů. `DEF` `[PAST-drop]` `books` `raining/falling` _Analysis:_ `Zètopù` is inside the phrase started by `onýj`, so it is a modifier. `toponů` is the main verb. _Meaning:_ "The books that were dropped are falling."