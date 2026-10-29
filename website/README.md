# Core Critical website

The live site is [corecritical.dev](https://corecritical.dev), hosted by the
existing Cloudflare Pages project `core-critical`. Website source now lives in
this repository's `website/` directory. Cloudflare builds production from this
repository's `main` branch, with `website/` as its project root. Automatic production deployments are enabled.

## Build and preview

From the repository root, build the static pages and MechLab news:

```powershell
python website/build.py
```

The build reads public dated notes from `docs/mechlab/` in this repository and
generates the homepage updates, `news.html`, dated `updates/` pages and `feed.xml`.
It also generates the media gallery from the metadata in `website/data/`.
Original footage remains at the already-published URLs in
`data/media-assets.json`; the build does not download or package it.

To preview the site and its YouTube Pages Function, run Wrangler from
`website/` after building:

```powershell
Set-Location website
npx --yes wrangler@4.151.0 pages dev dist
```

Wrangler serves the static build and discovers the Function in `website/functions/`.
For a static-only preview, use `python -m http.server 4173 --directory dist`
from `website/`.

## Publish

The maintainer keeps the existing `core-critical` Pages project and custom
domain, and points its Git integration at this repository with `website/` as
the root directory. Configure the build command as `python3 build.py` and the
output directory as `dist`. The Pages Function must stay in the project root
(`website/functions/`), outside `dist/`. See [CLOUDFLARE.md](CLOUDFLARE.md) for
the cutover checklist.

The media gallery uses files and hashes in `data/media-assets.json` that are
hosted on the existing pinned Pages deployment. Keep that deployment available;
the migration does not recreate or remove it.

The maintainer supplies Cloudflare access through the existing account or a
local Wrangler login. Keep API tokens and signing credentials outside Git.
The legacy cross-repository MechLab publishing bridge is retired. Future site
and dated MechLab changes publish from this repository's `main` branch.

## Content and boundaries

Only dated `docs/mechlab/YYYY-MM-DD.md` notes feed the development news. The
build does not call GitHub APIs, create a copied `data/mechlab.json`, or need a
cross-repository deploy key. Do not add original game media, generated game
code, Cloudflare tokens or signing credentials to this tree.
