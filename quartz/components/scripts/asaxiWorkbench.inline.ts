const workbenchFrames = new Set<HTMLIFrameElement>()

function resizeWorkbench(frame: HTMLIFrameElement, height: number) {
  if (!Number.isFinite(height) || height < 320 || height > 100_000) return
  // The reported document height describes the iframe's content box. Preserve
  // room for its CSS borders so they cannot create a tiny internal scrollbar.
  const iframeChrome = Math.max(0, frame.offsetHeight - frame.clientHeight)
  frame.style.height = `${Math.ceil(height + iframeChrome)}px`
  frame.dataset.workbenchSized = "true"
}

function measureWorkbench(frame: HTMLIFrameElement) {
  try {
    const document = frame.contentDocument
    if (!document) return
    resizeWorkbench(
      frame,
      Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight ?? 0),
    )
  } catch {
    // The message listener below remains available if the embedding origin changes.
  }
}

function registerWorkbenchFrames() {
  document.querySelectorAll<HTMLIFrameElement>("iframe[data-asaxi-workbench]").forEach((frame) => {
    if (workbenchFrames.has(frame)) return
    workbenchFrames.add(frame)
    frame.addEventListener("load", () => measureWorkbench(frame))
    measureWorkbench(frame)
  })
}

window.addEventListener("message", (event) => {
  const payload = event.data
  if (!payload || payload.type !== "asaxi-workbench-height") return
  for (const frame of workbenchFrames) {
    if (event.source === frame.contentWindow) {
      resizeWorkbench(frame, Number(payload.height))
      break
    }
  }
})

document.addEventListener("nav", registerWorkbenchFrames)
registerWorkbenchFrames()
