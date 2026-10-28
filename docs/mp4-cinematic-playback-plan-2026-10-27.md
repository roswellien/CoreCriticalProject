# Native MP4 cinematic playback implementation plan

Status: investigation and proposed implementation sequence, 2026-10-27.
No player, launcher format change, replacement pack, runtime or release is
implemented by this document. The user has resumed cinematic integration work;
the older deferral and AV1 delivery proposal remain dated research.

## Intended behavior

An enabled cinematic `.mw3pack` maps an original requested movie, such as
`intro.avi`, to its replacement MP4. The native game plays it in its existing
window at the movie's resolution/rate, with synchronized sound, original
skip/completion behavior, and a clean return to menus or missions. Installing
another compatible replacement requires pack metadata, not another native
registration or code change. Disabling the pack restores original playback.

This advances the recompiled movie-command -> host media decoder/audio -> Vulkan
presentation boundary. Original script sequencing remains recompiled game logic.
Do not replace the game with a separate movie application, execute original x86
code as a fallback, or feed MP4 bytes into the VfW/Indeo service.

## What was verified

Source baseline: `origin/develop` commit
`e60907fea1987bb1538a1f6314c8ff780423e7e7`. Sources referenced below are in that
baseline. The original U.S. retail 1.2 `Mech3.exe` was freshly hashed as
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.

| Evidence | Finding / limitation |
| --- | --- |
| Current pack, freshly verified archive member hashes and sizes | `com.mw3remaster.cinematics-960p24-library` version `0.1.0`; 631,418,763 bytes; SHA-256 `645e7dc3b7604e153397c716bd3b25424d5aae66c01707cff98ca653833adc2f` |
| Registry inside that archive | All 19 clips have `replaces: null`, so they are launcher-library entries, not game replacements |
| Fresh ffprobe stream-header inspection of all 19 loose delivery MP4s | H.264 High, level 4.0, 8-bit `yuv420p`, 1280x960, 24/1 fps; AAC-LC, 22050 Hz, mono or stereo |
| Original `VIDEO` inventory | All 19 clip IDs match an installed original AVI stem; no fabricated `c3m3` source is needed |
| Current MP4 headers | All lack explicit color-matrix tags. Audio/video endpoints differ slightly in several files; for INTRO video is 182.5 s, audio about 182.467 s |
| Existing collection audit | Records 26,264 video frames and pending full-speed subjective review. This pass inspected stream metadata and integrity; it did not decode every frame again or certify visual quality |
| Launcher `Core/CinematicPack.cs` | Non-null replacement targets require original-compatible AVI; MP4 is library-only. Integrity checks and original target checks already exist |
| Native `cinematic_paths.inc` and `mfc_stage.hpp` | `MWCINE1` maps filenames only at `AVIStreamOpenFromFileA`, which still opens real AVI streams. It is not an MP4 player |

The current library can supply the first implementation without upscaling or
re-encoding. The earlier 2880x2160/30 fps FFV1 masters and AV1/MKV/FLAC experiments
are separate archival/delivery research; they do not describe this installed pack.

Private evidence remains outside Git at
`D:/CoreCriticalCinematicRuntime-20261027-r1/`: `pack-probe.json`, focused
Ghidra scripts/logs and `lifecycle/`. The package remains in the project's local
`assets/MW3/Cinematics/` directory. No movie, generated translation or decompiled
listing belongs in the PR.

## Original movie lifecycle: recovered and still open

Read-only Ghidra 12.1.4 analysis reused the existing matching `MW34Pilot` database.
Addresses below are original executable virtual addresses, not RVAs or host
pointers. Static code observations are not live execution evidence. New function
boundaries used for this inspection were discarded when the read-only project
closed. Preserve unresolved original names in implementation notes.

| VA | Observed responsibility |
| --- | --- |
| `0x598D80` | Script-command factory; constructs the movie command through `0x599C00` |
| `0x599C00` | Movie-command construction: builds/checks the original pathname; establishes vtable `0x5CF880` |
| `0x599EA0` | Vtable `+8`, start/initialize: allocates the AVI player through `0x59A4A0`, initializes presentation fields and last-frame state; assembly ends in `RET 8` |
| `0x599DE0` | Vtable `+4`, update: `ECX` is command object; stack carries an 8-byte time value; computes a legacy frame, decodes/presents, returns continuing status in `AL`, `RET 8` |
| `0x599F40` | Vtable `+12`, close: destroys/deletes the AVI player and clears command object `+0x10` |
| `0x599D50` / `0x599D80` | Deleting destructor / pathname cleanup; close and destruction are separate responsibilities |
| `0x493120` | A synchronous command runner: invokes vtable `+8`, repeatedly calls `+4` until false, then invokes `+12` |
| `0x59A4A0`, `0x59A650`, `0x59A900`, `0x59AAF0`, `0x59A530` | Legacy player construction, video open, audio open, frame decode and resource teardown |

