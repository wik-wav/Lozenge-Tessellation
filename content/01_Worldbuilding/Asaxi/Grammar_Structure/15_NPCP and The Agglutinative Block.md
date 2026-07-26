---
title: 15_NPCP and The Agglutinative Block
tags:
  - Asaxi
  - language
  - grammar
  - grammar_concept
---
Navigation:
- [[00_Structural Sets in Asaxi| Back to Structural Sets in Asaxi]]
 
- - - 

# Grammatical Concept: Noun-Preceding Case-Particles (NPCP) & The Agglutinative Block

Asaxi utilizes a system of **Noun-Preceding Case-Particles (NPCP)** to manage case marking, noun modification, and syntactic roles. Noun phrases operate on a strict **Left-Branching Agglutinative** logic.

This system allows for the creation of an **Agglutinative Particle Block**: a chain of prefixes that defines exactly "what" the noun is doing, "what" it is made of, and "where" it is, before the noun is even spoken.

## Rules

**1. Particle Classification** There are two types of NPCPs, distinguished by their binding strength to the **Noun**:

- **Relational Particles (Case):** These define the syntactic role of the noun (e.g., Subject, Owner, Tool, Direction). They stand as separate words if followed immediately by a Noun.
- **Fusing Particles (Lexical):** Specifically the particle `ga`. This particle modifies the meaning of the noun itself (creating a compound/attribute). It **always** fuses with the following element.

**2. The Fusion Rule (The Block)** **Any** particle followed immediately by another particle must fuse into a single block, regardless of type.

- **Relational + Relational:** They merge (e.g., `måmå` + `ni` → `måmåni`).
- **Relational + Fusing:** They merge (e.g., `to` + `ga` → `toga`).
- **Particle + Locative Prefix:** They merge via a bridge (e.g., `izo` + `o-` → `izowo-`).
- **Exception (The Break):** If a **Relational Particle** is followed directly by a **Head Noun**, fusion stops, and they remain separated by a space (e.g., `ni shěsokam`).

**3. Vowel Hiatus** 
1. If the Attributive particle `ga` and the following noun both start with `a`, they merge,
	- Eg. `ga` + `apo` (red) = `gapo`
2. If the Attributive particle `ga` is followed by any other vowel, hiatus is **allowed**,
	- Eg. `ga` + `o` (blue) = gao
3. Bridges (w/x) are only strictly required when attaching to Locative Prefixes.

## Syntactic Structure

**Formula (Maximal Expansion):**
	`[Determiner]+[Agglutinative Block]−[Head Noun]`

**The Particle Block Internal Order:**
	`[Relational Stack]+[Attributive ga]+[Modifier Noun]+[Bridge]+[Locative Prefix]`

**Logic:** The "Role" (Case) wraps the "Definition" (Attribute/Modifier), which wraps the "Position" (Locative), which attaches to the "Object" (Head Noun).

### The Inventory

| Particle | Type       | Function          | Meaning / English Equivalent        |
| -------- | ---------- | ----------------- | ----------------------------------- |
| **[[to (particle)\|to]]**   | Relational | **Nominative**    | Subject marker (Objective).         |
| **[[ă (particle)\|ă]]**    | Relational | **Subjective**    | Subject marker (Internal/Felt).     |
| **[[dhè (particle)\|dhè]]**  | Relational | **Topic/Patient** | Passive Voice marker.               |
| **[[sè (particle)\|sè]]**   | Relational | **Genitive**      | Of / 's / Belonging to.             |
| **[[bă (particle)\|bă]]**   | Relational | **Instrumental**  | Using / With / Because of (Causal). |
| **[[zá (particle)\|zá]]**   | Relational | **Comitative**    | With / Accompanied by.              |
| **[[då (particle)\|då]]**   | Relational | **Dative**        | To / For (recipient).               |
| **[[ni (particle)\|ni]]**   | Relational | **Allative**      | To / Towards (destination).         |
| **[[izo (particle)\|izo]]**  | Relational | **Ablative**      | From / Out of (source).             |
| **[[måmå (particle)\|måmå]]** | Relational | **Terminative**   | Until / Up to (limit).              |
| **[[ăni (particle)\|ăni]]**  | Relational | **Topical**       | About / Concerning / Regarding.     |
| **[[ga (particle)\|ga]]**   | Fusing     | **Attributive**   | Made of / -type (lexical modifier). |
### 1.1 The Dual Function of `to`

