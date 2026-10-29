# Cloudflare Pages publishing

The site uses the existing Cloudflare Pages project `core-critical` and its
`corecritical.dev` custom domain. Keep this project; the gallery references
media at the pinned deployment `a67a6e69.core-critical.pages.dev`.

The existing Pages project is connected to `roswellien/MW3Recomp-Private`.
Automatic production deployments use these settings:

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

Before merging website changes into `main`, build and preview from this checkout
and confirm the homepage, navigation, MechLab pages, media gallery and YouTube
carousel. A push to `main` automatically builds and deploys the site. Verify
production at `corecritical.dev`. Do not create a replacement Pages project or
delete the pinned media deployment.

Cloudflare account access and API tokens are supplied by the maintainer and
stay outside Git. The old cross-repository MechLab workflow and template are
retired; the build reads `docs/mechlab/` directly. The source history remains in
`roswellien/corecritical-website`.

## Verified cutover

On October 28, 2026, release PR #75 promoted the source to `main` at
`f21105fa9d11b8b3fbc884affa3950b1c608885d`. The first deployment from this
repository succeeded:
[3b547114.core-critical.pages.dev](https://3b547114.core-critical.pages.dev).
The homepage, all 41 content pages, existing fallback routes, RSS and pinned
media returned HTTP 200. The YouTube Function returned its Atom feed on the
new deployment URL, and the browser rendered the carousel. Some subsequent
requests failed because YouTube returned HTTP 404 to the Function; the saved
carousel remains available. This upstream refresh limitation is tracked in
release checklist #74.

The production domain and pinned media deployment were retained. GitHub App
access is limited to selected repositories, including this private repository.
The legacy `CORECRITICAL_WEBSITE_DEPLOY_KEY` Actions secret and the old site's
"MechLab updates from game main" deploy key were deleted after verification.
No repository was made public.

## Admin crash report archive

The D1 database bound as `CRASH_REPORT_DB` stores each normalized accepted
crash report for the admin archive, in addition to the existing private GitHub
issue flow. Apply `migrations/0002_crash_report_archive.sql` to the production
D1 database before deploying code that writes or reads the archive.

Protect `corecritical.dev/admin/crash-reports*` with a Cloudflare Access
self-hosted application whose allow policy names the maintainer's email. Add
`CRASH_REPORT_ACCESS_ISSUER`, `CRASH_REPORT_ACCESS_AUD` and
`CRASH_REPORT_ADMIN_EMAIL` as Pages production variables matching that
application and policy. The Pages Function also verifies the signed Access
JWT and exact email before reading D1, so a direct Pages URL without an admin
JWT cannot return report data. No Access token or private signing key is stored
in the repository. D1 rows persist until manually deleted with Wrangler; there
is no automatic expiry or delete control in the page. See the archive setup and
deletion instructions in `README.md`.

References:

- [Pages monorepos](https://developers.cloudflare.com/pages/configuration/monorepos/)
- [Pages Functions](https://developers.cloudflare.com/pages/functions/get-started/)
- [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)
