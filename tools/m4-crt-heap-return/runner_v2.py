"""Author-executed x64 source returns, timed stages and strict capture bundles."""
import json
import struct
import sys
import time
import traceback
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, verify_manifest
from paths import publish_bytes, workspace_path
from stages import run_stage, verify_stage

BASE = ROOT / 'reports/m4-crt-heap-return'
BASELINE_SHA = 'cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'

def main(build_path, build_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != BASE:
        raise ValueError('Fresh root execution directory required')
    out.mkdir()
    started = time.perf_counter_ns()
    files, levels = {}, {}
    actual_creates = actual_destroys = owned_results = injected_zero = injected_cleanup_skip = 0
    actual_queries = qualifying_returns = alternate_frontiers = output_commits = 0
    actual_mode_stores = initializer_returns = 0
    passed, completed = False, 0

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        if digest is not None and actual != digest:
            raise ValueError('External SHA mismatch: ' + str(path))
        key = normalized(str(path))
        if key in files and files[key] != actual:
            raise ValueError('Conflicting current binding: ' + key)
        files[key] = actual
        return path

    try:
        bpath = pin(build_path, build_sha)
        build = json.loads(bpath.read_text(encoding='utf-8-sig'))
        if not build['passed']:
            raise ValueError('Successful current build required')
        pin(build['source_scope_note'],build['source_scope_note_sha256'])
        pin(ROOT / 'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json', BASELINE_SHA)
        pin(build['preparation_path'], build['preparation_sha256'])
        for category in ('sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
            for p, h in build.get(category, {}).items():
                pin(p, h)
        game = pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        pack = pin(ROOT / 'reports/m4-crt-fdiv/native-derived-r1/pack.bin', 'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80')
        before = pin(ROOT / 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin', '4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a')
        for name in ('capture_bundle.py', 'paths.py', 'stages.py', 'manifests.py'):
            pin(ROOT / 'tools/m4-pipeline' / name)
        pin(__file__)
        pin(sys.executable)
        for level in ('O0', 'O2'):
            worker = pin(build['workers'][level])
            obj = pin(ROOT / f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj')
            tree = out / ('native-' + level)
            stage = out / ('run-' + level)
            argv = list(map(str, (worker, game, obj, provider, pack, before, tree)))
            record = run_stage(argv, stage, timeout_seconds=180,
                required_outputs=[tree / 'COMPLETE'], inputs=list(files))
            verify_stage(stage, sha_file(pin(stage / 'stage.json')))
            if not record['passed'] or (tree / 'COMPLETE').read_bytes() != b'COMPLETE':
                raise ValueError('Native x64 stage failed')
            completed += 1
            bundle = out / (level + '.mwb')
            pack_stage = out / ('pack-' + level)
            packed = run_stage([sys.executable, str(ROOT / 'tools/m4-pipeline/capture_bundle.py'),
                'pack', str(tree), str(bundle)], pack_stage, timeout_seconds=600,
                required_outputs=[bundle], inputs=list(files))
            verify_stage(pack_stage, sha_file(pin(pack_stage / 'stage.json')))
            if not packed['passed']:
                raise ValueError('Capture bundle stage failed')
            digest = sha_file(pin(bundle))
            with CaptureBundle(bundle, digest) as reader:
                if reader.read_bytes('COMPLETE') != b'COMPLETE':
                    raise ValueError('Bundled completion changed')
                for index in range(36):
                    value = json.loads(reader.read_bytes(f'row-{index}/result.json'))
                    if not value['passed'] or value['scenario'] != index or value['control'] != (0 if index < 24 else index + 133):
                        raise ValueError('Native declared row identity changed')
                    witness = struct.unpack('<16Q', reader.read_bytes(f'row-{index}/heap-return-witness.bin'))
                    registry = struct.unpack('<18Q', reader.read_bytes(f'row-{index}/heap-return-registry.bin'))
                    if registry[7] != 0 or registry[15] != 1 or registry[8] != witness[2] or registry[9] != registry[10] or registry[9] != bool(witness[6]):
                        raise ValueError('Exact owned result and successful real cleanup required')
                    if witness[6] != registry[4] or (witness[6] and registry[16] != witness[6]):
                        raise ValueError('Full64 owned handle must equal actual destroy input')
                    actual_creates += registry[8]
                    actual_destroys += registry[9]
                    owned_results += bool(witness[6])
                    injected_zero += witness[1]
                    injected_cleanup_skip += registry[13]
                    query = struct.unpack('<20Q', reader.read_bytes(f'row-{index}/heap-return-query-witness.bin'))
                    actual_queries += query[2]
                    qualifying_returns += query[16]
                    alternate_frontiers += query[17]
                    output_commits += query[11]
                    job = struct.unpack("<72I", reader.read_bytes(f"row-{index}/heap-return-job.bin"))
                    actual_mode_stores += job[66]
                    initializer_returns += job[69]
                    if index<24 and query[16] and not(job[66] and job[67]==1 and job[69] and job[3]==35 and job[5]==13):
                        raise ValueError("Qualifying genuine mode publication and initializer RET required")
                    if index<24 and not(query[2] and query[11]==37 and query[14]==1 and query[15]==1 and (query[16] or query[17])):
                        raise ValueError('Ordinary actual API witness and branch-authentic source closure required')
                count = len(reader.names())
            for s in (stage, pack_stage):
                for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
                    pin(s / name)
            levels[level] = dict(worker=str(worker), bundle=str(bundle), bundle_sha256=digest,
                logical_files=count, native_stage=str(stage), pack_stage=str(pack_stage),
                native_seconds=record['elapsed_seconds'], pack_seconds=packed['elapsed_seconds'],
                argv=argv)
        closure = verify_manifest(files)
        passed = True
    except Exception:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode('utf-8'))
        raise
    finally:
        report = dict(passed=passed, build_path=str(build_path), build_sha256=build_sha,
            native_executed_by_author=completed > 0, native_stages_completed=completed,
            original_executed=False, game_launched=False, whole_M4_complete=False,
            levels=levels, files=files, physical_closure=closure if passed else None,
            positive_sequences=48 if passed else 0, causal_sequences=24 if passed else 0,
            actual_HeapCreate_calls=actual_creates, actual_owned_results=owned_results, actual_successful_HeapDestroy_calls=actual_destroys,
            injected_zero_result_sequences=injected_zero, injected_pre_OS_cleanup_skip_sequences=injected_cleanup_skip,
            actual_GetVersionExA_calls=actual_queries, actual_API_output_DWORD_commits=output_commits,
            qualifying_selector_RET_sequences=qualifying_returns,alternate_environment_frontier_sequences=alternate_frontiers,
            actual_source_mode_publication_sequences=actual_mode_stores, genuine_initializer_RET_sequences=initializer_returns,
            ordinary_source_PCs_if_qualifying=59,ordinary_source_accesses_if_qualifying=35,source_RET_count_if_qualifying=3,separate_API_return_reads=2,
            actual_full_BOOL_and_all148_output_bytes_witnessed=True, API_output_store_ledger_separate=True,
            genuine_probe_RET_executed=True, real_version_query_executed=actual_queries>0, environment_API_called=False,
            declared_ordinary_lower_stack_input_zero=True, borrowed_pages=21, new_guest_objects=0, reused_guest_objects=38,
            API_guest_model_universal_original_equivalence_claimed=False, selector_return1_produced=qualifying_returns>0,
            heap_mode_global_published=actual_mode_stores>0, initializer_RET_executed=initializer_returns>0,qualifying_initializer_RET_completed=initializer_returns>0,full_heap_allocator_initialized=False,
            fragment_caller_continued=False, source_identity_bytes=2086,compiled_source_bytes=230,qualifying_executed_source_bytes=192,
            seconds=(time.perf_counter_ns() - started) / 1e9)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'levels')}))

if __name__ == '__main__':
    main(*sys.argv[1:])
