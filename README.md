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
The OpenType typographic family is `Asaxi Merriweather 24pt`; its full face
name is `Asaxi Merriweather 24pt Medium`.
`quartz/styles/custom.scss` applies it only to semantic Asaxi text:

- `.asaxi-script-alpha`
- `.asaxi-text`
- `[lang="art-x-asaxi"]`
- lexicon-browser headwords (`.lexicon-browser .lex-word`)

The face has no separate bold or italic files. The stylesheet therefore
disables synthetic bold and italic for these selectors. English and Polish
prose continue to use the site theme fonts.

To publish a new alphabet font export everywhere, place it at the documented
FontLab export location and run the central updater:

```powershell
py -3.14 -X utf8 D:\wyash\Documents\Lozenge-T-Vault\99_Tools\font_manager\update_asaxi_font.py
```

The same updater is prepared for an optional future `AsaxiAbugida.ttf`. Use
`--check` for a read-only checksum and identity audit.

## Asaxi Translator

The left navigation places **Asaxi Translator** directly below **Grammar
Book**. The `/translator` page embeds the public Workbench bundle from
`quartz/static/asaxi-workbench/`.

The static bundle includes verified authored-phrase search and the same Python
Workbench translator under a pinned, self-hosted Pyodide runtime. Translation
runs in a background worker; developer phrase authoring remains local-only.
Re-export the public bundle through the central font updater above before
publishing translator or font changes. Pyodide's MPL-2.0 notice is published
in `quartz/static/asaxi-workbench/THIRD_PARTY_NOTICES.txt`.

After building, validate all generated local links and embedded assets:

```powershell
py -3.14 -X utf8 D:\wyash\Documents\Lozenge-T-Vault\99_Tools\check_quartz_links.py `
  D:\wyash\Documents\HTML\Lozenge_Vault\quartz\public `
  --base-path lozenge-tessellation
```

## Local Development

The authoritative Obsidian vault is the separate local directory
`D:\wyash\Documents\Lozenge-T-Vault\Lozenge-T-Notes`. The `content/`
directory in this Quartz checkout is a publication mirror. Before building,
update that mirror with the checked synchronization tool in the tools
workspace:

```powershell
py -3.14 D:\wyash\Documents\Lozenge-T-Vault\99_Tools\sync_quartz_content.py `
  --quartz D:\wyash\Documents\HTML\Lozenge_Vault\quartz `
  --apply
```

Omit `--apply` for a read-only drift check. The tool copies only changed or
missing files, rejects symlinks, and does not delete target-only files unless
`--prune` is supplied explicitly.

`npx quartz sync` is Quartz's Git publication command. It does **not**
synchronize the authoritative local Obsidian vault into `content/`.
The synchronization check also rejects case-only Git-index drift, which would
otherwise produce broken links after a Windows build is deployed to Linux.

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

To prepare local content and verify a production build:

1. Update the authoritative `Lozenge-T-Notes` vault.
2. Run the local synchronization command above with `--apply`.
3. Build the site:

```powershell
npx quartz build
```

Git commits, pushes, and deployment remain separate operations.

## License & Protocol

### The Asaxi Language (Content)

The **Asaxi language**, worldbuilding lore, and all documentation within the `content/` directory are dedicated to the public domain under the **Creative Commons Zero v1.0 Universal (CC0)** waiver.

This means Asaxi is designed as an open **protocol**:

- **Permissionless:** You are free to speak, write, modify, remix, and build upon this linguistic system for any purpose (including commercial) without asking for permission.
- **Attribution:** While not legally required, attribution to **wik_wav** is appreciated as it helps track the lineage of the protocol.
- **Compatibility:** To maintain intelligibility with the core framework, please refer to the grammar documentation in this repository.

### The Engine (Software)

The underlying source code for this site generator (Quartz) remains under the **MIT License** (see `LICENSE.txt`).
