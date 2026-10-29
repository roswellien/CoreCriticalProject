# Public release preparation

Status-reporting policy, 2026-10-27: follow
[project status reporting](project-status-reporting.md). The paused startup
equivalence audit is historical evidence, not a current release-readiness gate.
The dated preparation notes below do not replace current install/update,
compatibility, fidelity or distribution checks.

Working review, October 21, 2026. The repository remains private. This document
tracks the owner's requested preparation; it does not authorize publication,
commits, history replacement, or a change to distribution policy.

The latest [original-input native generation work](archive/native-generation-preparation-2026-10-21.md)
now includes complete body regeneration, native linking and isolated live-menu
launches. The [October 22 source installer integration](archive/source-installer-integration-2026-10-22.md)
adds a bundled preparer and private source-tool installer. Signed update/reuse
integration passes; fresh packaged first-install generation is running.
Clean-machine installation and public release clearance remain open.

The subsequent [playtest launcher preparation](archive/playtest-launcher-preparation-2026-10-21.md)
adds persistent per-user settings/sessions, actionable failures and local support
exports in deployed launcher 1.0.3-preview. Its actual launch/normal-quit check
passes. The [1.0.4 installer setup follow-up](archive/installer-original-game-setup-2026-10-21.md)
adds the requested existing-installation or ISO-plus-patch choice and verifies
original-data extraction against the supplied media. Complete installed runtime,
content preparation and clean-machine setup remain open. The
[first installed-runtime trial](archive/installed-runtime-first-stage-2026-10-21.md)
now reaches the native live menu and normal close using external runtime/data
directories; it is a private baseline integration, not a distributable installer.
The [installed content follow-up](archive/installed-content-trial-2026-10-21.md) tests
Training with mech/environment packs and optional music, repairs fresh-pilot
keyboard services, and resolves existing-install support-file import. Permitted
local generation, environment-pack migration and clean-machine installer tests
remain open.
The [soundtrack/setup follow-up](archive/soundtrack-pack-setup-2026-10-21.md) adds
verified soundtrack `.mw3pack` loading and optional pack imports during first-run
game setup. The staged GUI is 1.0.7-preview; a shareable game installer remains open.
The [launcher migration and extraction build](archive/launcher-migration-media-build-2026-10-21.md)
deploys 1.0.9 with preserved settings and a soundtrack pack, verifies actual GUI
Play/normal quit, and replaces the Python-sourced extraction dependency with
pinned source builds and notices. Native user-file generation and clean-machine
installer validation remain open.
The [environment mission-lighting follow-up](archive/environment-pack-mission-lighting-2026-10-21.md)
deploys launcher 1.0.10 and the optional native catalog reader, with five rebuilt
1.1.0 environment packs. This closes the pack-data dependency for mission lighting;
it does not clear native generation/distribution or whole-campaign fidelity gates.
The [artwork/cinematic pack follow-up](archive/artwork-cinematic-packs-2026-10-21.md)
adds independently installable HUD/menu artwork, original-compatible AVI
replacement routing, an MP4 additions library and an explicit private original
movie-decoder resource. Modern high-resolution movies inside native gameplay,
new automatic story triggers and full enhanced movie masters remain open.
The [user-input generation step](archive/installer-user-input-generation-2026-10-21.md)
imports all four required support images from the player's ISO and generates
the codec image and startup source pack locally. Fresh 151-file original setup
and external native startup pass. The staged launcher is 1.0.12; native-host/entry
generation and clean-machine lifecycle validation remain open. Inno Setup 7.1
now compiles the launcher-only preview; isolated same-machine install, upgrade
and uninstall tests pass, with settings and pack metadata preserved.
The [native update follow-up](archive/launcher-runtime-updates-2026-10-21.md) deploys
launcher 1.0.13 with signed source/tool update preparation, version selection,
cancellation and rollback. Authored process fixtures pass; a production feed/key,
the actual whole-game preparation tool and clean-Windows updated-game launch
remain open. This does not make the preview a playable end-user installer.
The [merged-native setup follow-up](archive/merged-native-installer-2026-10-21.md) combines
the current pack/skin feature host, 21 audited readability files and installed
user-provider bindings. External installed launch with five packs and normal
quit passes; launcher 1.0.14 selects the merged build. Native generation from
player files and clean-Windows distribution gates remain open.

