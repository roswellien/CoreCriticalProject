# MW3-RE: playing the owner's HD MP4 cutscenes in game (research, 2026-11-16)

> **Update 2026-11-16, after the owner's answers (section 9):** the owner requires cross-platform playback, so the
> Windows-only Media Foundation recommendation in sections 1 and 3.4 is superseded. Section 9 records the decisions and the
> revised decoder recommendation (FFmpeg shared libraries, already built and bundled by `tools/deps/build_deps.sh`).

Read-only research. Nothing was built or run, and no game was started. No long job was running (python and claude
processes only, no ffmpeg or cmake). Paths are relative to `runtime/mw3-re/` unless they start with `tools/` or are
marked `develop:`. The launcher planner and runtime contract are not in this checkout, so I read them from
`origin/develop`. Tags: **[C]** confirmed in code or files, **[L]** likely, **[G]** guess.

## 1. Recommended design (one page)

**HD sidecar. The game's own movie script keeps owning the lifecycle. Only the picture and the sound source change.**

1. **Substitution point: the AVI, by name.** The script plays `<FMV_PATH>\<name>.avi` through `zfmv::Host`. A block such as
   `c1m1` plays two AVIs (`c1` 870 frames, then `c1m1` 690) **[C]**. The pack's 19 clips are those 19 distinct AVIs: all 19
   durations equal original frames / 15 fps within 0.1 s (intro 182.5 s vs 2737/15, campaign 204.29 s vs 3064/15,
   c4win 72.2 s vs 1083/15) **[C]**. So substitute in `GameFmvHost::file_stat` and `avi_open` (`app_fmv.cpp:112,119`) by
   AVI base name. Never substitute by block name.
2. **Serve a synthetic stream instead of the Indeo or MPEG-1 one.**
   - *Picture:* length equals the original `dwLength`, from `movie_shape_table.cpp`, at 15 fps. Nothing is decoded into the 16-bit buffer.
   - *Sound:* the AAC track decoded to 22,050 Hz PCM16 and served through `AVIStreamRead`. The ported zSound stream (`zsnd_create.cpp`),
     `--nosound`, volume, the cursor-driven frame count, Space/Esc/Enter skip, c4win under `-nofmv`, the CD-music pause and
     "movie finished" stay original, because the ported script and engine run unchanged **[C]**. Our player never signals completion.
   - A side effect: replaced movies need neither the importer files nor the Indeo helper.
3. **Pixels: a GPU overlay, drawn every pass.**
   - *Decode:* a Media Foundation `IMFSourceReader` on its own thread (H.264 to RGB32, plus AAC to PCM). It keeps a 3-4 frame queue
     tagged with pts.
   - *Clock:* each pass, `GameEngine::movie_playing` (`app_fmv.cpp:430`) is the tick that runs while the movie plays. It picks
     the newest frame with pts ≤ the zSound play cursor (samples / 22,050), uploads it if it changed, and presents.
   - *Upload and draw:* reuse `SdlScreen2D` (`sdl_platform.cpp:209-247`). Upload goes through `FrameRenderer::create_texture` and `update_texture`;
     the draw is a sharp quad in a 4:3 viewport with black bars, like the HUD layer.
   - *Interaction with the game's flip:* while an HD stream is open, `video_flip` (`app_engine.cpp:721`) must not call `present_16`, which would
     overwrite the HD frame.
4. **Fallback:** any failure (no decoder, a bad file, a duration mismatch over 1 s) gives the original path for that clip. Log one line,
   like the Indeo helper's `movies not through the Indeo helper (why)` (`docs/fmv.md:385-388`).
5. **Pack and planner:** a new replacement format for MP4 and a `--hd-movie NAME PATH` option. An `hd-movies` capability is checked by the launcher. See §3.6.

**Why not the 16-bit surface (Q2).** The claim is **confirmed [C]**. The game draws into `buffer_`, a `uint16_t` buffer of `width_ x height_`
(`app_fmv.cpp:46-47,480-495`; `app_engine.cpp:738`), at 640x480, or 853x480 with wide menus. `fmv_stretch` samples it nearest-neighbour, in RGB565.
That is about 4x fewer pixels than 1280x960 (640x480 on the 853x480 canvas, the original on-screen size) and 5-6 bits per channel. Even a
1920x1080 canvas (`docs/fmv.md:517-519`) is still nearest-neighbour 16-bit. The upgrade would be lost.

## 2. Alternatives considered

