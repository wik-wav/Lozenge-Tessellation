import { FullSlug, SimpleSlug, joinSegments, pathToRoot, resolveRelative } from "../../util/path"

type LexSense = { en: string; pl: string }

type LexEntry = {
  slug: SimpleSlug
  word: string
  type: string
  senses: LexSense[] // ordered; a word may have several meanings (polysemy)
  freq: number | null
  fields: string[]
}

let DATA: LexEntry[] | null = null
const collator = new Intl.Collator(undefined, { sensitivity: "base", numeric: true })

// Latin-alphabetical fold so accented Asaxi letters sort/search by their base.
function fold(s: string): string {
  return (s || "")
    .toLowerCase()
    .replace(/ŋ/g, "ng")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
}

function esc(s: string): string {
  return (s || "").replace(
    /[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] as string,
  )
}

// the headword field can hold variants ("să, 1") -> compare each token
function wordTokens(w: string): string[] {
  return fold(w)
    .split(/[,;/]/)
    .map((t) => t.trim())
    .filter(Boolean)
}

// Relevance of an already-matching entry for query q:
// 0 = exact headword, 1 = headword prefix, 2 = headword contains,
// 3 = English gloss contains, 4 = only the Polish gloss contains.
// Keeps "să" itself above entries that merely contain "sa" in a gloss.
function tier(e: LexEntry, q: string): number {
  const toks = wordTokens(e.word)
  if (toks.some((t) => t === q)) return 0
  if (toks.some((t) => t.startsWith(q))) return 1
  if (fold(e.word).includes(q)) return 2
  if (e.senses.some((s) => fold(s.en).includes(q))) return 3
  return 4
}

// index of the first sense whose gloss matches q (-1 if none)
function senseMatch(e: LexEntry, q: string): number {
  return e.senses.findIndex((s) => fold(s.en).includes(q) || fold(s.pl).includes(q))
}