An interception at `0x599C00` alone is insufficient: original path allocation,
initialization, update, close and destructor ownership must still agree. Reuse
the native `Stage::enter` / `remaster_body` call-routing boundary, with an
explicit guest ABI adapter and host registry keyed by movie-command identity.
Do not store host pointers in original object fields or fabricate an AVI object.
Only commands with a validated MP4 mapping take the modern path; other commands
continue their existing translated implementation.

Before implementing that adapter, confirm the actual INTRO and mission command
owners, both synchronous/asynchronous call paths, object reuse, time units,
nonvolatile registers, stack/return behavior, FP state, and exceptional teardown.
The constructor's byte flag is not yet assigned a semantic name. Keyboard/mouse
skip handling, focus behavior, movie volume and background music ownership are
not established by these focused static reads. Recover them through narrow
original/native observations before replacing behavior; do not invent shortcuts.

## Recommended first backend

Use Windows Media Foundation Source Reader for local H.264/AAC decoding and a
small host-owned media interface so a portable decoder can be added later.
Microsoft documents support for [H.264 High](https://learn.microsoft.com/en-us/windows/win32/medfound/h-264-video-decoder)
and [AAC-LC](https://learn.microsoft.com/en-us/windows/win32/medfound/aac-decoder).
That establishes a suitable candidate, not successful decoding on every tester's
PC. Probe the actual files and negotiate output before claiming compatibility.

Source Reader supplies samples, not a complete player: the application owns
presentation and A/V timing. See Microsoft's [Source Reader boundary](https://learn.microsoft.com/en-us/windows/win32/medfound/source-reader)
and [processing/draining guidance](https://learn.microsoft.com/en-us/windows/win32/medfound/processing-media-data-with-the-source-reader).
Use CPU-accessible decoded samples first; hardware acceleration and interop are
later optimizations after the software path meets the measured playback budget.

Prefer a shared-mode, event-driven WASAPI PCM sink for new movie audio. Use
`IAudioClock::GetPosition` together with `GetFrequency`, not submitted byte counts,
as the audio master clock. Microsoft's [clock contract](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclock-getposition)
defines position/frequency units and device-invalidated errors. Existing
`runtime/audio/local_cd_audio.hpp` is useful ownership/cleanup evidence, but its
44.1 kHz stereo CD/MCI semantics are not a general movie sink. Do not route movie
audio through a pretend CD device or change system mixer volume.

Alternatives considered:

| Option | Decision for first implementation |
| --- | --- |
| Existing WPF `CinematicWindow` | Retain launcher library use. A separate WPF window does not solve native window, event or script ownership |
| Source Reader + native audio/Vulkan | Recommended for the Windows x64 target and existing MP4 delivery files |
| Media Session / EVR | Full playback pipeline is useful generally, but default rendering introduces another display owner; custom Vulkan integration would still be needed |
| Pinned FFmpeg/libavcodec | Keep as a future portable backend or a response to a measured MF limitation. The existing installed encoding CLI is not a distributable runtime dependency |
| Legacy AVI conversion or renaming | Does not implement MP4; would add encoding/codec constraints and risks losing remastered detail |

The recommended path uses OS components, without bundling a codec executable or
downloading codecs. Record the exact compiler/Windows SDK/import-library
identities in the implementation build receipt. Delay-load/probe optional MF
entry points so a missing media component cannot prevent stock game startup.
Windows N may need the [Media Feature Pack](https://support.microsoft.com/en-us/windows/experience/platform-variants/media-feature-pack-for-windows-n);
show an actionable optional-cinematic error and allow disabling the pack.
Do not require a Windows SDK on players' PCs. No new third-party runtime package
is selected; if FFmpeg becomes necessary, first pin its source/build, hashes,
license configuration and notices as required by `CONTRIBUTING.md`.

## Playback, display and resource contract

Implement a host-owned player with `open`, `poll`, `request_skip`, `close` and
distinct continuing/completed/skipped/failed states. Workers never access guest
registers/memory or present Vulkan frames. The game/presentation thread consumes
bounded status/frame data through the original command adapter.

- Initialize COM/MF on their owning thread; release and shut down in the matching
  order. Prefer opening a validated local file byte stream rather than passing
  arbitrary URLs to the resolver. Recheck selected-file identity and keep its
  read handle stable during playback. No pack scripts, codecs, network streams
  or custom executable handlers are part of the pack contract.
- Enumerate streams and negotiate H.264 video plus optional AAC audio. Inspect
  decoded media types, dimensions, stride, orientation and allocation arithmetic.
  Reject unsupported formats and unexpected midstream type changes explicitly.
- Keep a small bounded video queue (initial target three frames) and bounded PCM
  queue (initial target at most 500 ms). Add byte caps as well as item caps; the
  catalog's compressed size is not a decoded-memory budget. Backpressure workers
  and make cancellation wake every wait. Never preload an entire decoded movie.
- Negotiate decoded YUV and perform a measured conversion into BGRA/RGBA for the
  first Vulkan path; a converter/MFT must be explicit and tested. Do not silently
  assume Source Reader's basic RGB conversion is fast enough. Honor color tags;
  for the current untagged footage, compare against the existing approved preview
  and record the chosen matrix/range policy before release. Do not infer BT.709
  merely from the upscaled resolution. NV12 shaders can follow if profiling
  identifies conversion/upload as the bottleneck.
- Add `present_movie_bgra` (proposed API) beside `Renderer::present` in
  `native-overrides/vk_scene.hpp`. Reuse the host presenter, window, swapchain and
  resize handling, with an independent 32-bit movie image/staging allocation.
  Current `present`/`presentSource` accept RGB565 and allocate two bytes/pixel.
  The new path must not reuse those assumptions or the guest backbuffer.
- Always fit the source display aspect to the actual client extent, with black
  bars and no crop/stretch. The current RGB565 path's conditional `widescreen()`
  fit is insufficient. Preserve window input ownership and host FP isolation;
  rebuild only needed movie/swapchain resources on resize.
- Schedule by sample timestamps. With audio, use played audio position, including
  start latency and resampling; for silent clips use a monotonic host clock.
  Keep mute clocked. On slow frames, hold/drop video as needed without speeding
  audio or altering gameplay ticks. After audio ends, advance any real video tail
  with a continuous monotonic clock; drain delayed samples and wait for both
  actual stream endpoints. Do not complete at the legacy 15 fps frame count or
  immediately on demux EOF.
- Derive gain, music stop/resume and focus policy from the recovered game
  contract. Handle minimize/focus/device loss without silently advancing story
  events; surface nonrecoverable errors. Keep `host.frames`, virtual simulation
  clocks, gameplay input replay and frame-budget side effects independent of
  movie presentation (`native-overrides/vdd.inc`).
- Skip cancels decode, stops/discards queued audio, releases GPU/file resources,
  and returns through the observed command completion path exactly once. Close
  and destruction must be idempotent. Prevent the skip input reaching the next
  screen according to the recovered input contract.
- An absent/disabled replacement uses the existing translated AVI path. A selected
  corrupt/incompatible MP4 is an explicit error, not fake successful completion.
  Offer retry with that replacement disabled rather than silently skipping a
  briefing or changing scripts. Renderer/device errors follow existing visible
  failure handling after deterministic cleanup.

Current screenshot/photo capture reads world `colorImage`, not every presented
image. Include selection of the active movie image in capture integration, or
explicitly disable screenshot capture during movies with a visible explanation;
do not return stale gameplay pixels as a movie screenshot.

## Versioned pack and launcher contract

Proposed names below are design decisions for the first contract PR, not formats
already recognized by a released launcher/runtime:

| Part | Proposed contract |
| --- | --- |
| Pack envelope | Existing schema-2 `.mw3pack`, new `prepared-cinematic-v2` payload profile and schema-2 cinematic registry |
| Media entry | Existing `id`, `title`, `source`, `replaces` fields; source `cinematics/media/<id>.mp4`, explicit original lowercase stem in `replaces` |
| File format | `MP4-H264-AAC-v1`; declared byte count and SHA-256 remain mandatory |
| Capability | `cinematic-replacements` version 2; update profile-to-required-version logic in C# and Python rather than retaining its hardcoded implicit version 1 |
| Runtime profile | Advertise support only after implemented; proposed `cinematic_media_versions: [1]`, separate from legacy `cinematic_path_versions` |
| Session catalog | New `MWCMED1` catalog / `MW34_CINEMATIC_MEDIA`, separate from `MWCINE1` / `MW34_CINEMATIC_PATHS`; never expose MP4 to the AVI filename substitution |

Keep `prepared-cinematic-v1` library and compatible AVI handling unchanged. The
runtime must advertise `cinematic-replacements: [1, 2]`, retain
`cinematic_path_versions: [1]`, and add `cinematic_media_versions: [1]`.
Capability checks require exact version membership, not a greater-than comparison;
advertising only version 2 would incorrectly reject existing v1 replacements.
The
new player is data-only optional content; community packs need no publisher
signature. Executable decoder/runtime updates remain in the existing trusted
update delivery, never supplied by an unsigned asset pack.

The modern catalog should carry bounded target, normalized absolute local path,
format identifier, byte count and SHA-256. Specify exact little-endian layout,
UTF-8 lengths, entry/byte limits, duplicate/trailing-data rejection and path
validation in the contract PR. Use wide Windows file APIs after strict UTF-8
decoding so non-ASCII user paths work. Clip duration/dimensions in metadata, if
added, are validation hints, never permission to allocate or advance a script.

Reuse the launcher's selected-pack priority and `cinematic/<target>` conflict
slot across both profiles. Warn on conflicts and use one winner deterministically.
Unknown capabilities fail before game launch with an update-required message.
Explicit empty capability tables must remain authoritative.

Repackage the current collection as a new, reviewed version with explicit
replacement targets from the existing 19-entry planning map, retaining the exact
verified MP4 bytes. Do not mutate the published library archive or infer targets
for arbitrary future packs from filenames. `replaces: null` continues to mean
library-only. Adding an entirely new story event requires a separate authorable
mission/event contract; this player does not invent mission triggers.

Implementation touchpoints: `CinematicPack.cs`, `PackStorage.cs`,
`PackManifest.cs`, `PackManager.cs`, `GameRunner.cs`,
`RuntimeContentCapabilities.cs`, `build_cinematic_pack.py`,
`content_capabilities.py`, runtime-profile staging/validation, the native command
adapter, and `vk_scene.hpp`. Audit every `CinematicPack.Profile` equality and
schema/version whitelist, rather than updating only the import dialog. Existing
`ArtworkCinematicChecks.cs`, `test_artwork_cinematic_packs.py` and
`test_cinematic_paths.cpp` provide compatibility checks to extend.

## Implementation PR sequence and completion gates

| PR | Work | Required evidence before moving on |
| --- | --- | --- |
| 1: lifecycle and decoder feasibility | Verify original INTRO/mission start, update, skip, close, focus, volume and outer script ownership. Exercise actual MP4 samples with MF using a private probe, plus authored color-bar/tone clips | Written ABI/lifecycle contract; H.264 High/AAC mono/stereo decode, timestamps, drain, optional component failure and bounded memory proven. No production capability advertised |
| 2: native media service | Add bounded MF decoder, WASAPI clock/sink and full-resolution Vulkan movie API, with authored clips | Synchronized complete playback, color/stride/aspect, silent/audio-tail endpoints, cancellation, repeat cleanup, resize/minimize and device/error handling. Presentation stays independent of guest simulation |
| 3: game command adapter | Connect only mapped commands to modern playback, preserving original sequencing and no-pack path | INTRO full completion + skip -> live menu; mission briefing -> correct next screen; repeated playback/quit; exact guest return/FP/ownership checks; no legacy movie audio/raster running underneath |
| 4: pack/import integration | Add v2 format, capabilities, session catalog, modder example and builder; revise collection metadata | Authored valid/invalid packs across C#/Python/native, deterministic conflicts, Unicode paths, old-library/AVI compatibility, old-runtime rejection, and exact MP4 preservation on repack |
| 5: release validation | Validate all 19 mappings and publish only after normal feature/release PR merges | DEV and clean installed PC use identical pack bytes; representative real script transitions and full endings; update/rollback/pack-disable/no-pack regression; signed versioned artifacts and website checks |

PRs 2 and 4 must not imply in-game support until PR 3 is integrated and verified.
The first visible vertical slice is INTRO; no full-library reprocessing or
campaign-wide implementation claim is needed to begin. The actual command
semantics and target-PC performance are prerequisites to a reliable effort
estimate. This is several component changes and testing, not just a manifest edit.

Acceptance includes all 19 catalog entries opening/decoding to their endpoints;
INTRO, CAMPAIGN, a mission briefing and C4WIN through real game requests;
Escape/click behavior as observed in the original; repeated skip/play/quit;
4:3 and widescreen windows/fullscreen; focus/minimize/resize; missing media
components/audio endpoints; malformed/truncated media; and clean return to
original rendering/audio. Aim for A/V skew within one 24 fps video frame
(41.7 ms) after startup and no accumulating drift, measured on both machines.
Record dropped frames/underruns and peak resident/queued/GPU memory; a decode-to-null
benchmark on DEV does not establish integrated minimum hardware requirements.

Asset-free tests use authored media fixtures only. Private cinematic footage,
original binaries, traces and generated code stay local. Documentation checks
for this planning PR are link/source consistency and `git diff --check`; no
production game build or release is warranted by a plan alone.

The shipping change will need both a launcher `.ccupdate` and native
`.mw3update`, plus the optional revised cinematic `.mw3pack`. A fresh installer
should later bundle those merged launcher/runtime builds. Follow the existing
[PR/release workflow](github-workflow.md) and versioned artifact filename rules;
do not publish media in the public update-only feed or bundle it into the setup.
Preserve the original-compatible decoder and the historical library download.
