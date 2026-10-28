# MW5-style controls investigation

Recorded 2026-10-18. User requested investigation of modernizing MW3 controls
to use an MW5-style scheme. Read-only source/configuration research plus this
document; no game launch, binding changes, profile edits or native build.
The user subsequently selected both MW5 Traditional and FPS controls for this
investigation. Mercenaries is the working reference; keyboard/mouse is the
initial scope. Both are proposed selectable modes alongside original MW3 controls.

## Findings

An optional MW5-style input preset fits the
[faithful modernization strategy](../faithful-modernization-plan.md). Preserve MW3's
simulation, acceleration, turning limits, torso limits, weapons and mission logic;
translate player intent through its recovered input/action contracts.

MW5 has multiple schemes. Mercenaries' traditional controls and its FPS mode
must be treated separately. PGI's [March 2023 patch notes](https://mw5mercs.com/news/2023/03/80-march-9th-patch-notes)
describe FPS mode as controlling the torso while the legs rotate to catch up.
Automatic leg following therefore needs behavior work beyond key remapping.
This source describes a dated release, not a measurement of the installed build.
Clans controls have not been investigated here.

The local saved Mercenaries settings at
`%LOCALAPPDATA%/MW5Mercs/Saved/Config/WindowsNoEditor/GameUserSettings.ini`
provide a concrete candidate reference: `bFirstPersonControlMode=False`,
`EnableThrottleDecay=False`, `EnableArmLock=False`, X/Y inversion false and
mouse X/Y sensitivity 1.0. These are saved settings, not proof of the user's
desired preset, current factory defaults, or live observed behavior. Numeric
sensitivity cannot simply be copied between engines.

## Candidate bindings from the local MW5 keyboard/mouse map

| Intent | Saved MW5 binding | MW3 investigation/implementation requirement |
| --- | --- | --- |
| Increase/decrease throttle | W / S | Recover held/released/reverse semantics of MW3 forward/reverse actions before mapping. |
| Turn legs | A / D | Map to original turning actions; retain original turn rates. |
| Aim | Mouse X / Y | Saved MW5 axis mappings; compare MW3 twist/pitch, inversion and sensitivity. |
| Stop | X | Bind original stop action if confirmed; resolve conflict with MW3's current third-person X binding. |
| Center torso / legs | C / F | Recover and distinguish both MW3 actions; do not assume they are interchangeable. |
| Fire groups 1 / 2 | Left / right mouse, also 1 / 2 | Confirm MW3 direct-group firing versus group selection plus fire. |
| Fire groups 3 / 4 | Mouse side buttons, also 3 / 4 | Additional physical-button capture/mapping likely needed; verify MW3 group model. |
| Fire groups 5 / 6 | 5 / 6 | MW5 action count does not establish corresponding MW3 group support. |
| Jump jets | Space | Map to recovered original jets action; verify hold/release. |
| Hostile near crosshair / next hostile | R / T | Verify equivalent MW3 targeting semantics; nearest and crosshair-nearest may differ. |
| Zoom | Middle mouse / wheel | Cycle versus increase/decrease require separate semantic checks. |
| Camera | V | Map original view action and resolve old binding conflicts. |
| Power / override | P / O | Verify original toggle semantics. |
| Freelook | Left Ctrl | MW3 readme excludes standalone modifiers from its ordinary remapping UI. |

MW5-only actions such as its specific interaction, equipment, sprint or lance
interface must not be invented in MW3 merely to fill a preset. Preserve access
to MW3-specific actions such as its own lance/MFB commands and targeting modes.

## Current native input boundary

The native host already uses real Windows DirectInput. Both
[`mfc_stage.hpp`](../../tools/m4-crt-heap-carry/mfc_stage.hpp) and the remaster
[`override`](../../tools/remaster-launcher/native-overrides/mfc_stage.hpp) implement
device creation, data formats, acquisition, immediate `GetDeviceState`, buffered
`GetDeviceData`, properties and guest/host data conversion. Scripted input also
feeds both keyboard consumption paths. The remaster's physical-input branch
currently forwards provider data without an MW5 action preset.

