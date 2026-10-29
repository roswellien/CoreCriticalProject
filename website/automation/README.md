# Website source migration record

The permanent website source is `website/` in `roswellien/MW3Recomp-Private`.
Cloudflare Pages project `core-critical` builds this repository's `main` branch
with root `website`, command `python3 build.py`, and output `dist`.

The first production deployment from this repository was verified on October 28,
2026: [3b547114.core-critical.pages.dev](https://3b547114.core-critical.pages.dev),
from main commit `f21105fa9d11b8b3fbc884affa3950b1c608885d` (release PR #75).
The custom domain and pinned media deployment were retained.

The old `.github/workflows/publish-mechlab.yml` and inactive template have been
removed. The build reads public dated notes directly from `docs/mechlab/` and
needs no copied `data/mechlab.json` or cross-repository deploy key. The legacy
secret and deploy key are removed separately through repository settings after
production verification; current cleanup status is tracked in release issue #74.
Do not restore the old publishing bridge.

Historical source remains in `roswellien/corecritical-website`; archival preserves
that history and must retain a README pointing to this permanent source.
