# Code and provenance review — October 21, 2026

**Decision: keep publication and downloads on hold.** The repository-wide
inventory and history scan are complete for the refs described below; the
file-by-file correctness/readability review remains open. Several release-facing
defects are reproduced. This is a review record, not a security clearance or
permission to distribute original or derived game content.

Reviewed checkout: `37bda63c42479f5ad5927b375b0b8244c8bd52f7`, including the
uncommitted working tree on October 21. Other graphics/asset work was present.
Per-file SHA-256 identities, disposable authored fixtures and detailed results
are retained locally in `reports/full-code-provenance-review-20261021/`.
Earlier history/syntax/build results are in `reports/publication-preflight-20261021/`.
Those ignored reports are not public release contents.

Line references below describe the source captured for this review, before the
subsequent local readability cleanup expanded formatting and comments. Use the
named classes/functions and retained source hashes when locating a finding in a
later working tree. Readability changes do not mark these functional findings fixed.

No production code was changed during this review. No generated command or
original game code was executed by the new probes. Directory-deletion probes
were confined to resolved, disposable review directories. Existing processes,
SQLite databases, frozen evidence and other writers were preserved. No commit,
push, release upload or visibility change was performed. The execution boundary
and strict acceptance count remain unchanged: **131/144**.

## Confirmed release-facing findings

P1 means address before exposing the affected import/run operation to users.
P2 means a concrete correctness, packaging or disclosure problem to resolve
before claiming the corresponding feature is ready. These are project review
priorities, not externally assigned vulnerability scores.

