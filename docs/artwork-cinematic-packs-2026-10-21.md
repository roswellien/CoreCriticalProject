# HUD, menu and cinematic pack deployment

The playtest launcher adds independent artwork and cinematic contracts to
**Mods & Packs → Install New Pack**. These are optional content resources;
layout, controls and game logic remain in the native runtime. Packs cannot
provide commands, code, DLLs, registry settings or arbitrary process flags.
Strict native acceptance remains **131/144**.

## Local content to use

The completed HUD/menu archives are under
`local/asset-packs/artwork-20261021-r2/`:

| Archive | Contents | Compressed bytes |
| --- | --- | ---: |
| `hud-1.0.0.mw3pack` | 27 current HUD sprites | 26,130 |
| `menu-1.0.0.mw3pack` | 26 menu sprites and 5760×4320 background | 58,998,167 |

These preserve every source resource byte. Unused authoring manifests are
excluded. `packs.json` records complete file pins and archive readback checks.
The small HUD archive reflects compression of the existing sprite resources;
it is not a placeholder pack. Rebuild with `build_ui_packs.py` against the
selected native profile, using a fresh output directory.

Mission lighting is already included in all five version 1.1.0 environment
archives under `local/asset-packs/environments-lighting-20261021-r1/`:
Training and Operations 1–4. Reuse these completed archives; their existing
texture/normal/detail resources are unchanged. See the
[mission-lighting integration](environment-pack-mission-lighting-2026-10-21.md).

All original-derived packs and movie controls remain local under the existing
[distribution policy](legal.md). Their creation does not authorize publication.

## Artwork contract

Schema-2 `pack.json` declares `native_payload.profile: prepared-ui-v1`,
`registry: ui/ui.json`, `path_base: pack-root`, a matched
`reference_host_sha256`, exhaustive `files` hashes/lengths and the required
formats actually used. The registry is:

```json
{
  "schema_version": 2,
  "payload_profile": "prepared-ui-v1",
  "kind": "hud",
  "sprites": {"0123456789abcdef": "ui/sprites/0123456789abcdef.rgba"},
  "background": null
}
```

`kind` is `hud` or `menu`. Sprite identities match the original native reader.
`MW3H-v1` resources have a 28-byte header: `MW3H`, little-endian width/height,
four float UV bounds, then exactly width × height × 4 RGBA bytes. Dimensions
are 1–8192; UV coordinates must be finite, ordered and within [0,1]. A menu
may also bind `ui/background.mwhd`, format `MWHDBG1`: eight-byte
`MWHDBG1\0` magic, little-endian width/height/source-width/source-height, then
exactly width × height × 3 RGB bytes. Dimensions are 1–16384.

There are at most 256 sprites and 512 MiB of expanded artwork per pack. The
first enabled pack wins per kind. Disabling all restores original menu art
and explicitly disables the HUD reader's historical loose-directory fallback.
The two native sprite readers share an identity table: conflicting selected
HUD/menu identities with different hashes reject visibly. Unregistered loose
files in the sprite directory also reject. Artwork never enters mech or
environment pack dispatch.

## Cinematic contract and current limits

Schema-2 `prepared-cinematic-v1` uses `cinematics/cinematics.json`:

```json
{
  "schema_version": 2,
  "payload_profile": "prepared-cinematic-v1",
  "clips": [
    {"id": "opening", "title": "Opening", "source": "cinematics/media/opening.avi", "replaces": "intro"},
    {"id": "bonus", "title": "Bonus scene", "source": "cinematics/media/bonus.mp4", "replaces": null}
  ]
}
```

The file table is exhaustive and hash-verified at install and use. The registry
allows 1–64 uniquely identified clips. Unknown trigger fields and code payloads
reject. Author packs with `build_cinematic_pack.py --description ... --output ...`.
Its authoring description uses the same clip fields, with source paths relative
to the description (or absolute), plus pack `id`, `name`, optional `version`
and `reference_host_sha256` for in-game replacements. The launcher remains the
authoritative format validator before installation.

* **In-game replacement:** `replaces` is an original lowercase AVI filename
  stem. It must exist in the selected game's Video directory. First enabled
  replacement wins for each target; conflict inspection reports that order.
  The current admitted format is `AVI-IV50-original-v1`: complete RIFF AVI,
  one 640×480 IV50 video stream at 15 fps and optional original-compatible
  22050 Hz PCM audio (mono/stereo, 8/16 bit). This is a conservative versioned
  admission, not a claim that the original engine intrinsically requires those
  dimensions. Modern MP4/HD/AV1/MKV in-game decoding is **not implemented**.
* **Addition:** `replaces: null` declares `MP4-library-v1`. Enabled additions
  appear under **Watch installed cinematics…** in Mods & Packs. The WPF player
  preserves aspect ratio and offers Play/Pause/Restart/Close. Playback uses
  installed Windows media components; unsupported codecs fail visibly.
  H.264/AAC MP4 is the current compatibility target. This library does not
  insert new story events into guest missions. New automatic in-game triggers
  require a separately implemented and validated lifecycle boundary.