Follow-up: the launcher-selected host-source snapshot additionally calls
`photo_replay_filter_device_state` and `photo_replay_filter_device_data` before
guest delivery. These consume input during photo/replay/free-camera operation
and suppress reserved hotkeys. The unpatched override above is not the complete
deployed input path; see the source investigation below.

[`runtime/input/README.md`](../../runtime/input/README.md) reserves a reusable input
backend; its statement that no backend exists refers to that directory and must
not be read as absence of functional input in the experimental native host.

The locally supplied MW3 1.2 `readme.txt`, sections "Game Control
Configurations" and "Gameplay", documents remappable keyboard/buttons and
forward/reverse throttle, turn, twist and pitch axes. It documents three mouse
buttons and excludes standalone Shift/Ctrl/Alt keys from ordinary key remapping.
It recommends Torso Auto Return off for mouse use. These establish existing
facilities/limits, not the exact action IDs, profile layout or executed semantics.
Keep original media local; no original readme content is copied into the repo.

## Selected modes and FPS feasibility

| Mode | Proposed behavior | Evidence still needed |
| --- | --- | --- |
| Original MW3 | Existing bindings and original input behavior | Baseline for each affected action. |
| MW5 Traditional | MW5-style bindings, independently aimed torso and manually steered legs; saved local non-decaying throttle as the initial reference | Original MW3 action IDs, throttle/reverse behavior, centering and weapon-group equivalence. |
| MW5 FPS-style | Shared combat bindings plus mouse-led torso aim and assisted leg alignment; investigate hold-to-move behavior | Observe MW5 W/S release, A/D and diagonals, reverse and stationary turns, freelook, centering, and how movement direction interacts with torso aim. |

Only torso aim with legs catching up is established by the cited PGI description.
Exact FPS movement semantics must be observed before calling the result a match.
In particular, A/D must not be assumed to mean the same thing in both modes, and
MW5 FPS must not be reduced to traditional controls with throttle decay enabled.

A feasible MW3 FPS-style adapter would maintain player movement intent and
request original throttle/steering actions at simulation input updates. Automatic
alignment needs recovered leg/torso headings, angle-wrap handling, original turn
limits and a measured tolerance to prevent oscillation. Device forwarding alone
does not provide that game state. Identify a justified game-action integration
point before implementing feedback; do not write guessed orientation fields.
Define manual-steering, freelook and centering precedence explicitly, and clear
assistance on pause, focus loss, mission exit and preset changes.

If exact MW5 movement requires motion unavailable through MW3's original actions,
record that limitation and offer the bounded FPS-style adaptation for review.
Do not silently add lateral movement or bypass the original movement simulation.

## Suggested implementation sequence

1. Investigate both selected schemes. Use the existing local traditional
   Mercenaries configuration as a reference and measure FPS behavior separately
   in an isolated settings/profile setup, preserving the user's saved settings.
2. Inspect the original controls screen/action table and saved bindings using a
   separate test pilot/profile. Record current bindings and mouse behavior before
   edits. Identify the active native build's input-source provenance; the launcher
   selects a registered executable, so changing a header alone changes no gameplay.
3. Implement an optional preset for movement, aiming, centering, firing and
   targeting, using existing MW3 actions where equivalent. Prefer original
   remapping where sufficient; use host input adaptation for proven UI/device
   limits. Avoid fixed scan-code substitutions that assume an unchanged pilot map.
4. Keep menu/text input working. Any adapter must reconcile immediate and buffered
   reads, modifiers, held keys, focus loss, release, acquisition errors and device
   identity. Do not identify a device solely by its buffer size or report fake API
   success. Reset adapter-owned held state on focus/profile transitions.
5. Persist the selected preset through the actual launcher/profile path.
   `play_remaster.py` clears inherited `MW34_*` environment variables, while
   `play_native.ps1` loads registered runtime settings. A shell-only switch is
   insufficient for a user-facing setting. Keep the original-compatible option.

6. Add the selected FPS-style mode after the shared bindings/traditional baseline,
   with separately validated movement assistance and explicit mode selection.

