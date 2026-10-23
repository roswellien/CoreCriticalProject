"""Freeze only three actually passed current families; failed parent stays false."""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-original141-source/retained-positive-family-r1';assert not out.exists();out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 parentpath=pin(R/'reports/m4-original141-source/source-r4/report.json');parent=json.loads(parentpath.read_bytes());assert parent['passed']is False and parent['reader_closed']and parent['configuration_sha256']=='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0'and parent['original_validation_sha256']=='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
 expected={'constructor18':('source-r4-constructors','8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899','constructor_replay141_v1.py',18),'formatter4':('source-r4-formatters','e00c61062f51b554d0cfa740b0d7cec53a2f50698c4fcf074c72574b7400478f','format_source141_v2.py',24),'old4':('source-r4-old4','205bd6b71b79719d9c6aaa410107ae16df9d74142c83a387e53273869fca2b17','old4_source141_v2.py',24)}
 rows=[]
 for domain,(folder,digest,helper,extent)in expected.items():
  path=pin(R/'reports/m4-original141-source'/folder/'report.json',digest);child=json.loads(path.read_bytes());assert child['passed']and child['source_AFTER_seed']is False and child['canonical_reader_opened']is False
  assert any(r['domain']==domain and r['receipt']==str(path)and r['sha256']==digest for r in parent['children'])
  for p,h in child['files'].items():pin(p,h)
  helperpath=pin(R/'tools/m4-original141-source'/helper);assert child['files'][str(helperpath)]==sha(helperpath)
  if domain=='constructor18':
   assert len(child['cases'])==18 and {(r['sequence'],r['root'])for r in child['cases']}=={(s,r)for s in range(6)for r in(0x4103f0,0x410440,0x459b40)}and all(r['whole_GPR_EIP']and r['defined_EFLAGS']and r['whole_FX512']and r['whole_ENV28']and r['source_AFTER_seed']is False for r in child['cases'])
   vpath=R/'reports/m4-original141/root-capture-validation-r3/report.json';assert child['files'][str(vpath)]==parent['original_validation_sha256']
  else:assert child['source_case_extent']==extent and child['original_validation_sha256']==parent['original_validation_sha256']
  rows.append(dict(domain=domain,path=str(path),sha256=digest,source_case_extent=extent,helper_path=str(helperpath),helper_sha256=sha(helperpath)))
 config=pin(R/'reports/m4-original141-source/configuration-preparation-r3/configuration.json',parent['configuration_sha256'])
 # Whole positive dependencies are retained; parent failed aggregate is only
 # identity/reader-closure provenance and never a successful source gate.
 manifest=out/'manifest.json';manifest.write_text(json.dumps(dict(schema='mw34-current141-retained-positive-families-v1',configuration_sha256=sha(config),original_validation_sha256=parent['original_validation_sha256'],failed_parent_path=str(parentpath),failed_parent_sha256=sha(parentpath),failed_parent_passed=False,failed_parent_reader_closed=True,rows=rows,files=files),indent=2)+'\n');manifestsha=sha(manifest)
 p=R/'tools/m4-original141-source/replay_original141_v7.py';q=p.with_name('replay_original141_v8.py');assert not q.exists();a=p.read_text();b=a
 anchor="  E=load(R/'tools/m4-startup138-original/export_reader_r2.py','original141_export');reader=E.ExportReader(C['validation']['path'],C['validation']['sha256'],'original',pin)"
 add=f"""  reuse=read(R/'reports/m4-original141-source/retained-positive-family-r1/manifest.json','{manifestsha}');need(reuse['schema']=='mw34-current141-retained-positive-families-v1'and reuse['configuration_sha256']==configuration_sha and reuse['original_validation_sha256']==C['validation']['sha256']and reuse['failed_parent_passed']is False and reuse['failed_parent_reader_closed']is True,'Only three actual closed current positive children, failed parent never passes')
  prior=read(reuse['failed_parent_path'],reuse['failed_parent_sha256']);need(prior['passed']is False and prior['reader_closed']and prior['configuration_sha256']==configuration_sha and prior['original_validation_sha256']==C['validation']['sha256'],'Exact failed same-input parent identity/closure only')
  reused={{row['domain']:row for row in reuse['rows']}};need(len(reuse['rows'])==len(reused)==3 and set(reused)=={{'constructor18','formatter4','old4'}},'Exactly distinct three retained positive domains')
  for dep,h in reuse['files'].items():pin(dep,h)
  for domain,row in reused.items():
   pin(row['helper_path'],row['helper_sha256']);g=read(row['path'],row['sha256']);need(g['passed']and g['source_AFTER_seed']is False and g['canonical_reader_opened']is False and g['files'][row['helper_path']]==row['helper_sha256'],'Actual current passed helper/source family, no historical outcome oracle')
   need(any(v['domain']==domain and v['receipt']==row['path']and v['sha256']==row['sha256']for v in prior['children']),'Exact positive child physically recorded by failed parent')
   for dep,h in g['files'].items():pin(dep,h)
"""
 assert b.count(anchor)==1;b=b.replace(anchor,add+anchor)
 old="  ctor=load(R/'tools/m4-original141-source/constructor_replay141_v1.py','original141_constructor');ctor.main(name+'-constructors',C,reader,pin)\n  child=R/'reports/m4-original141-source'/(name+'-constructors')/'report.json'"
 new="  child=Path(reused['constructor18']['path']);pin(child,reused['constructor18']['sha256'])"
 assert b.count(old)==1;b=b.replace(old,new)
 olddir="need(childdir==ctorout.resolve(),'Exact additive child namespace')";newdir="need(childdir==Path(reused['constructor18']['path']).parent.resolve(),'Exact immutable retained positive constructor namespace')";assert b.count(olddir)==1;b=b.replace(olddir,newdir)
 oldloop="   childmodule=load(R/'tools/m4-original141-source'/tool,'current141_'+domain)\n   if domain=='new_MFC':childmodule.main(name+'-'+suffix,C,pin)\n   else:childmodule.main(name+'-'+suffix,reader,C,pin)\n   child=childdirs[suffix]/'report.json';g=read(child);"
 newloop="   childmodule=None\n   if domain in reused:\n    child=Path(reused[domain]['path']);g=read(child,reused[domain]['sha256']);need(reused[domain]['source_case_extent']==n and reused[domain]['helper_path']==str((R/'tools/m4-original141-source'/tool).resolve()),'Exact current positive extent/helper for retained domain')\n   else:\n    childmodule=load(R/'tools/m4-original141-source'/tool,'current141_'+domain)\n    if domain=='new_MFC':childmodule.main(name+'-'+suffix,C,pin)\n    else:childmodule.main(name+'-'+suffix,reader,C,pin)\n    child=childdirs[suffix]/'report.json';g=read(child)\n   "
 assert b.count(oldloop)==1;b=b.replace(oldloop,newloop)
 ast.parse(b);q.write_text(b);back=b.replace(newloop,oldloop).replace(newdir,olddir).replace(new,old).replace(add+anchor,anchor);assert back==a
 before=a.splitlines(True);after=b.splitlines(True);delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'controller-inverse.json').write_text(json.dumps(delta,indent=2)+'\n')
 physical={str(x.resolve()):sha(x)for x in[p,q,manifest,out/'controller-inverse.json',Path(__file__).resolve()]};r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,initializer_credit=0,retained_actual_positive_domains=rows,failed_parent_success_used=False,retained_manifest_sha256=manifestsha,controller_exact_whole_inverse=True,controller_inverse_hunks=len(delta),registry846_rerun=True,MFC6_widget42_fresh=True,all_complete_family_gate_checks_retained=True,ROOT_independent_reuse_admission_required=True,files=physical),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),manifest=str(manifest),manifest_sha256=manifestsha))))
if __name__=='__main__':main()
