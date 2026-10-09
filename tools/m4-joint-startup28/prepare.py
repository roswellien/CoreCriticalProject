"""Additive, immutable28-root snapshot; frozen27 components retained by physical identity."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(out):
 out=Path(out).resolve();assert out.parent==ROOT/'reports/m4-joint-startup28' and not out.exists();out.mkdir(parents=True)
 pins={};generated={}
 def bind(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return v
 def write(p,s):
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');generated[str(p)]=bind(p)
 accepted=ROOT/'reports/m4-joint-startup27/root-acceptance-r1/report.json';bind(accepted);assert json.loads(accepted.read_text())['connected_roots']==27
 oldbuild=ROOT/'reports/m4-joint27-startup/build-only-r1/build.json';bind(oldbuild,'695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5');b=json.loads(oldbuild.read_text());assert b['passed']
 for p,h in b['sources'].items()|b['tools'].items()|b['artifacts'].items():bind(p,h)
 lift=ROOT/'reports/m4-spi-literal/lifts-r2/report.json';bind(lift,'c21820082d9720dbf65aa5c68b73273f3a98c51b689ef42a8305381f2b274682');l=json.loads(lift.read_text());assert l['passed']
 for p,h in json.loads(lift.with_name('pins.json').read_text())['files'].items():bind(p,h)
 parent=ROOT/'reports/m4-joint27-startup/derived-r1';mainpath=ROOT/'tools/m4-joint-startup27/native_main.cpp';bind(mainpath)
 protocol=(parent/'joint_protocol.hpp').read_text();bind(parent/'joint_protocol.hpp')
 protocol=one(protocol,'std::array<std::uint32_t,14> pages','std::array<std::uint32_t,17> pages');protocol=one(protocol,'0x78115000};','0x78115000,0x5e6000,0x608000,0x482000};')
 protocol=one(protocol,'std::array<std::uint32_t,27> entries','std::array<std::uint32_t,28> entries');protocol=one(protocol,'0x4674d0,0x4adb50','0x4674d0,0x482cf0,0x4adb50')
 protocol=protocol.replace('14*4096','17*4096')
 protocol=one(protocol,'struct Native {','struct SpiService {Cpu before,after;std::array<unsigned char,512>fx_before,fx_after;std::array<unsigned char,28>env_before,env_after;std::array<unsigned char,16>rect_before,rect_after;unsigned called,BOOL_value,guest_cleanup,provider_ESP_before,provider_ESP_after;};\nstruct SpiEvent {unsigned pc,address,value,width,operation;};\nstruct Native {')
 protocol=one(protocol,'std::uint32_t numeric_phase{},host_observation_kind{};','std::uint32_t numeric_phase{},host_observation_kind{};\n SpiService spi_service{};unsigned spi_phase{},spi_event_count{},spi_transport_count{};std::array<SpiEvent,64>spi_events{};')
 protocol=one(protocol,'sizeof(Common)==116964&&sizeof(Native)==132636','sizeof(Common)==141540&&sizeof(Native)==159716&&sizeof(SpiService)==1212')
 write(out/'joint_protocol.hpp',protocol)
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc') and p.name!='joint_protocol.hpp':
   bind(p);s=p.read_text();s=s.replace((parent/'joint_protocol.hpp').as_posix(),(out/'joint_protocol.hpp').as_posix());write(out/p.relative_to(parent),s)
 for p in HERE.glob('*'):
  if p.is_file()and p.suffix in('.hpp','.inc','.txt','.py','.ps1'):
   bind(p);write(out/p.name,p.read_text())
 s=mainpath.read_text();s=one(s,'#include "corpus.hpp"','#include "corpus.hpp"\n#include "spi_context.hpp"\n#include "spi_export.inc"\n#include "D:/Projects/MW34Recomp/tools/m4-capture-direct/capture_direct_v3.hpp"')
 s=s.replace('#include "../m4-initializer-chain/runtime_adapter.hpp"','#include "D:/Projects/MW34Recomp/tools/m4-initializer-chain/runtime_adapter.hpp"').replace('#include "../m4-integer-startup/runtime_adapter.hpp"','#include "D:/Projects/MW34Recomp/tools/m4-integer-startup/runtime_adapter.hpp"')
 s=s.replace('57344','69632').replace('sizeof(SequenceRecord)==122824','sizeof(SequenceRecord)==147400')
 s=one(s,'std::unique_ptr<ni::Session>session_;','std::unique_ptr<ni::Session>session_;std::unique_ptr<m4_spi_connected::Session>spi_;')
 s=one(s,'ni::NumericHostBoundary boundary(admitted_cw_);return invoke_selected_body','m4_spi_connected::ErrorBoundary caller_error;ni::NumericHostBoundary boundary(admitted_cw_);return invoke_selected_body')
 s=one(s,'session_->observe_root_entry=&root_entry;r_.freeze_registry();','session_->observe_root_entry=&root_entry;spi_=std::make_unique<m4_spi_connected::Session>(r_);r_.freeze_registry();')
 s=one(s,'ni::Session::Borrow borrow(*session_);','ni::Session::Borrow borrow(*session_);m4_spi_connected::Session::Borrow spi_borrow(*spi_);')
 s=one(s,'record.numeric_phase?3U:1U','record.numeric_phase?3U:record.spi_phase?2U:1U')
 s=one(s,'record.host_observation_kind=item.target.value==ni::root?2:1;','record.host_observation_kind=item.target.value==ni::root?2:item.target.value==m4_spi_connected::root?3:1;')
 s=one(s,'phase==27&&r_.calls().size()==29&&r_.translation_count()==28','phase==28&&r_.calls().size()==31&&r_.translation_count()==29')
 s=one(s,'if(session_->failed()){auto f=session_->fault();first_.pc=f.pc;first_.address=f.address;first_.step=f.step;first_.kind=2;}','if(session_->failed()){auto f=session_->fault();first_.pc=f.pc;first_.address=f.address;first_.step=f.step;first_.kind=2;}else if(spi_->failed()){auto f=spi_->fault();first_.pc=f.pc;first_.address=f.address;first_.step=f.step;first_.kind=3;}')
 s=one(s,'records.push_back(record);++phase;completed=phase;','records.push_back(record);++phase;completed=phase;if(after_phase)after_phase(*this,phase);')
 s=one(s,' unsigned completed{};',' void(*after_phase)(Context&,unsigned){};\n unsigned completed{};')
 s=one(s,'bool failed()const{return failed_;}FirstFault fault()const{return first_;}','m4_spi_connected::Session&spi(){return *spi_;}bool failed()const{return failed_;}FirstFault fault()const{return first_;}')
 s=s[:s.index('int main(int argc,char**argv)')]+(HERE/'main.inc').read_text()
 write(out/'native_main.cpp',s)
 objects={level:list(b['objects'][level])+[str(lift.parent/f'{name}-{level}.obj')for name in('initializer','thunk','helper')]for level in('O0','O2')}
 for pp in sum(objects.values(),[]):bind(pp)
 for level in('O0','O2'):
  q=out/level;q.mkdir();p=ROOT/f'reports/m4-joint27-startup/build-only-r1/{level}/mixed_bindings.hpp';bind(p);write(q/'mixed_bindings.hpp',p.read_text())
  write(q/'spi_bindings.hpp','#pragma once\nnamespace mw34::m4_spi_connected {\ninline constexpr char spi_source_sha[]="ec7d2aa54ab353ae3e298f2752ca2bce4eae1ebdb8c1ddeefde03cd044576859",spi_native_sha[]="'+sha(lift.parent/f'initializer-{level}.obj')+'",spi_gate_sha[]="'+sha(lift)+'";\n}\n')
 report={'passed':True,'scope':'Frozen27-derived source plus3literal SPI bodies, connected28 preparation only','objects':objects,'generated_sources':generated,'physical_dependencies':pins,'parent_acceptance':str(accepted),'parent_acceptance_sha256':sha(accepted),'SPI_source_report':str(lift),'SPI_source_report_sha256':sha(lift),'connected_root_credit':False,'native_executed':False}
 write(out/'report.json',json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps({'files':pins|generated},indent=2)+'\n');print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json')}))
if __name__=='__main__':main(sys.argv[1])
