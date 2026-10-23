"""ROOT-only closure preparation for32 bounded controls, no model imports."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir();files={};deferred={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 oldpath=pin(R/'reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json');old=json.loads(oldpath.read_bytes());assert old['passed']and old['program_rows']==7389 and old['callback_sites']==415
 # The prior proof is a finite recursive54 source-program closure, not a cached
 # control outcome. Rehash each ordinary dependency physically; archive identities
 # are explicitly deferred and can never enter control admission.
 for p,h in old['files'].items():
  q=Path(p)
  if q.suffix.lower()in('.mwb','.mwi','.zip')or q.name=='transport.json':deferred[p]=h
  else:pin(q,h)
 for p in old['modules']:pin(p)
 for rel in ['tools/m4-original141-source/source_controls141_v1.py','tools/m4-original141-source/derive_source141_v1.py','tools/m4-original141-source/game_model141_v1.py','tools/m4-original141-source/observer_shadow141_v1.py','tools/m4-startup138-paired/registry_backing_policy.py','reports/m4-original141/PUSHFD-preparation-r2/spec.json','reports/m4-138-validation-review/constructor-original18-source-r4/original-0-4260848/input.json','reports/m4-original141-source/controls-preparation-r1/report.json']:pin(R/rel)
 assert files[str(R/'reports/m4-original141/PUSHFD-preparation-r2/spec.json')]=='da8a35a834970303ef3ded3465c0cb82d548761dfcded82e40b282563cf7b215'
 pin(__file__);q=out/'required-ordinary-files.json';q.write_text(json.dumps(files,indent=2)+'\n');digest=sha(q)
 recipe='ROOT independently reviews the complete closure and physically rehashes required-ordinary-files.json before imports. Scope original141_bounded_source_controls. Call source_controls141_v1.controls with a pin refusing every non-admitted external read; set sys.dont_write_bytecode before imports and enforce all project open reads through admission. Final whole map rehash. Expected32 controls:22 current computed PUSHFD source-store checks,6 stack/API causality controls,4 source registry adverses. No original141 endpoint evidence, source replay, capture reader, accepted credit.\n'
 (out/'ROOT-recipe.txt').write_text(recipe)
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_opened=False,control_fixture_original141_input=False,expected_controls=32,required_ordinary_filemap_sha256=digest,required_ordinary_files=str(out/'required-ordinary-files.json'),deferred_capture_identities=deferred,files={str(oldpath):sha(oldpath),str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(out/'required-ordinary-files.json'):digest,str(out/'ROOT-recipe.txt'):sha(out/'ROOT-recipe.txt')}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
