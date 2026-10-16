# Pirate's Moon native startup

Implementation begun 2026-10-15. The first milestone is a live native PM menu,
real input and normal shutdown, using the shared MW3 runtime and Vulkan.
This document distinguishes recovered static paths from executed boundaries.
The scripted menu slice is complete: native PM presents its live menu through
Vulkan, opens Options, returns to the menu and quits normally with code zero
after native dependency detach. All 210 scene fingerprints match the original
reference. Physical-device operation has not been manually checked; cinematics
and missions remain unverified.
MW3's accepted startup-root count remains **131/144**; its receipt still hashes
to `aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061`.

## Completed menu slice and local handoff

Final native run: `reports/pirates-moon/play-20261015-133837-588/`.
It executes 2,308,340 translated bodies and 449,866 service calls, presents
210 frames, then reports `ExitProcess(0) after native shutdown` with native
detach of MSVCP60, MFC42 and MSVCRT. It exits before the 300-frame budget.
The original reference also quits after frame 210. All 210 draw counts/scene
hashes match; seven paired captures have mean absolute RGB channel differences
between 0.29 and 0.76 on the 0..255 scale. Pixels are not identical.

The bounded comparison, paths and executable/profile hashes are retained in
`reports/pirates-moon-startup-r1/menu-options-quit-comparison-r1.json`.
Native executable SHA-256:
`fe6ab4647eba94d546a5e9c4099b4e1289957203d66c5053bc7ac7cbd3301653`.
This experimental execution does not register M4 acceptance or grant admission
from the original-side hook. The preceding faults and failed lifts remain intact.

Current build: `build/pirates-moon-native-r1/shared-host/pirates_moon_native.exe`.
Its generated profile is `reports/pirates-moon/startup-r1/host-r73`, combining
closed lift reports **1 through 75**, with 9,199 verified native entries.
To launch with physical input (the default), using the currently mounted PM CD:

```powershell
./tools/pirates-moon/play.ps1 -MediaDrive H: -NoFmv
```

The tested scripted route is separate:

```powershell
./tools/pirates-moon/play.ps1 -MediaDrive H: -NoFmv -Frames 300 -Dump 30 -Script tools/pirates-moon/input-menu-options-quit.txt -Clock 50
```

Rebuild from the closed local reports into a fresh generated directory:

```powershell
$generated='reports/pirates-moon/startup-r1/host-handoff-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')
$arguments=@($generated)
foreach($n in 1..75){
  $directory="reports/pirates-moon/startup-r1/lifts-r$n"
  $arguments+=@('--lift',$directory,(Get-FileHash "$directory/report.json").Hash.ToLower())
}
python -B tools/pirates-moon/generate.py @arguments
./tools/pirates-moon/build.ps1 -Generated $generated
```

Inspect active process identities first and defer if another game session or
long job is running. Preserve the controls composer/watcher and all other asset
writers. Keep generated game code/media local; do not commit without instruction.

## Exact inputs and architecture

The [PM profile](../games/mw3-pirates-moon/config/target.json) and
[input manifest](../games/mw3-pirates-moon/config/supported-binaries.json) identify
the supplied executable, MSVCRT, MFC42, MSVCP60 and Mech3Msg. The executable's
SHA-256 is `57cd2ee74bafda3eeb9e9353c7c78a8b7c213a81f3040f1be7c2a164c505ddd9`.
Full installation/patch provenance remains unresolved.

MSVCRT is byte-identical to the staged MW3 CRT and reuses its native attach
machinery. PM's MFC42 and MSVCP60 are separate exact inputs, not substitutions
of MW3's MFC42/MSVCP50. Game addresses and generated dispatch are separate.
The optional host build profile preserves MW3's default constants and entry.

The experimental `Runtime::from_research_image` factory verifies its exact
input hash and creates a distinct `research_game` domain. Research translations
still require source/code/artifact bindings; neither that domain nor PM host
execution acquires MW3 accepted-game registration or milestone credit.

## Recovered static path

REA with Ghidra 12.1.4 analyzed the exact PM executable. All following addresses
are VAs; these are static observations, not execution claims:

