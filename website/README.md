# Core Critical website

Local, portable HTML/CSS/JavaScript implementation of the approved Mad Cat homepage concept. Cloudflare Pages is the selected host; publication is pending. No game runtime code or acceptance criteria are changed by this work.

Cloudflare Pages is now the selected hosting target. Wrangler login is verified and corecritical.dev is active in the authenticated Cloudflare account. The local wrangler.jsonc points at dist and proposes core-critical as the project name. Project creation, deployment mode, domain attachment, and publication are still pending. Do not run a production deployment until the site is complete and publication is authorized.

## Local preview

From this directory:

```powershell
python build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:4173/. Re-run `python build.py` after source edits. The build copies only website files and assets, keeping design notes and tools outside the served directory. Python is a local build/preview convenience; the finished site requires only a static web host.

## Current state

The homepage is assembled with approved artwork, live title/navigation, modernization entries, project-family sections, development updates, and a GitHub link. Its first viewport awaits the Impeccable assembled-page review before implementation proceeds. Supporting pages and final mobile/functional checks remain unfinished; local links to those supporting pages are planned destinations at this checkpoint.

Approved assets remain in ignored `assets/plates/`; local artwork and mockups are not part of a public release. Generation prompts are embedded in every raster asset. The original cover was used as a local visual reference for the user-requested Mad Cat and is not served.

## Fonts

Fonts are self-hosted from the Google Fonts source repository. Each family retains its SIL Open Font License alongside the font files in `assets/fonts/`. Exact installed file identities are recorded in `assets/fonts/provenance.json`; the original game-content policy does not license these fonts or other third-party material.

## Boundaries

This work advances the website's approved mockup → local semantic HTML boundary, not a game execution milestone. The accepted startup-root count remains 131/144. No commit, push, deployment, domain, or DNS change has been performed.
