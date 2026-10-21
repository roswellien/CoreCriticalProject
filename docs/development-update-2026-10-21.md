# Development update — October 21, 2026

We are preparing MechWarrior 3 Recomp for wider collaboration. This update
improves the project page, documents setup, and makes maintained source easier
to understand. It does not publish a playable release or complete the code audit.

## Project presentation and setup

The README now introduces the project, shows development screenshots, and links
the announcement trailer. Game / Launcher and Mod Tools have separate setup
guides. Both require users to supply their own original game files.

The Mod Tools source preview has an isolated Python environment, pinned
dependencies, configurable game and converter paths, and an explicit package
file list. The package builder creates a local review candidate; it does not
publish a download. Portable game preparation and supported custom-mission
export/play remain unfinished.

## Source readability

The ongoing cleanup expands compressed Python and JavaScript, improves local
variable names, and explains important contracts in the launcher, editor,
asset tools and native runtime. Comments describe binary formats, coordinates,
ownership, failure handling and guest calling conventions. Frozen research
snapshots retain their original evidence identities.

The contribution guide and code guide explain where to start and how to make
focused changes. This remains a subsystem-by-subsystem review, with functional
findings tracked separately from readability work.

## Verification and remaining work

Local checks passed for the native bootstrap, runtime host and video fixture,
including 19 native test groups. The Windows launcher rebuilt in Release mode
with zero warnings or errors, and its checks passed. All 57 remaster Python
tests passed, and 135 maintained Python tool sources passed syntax checks.
Code-structure comparisons checked the readability batches for unintended
executable changes, accounting for documented local variable renames.

A wider scan found 15 syntax errors in older research scripts outside the
cleanup; six also fail in the committed baseline, and nine have no committed
baseline. These findings remain open. The successful builds do not establish
complete game compatibility or public-release readiness.

Next work continues the source readability review and addresses release-facing
defects. No gameplay execution boundary or formal acceptance criterion is
advanced by this documentation and readability update; acceptance remains
131/144. Original game content, generated translations and local output packages
remain outside this commit.