| Boundary | Recovered PM location |
| --- | --- |
| Retail CRT entry | `0x5CEFE8` |
| CRT control-word setup | `0x5CF18C`, `_controlfp(0x10000, 0x30000)` |
| Initializer import thunk | `0x5CF186` |
| First initializer interval | `[0x6022A8, 0x6022AC)` |
| Main initializer interval | `[0x602000, 0x6022A4)` |
| Main initializer return | `0x5CF0B2` |
| WinMain wrapper | `0x5D0EC0`, calls imported `AfxWinMain` |
| Menu construction candidate | `0x488C40` |
| Menu resource call | `0x488F6A` references `MAINMENU`; calls `0x5BEF50` with `dialog.zrd` |
| Archive opening candidate | `0x5BEF50` calls `0x578630`, then `0x5BEFA0` |

Entry evidence: `ev_bbfa8ed4f3b6c34fa8c01dceeeb7ed2696db849b8f76c85c29732bdec99d38c6`.
WinMain wrapper: `ev_f2e195f67fb5ec967b083ae0e4aeec4f84ee7687ccae5ac9f799a7b8625bcf0c`.
Complete private evidence is retained in
`reports/pirates-moon-startup-r1/rea-evidence-r2.json`. The Ghidra session was
closed after export. No additional Ghidra installation is needed.

## Native pipeline and validation

[PM tools](../tools/pirates-moon/README.md) adapt the existing recursive scanner,
Remill semantics, FP lowering and LLVM compiler. The initial startup closure
contains 2,442 static entries; recursion splits create additional native entries.
Reports, source spans, LLVM, objects and dispatch stay under ignored
`reports/pirates-moon/`. No generated game code is added to the repository.
The driver executes native CRT/dependency attachment before retail game entry.
It uses host-built initial state, without original BEFORE or AFTER packs.

The launcher provides fresh local root files, asset-directory junctions, and
separate PM logs/configuration. Address-specific MW3 GPU-HUD and SEH test hooks
are refused for PM until separately recovered. The ordinary renderer/input
service path remains shared.

Checks performed:

- 27 existing binary-tool tests and 13 authored PM identity/isolation/asset/scan controls pass.
- Shared runtime contract tests pass, including research-domain and wrong-code identity rejection.
- Separate MW3 regression build: all 400 scripted menu/Training draw-log lines
  are byte-identical to the existing native executable, as are all 41 saved
  frames. Both terminate at the requested budget, not normal shutdown.
- First PM native run executes shared CRT initialization and FDIV at its actual
  `_cinit` call, then refuses MFC42's unresolved indirect callback `0x5F40FA41`.
  Its recovered closure adds ten native entries to the existing PM coverage.
- The next native run reaches MFC42's real initializer loop and stops at
  callback `0x5F40895B`. LLVM inspection of call `0x5F40FC9E` identifies its
  initializer interval `[0x5F4D25A4, 0x5F4D26A4)`. MSVCP60's initialization
  call at `0x780C10EE` uses `[0x7811B008, 0x7811B054)`. These intervals are
  retained in the target profile and their literal callback closures are lifted.
- Subsequent runs resolve virtual callbacks `0x5F4097F5` and `0x5F409825`, then
  expose a concrete attach-stack contract difference: PM MFC42's store at
  `0x5F40F9EC` writes its result to `[entry ESP+8]`. MSVCP60 has the same store
  at `0x780C1028`. PM now permits this one argument DWORD during attach;
  the outer return word and other argument slots remain protected. MW3 keeps
  its previous write boundary.
- With that correction, run `play-20261015-101756-539` completes native MFC42
  attachment (933 translated bodies, 318 services) and MSVCP60 attachment
  (1,013 bodies, 352 services), binds 12 PM data imports and executes its
  retail CRT entry. It stops after 269 game-stage bodies at indirect callback
  `0x4F5F00`, with zero frames. This advances dependency startup -> PM game
  initialization; it is not menu acceptance.
