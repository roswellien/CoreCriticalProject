"""Finite constructor-owned outer FS provenance; prepare only, no worker."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
OLD=R/'reports/m4-constructor-native/service-preparation-r4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact finite constructor FS hunk '+a[:100]);return s.replace(a,b,1)
def main(name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh finite FS preparation');pins={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact current physical source '+str(p));pins[str(p)]=v;return p
 old=json.loads(pin(OLD/'report.json','ccd92f92048563db7fe9de82d694179d5f43bec42b9e4ad32ff733934cbd74e5').read_bytes());need(old['passed'],'Current immutable constructor service')
 src=R/'reports/m4-constructor-source/preparation-r1';sreport=json.loads(pin(src/'report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf').read_bytes());rows=json.loads(pin(src/'source-instructions.json',sreport['files'][str((src/'source-instructions.json').resolve())]).read_bytes());rows=rows['instructions']if isinstance(rows,dict)else rows;by={r['pc']:r for r in rows}
 fs=[dict(entry=e,read=e+7,install=e+14,handler=h,restore=t)for e,h,t in((0x459b80,0x5b2d88,0x459d9d),(0x4bf910,0x5b7898,0x4bfb82),(0x4c0310,0x5b7978,0x4c0506),(0x4c0570,0x5b7998,0x4c0766),(0x58aec0,0x5ba08b,0x58afd2))]
 for f in fs:
  need(by[f['entry']]['bytes']=='6aff'and by[f['entry']+2]['bytes']=='68'+f['handler'].to_bytes(4,'little').hex(),'Physical normal scope/handler pushes')
  need(by[f['read']]['bytes']=='64a100000000'and by[f['read']+6]['bytes']=='50'and by[f['install']]['bytes']=='64892500000000'and by[f['restore']]['bytes']=='64890d00000000','Physical FS read/predecessor push/ESP install/ECX restore')
 diagnostic=R/'reports/m4-tree-review/constructor-native37-failure-r1';d=json.loads(pin(diagnostic/'report.json','ac147e114599064caa909c6949d381cfd3bd122dbf9823143a957604407e4555').read_bytes());need(d['passed']and d['reader_closed'],'Sealed actual first-fault diagnosis, not success')
 for fn in('locale-fault.bin','locale-fault-reason.bin'):
  p=diagnostic/'sequence-0/selected'/fn;pin(p,d['files'][str(p.resolve())])
 out.mkdir(parents=True)
 for p in OLD.iterdir():
  if not p.is_file()or p.name=='report.json':continue
  pin(p,old['files'][str(p.resolve())]);shutil.copyfile(p,out/p.name)
 def edit(fn,a,b):
  p=out/fn;s=p.read_text();p.write_text(one(s,a,b));changes.append(dict(file=fn,before=a,after=b))
 edit('locale_batch.hpp','bool fs_admitted_{};','bool fs_admitted_{};unsigned constructor_source_root_{};')
 a=' if(install==source_accesses_.rend()||install->pc<0x78000000||!instruction(install->pc)||\n     runtime.memory().load<unsigned>({head+4})!=0x7800ef03)\n   deny("Only an accepted original CRT normal frame may nest the owned guest FS chain",head);'
 cases=''.join('case 0x%x:handler=0x%x;break;'%(f['install'],f['handler'])for f in fs)
 b=''' bool constructor_frame=false;
  if(install!=source_accesses_.rend()&&(constructor_source_root_==0x4103f0||constructor_source_root_==0x410440||constructor_source_root_==0x459b40)){
   unsigned handler{};switch(install->pc){'''+cases+'''default:break;}
   if(handler&&head>=0x20001000&&std::uint64_t(head)+12<=0x20002000){
    std::array<std::byte,12>actual{};runtime.memory().read({head},actual);
    constructor_frame=runtime.memory().load<unsigned>({head+4})==handler&&
     std::equal(actual.begin(),actual.end(),upper_expected_.begin()+head-0x20001000);
   }
  }
  if(!constructor_frame&&(install==source_accesses_.rend()||install->pc<0x78000000||!instruction(install->pc)||
     runtime.memory().load<unsigned>({head+4})!=0x7800ef03))
   deny("Only an accepted original CRT or exact current constructor source frame may nest the owned guest FS chain",head);'''
 edit('fs_operations.inc',a,b)
 edit('fs_operations.inc',' const auto native_input=fs_native_input_;const auto admitted=fs_admitted_;',' const auto native_input=fs_native_input_;const auto admitted=fs_admitted_;const auto constructor_root=constructor_source_root_;')
 edit('fs_operations.inc','||native_input!=fs_native_input_||admitted!=fs_admitted_)','||native_input!=fs_native_input_||admitted!=fs_admitted_||constructor_root!=constructor_source_root_)')
 edit('session_impl.inc','  constructor_active_root_=entering?root:0;constructor_prior_read_={};constructor_prior_root_=0;++constructor_access_epoch_;','''  require(binding->constructor_source_root_==(entering?0:root)&&binding->fs_expected_==m4_runtime::Runtime::seh_end&&r.memory().load<unsigned>(r.fs_base())==m4_runtime::Runtime::seh_end,"Exact restored source FS sentinel at balanced constructor scope endpoints");
  constructor_active_root_=entering?root:0;binding->constructor_source_root_=constructor_active_root_;constructor_prior_read_={};constructor_prior_root_=0;++constructor_access_epoch_;''')
 edit('session_impl.inc',' void clear_constructor_scope()noexcept{constructor_active_root_=0;',' void clear_constructor_scope()noexcept{binding->constructor_source_root_=0;constructor_active_root_=0;')
 edit('session_impl.inc','binding->expected_store(address,raw.data(),bytes);','binding->expected_store(address,raw.data(),bytes);if(address==r.fs_base().value){require(bytes==4,"Whole constructor FS source DWORD witness");binding->source_accesses_.push_back({pc,address,value,bytes,1});}')
 edit('session_impl.inc','  sink("constructor-source-mirror-accesses.bin",std::as_bytes(std::span(constructor_accesses_)),user);','  sink("constructor-source-mirror-accesses.bin",std::as_bytes(std::span(constructor_accesses_)),user);const std::array<unsigned,2> constructor_fs_scope{constructor_active_root_,b.constructor_source_root_};sink("constructor-FS-source-scope.bin",std::as_bytes(std::span(constructor_fs_scope)),user);')
 # Every unchanged current file is individually compared. A source guard
 # admits five exact normal frame forms only; no whole AFTER input exists.
 changed=[p.name for p in out.iterdir()if p.is_file()and sha(p)!=old['files'][str((OLD/p.name).resolve())]]
 need(sorted(changed)==['fs_operations.inc','locale_batch.hpp','session_impl.inc'],'Only three finite private/source guard files change')
 (out/'constructor-FS-contracts.json').write_text(json.dumps(dict(roots=[0x4103f0,0x410440,0x459b40],frames=fs,full12B_private_mirror=True,source_FS_store_witness=True,scope_enters_and_exits_at_actual_guest_sentinel=True,legacy_CRT_branch_unchanged=True,no_arbitrary_frame_seed=True,observed_failure_head=0x2000177c,initializer_credit=0),indent=2)+'\n')
 (out/'constructor-FS-deltas.json').write_text(json.dumps(changes,indent=2)+'\n')
 relations=[]
 for p in OLD.iterdir():
  if p.is_file()and p.name!='report.json':relations.append(dict(parent=str(p),child=str(out/p.name),parent_sha256=sha(p),child_sha256=sha(out/p.name),unchanged=sha(p)==sha(out/p.name)))
 for p in out.iterdir():pin(p)
 pin(__file__)
 report=dict(passed=True,scope='Unexecuted finite exact constructor FS predecessor admission; no source/native initializer credit',parent_service_path=str(OLD/'report.json'),parent_service_sha256=sha(OLD/'report.json'),actual_first_failure_sha256=sha(diagnostic/'report.json'),native_include=str(out),native_library=str(out/'registry_library.cpp'),changed_files=changed,source_relations=relations,exact_constructor_FS_source_frames=5,complete12B_private_frame_mirror=True,legacy_CRT_FS_admission_unchanged=True,source_after_seed=False,native_executed=False,initializer_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
