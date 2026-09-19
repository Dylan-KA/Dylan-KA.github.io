# Dylan Archer Portfolio

This is the source code for my personal portfolio website, built with [Eleventy](https://www.11ty.dev/).

## Project Structure

The project has been refactored to use Nunjucks templating for better maintainability.

- **`_data/`**: Contains global data files.
  - `projects.json`: Stores all project data (title, description, links, images). **Add new projects here.**
  - `site.js`: Global site data (e.g., current year).
- **`_includes/`**: Contains Nunjucks templates.
  - `layout.njk`: The main base layout for all pages.
  - `components/`: Reusable components (Navigation, Footer, ProjectCard, etc.).
- **`html/`**: Contains the individual page templates.
  - `index.html`: The home page, which loops through `projects.json` to display projects.
  - `[ProjectName].html`: Individual project pages.
- **`css/`**: CSS files, organized by component/section.
- **`.eleventy.js`**: Eleventy configuration file.

## How to Add a New Project

1.  Open `_data/projects.json`.
2.  Add a new entry to the appropriate category array (e.g., "games", "web").
    ```json
    {
      "title": "My New Project",
      "link": "MyProject.html",
      "img": "Images/...",
      "logos": ["Images/Logos/Tool.png"],
      "description": "Description here..."
    }
    ```
3.  Create a new HTML file in `html/` (e.g., `MyProject.html`).
4.  Add the front matter:
    ```html
    ---
    layout: layout.njk
    title: My New Project
    permalink: "{{ page.fileSlug }}.html"
    ---
    ```
5.  Add your page content.

## Local Development

1.  **Install dependencies:**
    ```powershell
    npm ci
    ```

2.  **Run the development server:**
    ```powershell
    npx @11ty/eleventy --serve
    ```
    The site will be available at `http://localhost:8080`.

## Deployment

The site is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.
See `.github/workflows/deploy.yml` for details.
