"""Retain full v4 physical/link review; independently prove finite CRT restore repair."""
from pathlib import Path
import importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v4.py'
spec=importlib.util.spec_from_file_location('retained_constructor_prelaunch_v4',p);parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
def review_finite_constructor_FS(pin,read,base,sp,physical,counts):
 old=read(base/'service-preparation-r5/report.json','61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761')
 parent.review_finite_constructor_FS(pin,read,base,old,physical,counts)
 cause=read(R/'reports/m4-138-constructor-readiness/current-cause-r1/report.json','fa8b16033af95dedae6b19f5484958c4ba16f74fae4b215efc05794ddfe0b5a1')
 assert cause['passed']and not cause['reader_opened']and not cause['native_execution_performed']
 assert cause['same_head_source_store_candidates'][-1]['row'][0]==0x7800136a
 assert cause['latest_constructor_frame_mirror_words'][1]==0x5ba08b
 assert sp['parent_service_sha256']=='61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761'
 assert sp['actual_current_cause_sha256']=='fa8b16033af95dedae6b19f5484958c4ba16f74fae4b215efc05794ddfe0b5a1'
 assert sp['changed_files']==['fs_operations.inc']and sp['legacy_CRT_FS_admission_unchanged']and sp['complete12B_private_frame_mirror']and sp['exact_intervening_CRT_source_provenance']
 delta=json.loads(pin(base/'service-preparation-r7/constructor-restore-delta.json').read_bytes())
 contract=json.loads(pin(base/'service-preparation-r7/constructor-restore-contract.json').read_bytes())
 assert delta['file']=='fs_operations.inc'
 assert contract['genuine_constructor_installs']==[0x459b8e,0x4bf91e,0x4c031e,0x4c057e,0x58aece]
 assert contract['legacy_CRT_branch_unchanged']and contract['full12B_private_mirror_unchanged']and contract['initializer_credit']==0
 wanted=[(0x780012f2,'64a100000000'),(0x780012f8,'50'),(0x780012f9,'64892500000000'),(0x78001367,'8b4df0'),(0x7800136a,'64890d00000000')]
 assert contract['physical_CRT_instructions']==[dict(pc=pc,source_hex=raw)for pc,raw in wanted]
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 crt=PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
 for pc,raw in wanted:
  payload=bytes.fromhex(raw);off,_=crt.rva_range(pc-crt.image_base,len(payload));assert crt.data[off:off+len(payload)]==payload;counts['physical_balanced_CRT_predecessor_source_forms']+=1
 changed=set()
 for row in sp['source_relations']:
  a=pin(row['parent'],row['parent_sha256']);z=pin(row['child'],row['child_sha256']);assert a.parent==base/'service-preparation-r5'and z.parent==base/'service-preparation-r7'and a.name==z.name
  if row['unchanged']:
   assert a.read_bytes()==z.read_bytes();counts['whole_unchanged_CRT_restore_service_inputs']+=1
  else:
   changed.add(z.name);text=a.read_text();assert z.name==delta['file']and text.count(delta['before'])==1;assert text.replace(delta['before'],delta['after'],1)==z.read_text();counts['whole_exact_CRT_restore_service_deltas']+=1
 assert changed=={'fs_operations.inc'}and counts['whole_exact_CRT_restore_service_deltas']==1
 # Only finite constructor installer PCs may produce handlers. The branch is
 # entered only for the current exact CRT restore, and every intervening FS
 # write must be a balanced source allocator install/restore with predecessor
 # read/store joins. The old fallback and entire12B mirror remain verbatim.
 for token in ("if(install->pc==0x7800136a)","a.address==base&&a.bytes==4&&a.write&&a.value==head&&constructor_handler(a.pc)","if(a.address!=base||!a.write)continue;","a.pc==0x780012f9&&!crt_frame&&a.bytes==4","a.value>=lower_stack&&a.value+12<=0x20002000&&a.value<head&&i>=2","same(source_accesses_[i-2],0x780012f2,base,head,0)","same(source_accesses_[i-1],0x780012f8,crt_frame,head,1)","a.pc==0x7800136a&&crt_frame&&same(a,0x7800136a,base,head,1)","same(source_accesses_[i-1],0x78001367,crt_frame,head,0)","}else proven=false;","proven=proven&&!crt_frame;","if(!proven)constructor_install=source_accesses_.rend();"):
  assert token in delta['after'],token
 source=pin(base/'service-preparation-r7/fs_operations.inc').read_text()
 for token in ("std::array<std::byte,12>actual{};runtime.memory().read({head},actual)","std::equal(actual.begin(),actual.end(),upper_expected_.begin()+head-0x20001000)","install->pc<0x78000000||!instruction(install->pc)","runtime.memory().load<unsigned>({head+4})!=0x7800ef03"):
  assert token in source,token
 for q in(base/'fixture-preparation-r4').iterdir():
  if q.is_file()and q.suffix in('.cpp','.s','.inc','.hpp'):
   assert pin(q).read_bytes()==pin(base/'fixture-preparation-r5'/q.name).read_bytes();counts['whole_unchanged_current_constructor_fixture_sources']+=1
 assert not sp['source_after_seed']and not sp['native_executed']and sp['initializer_credit']==0
t=parent.t
changes=[]
def change(a,z):
 global t
 assert a in t,a;changes.append(dict(before=a,after=z));t=t.replace(a,z)
for a,z in [('fa3783ea0dd32723e8d2b7917d7847e5b1951408d699fc3d82e77af0364c404d','31b3f6b5ce2f8af0bb43dbcf7b983629c6978f2d1fcf71c25f14efc6750682a1'),('97d32f7dbf5003f3ec0c79d95b8cfa02729b099cf2f03288ff69a69f6be9efe4','4bbe778a6938db08f3e583d98dd31429c1bbbf0d0a4de6475edd0e6a758ef805'),('61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761','8ad628b4aa2953e7900ca44cc091ebd3cefa6b490338f09763d3079ad23df516'),('edf6b8acdb6f957005d35ee972073f837ff1773228fb2651bff1d6fb4febbfee','0c72e7a8932db208a6940d7c0e447e566b0ab1c5ae976c19c1bee8412eb03f31'),('fixture-preparation-r4','fixture-preparation-r5'),('fixture-build-r8','fixture-build-r9'),('service-preparation-r5','service-preparation-r7'),('service-build-r5','service-build-r7')]:change(a,z)
change("out = R/'reports/m4-tree-review'/name","out = R/'reports/m4-138-validation-review'/name")
change("  pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v3.py');","  pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v4.py');pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch_v3.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