async function setup(container: Element, currentSlug: FullSlug) {
  const search = container.querySelector(".lex-search") as HTMLInputElement
  const typeSel = container.querySelector(".lex-type") as HTMLSelectElement
  const fieldSel = container.querySelector(".lex-field") as HTMLSelectElement
  const sortSel = container.querySelector(".lex-sort") as HTMLSelectElement
  const list = container.querySelector(".lex-list") as HTMLDivElement
  const stats = container.querySelector(".lex-stats") as HTMLDivElement
  if (!search || !list) return

  // "open the real search" button in the note (native quartz search bar)
  const openSearch = container.querySelector(".lex-open-search") as HTMLButtonElement | null
  if (openSearch) {
    const nativeBtn = document.querySelector(".search .search-button") as HTMLButtonElement | null
    if (nativeBtn) openSearch.onclick = () => nativeBtn.click()
    else openSearch.style.display = "none"
  }

  if (!DATA) {
    const url = joinSegments(pathToRoot(currentSlug), "static/lexicon.json")
    try {
      DATA = (await fetch(url).then((r) => r.json())) as LexEntry[]
    } catch {
      stats.textContent = "Could not load the lexicon data."
      return
    }
  }
  const data = DATA ?? []

  if (typeSel.options.length <= 1) {
    for (const t of [...new Set(data.map((e) => e.type))].sort(collator.compare)) {
      const o = document.createElement("option")
      o.value = t
      o.textContent = t
      typeSel.appendChild(o)
    }
    for (const f of [...new Set(data.flatMap((e) => e.fields))].sort(collator.compare)) {
      const o = document.createElement("option")
      o.value = f
      o.textContent = f
      fieldSel.appendChild(o)
    }
  }

  const PAGE = 60
  let shown = PAGE
  let current: LexEntry[] = []
  let lastQ = ""
  const more = container.querySelector(".lex-more") as HTMLButtonElement | null

  // one <li> per sense, numbered — same nested-list pattern as the grammar book
  const sensesHtml = (e: LexEntry) =>
    `<ul class="lex-senses">` +
    e.senses
      .map(
        (s, i) =>
          `<li><span class="lex-sense-n">${i + 1}.</span>` +
          `<span class="lex-sense-en">${esc(s.en)}</span>` +
          (s.pl ? `<span class="lex-sense-pl">${esc(s.pl)}</span>` : "") +
          `</li>`,
      )
      .join("") +
    `</ul>`

  const rowTail = (e: LexEntry) =>
    `<span class="lex-badge">${esc(e.type)}</span>` +
    `<span class="lex-gloss">${esc(e.senses[0]?.en ?? "")}</span>` +
    (e.senses.length > 1 ? `<span class="lex-count">${e.senses.length}</span>` : "") +
    (e.freq != null ? `<span class="lex-freq" title="frequency rating">${e.freq}</span>` : "")

  const mkEntry = (e: LexEntry): HTMLElement => {
    const href = resolveRelative(currentSlug, e.slug)
    if (e.senses.length <= 1) {
      // single sense: a plain link row, exactly as before
      const a = document.createElement("a")
      a.className = "lex-row"
      a.href = href
      a.innerHTML = `<span class="lex-word">${esc(e.word)}</span>` + rowTail(e)
      return a
    }
    // several senses: grammar-book style <details>; the headword stays a link
    const det = document.createElement("details")
    det.className = "lex-entry"
    det.innerHTML =
      `<summary class="lex-row">` +
      `<a class="lex-word" href="${esc(href)}">${esc(e.word)}</a>` +
      rowTail(e) +
      `</summary>` +
      sensesHtml(e)
    // if the query matched a later sense, open so the hit is visible
    if (lastQ && senseMatch(e, lastQ) > 0) det.open = true
    return det
  }

  const paint = () => {
    const slice = current.slice(0, shown)
    const frag = document.createDocumentFragment()
    for (const e of slice) frag.appendChild(mkEntry(e))
    list.replaceChildren(frag)
    stats.textContent =
      `showing ${slice.length} of ${current.length}` +
      (current.length !== data.length ? ` · ${data.length} total` : "")
    const remaining = current.length - slice.length
    if (more) {
      more.style.display = remaining > 0 ? "" : "none"
      more.textContent = remaining > 0 ? `Show more (${remaining} more)` : "Show more"
    }
  }

  const applyFilters = () => {
    const q = fold(search.value.trim())
    const t = typeSel.value
    const f = fieldSel.value
    const sort = sortSel.value
    lastQ = q

    current = data.filter((e) => {
      if (t && e.type !== t) return false
      if (f && !e.fields.includes(f)) return false
      if (q) {
        const hay =
          fold(e.word) +
          " " +
          e.senses.map((s) => fold(s.en) + " " + fold(s.pl)).join(" ")
        if (!hay.includes(q)) return false
      }
      return true
    })

    let cmp: (a: LexEntry, b: LexEntry) => number
    if (sort === "alpha-desc") cmp = (a, b) => collator.compare(b.word, a.word)
    else if (sort === "freq-desc")
      cmp = (a, b) => (b.freq ?? -1) - (a.freq ?? -1) || collator.compare(a.word, b.word)
    else if (sort === "freq-asc")
      cmp = (a, b) => (a.freq ?? 101) - (b.freq ?? 101) || collator.compare(a.word, b.word)
    else cmp = (a, b) => collator.compare(a.word, b.word)

    // with a query, rank by how the entry matched (headword before glosses);
    // the chosen sort still orders entries within each relevance tier
    if (q) current.sort((a, b) => tier(a, q) - tier(b, q) || cmp(a, b))
    else current.sort(cmp)

    shown = PAGE
    paint()
  }

  search.oninput = applyFilters
  typeSel.onchange = applyFilters
  fieldSel.onchange = applyFilters
  sortSel.onchange = applyFilters
  if (more) more.onclick = () => { shown += PAGE; paint() }
  applyFilters()
}

document.addEventListener("nav", async (e: CustomEventMap["nav"]) => {
  const currentSlug = e.detail.url
  const container = document.querySelector(".lexicon-browser")
  if (container) await setup(container, currentSlug)
})
