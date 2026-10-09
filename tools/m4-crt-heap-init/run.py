"""Root-owned x64 execution, timed stages and externally bound capture bundles."""
import json
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

BASE = ROOT / 'reports/m4-crt-heap-init'
BASELINE_SHA = '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e'

def main(build_path, build_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != BASE:
        raise ValueError('Fresh root execution directory required')
    out.mkdir()
    started = time.perf_counter_ns()
    files, levels = {}, {}
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
        pin(ROOT / 'reports/m4-crt-locale-default-root/root-acceptance-r2/report.json', BASELINE_SHA)
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
                    if not value['passed'] or value['scenario'] != index or value['control'] != (0 if index < 24 else index + 85):
                        raise ValueError('Native declared row identity changed')
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
            seconds=(time.perf_counter_ns() - started) / 1e9)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'levels')}))

if __name__ == '__main__':
    main(*sys.argv[1:])