Investigate hold-to-move/throttle decay and automatic leg following as distinct
parts of the FPS work. Prove that automatic leg following can issue
ordinary steering commands within MW3's turn/torso limits. Instant yaw changes,
new lateral velocity or copied MW5 acceleration would require separate gameplay
decisions and must not be implied by an input preset.

## Narrow validation and execution boundary

First compare equivalent original/new input sequences at matched simulation
times: starting/stopping, reverse, simultaneous turn/aim, torso limits, centering,
jets, group firing and targeting. Exercise pause/menu/text entry, focus loss while
holding fire/throttle, re-entry and return to original bindings. Check that one
physical action is not delivered twice through buffered/immediate paths and that
release does not leave movement or fire held. Test at different presentation
rates without changing simulation cadence. Use the existing scripted input path
for repeatable cases, followed by physical-input checks in Training.

For FPS assistance, also check torso/leg disagreement, angle wrap, stationary and
reverse movement, A/D with W/S, released movement keys, turn-limit saturation and
manual override. Switching modes while an input is held must neither latch fire
or throttle nor carry an old assistance target into the new mode. Compare outcomes
at matched simulation times across presentation rates to detect frame-driven
steering. These are proposed checks, not completed native validation.

This investigation advances no executable boundary. The proposed first slice
advances physical input -> optional preset -> original MW3 input/actions -> native
Training. It does not claim MW5-equivalent feel, validated gameplay or formal
acceptance. Strict accepted roots remain **131/144**. No active SQLite was opened,
no composer/watcher was modified and no long job was started. Existing unrelated
working-tree changes were preserved. The AGENTS-listed Codex-named work review
and continuation files are absent; the existing Claude-named counterparts were read.

## Follow-up: recovered original commands and configuration path

Read-only REA/Ghidra 12.1.4 analysis of local MW3 retail 1.2 executable SHA256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
All addresses below are **VAs**, image base `0x400000`; subtract the base for RVAs.
Analysis is static, not proof of an executed control or gameplay equivalence.
Raw tool evidence and the complete recovered registration list remain local at
`local/controls-investigation-2026-10-18-r1/static-evidence.json`.

### Command registration: answered

`sub_00411150` registers commands through `sub_004110D0`. Instruction inspection
recovers action IDs passed in ECX, which the decompiler's inferred signature
omits. `sub_004110D0` maintains metadata with a 0x14-byte stride and a command-name
lookup. These are original action IDs, not Windows keys or invented aliases.

| Original action | Registered ID | Proposed use |
| --- | --- | --- |
| `CMD_THROTTLE_UP` / `CMD_THROTTLE_DN` | `0x18` / `0x19` | Traditional W/S |
| `CMD_TURN_LEFT` / `CMD_TURN_RIGHT` | `0x02` / `0x03` | Traditional A/D; candidate original steering for assistance |
| `CMD_TWIST_LEFT` / `CMD_TWIST_RIGHT` | `0x08` / `0x09` | Original torso motion |
| `CMD_PITCH_UP` / `CMD_PITCH_DN` | `0x04` / `0x05` | Original vertical aiming |
| `CMD_CENTER_TORSO` / `CMD_CENTER_LEGS` | `0x06` / `0x07` | C/F candidates |
| `CMD_JJ_UP` | `0x0C` | Space candidate |
| `CMD_TRIGGER1` | `0x3D` | Original firing trigger |
| `CMD_WEPGRP_1` through `CMD_WEPGRP_5` | `0x2C` through `0x30` | Five registered group commands; firing versus selection still untraced |
| `CMD_TARGET_CURSOR` / `CMD_TARGET_NEXT_E` | `0x48` / `0x46` | Candidates for crosshair/next targeting; filtering semantics still untraced |
| `CMD_FREELOOK` | `0x17` | Freelook candidate |
| `CMD_CYCLE_CAM` | `0x61` | V candidate |
| `CMD_RETICULE_ZOOM` / `CMD_ZOOM_LOCK` | `0x14` / `0x15` | Zoom candidates; not assumed equivalent to MW5 zoom steps |
| `CMD_SHUTDOWN` / `CMD_SHUT_OVER` | `0x3F` / `0x40` | P/O candidates |

