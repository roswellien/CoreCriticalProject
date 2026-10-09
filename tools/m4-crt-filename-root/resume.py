"""Preserve a successful O0 execution after timed-out legacy capture conversion."""
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

PREVIOUS_SHA = 'f7bbfb1cc67db8c4283c3012cf07f121f5f287ec471d02e272bd79950073a4f4'


def main(directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT / 'reports/m4-crt-filename':
        raise ValueError('Fresh root execution recovery output required')
    out.mkdir()
    started = time.perf_counter_ns()
    previous_path = ROOT / 'reports/m4-crt-filename/root-execution-r1/report.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8'))
    files, levels = {}, {}
    passed = False

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        if digest is not None and actual != digest:
            raise ValueError('Recovery input SHA mismatch: ' + str(path))
        key = normalized(str(path))
        if key in files and files[key] != actual:
            raise ValueError('Conflicting recovery binding')
        files[key] = actual
        return path

    try:
        pin(previous_path, PREVIOUS_SHA)
        if previous['passed'] or previous['native_stages_completed'] != 1:
            raise ValueError('Expected the preserved O0 pass and failed transport attempt')
        for p, h in previous['files'].items():
            pin(p, h)
        pin(__file__)
        pin(sys.executable)
        build_path = pin(previous['build_path'], previous['build_sha256'])
        build = json.loads(build_path.read_text(encoding='utf-8-sig'))
        for level in ('O0', 'O2'):
            worker = pin(build['workers'][level])
            if level == 'O0':
                tree = previous_path.parent / 'native-O0'
                native_stage = previous_path.parent / 'run-O0'
                verify_stage(native_stage, files[normalized(str(native_stage / 'stage.json'))])
                value = json.loads((native_stage / 'stage.json').read_text(encoding='utf-8'))
                if not value['passed'] or value['argv'][0] != str(worker) or value['argv'][-1] != str(tree):
                    raise ValueError('Preserved native stage association changed')
                adopted = True
            else:
                tree, native_stage = out / 'native-O2', out / 'run-O2'
                obj = pin(ROOT / 'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj')
                argv = list(map(str, (worker, ROOT / 'MW3/Mech3.exe', obj,
                    ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
                    ROOT / 'reports/m4-crt-fdiv/native-derived-r1/pack.bin',
                    ROOT / 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin', tree)))
                value = run_stage(argv, native_stage, timeout_seconds=120,
                    required_outputs=[tree / 'COMPLETE'], inputs=list(files))
                verify_stage(native_stage, pin(native_stage / 'stage.json') and sha_file(native_stage / 'stage.json'))
                adopted = False
            if not value['passed'] or (tree / 'COMPLETE').read_bytes() != b'COMPLETE':
                raise ValueError('Required native stage did not pass')
            bundle, pack_stage = out / (level + '.mwb'), out / ('pack-' + level)
            packed = run_stage([sys.executable, str(ROOT / 'tools/m4-pipeline/capture_bundle.py'),
                'pack', str(tree), str(bundle)], pack_stage, timeout_seconds=600,
                required_outputs=[bundle], inputs=list(files))
            verify_stage(pack_stage, pin(pack_stage / 'stage.json') and sha_file(pack_stage / 'stage.json'))
            if not packed['passed']:
                raise ValueError('Required conversion did not pass')
            digest = sha_file(pin(bundle))
            with CaptureBundle(bundle, digest) as reader:
                if reader.read_bytes('COMPLETE') != b'COMPLETE':
                    raise ValueError('Bundled completion marker changed')
                for i in range(36):
                    row = json.loads(reader.read_bytes(f'row-{i}/result.json'))
                    if not row['passed'] or row['scenario'] != i or row['control'] != (0 if i < 24 else i + 37):
                        raise ValueError('Native row identity changed')
                count = len(reader.names())
            for stage in (native_stage, pack_stage):
                for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
                    pin(stage / name)
            levels[level] = dict(worker=str(worker), bundle=str(bundle), bundle_sha256=digest,
                logical_files=count, native_stage=str(native_stage), pack_stage=str(pack_stage),
                native_seconds=value['elapsed_seconds'], pack_seconds=packed['elapsed_seconds'],
                adopted_successful_root_stage=adopted, flat_capture_directory=str(tree))
        closure = verify_manifest(files)
        passed = True
    except Exception:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode('utf-8'))
        raise
    finally:
        report = dict(passed=passed, format='mw34.filename.root-execution.v1',
            build_path=previous['build_path'], build_sha256=previous['build_sha256'],
            native_executed_by_root=bool(levels), original_executed=False, game_launched=False,
            positive_cases=48 if passed else 0, causal_controls=24 if passed else 0,
            API_capacity_units=8 if passed else 0, levels=levels, files=files,
            physical_closure=closure if passed else None, seconds=(time.perf_counter_ns() - started) / 1e9,
            preserved_failure_path=str(previous_path), preserved_failure_sha256=PREVIOUS_SHA,
            recovery='Reuse the verified completed O0 native stage; fresh O2 native stage and two fresh bundles',
            whole_M4_complete=False)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'levels')}))


if __name__ == '__main__':
    main(sys.argv[1])
