# Bounded MW3 live graphics trace

Call-through instrumentation for the admitted MW3 U.S. 1.2 executable. It does
not translate game logic or replace the renderer. The executable on disk remains
unchanged. The launcher reuses the existing admitted-image/pre-entry injection
implementation; it detaches its temporary startup debugger before gameplay.

The DLL replaces one process-local DirectDrawCreate import slot, then installs
per-object cloned vtables for IDirectDraw, IDirectDraw2/4, IDirect3D3 and
IDirect3DDevice3. SDK struct sizes and member offsets determine table sizes and
slots. Original arguments/results are forwarded through typed stdcall entries.
The clones retain all untouched method pointers, including AddRef/Release.
Clones remain allocated until process exit to avoid freeing a table while an
object or cached table address still uses it. There are at most 512 records.

Observations include QueryInterface, CreateDevice, BeginScene/EndScene and
DrawPrimitive/DrawIndexedPrimitive. Instrumentation preserves its incoming
FXSAVE state and last-error value around bookkeeping/logging. This guard is
tested; it is not a universal proof of live execution equivalence or timing.
Selftests use authored COM fixtures, are marked `live:false` and never count as
game observations. HRESULT failures and caller-owned vertex/index memory are
checked in the fixture tests. No work runs in DllMain.

Budgets: 1,024 log records; first 64 combined draw calls; first 64 combined scene
calls; at most three vertices/256 bytes per sample. Unrecognized vertex layouts
have stride zero and no sample. Only non-blended XYZ/XYZRHW, optional normal,
packed colors and up to eight default 2D texture-coordinate sets are decoded.
These samples are insufficient for frame replay: textures, complete vertices,
indices and render states are not captured. Logging and vtable indirection can
affect timing. This is a research session, not a performance setting.

## Build, test and launch

The current surface-command recovery work is described in
[live rendering work](../../docs/live-native-rendering-current-work.md).
Z-buffer surfaces are observed; selected flip intervals also retain bounded
surface API input/result diagnostics, including write locks and GDI access.
The observed D16 zero-depth fills and full-target RGB565 Lock/Unlock writes have
bounded ordered replay paths; unsupported operations still refuse capture.
Observer snapshot reads are excluded from game-operation observations.
`-BuildDirectory` selects a separate
build without replacing a DLL loaded by another session.

Requires Visual Studio Win32 C++ tools and Windows SDK legacy DirectX headers:

```powershell
./tools/graphics-trace/build.ps1
./tools/graphics-trace/build.ps1 -Launch
```

`-Launch` refuses an existing session. It creates fresh ignored receipts, runs
typed selftests, and launches only after they pass. Enter Training, move/fire
briefly and quit normally. Keep that user observation separate from event logs.
Do not overwrite old receipts. Exiting the game removes the instrumentation.
Do not unload the trace DLL while cloned tables remain reachable.

For passive exit/window-health monitoring of the printed game PID:

```powershell
./tools/game-monitor/start.ps1 -Mode attach -GamePid <PID>
```

Capture provider modules while the game is still running; `modules.json` records
names, full local paths, bases, mapped sizes and SHA-256 hashes. The first accepted
capture is documented in [the live record](../../docs/mw3-live-graphics-trace.md).
Then run:

```powershell
python tools/graphics-trace/verify.py reports/graphics-trace/<run> --stage draws
python tools/graphics-trace/check_controls.py reports/graphics-trace/<run> --output reports/graphics-trace/<run>/controls.json
```

The verifier rehashes admitted game/tool/source identities, checks monotonic
record sequence and selftest claims, validates the actual imported provider
against the module inventory, requires live interface/device results, and checks
bounded FVF/vertex samples independently. `--stage creation` accepts creation
evidence only; default `draws` additionally requires successful sampled live draws.
It does not certify Training, clean shutdown, full-frame correctness or arbitrary
interfaces. Keep all traces and vertex payloads under ignored reports.
Pass `--monitor reports/mw3-monitor/<session>` to additionally require a matching
passive monitor's completed zero exit, no alerts and no dropped segments.
