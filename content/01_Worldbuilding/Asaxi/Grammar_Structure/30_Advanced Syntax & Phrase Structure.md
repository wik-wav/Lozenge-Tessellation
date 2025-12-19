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

# 30_Advanced Syntax & Phrase Structure

## Grammatical Concept: The Left-Branching Hierarchy

Asaxi syntax is built on a strict **Head-Final** logic. In almost every structure (Noun Phrases, Verb Complexes, Sentences), the "Head" (the core meaning) appears last, while all modifiers branch to the **Left**.

This consistency allows speakers to stack complex descriptions without ambiguity, even when pronouns are dropped.

---

## 1. The Noun Phrase (Micro-Syntax)

The internal structure of a Noun Phrase (NP) follows a rigid **Determiner-First** hierarchy.

**The Hierarchy:**

> `[Determiner]` + `[Floating Quantifier]` + `[Relative Clause]` + `[Adjective / Ga-Compound]` + `[Head Noun]`

### A. The Phrasal Linker (`to` / `ă`)

Complex Prepositional Phrases modify a noun by linking them with `to`.

- **Standard Rule:** `[Phrase] + to + [Head Noun]`
    - _Example:_ **Izo kjè to ŕimshá.** ("The lemur from the tree").
- **Genitive Exception:** For possession (`sè`), the linker is optional.
    - _Structure:_ `[Sè Owner] + [Head Noun]`
    - _Example:_ **Sè wo shěso.** ("My book").

### Breakdown of Slots

1. **Determiner:** The **Anchor**. It signals the start of the phrase. (`onă` / `onýj`)
2. **Floating Quantifier:** Distributives (`jonojo`, `ojano`).
3. **Relative Clause:** The complex modifier. Describes an event involving the noun.
4. **Adjective / Compound:** Intrinsic qualities (`shěsonýj`, `gapo`).
5. **Head Noun:** The entity itself.

### Complex Example

**Target:** _"The red books that John dropped one by one."_

> **Onýj jonojo [To John zètopu] gaposhěsa...** `DEF` `DIST` `[SUBJ` `John` `PAST-drop]` `red-books`...

- **Analysis:**
    
    1. **Onýj**: Starts the phrase (The...).
    2. **Jonojo**: Distributes the items (One by one...).
    3. **[To John zètopu]**: Describes the event (That John dropped...).
    4. **gaposhěsa**: The core object (Red books).
### A. The Phrasal & Clausal Linker (`to` / `ă`)

The particles `to` and `ă` function as **Linkers** when they connect a modifier to a noun.

- **Structure:** `[Modifier Phrase] + to + [Head Noun]`
- **Example:** **Sè John to shěso.** ("John's book").

**Binding Priority (The Absolute Linker Rule):** If the particle `to` (or `ă`) appears immediately after a Relational Phrase (`izo X`, `sè Y`), it is **ALWAYS interpreted as a Linker** connecting that phrase to the following noun.

- **Consequence:** You cannot place a Marked Subject (`to Subject`) immediately after an Oblique Argument (`ni Location`) without a pause, because the grammar will try to fuse them.

### B. Disambiguation via Pause (The Comma Rule)

To break the "Absolute Linker" bond and treat the `to` as a **Subject Marker**, the speaker must use a **Pause** (Comma).

**Minimal Pair Comparison:**

**1. The Linker (No Pause)**

> **Tom izo sháŕo to Mary ijo.** `Tom` `[from pool LINK Mary]` `see` _"Tom sees \[the Mary from the pool\]."_
> 
> - _Analysis:_ `to` fuses "from pool" and "Mary" into one object. Tom is the Subject.

**2. The Subject Marker (With Pause)**

> **Izo sháŕo, to Mary Tom ijo.** `from` `pool`, `SUBJ` `Mary` `Tom` `see` _"From the pool, Mary sees Tom."_
> 
> - _Analysis:_ The comma breaks the link. `to` marks Mary as Subject. "From the pool" acts as an adverb describing the location of the seeing.
>     

**3. The Fronted Object (With Pause)**

> **Tom izo sháŕo, to Mary ijo.** `Tom` `from` `pool`, `SUBJ` `Mary` `see` _"Mary sees Tom from the pool."_
> 
> - _Analysis:_ `Tom` is the Object (fronted). `to Mary` is the Subject (Emphasized).

> - _Nuance:_ The speaker is pointing out that it is **SPECIFICALLY** Mary who is seeing, differentiating her from Tom or others.>

### C. Dropping the Subject Marker (Linker Persistence)

If the Subject of the sentence is a Complex Noun Phrase (using a Linker), the initial **Subject Marker** (`to` at the very start) can be dropped for efficiency, but the **Linker** (`to` inside the phrase) **must remain** to connect the pieces.

- **Full Form:** `To [Sè John] to [shěso]...` ("The book of John...").
- **Dropped Form:** `[Sè John] to [shěso]...` ("John's book...").

**Example 1 (Object with Linker, Subject Unmarked):**

> **Wo \[bă shosa zèxaśù\] to Tom ijo.** `1SG` `[via road ran]` `LINK` `Tom` `see` _"I see Tom, who ran down the road."_
> 
> - _Analysis:_ `Wo` is the Subject (No marker). `to` acts solely as the link between the clause and Tom.

**Example 2 (Subject with Linker, Marker Dropped):**

> **\[Sè ijoŕo\] ă \[Tom\] zèxoxo.** `[of dream]` `LINK(Subj)` `[Tom]` `PAST-depart` _"The Tom of the dream departed."_
> 
> - _Analysis:_ The initial `Ă` (Subject Marker) is omitted. The internal `ă` remains to define the "Dream-Tom" relationship.

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

> **[Nani John izo Tom] apa dănă chỏnů.** `[More` `John` `than` `Tom]` `apples` `heavily` `eats` _"John eats apples more heavily than Tom."_

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

> **Månixåkam xő pazènánixèshěsonů.** _"By the time, he **will not have started trying to read**."_

---

### B. The Post-Verbal Tail (Right-Branching)

This is the only part of the language that branches Right. It handles the **Consequences** (Cessation) and the **Meta-Data** (Questions, Emotions, Logic).

**Formula:**

> `[Verb]` + `(Cessative)` + `(Question)` + `(Discourse)` + `(Connector)`

#### Logical Example: The Clarification

**Context:** Two people are watching John. He puts his book down. One person asks if he stopped, but then notices he picks it up again.

**The Sentence:**

> **Shěsonů tomo kè ë dzè...** `read` `STOP` `QUES` `RIGHT` `BUT`...

**Breakdown:**

1. **Shěsonů:** The Action (Reading).
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
| **7. Tail**      | Connector      | **ŕa...** (and...)                |
**Full Sentence:**

> **Vashěsokam, to wo ximă shěso gadăchỏnă shěsonů ŕa...** `in-library` `SUBJ` `1SG` `daily` `book` `ravenously` `read` `AND` _"In the library, I daily read the book ravenously, and..."_

### Ambiguity Resolution (Pro-drop Contexts)

When pronouns are dropped, Asaxi relies on **Strict Position**.

- **Rule:** The **First Unmarked Noun** is the Subject. The **Second Unmarked Noun** is the Object.
- **Relative Clause Check:** If a verb is followed immediately by a Determiner/Noun, it is a Relative Clause, not the Main Verb.

**Example:**

> **Onýj [zètopu] shěsa toponů.** `DEF` `[PAST-drop]` `books` `raining/falling` _Analysis:_ `Zètopu` is inside the phrase started by `Onýj`, so it is a modifier. `Toponů` is the main verb. _Meaning:_ "The books that were dropped are falling."