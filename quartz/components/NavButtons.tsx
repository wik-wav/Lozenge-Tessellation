import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { resolveRelative, SimpleSlug } from "../util/path"
// @ts-ignore
import style from "./styles/navButtons.scss"

export type NavButton = {
  title: string
  slug: string
  accent?: boolean
}

export interface NavButtonsOptions {
  buttons: NavButton[]
}

const defaultOptions: NavButtonsOptions = { buttons: [] }

export default ((userOpts?: Partial<NavButtonsOptions>) => {
  const opts = { ...defaultOptions, ...userOpts }
  const NavButtons: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
    if (opts.buttons.length === 0) return null
    return (
      <nav class={classNames(displayClass, "nav-buttons")}>
        {opts.buttons.map((b) => (
          <a
            href={resolveRelative(fileData.slug!, b.slug as SimpleSlug)}
            class={`nav-button${b.accent ? " accent" : ""}`}
            data-slug={b.slug}
          >
            {b.title}
          </a>
        ))}
      </nav>
    )
  }
  NavButtons.css = style
  return NavButtons
}) satisfies QuartzComponentConstructor
