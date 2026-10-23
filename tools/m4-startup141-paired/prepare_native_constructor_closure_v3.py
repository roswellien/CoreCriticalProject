"""ROOT-only cold source/API/metadata closure, no reader/model imports."""
from pathlib import Path
import hashlib,json,ast,difflib,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-constructor-source-preparation-r3';assert not out.exists();out.mkdir();p=R/'tools/m4-startup141-paired/constructor_native36_source141_v2.py';q=p.with_name('constructor_native36_source141_v3.py');assert not q.exists();a=p.read_text();old="   if reading:\n    need(dep.suffix.lower()not in('.mwb','.mwi','.zip')";new="   if reading:\n    if dep.suffix.lower()=='.pyc':raise PermissionError('No cached bytecode import; only ROOT-admitted physical source')\n    need(dep.suffix.lower()not in('.mwb','.mwi','.zip')";assert a.count(old)==1;b=a.replace(old,new);ast.parse(b);q.write_text(b);assert b.replace(new,old)==a
 before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n');files={};deferred={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def absorb(f):
  for p,h in f.items():
   path=Path(p).resolve()
   if path.suffix.lower()in('.mwb','.mwi','.zip','.pyc')or path.name=='transport.json':deferred[p]=h
   else:pin(path,h)
 control=read(R/'reports/m4-original141-source/root-control-closure-r1/required-ordinary-files.json');absorb(control)
 inventory=read(R/'reports/m4-original141-tree-source/import-inventory-r2/report.json','e999db06968951368c1202fd67842e57f32ebfd8ad514a2ea8f4cdb38818f1c2');assert inventory['passed']and inventory['actual_cold_import_and_metadata_reads']==148;absorb(inventory['files'])
 original=read(R/'reports/m4-original141-source/source-r4-constructors/report.json','8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899');assert original['passed']and len(original['cases'])==18;absorb(original['files'])
 sourcepath=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';N=read(sourcepath,'8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3');assert N['passed']and N['reader_closed'];pin(sourcepath.parent/'Constructor-carried-source-derivations.json',N['files'][str((sourcepath.parent/'Constructor-carried-source-derivations.json').resolve())])
 # Exactly current two native ordinary sealed branches. The source6 original138
 # export row never enters the required map or reader iteration.
 exports=[]
 for level in('O0','O2'):
  rows=[e for e in N['paired_exports']if e['branch']==level];assert len(rows)==1;e=rows[0];exports.append(e)
  for field in('index','payload'):pin(e[field+'_path'],e[field+'_sha256'])
 for path in[p,q,out/'inverse.json',R/'tools/m4-startup141-paired/constructor_native_input141_v2.py',R/'tools/m4-constructor-native/derive_source_v9.py',R/'tools/m4-startup138-original/export_reader_r2.py',R/'reports/m4-startup141-paired/native-constructor-source-preparation-r1/configuration.json',R/'reports/m4-startup141-paired/native-constructor-source-preparation-r1/report.json',R/'reports/m4-startup141-paired/native-constructor-source-preparation-r2/report.json',Path(sys.executable),Path(__file__).resolve()]:pin(path)
 required=out/'required-ordinary-files.json';required.write_text(json.dumps(files,indent=2)+'\n')
 recipe='UNEXECUTED main/reader/model. ROOT review entire derivative3, sourceadapter2, derive9 and all physical inheritedcoldconstructor54/TREE148 program metadata closure plus actualcurrent original18 filemap. ROOT may independently rehash required-ordinary-files.json (currentnative O0/O2 sealed payloads authenticated during this preparation only as ordinary contiguous files, never opened by an ExportReader). Do not admit source6 oldoriginal138 export. ROOTadmission scope native141_constructor36_own_source with configuration_sha256 a5c92bfb81bcc981d1fe8adf532d4c6876f1a5eb9b28091f70e81f6f7aac37e0. CLI Python -B constructor_native36_source141_v3.py ADMISSION SHA CONFIG SHA FRESH_NAME. OwnBeforeENV derived before endpoint opens from entireinteger path+all5 actual API FXbefore/afterconservation; exact whole ownCPUStateFX/Env/pages/backings/game+borrowed operands and source6before/after/wholejournal joins mandatory. BeforeNonphase ownercarry remains explicitly pending; never equated from endpoint success. No nativeworker/fullverifier/fullpair/acceptance.\n'
 (out/'ROOT-recipe.txt').write_text(recipe);r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,native_worker_launched=False,initializer_credit=0,cache_reads_refused_by_main_audit=True,cache_refusal_whole_inverse=True,cache_inverse_hunks=len(d),current_native_only_exports=exports,required_ordinary_files=str(required),required_ordinary_files_sha256=sha(required),native36_source_main_admitted=False,previous_checkpoint_nonphase_owner_carry_proven=False,input_carry_policy_review_pending=True,deferred_capture_identities=deferred,files={str(p):sha(p),str(q):sha(q),str(out/'inverse.json'):sha(out/'inverse.json'),str(required):sha(required),str(out/'ROOT-recipe.txt'):sha(out/'ROOT-recipe.txt'),str(Path(__file__).resolve()):sha(Path(__file__))}),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),ordinary_files=len(files))))
if __name__=='__main__':main()
