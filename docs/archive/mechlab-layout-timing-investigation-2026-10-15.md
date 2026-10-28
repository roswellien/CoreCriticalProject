# Mech Lab layout and frame-rate investigation

The user confirms the observed failure is broken layout. Equipment editing and
dragging have not yet been tested. The separate report of an inherent engine
limit above30 FPS is hearsay without an identified mod or threshold.

This is investigation only. No native implementation, frame cap, launcher
setting, pilot/save, campaign flag or original media was changed. No game was
launched. The current default remains1600 scenery units with fog. Acceptance
remains131/144; no execution boundary was advanced by this source review.

## Identities and evidence

Freshly checked original `MW3/Mech3.exe` SHA256:
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Current native build SHA256:
`e95305b22aba43e44e6cb8663405d7580f1be6ec894938f2b54ba1628b1a23cd`.

Original pseudocode is retained locally in
`local/hud-mechlab-investigation-r1/mechlab/original-contract-evidence.json`
(Ghidra12.1.4, `facts` array). The original loop evidence is
`ev_e08854c36d9b7be75c5a01ef3e5b05381b635fda0dc95d4c12f07c63afa128df`;
preview draw evidence is
`ev_10c7ceefbb18e5a57c97463a3204a75f3587e2056e442a0b024a6032d28fe5bc`.
The preview arithmetic was independently checked against the original bytes
using the existing LLVM21.1.8 `llvm-objdump`, VA00450710..00450775.
An independent read-only review checked timing and input consumers against the
retained source evidence and disassembly. No new REA session was needed.

## Findings

| Question | Finding | Evidence boundary |
| --- | --- | --- |
| Does the preview advance by a fixed angle every frame? | No. It advances by0.8 times elapsed seconds in radians. Expected revolution time is approximately7.85 seconds. | Static original arithmetic, not a new live Lab measurement. |
| Does the UI receive elapsed time? | Yes. Lab loop passes the engine delta to the UI root update. | Exact leaf control handlers, drag and repeat behavior remain unresolved. |
| Is the layout mismatch caused by FPS? | The identified rectangle/composition mismatch has no timing input. | Current presentation source confirms incompatible mappings; the user's live Lab branch still needs capture. |
| Is a universal30 FPS ceiling established? | No. Neither the inspected Lab preview nor the original loop establishes one. | This does not establish all Lab actions or all gameplay safe at every rate. |

Lab loop00448A80 forwards engine delta0072C52C to UI00448F10 at
00448B27..00448B2F and preview00450690 at00448B34..00448B3D.
00448F54..00448F57 forwards delta into the UI root's virtual update.
0045072D..0045073B implements `angle = angle - dt * -0.8`; the following
branch subtracts2pi after crossing pi, then0045076B applies the orientation.

Lab polls input withCL=0 at00448A9E..00448AA4. The generic held-key callback
and mouse-callback dispatch paths are gated off in this mode. They should not
be blamed for Lab repeat bugs without tracing the actual UI leaf handlers.
Absolute pointer processing0051B4F0 uses ScreenToClient and configured logical
dimensions; it has no delta-time multiplier. This is a coordinate-domain risk
when the displayed canvas and physical client differ, not proof of an active
input failure in the user's screen.

The original engine clock00575A00 derives the shared delta from GetTickCount.
The current native host's `mfc_stage.hpp:244` documents and implements a shared
QPC-derived, session-relative millisecond clock for GetTickCount/timeGetTime
and input/message stamps. It avoids coarse host ticks and loss of float timing
precision after long Windows uptime. Existing Training20/40/80 game-step checks
are recorded in `tools/m4-crt-heap-carry/README.md`; those checks do not cover Lab.
They must not be promoted to a universal high-FPS validation claim.

The third-party [ZipperFixup changelog](https://github.com/TerranMechworks/ZipperFixup/blob/main/CHANGELOG.md)
also identifies coarse GetTickCount accuracy and long uptime as timing problems.
It does not establish a Mech Lab-specific limit. An explicit
[mod-author warning about Mech Lab above30 FPS](https://www.reddit.com/r/mechwarrior/comments/1wxzifb/my_mechwarrior_3_4_alloneone_launcher_installer/)
names MW4. That report is not evidence of the same defect in MW3. The historical
mod/mechanism the user heard about remains unidentified.

## Layout repair to evaluate

The earlier [Lab investigation](hud-mechlab-investigation-2026-10-15.md)
identified the original preview rectangle210,52..430,288, with separate
`labworld`, `labwindow` and `labcam`. Current host source still contains the
same mismatch: raster blits use original coordinates, unidentified preview
geometry receives a center adjustment, resident targets are forced to3440x1440,
and CPU versus resident presentation fit different canvases. Readback can
include a prior adjustment before the final frontend fit.

The proposed first repair is one shared original4:3 frontend canvas. At3440x1440
it occupies1920x1440 centered atx760. Controls, preview, clipping and hit testing
must agree on that mapping through draw, readback and present. Apply its inverse
to absolute input only if that input branch is actually active. Preserve raw
relative input and original equipment/inventory rules. Restore combat rendering
state on exit. No redesigned full-width Lab is proposed in this first repair.

## Required live checks

First enter Lab through its genuine enabled postmission campaign action.
The initial reloaded1/1 campaign map disables Lab by design and is not an
equivalent reproduction. The retained route is Win/Continue -> original loader
state6 -> campaign action2 -> modal Lab. Do not patch flags or jump directly
into the Lab to substitute for this transition.

Use the same real-time gestures at measured30/60/120 FPS and with no application
cap, at both4:3 and ultrawide:

1. Capture initial control and preview rectangles before interaction.
2. Measure rotation angle against wall time and accumulated engine delta.
3. Trace actual control identities, pointer coordinates and repeat intervals
   during drag, scroll and held buttons.
4. Check armor, weapons/ammo edits, confirm/cancel and configuration persistence
   into the next mission; also exercise entry/exit repeatedly.

Keep elapsed interaction duration identical across rates. Equal frame counts
with a fixed virtual clock do not test real frame-rate sensitivity. The current
Vulkan swapchain uses FIFO, so no application cap can still be limited by the
display's refresh rate; record achieved presentation rates. A diagnostic pacing
change, if needed, belongs in an isolated host, with the production profile kept
intact until the actual defect and repair are verified.

No blanket30 FPS cap or timing rewrite is justified by the current evidence.

Follow-up: the authorized layout repair and subsequent authentic Instant Action
Lab coverage are recorded in [Mech Lab canvas repair](mechlab-canvas-repair-2026-10-15.md).
The exact postmission campaign chain and real-time FPS matrix above remain open.
