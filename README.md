# The Lozenge Tessellation

This repository hosts the source content and configuration for **The Lozenge Tessellation** worldbuilding project, generated using [Quartz 4](https://quartz.jzhao.xyz/).

**Live Site:** [https://wik-wav.github.io/lozenge-tessellation/](https://wik-wav.github.io/lozenge-tessellation/)

## Project Structure

- **`content/`**: Contains the Obsidian vault, including the Asaxi language lexicon, grammar documentation, and worldbuilding notes.
- **`quartz/`**: The internal logic and components for the static site generator.
- **`quartz.config.ts`**: Configuration for plugins, themes, and server settings.
- **`quartz.layout.ts`**: Definitions for page layouts (headers, footers, sidebars).

## Asaxi Typeface

Quartz embeds the single real Medium face of **Asaxi Merriweather 24pt**
from `quartz/static/fonts/Asaxi-alphabet-Merriweather24pt-Medium.ttf`.
`quartz/styles/custom.scss` applies it only to semantic Asaxi text:

- `.asaxi-script-alpha`
- `.asaxi-text`
- `[lang="art-x-asaxi"]`
- lexicon-browser headwords (`.lexicon-browser .lex-word`)

The face has no separate bold or italic files. The stylesheet therefore
disables synthetic bold and italic for these selectors. English and Polish
prose continue to use the site theme fonts.

## Local Development

To preview the site locally or make structural changes:

### 1. Prerequisites

- [Node.js](https://nodejs.org/) (v22 or higher)
- npm (comes with Node.js)

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone [https://github.com/wik-wav/lozenge-tessellation.git](https://github.com/wik-wav/lozenge-tessellation.git)
cd lozenge-tessellation
npm install
```

### 3. Running the Server

Start a local preview server. This will watch for changes in the content/ folder and auto-refresh.

```
npx quartz build --serve
```

### Deployment

This repository uses GitHub Actions to automatically build and deploy the site to GitHub Pages.

To publish changes:

1. Save your Markdown files in content/.
2. Commit and push to the repository:

```
npx quartz sync
```

## License & Protocol

### The Asaxi Language (Content)

The **Asaxi language**, worldbuilding lore, and all documentation within the `content/` directory are dedicated to the public domain under the **Creative Commons Zero v1.0 Universal (CC0)** waiver.

This means Asaxi is designed as an open **protocol**:

- **Permissionless:** You are free to speak, write, modify, remix, and build upon this linguistic system for any purpose (including commercial) without asking for permission.
- **Attribution:** While not legally required, attribution to **wik_wav** is appreciated as it helps track the lineage of the protocol.
- **Compatibility:** To maintain intelligibility with the core framework, please refer to the grammar documentation in this repository.

### The Engine (Software)

The underlying source code for this site generator (Quartz) remains under the **MIT License** (see `LICENSE.txt`).
