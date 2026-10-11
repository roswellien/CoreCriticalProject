"""Full inherited prelaunch plus exact second-family balanced CRT journal proof."""
from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];p=Path(__file__).with_name('review_constructor_native37_prelaunch_v5.py')
spec=importlib.util.spec_from_file_location('constructor_retained_v5',p);previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
def review_finite_constructor_FS(pin,read,base,sp,physical,counts):
 old=read(base/'service-preparation-r7/report.json','8ad628b4aa2953e7900ca44cc091ebd3cefa6b490338f09763d3079ad23df516')
 previous.review_finite_constructor_FS(pin,read,base,old,physical,counts)
 assert sp['parent_service_sha256']=='8ad628b4aa2953e7900ca44cc091ebd3cefa6b490338f09763d3079ad23df516'
 assert sp['actual_current_cause_sha256']=='e8ed5ca3100d039fa9d1a68eaa56b7f116dd4f2664edbbbc9741577e1d1d7dff'
 cause=json.loads(pin(R/'reports/m4-138-constructor-readiness/current-failure-r3/report.json',sp['actual_current_cause_sha256']).read_bytes());assert cause['passed']and cause['reader_closed']and not cause['native_execution_performed']
 delta=json.loads(pin(base/'service-preparation-r8/free-restore-delta.json').read_bytes());contract=json.loads(pin(base/'service-preparation-r8/free-restore-contract.json').read_bytes())
 assert delta['before']==json.loads(pin(base/'service-preparation-r7/constructor-restore-delta.json').read_bytes())['after']
 assert contract['legacy_CRT_branch_unchanged']and contract['full12B_private_mirror_unchanged']and contract['initializer_credit']==0
 wanted=[(0x780012f2,'64a100000000'),(0x780012f8,'50'),(0x780012f9,'64892500000000'),(0x78001367,'8b4df0'),(0x7800136a,'64890d00000000'),(0x7800139f,'64a100000000'),(0x780013a5,'50'),(0x780013a6,'64892500000000'),(0x78001416,'8b4df0'),(0x78001419,'64890d00000000')]
 assert contract['physical_CRT_instructions']==[dict(pc=pc,source_hex=raw)for pc,raw in wanted]
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 crt=PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
 for pc,raw in wanted:
  data=bytes.fromhex(raw);off,_=crt.rva_range(pc-crt.image_base,len(data));assert crt.data[off:off+len(data)]==data;counts['physical_balanced_allocator_free_source_forms']+=1
 changed=set()
 for row in sp['source_relations']:
  a=pin(row['parent'],row['parent_sha256']);b=pin(row['child'],row['child_sha256']);assert a.parent==base/'service-preparation-r7'and b.parent==base/'service-preparation-r8'and a.name==b.name
  if row['unchanged']:assert a.read_bytes()==b.read_bytes();counts['whole_unchanged_free_restore_service_inputs']+=1
  else:
   changed.add(b.name);assert b.name==delta['file']=='fs_operations.inc';s=a.read_text();assert s.count(delta['before'])==1 and s.replace(delta['before'],delta['after'],1)==b.read_text();counts['whole_exact_free_restore_service_deltas']+=1
 assert changed=={'fs_operations.inc'}
 for token in ('install->pc==0x7800136a||install->pc==0x78001419','a.pc==0x780012f9||a.pc==0x780013a6','&&!crt_frame&&a.bytes==4','crt_family=a.pc','crt_family==0x780012f9?0x780012f2:0x7800139f','crt_family==0x780012f9?0x780012f8:0x780013a5','crt_family==0x780012f9?0x7800136a:0x78001419','crt_family==0x780012f9?0x78001367:0x78001416','same(source_accesses_[i-2],read_pc,base,head,0)','same(source_accesses_[i-1],push_pc,crt_frame,head,1)','same(a,restore_pc,base,head,1)&&same(source_accesses_[i-1],saved_read_pc,crt_frame,head,0)','}else proven=false;','proven=proven&&!crt_frame&&!crt_family;','if(!proven)constructor_install=source_accesses_.rend();'):assert token in delta['after'],token
 for f in(base/'fixture-preparation-r5').iterdir():
  if f.is_file()and f.suffix in('.cpp','.s','.inc','.hpp'):
   assert pin(f).read_bytes()==pin(base/'fixture-preparation-r6'/f.name).read_bytes();counts['whole_unchanged_free_constructor_fixture_sources']+=1
 assert not sp['source_after_seed']and not sp['native_executed']and sp['initializer_credit']==0
 pin(p)
t=previous.t;changes=[]
def one(a,b):
 global t
 assert a in t;changes.append((a,b));t=t.replace(a,b)
for a,b in [('31b3f6b5ce2f8af0bb43dbcf7b983629c6978f2d1fcf71c25f14efc6750682a1','f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0'),('4bbe778a6938db08f3e583d98dd31429c1bbbf0d0a4de6475edd0e6a758ef805','0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18'),('8ad628b4aa2953e7900ca44cc091ebd3cefa6b490338f09763d3079ad23df516','7437fa44e96c0ad7ec07431b8b69c00e08e63a8be139827bf7e1e11caaa53140'),('0c72e7a8932db208a6940d7c0e447e566b0ab1c5ae976c19c1bee8412eb03f31','17d9a84bf3cdef4404024e27e692d3432546b9751a77750889cfa974e3be1cc3'),('fixture-preparation-r5','fixture-preparation-r6'),('fixture-build-r9','fixture-build-r10'),('service-preparation-r7','service-preparation-r8'),('service-build-r7','service-build-r8')]:one(a,b)
reverse=t
for a,b in reversed(changes):reverse=reverse.replace(b,a)
assert reverse==previous.t
exec(compile(t,str(Path(__file__)),'exec'),globals())
