"""Run finite actual-command-line fixtures directly into strict native archives."""
import json
from pathlib import Path
import sys
import time
import traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized, verify_manifest
from paths import publish_bytes, workspace_path
from stages import run_stage, verify_stage
from transport import DirectSet, read, need

PATTERNS = [['simple'], ['has space', ''], ['a"b', 'tail\\'],
            ['\\\\\\"quote', 'two', 'three'], ['tab\tvalue', 'double  spaces'],
            ['\\\\end', 'paired "quote"', 'semi;literal']]

def main(build_path, build_sha, directory):
    start = time.perf_counter()
    out = workspace_path(directory, reports=True)
    need(out.parent == ROOT / 'reports/m4-crt-locale-batch-review' and not out.exists(), 'Fresh independent execution namespace')
    out.mkdir(parents=True)
    files, levels = {}, {}
    launched = completed = rows = 0
    passed = False
    closure = None
    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or digest == actual, 'Current native dependency: ' + str(path))
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Consistent physical dependency')
        files[key] = actual
        return path
    try:
        build = read(pin(build_path, build_sha))
        need(build['passed'] and not build['native_executed'], 'Passed source-only independent build')
        for category in ('sources', 'tools', 'entry_objects', 'libraries', 'compiler_read_headers', 'artifacts'):
            for path, digest in build[category].items():
                pin(path, digest)
        for path_key, sha_key in [('fixture_report', 'fixture_report_sha256'),
                                  ('author_build', 'author_build_sha256'),
                                  ('writer_build', 'writer_build_sha256')]:
            pin(build[path_key], build[sha_key])
        game = pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        pack = pin(ROOT / 'reports/m4-crt-fdiv/native-derived-r1/pack.bin', 'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80')
        before = pin(ROOT / 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin', '4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a')
        for path in (Path(__file__), Path(__file__).parent / 'transport.py', Path(sys.executable)):
            pin(path)
        for name in ('capture_bundle.py', 'paths.py', 'stages.py', 'manifests.py'):
            pin(ROOT / 'tools/m4-pipeline' / name)
        base_inputs = tuple(files)
        for level in ('O0', 'O2'):
            worker = pin(build['workers'][level])
            obj = pin(ROOT / f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj')
            invocations = []
            for selection, pattern in enumerate(PATTERNS):
                captures = out / f'native-{level}-{selection}'
                stage = out / f'run-{level}-{selection}'
                argv = list(map(str, (worker, game, obj, provider, pack, before, captures))) + [str(selection)] + pattern
                launched += 1
                result = run_stage(argv, stage, timeout_seconds=180,
                                   required_outputs=[captures / 'transport.json'],
                                   inputs=list(base_inputs) + [str(worker), str(obj)])
                stage_sha = sha_file(pin(stage / 'stage.json'))
                verify_stage(stage, stage_sha)
                for name in ('stdout.bin', 'stderr.bin'):
                    pin(stage / name)
                need(result['passed'], 'Actual native fixture completed: ' + level + '/' + str(selection))
                completed += 1
                verify_start = time.perf_counter()
                bundles = DirectSet(captures / 'transport.json', pin)
                try:
                    need(bundles.data('COMPLETE') == b'COMPLETE' and 'INCOMPLETE' not in bundles.entries and 'FAILURE.txt' not in bundles.entries,
                         'Whole two-row semantic corpus is complete')
                    summary = json.loads(bundles.data('review-controls.json'))
                    need(summary['passed'] and summary['rows'] == 2 and summary['ordinary_rows'] == 1
                         and summary['independent_control_rows'] == 1 and summary['selection'] == selection
                         and summary['actual_GetCommandLineA_input'] and not summary['API_response_injection']
                         and not summary['game_executed'], 'Finite measured-input fixture scope')
                    rows += summary['rows']
                    inventory = out / f'inventory-{level}-{selection}.json'
                    publish_bytes(inventory, (json.dumps({'files': dict(sorted(bundles.records.items()))}, indent=2)+'\n').encode())
                    pin(inventory)
                    invocations.append(dict(selection=selection, supplemental_argv=pattern,
                        worker=str(worker), argv=argv, native_stage=str(stage), native_stage_sha256=stage_sha,
                        transport_manifest=str(bundles.path), transport_sha256=sha_file(bundles.path),
                        inventory_path=str(inventory), inventory_sha256=sha_file(inventory),
                        logical_files=len(bundles.entries), payload_bytes=bundles.value['payload_bytes'],
                        archive_parts=len(bundles.bundles), native_and_emission_seconds=result['elapsed_seconds'],
                        emit_seconds=bundles.value['emit_seconds'], finalize_parts_seconds=bundles.value['finalize_parts_seconds'],
                        strict_verification_seconds=time.perf_counter()-verify_start,
                        compiled_checks=summary['checks'], wrong_thread_units=summary['wrong_thread_units']))
                finally:
                    bundles.close()
            levels[level] = dict(worker=str(worker), invocations=invocations)
        closure = verify_manifest(files)
        passed = True
    except BaseException:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode())
        raise
    finally:
        report = dict(passed=passed, scope='Finite independent whole-locale/argv fixtures; source/hardware admission remains separate',
                      build_path=str(Path(build_path).absolute()), build_sha256=build_sha,
                      native_executed=launched > 0, native_stages_completed=completed,
                      native_stages_launched=launched, native_rerun=False, native_scenarios=rows,
                      levels=levels, files=files, current_physical_closure=closure,
                      game_launched=False, original_executed=False, API_response_injection=False,
                      full_CRT_complete=False, whole_M4_complete=False,
                      per_record_physical_files=0, later_copy_or_pack_passes=0,
                      elapsed_seconds=time.perf_counter()-start)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2)+'\n').encode())
        print(json.dumps({key: value for key, value in report.items() if key not in ('files', 'levels')}))

if __name__ == '__main__':
    main(*sys.argv[1:])
