"""Run both finite occupied-stack probes with fixed current input identities."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'reports/m4-hypot-native'

def main(build_digest, name):
    out = BASE/name
    assert not out.exists()
    out.mkdir()
    pins, rows = {}, []
    def pin(path, expected=None):
        path = Path(path).resolve()
        with path.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        assert expected is None or digest == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == digest
        pins[str(path)] = digest
        return path
    passed = False
    try:
        path = pin(BASE/'control-build-r2/report.json', build_digest)
        build = json.loads(path.read_text(encoding='utf-8-sig'))
        assert build['passed'] and not build['native_executed']
        for path, digest in build['files'].items():
            pin(path, digest)
        inputs = pin(BASE/'inputs-r3/input-state.bin')
        before = inputs.read_bytes()
        assert len(before) == 6*580
        for level in ('O0', 'O2'):
            worker = pin(BASE/f'control-build-r2/control-{level}.exe')
            result = subprocess.run([str(worker), str(inputs)], capture_output=True,
                                    creationflags=0x08000000, timeout=30)
            for suffix, data in (('stdout', result.stdout), ('stderr', result.stderr)):
                path = out/f'{level}.{suffix}'
                path.write_bytes(data)
                pin(path)
            assert result.returncode == 0, (level, result.returncode, result.stderr.decode(errors='replace'))
            row = json.loads(result.stdout)
            assert row == dict(passed=True, hardware_cases=768, masked_only=True,
                               original_AFTER_seed=False, initializer_credit=0)
            rows.append(dict(level=level, **row))
        for path, digest in list(pins.items()):
            pin(path, digest)
        pin(__file__)
        pin(sys.executable)
        passed = True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Actual O0/O2 masked x87 control-transfer unit evidence, not literal helper equivalence',
                      build_sha256=build_digest, levels=rows,
                      total_hardware_cases=sum(row['hardware_cases'] for row in rows),
                      whole_State_bytes=3504, whole_guest_operand_backing_bytes=12,
                      hardware_x87_header_bytes=24, hardware_raw80_backings=8,
                      complete_legacy_ENV_bytes=28, SIMD_or_whole_caller_FX_claim=False,
                      source_dynamic_path_proven=False, full_native_helper_executed=False,
                      original_AFTER_seed=False, initializer_credit=0, files=pins)
        path = out/'report.json'
        path.write_text(json.dumps(report, indent=2)+'\n')
        with path.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        print(json.dumps(dict(passed=passed, sha256=digest, levels=rows)))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
