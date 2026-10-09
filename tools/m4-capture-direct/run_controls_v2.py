"""Targeted actual transport controls; no game or original source execution."""
import hashlib
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import verify_manifest
from paths import publish_bytes, workspace_path
from stages import run_stage, verify_stage

def need(ok, why):
    if not ok:
        raise ValueError(why)

def main(directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == ROOT / 'reports/m4-capture-direct' and not out.exists(), 'Fresh direct control receipt')
    build_path = ROOT / 'reports/m4-capture-direct/controls-build-r3/build.json'
    build = json.loads(build_path.read_bytes())
    need(build['passed'] and not build['native_executed'], 'Frozen compiled controls')
    files = {}
    def pin(path, expected=None):
        path = Path(path).absolute()
        digest = sha_file(path)
        need(expected is None or digest == expected, 'Exact content identity: ' + str(path))
        files[str(path)] = digest
        return path
    pin(build_path)
    pin(Path(__file__))
    pin(Path(sys.executable))
    for mapping in ('sources', 'tools', 'artifacts', 'compiler_read_headers'):
        for name, digest in build[mapping].items():
            pin(name, digest)
    primary = pin(build['primary_build'], build['primary_sha256'])
    frozen = json.loads(primary.read_bytes())
    for mapping in ('sources', 'tools', 'artifacts', 'objects', 'libraries', 'compiler_read_headers'):
        for name, digest in frozen[mapping].items():
            pin(name, digest)
    for name in ('capture_bundle.py', 'paths.py', 'manifests.py', 'stages.py'):
        pin(ROOT / 'tools/m4-pipeline' / name)
    # Historical failed build wrapper is retained by direct identity; its current
    # source paths are intentionally not expanded into the success closure.
    history = pin(ROOT / 'reports/m4-capture-direct/controls-build-r1/build.json')
    out.mkdir(parents=True)
    levels = {}
    try:
        for level in ('O0', 'O2'):
            driver = pin(build['workers'][level])
            target, stage = out / level, out / ('stage-' + level)
            result = run_stage([str(driver), str(target)], stage, timeout_seconds=180,
                               inputs=[driver, build_path, primary])
            stage_digest = sha_file(stage / 'stage.json')
            need(verify_stage(stage, stage_digest)['recorded_stage_passed'], 'Actual control stage passed')
            need(result['passed'], 'Actual native transport control result')
            for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
                pin(stage / name)
            actual = json.loads((target / 'controls.json').read_bytes())
            need(actual['passed'] and actual['hardware_pairs'] == 47 and actual['refusals'] == 27 and
                 actual['default_limit_records'] == 200001, 'Measured bounded control counts')
            need((target / 'hardware.bin').stat().st_size == 47 * (2 * 560 + 8),
                 'Every actual hardware pair retained')
            need(not any(p.name.startswith('.') for p in target.iterdir()), 'No owned private debris')
            archives, unions, verify_seconds = [], {}, 0.0
            for directory in ('count-split', 'split-0', 'split-1', 'split-2', 'default-overflow'):
                folder = target / directory
                manifest = json.loads((folder / 'transport.json').read_bytes())
                names, payload = {}, 0
                need(manifest['passed'] and manifest['transport_only'] and not manifest['native_executed'],
                     'Only transport completion claimed')
                need(set(p.name for p in folder.iterdir()) == {'transport.json', *(p['bundle'] for p in manifest['parts'])},
                     'Compact exact physical inventory')
                for part in manifest['parts']:
                    path = folder / part['bundle']
                    need(sha_file(path) == part['sha256'] and path.stat().st_size == part['bundle_bytes'],
                         'Actual external archive identity')
                    started = time.perf_counter_ns()
                    with CaptureBundle(path, part['sha256']) as reader:
                        need(len(reader.names()) == part['logical_files'] <= 200000, 'Unchanged strict record bound')
                        measured_payload = 0
                        for name in reader.names():
                            need(name.lower() not in names, 'Global exact disjoint normalized logical union')
                            data = reader.read_bytes(name)
                            if directory == 'count-split':
                                need(data == (b'' if name == 'z/empty' else bytes(range(256))), 'Exact binary/empty bytes')
                            else:
                                need(data == (b'\x00\x01' if directory == 'split-0' else b''), 'Exact bounded control bytes')
                            names[name.lower()] = len(data)
                            measured_payload += len(data)
                        need(measured_payload == part['payload_bytes'], 'Actual payload extent')
                    verify_seconds += (time.perf_counter_ns() - started) / 1e9
                    payload += measured_payload
                    archives.append(dict(path=str(path), sha256=part['sha256'], logical_files=part['logical_files']))
                need(len(names) == manifest['logical_files'] and payload == manifest['payload_bytes'], 'Actual complete-set totals')
                expected = 200001 if directory == 'default-overflow' else 3
                need(len(names) == expected, 'No missing or duplicate records across parts')
                unions[directory] = dict(logical_files=len(names), payload_bytes=payload, parts=len(manifest['parts']))
            for path in target.rglob('*'):
                if path.is_file():
                    pin(path)
            levels[level] = dict(stage=str(stage), stage_sha256=stage_digest,
                                 native_seconds=result['elapsed_seconds'], verify_seconds=verify_seconds,
                                 actual=actual, archives=archives, unions=unions)
        report = dict(passed=True, transport_only=True, game_executed=False, native_transport_executed=True,
                      hardware_pairs=sum(v['actual']['hardware_pairs'] for v in levels.values()),
                      refusals=sum(v['actual']['refusals'] for v in levels.values()),
                      default_limit_records=sum(v['actual']['default_limit_records'] for v in levels.values()),
                      native_checks=sum(v['actual']['checks'] for v in levels.values()), levels=levels,
                      current_physical_closure=verify_manifest(files), files=files,
                      failure_history=dict(path=str(history), sha256=files[str(history)]),
                      performance_claim=False, volatile_XMM0_5_equality_claimed=False,
                      hardware_domain='Full ENV28/nonzero legacy witness, CW/SW/FTW, full raw80 x8, MXCSR, XMM6..15, ABI DF equality and caller LastError')
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'levels')}))
    except Exception as error:
        publish_bytes(out / 'refusal.json', (json.dumps(dict(passed=False, error=str(error), levels=levels,
                                                           files=files), indent=2) + '\n').encode())
        raise

if __name__ == '__main__':
    main(*sys.argv[1:])
