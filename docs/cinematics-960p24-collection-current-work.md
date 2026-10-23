# Two-pass cinematic collection and asset pack

Authorized 2026-10-22: upgrade the remaining 18 original MW3 movies with the
approved restrained two-pass routine and prepare a cinematic asset pack.
Reuse the completed full opening; the extreme third-pass experiment is excluded.
See [the selected routine and opening checks](cinematics-960p24-restrained-2026-10-22.md).

## Completed collection and verified pack

Completed **2026-10-23 at 02:52 America/Denver**. All18remaining movies passed
the approved two-pass routine; the existing full opening was reused. All19
movies are 1280x960 at 24fps, with **26,264 decoded output frames** across
1,094.333 seconds of movie timelines. There were no failed clips. Original PCM
identity and audio continuity passed for every lossless master; MP4s use AAC.
Full-speed whole-collection subjective review remains pending.

Ready local pack:

`local/asset-packs/cinematics-960p24-two-pass-v1/cinematics-960p24-two-pass-library-0.1.0.mw3pack`

- Size: **631,418,763 bytes**.
- SHA-256: `645e7dc3b7604e153397c716bd3b25424d5aae66c01707cff98ca653833adc2f`.
- Independent completion audit rehashed all19 MP4s and the full pack; checked
  all20 declared archive members, exact membership, original filename coverage,
  per-clip frame totals and recorded master/PCM checks.
- The launcher's existing importer successfully installed the whole pack into
  `isolated-install-check/`; its installed manifest and cinematic registry match
  the archive exactly. The frozen validator's file pins also still match.
- Local evidence: `collection-completion-audit.json`, `media-inventory.json`,
  `launcher-import-check.log`, authoring description and future-replacement map
  beside the pack, plus the worker's completed `batch.json` and per-movie records.

The worker has exited. The completion heartbeat is **paused** after verification.
This pack provides the launcher's **Watch installed cinematics** library. Native
enhanced in-game MP4 playback remains unimplemented; filename mappings are staged
planning data. No active-profile installation, upload, publication or commit was
performed. Native acceptance remains131/144, with no execution boundary advanced.

## Launch history and ownership

Working directory: `local/work-ahead/cinematics-960p24-two-pass-collection-v1/`.
The detached, hidden worker is `run_collection.py`, initially Python PID **21588**.
Recheck its command line and creation identity before continuation. Never start
a second worker while this one is alive. `worker.lock` also uses an exclusive
Windows byte-range lock to reject concurrent copies.

At launch, all 18 source AVI hashes and stream/audio contracts passed admission.
The previously completed opening's master and MP4 hashes were also verified:
**1/19 movies complete; 18 queued** at this snapshot. Actual status is in
`batch.json`; read that rather than treating this snapshot as live progress.
Bounded logs: `worker.stdout.log` and `worker.stderr.log`.

The existing graphics capture/export pipeline under
`C:/Users/jcbla/MW34SunTests/mech-evolution-series-3-20261022/` was active, with
pipeline PID73692 and capture queue PID72608 plus changing native/encoder children.
The cinematic worker waits for this exact capture tree to finish before GPU
processing and rechecks before each AI/interpolation invocation. It does not
terminate, alter, or run alongside those GPU captures. Other writers and active
SQLite databases remain untouched. Expected processing is roughly 2-3 hours after
the GPU becomes available; that is an estimate, not a completion claim.

## Exact media policy

- Source: the 18 admitted original `source.avi` files in the prior batch folders,
  never the old 4K movies. Inventory: 13,674 source display frames over 911.6s.
- Timing: native-size RIFE v4.6 at 8x with scene threshold20, then every fifth
  sample to obtain 24fps, before spatial enhancement. Hold the final picture to
  fill the last fractional output frame. Retain complete original audio tails.
- Pass1: native 2x anime-video-v3, 35% AI plus 65% Lanczos-enlarged source.
- Pass2: native 2x enhancement of the pass1 master, Lanczos back to 1280x960,
  35% new enhancement plus 65% pass1 master. No second interpolation.
- Lossless FFV1 masters retain each movie's exact original PCM: 22050Hz, mono
  8-bit or stereo16-bit as actually observed. MP4 viewing copies use H.264 CRF16
  slow and AAC; original framing, aspect ratio and bars are retained.

The first two queued movies are C2M1 (mono8-bit with an audio tail) and C1
(stereo16-bit), exercising both actual source contracts early. C4WIN and CAMPAIGN
follow, then remaining filenames. Filename identities are preserved without
inventing new story events. Every final master/MP4 receives a full decoded-frame
count and timestamp check; each lossless master receives audio continuity and
byte-exact original PCM checks. Source and output hashes support bounded resume.
Failures remain explicit; a failed clip prevents final pack creation.

The historical first-pass `process.py` is reused unchanged. The pack author and
launcher validator are private snapshots, with hashes, so ongoing launcher edits
cannot silently alter this batch. No generated code or game media is committed.

## Asset-pack readiness and current playback boundary

The current maintained cinematic contract admits H.264/AAC MP4 as launcher
library additions (`MP4-library-v1`, `replaces: null`). Its native in-game
replacement path still admits only original-compatible 640x480, 15fps IV50 AVI.
Do not label these enhanced movies as functioning in-game replacements, change
extensions to bypass admission, or invent successful modern decoding.

The worker builds this complete **19-movie library preview** automatically only
after every movie validates:

`local/asset-packs/cinematics-960p24-two-pass-v1/cinematics-960p24-two-pass-library-0.1.0.mw3pack`

Pack ID: `com.mw3remaster.cinematics-960p24-library`. Schema2, profile
`prepared-cinematic-v1`, exact file table and original movie identities. No code,
runtime flags or custom mission triggers are included. The pack directory will
also contain its authoring description, validated media inventory, README, and a
separate future-replacement filename map. That map is planning data, not a native
playback claim or an unknown field inserted into the pack registry.

Before starting the queue, an opening-only authored MP4 pack passed actual
installation through a frozen copy of the existing `LauncherChecks.exe
--install-packs` command, in the isolated `smoke-isolated-install/` folder. This
executes the launcher's existing cinematic admission, not a new verifier layer.
The final pack must pass the same importer in its own isolated folder. The
active launcher/player profile is not modified.

## Continuation and completion

The current-chat completion heartbeat `finish-mw3-two-pass-cinematic-collection`
checked every15minutes and stayed quiet during unchanged running/waiting states.
It is now paused after successful collection and pack verification. Do not
restart the completed worker or create duplicate monitors.

If continuation is necessary, first inspect actual process identities, batch
status and bounded logs. After the worker has genuinely stopped, `python
local/work-ahead/cinematics-960p24-two-pass-collection-v1/run_collection.py --resume`
can reuse verified completed stages. An existing unvalidated/changed output
fails closed: retain it in a fresh failure namespace before repairing or retrying;
do not overwrite it or admit it solely because the process exited.

Completion requires all19 movie records, their MP4 identities, final `.mw3pack`
identity and successful isolated-import log. Full-speed subjective review of all
movies and native modern-codec integration remain separate. User-file generation,
distribution eligibility and decoder lifecycle tests still apply before an
in-game release pack. Keep originals and derived media local; this batch does
not authorize Drive upload or public distribution. No native execution boundary
or acceptance gate advances; strict accepted count remains **131/144**.
