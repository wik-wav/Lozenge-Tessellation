import { FullSlug, SimpleSlug, joinSegments, pathToRoot, resolveRelative } from "../../util/path"

type LexEntry = {
  slug: SimpleSlug
  word: string
  type: string
  en: string
  pl: string
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

async function setup(container: Element, currentSlug: FullSlug) {
  const search = container.querySelector(".lex-search") as HTMLInputElement
  const typeSel = container.querySelector(".lex-type") as HTMLSelectElement
  const fieldSel = container.querySelector(".lex-field") as HTMLSelectElement
  const sortSel = container.querySelector(".lex-sort") as HTMLSelectElement
  const list = container.querySelector(".lex-list") as HTMLDivElement
  const stats = container.querySelector(".lex-stats") as HTMLDivElement
  if (!search || !list) return

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
  const more = container.querySelector(".lex-more") as HTMLButtonElement | null

  const rowHtml = (e: LexEntry) =>
    `<span class="lex-word">${esc(e.word)}</span>` +
    `<span class="lex-badge">${esc(e.type)}</span>` +
    `<span class="lex-gloss">${esc(e.en)}</span>` +
    (e.freq != null ? `<span class="lex-freq" title="frequency rating">${e.freq}</span>` : "")

  const paint = () => {
    const slice = current.slice(0, shown)
    const frag = document.createDocumentFragment()
    for (const e of slice) {
      const a = document.createElement("a")
      a.className = "lex-row"
      a.href = resolveRelative(currentSlug, e.slug)
      a.innerHTML = rowHtml(e)
      frag.appendChild(a)
    }
    list.replaceChildren(frag)
    stats.textContent =
      `showing ${slice.length} of ${current.length}` +
      (current.length !== data.length ? ` \u00b7 ${data.length} total` : "")
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

    current = data.filter((e) => {
      if (t && e.type !== t) return false
      if (f && !e.fields.includes(f)) return false
      if (q) {
        const hay = fold(e.word) + " " + fold(e.en) + " " + fold(e.pl)
        if (!hay.includes(q)) return false
      }
      return true
    })

    if (sort === "alpha") current.sort((a, b) => collator.compare(a.word, b.word))
    else if (sort === "alpha-desc") current.sort((a, b) => collator.compare(b.word, a.word))
    else if (sort === "freq-desc")
      current.sort((a, b) => (b.freq ?? -1) - (a.freq ?? -1) || collator.compare(a.word, b.word))
    else if (sort === "freq-asc")
      current.sort((a, b) => (a.freq ?? 101) - (b.freq ?? 101) || collator.compare(a.word, b.word))

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
