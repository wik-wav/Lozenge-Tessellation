import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import style from "./styles/lexiconBrowser.scss"
// @ts-ignore
import script from "./scripts/lexiconBrowser.inline"
import { classNames } from "../util/lang"

export default (() => {
  const LexiconBrowser: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <div class={classNames(displayClass, "lexicon-browser")}>
        <div class="lex-controls">
          <input
            class="lex-search"
            type="text"
            placeholder="Search a word or its translation…"
            autocomplete="off"
            aria-label="Search the lexicon"
          />
          <select class="lex-type" aria-label="Filter by word type">
            <option value="">all types</option>
          </select>
          <select class="lex-field" aria-label="Filter by semantic field">
            <option value="">all semantic fields</option>
          </select>
          <select class="lex-sort" aria-label="Sort">
            <option value="alpha">sort: A → Z</option>
            <option value="alpha-desc">sort: Z → A</option>
            <option value="freq-desc">sort: most frequent</option>
            <option value="freq-asc">sort: least frequent</option>
          </select>
        </div>
        <div class="lex-note">
          <span>
            Every entry — including all its senses — is meant to be findable here. If you are
            certain a word exists but it does not show up, try the site-wide search.
          </span>
          <button
            class="lex-open-search"
            type="button"
            title="Open the site-wide search (Ctrl+K)"
            aria-label="Open the site-wide search"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 19.9 19.7"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              aria-hidden="true"
            >
              <path stroke-linecap="square" d="M18.5 18.3l-5.4-5.4" />
              <circle cx="8" cy="8" r="7" />
            </svg>
          </button>
        </div>
        <div class="lex-stats"></div>
        <div class="lex-list"></div>
        <button class="lex-more" type="button" style="display:none">
          Show more
        </button>
      </div>
    )
  }
  LexiconBrowser.afterDOMLoaded = script
  LexiconBrowser.css = style
  return LexiconBrowser
}) satisfies QuartzComponentConstructor
