# Fernando’s portfolio

This is a static website made with HTML, CSS, and a small amount of plain JavaScript. The deployable site is the `dist/` directory. It has no package installation or build step.

## Files

| Path | What to edit |
| --- | --- |
| `dist/index.html` | Homepage introduction, About, contact copy, and navigation |
| `dist/content.js` | Selected-work card titles, descriptions, images, and case-study links |
| `dist/app.js` | Renders the cards from `content.js`; usually does not need editing for copy changes |
| `dist/project-01.html`, `project-02.html`, `project-03.html`, `project-05.html` | Case-study text, section order, and image placement |
| `dist/styles.css` | Shared styling |
| `dist/case-study.css`, `project-02.css`, `project-03.css`, `project-05.css` | Case-study-specific styling |
| `dist/assets/` | Images, GIFs, and MP4s used by the pages |
| `.openai/hosting.json` | Configuration for the current hosting platform; other static hosts do not use it |

The project-card content is already separate from its layout in `content.js`. Longer case-study writing stays in semantic HTML so the pages remain readable and editable without a content service or build tool. Keep the CSS in its separate files when making copy changes.

## Update the portfolio

1. Edit a card in `dist/content.js`. Set `caseStudyUrl` to a relative HTML path when that case study exists. For a card without a case study, leave it empty and edit `previewMessage` to change the note shown when the card is clicked.
2. Edit the corresponding `dist/project-*.html` for longer case-study copy. Edit `dist/index.html` for the homepage bio and contact section.
3. Put new media in `dist/assets/` and refer to it with a relative path such as `./assets/example.png`. Keep the filename’s capitalization consistent with the reference.
4. To change the contact address, update the visible address and the `mailto:` links in the HTML pages. There is no contact form or form service.

## Run locally

From this project directory:

```sh
cd dist
python3 -m http.server 4173
```

Then open `http://localhost:4173/`. Any basic static-file server can serve the same directory.

## Move to another host

Upload the **contents** of `dist/` to the new host’s public web root so `index.html` is at the site root. Keep the page filenames and `assets/` directory together; internal page and media references use relative paths. A static host does not need `.openai/hosting.json`. Keep a copy of this whole project directory as a portable backup, including the original assets and this README.

The current design loads DM Sans and Manrope from Google Fonts through `dist/styles.css`. A destination host needs to allow that external request for the same typography; the CSS includes Arial fallbacks. Self-host those fonts if the destination must work without Google Fonts. Contact links use the visitor’s email app through `mailto:`. There is no backend, database, account system, or form to recreate.

The local file references can be checked here, but verify the site again on the destination host, especially its case-sensitive asset paths, media playback, fonts, and navigation. To update the current ChatGPT Site, change the files here and publish a new version through Sites; `.openai/hosting.json` records its Site ID.

## Vercel copy

The same `dist/` files are published at https://fernando-product-design-portfolio.vercel.app/. The Vercel project is `fernando-product-design-portfolio` in the `fer-digital-s-projects` account. It is a separate deployment from the ChatGPT Site, so changes to one host do not automatically update the other. After editing the files here, deploy `dist/` again to that existing Vercel project. Vercel's local project link and account sign-in are deployment tools only; the public site itself remains plain static files and does not require visitor sign-in.
