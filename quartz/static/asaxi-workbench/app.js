"use strict"

const runtimeConfig = window.ASAXI_WORKBENCH_CONFIG || {}
const apiBase = String(runtimeConfig.apiBase || "").replace(/\/$/, "")

function apiUrl(path) {
  return `${apiBase}${path}`
}

const state = {
  direction: "asaxi-to-english",
  document: null,
  focusedClauseId: null,
  selectedByClause: new Map(),
  requestController: null,
  activeTab: "tokens",
  sourceDirty: false,
  previewFrame: 0,
  apiAvailable: true,
  phraseSearchTimer: 0,
  phraseSearchController: null,
  publicPhraseIndex: null,
  developerExtensionLoaded: false,
  developerCsrfToken: null,
}

const elements = {
  source: document.querySelector("#source-text"),
  output: document.querySelector("#output-text"),
  sourceLabel: document.querySelector("#source-label"),
  outputLabel: document.querySelector("#output-label"),
  sourceCount: document.querySelector("#source-count"),
  outputCount: document.querySelector("#output-count"),
  sourceRomanizationRow: document.querySelector("#source-romanization-row"),
  sourceRomanization: document.querySelector("#source-romanization-text"),
  outputRomanizationRow: document.querySelector("#output-romanization-row"),
  outputRomanization: document.querySelector("#output-romanization-text"),
  translate: document.querySelector("#translate-button"),
  swap: document.querySelector("#swap-button"),
  copy: document.querySelector("#copy-button"),
  copyFeedback: document.querySelector("#copy-feedback"),
  theme: document.querySelector("#theme-toggle"),
  resultStatus: document.querySelector("#result-status"),
  databaseStatus: document.querySelector("#database-status"),
  diagnostics: document.querySelector("#diagnostics"),
  clauseDisclosure: document.querySelector("#clause-focus-disclosure"),
  clauseList: document.querySelector("#clause-list"),
  clauseCurrent: document.querySelector("#clause-focus-current"),
  clauseCount: document.querySelector("#clause-focus-count"),
  interpretationsDisclosure: document.querySelector("#interpretations-disclosure"),
  interpretationsHeading: document.querySelector("#interpretations-heading"),
  interpretationsCurrent: document.querySelector("#interpretations-current"),
  interpretationsCount: document.querySelector("#interpretations-count"),
  interpretationsList: document.querySelector("#interpretations-list"),
  interlinearDisclosure: document.querySelector("#interlinear-disclosure"),
  interlinearHeading: document.querySelector("#interlinear-heading"),
  interlinearCount: document.querySelector("#interlinear-count"),
  interlinearGrid: document.querySelector("#interlinear-grid"),
  analysisScope: document.querySelector("#analysis-scope"),
  tokenRows: document.querySelector("#token-rows"),
  tokenCount: document.querySelector("#token-count"),
  reviewCount: document.querySelector("#review-count"),
  traceCount: document.querySelector("#trace-count"),
  assumptions: document.querySelector("#assumptions-list"),
  ambiguities: document.querySelector("#ambiguities-list"),
  trace: document.querySelector("#trace-list"),
  json: document.querySelector("#json-output"),
  phrasebookDisclosure: document.querySelector("#phrasebook-disclosure"),
  phrasebookCount: document.querySelector("#phrasebook-count"),
  phraseSearchForm: document.querySelector("#phrase-search-form"),
  phraseSearchInput: document.querySelector("#phrase-search-input"),
  phraseSearchScope: document.querySelector("#phrase-search-scope"),
  phraseSearchResults: document.querySelector("#phrase-search-results"),
  developerHost: document.querySelector("#developer-extension-host"),
}

function clearNode(node) {
  node.replaceChildren()
}

function plural(count, singular, pluralForm = `${singular}s`) {
  return `${count.toLocaleString()} ${count === 1 ? singular : pluralForm}`
}

function setStatus(status, label) {
  elements.resultStatus.dataset.status = status
  elements.resultStatus.textContent = label
}

function currentClauses() {
  return state.document?.clauses || []
}

function focusedClause() {
  return currentClauses().find((clause) => clause.id === state.focusedClauseId) || null
}

function authoredChoice(match) {
  return {
    id: match.id,
    output_text: match.output_text,
    authored_translation: match.provenance,
    tokens: [],
    assumptions: [],
    ambiguities: [],
    rule_trace: [],
    _choiceKind: "authored",
  }
}

function availableInterpretations(clause = focusedClause()) {
  if (!clause) {
    return []
  }
  return [
    ...(clause.translation.authored_matches || []).map(authoredChoice),
    ...clause.translation.alternatives,
  ]
}

