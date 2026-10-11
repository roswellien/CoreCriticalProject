"""Clone formatting4 and fix binding publication order on poisoned cleanup."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / 'reports/m4-formatting-native/preparation-r18'
PARENT_SHA = '68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06'
COSINE = ROOT / 'reports/m4-cosine-native/runtime-fixture-preparation-r4/registry/session_impl.inc'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = ROOT / 'reports/m4-formatting-native' / name
    assert not out.exists()
    out.mkdir(parents=True)
    assert sha(PARENT / 'report.json') == PARENT_SHA
    parent = json.loads((PARENT / 'report.json').read_bytes())
    assert parent['passed'] and parent['live_owner_bound'] == 92
    original = (PARENT / 'session_impl.inc').read_text()
    before = '  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();\n  try{\n   if(r.poisoned())poison();'
    after = '  if(r.poisoned()&&!failed)poison();\n  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();\n  try{'
    assert original.count(before) == 1
    corrected = original.replace(before, after)
    cosine = COSINE.read_text()
    assert cosine.count(after) == 1
    assert corrected.count('if(r.poisoned()&&!failed)poison();') == 1
    assert corrected.replace(after, before) == original
    files = dict(parent['files'])
    files[str((PARENT / 'report.json').resolve())] = PARENT_SHA
    files[str(COSINE.resolve())] = sha(COSINE)
    files[str(Path(__file__).resolve())] = sha(__file__)
    copied = {}
    for path in PARENT.iterdir():
        if path.is_file() and path.suffix in ('.cpp', '.hpp', '.inc', '.json') and path.name != 'report.json':
            expected = parent['files'][str(path.resolve())]
            assert sha(path) == expected
            destination = out / path.name
            if path.name == 'session_impl.inc':
                destination.write_text(corrected)
            else:
                destination.write_bytes(path.read_bytes())
                assert sha(destination) == expected
            files[str(destination.resolve())] = sha(destination)
            copied[path.name] = dict(before_sha256=expected, after_sha256=sha(destination),
                                     byte_identical=sha(destination) == expected)
    assert [name for name, relation in copied.items() if not relation['byte_identical']] == ['session_impl.inc']

    def remap(value):
        if isinstance(value, dict):
            return {key: remap(item) for key, item in value.items()}
        if isinstance(value, list):
            return [remap(item) for item in value]
        if isinstance(value, str):
            for old, new in [(str(PARENT.resolve()), str(out.resolve())),
                             (PARENT.as_posix(), out.as_posix())]:
                if value.startswith(old + ('/' if '/' in old else '\\')):
                    return new + value[len(old):]
        return value

    report = remap(parent)
    report.update(
        scope='Unexecuted formatting4 composition with exact corrected poisoned cleanup transition; actual controls and full130 rerun required',
        parent_preparation=str(PARENT / 'report.json'), parent_preparation_sha256=PARENT_SHA,
        native_library=str(out / 'registry_library.cpp'), native_include=str(out),
        files=files, cleanup_source_relations=copied,
        external_Runtime_poison_cleanup=True,
        cleanup_poison_before_boundary_and_binding_publication=True,
        cleanup_first_fault_preserved=True,
        cleanup_transition_matches_passed_cosine_fixture4=True,
        literal_objects_changed=False, normal_source_bodies_changed=False,
        native_executed=False, source_or_native_executed=False, initializer_credit=0,
    )
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(out / 'report.json'),
                          copied_files=len(copied), changed_files=1, native_executed=False)))


if __name__ == '__main__':
    main(sys.argv[1])
