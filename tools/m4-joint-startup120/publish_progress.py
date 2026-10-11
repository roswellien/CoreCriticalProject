"""Publish current documentation only after exact120 acceptance succeeds."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def main():
 p=ROOT/'reports/m4-joint-startup120-root/acceptance-r1/report.json'
 data=p.read_bytes();a=json.loads(data)
 assert a['passed'] and a['connected_roots']==120 and a['remaining_inventory_roots']==24
 assert not a['whole_M4_complete'] and not a['native_game_launch_complete']
 gates=a['gates'];assert len(gates)==44
 def report(key):
  item=gates[key];b=(ROOT/item['path']).read_bytes()
  assert hashlib.sha256(b).hexdigest()==item['sha256']
  r=json.loads(b);assert r['passed'];return r
 provider=report('provider');native=report('native')
 levels={r['level']:r for r in native['levels']};assert set(levels)=={'O0','O2'}
 closure=a['physical_closure'];assert closure['passed'] and not closure['metadata_only_cache_used']
 inputs=closure['unique_physical_dependencies'];seconds=closure['verify_seconds']
 predicates=sum(len(v['equal']) for v in gates.values())
 capacity=sorted({r['first_replay_msize_capacity'] for r in provider['provider_sequences']})
 queries=sorted({r['first_replay_msize_queries'] for r in provider['provider_sequences']})
 growth=sorted({r['actual_growth_replays'] for r in provider['provider_sequences']})
 pc=provider['provider_counts']
 progress=f'''# Accepted native startup sequence: 120 selected roots

Updated 2026-10-09. **120/144 selected startup initializers are accepted**, up from [116](m4-progress-startup116.md), with **24 inventory roots remaining**. This is 83.3% of the initializer inventory. Full M4, project-built native menus and native Training remain open.

The [final acceptance](../reports/m4-joint-startup120-root/acceptance-r1/report.json), SHA `{hashlib.sha256(data).hexdigest()}`, binds **44 passed gates and {predicates} explicit measured predicates**. Its conflict-normalized union rehashed all **{inputs:,} physical dependencies** in {seconds:.2f} seconds without a metadata cache. Accepted116 evidence remains unchanged.

## Added behavior

Roots `40F0E0`, `4795F0`, `47F5F0` and `4B5220` execute in original relative table order. Their recovery contains fifteen new game bodies, 184 physical instruction rows and 596 bytes. They add four callback registrations and one normal game exception-chain record. They introduce no new provider, allocation or string-copy operation. The complete selected schedule has **92 ordered callbacks, 50 MFC allocations, 19 strings and one callback vector: 70 live owners before cleanup**.

Six reached calls use three physical target cells. Four calls use absolute cells; two genuinely read the constructor-installed instance vtable. The derived vtable is committed before its instance use. The literal helper ORs the global DWORD at `5F49B8` into the object and retains its complete flag effects before the caller clears the field. The pointer helper is admitted only for the reached zero argument, with no pointee read. General virtual dispatch and the nonzero pointer path remain open.

The original observes genuine target entry and pre-RET CPU/FX/environment and stack frames; its post-RET CPU is derived from the literal RET. Native captures observe actual entered and returned State/CPU/FX checkpoints. These are distinct observation boundaries.

## Passed evidence

| Gate | Measured extent |
| --- | --- |
| [Original x86 execution](../{gates['original_validation']['path']}) | Six persistent sequences, 720 root calls, forty observed pages |
| [Original source](../{gates['original_source']['path']}) | 552 constructor prefixes, 21,528 whole nonstack-page checks and 36 complete indirect entry/pre-RET pairs |
| [Persistent native source](../{gates['source']['path']}) | Twelve sequences, 1,440 root calls, 57,600 whole-page checks before plus 57,600 after; no per-phase or AFTER state seeding |
| [Finite indirect source](../{gates['indirect_source']['path']}) | 72 actual native CALL/RET joins, 144 full native boundaries, 36 original pairs and 72 paired interfaces |
| [Whole paired data](../{gates['paired']['path']}) | 1,440 phases and 109,440 ordinary nonstack-page relations |
| [Normal chain relation](../{gates['paired_FS']['path']}) | 180 paired game frames, 360 complete installed/restored twelve-byte relations and 180 nested CRT null-free accesses |
| [Typed ownership](../{gates['paired_owned']['path']}) | 96 carried owner relations, 288 complete selected/grown/cleaned endpoints and 204 vector-field commits |
| [Independent fault audit](../{gates['control_audit']['path']}) | 108 attempts, 52 causal refusals, 54 unchanged retries, 358,404 byte-exact retry records and 54 HeapDestroy identity triplets |

The [provider proof](../{gates['provider']['path']}) checks {pc['whole_State_checkpoints']:,} complete State/CPU/FX checkpoints and {pc['whole_checkpoint_pages']:,} whole checkpoint pages. It verifies 600 MFC allocations, 228 duplicated strings, 840 source frees and twelve real heap destructions. First-replay genuine size-query counts are {queries}, measured capacities are {capacity} bytes, and independently predicted actual additional growth counts are {growth}. The source growth formula and same-owner size queries are checked against actual API observations.

The [raw paired audit](../{gates['paired_review']['path']}) derives six observed compiled diagnostic spans totaling forty bytes and verifies all 17,280 exact span relations. Each remaining page difference has an explicit typed or branch-input relation; no blanket mask is granted. The complete original initialized MFC loader page and native raw PE page are carried separately, with all actual differences retained. The borrowed pointee remains outside the read/mapping domain.

The controlled original RET hook at `59FF0D` replays the genuine one-byte RET. Its unused tail contains two NOP bytes and two bytes of the unselected neighboring body at `59FF10/11`. Independent review excludes that neighbor from the complete selected120 closure; whole-game use is outside this fixture.

## Build, tools and remaining scope

The [link audit](../{gates['link']['path']}) verifies **351 literal COFFs, 27 compiled objects and two capture objects per level: 380 actual inputs**. One historical FDIV archive per level remains physically retained and unlinked. The [actual native run](../{gates['native']['path']}) completes all 120 roots in {levels['O0']['elapsed_seconds']:.2f} seconds at O0 and {levels['O2']['elapsed_seconds']:.2f} seconds at O2. Each level emits {levels['O0']['logical_files']:,} canonical logical records and {levels['O0']['payload_bytes']:,} logical payload bytes. These are worker measurements, not a whole-workflow speedup estimate. The isolated control fixture additionally links its rich hardware capture object, totaling 381 inputs per level.

Warm Ghidra exports cover all fifteen requested bodies without a cold import. A missing `59FF80` boundary uses an explicit unsaved, physical-source-bound annotation. Focused [REA evidence](../reports/m4-vtable-rea/review-r1/report.json) corroborates five boundaries and two fixed targets, while retaining the missing boundary and unresolved instance target. Literal physical bytes remain primary. These measurements do not establish whole-workflow speedup.

Earlier rejected preparations, invocations and proof scripts remain preserved. Corrections are additive. The final fault audit authenticates committed source prefixes, actual private mutations, full retries and cleanup. Hardware preservation covers the authored caller boundary through C++ catch; it gives no naked throwing Session guarantee.

[Plan r9](m4-execution-plan-r9.md) starts with authentic MSVCP initialization and the five-root Lockit family. Remaining graph, service and numerical roots, startup scheduling, environment/mainargs, required thread/exception behavior and menus must still pass before M4 closes. Earlier live helper/numeric Training tests do not establish project-built native Training.
'''
 plan='''# M4 execution after the four-root indirect-call batch

Updated 2026-10-09. **120/144 initializers are accepted, with 24 remaining**. This supplements [plan r8](m4-execution-plan-r8.md). The [accepted record](m4-progress-startup120.md) binds original/native execution, persistent source state, finite indirect calls, paired ownership and independent controls. Full M4 and native menus remain open.

## Next counted family

The [physical Lockit frontier](../reports/m4-lockit-frontier/recovery-r1/report.json) identifies five roots sharing exact MSVCP50 constructor/destructor services. Freeze the four smaller roots `411010`, `4DC140`, `500660` and `5968F0` as the first candidate toward124 after authentic provider admission. Recover the complex `4B7F70` tree graph concurrently as a separate follow-on toward125. It owns613 of891 physical rows and adds nine unresolved register calls; its closure is not a prerequisite for accepting the four smaller roots. Static recovery grants no execution credit.

First build an isolated genuine x86 loader probe for the exact CRT and MSVCP DLLs. Capture the post-DllMain state at `78145658`, the critical-section owner at `78145640`, loaded import identities and relevant complete pages. Run one balanced scratch-object Lockit constructor/destructor and retain actual entry/return, CPU/FX/environment, API and ownership observations. If it reaches lazy initialization, recover that path before selecting the runtime domain. Raw BSS zeros do not authenticate an initialized state; forcing state2 supplies no original evidence.

Admit the distinct MSVCP critical-section resource with an explicit native association, lifecycle and exact import contract. Existing CRT lock support does not automatically admit this owner. Recover the finite four-root game/provider closure, derive the normal reached path and actual allocation geometry, compile at O0/O2 and add causal controls for invalid targets, state/resource identities, permissions and committed prefixes. Bind authentic original observations before running the full124-root candidate schedule in original relative order. Count roots only after persistent source, provider, paired-data, controls and full physical acceptance pass. The follow-on tree root must additionally close source-owned nodes, repeated allocation occurrences, links/rotations and all nine register-import carry proofs before its full125-root gate.

Then choose coherent remaining MFC graph/service families from the exact original table. Recover callback arguments and shared-node ownership where reached. Formatting, font, version, OS and codepage services need genuine new-provider/environment contracts. `4B64F0` requires its separate FCOS numerical/status proof. Keep unresolved required branches explicit.

## Execution lanes and efficiency

Keep recovery/original observation, additive native implementation and independent source/provider/control review concurrent. Reuse accepted bodies, API and ownership contracts, warm Ghidra projects and canonical capture consumers. Use focused REA observations to find targets and boundaries, then check actual source bytes; unresolved tool output remains an open dependency. Serialize full capture readers to fit memory, while light reviews and next-family recovery continue. Release closed transport indexes between O0/O2 without changing retained evidence.

Freeze exact root lists, physical closure, reached domain, new resources and the first unsupported path before implementation. Update named schedule counts separately from fixed binary byte offsets, and review the ABI before running capture consumers. Preserve failed evidence and make additive corrections. Reuse accepted identities in local preparation; final acceptance still rehashes the complete conflict-normalized physical dependency union. Production keeps canonical transport; the separate capture-sharing pilot needs complete consumer compatibility and measured whole-workflow benefit before adoption.

## Wider M4 completion

Initializer coverage is one M4 inventory. Complete the required providers and controls, original startup scheduling, environment/mainargs and required thread/exception behavior. Then connect file/configuration, graphics, input and audio dependencies to a project-built native menu executable. Validate menu appearance, navigation and input against the original. M5 begins when that runtime loads and plays Training with recovered movement, weapons, collision, AI, HUD and audio.

Normal initializers register stored callbacks; their execution is a separate gate. Allocation-null, handler/exception dispatch, general virtual calls and nonzero pointer paths remain outside current acceptance. No whole-project percentage or unsupported ETA is assigned.
'''
 milestones=f'''# MW34 RECOMP milestone update

Updated 2026-10-09. This supplements the [milestone register](project-milestones.md) and [accepted116 update](project-milestones-r8.md). [Final acceptance](../reports/m4-joint-startup120-root/acceptance-r1/report.json) passed forty-four gates and rehashed {inputs:,} physical dependencies.

| Milestone | Current state | Next completion requirement |
| --- | --- | --- |
| M1: MW3 bootstrap | Complete within admitted research scope | Maintain provenance and reproducibility |
| M2: CPU and ABI validation | Complete within accepted bounded scope | Extend contracts for newly reached paths |
| M3: First native subsystem | Complete for the accepted two-entry buffer component | Reuse checked dependencies |
| M4: Native startup and menus | Active; **120/144 selected initializers accepted, 24 remaining** | Remaining providers/controls, required thread/exception behavior, environment/mainargs, startup scheduling and native menus |
| M5: Native Training | Planned | Load and play Training through the project-built native runtime |
| M6: Gameplay compatibility/release | Planned | Missions, saves, timing, stability and reproducible asset-free installation |
| M7: Configurable modernization | Later; Vulkan and asset experiments exist | Integrate improvements against recovered behavior |
| M8: Additional systems/games | Later | Admit and validate each platform/title separately |

The [120-root record](m4-progress-startup120.md) adds four normal constructor roots with six finite indirect CALL/RET instances and one game exception-chain frame. Genuine original execution covers 720 root calls; native O0/O2 source comparisons cover 1,440 calls and forty observed pages. The actual link uses 351 literal COFFs and 380 inputs per level. Both build modes pass independent fault tests with exact retries and actual heap cleanup.

**83.3% measures this initializer inventory only.** Full M4, project-built native menus and native Training remain open. Earlier live helper/numeric Training tests retain their separate scope.

[Plan r9](m4-execution-plan-r9.md) begins with authentic MSVCP initialization and the five-root Lockit family, followed by the remaining graph/service and numerical roots. Recovery, native work and independent review continue concurrently; memory-intensive capture readers run serially. No whole-project completion percentage or unsupported ETA is assigned.
'''
 for name,text in [('m4-progress-startup120.md',progress),('m4-execution-plan-r9.md',plan),('project-milestones-r9.md',milestones)]:
  out=ROOT/'docs'/name;assert not out.exists();out.write_text(text,encoding='utf-8')
 print(json.dumps(dict(published_documents=3,connected_roots=120,physical_inputs=inputs,predicates=predicates)))

if __name__=='__main__':main()