| Alternative | Verdict |
|---|---|
| **(b) Replace the 16-bit path with an HD surface** | Rejected. `buffer_` is shared by menus, fades, blur, grabs and message boxes (`fmv_script.cpp:198-440`), so the change is invasive, and the differential tests (`tests/differential/test_fmv.py`) pin that code. |
| **(c) Separate SDL window or texture** | Rejected. It breaks borderless/fullscreen focus and alt-tab, and DXGI interop owns the main swapchain (`dxgi_present.hpp:19`). It gives a second Vulkan device or surface and a second present loop. |
| **Own `movie_playing` in the player ("movie finished" from us)** | Rejected. It risks the skip, CD-pause and c1m1 two-AVI chain that already works. |
| **FFmpeg shared DLLs** (recommended fallback, §3.4) | More portable, but ships 4+ DLLs, needs an LGPL-only build, notices, and pinning in `runtime.json`. |
| **openh264** | Baseline-profile decode only; the clips are High profile **[C]** (ffprobe). Rejected. |
| **Offline transcode to MPEG-1 for `pl_mpeg`** | Zero new runtime code, but it re-encodes lossy over lossy, needs about 8-10 Mbps (larger files), and gives MP2 audio. Keep only as a manual last resort **[L]**. |
| **A/V clock = video master** | Rejected. The game derives frames from the sound cursor, as on Windows (`docs/fmv.md:248-262`). |

## 3. Detail by question

**3.1 Lifecycle [C].**
- `start_movie` creates the script, loads `fmv.zrd` and plays it (`app_states.cpp:45-52`). Callers: INTRO and SPLASH, ATTRACT, `campaign` (pilot menu), `c<op>m<n>`
  (before the briefing), and `c4win` (`docs/fmv.md:13-22`).
- The poll is `movie_playing` each state update. Skip is Space, Esc, Enter or keypad Enter (`docs/fmv.md:73-77`).
- A missing movie ends the action at once (`docs/fmv.md:159-165`, `file_stat` returns -1).
- The stream answers 0 past its last frame and the action ends (`docs/fmv.md:174-176`).
- `GameEngine::movie_*` pause and resume the CD (`app_fmv.cpp:412-445`).
- Signals that must still arrive: the stream-end answer, the key poll, and the sound cursor.

**3.2 Q3, option (a) detail [L].**
- *Sizing:* `Renderer::present` already takes arbitrary w/h RGBA (`vk_scene.hpp:293-295`; the first-frame path uses it, `frame_presentation.inc:39`). Draws are
  viewport pixels scaled onto the resident target (`vk_scene.hpp:879`), so a 1280x960 quad is resampled once, at window scale. The
  `present_16` canvas-size problem (a small target) must be checked in the spike: set the viewport to the output rect, not 853x480.
- *FXAA:* it is world-only (`quality_stage.inc:1`), so it does not touch the quad **[C]**.
- *Presenter:* the same one, so Vulkan WSI vs DXGI interop makes no difference to us; there is no new interop **[L]**.
- *Render worker:* the present is posted (`frame_presentation.inc:82-85`), and texture bytes ride the scene packet. At 24 uploads a second the cost is about 5 MB each **[L]**.
- *HUD and menus:* during a movie, no 3D scene is drawn, so `GpuHud` is not active **[L]**.
- *Pillarboxing:* at 3440x1440 the 4:3 picture is 1920x1440, using the same bar logic as `fmv_stretch` (`app_fmv.cpp:474-482`). It is a black clear plus a quad.

**3.3 Q8 Performance and memory [L].**
- Decode thread: one, a 4-frame queue of 1280x960 RGBA (about 20 MB at most; NV12 or BGRX frames about 5 MB each).
- PCM up front: intro 182.5 s stereo is about 16 MB; others are smaller. Or stream it.
- Texture 4.9 MB, plus the render packet copy. Ceiling about 50 MB, freed at the clip's end.
- Software H.264 at 1280x960, 24 fps, is a small fraction of one core. DXVA is optional.

**3.4 Q4 Decoder [L].**
- *Media Foundation (recommended first):*
  - `MFCreateSourceReaderFromURL` with `MF_SOURCE_READER_ENABLE_VIDEO_PROCESSING` gives RGB32 and PCM; no DLLs, no licence, Windows-only.
  - Hardware decode is available through `MF_SOURCE_READER_D3D_MANAGER`, but it is not needed.
  - Windows N editions without the Media Feature Pack lack the decoder. Probe with `MFTEnumEx(MFT_CATEGORY_VIDEO_DECODER, MFVideoFormat_H264)` and the AAC decoder at start-up. If either is missing, log
    "HD movies unavailable: install the Media Feature Pack", use the original movies, and report it via an exit-code or `--probe-hd-movies` line the launcher can show.
  - macOS and Linux keep `pl_mpeg`, behind an interface and a null backend that tests use.