function selectedAlternative(clause = focusedClause()) {
  if (!clause) {
    return null
  }
  const selectedId =
    state.selectedByClause.get(clause.id) || clause.translation.selected_alternative_id
  const choices = availableInterpretations(clause)
  return choices.find((alternative) => alternative.id === selectedId) || choices[0] || null
}

function selectedInterlinear(clause = focusedClause()) {
  const alternative = selectedAlternative(clause)
  if (!clause || !alternative) {
    return []
  }
  return clause.interlinear_by_alternative[alternative.id] || []
}

function composeOutput() {
  if (!state.document) {
    return ""
  }
  let output = state.document.leading_text
  state.document.clauses.forEach((clause) => {
    const alternative = selectedAlternative(clause)
    output +=
      alternative?.output_text || clause.translation.fallback_output_text || clause.source_text
    output += clause.separator_after
  })
  return output
}

function renderOutput() {
  const output = composeOutput()
  elements.output.value = output
  elements.outputCount.textContent = plural(output.length, "char")
  const outputIsAsaxi = state.direction === "english-to-asaxi"
  elements.outputRomanizationRow.classList.toggle("is-inactive", !outputIsAsaxi)
  elements.outputRomanization.textContent = outputIsAsaxi ? output : ""
}

function updateSourcePreview() {
  state.previewFrame = 0
  const text = elements.source.value
  elements.sourceCount.textContent = plural(text.length, "char")
  const sourceIsAsaxi = state.direction === "asaxi-to-english"
  elements.sourceRomanizationRow.classList.toggle("is-inactive", !sourceIsAsaxi)
  elements.sourceRomanization.textContent = sourceIsAsaxi ? text : ""
}

function scheduleSourcePreview() {
  if (state.previewFrame) {
    return
  }
  state.previewFrame = requestAnimationFrame(updateSourcePreview)
}

function resetDocument() {
  state.document = null
  state.focusedClauseId = null
  state.selectedByClause.clear()
  state.sourceDirty = false
  elements.output.value = ""
  renderAll()
}

function setDirection(direction, { reset = true } = {}) {
  if (direction === state.direction && !reset) {
    return
  }
  state.direction = direction
  document.querySelectorAll(".direction-button").forEach((button) => {
    const active = button.dataset.direction === direction
    button.classList.toggle("is-active", active)
    button.setAttribute("aria-pressed", String(active))
  })
  const sourceIsAsaxi = direction === "asaxi-to-english"
  elements.sourceLabel.textContent = sourceIsAsaxi ? "Source · Asaxi" : "Source · English"
  elements.outputLabel.textContent = sourceIsAsaxi ? "Output · English" : "Output · Asaxi"
  elements.source.classList.toggle("asaxi-editor", sourceIsAsaxi)
  elements.output.classList.toggle("asaxi-editor", !sourceIsAsaxi)
  elements.source.placeholder = sourceIsAsaxi ? "JOHN apo chỏnů." : "John eats an apple."
  scheduleSourcePreview()
  if (reset) {
    resetDocument()
  }
  refreshPhraseSearch()
}

function statusLabel() {
  if (!state.document) {
    return ["idle", "Ready"]
  }
  if (state.sourceDirty) {
    return ["idle", "Source changed · translate to refresh"]
  }
  const counts = state.document.counts
  const bestEffortCount = state.document.clauses.filter(
    (clause) =>
      clause.translation.status === "unsupported" && clause.translation.fallback_output_text,
  ).length
  const authoredCount = state.document.clauses.filter(
    (clause) => (clause.translation.authored_matches || []).length > 0,
  ).length
  const authoredSenseChoices = state.document.clauses.filter(
    (clause) => (clause.translation.authored_matches || []).length > 1,
  ).length
  if (authoredSenseChoices) {
    return ["ambiguous", `Choose an authored sense · ${plural(authoredSenseChoices, "clause")}`]
  }
  if (state.document.status === "unsupported" && authoredCount) {
    return ["partial", "Authored match available · grammar unsupported"]
  }
  if (state.document.status === "partial" && authoredCount) {
    return ["partial", `Authored output available · ${plural(authoredCount, "clause")}`]
  }
  if (state.document.status === "ok") {
    return ["ok", `Complete · ${plural(counts.clauses, "clause")}`]
  }
  if (state.document.status === "ambiguous") {
    return ["ambiguous", `Review available · ${plural(counts.review, "clause")}`]
  }
  if (state.document.status === "partial") {
    if (bestEffortCount) {
      return ["partial", `Best effort · ${plural(bestEffortCount, "clause")} needs review`]
    }
    return ["partial", `Partial translation · ${plural(counts.unsupported, "unsupported clause")}`]
  }
  if (bestEffortCount) {
    return ["partial", "Best effort · review unresolved structure"]
  }
  return ["unsupported", "Unsupported · review diagnostics"]
}

