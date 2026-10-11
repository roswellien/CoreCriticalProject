"""Exact second CRT family extension using closed ordinary current-failure-r3."""
from pathlib import Path
import hashlib,json,shutil,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-constructor-native'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 parent=R/'reports/m4-constructor-native/service-preparation-r7'
 d=json.loads(pin(parent/'report.json','8ad628b4aa2953e7900ca44cc091ebd3cefa6b490338f09763d3079ad23df516').read_bytes())
 diagnostic=R/'reports/m4-138-constructor-readiness/current-failure-r3/report.json'
 c=json.loads(pin(diagnostic).read_bytes());assert c['passed']and c['reader_closed']and not c['initializer_credit']
 def raw(n):
  p=diagnostic.parent/'sequence-0/selected'/n;return pin(p,c['files'][str(p.resolve())]).read_bytes()
 fault=struct.unpack('<4I',raw('locale-fault.bin'));assert fault==(1,0x78001420,0x2000177c,91)
 reason=raw('locale-fault-reason.bin').decode();a=list(struct.iter_unpack('<IIQII',raw('locale-source-accesses.bin')))
 head=fault[2];base=0x7ffde000
 assert a[1700]==(0x58aece,base,head,4,1)
 assert a[1823:1826]==[(0x7800139f,base,head,4,0),(0x780013a5,0x20001744,head,4,1),(0x780013a6,base,0x20001744,4,1)]
 assert a[1830:1832]==[(0x78001416,0x20001744,head,4,0),(0x78001419,base,head,4,1)]
 before=json.loads(pin(parent/'constructor-restore-delta.json',d['files'][str((parent/'constructor-restore-delta.json').resolve())]).read_bytes())['after']
 after=before.replace('CRT allocator restore','CRT allocator/free restore').replace('if(install->pc==0x7800136a){','if(install->pc==0x7800136a||install->pc==0x78001419){').replace('unsigned crt_frame{};','unsigned crt_frame{},crt_family{};')
 old='''      if(a.pc==0x780012f9&&!crt_frame&&a.bytes==4&&a.value>=lower_stack&&a.value+12<=0x20002000&&a.value<head&&i>=2){
       crt_frame=unsigned(a.value);
       proven=same(source_accesses_[i-2],0x780012f2,base,head,0)&&same(source_accesses_[i-1],0x780012f8,crt_frame,head,1);
      }else if(a.pc==0x7800136a&&crt_frame&&same(a,0x7800136a,base,head,1)&&i){
       proven=same(source_accesses_[i-1],0x78001367,crt_frame,head,0);crt_frame=0;'''
 new='''      if((a.pc==0x780012f9||a.pc==0x780013a6)&&!crt_frame&&a.bytes==4&&a.value>=lower_stack&&a.value+12<=0x20002000&&a.value<head&&i>=2){
       crt_frame=unsigned(a.value);crt_family=a.pc;
       const unsigned read_pc=crt_family==0x780012f9?0x780012f2:0x7800139f;
       const unsigned push_pc=crt_family==0x780012f9?0x780012f8:0x780013a5;
       proven=same(source_accesses_[i-2],read_pc,base,head,0)&&same(source_accesses_[i-1],push_pc,crt_frame,head,1);
      }else if(crt_frame&&crt_family&&i){
       const unsigned restore_pc=crt_family==0x780012f9?0x7800136a:0x78001419;
       const unsigned saved_read_pc=crt_family==0x780012f9?0x78001367:0x78001416;
       proven=same(a,restore_pc,base,head,1)&&same(source_accesses_[i-1],saved_read_pc,crt_frame,head,0);crt_frame=0;crt_family=0;'''
 assert after.count(old)==1;after=after.replace(old,new).replace('proven=proven&&!crt_frame;','proven=proven&&!crt_frame&&!crt_family;')
 # All inherited files except this exact block remain physically identical.
 out.mkdir(parents=True);relations=[]
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':pin(p,d['files'][str(p.resolve())]);shutil.copyfile(p,out/p.name)
 target=out/'fs_operations.inc';text=target.read_text();assert text.count(before)==1;target.write_text(text.replace(before,after,1))
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 crt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pe=PEImage(crt.read_bytes());physical=[]
 for pc,wanted in [(0x780012f2,'64a100000000'),(0x780012f8,'50'),(0x780012f9,'64892500000000'),(0x78001367,'8b4df0'),(0x7800136a,'64890d00000000'),(0x7800139f,'64a100000000'),(0x780013a5,'50'),(0x780013a6,'64892500000000'),(0x78001416,'8b4df0'),(0x78001419,'64890d00000000')]:
  off=pe.rva_range(pc-pe.image_base,len(bytes.fromhex(wanted)))[0];assert pe.data[off:off+len(bytes.fromhex(wanted))].hex()==wanted;physical.append(dict(pc=pc,source_hex=wanted))
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':relations.append(dict(parent=str(p),child=str(out/p.name),parent_sha256=sha(p),child_sha256=sha(out/p.name),unchanged=sha(p)==sha(out/p.name)))
 assert [Path(x['child']).name for x in relations if not x['unchanged']]==['fs_operations.inc']
 (out/'free-restore-delta.json').write_text(json.dumps(dict(file='fs_operations.inc',before=before,after=after),indent=2)+'\n')
 contract=dict(physical_CRT_instructions=physical,current_fault_words=fault,current_source_reason=reason,genuine_constructor_index=1700,free_install_index=1825,free_restore_index=1831,
  scope='Two exact non-overlapping balanced CRT journals; matching family saved-predecessor source read/push/restore. No arbitrary same-value write admission.',legacy_CRT_branch_unchanged=True,full12B_private_mirror_unchanged=True,initializer_credit=0)
 (out/'free-restore-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(R/'tools/analysis/pe.py')
 report=dict(passed=True,scope='Unexecuted exact constructor restore second CRT free family extension only',parent_service_path=str(parent/'report.json'),parent_service_sha256=sha(parent/'report.json'),
  actual_current_cause_path=str(diagnostic),actual_current_cause_sha256=sha(diagnostic),native_include=str(out),native_library=str(out/'registry_library.cpp'),changed_files=['fs_operations.inc'],source_relations=relations,
  legacy_CRT_FS_admission_unchanged=True,complete12B_private_frame_mirror=True,exact_intervening_CRT_source_provenance=True,source_after_seed=False,native_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