- *FFmpeg:* already an optional build-time dependency (`CMakeLists.txt:832-840`, `mw3import.cpp:41-43`) but never shipped. Choose it if MF's seeking or timing is poor, or if cross-platform HD is wanted.

**3.5 Q5 Audio and sync [L].**
- The game's zSound is already on SDL3 audio (F32 stereo, `sdl_sound.cpp:25,218-233`), so we add no audio device.
- The master is the zSound cursor. Pause on focus loss, volume and `--nosound` (a silent cursor that moves with the clock) are inherited.
- A/V drift is bounded by the cursor, because the picture reads the same cursor.
- Skip stops the decode thread when the stream is released.

**3.6 Q6 Pack, planner, launcher.**
- `replaces` set on an MP4 flips the format to AVI today (`CinematicPack.cs:104,110-111`): only {id,title,source,replaces}, and `.avi` is forced. Add `schema_version 3` and a format
  `MP4-H264-replacement-v1`. The `replaces` value is the AVI base name. Keep `intro` etc. as library entries too, so one pack serves both uses **[L]**.
- Validation: the launcher checks hash and size (pack manifest), the `ftyp` header (`CinematicPack.cs:121`), and a limit table (<= 1280x960 is not required; 16-1920 wide, <= 30 fps, <= 400 s, <= 250 MB). The runtime checks duration against the table.
- Planner: `tools/remaster-launcher/mw3_re_launch.py` (develop) stays one self-contained file and emits `--hd-movie NAME PATH`, repeated, or nothing when the setting is off or the pack is invalid.
- Capability: `hd-movies` v1 in `runtime.json`, checked like `controller-profile` (`Mw3ReRuntimeContract.cs:28-30`, develop). A missing capability means no HD args and a note in the plan.
- Setting: "HD cinematics" on/off, plus runtime `--no-hd-movies`. Gameplay and the startup flow are unchanged.

**3.7 Q7 Edge cases.**
- Durations match, so briefing music and mission start are unchanged **[C]**. Because the original timing comes from the sound, even a mismatch only shifts the end time **[L]**.
- `campaign` and `c4win` are single AVIs. `c4win` plays regardless of `-nofmv` (`app_states.cpp:94-96`).
- The intro plays once, then SPLASH stills use the 16-bit path unchanged.
- Alt-tab and resize: the layer redraws each tick, and the texture persists. After device loss it is re-uploaded **[L]**.
- 24 fps on a faster display: frames repeat. 60 Hz gives a 3:2 cadence. Use frame selection by clock, no blending **[G]**.
- The pack's audio is AAC 22.05 kHz, mono or stereo (ffprobe). The original streams were 22.05 kHz PCM (`CinematicPack.cs:71`), so no resampling is needed.

## 4. Tasks, effort and the first spike

| # | Task | Days |
|---|---|---|
| 1 | Decoder interface plus MF backend (video queue, AAC to PCM, probe) | 3-4 |
| 2 | Host integration: synthetic stream, flip suppression, the tick | 3-4 |
| 3 | HD layer in `SdlScreen2D`, sizing, bars | 2-4 |
| 4 | Pack format, validation, planner, capability, setting | 3-4 |
| 5 | Tests: synthetic clip, fakes, planner and C# cases | 2-3 |
| 6 | Playtest, DXGI and render-thread passes, polish | 3-5 |
| | **Total** | **16-24** |

**Smallest spike (3-5 days):** `mw3 --hd-movie intro PATH` plays the owner's `intro.mp4` in place of `intro`.
Acceptance:
1. It plays at 1280x960 pixels (a screenshot at 3440x1440 shows a 1920x1440 4:3 picture, not 853x480 nearest-neighbour), with audio.
2. The intro ends on its own at about 182.5 s and SPLASH follows.
3. Space or Esc skips.
4. With `--nosound` it still finishes.
5. Memory stays under about 60 MB above the baseline.
6. With the option removed, nothing changes.

## 5. Risks, ranked

