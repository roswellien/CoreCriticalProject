"""Prepare bounded extraction code/physical closure; never opens capture metadata/archive."""
from pathlib import Path
import ast,difflib,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-owner-export-preparation-r1';assert not out.exists();out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 p=pin(R/'tools/m4-138-validation-review/export_constructor37_current_r1.py');q=pin(R/'tools/m4-startup141-paired/export_native_owner_cuts_v1.py');a=p.read_text();b=q.read_text();ast.parse(b)
 delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a.splitlines(True)[i:j]),child=''.join(b.splitlines(True)[k:l])))
 back=b.splitlines(True)
 for h in reversed(delta):assert ''.join(back[h['child_start']:h['child_stop']])==h['child'];back[h['child_start']:h['child_stop']]=h['parent'].splitlines(True)
 assert ''.join(back)==a;inv=out/'parent-transport-inverse.json';inv.write_text(json.dumps(delta,indent=2)+'\n');pin(inv)
 source=pin(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3');N=json.loads(source.read_bytes());execution=pin(R/'reports/m4-startup141-root/execution-r2/report.json','536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6');E=json.loads(execution.read_bytes());assert N['passed']and N['reader_closed']and E['passed'];capture={}
 # Physical identities are declared by closed current worker/source receipts;
 # ROOT independently authenticates these exact files before a future reader.
 for level in('O0','O2'):
  row=next(v for v in N['paired_exports']if v['branch']==level);path=Path(E['runs'][level]['capture']).resolve();assert path==Path(row['transport_path']).resolve();assert N['files'][str(path)]==row['transport_sha256'];capture[str(path)]=row['transport_sha256']
  for name,h in E['files'].items():
   dep=Path(name).resolve()
   if dep.parent==path.parent:
    assert dep.suffix.lower()=='.mwb'or dep==path;assert name not in capture or capture[name]==h;capture[name]=h
  assert any(Path(n).suffix.lower()=='.mwb'and Path(n).parent==path.parent for n in capture),'Current archive parts explicitly in closed execution map'
 for name in('capture_bundle.py','manifests.py','paths.py','stages.py'):pin(R/'tools/m4-pipeline'/name)
 pin(R/'tools/m4-crt-allocation-root/run_v2.py');pin(R/'reports/m4-startup141-source/preparation-r6/paired_exports.py');pin(R/'reports/m4-startup141-paired/native-owner-cut-preparation-r1/report.json');pin(R/'tools/m4-startup141-paired/constructor_native_input141_v3.py');pin(sys.executable);pin(__file__)
 # Reuse admitted constructor cold Python/import inputs, omitting old payloads,
 # images and unrelated source receipt unions from the reader-specific recipe.
 cold=pin(R/'reports/m4-startup141-paired/native-constructor-source-preparation-r3/required-ordinary-files.json');m=json.loads(cold.read_bytes())
 for name,h in m.items():
  dep=Path(name)
  if dep.suffix.lower()in('.py','.pyi','.pyd','.dll')and not dep.is_relative_to(R):pin(dep,h)
 closure=out/'required-ordinary-files.json';closure.write_text(json.dumps(files,indent=2)+'\n');c=out/'required-capture-identities.json';c.write_text(json.dumps(capture,indent=2)+'\n')
 recipe=out/'ROOT-recipe.txt';recipe.write_text('UNEXECUTED. ROOT independently review exporter/adaptor3 and current source36 zero-owner-write prefix; authenticate required ordinary map and exact current native O0/O2 capture identities before imports/readers. scope_identity native141_constructor_owner_cut_export. CLI Python -B export_native_owner_cuts_v1.py ROOT_ADMISSION SHA FRESH_NAME. Existing capture ONLY; no worker/model. Full DirectSet authentication unchanged. Export exactly first constructor-mfc-before dynamic mapped owner pages + separately terminal widget-onexit-after dynamic owner equality targets for36 rows. Static pages/caller stack remain actual root BEFORE, never borrowed checkpoint prefixes. Fresh supplement is not source proof or acceptance. After closed PASS ROOT must independently admit supplement index/payload/report and prepare sourcecaller5 bound adapter3; do not invoke source4 unchanged.\n')
 report=out/'report.json';report.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,reader_opened=False,canonical_reader_opened=False,worker_launched=False,initializer_credit=0,root_admission_minted=False,export_main=str(q),parent_transport_inverse_hunks=len(delta),whole_parent_transport_inverse=True,required_ordinary_files=str(closure),required_ordinary_files_sha256=sha(closure),required_capture_identities=str(c),required_capture_identities_sha256=sha(c),capture_identities_authenticated_by_this_preparation=False,only_current_native_levels=['O0','O2'],current_original138_export_excluded=True,files={str(v.resolve()):sha(v)for v in[p,q,inv,source,execution,closure,c,recipe,Path(__file__).resolve()]}),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report),exporter_sha256=sha(q),ordinary_code_files=len(files),deferred_capture_files=len(capture))))
if __name__=='__main__':main()