function makeChoice({ checked, title, subtitle, stateText, stateClass, onSelect }) {
  const button = document.createElement("button")
  button.type = "button"
  button.className = "choice"
  button.setAttribute("role", "radio")
  button.setAttribute("aria-checked", String(checked))
  button.tabIndex = checked ? 0 : -1

  const radio = document.createElement("span")
  radio.className = "radio-mark"
  radio.setAttribute("aria-hidden", "true")

  const copy = document.createElement("span")
  copy.className = "choice-copy"
  const strong = document.createElement("strong")
  strong.textContent = title
  const small = document.createElement("small")
  small.textContent = subtitle
  copy.append(strong, small)

  const badge = document.createElement("span")
  badge.className = `choice-state ${stateClass || ""}`.trim()
  badge.textContent = stateText

  button.append(radio, copy, badge)
  button.addEventListener("click", onSelect)
  return button
}

function enableRadioNavigation(container) {
  container.querySelectorAll('[role="radio"]').forEach((choice) => {
    choice.addEventListener("keydown", (event) => {
      const choices = Array.from(container.querySelectorAll('[role="radio"]'))
      const index = choices.indexOf(choice)
      let target = null
      if (event.key === "ArrowDown" || event.key === "ArrowRight") {
        target = choices[(index + 1) % choices.length]
      } else if (event.key === "ArrowUp" || event.key === "ArrowLeft") {
        target = choices[(index - 1 + choices.length) % choices.length]
      } else if (event.key === "Home") {
        target = choices[0]
      } else if (event.key === "End") {
        target = choices[choices.length - 1]
      }
      if (target) {
        event.preventDefault()
        target.focus()
        target.click()
      }
    })
  })
}

function focusClause(clauseId, { selectSource = false } = {}) {
  if (!currentClauses().some((clause) => clause.id === clauseId)) {
    return
  }
  state.focusedClauseId = clauseId
  elements.interpretationsDisclosure.open = false
  elements.interlinearDisclosure.open = false
  renderClauseList()
  renderFocusedClause()
  if (selectSource && !state.sourceDirty) {
    const clause = focusedClause()
    elements.source.focus({ preventScroll: true })
    elements.source.setSelectionRange(clause.span.start, clause.span.end)
  }
}

function renderClauseList() {
  const clauses = currentClauses()
  elements.clauseDisclosure.hidden = clauses.length === 0
  clearNode(elements.clauseList)
  if (!clauses.length) {
    elements.clauseCurrent.textContent = "No translated document"
    elements.clauseCount.textContent = "0 clauses"
    return
  }
  const current = focusedClause() || clauses[0]
  elements.clauseCurrent.textContent = current.source_text
  elements.clauseCount.textContent = `Clause ${current.index + 1} of ${clauses.length}`
  clauses.forEach((clause) => {
    const status = clause.translation.status
    const hasAuthored = (clause.translation.authored_matches || []).length > 0
    const bestEffort = status === "unsupported" && clause.translation.fallback_output_text
    const button = makeChoice({
      checked: clause.id === current.id,
      title: `Clause ${clause.index + 1}`,
      subtitle: clause.source_text,
      stateText:
        hasAuthored && status === "unsupported"
          ? "Authored · grammar unsupported"
          : hasAuthored
            ? "Authored available"
            : bestEffort
              ? "Best effort"
              : status === "ok"
                ? "Complete"
                : status === "ambiguous"
                  ? "Review"
                  : "Unsupported",
      stateClass: bestEffort ? "partial" : status,
      onSelect: () => focusClause(clause.id, { selectSource: true }),
    })
    elements.clauseList.appendChild(button)
  })
  enableRadioNavigation(elements.clauseList)
}

function interpretationCaption(alternative) {
  if (alternative.authored_translation) {
    return alternative.authored_translation.verified
      ? "✓ Human-authored and reviewed"
      : "Human-authored draft"
  }
  const selected = alternative.ambiguities.map((ambiguity) => ambiguity.selected).filter(Boolean)
  if (selected.length) {
    return selected.join(" · ")
  }
  if (alternative.assumptions.length) {
    return plural(alternative.assumptions.length, "assumption")
  }
  return "Deterministic interpretation"
}