1. **Overlay sizing in the Core Critical path:** the `present_16` canvas could resample down. Spike item 1 answers it. If it fails, use the output rect or the `present` RGBA path.
2. **Per-pass tick and flip interaction with the ported script** (`movie_playing` is polled, but a flip happens only on frame change): confirm with `MW3_MOVIE_TRACE`.
3. **Render worker upload cost and hashing** at 24/s.
4. **MF on N editions and its seek and timing behaviour:** the plan changes to FFmpeg LGPL DLLs if the probe fails often.
5. **24 fps on 60/144 Hz judder:** cosmetic.
6. **Pack format change** touches two repos' files (launcher C# and planner) and `runtime.json` pinning.

## 6. Open questions for the owner

- Should one pack serve both the Cinematics window and in-game, or is a separate replacement pack acceptable?
- Is Windows-only MF acceptable (macOS keeps the originals)?
- Do you want HD movies to work without the original AVIs or importer files installed?
- What counts as a failure when one clip is invalid: only that clip falls back, or the whole pack?
- Is a 24-fps repeat cadence acceptable, or should the display be matched?

## 7. Test plan

- **Asset-free:** a synthetic clip made at test time, never committed and never original media:
  `ffmpeg -f lavfi -i testsrc2=s=320x240:r=24:d=2 -f lavfi -i sine=f=440:r=22050:d=2 -c:v libx264 -pix_fmt yuv420p -c:a aac -ac 1 t.mp4`.
  Cases: a fake decoder backend; frame-pick logic by cursor; manifest and limits validation; planner and capability checks (`tools/remaster-launcher/test_mw3_re_launch.py`, develop); fallback logs; the dummy audio driver plus `--movie` style runs.
- **Real session only:** A/V sync on the 182 s intro, skip, alt-tab, borderless/fullscreen at 3440x1440, DXGI interop and render thread, hardware decode, an N edition, long-run memory.

## 9. Owner decisions and revised recommendation (2026-11-16)

**Decisions (answers to section 6).**

| # | Question | Answer |
|---|---|---|
| 1 | One pack for the Cinematics window and in-game? | **Yes.** |
| 2 | Is Windows-only decoding acceptable? | **No.** Cross-platform (Windows, macOS, Linux) is required. |
| 3 | HD movies without the original AVIs or the importer files? | **Yes.** The design already serves a synthetic stream by AVI name, so neither the importer files nor the Indeo helper is needed for replaced movies. |
| 4 | One invalid clip? | **Only that clip falls back** to the original; the rest of the pack plays. |
| 5 | Repeat frames when 24 fps meets a faster display? | Asked what it looks like; see below. |

**What question 2 changes.** Media Foundation is Windows-only, so it can no longer be the only backend. Checked against the repo:
- `third_party/` holds only `enet imgui miniupnpc miniz nlohmann-json pl_mpeg`. `pl_mpeg` decodes MPEG-1 only.
- `tools/deps/build_deps.sh mac|linux|win` already builds **FFmpeg 8.1.2 (LGPL 2.1, shared)** from source for all three platforms,
  with a pinned tarball, and the releases bundle its libraries for `mw3import` (`docs/deps.md`, `docs/release.md`). Today it is
  configured with only what the importer uses (the AVI demuxer and what it needs), and `mw3` itself does not link it.
- `docs/legal.md` says nothing about codecs or patents. H.264 is patent-encumbered, so shipping a software H.264 decoder in the
  game is an owner or legal decision for any public release. The pack manifests currently say private playtest only.

**Format options for cross-platform playback.**

| Option | Pack files | Decoder in the game | Pros | Cons |
|---|---|---|---|---|
| **A. Keep H.264 + AAC MP4 (recommended)** | The owner's files, unchanged | FFmpeg shared libs, configure widened to the H.264 and AAC decoders, MP4 demuxer, scaler and resampler | One pack and one decode path on all platforms. No re-encode, so no quality loss. The Windows launcher window (WPF `MediaElement`) keeps playing the same files, as decision 1 needs. The FFmpeg build and bundle pipeline already exists. | Ships FFmpeg libraries with the game (the release already bundles them for the importer). H.264 patent question for distribution. |
| B. VP9 + Opus (WebM) | Re-encoded from the lossy H.264 (generation loss) | Same FFmpeg libs, native decoders only | Royalty-free. Same plumbing as A. Smaller files (my guess, 30-40%). | Windows `MediaElement` cannot play it without extensions, so the launcher window needs another player. Re-encode quality loss. |
| C. MPEG-1 + MP2 | Re-encoded, large | `pl_mpeg`, already vendored | No new dependency, no patent question. | Roughly 1.5 GB for the pack (my estimate), visibly lower quality, two lossy generations. Launcher window cannot play it. |
| D. AV1 + Opus | Re-encoded | dav1d + libopus + a container library | Best compression, royalty-free. | Two new dependencies, `MediaElement` needs the AV1 extension. Not worth it now. |
| Media Foundation (Windows) | Unchanged H.264 | OS decoder | Nothing to ship. | Windows only. May be added later as an optional hardware-accelerated path; not needed. |

