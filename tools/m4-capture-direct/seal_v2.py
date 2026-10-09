"""Seal compact transport proof and preserved failures, without native reruns."""
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import verify_manifest
from paths import publish_bytes, workspace_path

def need(ok, why):
    if not ok:
        raise ValueError(why)

def main(directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == ROOT / 'reports/m4-capture-direct' and not out.exists(), 'Fresh transport seal')
    files = {}
    def pin(path, expected=None):
        path = Path(path).absolute()
        digest = sha_file(path)
        need(expected is None or digest == expected, 'Exact sealed identity')
        files[str(path)] = digest
        return path
    controls_path = pin(ROOT / 'reports/m4-capture-direct/controls-r3/report.json')
    controls = json.loads(controls_path.read_bytes())
    need(controls['passed'] and controls['hardware_pairs'] == 108 and controls['refusals'] == 54,
         'Actual checked transport evidence')
    for name, digest in controls['files'].items():
        pin(name, digest)
    pin(Path(__file__))
    pin(ROOT / 'tools/m4-capture-direct/README.md')
    histories = []
    for revision in ('controls-r1', 'controls-r2'):
        folder = ROOT / 'reports/m4-capture-direct' / revision
        refusal = pin(folder / 'refusal.json')
        stage = pin(folder / 'stage-O0/stage.json')
        stderr = pin(folder / 'stage-O0/stderr.bin')
        stdout = pin(folder / 'stage-O0/stdout.bin')
        raw = pin(folder / 'O0/hardware.bin')
        need(not json.loads(stage.read_bytes())['passed'] and b'ENV28' in stderr.read_bytes(),
             'Preserved original strict hardware refusal')
        histories.append(dict(receipt=str(refusal), sha256=files[str(refusal)],
                              stage=str(stage), stage_sha256=files[str(stage)],
                              raw=str(raw), raw_sha256=files[str(raw)],
                              raw_pairs=raw.stat().st_size // 1128,
                              success_credit=False))
    # Preserve superseded compiled snapshots by receipt identity, without claiming
    # their source-path maps remain the current compile closure.
    for revision in ('build-r1', 'build-r2', 'build-r3', 'controls-build-r2', 'controls-build-r3'):
        pin(ROOT / 'reports/m4-capture-direct' / revision / 'build.json')
    pin(ROOT / 'reports/m4-capture-direct/sealed-r1/report.json')
    raw_checks = 0
    for level in controls['levels']:
        path = ROOT / 'reports/m4-capture-direct/controls-r3' / level / 'hardware.bin'
        blob = path.read_bytes()
        need(len(blob) == 54 * 1128, 'Actual complete fixed-width raw samples')
        for offset in range(0, len(blob), 1128):
            before, after = blob[offset:offset+560], blob[offset+560:offset+1120]
            first, last = struct.unpack_from('<II', blob, offset+1120)
            need(first == last == 0x734612ab, 'Independent actual LastError equality')
            need(before[512:540] == after[512:540] and any(before[524:532]), 'Independent rich full ENV28 equality')
            need(before[:5] == after[:5] and before[24:28] == after[24:28], 'Independent CW/SW/FTW/MXCSR equality')
            for i in range(8):
                need(before[32+16*i:42+16*i] == after[32+16*i:42+16*i], 'Independent physical raw80 equality')
            for i in range(6, 16):
                need(before[160+16*i:176+16*i] == after[160+16*i:176+16*i], 'Independent actual nonvolatile SIMD equality')
            need((struct.unpack_from('<Q',before,544)[0] ^ struct.unpack_from('<Q',after,544)[0]) & 0x400 == 0,
                 'Independent ABI DF equality')
            raw_checks += 22
    out.mkdir(parents=True)
    report = dict(passed=True, transport_only=True, native_rerun=False, game_semantic_credit=False,
                  controls_path=str(controls_path), controls_sha256=files[str(controls_path)],
                  canonical_build=str(ROOT / 'reports/m4-capture-direct/build-r4/build.json'),
                  canonical_build_sha256=files[str(ROOT / 'reports/m4-capture-direct/build-r4/build.json')],
                  hardware_pairs=108, hardware_raw_comparisons=raw_checks,
                  refusals=54, default_limit_records=400002, native_checks=controls['native_checks'],
                  failures=histories,
                  failure_explanation='Throwing convenience paths propagate C++ exceptions after assembly restoration; caller exception handling changed legacy ENV instruction fields. Checked API catches within protected body, reports status, preserves strict checks and is the canonical production API.',
                  current_physical_closure=verify_manifest(files), files=files)
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'failures')}))

if __name__ == '__main__':
    main(*sys.argv[1:])