| ID | Priority | Finding and evidence | Required change / meaningful regression |
| --- | --- | --- | --- |
| C01 | P1 | `tools/mw3-remaster-launcher/Core/PackManager.cs:138`: a manifest ID can escape `mods/`; `InstallPack` recursively deletes that target before validating archive contents. Separately, entry paths at line 162 escape the pack directory. Both writes and deletion of an authored sibling marker were reproduced using the actual C# source. Startup refresh automatically attempts archives in `mods/`. | Validate IDs, archive root and every resolved destination before mutation; reject rooted/traversal/reparse paths; bound expansion; stage and atomically replace with rollback. Test malicious IDs and entries, malformed/truncated packs and preservation of an existing installation. Apply containment to uninstall too. |
| C02 | P1 | `games/mw3/mod-tools/editor/core/exporter.py:246`: project names enter a generated CMD `echo` as shell syntax. Names loaded from project JSON are not restricted. `ui/main_window.py:427` runs that CMD on F5. An authored name containing a command separator produced a second command in the file; it was not executed. The Studio builder's earlier ID checks do not cover this desktop exporter. | Keep display names out of shell programs; pass launch data through structured arguments/configuration. Test metacharacters, newlines, percent expansion and paths with spaces end to end. |
| C03 | P1 | `tools/mw3-remaster-launcher/Core/IsoInstaller.cs:22,59`: an ISO filename is interpolated into PowerShell source. A legal Windows filename containing an apostrophe and separator parsed as an extra command, with zero parse errors. The parser probe never mounted or executed anything. | Pass the filename as a script parameter rather than source; use literal paths. Test apostrophes and command metacharacters without mounting media. |
| C04 | P2 | `Core/GameValidator.cs:178–182`: any readable file named `Mech3.exe` is marked valid and described as verified; archive counting uses `*.zfs`. A non-PE authored text file with no game archives returned `IsValid=true` and a retail/custom verification message. This is not equivalent to the strict image admission elsewhere. | Separate discovery from verification; use supported executable identities/PE contracts and required original archive checks. Unknown versions must be visibly unsupported or unverified. Test wrong game, malformed PE, missing archives and supported identities. |
| C05 | P2 | `editor/core/exporter.py:150`: spawn export still reads `game_root.parent/local/mod-cache`, while the updated loader uses configured cache storage. An authored export fixture reproduced `FileNotFoundError` despite the configured cache being present. This dependency was missed in the earlier setup change. | Carry the exact loaded reader/cache source in mission data; do not reconstruct an obsolete workstation path. Test object and spawn exports using an external game folder and the extracted source package. |
| C06 | P2 | `editor/ui/main_window.py:318,332,341`: history callbacks and undo/redo record the selected object instead of the command's object. Reproduced with actual methods and authored objects: move A to X=10, select B, undo; A displays X=0 but its saved delta remains X=10. | Record the object changed by the command. Test move/rotate/enable, switch selection, undo/redo, save/reload and export. Existing command-only tests miss UI-to-project synchronization. |
| C07 | P2 | `Core/SteamHelper.cs:127,192`: every shortcut entry uses key `0`. Two actual writer calls against a disposable authored VDF produced two `0` entries. No real Steam profile was accessed; Steam's handling of those duplicates was not tested. | Parse the existing structure, allocate the next entry index, back up and atomically replace it. Test multiple existing shortcuts and malformed files; verify behavior in an isolated Steam profile before shipping. |
| C08 | P2 | `tools/mw3-remaster-launcher/mw3pack.py:71–76`: the manifest ID selects the default extraction directory without containment. An authored pack escaped its archive-parent directory. This is a destination-ID defect; Python's ZIP member sanitization is not the same as C01's manual C# extraction. | Apply the same validated pack identity and destination policy as the launcher. Reject traversal/rooted IDs before creating directories. |
| C09 | P2 | `mw3pack.py:53`: validation builds an unused allowed-directory set, but packaging walks every file. A validated authored pack silently included an unrelated note. Symlink files and output-inside-input also require explicit policy. | Define deliberate include rules and reject unsupported files/symlinks and self-inclusion; show or record package contents before publication. Test exclusion of unrelated files and containment. |
| C10 | P2 | `editor/core/map_pack.py:226–300`: fixed node pools are reused across all advertised operations; pools overlap, unknown types silently become bunkers, and exhausted/out-of-range pools drop entities. The manifest's `total_placed_assets` counts requested items rather than successful placements. The code was inspected; no claim of a full live-game reproduction is made. | Scope supported operation/archetype identities explicitly, allocate nodes globally, reject unsupported/overflow placements before output and report actual applied changes. Test overlapping pools, capacity, invalid indices and each supported operation with authored fixtures. |
| C11 | P2 | `Core/IsoInstaller.cs:78–148`: absent media is skipped, subdirectories under `zbd` are not copied, and completion still says the game is “100% standalone.” Mount/dismount exit status is not checked. Source review only; no ISO was mounted. | Define supported source layouts and required files, validate completion and surface subprocess errors. Test empty/incomplete and representative authored disc trees; avoid a standalone claim without a validated native setup. |
| C12 | P2 | `Core/GameRunner.cs:117`: enabled pack directories only affect the upgraded-model ID test. Generic texture/audio/HUD pack contents and ordering are not passed into native preparation. The UI's generated official manifests are availability stubs, not proof of installed payloads; an ID prefix is not trusted provenance. | Implement and validate supported pack composition or limit the UI to the choices actually connected. Test that changing a supported pack changes the prepared launch inputs, and missing payloads fail clearly. |
| C13 | P2 | `tools/analysis/disassemble.py:24,64`: the interface calls output private research but permits a disassembly file anywhere except over the input binary. Unlike `extract_mw3_leaf.py`, it does not require an ignored output root. | Enforce resolved private output roots for derived code, including reparse paths; test rejection of tracked/public destinations before running the external disassembler. |
| C14 | P2 | `editor/ui/main_window.py:228,361`: `_open_mission` catches loading errors without signaling failure; `_open_project` then assigns the new project and applies its edits to the previous mission. Actual methods with an authored failing loader reproduced an error followed by a success notice and modification of the previous mission's object. Saved base-file hashes are also not checked before applying deltas. | Load and validate the requested mission/project into temporary state, including source identity and schema, then replace current state only on success. Test failed loads preserving the old mission/project and mismatched base identities rejecting edits. |

These findings invalidate readiness claims for the **current** Mod Tools source
candidate's export/run paths. Its byte/hash checks and isolated setup/catalog
checks remain valid for what they tested. Keep that candidate unpublished;
rebuild only after the relevant fixes and export/run checks pass.

## Provenance and privacy disposition