For replacements the launcher creates an exclusive session-owned `MWCINE1\0`
binary catalog: uint32 count, then uint32 key/path byte lengths and UTF-8 bytes.
The native reader bounds count/lengths, rejects duplicate/unsafe keys, missing
files and trailing/truncated data. It redirects only AVI stream reads; writes
through the replacement binding reject. Original movies are never overwritten.
Disabled or absent packs retain the existing original movie path. Current
native narrow-path support requires ASCII-only replacement media paths; this
fails explicitly rather than silently selecting another file.

The staged private runtime now also includes an explicit, hash-bound original
decoder resource through `MW34_IV50_IMAGE`, avoiding the historical assumption
that the game is beside the development checkout. This resource is supplied by
the trusted runtime, never a content pack. The C# coordinator checks its identity
before launch; an explicitly configured missing native resource also fails.
This fixes the observed external-runtime movie omission. Permitted user-file
generation of native runtime/codec artifacts remains a release prerequisite.

The selected successor is `gpu-native-cinematic-packs-r2`, SHA-256
`9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83`.
Compared with the lighting host, 116 source pins are identical. Only
`main_v2.inc` (explicit codec path) and `mfc_stage.hpp` (AVI read routing)
change, with one added `cinematic_paths.inc`; all 119 final source pins verify.
The translated object list and remaining readers/settings are retained. The
maintained MFC template predates that host's fixes and was not copied wholesale.
`apply_cinematic_codec_path.py` reproduces the exact codec-path change on a
fresh snapshot. Exact mech/environment admissions include this reviewed host,
including environment packs whose reference identity is the lighting host.

## Validation and evidence

Local records are under `reports/artwork-cinematic-packs-20261021/` and external
`D:/MW3ArtworkCinematicTrial-20261021-r1` through `r3`.

* C# checks cover installation, ordering, disabling, corruption, failed-update
  preservation, UI identity collisions, host/capability mismatch, unknown movie
  triggers and unsupported formats. They use authored fixtures without game data.
* Python authoring checks cover exact archive membership/hashes, preserved source
  bytes, exclusive output and wrong-role/truncated artwork rejection.
* The actual native routing reader passes valid/no-match/absent maps and rejects
  truncated, trailing, duplicate, unsafe, missing-file and empty maps. It also
  consumed the actual C#-generated installed movie catalog successfully.
* External r1 loaded all 53 installed sprites and the menu background for 180
  Vulkan presentations. It exposed the missing codec dependency; that evidence
  is retained, not treated as a movie-playback success.
* External r2 with the repaired decoder presented 180 real-clock opening frames.
  Both AVI audio/video opens, stream reads and the translated IV50 codec returned
  success. The pack uses an **unchanged original intro as a routing control**,
  not an enhanced movie. The separate authored silent MP4 pattern was actually
  displayed by the WPF player; Restart, Pause and Close were exercised on screen.
* The first combined Training attempt exposed a missing exact host admission
  for lighting-host-referenced environment packs. The narrow admission and a
  regression check fix that defect; the failed attempt remains in r2.
* External r3 prepared all selected content. Its first fresh-game run reached
  the original pilot screen, without a pilot yet created. A follow-on run using
  the completed composed profile and the established `i` test pilot reached
  Training: 340 Vulkan presentations, final 16,920 CPU / 1,287 GPU vertices,
  two GPU batches. HUD/menu packs, both mech packs, Training/Operation 1
  environments with lighting catalogs and soundtrack were enabled. Intro skip
  used ordinary scripted Escape input. No pilot fields or AFTER state were
  seeded. Exit 1 is the explicit presentation budget, not normal shutdown.
* Both native builds, 28 Python checks, the full C# launcher suite and a
  self-contained Windows publish pass. Source and executable identities were
  checked again before deployment. Launcher 1.0.11-preview is deployed with
  the two artwork packs enabled after the existing three packs; other user
  settings and environment migration state are preserved. Previous GUI entry
  files, published profile and settings are in `before-deploy/` under the
  report directory. The real dashboard shows 5/5 active packs, the original
  3440×1440/FXAA/AF16 settings and Ready status.
* Final deployed GUI Play also reached the live native main menu, loading all
  53 pack sprites and the menu background. Ordinary Alt+F4 closed normally with
  exit 0 after 1,428 presentations and native DLL detach; the launcher returned
  to Ready. The actual session is
  `%LOCALAPPDATA%/MW3Remaster/sessions/0bcc2c48f11040ee8b30f5bee757e0ef`.

The enhanced intro work currently documented in
[opening-cinematic-current-work.md](opening-cinematic-current-work.md) is a
30-second enhancement preview, not a completed full opening replacement.
No enhanced cinematic release pack was fabricated from that excerpt. Continue
with the [modern in-game decoder plan](cinematic-compression-and-runtime-plan.md)
for higher-resolution movies and validate skip, completion, audio synchronization,
repeated playback and mission transitions before calling that path playtest-ready.
