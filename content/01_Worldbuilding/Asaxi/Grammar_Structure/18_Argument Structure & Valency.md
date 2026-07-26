---
title: 18_Argument Structure & Valency
aliases:
  - imperative
  - imperatives
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
Navigation:
- [[00_Structural Sets in Asaxi| Back to Structural Sets in Asaxi]]
 
- - - 

# Grammatical Concept: Extended Valency

Asaxi constructs complex sentences (Ditransitive or Tritransitive) by utilizing the **NPCP** (Noun-Preceding Case-Particle) system. Rather than relying on unique verb conjugations to handle extra arguments, the language treats all non-Subject/non-Object participants as **Oblique Arguments** marked by specific particles.

### The Argument Inventory

The sentence core consists of the **Subject** (`to`) and the **Direct Object** (Unmarked). All other participants are slotted in using the following structures:

|Structure|Particle|Function|Logic|
|---|---|---|---|
|**Causative**|**bă**|Causer / Agent|Indicates who forced/enabled the action (Requires **Causative Voice** on verb).|
|**Dative**|**då**|Recipient|Indicates who receives the object/benefit.|
|**Ablative**|**izo**|Source|Indicates where the object is taken _from_.|
|**Allative**|**ni**|Goal|Indicates where the object is put _to_.|
|**Comitative**|**zá**|Partner|Indicates who accompanies the subject.|
## Syntactic Flexibility

The word order of these arguments depends entirely on the presence of the Subject Marker **to**.

### 1. Flexible Order (Marked Subject)

If the Subject is explicitly marked with `to`, the other arguments (including the Direct Object) may be **scrambled** for emphasis. Because the Direct Object is the _only_ unmarked noun in the sentence, it remains unambiguous.

### 2. Strict Order (Unmarked Subject)

If the Subject marker `to` is omitted (Pro-drop or Economy), the sentence must follow strict **SOV** logic.

- **Rule:** The **First Unmarked Noun** is the Subject. The **Second Unmarked Noun** is the Object.

---

## Primary Valency Structures

Here are the five primary ways to extend a sentence beyond Subject-Object-Verb.

### 1. The Imperative Structure

**Particle:** `bă` (Causer) + **Voice:** `hè-` (Prefix) This structure introduces an external agent who forces or permits the Subject to act.

- **Formula:** `[To Subject/Doer] + [bă Causer] + [Direct Object] + [hè-Verb]`

- **Example:**
    > to john bă shějýnshá shěso hèshěsonů. `SUBJ` `John` `CAUS` `teacher` `book` `IMP-read` "The teacher makes John read the book."


### 2. The Dative Structure (Transfer)

**Particle:** `då` (Recipient) Used for verbs of giving, showing, or telling.
- **Formula:** `[To Subject] + [då Recipient] + [Direct Object] + [Verb]`
- **Example:**
    > to wo då john apo ma. `SUBJ` `1SG` `DAT` `John` `apple` `have` "I have an apple for John."

### 3. The Ablative Structure (Source)

**Particle:** `izo` (Source) Used for verbs of taking, removal, or origin.

- **Formula:** `[To Subject] + [izo Source] + [Direct Object] + [Verb]`
- **Example:**
    > to john izo kjèpo apo chỏnů. `SUBJ` `John` `ABL` `tree` `apple` `eat` "John eats an apple from the tree."

### 4. The Allative Structure (Goal)

**Particle:** `ni` (Destination) Used for verbs of placement or sending.

- **Formula:** `[To Subject] + [ni Goal] + [Direct Object] + [Verb]`
- **Example:**
    > to wo ni tobo shěso topu. `SUBJ` `1SG` `ALL` `table` `book` `put` "I put the book on(to) the table."

### 5. The Comitative Structure (Association)

**Particle:** `zá` (Partner) Used for cooperative actions.

- **Formula:** `[To Subject] + [zá Partner] + [Direct Object] + [Verb]`
- **Example:**
    > to john zá shějýnshá shěso shěsonů. `SUBJ` `John` `COM` `teacher` `book` `read` "John reads the book with the teacher."

- - -
### Summary of Argument Slots

Asaxi allows you to slot these arguments freely between the Subject and the Verb. The table below shows the functional mapping.