function renderInterpretations() {
  const clause = focusedClause()
  const alternatives = availableInterpretations(clause)
  const hasAuthored = (clause?.translation.authored_matches || []).length > 0
  elements.interpretationsDisclosure.hidden = alternatives.length < 2 && !hasAuthored
  clearNode(elements.interpretationsList)
  if (!alternatives.length || (alternatives.length < 2 && !hasAuthored)) {
    return
  }
  const selected = selectedAlternative(clause)
  elements.interpretationsHeading.textContent = `Interpretations · Clause ${clause.index + 1}`
  elements.interpretationsCurrent.textContent = selected?.output_text || "No selection"
  elements.interpretationsCount.textContent = plural(alternatives.length, "output")
  alternatives.forEach((alternative) => {
    const checked = alternative.id === selected?.id
    const button = makeChoice({
      checked,
      title: alternative.output_text,
      subtitle: interpretationCaption(alternative),
      stateText: checked ? "Selected" : "Available",
      stateClass: checked ? "ambiguous" : "",
      onSelect: () => {
        state.selectedByClause.set(clause.id, alternative.id)
        renderOutput()
        renderInterpretations()
        renderFocusedAnalysis()
      },
    })
    elements.interpretationsList.appendChild(button)
  })
  enableRadioNavigation(elements.interpretationsList)
}

function renderInterlinear() {
  const clause = focusedClause()
  const records = selectedInterlinear(clause)
  elements.interlinearDisclosure.hidden = records.length === 0
  clearNode(elements.interlinearGrid)
  if (!records.length) {
    return
  }
  elements.interlinearHeading.textContent = `Interlinear gloss · Clause ${clause.index + 1}`
  elements.interlinearCount.textContent = plural(records.length, "token")
  records.forEach((record) => {
    const token = document.createElement("article")
    token.className = "interlinear-token"
    const surface = document.createElement("span")
    surface.className = "interlinear-surface"
    surface.lang = "x-asaxi"
    surface.textContent = record.surface
    const morphemes = document.createElement("span")
    morphemes.className = "interlinear-morphemes"
    morphemes.textContent = record.morphemes.join(" + ")
    const gloss = document.createElement("span")
    gloss.className = "interlinear-gloss"
    gloss.textContent = record.gloss
    token.append(surface, morphemes, gloss)
    elements.interlinearGrid.appendChild(token)
  })
}

function renderDiagnostics() {
  const clause = focusedClause()
  const diagnostics = clause?.translation.diagnostics || []
  clearNode(elements.diagnostics)
  if (!state.document) {
    elements.diagnostics.hidden = true
    return
  }
  if (!currentClauses().length) {
    const row = document.createElement("div")
    row.className = "diagnostic-item"
    row.textContent = "No translatable clause was found in the document."
    elements.diagnostics.appendChild(row)
  } else {
    diagnostics.forEach((diagnostic) => {
      const row = document.createElement("div")
      row.className = "diagnostic-item"
      const code = document.createElement("span")
      code.className = "diagnostic-code"
      code.textContent = diagnostic.code
      const message = document.createElement("span")
      const location =
        diagnostic.token_index === null ? "" : ` Token ${diagnostic.token_index + 1}:`
      message.textContent = `${location} ${diagnostic.message}`.trim()
      row.append(code, message)
      elements.diagnostics.appendChild(row)
    })
  }
  elements.diagnostics.hidden = elements.diagnostics.childElementCount === 0
}

function featureElements(features) {
  const list = document.createElement("div")
  list.className = "feature-list"
  const entries = Object.entries(features || {})
  if (!entries.length) {
    list.textContent = "—"
    return list
  }
  entries.forEach(([name, value]) => {
    const feature = document.createElement("span")
    feature.className = "feature"
    feature.textContent = `${name}: ${value}`
    list.appendChild(feature)
  })
  return list
}

function renderTokenTable() {
  const alternative = selectedAlternative()
  const interlinear = selectedInterlinear()
  const interlinearByIndex = new Map(interlinear.map((record) => [record.token_index, record]))
  clearNode(elements.tokenRows)
  const tokens = alternative?.tokens || []
  elements.tokenCount.textContent = String(tokens.length)
  if (!tokens.length) {
    const row = document.createElement("tr")
    const cell = document.createElement("td")
    cell.colSpan = 6
    cell.className = "empty"
    cell.textContent = "No token analysis for this clause"
    row.appendChild(cell)
    elements.tokenRows.appendChild(row)
    return
  }
  tokens.forEach((token) => {
    const record = interlinearByIndex.get(token.index)
    const analysis = token.morphology[0] || null
    const row = document.createElement("tr")
    const values = [
      token.surface,
      token.role || "—",
      record?.lemma || analysis?.lemma || token.normalized,
      record?.morphemes?.join(" + ") || analysis?.morphemes?.join(" + ") || token.surface,
    ]
    values.forEach((value, index) => {
      const cell = document.createElement("td")
      cell.textContent = value
      if (index === 0) {
        const sourceIsAsaxi = state.direction === "asaxi-to-english"
        cell.className = "token-surface"
        cell.classList.toggle("is-asaxi", sourceIsAsaxi)
        cell.classList.toggle("is-english", !sourceIsAsaxi)
        cell.lang = sourceIsAsaxi ? "x-asaxi" : "en"
      } else if (index === 2 || index === 3) {
        cell.className = "mono"
      }
      row.appendChild(cell)
    })
    const features = document.createElement("td")
    features.appendChild(featureElements(record?.features || analysis?.features || {}))
    const provenance = document.createElement("td")
    provenance.className = "mono"
    provenance.textContent = record?.provenance || "surface"
    row.append(features, provenance)
    elements.tokenRows.appendChild(row)
  })
}

