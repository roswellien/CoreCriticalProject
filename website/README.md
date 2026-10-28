# Core Critical website

The site is live on Cloudflare Pages at [corecritical.dev](https://corecritical.dev).
The Pages project is `core-critical`; [wrangler.jsonc](wrangler.jsonc) writes the
static build to `dist/`. Cloudflare account access and the existing domain
attachment are maintained by the site owner.

## Build and preview

From this directory, run:

```powershell
python build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open <http://127.0.0.1:4173/>. `build.py` copies the site and assets into `dist/`
and builds `news.html` from the dated Markdown updates in `docs/mechlab/` at the
repository root. Edit those source updates rather than editing generated news
HTML.

The approved display artwork in `assets/plates/` is ignored by Git. The tracked
homepage also links to `projects.html`, `media.html`, `about.html` and
`project.html`, which are absent from this repository snapshot. A fresh clone
therefore does not yet contain the complete production Pages source. Before a
production deployment, the maintainer must reconcile those current page files
and supply the current approved site-art files locally; verify all links and
assets are present in `dist/`. Use only approved website artwork. Original game
media and generated game code remain local. This checkout gap is why the Pages
deploy command below is documented but was not run from a fresh clone.

## Publish

After reviewing the build, publish the contents of `dist/` to the existing Pages
project:

```powershell
npx --yes wrangler@4.151.0 pages deploy dist --project-name core-critical
```

The maintainer supplies Cloudflare authentication through the local Wrangler
login or `CLOUDFLARE_API_TOKEN`; credentials stay outside the repository. Check
the deployment output, then open the live domain and verify the home page,
development news, navigation and assets.

## Content and boundaries

This is a static HTML/CSS/JavaScript site. `python build.py` does not publish or
change DNS. Development-news source is the authored Markdown in `docs/mechlab/`.
Do not put original game media, generated game code, signing credentials or
Cloudflare tokens in the site or its deployment output.
