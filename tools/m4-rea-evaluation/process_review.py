"""Read-only grounded process assessment; no shared REA target or execution."""
from pathlib import Path
import hashlib, json, sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    out = ROOT / 'reports/m4-rea-evaluation/process-review-r1'
    if out.exists(): raise ValueError('Fresh review output required')
    inputs = [
        'reports/m4-rea-evaluation/benchmark-r1.json',
        'reports/m4-rea-evaluation/initializer-inventory-r1.json',
        'docs/m4-execution-plan-r2.md', 'docs/m4-progress-startup28.md',
        'docs/m4-next-registration-batch.md',
        'tools/m4-service-initializers/recover.py',
        'tools/m4-onexit-batch-recovery/recover.py',
        'tools/m4-onexit-batch-recovery/prepare_v3.py',
        'tools/m4-crt-locale-batch-recovery/recover_v2.py',
        'tools/m4-crt-mainargs-recovery/recover.py',
        'tools/m4-onexit-source/lift_v3.py',
        'tools/m4-onexit-source/interface.py',
        'reports/m4-onexit-source/object-extent-r1/report.json',
        'reports/m4-onexit-source/symbol-attribution-r1/report.json',
        'reports/m4-onexit-source/lifts-r4/report.json',
        'reports/m4-onexit-source/original-run-r4/report.json',
        'reports/m4-joint-startup28-root/acceptance-r2/report.json',
    ]
    pins = {str((ROOT / name).resolve()): sha(ROOT / name) for name in inputs}
    benchmark = json.loads((ROOT / inputs[0]).read_bytes())
    inventory = json.loads((ROOT / inputs[1]).read_bytes())
    assert benchmark['passed'] and inventory['passed'] and inventory['nonzero_entries'] == 144
    rows = [
        dict(step='Entry discovery and dependency triage',
             current='Exact PE table/import/export recovery, byte-backed graph walk, direct closures and root grouping are already scripted.',
             opportunity='Seed exact table roots and required provider exports, then export batched call/reference summaries and unresolved boundaries to prioritize complete shared-service units.',
             retained='Original table order, literal byte checks, both conditional successors, cold/tail branches and unresolved indirect controls.'),
        dict(step='Manual helper and constructor investigation',
             current='Inspect instruction operands, implicit ECX objects, source stack arguments and absolute/dynamic field offsets.',
             opportunity='Pseudocode plus data flow gives a readable first-pass contract and field inventory; normalize exact address/offset/width evidence into page/frontier candidates.',
             retained='Verify every proposed field, source argument and page extent against the literal instruction rows and original BEFORE inputs.'),
        dict(step='Types and ABI contracts',
             current='Hand-authored API argc/signatures and guest/native ownership projections, source ECX/stack/RET handling.',
             opportunity='Recover candidate parameter locations, imported signatures, structures and return/stack effects as confidence-tagged review hints; generate repetitive declaration scaffolding after verification.',
             retained='Measured 32-bit stack cleanup, register and x87 return locations, Win64 ABI adaptation, privately full-width pointer ownership and checked guest aliases.'),
        dict(step='Literal translation and compilation',
             current='Exact source rows feed Remill, host lowering checks 34 layouts and State3504, then builds O0/O2 objects.',
             opportunity='Drive an existing reusable lift/build manifest from the seeded dependency export; derive dispatch names from the actual LLVM definition and physical COFF exports.',
             retained='Remill semantics, constrained raw80 operations, checked bridges, object/source hashes and actual compiled symbols.'),
        dict(step='Independent execution acceptance',
             current='Actual original x86, native O0/O2, original-BEFORE independent source model, persistent state/pages/owners and causal fault controls.',
             opportunity='Use static summaries to propose focused cases and consumers, and emit compact evidence once per complete functional unit.',
             retained='Actual API witnesses, whole-state comparisons, raw x87 hardware observations, failure cleanup and integrated startup order.'),
    ]
    metrics = [
        dict(name='Exact seeded entry coverage', definition='Recognized exact initializer entries / 144, plus declared required helper/provider entries; count static coverage separately from executable acceptance.', target='144/144 initializer table entries or an explicit per-entry conflict receipt before using whole-table Ghidra inventories.'),
        dict(name='Recovery cost per functional batch', definition='Cold import, seed/repair, warm export, reviewer correction and literal-contract preparation seconds, each measured once for the same byte-identified batch.'),
        dict(name='Accepted throughput', definition='New connected initializer roots accepted / total batch wall-clock hours and complete functional units accepted / wall-clock hours; include integration, comparison and control time.'),
        dict(name='First-pass quality', definition='Contracts and builds passing without source/ABI/page correction / attempted contracts and builds; count unknown indirect edges and post-review corrections separately.'),
        dict(name='Stage cost', definition='Static preparation, lift/compile/link, original run, native run, direct archive finalization, strict verification, independent comparison and review seconds.'),
        dict(name='Reuse and cold-start burden', definition='Cold program initializations per input SHA, warm requests per initialization, unchanged accepted objects reused / needed objects and avoidable reruns.'),
    ]
    recommendation = [
        'Keep one persistent analysis Program per pinned game/provider image and batch requests by a complete shared dependency unit. A saved neutral REA snapshot alone did not eliminate cold initialization in this pilot.',
        'Use the actual 145 table slots/144 nonzero entries as seeds, with explicit helper/callback/provider entry and overlap/tail-chunk handling. The default 10,575-function count is not initializer coverage.',
        'Export a compact artifact-bound JSON dossier: entry/table cell, chunks, bytes, direct and indirect calls, imports, parameter storage/confidence, data fields with widths, FP/FS sites and unresolved controls. Feed it to existing recovery manifests rather than adding another manual reporting queue.',
        'Use Ghidra pseudocode and types to accelerate contract review and propose bounded pages/API scaffolding. Recheck proposals through the existing literal byte/operand route before generating implementation bindings.',
        'Retain Remill/LLVM as the executable route and keep original x86/ABI/raw80/API ownership comparisons. Decompiler pseudocode omits observations that the current State/FX acceptance intentionally preserves.',
        'Continue independent source, owner/native and review lanes. The measured Java bridge serializes requests per Program, so concurrent queries into that same Program do not establish additional static throughput.',
        'Reuse accepted objects/contracts and direct archives; complete the pending 54-root registration unit before counting its roots. More recovered procedures alone do not advance 28/144 accepted coverage.',
    ]
    document = '''# REA/Ghidra process assessment

Use a persistent, explicitly seeded Ghidra project as the static recovery front end. Keep the current Remill/LLVM translation and executable acceptance pipeline. The likely benefit is less manual dependency, parameter and field investigation; current byte checking, CFG walking, dependency grouping and literal object generation are already automated.

The recorded pilot spent 95.757 seconds on the first cold request, which ended because the exact requested initializer had no recognized function. A warm four-function pseudocode batch took 41 ms; a constructor dossier took 46 ms. Saving and reopening the neutral snapshot still incurred a 93.811-second cold initialization. These are static request costs, and do not establish an end-to-end recompilation speedup.

Default analysis lists 10,575 procedures but recognizes only 3 of the 144 exact initializer table entries. Seed the original 145 slots with 144 nonzero roots, then required helper/provider and callback entries. Record overlaps and tail chunks explicitly. Direct CLI DLL/table-seeding results are owned by the independent pilot and remain outside this assessment until its receipt passes.

## Where it should save work

| Step | Specific opportunity | Existing checks to retain |
| --- | --- | --- |
| Dependency planning | Batch call graphs, imports and references from exact seeded roots; group work by shared services. | Original table order, full literal closure and unresolved-control declarations. |
| Constructors/helpers | Readable pseudocode and data flow to propose parameter, global and object-field contracts. | Source operand widths/addresses and independently declared input extents. |
| API/ABI scaffolding | Confidence-tagged parameter storage, structures and imported signature candidates. | Measured x86 stack/register/return contracts and checked Win64 ownership adaptation. |
| Repetitive preparation | Compact address-bound exports drive existing lift/build manifests and verified declarations. | Exact PE bytes, Remill semantics, layout checks and physical COFF symbol attribution. |
| Test planning | Static consumers/FP/FS/indirect-site inventories focus the necessary cases. | Actual original/native execution, original-BEFORE models, status observations and causal controls. |

A concrete useful result is the 51B020 constructor dossier: its six recovered field offsets match the literal 0x4844..0x4858 stores. Combined with source ECX=0x638578, these fields require page 0x63C000. The separate source receipt verifies all six writes and complete page results in six actual original cases. This illustrates how a fast field export can prevent an omitted-page investigation. The dossier's default low-confidence __stdcall label, however, does not establish the implicit ECX object ABI.

The 4C5960/4020D0 pseudocode also makes vector subtraction and normalization easy to understand. Executable equivalence still depends on raw80 intermediates, guest control word and rounding, x87 stack/top/tag/status and legacy metadata, checked memory ordering and return convention. A float10 label in a decompiler view does not prove those effects or provide a valid Win64 math-library ABI.

## Workflow to adopt

1. Keep a pinned game/provider analysis Program alive; amortize import/seed cost across batched requests. Do not reopen a neutral snapshot for each function.
2. Seed and export exact roots/chunks, imports, calls, parameter storage with confidence, field widths, FP/FS and unresolved-control sites. Bind exports to image SHA and addresses; keep output bounded to the active functional unit.
3. Reconcile the export with existing literal rows and use it to generate the next contract/lift manifest. Human review concentrates on uncertain ownership, ABI, indirect dispatch and FP behavior.
4. Compile once at O0/O2, execute a complete persistent unit, compare independently and run its targeted fault controls. Reuse unrelated accepted objects and evidence.
5. Publish accepted functional progress and measured stage costs. Static function counts and pseudocode completion remain separate.

The provider/translation/source-review lanes can work concurrently as in the current execution plan. The measured Java bridge serializes requests for one Program, so additional agents issuing the same static requests would duplicate work. Assign one static-analysis lane and parallelize implementation and independent review instead.

## Throughput measurements

Measure exact seeded coverage, static-contract preparation time, first-pass correction rate, new connected roots accepted per batch wall-clock hour, complete units accepted per hour, and separate analysis/lift/build/execution/capture/compare/review times. Compare batches with the same input SHA, similar shared dependencies and the same acceptance scope. Track cold initializations per SHA, warm requests per initialization and reused accepted objects.

The first coverage gate is 144/144 table entries or explicit conflict records. No numerical implementation speedup is established yet. The 41-ms query result demonstrates that warm static access is inexpensive; actual accepted throughput must include the remaining native/source/control work. Current accepted coverage stays 28/144. The prepared 54-root unit has actual original evidence and literal COFFs, but remains pending native integration and paired validation.
'''
    out.mkdir(parents=True)
    (out / 'assessment.md').write_text(document, encoding='utf-8')
    pins[str(Path(__file__).resolve())] = sha(Path(__file__))
    pins[str((out / 'assessment.md').resolve())] = sha(out / 'assessment.md')
    report = dict(passed=True, scope='Independent process assessment from current local scripts, plans and static tool pilot; no shared-target mutations or new execution',
                  measurements=benchmark['measurements'], exact_default_entry_coverage=benchmark['default_initializer_function_coverage'],
                  current_accepted_initializers=28, inventory_roots=144, rows=rows,
                  recommendations=recommendation, proposed_throughput_metrics=metrics,
                  quantified_end_to_end_speedup_established=False, direct_CLI_seed_and_DLL_pilot='pending independent receipt',
                  original54_evidence_preserved=True, physical_symbol_attribution_preserved=True,
                  static_analysis_reexecuted=False, shared_REA_target_changed=False,
                  initializer_credit=False, native_game_credit=False, files=pins)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    pins[str((out / 'report.json').resolve())] = sha(out / 'report.json')
    (out / 'pins.json').write_text(json.dumps(dict(files=pins), indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, report_sha256=sha(out / 'report.json'), assessment=str(out / 'assessment.md'))))

if __name__ == '__main__': main()