function renderIssueList(container, items, kind) {
  clearNode(container)
  if (!items.length) {
    const empty = document.createElement("p")
    empty.className = "panel-intro"
    empty.textContent = "None"
    container.appendChild(empty)
    return
  }
  items.forEach((item) => {
    const article = document.createElement("article")
    article.className = `issue ${kind}`
    const code = document.createElement("strong")
    code.className = "issue-code"
    code.textContent = item.code
    const message = document.createElement("p")
    const selected = item.selected ? ` Selected: ${item.selected}.` : ""
    message.textContent = `${item.message}${selected}`
    article.append(code, message)
    container.appendChild(article)
  })
}

function renderIssues() {
  const alternative = selectedAlternative()
  const assumptions = alternative?.assumptions || []
  const ambiguities = alternative?.ambiguities || []
  elements.reviewCount.textContent = String(assumptions.length + ambiguities.length)
  renderIssueList(elements.ambiguities, ambiguities, "ambiguity")
  renderIssueList(elements.assumptions, assumptions, "assumption")
}

function renderTrace() {
  const trace = selectedAlternative()?.rule_trace || []
  elements.traceCount.textContent = String(trace.length)
  clearNode(elements.trace)
  if (!trace.length) {
    const item = document.createElement("li")
    item.textContent = "No grammar trace for this clause"
    elements.trace.appendChild(item)
    return
  }
  trace.forEach((rule) => {
    const item = document.createElement("li")
    item.textContent = rule
    elements.trace.appendChild(item)
  })
}

function renderRawJson() {
  if (state.activeTab !== "json") {
    return
  }
  if (!state.document) {
    elements.json.textContent = "No translation result"
    return
  }
  elements.json.textContent = JSON.stringify(
    {
      ...state.document,
      client_selection: Object.fromEntries(state.selectedByClause),
      composed_output_text: composeOutput(),
      focused_clause_id: state.focusedClauseId,
    },
    null,
    2,
  )
}

function renderFocusedAnalysis() {
  const clause = focusedClause()
  elements.analysisScope.textContent = clause
    ? `Analysis · Clause ${clause.index + 1} of ${currentClauses().length}`
    : "Analysis · no focused clause"
  renderInterlinear()
  renderTokenTable()
  renderIssues()
  renderTrace()
  renderRawJson()
}

function renderFocusedClause() {
  renderInterpretations()
  renderDiagnostics()
  renderFocusedAnalysis()
}

function renderAll() {
  renderOutput()
  renderClauseList()
  renderFocusedClause()
  const [status, label] = statusLabel()
  setStatus(status, label)
}

function applyDocument(payload) {
  state.document = payload
  state.sourceDirty = false
  state.selectedByClause.clear()
  payload.clauses.forEach((clause) => {
    const selected =
      clause.translation.authored_matches?.[0]?.id || clause.translation.selected_alternative_id
    if (selected) {
      state.selectedByClause.set(clause.id, selected)
    }
  })
  state.focusedClauseId = payload.selected_clause_id || payload.clauses[0]?.id || null
  elements.clauseDisclosure.open = false
  elements.interpretationsDisclosure.open = false
  elements.interlinearDisclosure.open = false
  renderAll()
}

async function translate() {
  if (state.requestController) {
    state.requestController.abort()
  }
  const controller = new AbortController()
  state.requestController = controller
  elements.translate.disabled = true
  setStatus("loading", "Translating document")
  try {
    const response = await fetch(apiUrl("/api/translate-document"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        direction: state.direction,
        text: elements.source.value,
      }),
      signal: controller.signal,
    })
    const payload = await response.json()
    if (!response.ok) {
      throw new Error(payload.message || "Translation request failed")
    }
    applyDocument(payload)
  } catch (error) {
    if (error.name === "AbortError") {
      return
    }
    state.document = null
    state.focusedClauseId = null
    state.selectedByClause.clear()
    renderAll()
    setStatus("error", error.message || "Translation service error")
  } finally {
    if (state.requestController === controller) {
      state.requestController = null
      elements.translate.disabled = false
    }
  }
}

