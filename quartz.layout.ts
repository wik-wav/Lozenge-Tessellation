import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [
    Component.ConditionalRender({
      component: Component.LexiconBrowser(),
      condition: (page) => page.fileData.slug === "lexicon",
    }),
    Component.ConditionalRender({
      component: Component.GrammarBook(),
      condition: (page) => page.fileData.slug === "grammar",
    }),
    Component.ConditionalRender({
      component: Component.AsaxiWorkbench(),
      condition: (page) =>
        page.fileData.slug === "translator" || page.fileData.slug === "workbench",
    }),
  ],
  footer: Component.Footer({
    links: {
      Neocities: "https://wik-wav.neocities.org/",
      Youtube: "https://www.youtube.com/@wik_wav",
    },
  }),
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.ConditionalRender({
      component: Component.Breadcrumbs(),
      condition: (page) => page.fileData.slug !== "index",
    }),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
        { Component: Component.ReaderMode() },
      ],
    }),
    Component.NavButtons({
      buttons: [
        { title: "📖  Lexicon Browser", slug: "lexicon", accent: true },
        { title: "📘  Grammar Book", slug: "grammar" },
        { title: "⌨  Asaxi Translator", slug: "translator" },
      ],
    }),
    Component.Explorer(),
  ],
  right: [Component.DesktopOnly(Component.TableOfContents()), Component.Backlinks()],
}

// components for pages that display lists of pages  (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
      ],
    }),
    Component.NavButtons({
      buttons: [
        { title: "📖  Lexicon Browser", slug: "lexicon", accent: true },
        { title: "📘  Grammar Book", slug: "grammar" },
        { title: "⌨  Asaxi Translator", slug: "translator" },
      ],
    }),
    Component.Explorer(),
  ],
  right: [],
}