- After recovering UI callbacks from observed object tables, run
  `play-20261015-102413-181` executes 2,250 game-stage bodies and 341 services,
  then reaches `LoadLibraryA` of PM's exact `Mech3Msg.dll`. Its entry
  `0x10001A3B` and sole export `ZLocGetID` at `0x10001690` are translated in
  supplemental PM reports. The local initializer interval is
  `[0x10003000, 0x10003004)`, recovered from its CRT call at `0x100019E9`.
- Run `play-20261015-102610-978` reaches PM graphics-version detection after
  2,660 game-stage bodies. The required dynamic `DirectDrawCreateEx` call at
  `0x5A1718` requests IID `15e65ec0-3b9c-11d2-b92f-00609797ea5b`
  (`IDirectDraw7`), then releases the interface at `0x5A172B`. The adapter now
  calls the identified system provider and proxies its actual HRESULT/object;
  other DD7 methods remain explicit unsupported boundaries. This does not
  establish DD7 rendering, multitexturing or light-map support.
- The following source path enumerates the executable's RT_VERSION names
  (`0x4B2F8C`, callback `0x4B2F60`), deliberately stops after the first name,
  and loads that neutral-language resource with `FindResourceExA`. Enumeration
  now uses a Win32 data-only mapping and translated stdcall callback; no x86
  executable code runs in the host. The real callback-stop result is retained.
- PM then copies the raw resource into its own allocation and queries `"\\"`
  at `0x4B3043`. This differs from MW3's `GetFileVersionInfoA` path. Its raw
  resource is 968 bytes; Windows `VerQueryValueA` returns a 52-byte fixed-info
  value at offset 40. The adapter validates this raw root's length/key/signature
  inside a live allocation before calling Windows. ANSI subkey queries without
  their conversion workspace remain unsupported. Authored Windows-oracle and
  five malformed-resource controls pass alongside the runtime tests.
- Run `play-20261015-105517-390` confirms actual service results: the DD7
  creation probe returns `S_OK`, resource enumeration returns false after its
  callback intentionally stops, `FindResourceExA` returns a resource, the raw
  root query succeeds, and `RegFlushKey` returns `ERROR_SUCCESS`. Registry
  flushing is limited to the owned local overlay file and uses Windows
  `FlushFileBuffers`; it does not flush the machine registry.
- Application-vtable callbacks lead into MFC application initialization. Run
  `play-20261015-105756-084` executes 5,378 translated bodies and 929 services,
  stopping at the required `COMCTL32!InitCommonControlsEx`, still with zero
  frames. The adapter validates its two-DWORD record and delegates the exact
  class mask to the system common-controls provider; unavailable providers
  remain visible failures. Callback `0x5F409AA7` is retained as an additional
  startup root after observing it at MFC's indirect call.
- The common-controls calls succeed. The following dialog template at
  `0xB0FC80` is the original request for the PM CD, not a live menu. The local
  installation records identify a derived data ISO with SHA-256
  `9962fb0c04472fecb45543f31c3b38f8ee0c387d4fd58520ce6c3088184faf20`,
  mounted read-only as `H:` (`MW3 PM`) alongside the existing base CD `F:`.
  Original BIN/CUE remain local; this data-only image has no audio track.
- LLVM inspection of `0x5967C0` shows why both mounted CDs still hit that dialog:
  the original code opens the first matching file before validating its
  contents. A temporary user-level alias `B:` of the actual PM CD lets that
  original check pass. Run `play-20261015-110524-486` then stops at callback
  `0x409A80`, through the object table at `0x5F0228`. No file contents, drive
  type or API return were substituted. The launcher now provides `-MediaDrive`
  to manage that alias across a run and clean it up afterward.
- After the shared service additions, a fresh MW3 regression again matches
  all 400 draw-log lines and 41 saved frames exactly. Evidence is in
  `reports/pirates-moon-startup-r1/mw3-regression-summary-r2.json`.
- With additional `InitInstance` coverage, `play-20261015-111119-302`
  executes 28,268 bodies and 9,765 services before the application's virtual
  callback `0x482650`. That callback constructs a window object through
  `0x485620`; its store at `0x485654` assigns vtable `0x5E6C6C`.
  Run `play-20261015-111247-305` observes that table on the actual object at
  `0x50013430` during MFC's call at `0x5F40C1D8`, stopping at callback
  `0x5CEC50`. The profile retains the bounded 65-pointer candidate prefix
  `[0x5E6C6C, 0x5E6D70)` for incremental translation. This advances game
  initialization into native window-object construction, still with zero frames.
