"""Exercise the actual observer wrappers and audited direct-stack guard."""
from pathlib import Path
import json, subprocess
import apply_projection_bypass as patch
import harden_projection_watch as harden

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'local/gpu-projection-watch-r1/host-fixture'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 wrapper=patch.WRAPPERS[patch.WRAPPERS.index('extern "C" void mw34_projection_access'):]
 # Extract the guard emitted into the private host, rather than duplicating it.
 stage=(ROOT/'local/remaster/gpu-native-projection-watch-r1/host-source/mfc_stage.hpp').read_text()
 guard=stage[stage.index('inline void projection_ftol_span'):stage.index('inline bool ftol_core')]
 source=r'''
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <cstring>
struct State{unsigned pc{};};
namespace mf{
struct Runtime{int space;int&memory(){return space;}};
struct Owner{Runtime runtime;State state;unsigned calls{},observed_pc{};bool fail{};
 void guard(void*p){if(p!=&runtime.memory())throw std::runtime_error("Memory token mismatch");}
 void projection_access(unsigned,unsigned,unsigned,const State*s=nullptr){++calls;if(s)observed_pc=s->pc;unsigned short cw=0x27f;unsigned mx=0x3f80;
  __asm__ volatile("fldcw %0\n\tldmxcsr %1\n\tfnclex"::"m"(cw),"m"(mx):"memory");
  if(fail)throw std::runtime_error("Deliberate observer failure");
 }};
Owner*owner;
}
'''+wrapper+harden.WRAPPERS+guard+r'''
static void require(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
struct Fp{unsigned short cw,sw;unsigned mx;};
static Fp snapshot(){Fp f;__asm__ volatile("fnstcw %0\n\tfnstsw %1\n\tstmxcsr %2":"=m"(f.cw),"=m"(f.sw),"=m"(f.mx));return f;}
int main(){try{
 mf::Owner active;mf::owner=&active;
 for(bool flat:{false,true})for(bool fail:{false,true}){
  unsigned short cw=0xb7f;unsigned mx=0x5f80;__asm__ volatile("fldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mx):"memory");
  const Fp before=snapshot();active.fail=fail;bool caught=false;
  try{if(flat)mw34_projection_flat_access(&active.state,&active.runtime.memory(),0x72f41c,4,0);else mw34_projection_access(0x72f41c,4,0);}catch(const std::runtime_error&){caught=true;}
  const Fp after=snapshot();require(caught==fail,"Observer exception contract");
  require(before.cw==after.cw&&before.sw==after.sw&&before.mx==after.mx,"Observer did not restore host FP state");
 }
 active.fail=false;active.state.pc=0x57d6ce;
 mw34_projection_flat_access(&active.state,&active.runtime.memory(),0x72f424,4,0);
 require(active.observed_pc==0x57d6ce,"Flat observer lost explicit State");
 State other_state;int other;bool mismatch=false;
 try{mw34_projection_flat_access(&other_state,&active.runtime.memory(),0x72f41c,4,0);}catch(const std::runtime_error&){mismatch=true;}
 require(mismatch,"Flat observer accepted other State");mismatch=false;
 try{mw34_projection_flat_access(&active.state,&other,0x72f41c,4,0);}catch(const std::runtime_error&){mismatch=true;}
 require(mismatch,"Flat observer accepted other memory token");
 unsigned calls=active.calls;
 mw34_projection_memory_access(&other,0x72f41c,4,1);require(active.calls==calls,"Other address space altered tracker");
 mw34_projection_memory_access(&active.runtime.memory(),0x72f41c,4,1);require(active.calls==calls+1,"Active address space not observed");
 bool caught=false;try{mw34_projection_memory_access(&active.runtime.memory(),0,0x100000000ULL,1);}catch(const std::runtime_error&){caught=true;}
 require(caught&&active.calls==calls+1,"Transfer size truncated");
 projection_ftol_span(0,0x20001000);projection_ftol_span(0,0x72f418);projection_ftol_span(0,0x73042c);
 for(unsigned esp:{0U,15U,0x72f419U,0x72f41cU,0x73042bU,0xfffffffdU}){
  caught=false;try{projection_ftol_span(0,esp);}catch(const std::runtime_error&){caught=true;}require(caught,"Direct stack span overlap/wrap accepted");
 }
 caught=false;try{projection_ftol_span(0xffffffffU,16);}catch(const std::runtime_error&){caught=true;}require(caught,"Segment addition wrapped");
 std::puts("Host observer FP normal/unwind, memory identity, transfer width and direct-stack boundaries pass");
 }catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
'''
 cpp=OUT/'fixture.cpp';cpp.write_text(source)
 ps=OUT/'run.ps1';ps.write_text(f'''$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
& '{LLVM/'clang-cl.exe'}' /nologo /std:c++20 /MD /EHsc /O2 '{cpp}' '/Fe:{OUT/'fixture.exe'}' '/Fo:{OUT/'fixture.obj'}'
if($LASTEXITCODE){{throw 'Host fixture compile failed'}}
& '{OUT/'fixture.exe'}'
exit $LASTEXITCODE
''')
 run=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ps)],capture_output=True,text=True)
 (OUT/'run.log').write_text(run.stdout+run.stderr);print(run.stdout+run.stderr)
 (OUT/'result.json').write_text(json.dumps({'exit_code':run.returncode},indent=2))
 raise SystemExit(run.returncode)

if __name__=='__main__':main()
