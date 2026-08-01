import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import style from "./styles/asaxiWorkbench.scss"

export default (() => {
  const AsaxiWorkbench: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <section class={classNames(displayClass, "asaxi-workbench-embed")}>
        <iframe
          src="./static/asaxi-workbench/index.html"
          title="Asaxi translation and phrase workbench"
          allow="clipboard-write"
        />
        <p class="asaxi-workbench-fallback">
          If the embedded tool does not load,{" "}
          <a href="./static/asaxi-workbench/index.html">open Asaxi Workbench directly</a>.
        </p>
      </section>
    )
  }
  AsaxiWorkbench.css = style
  return AsaxiWorkbench
}) satisfies QuartzComponentConstructor
