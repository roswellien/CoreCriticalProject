"""Remove inherited CRT FS observers from the original-only trace worker."""
from pathlib import Path
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
B = R/'reports/m4-hypot-original'

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main(name):
    parent = B/'trace-preparation-r5'
    out = B/name
    assert not out.exists()
    pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve()
        identity = sha(path)
        assert expected is None or identity == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == identity
        pins[str(path)] = identity
        return path
    report_path = pin(parent/'report.json', '0431e475a5e7f11be98fafe2adcff2503f4f5882592f760ccee632d651b1ced8')
    old = json.loads(report_path.read_bytes())
    assert old['passed'] and not old['original_executed']
    for path, expected in old['files'].items():
        pin(path, expected)
    rows = json.loads(pin(parent/'trace-instruction-contracts.json').read_bytes())['instructions']
    fs = json.loads(pin(parent/'fs-hook-bindings.json').read_bytes())
    overlapping = [hook for hook in fs if any(hook['PC'] <= row['pc'] <
                   hook['PC'] + len(bytes.fromhex(hook['raw_bytes'])) for row in rows)]
    assert [hook['PC'] for hook in overlapping] == [0x7800139f, 0x780013a6, 0x78001419]
    assert len(fs) == 45
    out.mkdir()
    for path in parent.iterdir():
        if path.name not in ('report.json', 'pins.json'):
            (out/path.name).write_bytes(pin(path).read_bytes())
    path = out/'reference.cpp'
    text = path.read_text()
    for hook in overlapping:
        fragment = ('{' + hex(hook['PC']) + ',' + str(len(bytes.fromhex(hook['raw_bytes']))) +
                    ',' + str(hook['kind']) + ',&' + hook['declared_observer'] + ',{' +
                    ','.join(hex(value) for value in bytes.fromhex(hook['raw_bytes'])) + '}}')
        assert text.count(fragment+',') == 1
        text = text.replace(fragment+',', '')
    assert text.count('const std::array<FsHook,45> fs_hooks') == 1
    text = text.replace('const std::array<FsHook,45> fs_hooks', 'const std::array<FsHook,42> fs_hooks')
    path.write_text(text)
    live = [hook for hook in fs if hook not in overlapping]
    assert len(live) == 42 and not any(hook['PC'] <= row['pc'] <
           hook['PC'] + len(bytes.fromhex(hook['raw_bytes'])) for hook in live for row in rows)
    (out/'fs-hook-bindings.json').write_text(json.dumps(live, indent=2)+'\n')
    (out/'removed-trace-overlaps.json').write_text(json.dumps(dict(
        removed=overlapping, original_hook_count=45, retained_hook_count=42,
        reason='Full physical source instructions must remain unpatched for the tracer',
        guest_source_bytes_changed=False, descriptor_changes=0), indent=2)+'\n')
    pin(__file__)
    pin(sys.executable)
    for path in out.iterdir():
        pin(path)
    report = dict(old, previous_trace_preparation_sha256=sha(report_path),
                  removed_inherited_CRT_FS_hooks=3, active_FS_hooks=42,
                  trace_source_hook_overlaps=0, original_executed=False, files=pins)
    path = out/'report.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    pin(path)
    (out/'pins.json').write_text(json.dumps(dict(files=pins), indent=2)+'\n')
    print(json.dumps(dict(passed=True, sha256=sha(path))))

if __name__ == '__main__':
    main(sys.argv[1])
