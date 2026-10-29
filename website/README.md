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

The site pages are static HTML/CSS/JavaScript; the Pages Function in
`functions/api/crash-reports.js` is the server-side crash-report endpoint.
`python build.py` does not publish or change DNS.

## Crash report endpoint

Reports are sent only after the player enables automatic sending or approves a
one-time prompt. The endpoint targets a dedicated private repository such as
`roswellien/corecritical-crash-reports`, groups specific failures by engine
mode, exit code and message, reopens closed matching issues, and adds issues to
the configured Project V2 board through that board's built-in auto-add
workflow. The generic unexpected-exit message is never grouped. The launcher
displays a short report ID, not a private GitHub URL.

New crash issues are capped at 20 per UTC day by default. The cap is reserved
atomically in D1; reports beyond it are comments on one configured overflow
issue, without full logs. Matching issues include full logs for only their
first three repeats. The admin D1 archive retains each accepted report's
bounded logs until the maintainer deletes it (see below). Create the private
report repository, a private overflow issue in it, and a D1 database before
enabling production reporting. Apply a Cloudflare rate-limit rule to
`/api/crash-reports` as well.

In the Project V2 board, enable its **Auto-add to project** workflow for the
private crash-report repository with the filter `is:issue`. The overflow issue
must already be on the board; manually add it if it was created before this
workflow was enabled. GitHub auto-add workflows do not backfill existing issues.

Configure the `core-critical` Pages production environment with:

- `CRASH_REPORT_REPOSITORY=roswellien/corecritical-crash-reports`.
- `CRASH_REPORT_OVERFLOW_ISSUE_NUMBER`, the private repository's overflow issue number.
- Optional `CRASH_REPORT_DAILY_ISSUE_LIMIT` (defaults to `20`, maximum `1000`).
- Create a D1 database, apply the migration from `website/`, and bind it to
  Pages as `CRASH_REPORT_DB`:

  ```powershell
  npx wrangler d1 create corecritical-crash-reports
  npx wrangler d1 execute corecritical-crash-reports --remote --file migrations/0001_crash_issue_daily_limits.sql
  npx wrangler d1 execute corecritical-crash-reports --remote --file migrations/0002_crash_report_archive.sql
  ```

- A `GITHUB_TOKEN` secret with issue read/write access to the private report
  repository only. A fine-grained token can be restricted to this one repo;
  Project access is handled by GitHub's built-in auto-add workflow.

Keep the GitHub token in the Pages secret store and outside Git. The server
requires all configuration, including D1 and the overflow issue, and fails
visibly when any part is missing. Run endpoint checks from `website/` with
`npm test`.

### Admin crash report archive

Every accepted report is also stored as normalized JSON in the server-only D1
table `crash_report_archive`. The GitHub issue flow remains active for triage.
Open `https://corecritical.dev/admin/crash-reports` to review the latest 100
reports and open a report's hardware, settings, pack metadata and separate
line-preserving log sections. Dynamic report text is HTML-escaped. The page
does not generate public or static report documents.

Before enabling the archive in production, configure a Cloudflare Access
self-hosted application for `corecritical.dev/admin/crash-reports*` and create
a policy that allows the maintainer's email. Configure these Pages production
variables to match that Access application:

- `CRASH_REPORT_ACCESS_ISSUER=https://<team>.cloudflareaccess.com`.
- `CRASH_REPORT_ACCESS_AUD=<application-audience-tag>`.
- `CRASH_REPORT_ADMIN_EMAIL=<admin-email>`.

The Pages Function independently verifies the Access JWT signature, issuer,
audience, expiration and exact admin email before querying D1. The Access
application provides the login flow; its signed JWT reaches the function as
`Cf-Access-Jwt-Assertion`. Keep the app's email allow policy and the function's
email variable aligned. Requests through a Pages preview or direct Pages URL
without a valid admin JWT receive no report data. D1 remains bound only to
Pages server code; Cloudflare account administrators can still access the
database through their Cloudflare account permissions.

Archive records, including bounded logs, are retained until the maintainer
deletes them. There is no automatic expiry or delete control in the page.
To remove a report, use an authorized Wrangler session:

```powershell
npx wrangler d1 execute corecritical-crash-reports --remote --command "DELETE FROM crash_report_archive WHERE report_id = '<report-id>';"
```
