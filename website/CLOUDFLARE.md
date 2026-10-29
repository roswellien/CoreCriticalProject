# Cloudflare Pages cutover

The site uses the existing Cloudflare Pages project `core-critical` and its
`corecritical.dev` custom domain. Keep this project; the gallery references
media at the pinned deployment `a67a6e69.core-critical.pages.dev`.

After this repository change is reviewed and merged, the maintainer switches
the existing Pages project's Git connection to `roswellien/MW3Recomp-Private`
and configures:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Root directory | `website` |
| Build command | `python3 build.py` |
| Build output directory | `dist` |
| Pages Functions directory | `functions` at the project root |

The function source is `website/functions/api/youtube-latest.js`. Cloudflare
Pages expects the `functions/` directory at the Pages project root, outside
the static output directory. Keep it in `website/`; `build.py` must not copy
it into `dist/`.

Before changing the production source, build and preview from this checkout and
confirm the homepage, navigation, MechLab pages, media gallery and YouTube
carousel. Then connect the existing `core-critical` project to this repository
and verify the first production deployment at `corecritical.dev`. Do not create
a replacement Pages project or delete the pinned media deployment.

Cloudflare account access and API tokens are supplied by the maintainer and
stay outside Git. After the first deploy from this repository is verified,
remove the old cross-repository MechLab publishing workflow and its deploy-key
secret, then revoke the corresponding deploy key from the old website repo.
Keep `website/automation/README.md` as the migration record until that cleanup
is complete.

References:

- [Pages monorepos](https://developers.cloudflare.com/pages/configuration/monorepos/)
- [Pages Functions](https://developers.cloudflare.com/pages/functions/get-started/)
- [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)