- Real USER32 window creation delivers `WM_GETMINMAXINFO` in
  `play-20261015-111716-716`. Its MFC message-map traversal requires the PM
  getter `0x485AA0`, then base getter `0x5B22F0` in the subsequent run.
  `0x485AB0` returns map `0x5E6630` (64 six-DWORD entries at `0x5E6638`,
  empty terminator at `0x5E6C38`). Its base map at `0x5F1950` has nine
  entries at `0x5F1958`, followed by an empty record at `0x5F1A30`.
  These map bounds are retained in the profile; initializer scans validate
  the entry pointer/terminator and recover the actual callback DWORDs.
- Window setup reaches MFC's `CTempMenu` runtime-class creation callback
  `0x5F405308`; its descriptor callback slot `[0x5F49CB94, 0x5F49CB98)`
  and seven-entry vtable `[0x5F49CBB0, 0x5F49CBCC)` are retained separately.
- Run `play-20261015-112644-173` enumerates the Vulkan HAL, then reports that
  software-render files were not installed. The earlier deployment records
  confirm that the installation was copied from verified media without running
  the installer or creating its registry keys. PM `0x4824D0` resets hardware
  selection unless `InstallOptions & 0xFF` is nonzero. Code `0x43B3F0` pairs
  mask `0x4` with the eight-megabyte hardware texture option.
- The launcher now verifies all five supplied banks for that component against
  [pinned asset metadata](../games/mw3-pirates-moon/config/native-assets.json)
  before using project-authored local registry settings: `InstallOptions=4`,
  `HWCardFlag=1`, `HWCardDev=0` under PM's own `MicroProse\\MechWarrior 3 EP1\\1.0`
  keys. These are pre-launch component/user configuration, not guest-memory
  patches or captured AFTER state; no machine registry changes occur. Empty,
  mutated and escaping asset inventories are rejected by authored tests.
- With that configuration, `play-20261015-113202-424` stays on the hardware
  path and executes 32,836 bodies/10,884 services before an uncompiled MFC
  handler `0x5F40F339` during activation (`0x36E` nested within `WM_ACTIVATE`).
- PM's IAT cell `0x5DE374` imports MFC ordinal 4242, the actual CWnd message
  map at `0x5F4A1EC8`. Its 46 entries occupy `[0x5F4A1ED0, 0x5F4A2320)`;
  its base getter `0x5F402430` returns the 27-entry map recorded above.
  The `0x36E` callback is `0x5F40F339`, distinct from its base's handler.
- Renderer startup calls `ExtEscape` at `0x5A2725`: `QUERYESCSUPPORT`, a
  four-byte integer `0xC03`, and no output buffer. The adapter supports that
  bounded query shape and returns the real Windows result. The observed result
  is zero (unsupported); PM handles it and continues, rather than receiving a
  fabricated driver-capability success.
- `play-20261015-114257-073` presents the first 640x480 frame, a black startup
  clear, then stops at resource helper `0x530C00`. It is not a live menu.
  The next run reaches DirectSound initialization at `0x591E92` after 145,802
  bodies, using a 36-byte guest `DSBUFFERDESC`. Its source zeroes all nine
  DWORDs, sets size 36 and flags `0xC1`; the appended 3D-algorithm GUID is null.
  The shared adapter now copies that GUID to the native structure and preserves
  `dwReserved`, retaining actual DirectSound HRESULTs and buffer ownership.
- Windows returns `S_OK` for that primary sound buffer in
  `play-20261015-114520-977`. The following native runs advance into PM's
  sound/resource initialization; `0x593D80` and `0x593C00` are subsequent
  missing direct helpers, not substituted service results.
