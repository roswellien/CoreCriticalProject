"""Freeze the finite control-transfer hardware probe, without execution credit."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main(name):
    out = ROOT/'reports/m4-hypot-native'/name
    assert not out.exists()
    pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve()
        digest = sha(path)
        assert expected is None or digest == expected, str(path)
        pins[str(path)] = digest
        return path
    inputs = pin(ROOT/'reports/m4-hypot-native/inputs-r3/report.json',
                 '46e04c33ef7ca4f8ddcf8e59a4ecb1e6189f1f0410ad635fd471538c5458125d')
    report = json.loads(inputs.read_bytes())
    assert report['passed'] and report['original_AFTER_bytes_seeded'] == 0
    for path, digest in report['files'].items():
        pin(path, digest)
    out.mkdir()
    for name in ('control_runtime.cpp', 'control_probe.cpp'):
        path = out/name
        path.write_bytes(pin(Path(__file__).with_name(name)).read_bytes())
        pin(path)
    pin(__file__)
    pin(sys.executable)
    report = dict(passed=True, scope='Fully masked native x87 control unit preparation; source helper equivalence remains separate',
                  source_state_input=str(ROOT/'reports/m4-hypot-native/inputs-r3/input-state.bin'),
                  genuine_CW_inputs=6, authored_occupied_counts=[0,1,4,8], authored_masked_PE_inputs=[0,1],
                  precision_encodings=4, rounding_modes=4, expected_hardware_cases=768,
                  original_AFTER_seed=False, native_executed=False, initializer_credit=0, files=pins)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=True, sha256=sha(out/'report.json'))))

if __name__ == '__main__':
    main(sys.argv[1])