function publicPhraseIndexUrl() {
  return new URL(
    runtimeConfig.publicPhraseIndex || "./authored-phrases.public.json",
    document.baseURI,
  ).href
}

async function loadPublicPhraseIndex() {
  if (state.publicPhraseIndex) {
    return state.publicPhraseIndex
  }
  const response = await fetch(publicPhraseIndexUrl())
  if (!response.ok) {
    throw new Error("Published phrase index is unavailable")
  }
  const payload = await response.json()
  state.publicPhraseIndex = Array.isArray(payload.entries)
    ? payload.entries.filter((entry) => entry.verified)
    : []
  return state.publicPhraseIndex
}

function normalizePhraseLayout(text) {
  return String(text || "")
    .normalize("NFC")
    .replace(/\u00a0/gu, " ")
    .trim()
    .replace(/\s+/gu, " ")
    .replace(/\s+([,.;:!?])/gu, "$1")
}

function phraseSearchKey(text) {
  return normalizePhraseLayout(text).toLowerCase()
}

function staticPhraseSearch(entries, query) {
  const normalizedQuery = normalizePhraseLayout(query)
  const needle = phraseSearchKey(normalizedQuery)
  const direction = state.direction
  return entries
    .filter((entry) => entry.direction === direction)
    .map((entry) => {
      const forms = [entry.source_text, ...(entry.variants || [])]
      const exact = forms.find((form) => form === normalizedQuery)
      const caseInsensitive = forms.find((form) => !exact && phraseSearchKey(form) === needle)
      const sourceMatch = forms.find((form) => phraseSearchKey(form).includes(needle))
      const targetMatch = phraseSearchKey(entry.target_text).includes(needle)
      const rank = !needle
        ? 5
        : exact
          ? 0
          : caseInsensitive
            ? 1
            : sourceMatch
              ? 2
              : targetMatch
                ? 3
                : 9
      return {
        ...entry,
        authored: true,
        matched_text:
          exact || caseInsensitive || sourceMatch || (targetMatch ? entry.target_text : ""),
        match_kind: !needle
          ? "browse"
          : exact
            ? forms.indexOf(exact) === 0
              ? "canonical"
              : "variant"
            : caseInsensitive
              ? "case-insensitive-search"
              : sourceMatch
                ? "source-contains"
                : targetMatch
                  ? "translation-contains"
                  : "none",
        _rank: rank,
      }
    })
    .filter((entry) => entry._rank < 9)
    .sort(
      (left, right) =>
        left._rank - right._rank || left.source_text.localeCompare(right.source_text),
    )
    .slice(0, 50)
}

function renderPhraseResults(results, { unavailable = false } = {}) {
  clearNode(elements.phraseSearchResults)
  if (unavailable) {
    const message = document.createElement("p")
    message.className = "phrase-empty"
    message.textContent = "The reviewed phrase index is unavailable."
    elements.phraseSearchResults.appendChild(message)
    return
  }
  if (!results.length) {
    const message = document.createElement("p")
    message.className = "phrase-empty"
    message.textContent = elements.phraseSearchInput.value.trim()
      ? "No reviewed authored phrase matches this search."
      : "No reviewed authored phrases are published in this direction yet."
    elements.phraseSearchResults.appendChild(message)
    return
  }
  results.forEach((result) => {
    const item = document.createElement("article")
    item.className = "phrase-result"
    const heading = document.createElement("div")
    heading.className = "phrase-result-heading"
    const source = document.createElement("strong")
    source.className =
      result.direction === "asaxi-to-english"
        ? "phrase-result-source is-asaxi"
        : "phrase-result-source"
    source.lang = result.direction === "asaxi-to-english" ? "x-asaxi" : "en"
    source.textContent = result.source_text
    const verified = document.createElement("span")
    verified.className = "verified-label"
    verified.title = "Human-authored and reviewed translation"
    verified.setAttribute("aria-label", "Human-authored and reviewed")
    const mark = document.createElement("span")
    mark.className = "verified-mark"
    mark.setAttribute("aria-hidden", "true")
    mark.textContent = "✓"
    const label = document.createElement("span")
    label.textContent = "Authored"
    verified.append(mark, label)
    heading.append(source, verified)
    const target = document.createElement("p")
    target.className =
      result.direction === "english-to-asaxi"
        ? "phrase-result-target is-asaxi"
        : "phrase-result-target"
    target.lang = result.direction === "english-to-asaxi" ? "x-asaxi" : "en"
    target.textContent = result.target_text
    const meta = document.createElement("small")
    meta.className = "phrase-result-meta"
    const matchDescriptions = {
      browse: "Reviewed phrase translation",
      canonical: "Exact canonical phrase",
      variant: `Matched reviewed variant: ${result.matched_text}`,
      "case-insensitive-search": `Case-insensitive search only: ${result.matched_text}`,
      "source-prefix": `Source begins with: ${result.matched_text}`,
      "source-contains": `Source contains: ${result.matched_text}`,
      "translation-contains": `Translation contains: ${result.matched_text}`,
      "token-overlap": `Related source words: ${result.matched_text}`,
    }
    meta.textContent = matchDescriptions[result.match_kind] || "Reviewed phrase translation"
    item.append(heading, target, meta)
    elements.phraseSearchResults.appendChild(item)
  })
}