| Slot 1 (Subject) | Slot 2 (Oblique Arg) | Slot 3 (Direct Object) | Slot 4 (Verb) | Function    |
| ---------------- | -------------------- | ---------------------- | ------------- | ----------- |
| **To Doer**      | **bă Causer**        | **Object**             | **hè-Verb**   | Imperative  |
| **To Doer**      | **då Recipient**     | **Object**             | **Verb**      | Transfer    |
| **To Doer**      | **izo Source**       | **Object**             | **Verb**      | Removal     |
| **To Doer**      | **ni Goal**          | **Object**             | **Verb**      | Placement   |
| **To Doer**      | **zá Partner**       | **Object**             | **Verb**      | Cooperation |

## 6. Complex Structures: Compounds & Lists

Asaxi syntax allows for high-density information within the argument slots by using **Compound Particles** and **Nominal Lists**.

### A. The Transfer Compound (`dåni`)

When a verb implies both a beneficiary (Dative) and physical movement (Allative)—such as "giving," "handing," or "passing"—the particles fuse into a single block.

- **Components:** **[[då (particle)|då]]** (Recipient) + **[[ni (particle)|ni]]** (Direction).
- **Fusion:** **dåni**.
- **Meaning:** "To" (in the sense of transferring possession _towards_ someone).
- **Usage:** Preferred over simple `då` when the object physically moves from A to B.
    

**Example (Ditransitive Transfer):**

> to john dåni tom apa zèdao. `SUBJ` `John` `DAT-ALL` `Tom` `apples` `PAST-give` "John gave apples to Tom."

### B. Argument Lists (The `ja` Conjunction)

Multiple nouns can occupy a single argument slot using the connective particle **[[ja (particle)|ja]]**.

- **Rule:** The Relational Particle (e.g., `zá`, `då`, `bă`) is placed **once** at the beginning of the list. It applies to every noun in the chain.
- **Placement:** `ja` appears only before the final item.

**Formula:**

> `[Particle] [Noun A], [Noun B] ja [Noun C]`

#### Examples

**1. Subject List (Compound Doer)**

> john ja tom dåni jýnma jágoma zèdao. `John` `AND` `Tom` `DAT-ALL` `hyenas` `blueberries` `PAST-give` "John and Tom gave the hyenas blueberries."

**2. Oblique List (Compound Recipient)**

> to john dåni tom, jerry ja barry apa zèdao. `SUBJ` `John` `DAT-ALL` `Tom` `Jerry` `AND` `Barry` `apples` `PAST-give` "John gave apples to Tom, Jerry, and Barry."

**3. Object List (Compound Theme)**

> to john dåni tom apa ja jága zèdao. `SUBJ` `John` `DAT-ALL` `Tom` `apples` `AND` `blueberries` `PAST-give` "John gave Tom apples and blueberries."

## 7. Floating Modifiers (Scope Precision)

Asaxi allows specific quantifiers and aspectual particles to "float" within the sentence structure. Consistent with Asaxi's Left-Branching noun phrases (Modifier-Head), Floating Modifiers **precede** the noun they modify.

### The Distributive Quantifiers

- **[[ojano (particle)|ojano]]** (Individually / Apiece)
- **[[jonojo (particle)|jonojo]]** (One by one / Sequential)
- **[[okonoko (particle)|okonoko]]** (Here and there / Spatial)

### Scope Rules

**1. Subject Modification:** `[Quantifier] + [To Subject] + ... + [Verb]`

- _Logic:_ The Subject group performs the action individually.
- _Example:_ jonojo wa hja pashěsonů.
    - `DIST` `We` `them(things)` `FUT-read`
    - _"We, one by one, will read them."_ (We take turns reading).


**2. Object Modification:** `... + [Quantifier] + [Object] + [Verb]`
- _Logic:_ The Object group is processed individually.
- _Example:_ to wo jonojo shěsa pashěsonů.
    - `SUBJ` `1SG` `DIST` `books` `FUT-read`
    - _"I will read the books one by one."_ (I read Book A, then Book B).


**3. Oblique Modification:** `... + [Quantifier] + [då/zá/bă Noun] + ...`

- _Logic:_ The oblique participants are treated individually.
- _Example:_ to wo jonojo då sháma shěso zèdao.
    - `SUBJ` `1SG` `DIST` `DAT` `people` `book` `PAST-give`
    - _"I gave a book to the people, one by one."_ (To Person A, then to Person B).

### Syntax Summary

|Modifier Type|Position|Direction of Modification|Examples|
|---|---|---|---|
|**NPCP (Case)**|Pre-Noun|→ Right (Noun)|`to`, `sè`, `bă`, `då`|
|**Floating Quantifier**|**Pre-Noun**|→ Right (Noun)|`ojano`, `jonojo`|
