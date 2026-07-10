import { FullSlug, SimpleSlug, joinSegments, simplifySlug } from "../../util/path"
import { QuartzEmitterPlugin } from "../types"
import { write } from "./helpers"

export type LexiconSense = { en: string; pl: string }

export type LexiconEntry = {
  slug: SimpleSlug
  word: string
  type: string
  // all senses, in order. Sense 1 = the legacy unnumbered keys
  // ("trnsltion. En" / "trnsltion. Pl"); sense N >= 2 = "trnsltion. En N".
  // See vocab_forge AGENTS.md, "Polysemy standard".
  senses: LexiconSense[]
  freq: number | null
  fields: string[]
}

const SENSE_KEY_RE = /^trnsltion\. (En|Pl)(?: (\d+))?$/

// Emits static/lexicon.json: structured vocab data for the Lexicon Browser page.
export const LexiconIndex: QuartzEmitterPlugin = () => ({
  name: "LexiconIndex",
  async *emit(ctx, content) {
    // pass 1: map each semantic-field page's simple slug -> its field name
    const fieldName = new Map<string, string>()
    for (const [, file] of content) {
      const title = (file.data.frontmatter?.title ?? "").toString()
      const slug = file.data.slug
      if (slug && title.startsWith("Smntc_Field ")) {
        fieldName.set(simplifySlug(slug) as string, title.slice("Smntc_Field ".length).trim())
      }
    }

    // pass 2: collect vocab entries from the Lexicon, Idioms and Grammar_Structure
    // folders. Grammar_Structure holds real lexeme entries too (particles,
    // pronouns, locatives, connectors, ...); doc pages there are filtered out
    // below by the required "Word (Asaxi)" field.
    const entries: LexiconEntry[] = []
    for (const [, file] of content) {
      const fm = file.data.frontmatter as Record<string, any> | undefined
      const slug = file.data.slug
      const rel = (file.data.relativePath ?? "").toString()
      if (!fm || !slug) continue
      if (!/(?:Lexicon|Idioms_Expressions|Grammar_Structure)\//.test(rel)) continue

      const stem = rel.replace(/\.md$/, "").split("/").pop() ?? ""
      const m = stem.match(/^(.+) \(([^)]+)\)$/)
      const word = (fm["Word (Asaxi)"] ?? "").toString().trim()
      if (!m || !word) continue
      const type = m[2].trim().toLowerCase()
      if (type === "list") continue

      const fields = [
        ...new Set(
          (file.data.links ?? [])
            .map((l) => fieldName.get(l as unknown as string))
            .filter((x): x is string => Boolean(x)),
        ),
      ]

      const freqRaw = fm["freq"]
      let freq: number | null = null
      if (typeof freqRaw === "number") freq = freqRaw
      else if (freqRaw != null && `${freqRaw}`.trim() !== "") {
        const n = parseInt(`${freqRaw}`, 10)
        if (Number.isFinite(n)) freq = n
      }

      // collect every sense: unnumbered keys are sense 1, "En 2"/"Pl 2" etc.
      const byN = new Map<number, LexiconSense>()
      for (const [key, val] of Object.entries(fm)) {
        const km = key.match(SENSE_KEY_RE)
        if (!km) continue
        const n = km[2] ? parseInt(km[2], 10) : 1
        const s = byN.get(n) ?? { en: "", pl: "" }
        if (km[1] === "En") s.en = (val ?? "").toString().trim()
        else s.pl = (val ?? "").toString().trim()
        byN.set(n, s)
      }
      const senses = [...byN.entries()]
        .sort((a, b) => a[0] - b[0])
        .map(([, s]) => s)
        .filter((s) => s.en !== "" || s.pl !== "")
      if (senses.length === 0) senses.push({ en: "", pl: "" })

      entries.push({
        slug: simplifySlug(slug),
        word,
        type,
        senses,
        freq,
        fields,
      })
    }

    entries.sort((a, b) => a.word.localeCompare(b.word))

    yield write({
      ctx,
      slug: joinSegments("static", "lexicon") as FullSlug,
      ext: ".json",
      content: JSON.stringify(entries),
    })
  },
})