async function searchPhrases() {
  if (state.phraseSearchController) {
    state.phraseSearchController.abort()
  }
  const controller = new AbortController()
  state.phraseSearchController = controller
  const query = elements.phraseSearchInput.value.trim()
  elements.phraseSearchScope.textContent =
    state.direction === "asaxi-to-english"
      ? "Reviewed Asaxi → English phrases"
      : "Reviewed English → Asaxi phrases"
  try {
    let results
    if (state.apiAvailable) {
      const params = new URLSearchParams({
        q: query,
        direction: state.direction,
      })
      const response = await fetch(apiUrl(`/api/phrases/search?${params}`), {
        signal: controller.signal,
      })
      if (!response.ok) {
        throw new Error("Phrase search request failed")
      }
      const payload = await response.json()
      results = payload.results || []
    } else {
      results = staticPhraseSearch(await loadPublicPhraseIndex(), query)
    }
    renderPhraseResults(results)
  } catch (error) {
    if (error.name !== "AbortError") {
      try {
        state.apiAvailable = false
        const entries = await loadPublicPhraseIndex()
        renderPhraseResults(staticPhraseSearch(entries, query))
      } catch {
        renderPhraseResults([], { unavailable: true })
      }
    }
  } finally {
    if (state.phraseSearchController === controller) {
      state.phraseSearchController = null
    }
  }
}

function refreshPhraseSearch() {
  window.clearTimeout(state.phraseSearchTimer)
  state.phraseSearchTimer = window.setTimeout(searchPhrases, 180)
}

async function loadDeveloperExtension() {
  if (state.developerExtensionLoaded) {
    return
  }
  state.developerExtensionLoaded = true
  const moduleUrl = new URL("./developer.js", document.baseURI).href
  const developer = await import(moduleUrl)
  await developer.initializeDeveloperPhraseAuthoring({
    apiUrl,
    state,
    elements,
    focusedClause,
    selectedAlternative,
    refreshPhraseSearch,
  })
}

async function loadHealth() {
  try {
    const response = await fetch(apiUrl("/api/health"))
    if (!response.ok) {
      throw new Error("Translation API unavailable")
    }
    const payload = await response.json()
    state.apiAvailable = true
    const stats = payload.statistics
    const grammar = payload.grammar_model
    const coverage = payload.grammar_coverage || {}
    const coverageSummary = coverage.summary || {}
    const sourceSnapshotStatus = grammar.source_snapshot_status || grammar.status
    const grammarLabel = grammar.model_version
      ? `grammar ${grammar.model_version} | ${grammar.updated_on}`
      : "grammar unversioned"
    const verifiedNotes = coverageSummary.behaviorally_verified
    const totalNotes = coverageSummary.total
    const coverageLabel =
      Number.isInteger(verifiedNotes) && Number.isInteger(totalNotes)
        ? `${verifiedNotes}/${totalNotes} notes verified`
        : "coverage unavailable"
    elements.databaseStatus.dataset.sourceSnapshotStatus = sourceSnapshotStatus
    elements.databaseStatus.textContent =
      `${stats.lexemes.toLocaleString()} lexemes | ` +
      `${stats.morphemes.toLocaleString()} morphemes | ${grammarLabel} | ` +
      coverageLabel +
      (sourceSnapshotStatus === "source-drift" ? " | notes changed" : "")
    elements.databaseStatus.title =
      `Grammar source snapshot: ${sourceSnapshotStatus}\n` +
      `Implementation coverage: ${coverageLabel}\n` +
      `Coverage source: ${coverage.source_digest || "not recorded"}\n` +
      `Current source: ${grammar.current_source_digest}\n` +
      `Validated with Workshop: ` +
      `${grammar.validated_with_workbench_version || "not recorded"}`
    const phrases = payload.phrase_memory || {}
    state.developerCsrfToken = phrases.csrf_token || null
    elements.phrasebookCount.textContent = plural(phrases.verified_count || 0, "entry", "entries")
    if (phrases.writable) {
      await loadDeveloperExtension()
    }
    refreshPhraseSearch()
  } catch {
    state.apiAvailable = false
    delete elements.databaseStatus.dataset.sourceSnapshotStatus
    elements.databaseStatus.textContent = "Static phrasebook mode"
    elements.translate.disabled = true
    elements.translate.title = "Full translation requires the Asaxi Workbench API"
    try {
      const entries = await loadPublicPhraseIndex()
      elements.phrasebookCount.textContent = plural(entries.length, "entry", "entries")
    } catch {
      elements.phrasebookCount.textContent = "Unavailable"
    }
    refreshPhraseSearch()
  }
}

