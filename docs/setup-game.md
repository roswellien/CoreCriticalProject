# Game and Launcher setup

**A portable playable download is not available yet.** The GUI and native host
work in a prepared development environment. This page distinguishes that local
path from the setup being prepared for other users.

## What you will supply

A legally obtained MechWarrior 3 installation, with a supported executable/data
version. Current research targets the U.S. retail 1.2 profile. Admission is by
exact identity, not the filename. Different research and GUI identities still
need to be reconciled before a public setup can claim one supported profile.
Do not download a game or legacy DLL from an unofficial link to satisfy setup.

Windows x64 and Vulkan are the initial native platform/backend. Hardware and
driver requirements for a release remain to be established through broader
testing; development performance on one GPU is not a minimum-spec guarantee.

## Current development setup

The [native-host notes](../tools/m4-crt-heap-carry/README.md) describe local build
inputs. Generated translations, staged providers, dispatch metadata, pinned
objects and source snapshots remain local. The
[enhanced launcher](../tools/remaster-launcher/README.md) additionally uses
prepared bank/model/material registrations. Those are not included with source.

In an already prepared checkout, the existing `Play-MW3.cmd` and
`Play MW3Remaster.cmd` entry points select their local native profiles. The
graphical launcher invokes the same preparation path. Cloning the repository,
compiling just the WPF project or running its existing Inno script does not
create those inputs.

## Required public first-run experience

The separate Game / Launcher package must let a user:

1. Install into a new writable folder without administrator rights.
2. Select their original installation, check its exact identity, and receive a
   clear explanation of unsupported versions or missing inputs.
3. Prepare/import the necessary runtime data locally using a documented pinned
   pipeline, without uploading content or changing the original installation.
4. Choose resolution, window mode and supported graphics options; optional visual
   enhancements must be separate from the original-compatible setup.
5. Start the native game, reach the menu and Training, save/load and quit normally.
6. Find logs, update without losing saves/preferences, and uninstall only the
   project's files.

This experience has not yet been validated outside the developer environment.
There is no success-only installer placeholder: packaging remains blocked until
local generation and all required service/data inputs are reproducible.

## If you only want the editing tools

Use the separate [Mod Tools setup](setup-mod-tools.md). Editing, previewing and
exporting projects do not require a public game-host binary. Playing an exported
mission still requires a compatible prepared native host and independent checks.

See [release readiness](public-release-readiness.md) for the remaining work and
[distribution policy](legal.md) for material that cannot be included in downloads.
