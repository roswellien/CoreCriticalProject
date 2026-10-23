"""Immutable141 service union; exact FPS growth body plus exact constructor8."""
from pathlib import Path
import hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-runway'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 ctor=R/'reports/m4-constructor-native/service-preparation-r8';fps=R/'reports/m4-fps-native/service-preparation-r3'
 c=json.loads(pin(ctor/'report.json','7437fa44e96c0ad7ec07431b8b69c00e08e63a8be139827bf7e1e11caaa53140').read_bytes());f=json.loads(pin(fps/'report.json','cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9').read_bytes())
 assert c['passed']and f['passed']
 raw_c=pin(ctor/'session_impl.inc',c['files'][str((ctor/'session_impl.inc').resolve())]).read_text();raw_f=pin(fps/'session_impl.inc',f['files'][str((fps/'session_impl.inc').resolve())]).read_text()
 def method(s):
  begin=s.index(' void borrow_widget_onexit(State&source,');body=s.index('{',begin);depth=0
  for i in range(body,len(s)):
   if s[i]=='{':depth+=1
   if s[i]=='}':
    depth-=1
    if not depth:return s[begin:i+1]
  raise ValueError('Complete method')
 before=method(raw_c);baseline=method(raw_f);assert raw_c.count(before)==raw_f.count(baseline)==1
 tail='case 0x40f000:callback=0x40f030;break;default:';added='case 0x4103f0:callback=0x410420;break;case 0x410440:callback=0x410470;break;case 0x459b40:callback=0x459b70;break;'
 assert baseline.count(tail)==1;after=baseline.replace(tail,'case 0x40f000:callback=0x40f030;break;'+added+'default:',1)
 assert after.count(added)==1 and after.replace(added,'',1)==baseline
 merged=raw_c.replace(before,after,1);assert merged.replace(after,before,1)==raw_c
 # Method comments live outside the method and must describe all ten roots.
 comment=' // Borrow only the exact source import reached by the six normal widget roots.'
 assert merged.count(comment)==1;newcomment=' // Borrow only the exact source import reached by seven widget/FPS and three constructor roots.';merged=merged.replace(comment,newcomment,1)
 assert merged.replace(newcomment,comment,1).replace(after,before,1)==raw_c
 expected=[(0x40e250,0x40e420),(0x40ef50,0x40ef90),(0x40f000,0x40f030),(0x479590,0x4795d0),(0x5a3c30,0x5a3c60),(0x5a3ff0,0x5a4020),(0x5a66f0,0x5a6720),(0x4103f0,0x410420),(0x410440,0x410470),(0x459b40,0x459b70)]
 for root,callback in expected:assert after.count(f'case 0x{root:x}:callback=0x{callback:x};break;')==1
 # Current complete growth adapter required; no relaxed equal-value/owner path.
 for phrase in ['including a full vector','One bounded literal registry growth per widget registration','Whole actual HeapSize capacity with only the literal callback append','Whole actual realloc initial extent with only the literal callback append','Every preceding producer byte carried, except the one source callback append']:
  assert phrase in after
 out.mkdir(parents=True);relations=[]
 for p in ctor.iterdir():
  if p.is_file()and p.name!='report.json':pin(p,c['files'][str(p.resolve())]);shutil.copyfile(p,out/p.name)
 (out/'session_impl.inc').write_text(merged)
 for p in ctor.iterdir():
  if p.is_file()and p.name!='report.json':relations.append(dict(parent=str(p),child=str(out/p.name),parent_sha256=sha(p),child_sha256=sha(out/p.name),whole_bytes_equal=sha(p)==sha(out/p.name)))
 assert [Path(x['child']).name for x in relations if not x['whole_bytes_equal']]==['session_impl.inc']
 (out/'service-union-delta.json').write_text(json.dumps(dict(file='session_impl.inc',constructor_before=before,union_after=after,current138_growth_baseline=baseline,constructor_callback_case_addition=added,comment_before=comment,comment_after=newcomment,
  inverse_restores_exact_constructor8=True,remove_exact3cases_restores_entire_current138_growth_method=True),indent=2)+'\n')
 (out/'service-union-contract.json').write_text(json.dumps(dict(callbacks=[dict(root=r,callback=c)for r,c in expected],whole_growth_function_unchanged_except3cases=True,complete_FPS_case_restored=True,
  all_constructor8_code_outside_exact_adapter_identical=True,full12B_private_FS_mirror_unchanged=True,balanced_allocator_and_free_family_provenance_unchanged=True,source_after_seed=False,initializer_credit=0),indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Unexecuted exact141 registry service union: current138 full-growth adapter plus constructor8 complete source/owner/FS guards',native_include=str(out),native_library=str(out/'registry_library.cpp'),
  parent_constructor_preparation_sha256=sha(ctor/'report.json'),current138_borrowed_service_sha256=sha(fps/'report.json'),source_relations=relations,changed_constructor_files=['session_impl.inc'],
  exact_inverse_restores_constructor8=True,whole_current138_growth_method_preserved_except3exactcallbacks=True,widget_FPS_root_count=7,constructor_root_count=3,
  worker_executed=False,native_executed=False,execution_admitted=False,independent_union_source_review_pending=True,whole141_source_original_controls_pending=True,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
