"""One precise FS install/CRT restore provenance correction; no execution."""
from pathlib import Path
import hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-constructor-native'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 parent=R/'reports/m4-constructor-native/service-preparation-r5'
 d=json.loads(pin(parent/'report.json','61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761').read_bytes())
 cause=pin(R/'reports/m4-138-constructor-readiness/current-cause-r1/report.json','fa8b16033af95dedae6b19f5484958c4ba16f74fae4b215efc05794ddfe0b5a1')
 c=json.loads(cause.read_bytes());assert c['passed']and not c['reader_opened']
 for p,h in c['files'].items():pin(p,h)
 out.mkdir(parents=True)
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':pin(p,d['files'][str(p.resolve())]);shutil.copyfile(p,out/p.name)
 before='''   unsigned handler{};switch(install->pc){case 0x459b8e:handler=0x5b2d88;break;case 0x4bf91e:handler=0x5b7898;break;case 0x4c031e:handler=0x5b7978;break;case 0x4c057e:handler=0x5b7998;break;case 0x58aece:handler=0x5ba08b;break;default:break;}'''
 after='''   const auto constructor_handler=[](unsigned pc){switch(pc){case 0x459b8e:return 0x5b2d88U;case 0x4bf91e:return 0x5b7898U;case 0x4c031e:return 0x5b7978U;case 0x4c057e:return 0x5b7998U;case 0x58aece:return 0x5ba08bU;default:return 0U;}};
   auto constructor_install=install;
   // A literal CRT allocator restore can republish this same game head.
   // Authenticate its complete journal, never an arbitrary equal-value write.
   if(install->pc==0x7800136a){
    constructor_install=std::find_if(install,source_accesses_.rend(),[&](const auto&a){return a.address==base&&a.bytes==4&&a.write&&a.value==head&&constructor_handler(a.pc);});
    bool proven=constructor_install!=source_accesses_.rend();unsigned crt_frame{};
    const auto same=[](const SourceAccess&a,unsigned pc,unsigned address,std::uint64_t value,unsigned write){return a.pc==pc&&a.address==address&&a.value==value&&a.bytes==4&&a.write==write;};
    if(proven){
     const auto begin=std::size_t(std::distance(source_accesses_.begin(),constructor_install.base())-1);
     const auto end=std::size_t(std::distance(source_accesses_.begin(),install.base())-1);
     for(std::size_t i=begin+1;proven&&i<=end;++i){
      const auto&a=source_accesses_[i];if(a.address!=base||!a.write)continue;
      if(a.pc==0x780012f9&&!crt_frame&&a.bytes==4&&a.value>=lower_stack&&a.value+12<=0x20002000&&a.value<head&&i>=2){
       crt_frame=unsigned(a.value);
       proven=same(source_accesses_[i-2],0x780012f2,base,head,0)&&same(source_accesses_[i-1],0x780012f8,crt_frame,head,1);
      }else if(a.pc==0x7800136a&&crt_frame&&same(a,0x7800136a,base,head,1)&&i){
       proven=same(source_accesses_[i-1],0x78001367,crt_frame,head,0);crt_frame=0;
      }else proven=false;
     }
     proven=proven&&!crt_frame;
    }
    if(!proven)constructor_install=source_accesses_.rend();
   }
   unsigned handler=constructor_install==source_accesses_.rend()?0:constructor_handler(constructor_install->pc);'''
 target=out/'fs_operations.inc';text=target.read_text();assert text.count(before)==1;target.write_text(text.replace(before,after,1))
 # Physical literal CRT operand identities are separately pinned, including
 # the exact saved-predecessor push, read and FS install/restore opcodes.
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 crt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pe=PEImage(crt.read_bytes())
 physical=[]
 for pc,wanted in [(0x780012f2,'64a100000000'),(0x780012f8,'50'),(0x780012f9,'64892500000000'),(0x78001367,'8b4df0'),(0x7800136a,'64890d00000000')]:
  lo=pe.rva_range(pc-pe.image_base,len(bytes.fromhex(wanted)))[0];actual=pe.data[lo:lo+len(bytes.fromhex(wanted))].hex();assert actual==wanted,(hex(pc),actual);physical.append(dict(pc=pc,source_hex=wanted))
 relations=[]
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':relations.append(dict(parent=str(p),child=str(out/p.name),parent_sha256=sha(p),child_sha256=sha(out/p.name),unchanged=sha(p)==sha(out/p.name)))
 assert [Path(x['child']).name for x in relations if not x['unchanged']]==['fs_operations.inc']
 (out/'constructor-restore-delta.json').write_text(json.dumps(dict(file='fs_operations.inc',before=before,after=after),indent=2)+'\n')
 (out/'constructor-restore-contract.json').write_text(json.dumps(dict(physical_CRT_instructions=physical,
  genuine_constructor_installs=[0x459b8e,0x4bf91e,0x4c031e,0x4c057e,0x58aece],
  scope='Only latest exact CRT allocator restoration0x7800136a may refer back to an original literal constructor install; intervening FS writes must be balanced exact allocator install/restore with saved-predecessor read/store joins',
  legacy_CRT_branch_unchanged=True,full12B_private_mirror_unchanged=True,initializer_credit=0),indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(R/'tools/analysis/pe.py')
 report=dict(passed=True,scope='Unexecuted exact constructor install/CRT restore provenance correction only',parent_service_path=str(parent/'report.json'),parent_service_sha256=sha(parent/'report.json'),
  actual_current_cause_path=str(cause),actual_current_cause_sha256=sha(cause),native_include=str(out),native_library=str(out/'registry_library.cpp'),
  changed_files=['fs_operations.inc'],source_relations=relations,legacy_CRT_FS_admission_unchanged=True,
  complete12B_private_frame_mirror=True,exact_intervening_CRT_source_provenance=True,source_after_seed=False,native_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