## Intended deliverables

| Deliverable | Required outcome | Current state |
| --- | --- | --- |
| GitHub project page | Clear README, announcement trailer, real gameplay, launcher and editor screenshots | README/gallery drafted; launcher and desktop editor captures still needed |
| Game / Launcher download | Windows installer; user supplies an existing game or ISO and patch; first-run setup works without this checkout | External runtime and Training content tested locally; private build inputs, pack migration and clean-machine installer validation remain open |
| Mod Tools download | Separate tools and setup; user supplies original archives and external conversion tools | Local source-preview ZIP and isolated setup tested; supported Studio export/play remains open |
| Contribution guide | Explain source layout, evidence, tests, readability and content rules | Review draft in CONTRIBUTING.md |
| Privacy and provenance | Review published refs/history, current changes, assets, logs and release payloads | First pattern/inventory pass complete; manual review open |
| Code review | Review all authored subsystems and document contracts before publication | Inventory complete; subsystem review begun, not completed |

## Findings that affect release

1. **The existing game installer is not a working end-user release.**
   `tools/mw3-remaster-launcher/installer.iss` copies the WPF output and artwork.
   `Core/GameRunner.cs` now supports an application-local runtime as well as the
   development checkout. The private external runtime trial works, but still
   contains generated host builds, source snapshots and derived preparation
   inputs. Installing the GUI alone cannot supply these.
   The installer's placeholder URL and stable `1.0.0` label have been corrected
   to the actual repository and an explicit development preview.
   Do not publish it as a playable package.
2. **Original-game ownership does not settle binary distribution.** The existing
   policy keeps generated game/codec translations and derived replacement packs
   local. The game package needs a reproducible local-generation/import workflow
   using the user's files, or a separately resolved distribution decision. The
   current host build depends on earlier CMake caches, object lists and staged
   providers. Preserve those working inputs while replacing this dependency chain.
3. **Binary admission is inconsistent across entry points.** The research manifest
   admits SHA-256 `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`;
   the GUI defines a different community executable identity. Review provenance,
   provider compatibility and intended profiles before promising one setup path.
   Do not broaden admission by filename or accept arbitrary binaries.
4. **Current GitHub CI is red.** GitHub run `39521422379`, HEAD `37bda63`, fails on two
   signed-to-unsigned canvas-index conversions in `runtime/graphics/menu_wave.hpp`.
   Explicit nonnegative index conversions now compile with Clang's conversion
   warnings as errors. The existing fixture and narrow MSVC/CTest checks pass
   locally. No push or new GitHub run was performed.
5. **Mod Tools had development-only assumptions.** The new separate setup selects
   the user's Mech3AX/game paths and keeps per-installation caches in the tools'
   local workspace. The original development defaults remain available. Studio
   export needs extracted caches and its generated launcher selects private
   lighting profiles. Missing caches must be reported rather than shipped.
   Exported archives contain game-derived content and remain local.
6. **Studio needs a full public-input review.** The HTTP handlers accept pack
   identifiers, titles and large JSON bodies, then write archives and generate or
   execute CMD files. Review containment, command text, request origins, body limits
   and failure cleanup before calling this a supported public editor. Initial
   repairs reject path escapes, nonnumeric shell-bound lighting, foreign
   Host/Origin headers, non-JSON and oversized requests; labels no longer enter
   command text. Asset-free rejection tests pass. This is not a complete audit.
   Do not expose this server to a LAN.

## History and privacy review

The first local pass examined 6,636 distinct reachable blobs (69,922,029 bytes)
from local refs, plus 1,229 non-ignored untracked files. It found no matches for
the checked credential patterns: GitHub/Google/AWS/Slack tokens, private-key
headers, credential assignments and credentials embedded in HTTP URLs. This is
an initial pattern scan, not a claim that every source or asset is publishable.
The detailed results stay in ignored `reports/publication-preflight-20261021/`.

Local checkpoint refs also retain two Windows shortcuts and three settings-file
versions. Path history checks found no commits for those paths in ordinary branch
history; do not describe checkpoint-only material as a GitHub leak. Do not push
local checkpoint refs or a mirror of this working repository.

