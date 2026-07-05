import { FullSlug, SimpleSlug, joinSegments, simplifySlug } from "../../util/path"
import { QuartzEmitterPlugin } from "../types"
import { write } from "./helpers"

export type LexiconEntry = {
  slug: SimpleSlug
  word: string
  type: string
  en: string
  pl: string
  freq: number | null
  fields: string[]
}

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

    // pass 2: collect vocab entries from the Lexicon + Idioms folders
    const entries: LexiconEntry[] = []
    for (const [, file] of content) {
      const fm = file.data.frontmatter as Record<string, any> | undefined
      const slug = file.data.slug
      const rel = (file.data.relativePath ?? "").toString()
      if (!fm || !slug) continue
      if (!/(?:Lexicon|Idioms_Expressions)\//.test(rel)) continue

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

      entries.push({
        slug: simplifySlug(slug),
        word,
        type,
        en: (fm["trnsltion. En"] ?? "").toString(),
        pl: (fm["trnsltion. Pl"] ?? "").toString(),
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