The particle **to** serves two distinct functions depending on its position:
1. **Subject Marker:** When it initiates a Noun Phrase.
2. **Nominal Linker:** When it follows a Relational Particle block, connecting it to the head noun.

**Exception: The Genitive Zero-Link** When using the Genitive particle **[[sè (particle)|sè]]** (Of/Belonging to), the linker `to` is **optional** and frequently dropped. The possession relationship is considered strong enough to bind the phrase directly to the Head Noun.

- **Full Form:** `sè john to shěso` ("John's book").
- **Efficient Form:** `sè john shěso` ("John's book").

- - - 

1. Basic Modification (The Compound) _Context: A book made of blue material (Bluebook)._
	 gaoshěso. 
	`ATTR-blue-book` 
	"Blue-book."
2. Relational Case (Simple) _Context: John (as the possessor)._
	**Sè John**.
	`ASSOC John` 
	"Of John"
3. The Passive Topic (`dhè`) _Context: The tree (as the receiver of chopping)._
	 dhè kjèpo... `TOP` `tree` 
	 _"The tree (was)..."_
4. The Fused Block (Complex)** _Context: The red book (which is the Subject) located here._
	toonýj gapowo-shěso... `
	SUBJ DEF.COLD ATTR-red-here-book
	`_"The Red-Here-Book (Subject)..."_
5. Nested Structure (Possession of a Modified Noun) _Context: I see John's green book._
	 to wo sè john gavishěso ijo. 
	 `SUBJ` `1SG` `ASSOC` `John` `ATTR-green-book` `see` 
	_"I see John's green-book."_
6. Motion Towards (`ni`) _Context: I am going to the library._
	- _Note: `ni` acts as a relational particle followed by a noun, so a space is used._
	to wo ni shěsokam xoxo. 
	`SUBJ` `1SG` `ALL` `library` `depart` 
	_"I depart to the library."_
7. Motion From (`izo`) _Context: The book is from the library._
	- _Note: `izo` fuses with the locative prefix `o-` via the bridge `w`._
	onýj o-shěso izowo-shěsokam xiŕa. 
	`DEF.COLD` `here-book` `ABL-here-library` `EXIST` 
	_"The book is from-the-library-here."_
8. Complex Path (Relational Stacking)** 
   _Context: I walk from the house up to the tree._
	- _Note: `måmå` (Until) and `ni` (To) are both Relational Particles. Per Rule 2, they fuse into `måmåni`._
	izo kamm måmåni kjèpo aśù. 
	`ABL` building TERM-ALL tree walk
	"I walk from building as-far-as-to tree."
9. **The Topical Argument (`ăni`)**
	 To wo ăni no ŕima. `SUBJ` `1SG` `[ABOUT` `2SG]` `think` _"I think **about you**."_

### Ga-Modified Noun and Adjectival Noun Disambiguation

Because the `ga` particle creates descriptive words, it is easy to confuse it with the standard morphological adjective system (suffixes `-nă` / `-nýj`). However, they carry distinct semantic logic.

- **Morphological Adjectives (Simile):** Describe **Behavior** or **Abstract Quality**. They imply the subject acts _like_ the root or shares a trait with it.

- **Ga-Modified Nouns (Constitution):** Describe **Biology**, **Material**, or **Category**. They imply the subject _is_ physically made of or classified as the root.


**Comparative Examples** _Root Word: **jýnnshá** (Hyena)_

1. The Morphological Adjective (Behavior)
	john jýnă shá xiŕa. 
	`John hyena-ADJ person EXIST`
	_"John is a chatty person."_
	 **Logic:** John is a person, he behaves **like** a hyena (he is talkative/loud).

