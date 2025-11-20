# Building and Deploying this Eleventy Site

This document explains how to build the site locally with Eleventy (11ty), how to ensure files and folders are copied into the generated site using `.eleventy.js`, and how the GitHub Actions workflow (`.github/workflows/deploy.yml`) automates the build-and-deploy process.

---

## Quick local commands (PowerShell)

Install dependencies (first time or when `package-lock.json` changed):

```powershell
npm ci
```

Build the site once with Eleventy (no npm script present by default):

```powershell
npx @11ty/eleventy
```

Start Eleventy's local dev server with auto-reload:

```powershell
npx @11ty/eleventy --serve
```

Recommended: add a `build` script to `package.json` so you can run `npm run build`:

```json
// package.json (scripts)
{
  "scripts": {
    "build": "eleventy"
  }
}
```

Then run:

```powershell
npm run build
```

Notes:
- The project currently includes `@11ty/eleventy` as a dependency (see `package.json`). When you run `npm run build`, npm will find the local `eleventy` binary in `node_modules/.bin`.
- The default Eleventy output directory for this project is `_site` (configured in `.eleventy.js`). After building, check `_site/` for the generated files.

---

## Ensuring files are included in the build (passthroughs in `.eleventy.js`)

Eleventy processes templates and copies files you tell it to copy. In this project, passthrough copies are configured in `.eleventy.js` using `eleventyConfig.addPassthroughCopy()`.

Example from this project (already in `.eleventy.js`):

```js
// .eleventy.js
eleventyConfig.addPassthroughCopy("Images");
eleventyConfig.addPassthroughCopy("Scripts");
eleventyConfig.addPassthroughCopy("stylesheet.css");
eventyConfig.addPassthroughCopy("Resume.pdf");
eventyConfig.addPassthroughCopy("css");
```

How to add files or folders:
- To copy an entire folder (preserve its path):
  - `eleventyConfig.addPassthroughCopy("Images");`
- To copy a single file in the project root:
  - `eleventyConfig.addPassthroughCopy("stylesheet.css");`
- To map source -> destination (custom path in `_site`):
  - `eleventyConfig.addPassthroughCopy({ "src/somefile.png": "assets/img/somefile.png" });`

Important notes:
- Paths are relative to Eleventy's `input` directory (this project sets `input: "."` in `.eleventy.js`, so use repository-relative paths).
- Files added with `addPassthroughCopy` are copied unchanged into the output directory (`_site`), not processed by Eleventy templates.
- After updating `.eleventy.js`, re-run the build (or the dev server) so changes take effect.

---

## How the GitHub Actions workflow automates build and deploy (`.github/workflows/deploy.yml`)

The repository includes a GitHub Actions workflow that builds the site and publishes it to GitHub Pages whenever changes are pushed to `main`.

Key steps performed by the workflow:
1. Trigger: runs on `push` to the `main` branch.
2. Checkout: checks out your repository code on an Ubuntu runner.
3. Node setup: installs Node.js (the workflow sets `node-version: 18`).
4. Install dependencies: runs `npm ci` to install dependencies from `package-lock.json`.
5. Build: runs `npx @11ty/eleventy` to generate the static site into `_site`.
6. Deploy: uses `peaceiris/actions-gh-pages@v3` to publish the contents of `./_site` to GitHub Pages and (in this project) writes a CNAME to configure a custom domain (`dylan-archer-dev.com`). The action uses `${{ secrets.GITHUB_TOKEN }}` for authentication.

Why this is helpful:
- Every push to `main` automatically rebuilds the site on GitHub's servers and publishes the latest `_site` output to GitHub Pages.
- You don't need to build locally and push generated files—source is committed, build+deploy is handled by the workflow.

What to check if deployment fails:
- Ensure the workflow file is in `.github/workflows/deploy.yml` and committed to `main`.
- Confirm `node-version` matches any project requirements or adjust as needed.
- Ensure `npm ci` succeeds (valid `package-lock.json` and packages). If `npm ci` fails, try `npm install` locally to debug.
- Verify `.eleventy.js` `output` directory matches the workflow `publish_dir` (`_site` by default).
- For the `peaceiris/actions-gh-pages` step: by default it publishes to the `gh-pages` branch. If you need a different target, configure the action inputs.
- If using a custom domain: the workflow's `cname` input will create a `CNAME` record in the published branch. Double-check the domain DNS settings.

---

## Recommended local workflow

1. Pull latest code:

```powershell
git pull origin main
```

2. Install deps:

```powershell
npm ci
```

3. Build or run dev server:

```powershell
# one-time build
npx @11ty/eleventy
# dev server with live reload
npx @11ty/eleventy --serve
# or (if you added a package.json script)
npm run build
```

4. Commit changes to source files and to `.eleventy.js` passthroughs, then push to `main` to trigger GitHub Actions:

```powershell
git add .
git commit -m "Update site content or passthroughs"
git push origin main
```

---

## Short checklist when adding assets you want published

- Add the asset files to the repository under a path Eleventy can read (project root or subfolder).
- Add a matching `eleventyConfig.addPassthroughCopy("path/to/asset-or-folder")` line to `.eleventy.js`.
- Run `npx @11ty/eleventy` (or `npm run build`) locally to verify the asset appears in `_site`.
- Commit the changes and push to `main`—the GitHub Actions workflow will rebuild and deploy.

---

## Where this project configures the above

- Eleventy config file: `.eleventy.js` (contains `addPassthroughCopy` calls and `dir.input`/`dir.output` settings).
- GitHub Actions workflow: `.github/workflows/deploy.yml` (build and deploy automation).
- Local dependency: `package.json` (contains `@11ty/eleventy` dependency).
