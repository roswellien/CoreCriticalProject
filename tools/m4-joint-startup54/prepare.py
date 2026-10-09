"""Fresh connected54 derivative; accepted28 artifacts remain immutable."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(nativeprep,nativepin,out):
 nativeprep=Path(nativeprep).resolve();out=Path(out).resolve();assert out.parent==ROOT/'reports/m4-joint-startup54' and not out.exists();out.mkdir(parents=True)
 pins={};generated={}
 def bind(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),h,v);pins[str(p)]=v;return v
 def write(p,s):
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');generated[str(p)]=bind(p)
 accepted=ROOT/'reports/m4-joint-startup28-root/acceptance-r2/report.json';bind(accepted,'3f3f1486b94b28e15eb09572965bdd4e861b0a286375db8fbcaf9b0a4902140a')
 parent=ROOT/'reports/m4-joint-startup28/preparation-r4';bind(parent/'report.json','e0ccb2851c7f065190488d91b81b5d2b970b0bf8f81a2640e623def5c4b06391');prior=json.loads((parent/'report.json').read_text())
 for p,h in json.loads((parent/'pins.json').read_text())['files'].items():bind(p,h)
 bind(nativeprep/'report.json',nativepin);native=json.loads((nativeprep/'report.json').read_text());assert native['passed']
 for p,h in json.loads((nativeprep/'pins.json').read_text())['files'].items():bind(p,h)
 source=ROOT/'reports/m4-onexit-source/lifts-r4/report.json';bind(source,'03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e');lift=json.loads(source.read_text())
 for p,h in lift['files'].items():bind(p,h)
 bind(ROOT/'tools/analysis/pe.py');game=ROOT/'MW3/Mech3.exe';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes())
 runtime_bindings={}
 for root in lift['roots']:
  entry=root['entry'];body=lift['source_bodies'][f'f_{entry:x}'];size=body['source_bytes'];offset,_=pe.rva_range(entry-pe.image_base,size);raw=pe.data[offset:offset+size]
  assert len(raw)==size and max(row['pc']+row['size']for row in body['instructions'])==entry+size
  for row in body['instructions']:
   assert row['pc']>=entry and raw[row['pc']-entry:row['pc']-entry+row['size']]==bytes.fromhex(row['bytes'])
  # Lifting input fills unexecuted holes with INT3. Runtime admission attests the
  # actual contiguous original image, while literal-row checks retain the lift.
  runtime_bindings[f'f_{entry:x}']=dict(entry=entry,size=size,file_offset=offset,original_sha256=hashlib.sha256(raw).hexdigest(),literal_lift_input_sha256=body['source_sha256'],decoded_bytes=body['unique_decoded_bytes'])
 write(out/'runtime-entry-bindings.json',json.dumps(dict(scope='Actual contiguous original image bindings; literal lift padding remains separately attested',roots=runtime_bindings),indent=2)+'\n')
 interface=ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json';bind(interface);contract=json.loads(interface.read_text());selected=contract['selected_order'];assert len(selected)==54
 extent=ROOT/'reports/m4-onexit-source/object-extent-r1/report.json';bind(extent,'9f002515208461064a5066438dfaa4d0a0662f05d55d041d3eee7fbc7ba6e541');assert json.loads(extent.read_text())['passed']
 roots=[x['entry']for x in lift['roots']];assert len(roots)==26
 # Preserve old fixed record ABI. Extra source pages and provider owners use named direct records.
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc'):
   bind(p);s=p.read_text().replace(parent.as_posix(),out.as_posix());write(out/p.relative_to(parent),s)
 protocol=(out/'joint_protocol.hpp').read_text();start=protocol.index('constexpr std::array<std::uint32_t,28> entries');end=protocol.index(';',start)
 protocol=protocol[:start]+'constexpr std::array<std::uint32_t,54> entries{'+','.join(hex(x['entry'])for x in selected)+'}'+protocol[end:]
 write(out/'joint_protocol.hpp',protocol)
 newpages=sorted((set(contract['source_data_pages'])|{0x63c000})-set([0x5bb000,0x604000,0x605000,0x60b000]))
 # Contract lists page objects or integer addresses depending on evidence producer version.
 assert len(newpages)==12,newpages
 extra='#pragma once\nnamespace mw34::m4_mixed {\nconstexpr std::array<unsigned,12> registration_pages{'+','.join(hex(x)for x in newpages)+'};\nconstexpr std::array<unsigned,26> registration_roots{'+','.join(hex(x)for x in roots)+'};\n}\n'
 write(out/'registration_contract.hpp',extra)
 # Shared generic integer bridge dispatch is changed only while private registry Session is active.
 chain=ROOT/'tools/m4-initializer-chain/component.cpp';bind(chain);s=chain.read_text().replace('#include "execution.hpp"','#include "D:/Projects/MW34Recomp/tools/m4-initializer-chain/execution.hpp"\n#include "onexit_session.hpp"')
 s=one(s,'return static_cast<Context *>(token)->read32(address);','if(mw34::m4_onexit::active())return unsigned(mw34::m4_onexit::read(token,address,4));return static_cast<Context *>(token)->read32(address);')
 s=one(s,'static_cast<Context *>(token)->write32(address,value);','if(mw34::m4_onexit::active())return mw34::m4_onexit::write(token,address,value,4);static_cast<Context *>(token)->write32(address,value);')
 s=one(s,'static_cast<Context *>(token)->write8(address,value);','if(mw34::m4_onexit::active())return mw34::m4_onexit::write(token,address,value,1);static_cast<Context *>(token)->write8(address,value);')
 s=one(s,'return static_cast<Context *>(token)->returned(*s,pc);','if(mw34::m4_onexit::active())return mw34::m4_onexit::returned(token,s,pc);return static_cast<Context *>(token)->returned(*s,pc);')
 write(out/'chain_dispatch.cpp',s)
 # Author library is separately frozen, compiled as its own TU to keep accepted Context namespace private.
 write(out/'onexit_session.hpp',(nativeprep/'session.hpp').read_text())
 s=(out/'native_main.cpp').read_text();s=one(s,'#include "spi_export.inc"','#include "spi_export.inc"\n#include "onexit_session.hpp"\n#include "registration_contract.hpp"')
 s=one(s,'std::unique_ptr<m4_spi_connected::Session>spi_;','std::unique_ptr<m4_spi_connected::Session>spi_;std::unique_ptr<m4_onexit::Session>registry_;')
 s=one(s,'FirstFault first_{};','FirstFault first_{};std::array<char,512>failure_text_{};')
 s=one(s,'}catch(...){observation=nullptr;failed_=true;', '}catch(...){if(!failure_text_[0]){try{throw;}catch(const std::exception&e){const auto n=std::min(std::strlen(e.what()),failure_text_.size()-1);std::memcpy(failure_text_.data(),e.what(),n);}catch(...){constexpr char message[]="Unknown connected54 exception";std::memcpy(failure_text_.data(),message,sizeof(message));}}observation=nullptr;failed_=true;')
 s=one(s,' void(*after_phase)(Context&,unsigned){};',' inline static thread_local Context*active_context{};\n void(*before_phase)(Context&,unsigned){};void(*after_phase)(Context&,unsigned){};void(*after_selected)(Context&){};\n static void registration_entry(m4_runtime::Runtime&r){auto*c=active_context;require(c&&&r==&c->r_&&observation,"Selected registry callback Context identity");overlay_cpu(c->s_,r.cpu());snapshot(r,c->s_,true);c->registry_->enter(r.cpu().eip);sync_fx(r,c->s_);snapshot(r,c->s_,false);observation->state_seeded=r.remill_seeded();}\n')
 s=one(s,'std::span<const std::byte>provider,unsigned repeat','std::span<const std::byte>provider,std::span<const std::byte>crt,unsigned repeat')
 s=one(s,'spi_=std::make_unique<m4_spi_connected::Session>(r_);r_.freeze_registry();seed(r_,repeat,cw,top);','spi_=std::make_unique<m4_spi_connected::Session>(r_);seed(r_,repeat,cw,top);registry_=std::make_unique<m4_onexit::Session>(r_,crt);\n#include "registration_bindings.inc"\n r_.freeze_registry();')
 s=one(s,'bool ok=false;unsigned phase=0;','bool ok=false;unsigned phase=0;active_context=this;')
 s=one(s,'auto ledger=r_.prepare_initializers','registry_->bootstrap();if(before_projection)before_projection(*this);\n   // A single explicit external game caller CPU projection; no State/FX/page/owner reseed.\n   r_.cpu()={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame+4,0x92837465,0x56473829,0xaabbccdd,0x202,broker};overlay_cpu(s_,r_.cpu());sync_fx(r_,s_);if(after_projection)after_projection(*this);\n   auto ledger=r_.prepare_initializers')
 s=one(s,'record.host_observation_kind=item.target.value==ni::root?2:item.target.value==m4_spi_connected::root?3:1;','const bool registration=std::find(registration_roots.begin(),registration_roots.end(),item.target.value)!=registration_roots.end();record.host_observation_kind=registration?4:item.target.value==ni::root?2:item.target.value==m4_spi_connected::root?3:1;if(before_phase)before_phase(*this,phase);')
 s=one(s,'record.numeric_phase?3U:record.spi_phase?2U:1U','record.numeric_phase?3U:record.spi_phase?2U:1U')
 s=one(s,'phase==28&&r_.calls().size()==31&&r_.translation_count()==29','phase==54&&r_.calls().size()==57&&r_.translation_count()==55')
 s=one(s,'ok=true;','if(after_selected)after_selected(*this);ok=true;')
 s=one(s,'  return ok;','  active_context=nullptr;return ok;')
 s=one(s,'m4_runtime::Runtime&runtime(){return r_;}','void(*before_projection)(Context&){};void(*after_projection)(Context&){};m4_onexit::Session&registry(){return *registry_;}const char*failure_reason()const noexcept{return failure_text_.data();}\n m4_runtime::Runtime&runtime(){return r_;}')
 s=s[:s.index('int main(int argc,char**argv)')]+(HERE/'main.inc').read_text();write(out/'native_main.cpp',s)
 objects={};bodymap=lift['source_bodies']
 inheritedbuild=ROOT/'reports/m4-crt-locale-batch/build-r9/build.json';bind(inheritedbuild);ib=json.loads(inheritedbuild.read_text());assert ib['passed']
 for level in('O0','O2'):
  added=[p for p in native['entry_objects']if Path(p).stem.endswith('-'+level)]
  libraries=[p for p in native['libraries']if '-'+level+'/'in p.replace('\\','/')]
  objects[level]=list(dict.fromkeys(prior['objects'][level]+added+libraries))
  for p in objects[level]:bind(p)
  lines=[]
  for entry in roots:
   body=bodymap[f'f_{entry:x}'];obj=body['objects'][level];actual=runtime_bindings[f'f_{entry:x}']
   lines.append('r_.register_translation({{'+hex(entry)+'},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal callback registration root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,'+str(actual['size'])+',"'+actual['original_sha256']+'","'+obj['sha256']+'","'+sha(source)+'"}});')
  write(out/level/'registration_bindings.inc','\n'.join(lines)+'\n')
  entry=[p for p in added if Path(p).name==f'candidate-{level}.obj'];control=[p for p in added if Path(p).name==f'control-{level}.obj'];assert len(entry)==len(control)==1
  write(out/level/'registry_build_bindings.hpp','#pragma once\n#define MW34_ENTRY_OBJECT_SHA "'+sha(entry[0])+'"\n#define MW34_CONTROL_OBJECT_SHA "'+sha(control[0])+'"\n#define MW34_INITTERM_SOURCE_SHA "960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678"\n#define MW34_REPLAY_INPUT_SHA "4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a"\n#define MW34_MAINARGS_RECOVERY_SHA "ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038"\n')
 for name in('CMakeLists.txt','build.py','build.ps1','main.inc'):
  p=HERE/name;bind(p);write(out/name,p.read_text())
 report={'passed':True,'scope':'Connected54 preparation only; literal26 registration + exact accepted28','objects':objects,'native_library':str(nativeprep/'registry_library.cpp'),'native_include':str(nativeprep),'generated_sources':generated,'physical_dependencies':pins,'parent_acceptance':str(accepted),'parent_acceptance_sha256':sha(accepted),'source_lifts':str(source),'source_lifts_sha256':sha(source),'selected_order':selected,'registration_roots':roots,'extra_pages':newpages,'connected_root_credit':False,'native_executed':False}
 write(out/'report.json',json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps({'files':pins|generated},indent=2)+'\n');print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json')}))
if __name__=='__main__':main(*sys.argv[1:])
