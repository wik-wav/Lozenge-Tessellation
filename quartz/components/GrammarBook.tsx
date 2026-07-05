import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { resolveRelative, FullSlug } from "../util/path"
// @ts-ignore
import style from "./styles/grammarBook.scss"

type Doc = { numStr: string; num: number; letter: string; token: string; title: string; slug: FullSlug }

const collator = new Intl.Collator(undefined, { sensitivity: "base", numeric: true })

// A shared trailing "(...)" across a group's titles becomes its label (e.g. "Morphological Infix").
function sharedParenthetical(titles: string[]): string {
  const parens = titles.map((t) => {
    const m = t.match(/\(([^)]+)\)\s*$/)
    return m ? m[1].trim() : null
  })
  return parens.length > 0 && parens.every((p) => p && p === parens[0]) ? (parens[0] as string) : ""
}

export default (() => {
  const GrammarBook: QuartzComponent = ({ allFiles, fileData, displayClass }: QuartzComponentProps) => {
    const docs: Doc[] = []
    for (const f of allFiles) {
      const fp = f.filePath
      if (!fp || !fp.includes("Grammar_Structure/") || !f.slug) continue
      const base = fp.split("/").pop()!.replace(/\.md$/, "")
      // leading number (any length), optional letter suffix, underscore, then the title
      const m = base.match(/^(\d+)([A-Za-z]*)_(.+)$/)
      if (!m) continue // exclude anything without a leading number
      docs.push({
        numStr: m[1],
        num: parseInt(m[1], 10),
        letter: m[2],
        token: m[1] + m[2],
        title: m[3].trim().replace(/_/g, " \u2014 "), // internal underscores -> em dash for display
        slug: f.slug,
      })
    }

    const chapters = docs.filter((d) => d.letter === "")
    const groups = new Map<string, Doc[]>()
    for (const d of docs.filter((d) => d.letter !== "")) {
      const arr = groups.get(d.token) ?? []
      arr.push(d)
      groups.set(d.token, arr)
    }

    type Node =
      | { kind: "chapter"; num: number; letter: string; doc: Doc }
      | { kind: "group"; num: number; letter: string; token: string; docs: Doc[] }
    const nodes: Node[] = [
      ...chapters.map((d): Node => ({ kind: "chapter", num: d.num, letter: "", doc: d })),
      ...[...groups.entries()].map(
        ([token, arr]): Node => ({
          kind: "group",
          num: arr[0].num,
          letter: arr[0].letter,
          token,
          docs: arr.sort((a, b) => collator.compare(a.title, b.title)),
        }),
      ),
    ]
    // order by number, then letter (pure "" before "A" etc.), then title tiebreak
    nodes.sort(
      (a, b) =>
        a.num - b.num ||
        a.letter.localeCompare(b.letter) ||
        collator.compare(a.kind === "chapter" ? a.doc.title : "", b.kind === "chapter" ? b.doc.title : ""),
    )

    const href = (slug: FullSlug) => resolveRelative(fileData.slug!, slug)

    return (
      <div class={classNames(displayClass, "grammar-book")}>
        <ul class="grammar-toc">
          {nodes.map((n) =>
            n.kind === "chapter" ? (
              <li class="gb-chapter">
                <a href={href(n.doc.slug)}>
                  <span class="gb-num">{n.doc.numStr}</span>
                  <span class="gb-title">{n.doc.title}</span>
                </a>
              </li>
            ) : (
              <li class="gb-group">
                <details>
                  <summary>
                    <span class="gb-num">{n.token}</span>
                    <span class="gb-title">{sharedParenthetical(n.docs.map((d) => d.title))}</span>
                    <span class="gb-count">{n.docs.length}</span>
                  </summary>
                  <ul>
                    {n.docs.map((d) => (
                      <li>
                        <a href={href(d.slug)}>{d.title}</a>
                      </li>
                    ))}
                  </ul>
                </details>
              </li>
            ),
          )}
        </ul>
      </div>
    )
  }
  GrammarBook.css = style
  return GrammarBook
}) satisfies QuartzComponentConstructor
