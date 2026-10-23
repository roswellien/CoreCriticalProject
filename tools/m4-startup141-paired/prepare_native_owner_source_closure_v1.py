"""Future ROOT recipe: prior ordinary admission plus closed bounded owner supplement."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(owner_export_path,owner_export_sha,name):
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();declared={};fresh={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and p.name!='transport.json';v=sha(p);assert h is None or v==h;assert str(p)not in declared or declared[str(p)]==v;declared[str(p)]=v;fresh[str(p)]=v;return p
 oldpath=pin(R/'reports/m4-startup141-paired/root-native36-admission-r1/report.json','8f34c2bea39b3d231469339393e1ff386dec7bd3d7cefd1ff14e3407bc321bdd');old=json.loads(oldpath.read_bytes());assert old['passed']and old['independent_review']and old['scope_identity']=='native141_constructor36_own_source'
 for p,h in old['files'].items():
  path=Path(p).resolve();assert path.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and path.name!='transport.json';assert str(path)not in declared or declared[str(path)]==h;declared[str(path)]=h
 op=pin(owner_export_path,owner_export_sha);O=json.loads(op.read_bytes());assert O['passed']and O['reader_closed']and O['paired_export_readers_closed']and O['source_sha256']=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'and O['execution_sha256']=='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6'and O['worker_launched']is False and O['model_executed']is False
 assert len(O['cases'])==36 and {(c['level'],c['sequence'],c['root'])for c in O['cases']}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in(0x4103f0,0x410440,0x459b40)}
 for row in O['paired_exports']:
  assert row['branch']in('O0','O2')
  for f in('index','payload'):pin(row[f+'_path'],row[f+'_sha256'])
  assert O['files'][row['index_path']]==row['index_sha256']and O['files'][row['payload_path']]==row['payload_sha256']
 for p in ['tools/m4-startup141-paired/constructor_native36_source141_v5.py','tools/m4-startup141-paired/constructor_native_input141_v3.py','tools/m4-startup141-paired/native_owner_cut_controls_v1.py','tools/m4-startup141-paired/native_owner_cut_controls_v2.py','reports/m4-startup141-paired/native-constructor-source-preparation-r5/report.json','reports/m4-startup141-paired/native-constructor-source-preparation-r5/inverse.json','reports/m4-startup141-paired/native-owner-cut-preparation-r1/report.json','reports/m4-startup141-paired/native-owner-cut-preparation-r1/inverse.json','reports/m4-startup141-paired/native-owner-cut-preparation-r1/current-prefix-facts.json','reports/m4-startup141-paired/native-owner-export-preparation-r2/report.json']:
  path=pin(R/p)
  if path.suffix=='.py':ast.parse(path.read_text())
 pin(__file__);union=out/'required-ordinary-files.json';union.write_text(json.dumps(declared,indent=2)+'\n');recipe=out/'ROOT-recipe.txt';recipe.write_text('UNEXECUTED source/models/readers/admission. ROOT inspect entire adapter3/source5 inverses; execute pure native_owner_cut_controls_v2.controls(adapter3_text,source5_text) under actual physical inputs. Independently rehash ALL required-ordinary-files.json before imports/source run, including retained admission1046 inputs and new exact supplement report/index/payload. Fresh admission scope_identity native141_constructor36_own_source, configuration_sha256 retained a5c92bfb81bcc981d1fe8adf532d4c6876f1a5eb9b28091f70e81f6f7aac37e0, owner_export_sha256 '+owner_export_sha+'. Source CLI Python -B constructor_native36_source141_v5.py ROOT_ADMISSION SHA CONFIG SHA '+str(op)+' '+owner_export_sha+' FRESH_NAME. BEFORE adapter receives ONLY first MFC BEFORE dynamic owner cut; complete recorded zero-write prefix establishes owner carry. Static phaseBEFORE pages/stack remain genuine. Terminal owner equality cuts opened ONLY after derive terminates; fullStateCPUFX/ENV28/rawmetadata/game/provider operands/endpoints inherited unchanged. Broader previous nonphase provider carry and actual original/native relational141 gate remain pending. No worker/fullverifier/acceptance.\n')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,reader_opened=False,imports_executed=False,source_execution=False,root_admission_minted=False,owner_export_sha256=owner_export_sha,required_ordinary_files=str(union),required_ordinary_files_sha256=sha(union),ordinary_files=len(declared),retained_prior_admission_hashes_recomputed_by_this_preparation=False,ROOT_complete_union_rehash_required_before_import=True,actual_controls_execution_pending=True,actual_native36_source_execution_pending=True,files={**fresh,str(union.resolve()):sha(union),str(recipe.resolve()):sha(recipe)}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),ordinary_files=len(declared))))
if __name__=='__main__':main(*sys.argv[1:])