The same routine registers default Up/Down arrows for throttle and X for camera,
consistent with previous native Training observations. Defaults are not the
currently loaded pilot's binding map. No sixth group registration was found in
this routine; that is a bounded result, not proof that all gameplay storage is
limited to five. Direct MW5-style group firing needs explicit investigation of
selection, trigger ordering and simultaneous group presses.

Evidence: registration pseudocode
`ev_32b3ecdabc4de105c2c1272ac842ee0765e6b07d4c88ad7965dbf9d02787f223`,
assembly `ev_922ee03c40999b3e1d5efc244235efaee3546419d89d28557206058fe37a4b2c`,
metadata helper `ev_e003b74c1c7d38b7e562891d12324ec73a68edf6334dc7a1225c76a7687b581d`.

### Original named preset support: partially answered

`sub_0042D0B0` constructs `keys\<name>.zrd`, then invokes the existing load or
save path. `sub_00411E60` writes a text preset with `KEYS` and `AXES` sections,
command names, two keyboard slots, joystick/mouse-button slots, and axis
slope/intercept/deadzone properties. `sub_004120A0` reads named commands and axes
and applies bindings through `sub_0051D2C0`. The underlying keyboard binding
setter `sub_0051BFE0` clears conflicting reverse mappings before installing a
binding, so binding conflicts must be resolved as a complete preset.

This supports investigating an original-format Traditional preset before adding
host key emulation. No `keys` directory exists in the inspected MW3 installation,
and the checked `reader.zbd` directory contains no key preset entry. Startup
registers defaults; current persisted bindings/default resolution remain to be
traced. The existing pilot is a binary record and was not edited or assumed to
be a standalone binding preset. Preserve the loaded settings and use a separate
test configuration before exercising save/load.

Evidence: save `ev_54b4c75dea4167dc0651478cca511f6d59e2194eefc4dd8ccb7bb88a5203a10c`,
load `ev_ab80a3c61f6c8f22ef6d14d55bed86d12270016fd33564721e59782979f6b8fe`,
path `ev_49f0f9683eb2b539fa87cd40e4e601672994dfc60d5bc5c10889a78f9bb56e12`.

### Constant throttle and automatic alignment: partially answered

The `ThrottleConst` setting resolves to `sub_0040D020`. It updates settings bit
`0x20` and, when a player actor exists, writes an inverse boolean at offset
`0x3F` of the object reached through actor offset `0x37C`. Its getter
`sub_0040D060` reads that bit. Thus MW3 already has a connected constant-throttle
option; the observed code does not yet establish release, braking or reverse
semantics. Trace that object's consumer before implementing throttle decay.

Separate torso and leg centering commands make original leg alignment a concrete
candidate for FPS assistance. Neither the centering consumer nor heading/turn-rate
contract has been recovered here. Repeated centering, direct heading writes and
frame-driven steering are not approved substitutes for those missing contracts.
Ghidra also reports `0x41092D` (a relevant input-metadata cross-reference) outside
an analyzed procedure; no guessed function identity or decompilation is claimed.

Evidence: constant-throttle setter
`ev_9c334e888c18ba5e0cc9050439d5d1f1cd0308a7d2e651cf11730f9ff4767812`,
getter `ev_cb3ea15ea67861a0289440b29a93140a5fcd6fbb6fef7966a6b99fde6e8cc99a`.

### Actual native input integration: answered within the inspected source

The launcher-selected executable currently hashes to
`42672b409ad502c1ab3baee7a4e43e4756e7752ba59b394e88863a111a675190`.
Its adjacent `host-source/mfc_stage.hpp` calls photo-mode filters at both physical
input paths. The source snapshot's older recorded executable hash differs from
the current binary: this pass identifies current files but does not certify a
reproducible source-to-binary build.

[`photo_replay_stage.inc`](../../tools/remaster-launcher/native-overrides/photo_replay_stage.inc)
consumes gameplay input while detached/frozen, suppresses F9-F12 and briefly Esc,
and drains keyboard events on transitions. Any new preset must cooperate with
these rules and preserve MW3-specific commands currently using reserved keys.
The scripted branch precedes physical filters, so tests must explicitly exercise
the new mapping rather than assuming an existing script tests physical remapping.