2. The Ga-Modified Noun (Classification)
	 john gajýnnshá xiŕa. 
	 `John ATTR-hyena-person EXIST` 
	 _"John is a hyena-person."_
	 **Logic:** John is a specific **type** of creature (perhaps a hybrid or a specific clan member). It defines his essential constitution, not just his personality.

3. The Root Identity (Fact)
 	john jýnnshá xiŕa. 
 	`John hyena EXIST` 
 	_"John is a hyena."_
 	**Logic:** John is _not_ a human. He is literally a hyena.

### 5. Predicative NPCPs (The Validity Slot Integration)

While Relational Particles usually appear before a noun to mark its case, they can also be **moved** to the end of the sentence, placing them immediately before the Stative Particle (**xiŕa**).

When placed here, they fuse with `xiŕa`. This changes the definition of the relationship with the assertion of existence, creating complex "To Be" predicates.

**The Logic:** Instead of saying "The book exists \[of John\]" (Adjectival), you say "The book \[is-of\] John" (Predicative). , 
1. Note that if you decide to drop `xiŕa` entirely, the NPCP doesn't have anywhere to go, so it stays with John Eg.
	- John sèŕa - John's
	- Sè John. - John's

#### The Predicative Fusion Table

When a Relational Particle meets **xiŕa**, they fuse into a single Predicative Verb.

| Particle | Base Meaning   | + **xiŕa** (Fusion) | Definition / Translation              |
| -------- | -------------- | ------------------- | ------------------------------------- |
| **sè**   | Of / Belonging | **sèŕa**            | To be owned by / To be yours          |
| **då**   | For / To       | **dåŕa**            | To be for / To be intended for        |
| **izo**  | From           | **izoŕa**           | To be from / To originate from        |
| **bă**   | By / Using     | **băŕa**            | To be caused by / To be made by       |
| **zá**   | With           | **záŕa**            | To be with / To accompany             |
| **ni**   | Towards        | **nìŕa**            | To be leading to / To be destined for |

#### Usage Examples

**1. Predicative Possession (sèŕa)**
> to shěso john sèŕa. `SUBJ` `book` `John` `POSS-EXIST` "The book belongs to John." (Lit: The book is-of John).

**2. Predicative Origin (izoŕa)**
> to wo shěsokam izoŕa. `SUBJ` `1SG` `library` `ABL-EXIST` "I am from the library." (Lit: I exist-from the library).

**3. Predicative Purpose (dåŕa)**
> to apo john dåŕa. `SUBJ` `apple` `John` `DAT-EXIST` "The apple is for John."

---

### 6. Epistemic Stacking (The Truth Layer)

These Predicative NPCPs can further stack with **Validity Particles** (such as **ná** "Not" or **xă** "Indeed") to form a dense **Epistemic Block**. This allows the speaker to assert the truth, falsehood, or probability of the relationship in a single final word.

**The Hierarchy:**

> `[Polarity/Truth]` + `[Relational Case]` + `[xiŕa]`

When stacking, the Polarity particle attaches to the front of the fused Predicate. Take note of how `xi` is dropped from `xiŕa` in the following examples:

#### Negative Stacking (ná-)

Applies negation to the relationship.
- **sèŕa** (Belongs to) → **násèŕa** (Does not belong to).
- **dåŕa** (Is for) → **nádåŕa** (Is NOT for).

> to gaoshěso john násèŕa. "The blue book does not belong to John."

#### Emphatic Stacking (xă-)

Applies absolute certainty to the relationship.

- **izoŕa** (Is from) → **xăizoŕa** (Is INDEED from).

> wo gaŕo xăizoŕa. "I am absolutely from a city!"

#### Complex Stacking (Double Particles)

In rare cases, multiple particles may stack to express complex nuances, such as "Not made by."

- **ná** (Not) + **bă** (Instrumental) + **xiŕa** (Exist) → **nábăŕa**.

> jośýstèm jomåsháma nábăŕa. "The societal system is not made by humans.