- The visible path additionally creates MFC temporary objects during
  `WM_ERASEBKGND`. Runtime-class descriptors identify factories for `CTempWnd`
  (`0x5F40467B`), `CTempDC` (`0x5F405C53`), `CTempGdiObject`
  (`0x5F405F83`), `CTempMenu` and `CTempImageList` (`0x5F477F5B`).
  These callbacks are explicit profile roots; they were absent from the earlier
  recursive function graph and are compiled separately.
- `play-20261015-115545-453`, using the independent visible-check build,
  presents one startup clear through the **actual Vulkan swapchain on AMD
  Radeon RX 9070**, then stops at its one-frame budget. This confirms native
  PM startup -> visible Vulkan presentation, not a menu, input or quit pass.
- The final shared-service MW3 comparison uses identical frozen registry input
  in separate per-run overlays. All 400 draw-log lines and 41 saved frames match
  between the existing native executable and the updated host. Evidence:
  `reports/pirates-moon-startup-r1/mw3-regression-summary-r5.json` (including
  executable and registry-input hashes). The preceding r3 comparison against
  older captures differed after the shared live registry file changed; retain
  that failed comparison. The controlled r5 pair also includes the latest
  invalid-sentinel `FindClose` behavior; all 400 draw lines and 41 frames match.
- After the larger direct initialization pass, UI traversal observes table
  `[0x5DF4BC, 0x5DF580)` on a live object, then child table `0x5E2820`.
  PM's own common method slots (2=`0x4055C0`, 4=`0x4055E0`, 5=`0x4055F0`)
  identify 266 static UI-family candidate prefixes in `.rdata`, capped at the
  observed 49 slots. Slot 3 has only 21 distinct targets, including reached
  layout methods `0x40FFD0` and `0x43B950`; these are explicit profile roots.
  Candidate evidence is private `ui-family-candidates-r1.json`, not execution
  or whole-program completeness evidence.
- Bounded closure scans now record a maximum depth and visit the shortest call
  path first. Authored diamond/cycle controls ensure a longer route cannot hide
  a target reachable within the requested depth. Actual UI layout scanning
  closes 39 candidate functions without scanning unrelated deep descendants.
- `play-20261015-121150-117` reaches real `WM_PAINT`. Its paint-DC setup needs
  `0x5F405B45`, which records the attribute handle at `[ECX+8]`. The observed
  DC callback prefix `[0x5F49D380, 0x5F49D3FC)` contains 31 entries and is
  retained in the profile for native compilation.
- PM unconditionally closes `INVALID_HANDLE_VALUE` after an empty file search
  at `0x40E089`. The adapter now calls Windows for the recognized invalid/null
  sentinels and preserves failure/last-error behavior; arbitrary unowned live
  handles still stop. `find-services-r1.log` records the actual false results.
- Native execution then completes initialization and enters startup-state
  callback `0x484FA0` through table `0x5E6380`. Its opening-movie branch tests
  PM's original flag at `0x62CC55`, which the recovered `-nofmv` parser clears.
  The launcher's opt-in `-NoFmv` passes that original argument through the
  retail CRT. Subsequent menu validation selects it; cinematics get no credit.
- `play-20261015-122539-289` reaches main-menu-state initializer `0x489380`
  through table `0x5E6FE8`. That source calls constructor `0x488C40` directly,
  confirming the earlier static menu candidate in the live path. The next run
  reaches widget setup callback `0x5BBF50` (slot 8, table `0x5F1D9C`).
- Later runs execute PM's menu audio/resource helpers `0x595BE0` and
  `0x595EA0`, then shared widget resource loader `0x5BB940`. The observed
  derived menu-widget table occupies `[0x5E6F4C, 0x5E6FE8)` (39 slots),
  including loader `0x4891D0`; its separate base table occupies
  `[0x5E6F28, 0x5E6F4C)` (nine slots). These checked prefixes are retained
  as translation roots. `play-20261015-124422-433` executes 543,881 bodies
  and 230,004 services before missing callback `0x5BEE10`, reached from
  `0x4891A6`. It has still presented only the startup clear.
- The bounded UI-family pass closes 2,760 static entries and adds 2,029 native
  entries without translation failures. It is candidate coverage, not proof
  every widget executed. The next live fault identifies display-resolution
  lookup `0x598C90`, called from `0x4AF240`; its small closure adds seven entries.
