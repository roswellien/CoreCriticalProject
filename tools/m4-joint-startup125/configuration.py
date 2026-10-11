"""Freeze successful measured125 gates without granting initializer credit."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()

def main(specification, name):
    source = Path(specification).resolve(); rows = json.loads(source.read_bytes())
    spec = importlib.util.spec_from_file_location('accept125', Path(__file__).with_name('accept.py'))
    acceptance = importlib.util.module_from_spec(spec); spec.loader.exec_module(acceptance)
    assert set(rows) == acceptance.REQUIRED
    for label,item in rows.items():
        assert set(item) == {'path','sha256','equal'}
        path = ROOT / item['path']; report = json.loads(path.read_bytes())
        assert report['passed'] is True and sha(path) == item['sha256'], label
        assert len(item['equal']) >= 2, label
        for field,expected in item['equal'].items():
            actual = acceptance.extent_value(report,field); assert type(actual) is type(expected) and actual == expected, (label,field)
    result = dict(gates=rows, extent=acceptance.EXTENT, bounded_scope={k:False for k in sorted(acceptance.BOUNDED)}, configuration_source=str(Path(__file__).resolve()), configuration_source_sha256=sha(__file__), review_specification=str(source), review_specification_sha256=sha(source))
    out = ROOT / 'reports/m4-joint-startup125-root' / name; assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(configuration=str(out), sha256=sha(out), gates=len(rows))))

if __name__ == '__main__': main(*sys.argv[1:])