GitHub enumeration found two branches, one open PR, no tags/releases, no current
Actions artifacts and no tracked LFS objects. Both remote branch tips match local
tracking refs. A second scan of both branch histories and PR 1's synthetic merge
covered 5,235 distinct blobs (58,171,474 bytes), with no credential-pattern or
flagged private-path matches. The smaller count excludes local checkpoint-only
history. These checks do not review expired artifacts or every Actions log.

A broader Gitleaks 8.30.1 (MIT) provider-rule scan then covered the eighteen
commits reachable through those branch/PR roots, scanning 43.71 MB of Git patch
content. The official Windows archive digest was verified; tool, license,
provenance and fully redacted reports stay local. It reported 47 alerts, reviewed
as source-context false positives: sixteen SHA-256 evidence pins, twelve C++
allocator offset expressions, eleven Lockit boundary descriptions, three assertion
messages, three trace-scope descriptions, a source dictionary selector and a C#
settings-property reference. No alert was hidden through a baseline or inline
allow comment. No confirmed credential was found; these results still do not
establish distribution rights, erase exposure in expired artifacts or replace
the remaining manual source review.

Remaining work:

- Manually inspect published-ref/PR-merge source bytes,
  embedded shader headers, literal instruction sequences and source provenance.
- Review all tracked artwork, icons, fonts and third-party notices; MIT covers
  project contributions only. Original/derived replacement content stays local.
- Review commit authors/messages, documentation links to private Drive folders,
  personal absolute paths, screenshots and surviving Actions logs for disclosure.
- Review staged and proposed release files independently of ignore rules. Existing
  untracked `.lnk`, logs, compiled `.spv` and user-pack folders are not an upload list.
- Keep a private backup before any proposed sanitization. No history rewrite or
  deletion has been performed, and none is needed merely because a path was flagged.

## Acceptance before a Game / Launcher download

- Establish the exact supported original executable and required data/provider
  identities. Reject unsupported inputs with an actionable explanation.
- Reproduce local generation and host compilation from documented pinned tools,
  without earlier developer build directories or BEFORE/AFTER state captures.
- Install to a fresh path with spaces as a standard user, outside this checkout.
  Import data locally, choose stock/enhanced visuals, launch menu and Training,
  test input/audio, save/load and normal quit, and preserve the original installation.
- Retain saves/settings across update and uninstall. Document log locations,
  troubleshooting, hardware scope, supported versions and known limitations.
- Inventory every packaged file and its source/license; include dependency notices,
  checksums and matching source/version. Do not bundle a proprietary host simply
  because the installer also asks the user for their game.

## Presentation and contribution review

Use the README as the GitHub homepage. Lead with the announcement trailer and a
short explanation, followed by capabilities, download status, setup, Mod Tools,
contributing and technical references. The separate `website/` tree is an older
website workstream; changing this README does not deploy either website repository.

