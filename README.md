# The Lozenge Tessellation

This repository hosts the source content and configuration for **The Lozenge Tessellation** worldbuilding project, generated using [Quartz 4](https://quartz.jzhao.xyz/).

**Live Site:** [https://wik-wav.github.io/lozenge-tessellation/](https://wik-wav.github.io/lozenge-tessellation/)

## Project Structure

* **`content/`**: Contains the Obsidian vault, including the Asaxi language lexicon, grammar documentation, and worldbuilding notes.
* **`quartz/`**: The internal logic and components for the static site generator.
* **`quartz.config.ts`**: Configuration for plugins, themes, and server settings.
* **`quartz.layout.ts`**: Definitions for page layouts (headers, footers, sidebars).

## Local Development

To preview the site locally or make structural changes:

### 1. Prerequisites
* [Node.js](https://nodejs.org/) (v20 or higher)
* npm (comes with Node.js)

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
The site will be available at http://localhost:8080.

### Deployment

This repository uses GitHub Actions to automatically build and deploy the site to GitHub Pages.

To publish changes:

1. Save your Markdown files in content/.
2. Commit and push to the repository:

```
npx quartz sync
```

### License

This project uses Quartz, which is licensed under the MIT License.
