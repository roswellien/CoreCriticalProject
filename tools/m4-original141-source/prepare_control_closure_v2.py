"""Conservative closed retained semantic/source dependency supplement.

ROOT executes preparation only after reviewing it. No imports or source runs;
this broadens input authentication, never response permissions or semantics.
"""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir();files={};deferred={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.is_relative_to(R)and p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def absorb(mapping):
  for p,h in mapping.items():
   q=Path(p).resolve()
   if not q.is_relative_to(R)or q.suffix.lower()in('.mwb','.mwi','.zip')or q.name=='transport.json':deferred[p]=h
   else:pin(q,h)
 base=pin(R/'reports/m4-original141-source/root-control-closure-r1/required-ordinary-files.json');absorb(json.loads(base.read_bytes()))
 # ROOT's accepted actual semantic replay authenticated its full cold-source
 # importer closure. This is a physical dependency superset, not semantic reuse.
 admission=pin(R/'reports/m4-138-semantic-review/root-admission-r2/report.json','501fadf59bd716c493614b6e953e53fe5486d043ef666876b699d691cbec4c95');a=json.loads(admission.read_bytes());assert a['passed']and a['independent_review'];absorb(a['files'])
 source=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');s=json.loads(source.read_bytes());assert s['passed'];absorb(s['files'])
 assert str(R/'tools/m4-strings-review/provider_model.py')in files and str(R/'tools/m4-onexit-review/provider_model.py')in files
 pin(__file__);required=out/'required-ordinary-files.json';required.write_text(json.dumps(files,indent=2)+'\n')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_opened=False,expected_controls=32,conservative_dependency_superset=True,current_original141_endpoint_evidence=False,initializer_credit=0,required_ordinary_files=str(required),required_ordinary_files_sha256=sha(required),deferred_external_or_capture_identities=deferred,files={str(base):sha(base),str(admission):sha(admission),str(source):sha(source),str(Path(__file__).resolve()):sha(Path(__file__)),str(required):sha(required)}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),ordinary_files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
