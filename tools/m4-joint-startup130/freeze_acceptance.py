"""Freeze complete measured gates without granting startup inventory credit."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(specification, name):
    source = Path(specification).resolve()
    spec = importlib.util.spec_from_file_location(
        'acceptance130', Path(__file__).with_name('acceptance.py'))
    acceptance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acceptance)
    rows = json.loads(source.read_text(encoding='utf-8-sig'),
                      object_pairs_hook=acceptance.unique_object)
    acceptance.need(set(rows) == acceptance.REQUIRED, 'Every required current gate')
    gates = {}
    for label, item in rows.items():
        acceptance.need(set(item) == {'path', 'equal'}, 'Exact specification row')
        path = ROOT / item['path']
        receipt = acceptance.read(path)
        acceptance.need(receipt['passed'] is True, 'Passed gate ' + label)
        acceptance.need(len(item['equal']) >= 2, 'Measured gate extent ' + label)
        for field, expected in item['equal'].items():
            actual = acceptance.extent_value(receipt, field)
            acceptance.need(type(actual) is type(expected) and actual == expected,
                            'Typed measured predicate ' + label + ':' + field)
        gates[label] = dict(path=path.relative_to(ROOT).as_posix(),
                           sha256=sha(path), equal=item['equal'])
    result = dict(gates=gates, extent=acceptance.EXTENT,
        bounded_scope={field: False for field in sorted(acceptance.BOUNDED)},
        configuration_source=str(Path(__file__).resolve()),
        configuration_source_sha256=sha(__file__),
        requirements_source=str(Path(__file__).with_name('requirements.py').resolve()),
        requirements_source_sha256=sha(Path(__file__).with_name('requirements.py')),
        review_specification=str(source), review_specification_sha256=sha(source))
    out = ROOT / 'reports/m4-joint-startup130-root' / name
    acceptance.need(not out.exists(), 'Fresh frozen configuration')
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(configuration=str(out), sha256=sha(out), gates=len(gates),
        predicates=sum(len(v['equal']) for v in gates.values()), initializer_credit=0)))


if __name__ == '__main__':
    main(*sys.argv[1:])