| Material | Evidence and disposition |
| --- | --- |
| Remote-reachable Git history | Both fetched branch tips and the open PR merge were scanned: 5,235 distinct blobs, 58.17 MB. No custom credential-pattern matches or suspect executable/media/private-path candidates were found in that scope. Gitleaks 8.30.1 scanned 18 commits and reported 47 candidates; all were inspected as source-context false positives, including evidence hashes, allocator/assertion text and a C# property. Values were redacted; no suppression baseline was added. This is evidence of the scan, not proof that every possible secret is absent. |
| Local-only refs | The broader initial all-ref scan included Codex checkpoints and found shortcut/settings versions there. They were not in the scanned ordinary remote branch/PR history. Do not describe them as a confirmed GitHub disclosure or rewrite history on that basis. Never push a mirror/all local refs as a publication shortcut. |
| Game data and generated translations | No proprietary binary/media payload was identified by the scoped history inventory. Ignored local game installs, generated objects, dumps, translated bodies and derived enhancements are still excluded by policy. Their existence locally does not authorize redistribution. Check the final publication tree and every actual archive separately. |
| Original-code signatures/extracts | Literal byte signatures include 37–85 byte spans in research files, and a 41-byte original function in `tools/m4-spi-workarea-independent/model.py`. These need the necessity/rights review required by `docs/legal.md`. They are not automatically cleared because small or useful. Keep source pins/evidence intact while deciding their publication disposition, including history. Do not classify address tables or authored capture assembly as game bodies merely from their appearance. |
| Shaders | All 12 adjacent GLSL/header pairs were rebuilt into ignored outputs without running generators that overwrite tracked headers. Ten arrays match byte-for-byte. `model_scene_vert.h` and `world_scene_vert.h` each lack three `OpDecorate NoContraction` instructions emitted by the current source/compiler; the instruction multiset otherwise matches. The local compiler's SPIR-V enum identifies decoration 42. This is a reproducibility/precision question, not evidence of proprietary shader content. Record the intended source/compiler/options before regenerating or altering a validated host. |
| Compiler identity | The shader probe used glslang 16.6.0, generator 11, SHA-256 `c65441e754d18a76e70c76141bc9a96faa3b1ba6986e0d2c64a54468cb64932f`. Its local directory is named `glslang-main-windows`; a directory name alone is not a toolchain pin. Preserve the tested compiler identity in the eventual build recipe. |
| Fonts | All four launcher font hashes match the local website provenance record, and three OFL notices are present in the launcher tree. That provenance JSON is currently untracked and points at mutable upstream `main` URLs. `MW3RemasterLauncher.csproj:18` embeds fonts but does not copy their notices; Inno's separate recursive Assets rule does. Verify notices in each actual binary distribution, and retain the source/hash record in the intended publication tree. This is an output-packaging gap, not a finding that notices are missing from the source checkout. |
| Launcher artwork/icons | Six tracked plate PNGs lack embedded origin metadata; no complete tracked source/rights record was established. The icon generator refers to a website source image outside the tracked launcher inputs. Locate the author/generation/source records and document derivatives, or replace these files with material whose origin is established. Missing metadata alone does not prove copying or infringement. |
| Browser dependency | Three.js r128, OrbitControls and TransformControls have a version/source/hash record and MIT notice in the Mod Tools tree. Earlier package checks verified those exact hashes and included the notice. Keep these third-party files distinct from project-authored code; do not mass-reformat them. |
| Trailers/screenshots | Preserve the recorded YouTube origin and original unmodified captures. Gameplay imagery remains presentation material; it does not provide rights to package underlying game/model/audio assets. Keep that distinction in downloads and contributor guidance. |
| Hosted resources | The prior inventory found no tags, releases, stored Actions artifacts or LFS payloads. Remote services may change; repeat the inventory against the chosen publication revision. Git author identity and linked external pages also need the owner's disclosure review; a token scanner cannot decide that preference. |

## Coverage and limits

The working inventory contains **5,188 tracked files** plus **1,247 nonignored
untracked files**, including other ongoing work. The earlier tracked source
inventory counted 4,172 source/script/UI files and roughly 383,239 physical lines,
including third-party JavaScript and compiled shader arrays. Inventory, syntax
parsing and hash checks do **not** mean every line was manually reviewed.