### Updated MW5 reference and next concrete work

The saved Mercenaries configuration has separate `StrafeForward/Backward/Left/Right`
W/S/A/D bindings in addition to traditional throttle/turn actions. This confirms
distinct mappings, not physical lateral movement. PGI's
[January 2023 announcement](https://mw5mercs.com/news/2023/01/76-free-game-update-details)
introduces the FPS scheme; the [official manual](https://static.mw5mercs.com/docs/MW5Mercs_Game%20Manual.pdf)
documents traditional controls. Later [June 2026 fixes](https://mw5mercs.com/news/2026/06/191-chaos-reign-patch-1)
address FPS torso/arm locking and controller reverse behavior, so the installed
MW5 version must be recorded for eventual behavior comparisons.

Next work is now specific: recover the active binding-map/default path and
centering/throttle/group consumers; produce an isolated original-format
Traditional preset; then validate it in native Training. FPS work follows the
same actions with measured movement assistance. Exact FPS A/D, diagonals,
release/reverse, stationary rotation and freelook behavior remain unobserved.
No live control validation, executable change or acceptance credit was added.

## Second follow-up: consumers and an isolated Traditional candidate

Continued static analysis with REA/Ghidra 12.1.4 and the existing local LLVM
21.1.8 disassembler, against the same original executable identity. New evidence
is retained under ignored `local/controls-investigation-2026-10-18-r2/`:
`consumer-evidence.json`, bounded `command-dispatch-llvm.txt`, the candidate
`mw5-traditional-keyboard-candidate.zrd`, its layout JSON and README. Nothing was
installed or launched. The pilot hash remained
`ab7b065513091aeeeb529e311b9659bf072cdf226629f1bffa0be6b48572e690`.

### Throttle consumer: substantially answered statically

`sub_0046B0A0` polls action `0x18`/`0x19` through `sub_0051D300`, applies signed
0.025 keyboard throttle increments, and uses the constant-throttle/decay byte
at offset `0x3F`. With no throttle input, decay enabled and no persistent throttle
shortcut, a separate branch reduces stored throttle, snapping small magnitudes
below 0.05 to zero. The factor uses legacy floating-point bit construction and
the update interval; no exact decay curve or MW5-equivalence is asserted here.
The related `sub_00427D60` has a corresponding path. These are original simulation
input updates, not permission to drive increments from presentation frames.

`sub_004274D0` supplies the important shortcut semantics:

| Registered action | Actual handler effect |
| --- | --- |
| `CMD_THROTTLE1` (`0x1B`) | Sets throttle to zero; this is the stop command. |
| `CMD_THROTTLE2` through `CMD_THROTTLE9` | Signed 0.2 through 0.9, respecting reverse state. |
| `CMD_THROTTLE0` (`0x24`) | Signed full throttle, 1.0; it is not stop. |
| `CMD_THROTTLE_REV` (`0x1A`) | Negates nonzero throttle; at zero toggles reverse state. |

Therefore X must map to `CMD_THROTTLE1`, while 0 can retain full throttle.
The original numeric labels must not be interpreted as a zero-to-100% API.
The isolated candidate was corrected using these consumer findings before use.

Evidence: `ev_299aff42ef4d12c9415eb02d2821769e3e5d3c5211272e32f0877551ad3d1e4c`
and `ev_0a69ab93a35bbfe53b713aa14b04dac6000d5163851899617bf1c9c817ed2b7c`.

### Weapon groups: selection versus firing answered statically

The original two-stage action dispatcher includes a byte-indexed case table at
VA `0x41C8D4` and a target table at `0x41C7D0`. Reading these tables and checking
the corresponding instructions maps actions `0x2C` through `0x30` to `0x41C44C`.
That block clamps the requested index to 0..4 and calls `sub_004B0730`, which
checks group content, stores the selected index and updates the player interface.
It does not itself issue the firing trigger. `sub_00467480` separately polls
held action `0x3D` (`CMD_TRIGGER1`) through `sub_0051D300`.

Thus a named binding preset can provide 1–5 group selection plus left-button fire.
MW5-style independent mouse-button group firing would need an additional adapter
with defined selection/trigger ordering and simultaneous-group behavior; no sixth
group or new weapon simulation is implied. This distinction is now a traced
consumer result rather than an inference from command names.

Evidence: `ev_265cd7d7a1da82df57ea61331fd980c46c27982005ad22b4f956febdc3cffb7f`
and the retained original jump-table bytes/instruction ranges.

### Centering: a real FPS integration candidate, with a cancellation constraint

The same tables map torso action 6 to VA `0x41C55A` and leg action 7 to
`0x41C548`. Both call `sub_00465A00` on the actor's offset-`0x39C` component,
with modes 1 and 2 respectively. The setter records the mode at offset `0x1B0`.
`sub_00464E80` consumes it: mode 2 checks current steering and relative torso yaw,
temporarily supplies a steering value through the actor's movement component,
and invokes the original rotation update with the simulation interval.

This establishes a path for original leg alignment without directly overwriting
orientation. It also reveals why a repeated synthetic F key is insufficient:
manual aim inputs clear the centering mode, and manual steering can cancel it.
FPS control must define simultaneous aim/turn behavior around these existing
rules. Turn rates, signs, heading wrap, completion and damage limits still need
matched live checks. The aiming helper `sub_00465BC0` clamps pitch/yaw to original
limits, but this alone does not validate continuous automatic leg following.

Evidence: setter `ev_45ae5b81714458f066de9c58b63c79f6775484174b4fb4253fe527325c99afdc`,
update `ev_70dc88412ba2d17687210872161538c3554e33e9b5dd6695215682c4190e6ae1`.

### Prepared Traditional candidate and remaining boundary

The uninstalled candidate maps W/S throttle, A/D turning, C/F centering, Space
jets, X stop, P/O power/override, R/T cursor/next-enemy targeting and V camera.
Keys 1–5 select groups. It retains original left-button firing and right-button
freelook; it does not claim MW5 right/side-button direct firing, Ctrl freelook or
wheel zoom. Displaced MW3-specific commands have explicit replacement keys,
including alternatives for host-reserved F9–F12. The companion README lists them.

Independent checks found all 105 recovered command names exactly once and 109
unique nonzero keyboard codes, with X bound to confirmed stop and 0 to full
throttle. Original mouse/joystick bindings are retained; AXES is omitted so loading
this KEYS section preserves the current axes. This relies on the existing mouse
axis setup and does not set sensitivity, inversion, throttle mode or torso return.
Raw candidate SHA256 is
`b954436b1f3131a5fb5c40e3f4e988a34cbeb6a67b69a7a9e6092a7c0ba306dd`.

These checks establish an authored candidate, not acceptance by the game's
parser or playable controls. The existing assets CLI only parses packaged binary
documents; it cannot supply a text-preset game load/save roundtrip. Next is an
isolated game settings/profile load/save and native Training check, followed by
physical input and aim/centering comparisons. The candidate is not installed in
`MW3/keys`, and the standard launcher/executable remain unchanged.

No executable boundary advanced. Static investigation now reaches original
action registration -> binding -> throttle/group/centering consumers; the next
execution boundary is loading this isolated preset and exercising native Training.
Strict accepted roots remain **131/144**; no commit or acceptance run was made.

## Third follow-up: actual native preset load/save and Training test

The user authorized proceeding with the isolated test. The existing registered
x64 native host (SHA256 `42672b409ad502c1ab3baee7a4e43e4756e7752ba59b394e88863a111a675190`)
ran against a private copy of the executable, message resources, archives,
configs and pilot under `local/controls-investigation-2026-10-18-r3/game`.
No assets or writable pilot files were hard-linked. Each run selected a private
registry overlay via the existing `MW34_REG_OVERLAY` service. The candidate
overlay selected `keys\MW5Traditional.zrd` through `ActiveCtlCfg`; this was ordinary
configuration input, not injected guest state. The copied game had no intro video;
these tests do not retest intro playback. Original pilot, overlay and normal
launcher profile hashes were unchanged after all completed runs.

### Native load and persisted mapping: passed

`candidate-quit-r2` loaded the candidate, reached the live menu, clicked Quit and
the actual OK confirmation, and completed normal native shutdown with
`ExitProcess(0)` and `DLL_PROCESS_DETACH` for MSVCP50/MFC42/MSVCRT, after126frames.
The original save path persisted a map matching **105/105 candidate commands**;
no command mismatches. Only `DefaultCmdMap` changed relative to the private
initial overlay. The packed record was independently recovered from original
VAs `0x51BEB0` and `0x51BF00/20/40/60`:167little-endian32-bit words indexed by
command ID, with keya11bits, keyb11bits, joystick4bits and mouse2bits.

This proves native text-preset import and normal settings persistence. It is not
an original text-preset export/reimport test, and the button map does not contain
axis state. Evidence: `candidate-quit-r2/binding-comparison.json`, `exit.json` and
`stderr.txt` in the ignored r3 directory.

### Matched native Training: passed within the sampled scope

Compared `training-baseline-r2` (original bindings) with `training-candidate-r1`
(new bindings), with matching command timelines and virtual-clock50ms input tests.
The sequence covers startup, right turn, acceleration, stop and torso/leg-center
commands. Candidate physical scan codes were P/D/W/X/C/F. The original torso
shortcut required separate Shift press/release events, not a combined mapping
code sent as a physical key. The copied pilot was stable across the compared runs.

Both runs reached900presentations and were deliberately stopped by the frame
budget. Exit1 with the explicit presentation-budget diagnostic is expected for
these bounded runs; neither is normal mission completion. Of10sampledframes,
the three menu/early samples are byte-identical. The seven gameplay samples differ
only within observed control-hint text bounds (`x404..580`, `y700..766` across
samples). Screenshots show the original F12 objectives hint changing to SCROLL.
Every other pixel in the rendered scene and HUD matches at those samples. The
comparison retains exact full-image hashes and difference bounding boxes; it does
not relabel full-frame differences as full-frame equality.

Evidence: `training-comparison.json` and both run directories under ignored r3.
This is scripted native execution through the game's input/actions, not recorded
scene replay, physical-input validation or whole-game fidelity. It adds no strict
acceptance credit. The accepted roots remain **131/144**.

### Manual test entry point and remaining work

`local/controls-investigation-2026-10-18-r3/Play Traditional Controls Test.cmd`
opens the private test copy with real input, a fresh private overlay, no scripted
input and no virtual clock. It refuses concurrent game sessions. It was prepared
but not launched interactively. The standard game launcher and controls remain
unchanged. Full relocated bindings and limitations are in the r2/r3 READMEs.

Retained attempts include the initial menu observation, the Quit/Y attempt that
did not confirm, and a first Training baseline with incorrect modifier sequencing;
the latter is excluded from the matched comparison. A separate graphics test was
observed by process identity and left intact; candidate execution waited until
it exited. A later dedicated mouse-aim run was refused while another graphics
test was active. After that test exited, `aim-baseline-r1` and `aim-candidate-r1`
ran but stayed at the main menu through900frames. They are explicitly excluded
from gameplay evidence: pixel-identical menu samples do not prove aim/centering.
The navigation/timed-mouse interaction needs diagnosis or a direct-input check;
no runtime cause has been established. Their scripts, frames and failed scope
are retained in `aim-comparison.json` and the run directories.

Next checks are real mouse/keyboard feel, mouse-axis aiming followed by centering,
focus loss/reacquisition, weapon-group firing ergonomics and extended play. FPS
assistance remains a separate implementation task using the recovered original
centering/throttle contracts. The boundary advanced here is isolated preset file
-> native load -> original command mapping -> live Training -> saved settings.

## Controller direction selected by the user

On2026-10-18 the user requested Xbox and PlayStation controllers on Windows,
with possible future Linux support. This expands the controls target beyond
the keyboard preset; it does not mark controller support implemented or authorize
a claim that the current Windows host runs natively on Linux.

Initial hardware targets are Xbox One/Series gamepads, DualShock4 and DualSense.
Test USB and Bluetooth separately where supported by the device/OS. Older models,
third-party variants and proprietary wireless adapters require explicit coverage;
family recognition alone is not a passed hardware test. The same Traditional and
FPS-style action profiles should work across families, with appropriate button
labels and user overrides. Windows is the first integration/test host; retain a
portable controller/action layer for a future Linux port.

### Proposed portable backend

Use SDL3's gamepad subsystem for device discovery, normalized sticks/triggers,
buttons, mappings and hotplug events, behind a small project-owned input boundary.
SDL documents [Windows/Linux support and its zlib license](https://wiki.libsdl.org/SDL3/FrontPage),
a [normalized gamepad API](https://wiki.libsdl.org/SDL3/CategoryGamepad),
[PS4](https://wiki.libsdl.org/SDL3/SDL_HINT_JOYSTICK_HIDAPI_PS4) and
[PS5](https://wiki.libsdl.org/SDL3/SDL_HINT_JOYSTICK_HIDAPI_PS5) HIDAPI drivers, and
[device-specific button labels](https://wiki.libsdl.org/SDL3/SDL_GetGamepadButtonLabel).
These establish available library facilities, not compatibility of this game.

Dependency candidate for implementation review: SDL **3.4.18**, upstream commit
[`829a65d769d935c4852f8159e964312c0957260a`](https://github.com/libsdl-org/SDL/commit/829a65d769d935c4852f8159e964312c0957260a),
zlib license; [stable release](https://github.com/libsdl-org/SDL/releases/tag/release-3.4.18).
No package was downloaded, installed or linked. Pin and hash the actual source
archive/binary when acquired; artifact SHA256 is pending artifact selection.
The current DirectInput bridge exposes legacy device data but lacks a portable
gamepad mapping/hotplug layer. Windows-only XInput cannot provide the whole
Windows/Linux and native PlayStation target. SDL is proposed for input only;
this does not replace the existing window, graphics, audio or Vulkan integration.

The proposed flow is device -> normalized pad state -> deadzone/response settings
-> Traditional/FPS intent -> recovered MW3 actions and axes at simulation input
updates. Keep platform handles in host-owned state. Preserve original movement,
aim limits, action order and cadence. Device button numbers must not become
game-action IDs, and stick movement must not bypass the original simulation.

### Required controller behavior

- Remapping, stick deadzones, response/sensitivity, inversion and separate trigger
  values; device-independent profiles with optional per-device calibration.
- Xbox/PlayStation labels, explicit label override when a virtual controller
  obscures the physical device, and matching confirm/back prompts in menus.
- Menu, briefing and Mech Lab navigation as well as combat. Enough bindings or a
  command layer to retain access to MW3-specific actions on a limited button set.
- Connect/disconnect/reconnect and focus loss release owned input; define neutral
  throttle and pause behavior explicitly so a disconnected pad cannot leave an
  adapter-owned fire/throttle command held.
- One input owner per physical/virtual controller. Avoid delivering the same pad
  through SDL and legacy DirectInput simultaneously, and test Steam Input/remapper
  configurations for duplicate commands. Native USB/Bluetooth operation should
  not require a keyboard-emulation utility as the implementation strategy.
- Capability-detected optional rumble. Gyro, touchpad and adaptive triggers remain
  separate enhancements, not requirements for ordinary movement and firing.

Verify each controller family/transport on Windows before claiming support. Keep
the portable state/action transformation testable without Windows APIs. A later
Linux pass must check actual device permissions/drivers, hotplug, packaging and
event ownership alongside the separate native host port. Sharing SDL input code
does not establish Linux game execution or feature parity.

Next implementation slice is an input-only SDL discovery/state prototype with
actual Xbox and PlayStation device tests, then one bounded native Traditional
gamepad path using recovered throttle/turn/twist/pitch contracts. FPS assistance
builds on that shared path after its independent movement semantics are validated.
No controller backend or executable boundary was added by this requirements note.
