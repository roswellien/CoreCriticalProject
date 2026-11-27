---
name: core-critical-release-packaging
description: Package a Core Critical launcher or game release, verify installer and update filenames, signatures and receipts, draft the release PR and release notes, and track release artifacts. Use when preparing or packaging a release.
---

# Release packaging

The rules and commands live in the governing documents below. Read them first; each
document owns its rules. Where this checklist and a governing document disagree, follow
the document.

- `docs/launcher-and-website-release.md`: orchestrator steps, signing, catalog, R2, and feed.
- `docs/release-filenames.md`: required installer and update filename formats.
- `docs/github-workflow.md`: release PRs, project board tracking, notes, and branch sync.
- `docs/legal.md`: distribution rules for original game media and generated game code.
- `docs/project-status-reporting.md`: standards for reporting validation and release status.

## When to use

Use this skill when preparing, packaging, verifying, or publishing a Core Critical launcher
or game release, or when tracking a release lifecycle from merged `main` to publication.

## What an agent must never do

- **Never push directly or force-push** to `main` or `develop` (`docs/github-workflow.md`).
- **Never merge a PR or publish files** without explicit owner direction
  (`docs/github-workflow.md` "Review and merge"). Creating a PR or finishing packaging
  does not authorize merge or publication.
- **Never commit or distribute original MW3 media, generated game code, private build outputs,
  or signing material** (`docs/legal.md`, `docs/launcher-and-website-release.md`). Keep
  keys, tokens, and credentials outside git.

## Release checklist

Follow this sequence in order:

1. **Track the release issue:** Open or locate the release tracking issue using
   `.github/ISSUE_TEMPLATE/release.yml`. Record the target version and products, and update
   its checklist as milestones complete (`docs/github-workflow.md` "Project board").
2. **Open the develop to main release PR:** When the integration branch is ready, open a PR
   from `develop` to `main` titled "Release <what ships>" (`docs/github-workflow.md`
   "Promote and publish a release"). Summarize included changes and validation. Wait for
   maintainer review and merge.
3. **Check out merged main:** After the release PR merges, check out a fresh, clean clone
   at the exact merged `main` commit and record its SHA (`docs/launcher-and-website-release.md`
   "Launcher release"). Do not edit release sources or version numbers after checkout.
4. **Stage dependencies and build:** Follow `docs/launcher-and-website-release.md` to stage
   pinned dependencies and package the launcher and runtime. If a step is unclear, see
   `docs/launcher-and-website-release.md` rather than guessing commands.
5. **Enforce filename rules:** Check every installer, update and ZIP filename against
   `docs/release-filenames.md`, using the names recorded in the build receipt.
6. **Verify signatures and test locally:** Check Windows SignTool signatures, timestamps,
   update signatures, and receipt hashes as required by `docs/launcher-and-website-release.md`.
   On an isolated Windows test environment, verify clean installation, upgrade from a prior
   release, and runtime rollback.
7. **Build signed catalog and upload to R2:** Prepare the signed catalog with
   `tools/update-service/build_catalog.py`, upload immutable release objects to Cloudflare R2,
   promote the feed allowlist, and verify readbacks (`docs/launcher-and-website-release.md`).
8. **Deploy website updates:** If the release includes website updates, build with
   `python website/build.py` from `website/` and deploy to Cloudflare Pages following
   `docs/launcher-and-website-release.md` "Website deployment".
9. **Draft release notes:** Draft notes in GitHub Releases from the prior tag to the new tag
   using `.github/release.yml`, lightly editing for clarity on shipped products and player
   impact (`docs/github-workflow.md` "Promote and publish a release").
10. **Synchronize branches:** If `main` has commits that `develop` lacks after the release,
    open a synchronization PR from `main` to `develop` titled "Sync main into develop after
    <release>" (`docs/github-workflow.md` "Synchronize the branches").

## How to report results

Report release packaging results concisely following `docs/project-status-reporting.md`:
- Merged `main` commit SHA and release version.
- Exact artifact filenames and SHA-256 checksums from the build receipts.
- Verification results for signatures, clean install, upgrade, and rollback tests.
- Status of the release PR, catalog sequence, R2 keys, and release notes draft.
- Any checks not run and why; distinguish "awaiting review" from "merged" and "published".