| Scope | Review performed | Still required |
| --- | --- | --- |
| Launcher | All eight Core files read; application startup read; main-window integration inspected; actual-source probes for pack import, validator and shortcut writer; ISO source parsed without execution | Complete XAML/UI event review, settings/error lifetimes, pack composition and clean-machine setup |
| Desktop Mod Tools | Project/history/exporter and format boundary read; mission-loader, main-window, property-inspector and canvas paths inspected; export/cache/undo/failed-project-load probes use authored fixtures | Remaining UI/loader paths, schema/base-hash enforcement, all supported missions, full export round trips and actual game loading |
| Studio | Server/build boundaries read; substantial browser state/rendering/interaction code inspected | Remaining JS/history/load logic, request/read timeouts, resource disposal, generated-pack semantics and reproducible live output |
| Shared runtime | Guest address/memory and MFC receiver contracts read; DirectDraw creation adapter read; full local-CD audio service read | Hardware/error-path validation; DirectDraw adapter's standalone suite; all host service implementations are not yet cleared |
| Native runtime/loader | `tools/m4-runtime/runtime.hpp/.cpp`, `tools/m4-startup/image_loader.cpp` read; native launch preparation and entry configuration read; selected MFC service/dispatch sections inspected | The large MFC/graphics hosts and applicator chain need function-level review against current admitted inputs; no whole-host line-review claim |
| Graphics | Menu wave, material-normal, effect-lighting and sun-camera contracts read; all 12 shader pairs rebuilt | Renderer resource synchronization/ownership, geometry/HUD/lighting applicators and all remaining binary formats; explain the two shader differences |
| Analysis/lifting | PE parser and leaf extraction/disassembly paths read; pinned Remill build path inspected | Remaining analysis/lifting code, source patch provenance, dependency notices and local-generation setup |
| Historical research | Tracked Python syntax checked; signature/constant inventory and historical-role distinction recorded | Most dated M4/x87 scripts and fixtures have not received individual correctness/readability review |
| Release/onboarding | Explicit Mod Tools include list, pinned dependency/configuration/setup reviewed and tested in the earlier pass | Correct defects above, rebuild candidate, separate Game/Launcher package, actual release-content inspection and install/update/uninstall checks |

The earlier isolated asset-free MSVC build and all sixteen CTest groups passed
across the complete run and targeted asset-fixture repair rerun. Those checks
did not cover the newly reproduced pack/undo/export defects. Five of 3,282
tracked Python files fail syntax parsing; their exact paths are retained in
[release readiness](../public-release-readiness.md#code-review-coverage). Do not
silently edit pinned historical versions to make a global syntax count green.

The generic runtime routes unknown required translations/imports to explicit
faults, checks admitted bytes and guest ABI exits, and rejects unsupported image
layouts. No original-code execution fallback was identified in the inspected
production routing. Diagnostic/original measurement harnesses remain distinct.
This limited conclusion does not clear the unreviewed host service chain or
change native acceptance.

## Readability and remediation sequence

Fix data-loss and command-construction boundaries first, with narrow regressions
that exercise actual code. Then correct validation, editor delta persistence,
cache/source ownership and advertised pack semantics. Rebuild the source package
only after its user paths pass in a fresh extraction.

For readability, start with maintained launch/setup/export modules and the active
host interfaces. Dense one-line implementations in `play_remaster.py`,
`native_assets.py`, native overlays and some shader applicators should become
named validation/preparation/launch functions with normal formatting. Explain
path ownership, schemas, guest address units, binary layouts, resource lifetime,
threading and ABI/FP decisions. The monolithic MFC service host needs a documented
service inventory and carefully extracted helpers, not speculative semantic
renaming of recovered guest functions.

Keep behavior fixes separate from comment/format changes. Preserve frozen
snapshots and their hashes, identify the current executable/applicator chain,
and supply reviewed successors where necessary. Add meaningful regressions for
the identified defects; comments alone do not make these paths correct. Retain
this coverage record until every intended publication component has an explicit
disposition. Full source review and final publication approval remain open.
