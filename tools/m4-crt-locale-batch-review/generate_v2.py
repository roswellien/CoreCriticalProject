"""Prepare finite independent observers from a frozen whole-unit preparation."""
import json
from pathlib import Path
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
    need(text.count(old) == 1, 'Exactly one fresh observer seam: ' + old[:90])
    return text.replace(old, new)

def main(preparation, expected_sha, directory):
    prep = workspace_path(preparation, reports=True)
    out = workspace_path(directory, reports=True)
    need(prep.parent == ROOT / 'reports/m4-crt-locale-batch'
         and out.parent == ROOT / 'reports/m4-crt-locale-batch-review'
         and not out.exists(), 'Fresh independent fixture namespace')
    need(sha_file(prep / 'report.json') == expected_sha, 'Externally fixed prepared source identity')
    metadata = json.loads((prep / 'report.json').read_bytes())
    need(metadata['passed'] and not metadata['native_executed']
         and not metadata['State_reseed_after_writer'] and not metadata['source_bodies_modified']
         and metadata['direct_strict_capture_emission'], 'Source-only complete preparation with direct transport')
    files = {}
    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Current source identity: ' + str(path))
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Conflict-free source path')
        files[key] = actual
    pin(prep / 'report.json', expected_sha)
    pin(prep / 'pins.json')
    for name, digest in json.loads((prep / 'pins.json').read_bytes())['files'].items():
        pin(name, digest)
    for path in (Path(__file__), HERE / 'fixture_seed.inc', HERE / 'fixture_hooks_v2.inc'):
        pin(path)
    out.mkdir(parents=True)
    for path in prep.iterdir():
        if path.suffix in ('.cpp', '.hpp', '.inc'):
            publish_bytes(out / path.name, path.read_bytes())
    for name in ('fixture_seed.inc', 'fixture_hooks_v2.inc'):
        publish_bytes(out / name, (HERE / name).read_bytes())
    main = (out / 'main_v2.inc').read_text()
    main = replace(main, '#include "observations.hpp"',
                   '#include "fixture_seed.inc"\n#include "fixture_hooks_v2.inc"\n#include "observations.hpp"')
    main = replace(main, 'require(argc==7,"Exact game/object/provider/FDIV/BEFORE pack/fresh direct output arguments");',
        'require(argc>=8,"Exact original inputs, fresh output and independent selection with supplemental native argv");const unsigned review_selection=unsigned(std::stoul(argv[7]));require(review_selection<6,"Six bounded independent selections");')
    main = replace(main, 'auto seeded=saved;', 'auto seeded=saved;review_seed(seeded.fx,seeded.env);')
    main = replace(main, 'restore_host(seeded);(void)data_boundary_call(&j,&before,&after,&seeded);restore_host(saved);',
        '''const auto review_error_before=GetLastError();std::uint64_t review_flags_before{},review_flags_after{};
 restore_host(seeded);__asm__ volatile("pushfq\\n\\tpopq %0":"=r"(review_flags_before)::"memory");
 (void)data_boundary_call(&j,&before,&after,&seeded);__asm__ volatile("pushfq\\n\\tpopq %0":"=r"(review_flags_after)::"memory");
 const auto review_error_after=GetLastError();restore_host(saved);std::array<std::uint64_t,4>review_abi{review_error_before,review_error_after,review_flags_before,review_flags_after};raw_output(row/(std::string(name)+"-host-abi.bin"),review_abi);''')
    main = replace(main, 'scenario<18', 'scenario<2')
    main = replace(main, 'const unsigned mode=scenario<6?0:201+scenario-6;',
                   'const unsigned mode=scenario?1001+review_selection:0;review_case=review_selection;review_hook_hits=0;')
    main = replace(main, '(scenario<6?scenario:0)*sizeof(Input)', '(review_selection%6)*sizeof(Input)')
    main = replace(main, 'cm::Binding commandline(mainargs.context,provider,0);Context context',
                   'cm::Binding commandline(mainargs.context,provider,0);mainargs.batch.extra=&review_hook;Context context')
    marker = 'snapshot(r,row,"final");'
    main = replace(main, marker, marker + '''
 const auto before_retry=mainargs.batch.summary();Job retry;retry.entry_context=&context;boundary(retry,row,"retry",scenario);snapshot(r,row,"retry-after");
 review_check(retry.denied&&!retry.ok,"Consumed whole entry refuses retry");review_check(mainargs.batch.actual_create_calls()==1&&mainargs.batch.actual_destroy_calls()==1&&mainargs.batch.successful_destroy_calls()==1,"One actual private heap lifecycle per row");
 review_check(mainargs.batch.summary()[9]==before_retry[9]&&mainargs.batch.summary()[18]==before_retry[18],"Retry never adds actual native allocations or source APIs");
 review_check(!mainargs.batch.token_valid(lb::token),"Closed parent heap denies former guest token");review_check(review_hook_hits==unsigned(mode!=0),"Exactly one independent fault actually reached its selected frontier");
 std::array<std::uint64_t,12>review_ownership{1,review_selection,scenario,mode,review_hook_hits,mainargs.batch.actual_create_calls(),mainargs.batch.actual_destroy_calls(),mainargs.batch.successful_destroy_calls(),live[9],live[12],live[18],unsigned(retry.denied)};raw_output(row/"review-ownership.bin",review_ownership);
''')
    marker = 'require(!direct_failed,"Healthy direct semantic capture");'
    main = replace(main, marker, '''{DirectText totals(directory/"review-controls.json");totals<<"{\\"passed\\":true,\\"rows\\":2,\\"ordinary_rows\\":1,\\"independent_control_rows\\":1,\\"checks\\":"<<review_checks<<",\\"wrong_thread_units\\":"<<review_thread_units<<",\\"selection\\":"<<review_selection<<",\\"actual_GetCommandLineA_input\\":true,\\"API_response_injection\\":false,\\"game_executed\\":false}\\n";}
 ''' + marker)
    (out / 'main_v2.inc').write_text(main)
    observations = (out / 'observations.hpp').read_text()
    marker = ' const auto phase=row/name;'
    observations = replace(observations, marker,
        ''' const std::string_view selected=name;constexpr std::string_view kept[]{"writer-before","writer-after","entry-before-invoke","entry-after-stop","locale-batch-before","locale-static-locks-returned","locale-default-returned","locale-mainargs-before","locale-parser-sizing-returned","locale-parser-output-before","locale-parser-output-returned","locale-builder-returned","locale-batch-cleaned","final","retry-after"};
 if(std::find(std::begin(kept),std::end(kept),selected)==std::end(kept))return;
''' + marker)
    (out / 'observations.hpp').write_text(observations)
    for path in out.iterdir():
        if path.is_file():
            pin(path)
    closure = verify_manifest(files)
    report = dict(passed=True, schema='mw34-locale-batch-independent-fixture-v1',
                  preparation_path=str(prep), preparation_sha256=expected_sha,
                  ordinary_rows_per_level=6, control_rows_per_level=6,
                  native_stages_per_level=6, source_bodies_modified=False,
                  binding_sources_modified=False, native_executed=False,
                  source_api_response_injection=False, State_reseed_after_writer=False,
                  direct_capture_from_first_native_run=True, files=files,
                  current_physical_closure=closure,
                  scope='Fresh independent main and host observers only; original source, bridge and API binding remain exact prepared bytes')
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True, report_sha256=sha_file(out/'report.json'))))

if __name__ == '__main__':
    main(*sys.argv[1:])