- `play-20261015-130249-754` presents **120 live PM main-menu frames through
  the actual Vulkan swapchain on AMD Radeon RX 9070**. Captured frame 30 shows
  the PM menu labels, textures and animation rather than the startup clear.
  The run stops at its 120-frame budget, not normal quit. The isolated dispatch
  then has 8,519 source/artifact-verified native entries.
- `play-20261015-130324-848` replays the original-validated input sequence
  at 50 ms/frame and dispatches the Options-state initializer at frame 73.
  It stops at missing callback `0x4399F0`, return `0x5B16D2`, on an object
  with table `0x5E1F60`. Its checked 11-entry prefix ends at `0x5E1F8C`.
- Subsequent state/dialog translations render Options at frame 90, return to
  the menu by frame 150 and accept the quit prompt after frame 210. The main
  menu state's additional slot at `0x5E7010` calls `0x489850`, which forwards
  to application quit handling. Quit and retained-dialog destruction, shutdown
  initializer `0x484F70`, resource teardown, MFC ordinal 674 and its base
  window callbacks execute natively in later runs. The observed MFC base
  window table has 48 contiguous code slots at `[0x5F49B8AC, 0x5F49B96C)`;
  following data is not a callback table.
- The original and native scene-fingerprint prefixes match for all 180 checked
  frames before quit. Captured frames 30/60/90/150 have mean absolute RGB
  channel differences below 0.60 on the 0..255 scale. They are not claimed
  pixel-identical. At this point native shutdown still stops visibly on missing
  global/CRT callbacks, rather than treating a forced exit as success.

## Original reference and remaining work

An original-side visual reference now exists at
`reports/pirates-moon-startup-r1/original-menu-r1/frame-0060.ppm`: the actual
PM main menu, captured with the existing comparison hook adapted to PM in a
separate local experiment. `tools/pirates-moon/prepare_original.py` verifies
the same exact inputs and prepares the comparison copy. It changes only CRT
import-name strings to use the supplied 1998 CRT under `MSVCRZ.dll`, retains
derivation hashes, copies writable configuration, and reuses local dgVoodoo.
The original instructions remain intact. The hook uses PM entry `0x5CEFE8`
and recovered `RDTSC` sites `0x5B9CD2`, `0x5B9D01`, `0x5B9E8E`; raw matches
inside call operands at `0x42E8FD` and `0x4AB7B3` are excluded. The run captures
frames 30/60/90/120 and exits through its comparison frame-budget hook. That
is neither native-game credit nor normal-quit evidence. The complete paired
sequence is recorded separately above.

The original reference also validates the project-authored input sequence
`tools/pirates-moon/input-menu-options-quit.txt`, at 50 ms/frame: Options is
visible at frame 90, Escape returns to the main menu by frame 150, another
Escape opens the quit confirmation, and a mouse click on OK exits with code
zero after frame 210, before the 300-frame comparison budget. Evidence is
`reports/pirates-moon-startup-r1/original-options-quit-r2/`. Enter did not
accept that confirmation in the preceding r1 trial; that budget-stopped trial
is retained. Native replay now passes the same route; unscripted device-input
operation has not been manually checked.

The next agent starts from a verified native menu/Options/quit slice, not a CRT
bootstrap. First check unscripted mouse/keyboard operation. A subsequent PM
mission slice should follow an actual PM entry such as Instant Action; the PM
menu has no base-MW3 Training item. Recover required callbacks/services at the
first actual fault and validate against the corresponding original route.
Do not infer mission functionality from these menu results.

PM's translated reader now loads the menu resources. Further archive/mission
coverage remains open; do not change the authored version-1 asset adapter unless
the live execution path requires it. The extra footer DWORD, cinematic route, mission formats,
world-texture exceptions and multitexture lighting remain unresolved. Preserve
the initial comparison's bounded findings and all failed translations.

One statically reached CRT path (`0x78002E10`) fails translation because it
contains I/O-port writes. It is retained as a failure, not implemented as a
successful service or interpreter fallback.
