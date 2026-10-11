"""Add only finite constructor borrowing to the immutable widget service3."""
from pathlib import Path
import hashlib,json,re,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh constructor service');out.mkdir(parents=True);pins={};relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact physical constructor service input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 parent=pin(R/'reports/m4-widget-native/service-preparation-r3/report.json','3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd');prior=json.loads(parent.read_bytes());need(prior['passed'],'Frozen prior service')
 validation=read(R/'reports/m4-constructor-original/chronological-validation-r3/report.json','00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95');need(validation['passed']and validation['reader_closed'],'Current genuine positive observations')
 source=read(R/'reports/m4-constructor-source/preparation-r1/report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf');rows=read(source['files']and R/'reports/m4-constructor-source/preparation-r1/source-instructions.json',source['files'][str((R/'reports/m4-constructor-source/preparation-r1/source-instructions.json').resolve())]);rows=rows['instructions']if isinstance(rows,dict)else rows
 for p in parent.parent.iterdir():
  if not p.is_file()or p.name=='report.json':continue
  pin(p,prior['files'][str(p.resolve())]);q=out/p.name;shutil.copyfile(p,q);relations.append(dict(parent=str(p),child=str(q),parent_sha256=sha(p)))
 h=out/'session.hpp';s=h.read_text();a='struct SessionImpl;';b=a+'\nstruct ConstructorOwner {unsigned guest,generation,requested,extent,measured_capacity,kind;std::uintptr_t native;};';need(s.count(a)==1,'One current service declaration');s=s.replace(a,b,1)
 a=' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);';b=a+'\n void borrow_constructor_mfc(State&,unsigned root,unsigned site,unsigned frame,unsigned return_pc);\n ConstructorOwner constructor_owner(unsigned guest,unsigned bytes);\n void constructor_owner_read(State&,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value);\n void constructor_source_write(State&,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value);';need(s.count(a)==1,'One public borrowed constructor seam');h.write_text(s.replace(a,b,1))
 descriptors=[]
 for row in rows:
  m=row['mnemonic'];ops=row['operands'];width=0
  if m in('push','call'):width=4
  elif '['in ops.split(',',1)[0]and m not in('cmp','test','lea'):
   width=1 if 'byte ptr'in ops.split(',',1)[0]else 2 if 'word ptr'in ops.split(',',1)[0]and 'dword ptr'not in ops.split(',',1)[0]else 4
  if width:descriptors.append(dict(pc=row['pc'],size=row['size'],bytes=row['bytes'],width=width,writing=True))
 dh=['struct ConstructorInstruction {unsigned pc,size,width;bool writing;std::array<unsigned char,16>bytes;};','inline constexpr ConstructorInstruction constructor_instructions[]{']
 for row in descriptors:dh.append('{%d,%d,%d,true,{%s}},'%(row['pc'],row['size'],row['width'],','.join(str(v)for v in bytes.fromhex(row['bytes']))))
 dh+=['};'];(out/'constructor_store_contract.inc').write_text('\n'.join(dh)+'\n')
 impl=out/'session_impl.inc';s=impl.read_text();a=' std::vector<std::array<unsigned,8>>projections;';b=a+'\n std::vector<std::array<std::uint64_t,12>>constructor_accesses_;';need(s.count(a)==1,'One exact private constructor ledger seam');s=s.replace(a,b,1)
 add=pin(R/'tools/m4-constructor-native/borrowed_constructor.inc').read_text();a=' void finish(){';need(s.count(a)==1,'One concrete constructor service insertion');s=s.replace(a,add+'\n'+a,1)
 a='case 0x479590:callback=0x4795d0;break;';b=a+'case 0x4103f0:callback=0x410420;break;case 0x410440:callback=0x410470;break;case 0x459b40:callback=0x459b70;break;';need(s.count(a)==1,'One three-root callback extension');s=s.replace(a,b,1)
 a='void Session::borrow_widget_onexit(State&s,unsigned root,unsigned frame,unsigned ret){impl_->borrow_widget_onexit(s,root,frame,ret);}'
 b=a+'\nvoid Session::borrow_constructor_mfc(State&s,unsigned root,unsigned site,unsigned frame,unsigned ret){impl_->borrow_constructor_mfc(s,root,site,frame,ret);}\nConstructorOwner Session::constructor_owner(unsigned guest,unsigned bytes){return impl_->constructor_owner(guest,bytes);}\nvoid Session::constructor_owner_read(State&s,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value){impl_->constructor_owner_read(s,root,pc,address,bytes,value);}\nvoid Session::constructor_source_write(State&s,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value){impl_->constructor_source_write(s,root,pc,address,bytes,value);}';need(s.count(a)==1,'One constructor public method forwarding seam');s=s.replace(a,b,1)
 a='  sink("heap-query-witness.bin",std::as_bytes(std::span(b.query_witness)),user);';b=a+'\n  sink("constructor-source-mirror-accesses.bin",std::as_bytes(std::span(i.constructor_accesses_)),user);';need(s.count(a)==1,'One exact constructor mirror witness emission');s=s.replace(a,b,1)
 s='#include "constructor_store_contract.inc"\n'+s;impl.write_text(s)
 for row in relations:row['child_sha256']=sha(row['child']);row['unchanged']=row['parent_sha256']==row['child_sha256'];pin(row['child'])
 need(sorted(Path(v['child']).name for v in relations if not v['unchanged'])==['session.hpp','session_impl.inc'],'Only disjoint private/public constructor source additions')
 for p in out.iterdir():pin(p)
 pin(__file__);report=dict(passed=True,scope='Unexecuted finite constructor service extension; actual same-session source MFC and whole native/guest extent mirrors; no initializer credit',parent_service_path=str(parent),parent_service_sha256=sha(parent),original_validation_sha256=sha(R/'reports/m4-constructor-original/chronological-validation-r3/report.json'),source_relations=relations,changed_files=['session.hpp','session_impl.inc'],store_descriptors=len(descriptors),native_include=str(out),native_library=str(out/'registry_library.cpp'),preserves_registry_root_zero_research_scope=True,does_not_infer_HeapSize_capacity=True,whole_native_and_guest_extent_mirror=True,cold_source_call_admission=False,native_executed=False,initializer_credit=0,source_AFTER_seed=False,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),store_descriptors=len(descriptors))))
if __name__=='__main__':main(sys.argv[1])
