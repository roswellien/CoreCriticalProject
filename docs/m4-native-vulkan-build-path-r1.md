# Native M4 build path with Vulkan — investigation r1

Date: 2026-10-10

Strategy update, 2026-10-11: the [faithful modernization plan](faithful-modernization-plan.md)
now governs integration. Reuse this investigation's boundaries and presenter
work, but audit a complete application path rather than making every legacy CRT
implementation a mandatory first step. Recompiled producers and equivalent
platform services must still supply all required observable initialization.

## Current state

The project has two proven but separate native components:

1. `tools/vulkan-windowed/` builds an x64 Win32 application that creates a
   Vulkan swapchain, resizes/minimizes/restores safely, and presents a saved
   Training draw capture. The accepted checks and limits are in
   `docs/vulkan-windowed-replay.md`. It does not run MW3 startup or live game
   rendering.
2. `tools/m4-startup/` maps the admitted PE32 `Mech3.exe` into owned 32-bit
   guest memory from an x64 process. `tools/m4-runtime/` adds a guest CPU/stack,
   translation and service registries, and calls admitted native x64 entries.
   The current host deliberately refuses the actual entry: CRT/SEH, imports,
   initializer routing, and MFC startup are not complete. See
   `tools/m4-startup/main.cpp`, `tools/m4-runtime/runtime.hpp`, and
   `tools/m4-runtime/runtime.cpp`.

The common executable boundary therefore does not exist yet. The current
`runtime/CMakeLists.txt` library contains only `GuestMemory`; the M4-specific
execution runtime lives separately under `tools/m4-runtime/`. Neither is
linked to the Vulkan viewer. There is no PE import resolver, general x86
interpreter, complete CRT startup, or DirectDraw-to-Vulkan bridge.

## Recommended architecture

Use the existing Vulkan presentation implementation as the backend foundation
and keep MW3-facing graphics semantics in a separate compatibility layer:

`translated game code → guest Win32/DirectDraw COM services → host surface state → Vulkan images/commands → Win32 swapchain`

The guest side must preserve 32-bit object, vtable, handle, and structure
layouts. Host pointers and Vulkan handles stay in host-owned registries. A
locked legacy surface should expose the recovered guest pixel format and pitch;
unlock/flip or the observed presentation callback then uploads/presents the
surface through Vulkan. Vulkan is the rendering backend; it is not a substitute
for recovering the game's DirectDraw/Direct3D call contracts.

## Shortest credible route to a game-derived frame

1. **Define the integration boundary.** Make the M4 x64 host the process entry
   point; reuse its admitted image, guest memory, `Runtime`, and translation
   registry. Reuse Vulkan device/window/swapchain code behind a small presenter
   API that accepts explicit surface pixels and format. Do not fork the saved
   scene replay as the game frontend.
2. **Prove a surface round trip.** Add synthetic tests for guest COM object and
   vtable layout, surface creation, lock/pitch, unlock, palette/format cases,
   Vulkan upload, resize, presentation, and destruction. Compare the bridge's
   Win32/COM results with the source contract from the parallel video analysis.
   This is backend readiness, not game startup credit.
3. **Connect a justified application startup path.** Audit retail translated
   entry versus an equivalent host bootstrap, accounting for required CRT/SEH/
   import, initializer and failure/cleanup effects. Connect the actual app/frame
   path, MFC object/provider state, localization and reader ABI. Preserve the
   144-root acceptance gate separately; prototypes may advance integration before
   its final receipt, but cannot fabricate completed initialization or skip effects.
4. **Reach the first game-owned frame.** Run the translated initialization and
   graphics callbacks until a real game-owned surface produces pixels in the
   Vulkan swapchain. Keep unsupported services as explicit stops; do not fake a
   successful initializer or synthesize menu readiness.
5. **Expand toward the menu.** Add scene intervals, widget rendering, input,
   timing, and shutdown only after the first game-derived frame is matched.

## First implementation target

The first useful integration deliverable is a **Vulkan presenter interface and
surface-upload fixture linked into a new x64 M4 host target**, with the existing
windowed replay left unchanged. It should render pixels supplied by an owned
host surface and pass Vulkan validation/readback checks. The follow-on deliverable
connects that surface to the recovered guest DirectDraw ABI. This is a bounded
vertical slice that tests the hardest integration seam without claiming it has
started the original game.

Do not start by wiring the 47 KB replay viewer directly to guest callbacks; it
currently owns capture parsing, draw replay, window events, GPU resources, and
presentation in one executable. Extracting a narrow presenter contract first
keeps replay and live runtime behavior testable independently.

## Gates and limits

- A Vulkan clear or synthetic surface fixture proves the native graphics host,
  not a MW3 native launch.
- A mapped PE32 image proves loader behavior, not execution of original x86.
- An admitted generated function proves only its bound function and route.
- A visible native window is not a menu. The first menu requires the real
  initializer/app/frame prefix plus archive, widget, graphics, and input
  services.
- The active 144-root acceptance and its verifier remain a separate gate; this
  investigation adds no initializer or game-startup credit.
