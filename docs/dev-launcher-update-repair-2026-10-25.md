# DEV launcher update configuration repair

The source-output DEV launcher was running 1.0.38 without update-trust.json.
Both signed local imports and online discovery failed with “Updates are not
configured” before package/catalog verification. Its online-updates.json was
present and the public catalog itself was healthy.

The release's existing public RSA key configuration is now included in the
launcher project and copied into build/publish output alongside online-updates.json.
This contains only public verification material. No private signing key is
included. A clean isolated build confirmed the copied trust file's identity.

DEV was repaired using the exact signed full 1.0.39-preview installer in its
existing source-output directory after the user closed it. This establishes a
real setup installation and bundles runtime 1.0.37. A launcher-only setup would
have marked the development output as installed while leaving its runtime absent.
The previously selected repository host was the older 1.0.34 lazy-resources DEV
build; it and the repository profile remain intact. The repaired launcher now
selects its bundled 1.0.37 runtime. All 669 bundled file hashes passed verification.
Settings were unchanged by the repair, and installed packs were retained.

Before repair, restoring the missing trust file allowed the actual 1.0.38
assembly to verify local 1.0.39.ccupdate and 1.0.37.mw3update metadata and discover
both products online with no compatibility block. After repair, the actual
1.0.39 UI checked the live feed and reported “Up to date for channel playtest.”
Importing 1.0.39.ccupdate is now rejected as already installed, as expected.
No future-version launcher install was fabricated for this check.

The approved feed remains:
https://core-critical-updates.jcblackwell84.workers.dev/channels/playtest/catalog.json

It promotes independent launcher 1.0.39 and runtime 1.0.37 releases through a
signed catalog. New releases require new signed packages and catalog promotion;
the client does not infer updates by listing the bucket. Local imports require
the update metadata and matching ZIP together after extracting any wrapper ZIP.
The legacy runtime-only feed_url is intentionally empty; online discovery uses
the separate configured catalog, not that legacy single-package endpoint.

Evidence is local at local/work-ahead/dev-update-repair-20261025-r1/.
Cleaning the entire source build output also removes the installed runtime and
setup receipt: rerun setup to restore that installation. An ordinary build now
retains the public trust configuration. No native recompile, release promotion,
Git commit or acceptance-count change was performed for this repair.

## Follow-up: original support cache

The first actual launch after repair failed before native startup because the
new installed path could not find MSVCRT.DLL in the game or user cache. The old
repository launch used staged originals outside those locations. The preceding
runtime/catalog checks did not cover this launch prerequisite.

The four existing original support DLLs under local/mw3-staged were checked
against SupportedMedia.json (exact size and SHA-256), then copied into the
hash-addressed original-inputs caches for the normal and Codex-virtualized user
roots. No game-directory files or original inputs were replaced. The actual
installed assembly then passed GameValidator.Validate, FindProvider,
PrepareSupportFiles and BindSupportFiles using the player's configured game
directory and runtime 1.0.37. Derived CRT and rebased codec identities also
passed. This verifies the reported missing-support failure's prerequisites;
it does not claim a new live-game launch or gameplay check.

## Normal Windows shortcut verification and pack repair

The cache-only support repair did not reach the normal launcher's physical
AppData view. The admitted original support DLLs were subsequently copied into
the selected game's native-inputs directory, each verified against the exact
SupportedMedia.json size/hash. The real launcher passed that original-support
check, then correctly rejected Sommerset against its old replacement model.

Launching through Codex inherited redirected AppData (11 enabled packs, model
pack 1.3.0); launching the existing project shortcut from Windows Explorer used
the player's normal profile (15 enabled packs, old MW5 Replacement Mechs).
Command-line checks of the redirected profile therefore did not establish the
normal launcher's actual installed models. Even extended volume paths resolved
back into the redirected view; those checks were not treated as normal-profile
evidence.

Through the normal launcher's Install Pack UI, imported the exact
assets/MW3/Models/mw3-remastered-models-1.3.0.mw3pack archive. The UI confirmed
successful installation and v1.3.0. Disabled the superseded Updated MW3 Mechs
split pack while retaining its files. Sommerset, Marauder chassis and Gun Metal
remained enabled. Normal launch then passed composition and reached the live
native menu after the intro. Session c8f167a602d945ba8011c352b77ba016 records
that launch; the game was left open at its menu for the user. No mission or
visual skin selection check is claimed. Acceptance remains 131/144.
