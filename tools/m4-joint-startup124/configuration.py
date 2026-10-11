"""Freeze measured exact124 gates without granting native initializer credit."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(specification,name):
 source=Path(specification).resolve();spec=json.loads(source.read_bytes())
 module=importlib.util.spec_from_file_location('accept124',Path(__file__).with_name('accept.py'))
 acceptance=importlib.util.module_from_spec(module);module.loader.exec_module(acceptance)
 assert set(spec)==acceptance.REQUIRED
 gates={}
 for label,item in spec.items():
  assert set(item)=={'path','sha256','equal'}
  path=(ROOT/item['path']).resolve();report=json.loads(path.read_bytes())
  assert report['passed'] is True and sha(path)==item['sha256'],label
  assert len(item['equal'])>=2,label
  for field,expected in item['equal'].items():
   assert acceptance.extent_value(report,field)==expected,(label,field,expected)
  gates[label]=dict(path=path.relative_to(ROOT).as_posix(),sha256=item['sha256'],equal=item['equal'])
 result=dict(gates=gates,extent=acceptance.EXTENT,bounded_scope={key:False for key in sorted(acceptance.BOUNDED)},configuration_source=str(Path(__file__).resolve()),configuration_source_sha256=sha(__file__),review_specification=str(source),review_specification_sha256=sha(source))
 out=ROOT/'reports/m4-joint-startup124-root'/name;assert not out.exists()
 out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(configuration=str(out),sha256=sha(out),gates=len(gates))))

if __name__=='__main__':main(*sys.argv[1:])
