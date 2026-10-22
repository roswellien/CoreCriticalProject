# M4 application and retail menu workahead

Current use, 2026-10-11: this static map is an E0 input for the
[faithful modernization plan](faithful-modernization-plan.md). Reuse its source
paths and unresolved edges to choose the next actual execution blocker. The
dated prerequisite ordering below is not a requirement to reproduce every CRT
implementation before an equivalent application bootstrap can be investigated.
Required initialization effects and original-compatible contracts remain mandatory.

This preparation turns existing exact static records into implementation batches while the CRT argument/filename work continues. It does not run the original game, a provider or native application code. The inventory keeps source receipt identities, JSON pointers, call frontiers and exact original instruction/table bytes; it adds no native application credit.

The admitted game is `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. The staged MFC42 candidate is `5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8`; staged MSVCRT is `2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7`. Actual Windows MFC provider selection remains unobserved. The source records distinguish staged and SysWOW64 ordinal targets, so a staged static contract cannot silently stand in for a different runtime provider.

## Conditional source path

The application initializer slot `5E010C→47F760` reaches constructor `47F7A0`, which installs application vtable `5C3F80` on object `608C88`. The staged ordinal561 constructor stores that receiver in MFC module-state+4. After CRT completion, WinMain wrapper `5AE390` reaches ordinal1576 through `5AE3F4/IAT5BB438`; the staged provider retrieves the same object and conditionally calls application slots+8C,+58,+5C,+70. These are exact static links, with runtime context, helper effects and receiver lifetimes still open.

The initialization candidate `480000` loads detail.zrd directly or through the reader.zbd fallback before it dispatches app+BC to `47FF90→482D10`, stores the frame at app+20, and connects frame+C0 back to the app. Resource147 passes through `LoadMenuA` and `SetMenu`. Application services `480570` later remove that menu and initialize graphics/input/audio/data services. A bounded first window cut can stop at the next unsupported service with carried state; it cannot fabricate a completed initialization return. The retail frontend additionally requires the custom state/widget path and the complete service/run/message loop.

The run candidate `58FD70` dispatches queued startup object `608F58` using table `5C40C8` to `482070/482170`. Intro completion or the actual command-line-controlled branch queues factory12, which reads app+1DC. The default constructor setting is state `608F00`, table `5C5030`, callbacks `486990/486D40`; other command-line selections and later field/table mutations remain conditional. `486990→486260` constructs the composite and loads `dialog.zrd/MAINMENU`. Parse failure can still return from the constructor, so allocation/return alone is insufficient. `486D40→48ED30` needs valid child-widget/render/input receivers. Seven exact named control/vtable+30 targets are recorded for Instant Action, New Campaign, Multiplayer, Training, Options, Credits and Quit.

## Work batches

The machine inventory records roots, original call sites, per-batch unresolved frontiers, preparation priority, unknowns, next deliverables and integration gates for each batch. Dependencies describe implementation prerequisites; actual call order remains in the conditional source path. Runtime loops are marked separately and are not turned into a false acyclic execution graph. First prioritize MFC provider-state contracts and the reader ABI; localization/config, widget properties and required backend contracts can follow in parallel. This ordering makes prerequisite work reviewable while CRT implementation proceeds.

| Batch | Concrete next work | Integration prerequisite |
| --- | --- | --- |
| `provider-state` | Narrow MFC module/TLS/FS/SEH helper and typed object/callback lifetime contracts | Needed before application constructors and provider callbacks |
| `localization-config` | Mech3Msg/ZLocGetID, registry RunDir, working-directory/version/error contracts | Needed by constructor/init paths |
| `application-initializers` | Actual slots5E00E4→47F470,5E00E8→47F4B0,5E010C→47F760 and their object constructors | CRT environment/callback dispatch plus the two service batches |
| `other-initializers` / `main-table-complete` | Complete all required roots in original order, without skipping required constructors | Application slots and remaining CRT/dependency closure |
| `window-frame` | MFC dispatch, actual frame allocation, USER32 handles/resources and creation callbacks; stop truthfully at later unsupported service | Full main table, provider state, localization/config and reader ABI |
| `archive-reader` | Guest archive registry/cursor/read/allocation ABI and detail.zrd fallback | Can prepare now; required before frame construction |
| `widget-properties` | Inherited typed-property loaders, section ownership and named widget receivers | Can prepare now; integrates after reader ABI |
| `video` | Stored callback table, DirectDraw/COM/surface/presentation lifetime and failure contracts | Can prepare now; required before services/menu presentation |
| `input-audio` | Keyboard/mouse/focus and conditional DirectSound/MCI/CD/menu sound contracts | Can prepare now; required services retain their real branch conditions |
| `service-callback` | App+AC services, state queue/type3 dispatch and startup transition | Window, data and required backends |
| `retail-menu` | MAINMENU construction/update/render, directed input and clean quit | Real startup transition, widget ABI and required backends |

`crt-environment` is the separately owned current CRT work. The accepted mainargs composition stops at the real GetModuleFileNameA import before it executes; it has not produced filename/argv/environment or returned from the argument function. The selected27/144 initializer gate is reusable bounded native evidence, while full actual main-table composition remains open. The existing initializer inventory reports the three application/state roots as non-import-free, with50/66/848 unique reachable instruction counts and3/3/46 import sites; the application root also has FS instructions and unresolved control sites. Their known vtables are preparation evidence, not implementation readiness.

Provider-state, localization/config, reader/widget ABI, video, and input/audio contract preparation can run independently. Their implementation gates still respect dependencies; widget implementation needs reader objects. Window and later integration work must consume completed service contracts and owned carried state. This preparation does not select new providers, change configuration, inject `-nofmv`, or relax a success/failure contract.

## Reusable evidence and remaining uncertainty

The accepted host reader/tree parser agrees on178 archive entries and14925 tokens, including MAINMENU. Reuse that host data prerequisite; guest HANDLE/cursor/allocation behavior, root+128/12C ownership, widget+84/+88 callbacks, font/bitmap/primitive receivers and x87 conversions still require contracts and execution proof. The bounded graph records also contain deferred dependencies; the selected projection is not full transitive closure.

For later reference instrumentation, prioritize the exact provider/module-state receiver, app/frame backlinks and lifetimes; archive registry/cursor/read results; MAINMENU parse/setup and each actual widget target; stored graphics callback/COM objects; input/audio statuses and cleanup; and queue/timing/command-line state selection. Such original/native observations remain future work. The current deliverable performs only static source/identity checks.

## Artifacts and deterministic checks

- Inventory: `reports/m4-application-workahead/preparation-r4/inventory.json`.
- Checker receipt and pins: `reports/m4-application-workahead/check-r1/`.
- New scripts: `tools/m4-application-workahead/prepare.py` and `check.py`.

The checker physically rehashes source receipts and admitted images, validates each selected body/call projection through its frozen JSON pointer, rereads original instruction bytes and table words, rejects dropped call frontiers, computes marked CFG/direct-call cycles, and checks the deterministic prerequisite order. In-memory corruption controls exercise wrong identity/entry/call/slot/pointer, dropped frontier/failure branch, unmarked loops, dependency cycles and invented native/menu credit. This is consistency validation of an actionable static plan, not a new execution equivalence proof.

```powershell
C:/Python314/python.exe tools/m4-application-workahead/check.py --inventory reports/m4-application-workahead/preparation-r4/inventory.json --controls
```

The earliest defensible native window cut completes CRT environment, required initializers, provider state, the pre-frame reader ABI and app/frame contracts. Retail menu completion adds the genuine service/state transition, inherited widget ABI and required presentation/input/audio paths. Full message-pump/focus/normal shutdown proof belongs to that later integrated path. The exact smallest complete call closure remains unknown until these dependencies and dynamic receivers are admitted; no function count or calendar completion estimate is inferred from this inventory.
