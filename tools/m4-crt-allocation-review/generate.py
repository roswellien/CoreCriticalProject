"""Independent bounded composition fixtures; author/native code remains frozen."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes, workspace_path
from manifests import normalized, verify_manifest

def need(ok, why):
    if not ok:
        raise ValueError(why)

def replace(text, old, new):
    need(text.count(old) == 1, 'One explicit fixture seam: ' + old[:90])
    return text.replace(old, new)

def main(preparation, expected_sha, directory):
    prep = workspace_path(preparation, reports=True)
    out = workspace_path(directory, reports=True)
    need(prep.parent == ROOT / 'reports/m4-crt-allocation' and out.parent == ROOT / 'reports/m4-crt-allocation-review'
         and not out.exists(), 'Fresh privately owned review generation')
    need(sha_file(prep / 'report.json') == expected_sha, 'Externally frozen authored preparation')
    metadata = json.loads((prep / 'report.json').read_bytes())
    need(metadata['passed'] and not metadata['State_reseed_after_writer'] and metadata['reused_guest_objects'] == 38,
         'Author froze literal full-carry preparation')
    files = {}
    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Literal fixed source dependency')
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Consistent physical dependency aliases')
        files[key] = actual
        return path
    pin(prep / 'report.json', expected_sha)
    pin(prep / 'pins.json')
    for name, digest in json.loads((prep / 'pins.json').read_bytes())['files'].items():
        pin(name, digest)
    for path in (Path(__file__), HERE / 'fixture_extra.inc', ROOT / 'tools/m4-crt-allocation/worker_gate.inc'):
        pin(path)
    out.mkdir(parents=True)
    for path in prep.iterdir():
        if path.suffix in ('.cpp', '.hpp', '.inc'):
            publish_bytes(out / path.name, path.read_bytes())
    publish_bytes(out / 'fixture_extra.inc', (HERE / 'fixture_extra.inc').read_bytes())
    composition = (out / 'composition.cpp').read_text()
    composition = replace(composition, '#include "main_v2.inc"', '#include "fixture_extra.inc"\n#include "main_v2.inc"')
    # Modify fresh reviewer observer/main copies only; native binding and all
    # literal guest source bodies remain exact author/preparation bytes.
    (out / 'composition.cpp').write_text(composition)
    observations = (out / 'observations.hpp').read_text()
    marker = ' auto phase=directory/name;'
    observations = replace(observations, marker,
        ' const std::string_view selected=name;if(!selected.starts_with("allocation-")&&selected!="heap-create-after"&&selected!="writer-before"&&selected!="writer-after"&&selected!="retry-after")return;\n' + marker)
    observations = replace(observations, 'auto phase=directory/name;',
        'auto phase=directory/name;{std::array<std::byte,4096>reserved{};r.memory().read({0x30000000},reserved);fresh_output(phase/"reserved-runtime-heap.bin",reserved);}')
    (out / 'observations.hpp').write_text(observations)
    main = (out / 'main_v2.inc').read_text()
    main = replace(main, 'auto seeded=saved;', 'auto seeded=saved;review_seed(seeded.fx,seeded.env);')
    # The authored assembly imports only XMM6..15 from its seed argument;
    # actively load our private rich x87/ENV/MXCSR seed before it samples.
    # This affects host observer fixtures only, never the guest State/FX.
    main = replace(main, '(void)data_boundary_call(&j,&before,&after,&seeded);restore_host(saved);',
                   '''const auto review_error_before=GetLastError();std::uint64_t review_flags_before{},review_flags_after{};
 restore_host(seeded);__asm__ volatile("pushfq\\n\\tpopq %0":"=r"(review_flags_before)::"memory");
 (void)data_boundary_call(&j,&before,&after,&seeded);__asm__ volatile("pushfq\\n\\tpopq %0":"=r"(review_flags_after)::"memory");
 const auto review_error_after=GetLastError();restore_host(saved);std::array<std::uint64_t,4>review_abi{review_error_before,review_error_after,review_flags_before,review_flags_after};raw_output(row/(std::string(name)+"-host-abi.bin"),review_abi);''')
    main = replace(main, 'scenario<18', 'scenario<24')
    main = replace(main, 'const auto mode=scenario<6?0:scenario+163;',
                   'const auto mode=scenario<12?0:scenario+989;review_case=scenario;review_hook_hits=0;')
    main = replace(main, '(scenario<6?scenario:0)*sizeof(Input)', '(scenario%6)*sizeof(Input)')
    main = replace(main, 'allocation.configure_request(std::array<unsigned,6>{0,1,24,31,32,4096}[scenario<6?scenario:2]);',
                   'allocation.configure_request(std::array<unsigned,6>{0,1,24,31,32,4096}[scenario<12?(scenario+3*(scenario/6))%6:2]);allocation.extra=&review_hook;')
    marker = '  if(!mode){require(allocation.batch_complete'
    need(marker in main, 'Authored allocation gate seam exists')
    gate = '''
  const auto owned_registry=allocation.allocation_registry;
  const bool expected_alloc=!mode||(mode!=1001&&mode!=1002&&mode!=1007&&mode!=1010);
  review_check(allocation.actual_alloc_calls()==unsigned(expected_alloc),"Independent hook fault precedes expected genuine HeapAlloc");
  review_check(allocation.actual_free_calls()==unsigned(mode==0),"Independent directed faults never call genuine source HeapFree");
  review_check(owned_registry[17]==unsigned(mode!=0&&expected_alloc)&&owned_registry[18]==owned_registry[17],"Fault cleanup frees each actual owned pointer exactly once");
  review_check(!allocation.allocation_token_valid(al::allocation_address),"Closed allocation rejects former guest token");
  review_check(review_hook_hits==unsigned(mode!=0),"Each independent control actually reached its exact source/API frontier");
  std::array<std::uint64_t,12>review_summary{1,scenario,mode,review_hook_hits,allocation.known_handle(),allocation.known_allocation(),allocation.actual_create_calls(),allocation.actual_destroy_calls(),allocation.actual_alloc_calls(),allocation.actual_free_calls(),owned_registry[17],owned_registry[18]};raw_output(row/"review-ownership.bin",review_summary);
'''
    main = main.replace(marker, gate + marker, 1)
    marker = ' require(!direct_failed,"Direct capture failed without publication");'
    summary = ''' {DirectText totals(directory/"review-controls.json");totals<<"{\\"passed\\":true,\\"rows\\":24,\\"ordinary_rows\\":12,\\"independent_control_rows\\":12,\\"checks\\":"<<review_checks<<",\\"token_units\\":"<<review_token_units<<",\\"wrong_thread_units\\":"<<review_thread_units<<",\\"game_executed\\":false,\\"original_executed\\":false}\\n";}
'''
    main = replace(main, marker, summary + marker)
    (out / 'main_v2.inc').write_text(main)
    for path in out.iterdir():
        if path.is_file():
            pin(path)
    report = dict(passed=True, scope='Independent fixture generation only; no native/API execution',
                  preparation=str(prep), preparation_sha256=expected_sha, source_bodies_modified=False,
                  ordinary_rows_per_level=12, independent_control_rows_per_level=12,
                  planned_total_rows=48, planned_hardware_pairs=96,
                  per_instruction_snapshot_added=False, old_prefix_checkpoints_filtered=True,
                  full_State_FX_CPU_pages_at_allocator_milestones=True,
                  API_response_injection=False, transport='checked direct writer build-r4',
                  current_physical_closure=verify_manifest(files), files=files)
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}))

if __name__ == '__main__':
    main(*sys.argv[1:])