function focusClauseFromSelection() {
  if (!state.document || state.sourceDirty) {
    return
  }
  const start = elements.source.selectionStart
  const end = elements.source.selectionEnd
  const clauses = currentClauses()
  let candidate = clauses.find((clause) => start >= clause.span.start && start < clause.span.end)
  if (end > start) {
    candidate = clauses
      .map((clause) => ({
        clause,
        overlap: Math.max(0, Math.min(end, clause.span.end) - Math.max(start, clause.span.start)),
      }))
      .sort((left, right) => right.overlap - left.overlap)[0]
    candidate = candidate?.overlap ? candidate.clause : null
  }
  if (candidate && candidate.id !== state.focusedClauseId) {
    focusClause(candidate.id)
  }
}

function switchTab(tabName) {
  state.activeTab = tabName
  document.querySelectorAll(".tab").forEach((tab) => {
    const active = tab.dataset.tab === tabName
    tab.classList.toggle("is-active", active)
    tab.setAttribute("aria-selected", String(active))
    tab.tabIndex = active ? 0 : -1
  })
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.hidden = panel.id !== `${tabName}-panel`
  })
  renderRawJson()
}

document.querySelectorAll(".direction-button").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.direction !== state.direction) {
      setDirection(button.dataset.direction)
    }
  })
})

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => switchTab(button.dataset.tab))
  button.addEventListener("keydown", (event) => {
    const tabs = Array.from(document.querySelectorAll(".tab"))
    const index = tabs.indexOf(button)
    let target = null
    if (event.key === "ArrowRight") {
      target = tabs[(index + 1) % tabs.length]
    } else if (event.key === "ArrowLeft") {
      target = tabs[(index - 1 + tabs.length) % tabs.length]
    } else if (event.key === "Home") {
      target = tabs[0]
    } else if (event.key === "End") {
      target = tabs[tabs.length - 1]
    }
    if (target) {
      event.preventDefault()
      target.focus()
      target.click()
    }
  })
})

elements.source.addEventListener("input", () => {
  scheduleSourcePreview()
  if (state.document) {
    state.sourceDirty = elements.source.value !== state.document.input_text
    const [status, label] = statusLabel()
    setStatus(status, label)
  }
})
;["click", "keyup", "select"].forEach((eventName) => {
  elements.source.addEventListener(eventName, focusClauseFromSelection)
})

elements.source.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    translate()
  }
})

elements.translate.addEventListener("click", translate)

elements.phraseSearchForm.addEventListener("submit", (event) => {
  event.preventDefault()
  searchPhrases()
})

elements.phraseSearchInput.addEventListener("input", refreshPhraseSearch)

elements.phrasebookDisclosure.addEventListener("toggle", () => {
  if (elements.phrasebookDisclosure.open) {
    searchPhrases()
  }
})

elements.swap.addEventListener("click", () => {
  const output = elements.output.value
  const direction = state.direction === "asaxi-to-english" ? "english-to-asaxi" : "asaxi-to-english"
  setDirection(direction, { reset: false })
  elements.source.value = output
  resetDocument()
  scheduleSourcePreview()
  elements.source.focus()
})

elements.copy.addEventListener("click", async () => {
  if (!elements.output.value) {
    return
  }
  try {
    await navigator.clipboard.writeText(elements.output.value)
  } catch {
    elements.output.select()
    document.execCommand("copy")
  }
  elements.copyFeedback.textContent = "Copied"
  window.setTimeout(() => {
    elements.copyFeedback.textContent = ""
  }, 1600)
})

elements.theme.addEventListener("click", () => {
  const root = document.documentElement
  const current = root.getAttribute("saved-theme")
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches
  const effectiveDark = current ? current === "dark" : systemDark
  const next = effectiveDark ? "light" : "dark"
  root.setAttribute("saved-theme", next)
  elements.theme.textContent = next === "dark" ? "☀" : "☾"
  elements.theme.setAttribute(
    "aria-label",
    next === "dark" ? "Switch to light theme" : "Switch to dark theme",
  )
  try {
    localStorage.setItem("asaxi-workbench-theme", next)
  } catch {}
})

setDirection(state.direction, { reset: false })
switchTab("tokens")
renderAll()
updateSourcePreview()
loadHealth()
