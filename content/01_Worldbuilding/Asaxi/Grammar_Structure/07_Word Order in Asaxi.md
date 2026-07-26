---
title: 07_Word Order in Asaxi
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
# Word Order in Asaxi

Navigation:
- [[00_Structural Sets in Asaxi| Back to Structural Sets in Asaxi]]

## Grammatical Concept: Head-Final Syntax

Asaxi is a **Head-Final** language with a **Marked Nominative** alignment. While the default word order is **SOV** (Subject-Object-Verb), the language is fundamentally **Topic-Prominent**.

- **The Core Rule:** The Verb (or Stative Particle) must always come **last**.
- **Branching:** Asaxi is **Left-Branching**. Modifiers generally appear _before_ the word they modify.

---

## 1. The Core Sentence Structure (Active)

### Standard Order (SOV)

The default, neutral sentence places the actor first, the target second, and the action last.

**Formula:**

> `[Subject] + [Object] + [Verb]`

**Example:**

> to john shěso shěsonů. John reads the book.

### Subject vs. Object Identification

Asaxi operates on a strict **Marked Nominative / Zero Accusative** system.

- **The Unmarked Object:** Asaxi does **NOT** mark the Direct Object. There is no specific particle for the object. It is identified purely by **deduction** (it is the noun _without_ a subject/oblique marker).
- **The Marked Subject:** The Subject is explicitly identified by a particle.
    - **to:** Standard Subject Marker (Objective).
    - **ă:** Subjective Subject Marker (Internal/Emotional).

**Logic of Deduction:**

> "If a noun has `to` or `ă`, it is the **Doer**. If a noun has no particle, it is the **Receiver**."

---

## 2. Topic-Prominence & The Null Topic

Asaxi is a **Null-Topic Language**. This means the sentence is structured around a "Topic" (what we are talking about) rather than a strict grammatical Subject.

**Rules:**

1. **The Hidden Topic:** Once a topic is established, it is **omitted**.
    - _Context:_ "What about John?"
    - _Answer:_ `shěso shěsonů.` ("(As for him), reading a book.")
2. **Explicit Topic (`dhè`):** If you need to shift the topic or emphasize it, you use the particle **[[dhè (particle)|dhè]]**.

---

## 3. Dropping the Subject Marker (Efficiency)

The marker (`to` or `ă`) is **not mandatory** in standard speech (both formal and informal), if the sentence follows the strict **S-O-V** order. It is frequently dropped to increase conversation speed. 

**A. Intransitive / Stative Clauses** If there is only one noun, the marker is almost always dropped.

- _Example:_ john shá xiŕa. (John is a person).

**B. Transitive Clauses (Strict SOV)** If the subject marker is dropped in a sentence with two nouns, **Strict Word Order** is enforced to prevent ambiguity.

- **Rule:** The **First** unmarked noun is the Subject. The **Second** unmarked noun is the Object.
- _Example:_ john shěso shěsonů. (John reads the book).

 **C. Emphatic** `to`
Even in standard S-O-V order, inserting `to` places specific focus on the Subject.
- **Example:**
    > to john shěso shěsonů. _Nuance:_ "It is **John** (specifically) who is reading the book."

---

## 4. Poetic Inversion (Active OVS)

Because the Subject can be explicitly marked, it may be moved away from the start of the sentence for dramatic effect.

**Constraint A: Mandatory Marker** You **cannot** drop the subject marker (`to`/`ă`) if you change the word order. If the marker is absent, the first noun is assumed to be the Subject.

**Constraint B: The Pause (Disambiguation)** When moving the Subject to a position _after_ a prepositional phrase or object, a **Pause (Comma)** is often required to prevent the subject marker from being misinterpreted as a **Linker**.

- _Without Pause:_ `izo sháŕo **to** mary...` (The Mary from the pool...). (`to` links the phrase to the noun).
- _With Pause:_ `izo sháŕo, **to** mary...` (From the pool, Mary...). (The comma breaks the link, allowing `to` to mark the Subject).

**Structure:**

> `[Object] + [Verb] + [Pause] + [Marker + Subject]`

**Example (Dramatic Reveal):**

> shěso shěsonů, to john. Reading the book... is John.

---

## 5. Post-Verbal Elements

While the Verb ends the _grammatical_ clause, specific particles may trail after it to modify the mood or social context.

**The Tail Sequence:**

> `[Verb] + (Mood/Imperative) + (Discourse Marker) + (Conjunction)`

- **Example:** `shěsonů ë dzè...` (Reads, right? But...)

---

## 6. Passive Voice (Topicalized OSV)

Asaxi achieves Passive Voice by promoting the Object to the **Topic** position using the particle **[[dhè (particle)|dhè]]**.

**Structure:**

> `dhè [Patient/Object] + [Agent/Subject] + [Verb]`

**Example:**

> dhè kjèpo tom zèchỏnů. `TOP` `tree` `Tom` `PAST-chop` "The tree was chopped by Tom."

---

## 7. Temporal Adverbials (The Bare Adverb Rule)

Specific temporal nouns (like **hwo** "Yesterday", **vwo** "Today", **pwo** "Tomorrow") function as **Bare Adverbials**. They do not require a case particle to indicate time.

**A. Sentence-Initial (Frame / Topic)**

- **Structure:** `[Time], [Subject] ... [Verb]`
- **Example:** hwo, to wo zèxoxo. ("Yesterday, I departed.")

**B. Post-Subject (Standard Adverb)**

- **Structure:** `[Subject] [Time] ... [Verb]`
- **Example:** to wo hwo zèxoxo. ("I yesterday departed.")

- - -

## 8. Implicit Agents in Requests

In **Causative** sentences ("Make X do Y"), ambiguity can arise regarding who is causing the action. However, if the sentence is a **Request** (marked by **[[36_Polite Requests|kă]]**), the ambiguity is resolved by social logic.

**The Logic of `kă`:**

1. **Implied Agent:** A request always targets the Listener ("You"). Therefore, "You" are the Causer.
2. **Role Assignment:** Since the Causer is "You" (implicit), any remaining noun must be the **Subject** of the underlying verb (the one being made to act).

**Example: Waking Up**

> wo hèpăŕokă. `1SG` `CAUS-emerge-PLEASE` "Please wake me up." (Lit: Please make me emerge).

- **Parsing without `kă`:** `wo hèpăŕo.` → Ambiguous. "I make (someone) emerge" OR "I am made to emerge."
- **Parsing with `kă`:** Since you are asking the listener to do it, "You" are the Causer. Therefore, `wo` must be the one waking.

---

### See Also: Advanced Syntax

_For detailed rules on the internal structure of Noun Phrases and the complex ordering of Verb Prefixes, see:_ **[[30_Advanced Syntax & Phrase Structure]]**.