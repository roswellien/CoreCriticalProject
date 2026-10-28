# Core Critical website

The site is live on Cloudflare Pages at [corecritical.dev](https://corecritical.dev).
The Pages project is `core-critical`, with the static build in `dist/` as set in
[wrangler.jsonc](wrangler.jsonc). The production page sources and approved
illustrations are kept in this repository's `website/` tree.

## Build and preview

From `website/`:

```powershell
python build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open <http://127.0.0.1:4173/>. The build copies the site and approved artwork,
then generates `news.html`, dated `updates/` pages, `feed.xml`, and the media
gallery. Its MechLab summaries come directly from dated Markdown files in the
repository-root `docs/mechlab/` directory. The homepage shows the latest three
notes; the news archive contains all dated notes. See
[`docs/mechlab/README.md`](../docs/mechlab/README.md) for the public-note format.

The gallery references previously published video and thumbnail URLs listed in
`data/media-assets.json`; the build does not download or package game footage.
Original game media and generated game code remain local.

## Publish

Build and review `dist/`, then deploy to the existing Pages project:

```powershell
npx --yes wrangler@4.151.0 pages deploy dist --project-name core-critical
```

The maintainer supplies Cloudflare authentication through a local Wrangler login
or `CLOUDFLARE_API_TOKEN`. Keep tokens outside the repository. Check the deploy
URL and verify the home page, MechLab news, media pages, navigation, fonts and
illustrations on `corecritical.dev`.

## Content and boundaries

This is a static HTML/CSS/JavaScript site. `python build.py` does not publish or
change DNS. Only the explicitly authored `docs/mechlab/YYYY-MM-DD.md` notes feed
the development news. Do not add original game media, generated game code,
signing credentials or Cloudflare tokens to the site source.