**Revised recommendation: option A**, with the codec behind the decoder interface so switching to B costs only a re-encode and a
different FFmpeg configure line. The decoder interface, host integration, HD layer, planner and launcher design in sections 1-7
are unchanged. Changes to the plan:
- Task 1 becomes an FFmpeg backend (demux, decode, scale to RGBA, resample audio to PCM16 at the movie's rate), 3-5 days.
- New task: widen `build_deps.sh`'s FFmpeg configure, link it into `mw3`, bundle and pin the libraries in the release and in
  `stage_mw3_re_runtime.py` (the staging recipe allows only a fixed DLL set), add the licence notices, 2-3 days.
- Estimated total about **18-28 developer-days** (was 16-24). The first spike (one clip at full resolution with audio) is still
  3-5 days, on one platform first.
- The N-edition probe in section 3.4 is no longer needed, because the game ships its own decoder.

**Question 5: what repeating frames looks like.** A 24 fps frame lasts 41.7 ms. On a **60 Hz** display (the owner's display is
3440x1440 at 60 Hz) each refresh is 16.7 ms, so frames are shown for 2 or 3 refreshes in turn (33 ms, then 50 ms). That uneven
rhythm ("3:2 pulldown") shows as a faint judder on slow, steady camera pans. It is invisible on 120, 144 and 240 Hz displays (an exact
multiple) and with variable refresh. The original movies were 15 fps, which fits 60 Hz evenly (4 refreshes each), so the
upgrade is smoother in frame rate but with a slightly uneven rhythm. Options:
- **Repeat frames** (the plan): sharp and cheap, judder as described.
- **Blend neighbouring frames:** removes the judder but softens and ghosts motion.
- **Match the display rate:** only on variable-refresh displays.
Recommendation: repeat frames, no blending, no setting. Revisit only if it bothers in play.

## 8. Evidence list

- `docs/fmv.md:13-33` callers and blocks [C]; `:73-77` skip keys [C]; `:159-178` movie action, not-found [C]; `:248-262` the sound sets the frame [C]; `:321-334` importer files [C]; `:366-388` Indeo helper and fallback log [C]; `:442-453,517-519` wide screen and canvas sizes [C]
- `src/mech3/app_fmv.cpp:36-60` host; `:112,119` file_stat/avi_open; `:412-445` movie_* and CD; `:462-498` fmv_stretch [C]
- `src/mech3/app_engine.cpp:715-746` video_flip and present_16 [C]
- `src/mech3/app_states.cpp:45-56,79,94-115` start/end movie, attract, win [C]
- `src/mech3/app_movie.h:11-60`, `app_movie.cpp:119-123,160-195` pl_mpeg and 16-bit convert [C]; `src/mech3/movie_shape_table.cpp` frame counts [C]
- `src/frontend/sdl/sdl_platform.cpp:209-263,275-302` texture, present_16, overlay [C]; `gpu_hud.h:19-31` [C]
- `src/frontend/core_critical/renderer/vk_scene.hpp:293-295,520-531,879` present/resident/viewport scale [C]; `frame_presentation.inc:39,82-85`; `frame_submission.inc:29`; `renderer/quality_stage.inc:1` [C]; `renderer/dxgi_present.hpp:19` [C]
- `src/frontend/sdl/sdl_sound.cpp:25,218-233`, `sdl_music.cpp:126` SDL3 audio [C]; `mw3_main.cpp:449-450` helper options [C]
- `tools/mw3-remaster-launcher/Core/CinematicPack.cs:71,104,110-121`; `PackManager.cs:246-249` [C]
- develop: `tools/mw3-remaster-launcher/Core/Mw3ReRuntimeContract.cs:28-30`; `tools/remaster-launcher/mw3_re_launch.py:756-760` [C]
- `CMakeLists.txt:832-840`; `tools/import/mw3import.cpp:41-43` [C]
- Pack: `%LOCALAPPDATA%\MW3Remaster\mods\com.mw3remaster.cinematics-960p24-library` (`cinematics.json`, `pack.json`, ffprobe of intro, c1m1, c4win, campaign, c3m5: H.264 High 1280x960 24 fps, AAC 22.05 kHz) [C]
