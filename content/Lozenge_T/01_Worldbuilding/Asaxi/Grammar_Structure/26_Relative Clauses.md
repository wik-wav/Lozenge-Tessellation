---
title: 26_Relative Clauses
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
Navigation:
- [[00_Structural Sets in Asaxi| Back to Structural Sets in Asaxi]]
 
- - - 

# 26_Relative Clauses

## Grammatical Concept: Pre-Nominal Embedding

Asaxi handles Relative Clauses (e.g., "The man _who saw me_") by treating the entire clause as a **Complex Adjective** embedded within the Noun Phrase.

Unlike English, which places the clause after the noun ("The book **that I read**"), Asaxi places it **before** the noun. Crucially, the **Determiner** (`onă` / `onýj`) acts as the **Anchor**, signaling the start of the complex phrase.

### 1. Syntactic Structure

**Formula:**

> `[Determiner] + [Relative Clause Verb Phrase] + [Head Noun]`

- **The Anchor:** The Determiner (`onă`, `onýj`, or `anő`) appears first. It agrees with the **Head Noun**.
- **The Clause:** Placed immediately after the determiner and before the noun.

### 2. Types of Clauses

**A. Subject Relative ("The one who...")** The Head Noun is the Subject of the relative verb.

- _English:_ "The person **who** departed."
- _Asaxi:_ **Onă \[zèxoxo\] shá.**
    
    - _Structure:_ `DEF.WARM` `[PAST-depart]` `person`.
    - _Lit:_ "The \[departed\] person."
**B. Object Relative ("The thing that...")** The Head Noun is the Object of the relative verb.
- _English:_ "The book **that** John reads."
- _Asaxi:_ **Onýj \[John shěsonů\] shěso.**
    - _Structure:_ `DEF.COLD` `[John reads]` `book`.
    - _Lit:_ "The \[John-reads\] book."
**C. Oblique Relative ("The place where...")** The Head Noun is an oblique argument (Location, Tool, etc.).
- _English:_ "The library **where** I read."
- _Asaxi:_ **Onýj \[wo shěsonů\] shěsokam.**
    - _Lit:_ "The \[I-read\] library." (Context implies "at which").

### 3. Disambiguation

In the Standard Register, ambiguity is impossible because of the **Position of the Determiner**.

1. **Start of Phrase:** When a listener hears a Determiner (`onýj`), they expect a Noun Phrase.
2. **Nested Verb:** If a verb follows the determiner instead of a noun, the listener knows it is a **Modifier** (a Relative Clause), not the main verb of the sentence.
3. **End of Phrase:** The Head Noun eventually appears to close the bracket.

**Example:**

> **Onýj \[shěsonů\] shěso toponů.** `DEF.COLD` `[reads]` `book` `falling` _Analysis:_ `Onýj` opens the NP. `Shěsonů` modifies `shěso`. `Toponů` is the main verb. _Meaning:_ "The book that is read is falling."

**Disambiguation vs. Gerunds**

Since `anő + Verb` can also form a **Gerund** (e.g., `anő shěsonů` "A reading"), the listener waits for the next word.
- If the phrase ends there → **Gerund**.
- If a **Noun** follows → **Relative Clause**.

**Minimal Pair:**

> **To wo \[anő shěsonů\] jå.** _"I want a reading."_ (Gerund).
> **To wo \[anő shěsonů\] shěso jå.** _"I want a book that is read."_ (Relative Clause).

### 4. Interaction with Particles

The Relative Clause can contain its own internal particles (Negative, Tense, Causative).

- **Negative:** `Onă [shěsonůná] shá...` ("The person who does not read...").
- **Tensed:** `Onă [pazèxoxo] shá...` ("The person who will have left...").

### Example Sentences

**1. Context: Identifying a specific item.**

> **Onýj \[To John zètopu\] shěso ksi?** `DEF.COLD` `[SUBJ` `John` `PAST-drop]` `book` `where` _"Where is the book **that John dropped**?"_

**2. Context: Conditional Consequence.**

> **Onýj \[John shěsonů\] shěso chěná, wo pashěsonů.** `DEF.COLD` `[John` `reads]` `book` `UNLESS`, `1SG`, `FUT-read` _"Unless it is the book **that John reads**, I will read it."_ _(Lit: If-not the \[John-reads\] book...)_