"""Additive composition from accepted matherr and connected control contracts."""
import hashlib,json,pathlib,shutil,sys,re
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
BASE=ROOT/'reports/m4-crt-entry-control'
OLD=ROOT/'reports/m4-crt-entry-matherr/preparation-r3'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
def main(name):
 out=BASE/name;assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 for name in ('seed.hpp','matherr_context.hpp','composition.cpp','main_v2.inc','observations.hpp'):
  shutil.copyfile(OLD/name,out/(name+'.ancestor'))
  shutil.copyfile(HERE/name if (HERE/name).exists() else OLD/name,out/name)
 original=ROOT/'tools/m4-crt-control-integration/native_context.hpp'
 s=original.read_text();s=s.split('extern "C" unsigned __remill_read_memory_32(void*p,unsigned a){')[0]
 s=once(s,'#include "common.hpp"','#include "'+(ROOT/'tools/m4-crt-control-integration/common.hpp').as_posix()+'"')
 s=once(s,'#include <csetjmp>','#include <thread>')
 s=once(s,'extern "C" void*sub_5ac5a0(State*,unsigned,void*);','extern "C" void*sub_5ac5a0(State*,unsigned,void*) noexcept(false);')
 s=once(s,'extern "C" void*sub_780042e1(State*,unsigned,void*);','extern "C" void*sub_780042e1(State*,unsigned,void*) noexcept(false);')
 s=once(s,'struct Context{','struct BridgeAbort {};\nstruct Access{unsigned pc,address,value,width,write;};\nstruct Context{')
 s=once(s,'std::array<std::jmp_buf,4>boundaries{};unsigned boundary_depth{};bool failed{};const char*reason{};unsigned fault_pc{};',
  'unsigned boundary_depth{};bool active{},failed{},complete{};const char*reason{};unsigned fault_pc{},fault_address{};std::thread::id thread=std::this_thread::get_id();\n std::array<Access,256>accesses{};unsigned access_count{};\n void(*test_before_execute)(Context&,unsigned){};void(*test_after_access)(Context&,unsigned){};void(*test_after_event)(Context&,unsigned){};')
 s=once(s,'[[noreturn]]void deny(const char*w){if(!failed){failed=true;reason=w;fault_pc=state.gpr.rip.dword;}if(!boundary_depth)throw std::runtime_error(reason);std::longjmp(boundaries[boundary_depth-1],1);}',
  '[[noreturn]]void deny(const char*w,unsigned address=0){if(!failed){failed=true;reason=w;fault_pc=state.gpr.rip.dword;fault_address=address;}throw BridgeAbort{};}\n void guard(){if(owner!=this||!active||failed||thread!=std::this_thread::get_id())deny("Exact active serial control owner required");}\n void access(unsigned address,unsigned value,unsigned width,unsigned write){guard();if(access_count==accesses.size())deny("Control access bound",address);accesses[access_count++]={state.gpr.rip.dword,address,value,width,write};if(test_after_access)test_after_access(*this,access_count);}')
 s=once(s,'unsigned read32(unsigned a){if(a!=slot', 'unsigned read32(unsigned a,bool observed=false){guard();if(a!=slot')
 s=once(s,'if(bad)deny("Required checked32-bit read fault");return v;', 'if(bad)deny("Required checked32-bit read fault",a);if(observed)access(a,v,4,0);return v;')
 s=once(s,'void write32(unsigned a,unsigned v){if(!stack', 'void write32(unsigned a,unsigned v){guard();if(!stack')
 s=once(s,'if(bad)deny("Required checked32-bit write fault");}', 'if(bad)deny("Required checked32-bit write fault",a);access(a,v,4,1);}')
 s=once(s,'events[count++]={kind,pc,esp,ret};}', 'events[count++]={kind,pc,esp,ret};if(test_after_event)test_after_event(*this,count);}')
 s=once(s,'void state_identity(State*s,unsigned pc){if(', 'void state_identity(State*s,unsigned pc){guard();if(')
 s=once(s,'void wait(State*s,unsigned pc){const auto&f=', 'void wait(State*s,unsigned pc){guard();const auto&f=')
 start=s.index(' void execute(unsigned entry){');end=s.index('\n void tail(',start)
 s=s[:start]+''' void execute(unsigned entry){
  const bool outer=boundary_depth==0;if((entry!=wrapper&&entry!=provider_entry)||failed||boundary_depth==4||thread!=std::this_thread::get_id()||owner!=this||(outer?active:!active))throw std::runtime_error(reason?reason:"Connected boundary admission rejected");
  ++boundary_depth;if(outer)active=true;
  try{if(test_before_execute)test_before_execute(*this,entry);void*result=(entry==wrapper?sub_5ac5a0:sub_780042e1)(&state,entry,this);if(result!=this)deny("Connected compiled entry result identity rejected");}
  catch(BridgeAbort const&){--boundary_depth;if(outer)active=false;throw std::runtime_error(reason);}
  catch(...){--boundary_depth;if(outer)active=false;throw;}
  --boundary_depth;if(outer){active=false;complete=!failed&&depth==0;}if(failed)throw std::runtime_error(reason);
 }
''' + s[end:]
 s=s.replace('sub_5ac5a0','mw34_entry_control_sub_5ac5a0')
 (out/'control_context.hpp').write_text(s);shutil.copyfile(original,out/'control_context.hpp.ancestor')
 irpath=ROOT/'reports/m4-crt-control-integration/research-r1/host.ll';ir=irpath.read_text()
 mappings={n:'mw34_entry_control_'+n for n in ['sub_5ac5a0','sub_5ac5d6','__remill_flag_computation_zero','__remill_flag_computation_sign','__remill_undefined_8','__remill_compare_eq','__remill_compare_neq','__remill_flag_computation_carry','__remill_flag_computation_overflow']}
 renamed=ir
 for a,b in mappings.items():renamed=re.sub(r'(?<![A-Za-z0-9_.])'+re.escape(a)+r'(?![A-Za-z0-9_.])',b,renamed)
 reverse=renamed
 for a,b in mappings.items():reverse=reverse.replace(b,a)
 assert reverse==ir
 (out/'control.ll').write_text(renamed);shutil.copyfile(irpath,out/'control.ll.ancestor')
 files={str(p):sha(p)for p in out.iterdir() if p.is_file()}
 for p in [pathlib.Path(__file__),original,irpath,ROOT/'reports/m4-crt-entry-matherr/build-r3/build.json',OLD/'pins.json']:
  files[str(p.resolve())]=sha(p)
 for level in ('O0','O2'):
  p=ROOT/f'reports/m4-crt-control-integration/native-build-r1/native-{level}.obj';files[str(p)]=sha(p)
 report=dict(passed=True,scope='Additive CRT entry control preparation only',State_reseed_after_writer=False,State_reseed_after_control=False,provider_pages_remapped=False,control_exception_unwind='BridgeAbort plus decrement/active cleanup on all exit paths',control_IR_reverse_equal=True,control_IR_symbol_mapping=mappings,next_stop_PC=0x5ac440,next_stop_target=0x5ac598,native_component_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])
