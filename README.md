# Fernando portfolio

Static HTML, CSS, JavaScript and media. `dist/` is editable source and the public document root, not generated output. No dependency install or build step is required.

## Local development

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Visit http://127.0.0.1:4173/. Stop with Ctrl-C.

Work on `portfolio-case-study-update`; review `git status` and changes before committing. Keep original GIFs, backup ZIPs, secrets, dependencies and `.vercel/` out of Git. Site MP4s are optimized copies.

## Hosting

Production: https://fernando-product-design-portfolio.vercel.app/
Existing Vercel project: fer-digital-s-projects/fernando-product-design-portfolio.

The Git repository is not connected to automatic Vercel deployments. Do not create a duplicate project. CLI releases upload the contents of `dist/` to the explicitly named existing project. Future Git integration must use `dist` as the output directory and requires review of deployment effects.

See HANDOFF.md for provenance, checks and the known pre-existing empty case-06-01.webp image. RECOVERED_SOURCE.md contains historical export instructions.
