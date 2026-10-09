"""Root-owned native execution with stage timings and explicit capture bundles."""
import json
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized
from paths import publish_bytes, workspace_path
from stages import run_stage, verify_stage

BUILD_SHA = '1868574163cdbce4491afe2217688ef549189f184e20549e31f68e44930fb1d5'
BASELINE_SHA = '47a7ee8c611c936cd74190903c8f2a306d6e713242e6b0f43263a6172b07cf35'


def main(directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT / 'reports/m4-crt-filename':
        raise ValueError('A fresh filename root execution directory is required')
    out.mkdir()
    started = time.perf_counter_ns()
    files = {}
    levels = {}
    passed = False
    native_stages_completed = 0

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        if digest is not None and actual != digest:
            raise ValueError('Input SHA changed: ' + str(path))
        key = normalized(str(path))
        if key in files and files[key] != actual:
            raise ValueError('Conflicting evidence binding: ' + key)
        files[key] = actual
        return path

    try:
        build_path = pin(ROOT / 'reports/m4-crt-filename/build-r7/build.json', BUILD_SHA)
        build = json.loads(build_path.read_text(encoding='utf-8-sig'))
        if not build['passed']:
            raise ValueError('A successful build is required')
        pin(ROOT / 'reports/m4-crt-mainargs/root-acceptance-r1/report.json', BASELINE_SHA)
        pin(build['preparation_path'], build['preparation_sha256'])
        prep_pins = pin(Path(build['preparation_path']).parent / 'pins.json',
            '4646d4d7f8d9c969b623a41527f0c0eb34394406f7a39d69f28f6751e062ca3a')
        for p, h in json.loads(prep_pins.read_text(encoding='utf-8'))['files'].items():
            pin(p, h)
        for category in ('sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
            for p, h in build[category].items():
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
            native_stage = out / ('run-' + level)
            value = run_stage(list(map(str, (worker, game, obj, provider, pack, before, tree))),
                native_stage, timeout_seconds=120, required_outputs=[tree / 'COMPLETE'], inputs=list(files))
            verify_stage(native_stage, pin(native_stage / 'stage.json') and sha_file(native_stage / 'stage.json'))
            if not value['passed'] or (tree / 'COMPLETE').read_bytes() != b'COMPLETE':
                raise ValueError('Native stage failed: ' + str(native_stage))
            native_stages_completed += 1
            bundle = out / (level + '.mwb')
            pack_stage = out / ('pack-' + level)
            packed = run_stage([sys.executable, str(ROOT / 'tools/m4-pipeline/capture_bundle.py'),
                'pack', str(tree), str(bundle)], pack_stage, timeout_seconds=120,
                required_outputs=[bundle], inputs=list(files))
            verify_stage(pack_stage, pin(pack_stage / 'stage.json') and sha_file(pack_stage / 'stage.json'))
            if not packed['passed']:
                raise ValueError('Bundle stage failed: ' + str(pack_stage))
            digest = sha_file(pin(bundle))
            with CaptureBundle(bundle, digest) as reader:
                if reader.read_bytes('COMPLETE') != b'COMPLETE':
                    raise ValueError('Bundled completion marker changed')
                for i in range(36):
                    result = json.loads(reader.read_bytes(f'row-{i}/result.json'))
                    if not result['passed'] or result['scenario'] != i or result['control'] != (0 if i < 24 else i + 37):
                        raise ValueError('Bundled native row identity changed')
                count = len(reader.names())
            for stage in (native_stage, pack_stage):
                for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
                    pin(stage / name)
            levels[level] = dict(worker=str(worker), bundle=str(bundle), bundle_sha256=digest,
                logical_files=count, native_stage=str(native_stage), pack_stage=str(pack_stage),
                native_seconds=value['elapsed_seconds'], pack_seconds=packed['elapsed_seconds'])
        for p, h in files.items():
            if sha_file(p) != h:
                raise ValueError('Evidence changed during execution: ' + p)
        passed = True
    except Exception:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode('utf-8'))
        raise
    finally:
        report = dict(passed=passed, format='mw34.filename.root-execution.v1',
            build_path=str(ROOT / 'reports/m4-crt-filename/build-r7/build.json'), build_sha256=BUILD_SHA,
            native_executed_by_root=native_stages_completed > 0,
            native_stages_completed=native_stages_completed, original_executed=False, game_launched=False,
            positive_cases=48 if passed else 0, causal_controls=24 if passed else 0,
            API_capacity_units=8 if passed else 0, levels=levels, files=files,
            seconds=(time.perf_counter_ns() - started) / 1e9,
            capture_transport='Strict externally SHA-bound bundles; flat writer captures retained unchanged',
            whole_M4_complete=False)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'levels')}))


if __name__ == '__main__':
    main(sys.argv[1])
