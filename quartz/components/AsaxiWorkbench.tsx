import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import style from "./styles/asaxiWorkbench.scss"
// @ts-ignore
import script from "./scripts/asaxiWorkbench.inline"

export default (() => {
  const AsaxiWorkbench: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <section class={classNames(displayClass, "asaxi-workbench-embed")}>
        <iframe
          src="./static/asaxi-workbench/index.html?embed=browser-python-2"
          title="Asaxi Translator"
          allow="clipboard-write"
          scrolling="no"
          data-asaxi-workbench
        />
        <p class="asaxi-workbench-fallback">
          If the embedded tool does not load,{" "}
          <a href="./static/asaxi-workbench/index.html?embed=browser-python-2">
            open Asaxi Translator directly
          </a>
          .
        </p>
      </section>
    )
  }
  AsaxiWorkbench.css = style
  AsaxiWorkbench.afterDOMLoaded = script
  return AsaxiWorkbench
}) satisfies QuartzComponentConstructor