The verified announcement is [MechWarrior 3 and Pirate's Moon Recompile/Remaster](https://www.youtube.com/watch?v=2olchoLkZro).
Additional evolution videos are linked from the [media page](media/README.md).
Footage is development presentation, not whole-game acceptance or a benchmark.
Do not reuse the corrupt pre-repair F9 captures in `local/screenshots/`.

Review CONTRIBUTING.md together before finalizing its process: small scoped
changes, evidence for game behavior, useful comments and tests, original-content
exclusions, and issue/PR expectations. No signing, mandatory contributor agreement
or external service requirement is introduced by this draft.

## Code review coverage

The [October 21 code/provenance review](archive/code-provenance-review-2026-10-21.md)
records reproduced launcher pack deletion/traversal, desktop exporter command
construction, ISO command construction, editor undo/save divergence and setup
cache defects, plus provenance and packaging gaps. Keep the Mod Tools candidate
unpublished until its affected paths are corrected and retested. The full
file-by-file review remains open; passing setup/build checks do not clear these
user-facing operations.

The subsequent local readability batch changes 68 maintained Python files,
seven launcher Core files and three shared-runtime headers. It expands compressed
control flow, documents interfaces/ownership/formats and clarifies five asset-bank
local variable names. Python executable ASTs match the captured starting versions
after excluding docstrings and normalizing those five names; C# executable tokens
match exactly. All 57 remaster Python tests, launcher profile/pack checks and all
16 asset-free CTest groups pass. The broad Python run requires the existing NumPy
environment; the system interpreter lacked that optional authoring dependency.
Frozen host/applicator/research sources and other active writers are preserved.
This batch is not a claim that all 4,172 source files have been individually
made readable or semantically reviewed. The wider pass remains open, so these
changes remain local rather than being committed/pushed as a completed cleanup.

The next readability batch covers 12 source files: Studio JavaScript/CSS, native
launch/preset PowerShell, the root D7VK compatibility launcher, PE metadata
inspection, editor UI callbacks and setup/package configuration. It adds source
contracts for preview versus persisted data, degrees/radians, drag/command/save
ownership, registry restoration, process handles and local-only outputs. The
JavaScript executable AST, CSS selectors/declarations and PowerShell code tokens/
AST structure match the captured starting versions. Eight Python files match
after excluding documentation. All 27 binary-tool, three preset-resolver and
seven release/Studio checks pass; wrapper CLI help also runs without starting a
game. No vendor JavaScript, frozen host source or native execution boundary is
changed. The repository-wide pass remains open and uncommitted.

The tracked inventory contains 5,188 files, including 4,172 source/script/UI files
and approximately 383,239 physical lines. Counts include third-party browser code
and compiled shader arrays; they are not authored-code review coverage. Most files
are dated research tools. Use [the code guide](code-guide.md) to review active paths
and retain immutable source pins in historical evidence. A mass format/comment pass
would invalidate those pins without establishing correctness.

A syntax-only pass parsed 3,282 tracked Python files with Python 3.14.7. Five
files fail parsing: `tools/m4-formatting-original/validate.py`,
`tools/m4-joint-startup28-original/run.py`,
`tools/m4-lockit-original/validate_original.py`,
`tools/m4-tree-review/review_joint138_prelaunch_v3.py` and
`tools/m4-vtable-review/final_observer120.py`. Observed defects include missing
whitespace between keywords/operands and conflicting triple quotes. They have
not been edited: establish which versions are referenced by retained receipts,
then supply reviewed runnable replacements without rewriting evidence.

## Initial preparation checks

Seven asset-free release/Mod Tools tests cover exact package contents and hashes,
repeatable ZIP bytes, path/duplicate rejection, configured paths, unknown-tool
rejection, shell-bound values and HTTP Host/Origin/body/traversal failures. CMake
now registers this suite. The menu-wave fixture passes both a Clang build with
conversion warnings as errors and the focused MSVC/CTest run; formatting passes
for the changed header. A whole-working-tree whitespace check still reports
pre-existing issues in other writers' wrapper documents; changed files in this
preparation pass are checked separately.

The complete isolated MSVC asset-free build also passed. Fifteen of sixteen
CTest groups passed initially; seven cases within `asset_tools` failed because
their fixture root had become an archival junction on another drive. Production
exporters correctly rejected it. The three affected test files now place only
their authored fixtures in `local/authored-test-fixtures`; export guards and
archival junctions are unchanged. The complete 45-case asset group passed on its
targeted rerun, giving passing results for all sixteen groups across the run and
that repair check. This does not establish Linux CI or native game fidelity.

The candidate ZIP was extracted into a fresh folder with spaces. Setup installed
the hash-pinned Pillow wheel into its own environment; `--check` and editor help
work from `C:/Windows/System32`. The configured external game catalog extracted
successfully and discovered 48 mission identities; the two checked original
archive hashes were unchanged, and the cache resolved inside the package.
This verifies dependency/configuration/catalog preparation, not GUI interaction,
all mission loading, map export, native play or a clean-machine game install.

An actual browser Studio screenshot is in the gallery. The available UI surfaces
did not expose native application capture, so GUI launcher and desktop editor
screenshots remain pending. No mockup was substituted for either interface.

Review each authored subsystem for purpose, ownership, inputs/outputs, failure
behavior, naming, duplication, bounds, resource cleanup and meaningful tests.
Add comments explaining contracts and unusual decisions; do not narrate obvious
statements or invent semantic names for unresolved guest functions. Separate
readability-only changes from behavior fixes and validate callers after each.

This preparation advances documentation, packaging and contributor onboarding.
It does not establish additional native gameplay or formal milestone acceptance.
The historical initializer audit remains preserved separately and is not a
routine status or release-progress indicator.
