# Launcher startup preparation, October 22

October 24 follow-up: [demand loading and compatible runtime cache reuse](asset-pack-loading-performance-2026-10-24.md)
removes EXE-only environment-cache invalidation and reduces eager model/skin reads.
The measurements and release state below remain historical evidence.

Launcher 1.0.16-preview advances installed-pack -> prepared-resource reuse.
No native EXE/DLL or installer rebuild, signing, upload or commit was performed.
Gameplay acceptance remains **131/144**. Native debugging and playtesting remain
with their existing writers.

## Problem and changes

Session `cc2d033482944fe4a0c98b86ab8699e8` spent approximately 148 seconds between
coordinator creation and native process creation. Its two mech/six environment
packs declared roughly 38 GB of unpacked inputs. Pack readers hashed their full
closure each launch; environment preparation decoded, merged and re-encoded
surface-normal pages every time.

`startup_cache.py` records successful content hashes against absolute path,
expected digest, device/file identity, size, modification and change times.
Unchanged files reuse those local receipts. Missing or changed files receive
full checks; failures still reject launch. Manifest parsing, explicit host/format
admission, precedence and path containment run each time. Callers without a
verification cache retain full hashing.

The cache trusts the local player filesystem. It is not an authenticity boundary
against a process able to modify both player data and cache receipts. Native EXE/
DLL checks remain unchanged; this work admits no unknown native host.

Merged environment output has a complete receipt keyed by selected resources,
paths, pins, host settings and producer hashes. Changed inputs invalidate it.
Missing/incomplete/damaged output triggers rebuilding; changed output metadata
triggers rehashing. Atomic receipt publication and a writer lock prevent partial
reuse/overlapping resource writers. Failed attempts are retained. Disabling packs
changes the selection and removes their bindings.

The launcher warns beside Play that first startup and launches after changing
packs can take several minutes depending on PC/storage speed. Startup messages
show check counts, preparation/reuse stages and elapsed time beneath Play.
Redirected Python uses UTF-8. Future source-tool exports include the new module;
the frozen existing installer/source bundle remains untouched.

## Evidence

`D:/MW3LauncherStartupCacheTrial-20261022-r1` contains logs and receipts:

- **32 Python checks passed**, including six cache checks: warm reuse, invalid
  receipts, changed/replaced inputs, replacement with preserved mtime, damaged
  outputs, host/producer changes, disabled packs, interruption and writer locking.
- Full C# LauncherChecks passed, including packs, settings, original files,
  registry, installed runtime integrity and signed preparation/update recovery.
- Release build/publish succeeded. Final publish adds explicit UTF-8 output.
- Actual installed-pack preparation-only benchmark: **172.47 s cold, 2.01 s
  warm**, both exit 0. Warm log confirms reuse. This excludes native startup/menu
  loading; no game was launched by the benchmark.
- Copied resource outputs were SHA256 checked, and 464 still-matching file
  receipts staged into the normal per-user cache. Existing entries were retained.
  Further shared-cache testing was skipped when the user's coordinator was
  found running. That user's own cold preparation completed in 145 s; the
  resulting native process and its coordinator were preserved.
- Ordinary launcher EXE replaced with fresh single-file 1.0.16, retaining the old
  EXE in the trial's LauncherBackup. The open launcher/game were not closed.
  Restart the launcher after playtesting to load its new UI. Settings hash was
  unchanged. `deployment.json` records exact EXE identities. Profile untouched.

New packs, producer code or relevant host settings can still require slow first
preparation. The measured improvement applies to preparation on this PC, not a
claim that the native game/menu opens in two seconds on every machine. Cloud
installer and signing stay pending the user's native fix.
