"""Freeze an explicit120 review contract from named, passed receipt identities."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(role_map,name):
 roles=json.loads(Path(role_map).read_bytes())
 old=json.loads((ROOT/'reports/m4-joint-startup116-root/review-specification-r1.json').read_bytes())
 spec={k:old[k] for k in ('provider_lifts','geometry','allocation_interface','loader_identity')}
 for label,item in roles.items():
  assert set(item)=={'path','sha256','equal'},label
  assert label not in spec,label
  path=ROOT/item['path'];report=json.loads(path.read_bytes())
  assert report['passed'] is True and sha(path)==item['sha256'],label
  assert item['equal'] and item['equal'].get('passed') is True,label
  for field,expected in item['equal'].items():
   actual=report
   for key in field.split('.'):actual=actual[key]
   assert actual==expected,(label,field,actual,expected)
  spec[label]=item
 import importlib.util
 module=importlib.util.spec_from_file_location('accept120',Path(__file__).with_name('accept.py'))
 acceptance=importlib.util.module_from_spec(module);module.loader.exec_module(acceptance)
 assert set(spec)==acceptance.REQUIRED
 out=ROOT/'reports/m4-joint-startup120-root'/name;assert not out.exists()
 out.write_text(json.dumps(spec,indent=2)+'\n')
 print(json.dumps(dict(path=str(out),sha256=sha(out),gates=len(spec),predicates=sum(len(v['equal']) for v in spec.values()))))

if __name__=='__main__':main(*sys.argv[1:])
