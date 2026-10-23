"""Author-side exact-inverse/compiled-closed-frontier audit; never execute target."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup142-runway/component-controls-r1';assert not out.exists();pins={};results={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prep=R/'reports/m4-startup142-runway/component-preparation-r3';build=R/'reports/m4-startup142-runway/component-build-r2'
 p=read(prep/'report.json','353213df81b3fa35839c6024acd8e92697882de858b980af4fb1a436a97f5c08');b=read(build/'build.json','d5af15dbddcdbc3a8ada9739c3d7ad04dee6f047a9077e1e65d316c090978533');assert p['passed']and b['passed']and not p['carried_domain_admitted']
 for n in ['component.cpp','component.hpp','source-inverse.json','hardware_boundary.s','control_runtime.cpp','generated_bridges.inc','literal_dispatch.hpp','fixture_spec_O0.hpp','fixture_spec_O2.hpp','CMakeLists.txt']:
  q=prep/n;pin(q,p['files'][str(q.resolve())])
 inv=read(prep/'source-inverse.json');src=pin(inv['parent_source'],inv['parent_sha256']).read_text();code=(prep/'component.cpp').read_text();tail=inv['added_component_tail'];assert code.endswith(tail);prefix=code[:-len(tail)];restored=prefix
 for d in reversed(inv['changes']):assert restored.count(d['new'])==1;restored=restored.replace(d['new'],d['old'])
 assert restored+inv['removed_standalone_tail']==src
 a='static Context &owner(void *p)';z='#include "generated_bridges.inc"';assert prefix[prefix.index(a):prefix.index(z)+len(z)]==src[src.index(a):src.index(z)+len(z)]
 assert len(inv['changes'])==6 and all(('fire('+str(i)+')')in prefix for i in range(1,9))
 assert 'bool Component::carried_domain_admitted()noexcept{return false;}'in tail
 gate=tail.index('need(Component::carried_domain_admitted()');assert gate<tail.index('r.memory().load<unsigned>')and gate<tail.index('const auto cw=')
 assert 'std::memset'not in tail and 'r.memory().write'not in tail and 'std::memcpy'not in tail and 'Runtime::external_return'not in code
 assert 'unsigned(s.rflag.flat)'in prefix and '0x8d5U'in prefix and 'Exact source DF assumption retained'in prefix
 assert (0x8d5&(1<<10))==0
 oldasm=pin(R/'tools/m4-hypot-native/hardware_boundary.s').read_text();newasm=(prep/'hardware_boundary.s').read_text();assert newasm.replace('mw34_hypot_borrow_hardware_call','hypot_hardware_call').replace('mw34_hypot_borrow_invoke_guarded','hypot_invoke_guarded')==oldasm
 out.mkdir(parents=True);llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';dump=pin(llvm/'llvm-objdump.exe');symbol='?carried_domain_admitted@Component@m4_hypot_borrow@mw34@@SA_NXZ'
 for level in ['O0','O2']:
  lib=pin(b['libraries'][level]['path'],b['libraries'][level]['sha256']);obj=pin(build/('build-'+level)/'CMakeFiles/hypot-borrow.dir/component.cpp.obj');deps=pin(build/(level+'-dependencies.log'));paths=sorted({line.strip()for line in deps.read_text().splitlines()if re.match(r'^    [A-Za-z]:[/\\]',line)})
  for q in paths:pin(q)
  args=[str(dump),'--disassemble-symbols='+symbol,str(obj)];v=subprocess.run(args,capture_output=True,timeout=30,creationflags=0x08000000);assert v.returncode==0;txt=v.stdout.decode();assert symbol in txt and re.search(r'xor[l]?\s+%eax,\s*%eax',txt)and 'retq'in txt
  q=out/(level+'-compiled-frontier.txt');q.write_bytes(v.stdout+v.stderr);pin(q)
  results[level]=dict(library=str(lib),sha256=sha(lib),component_object=str(obj),object_sha256=sha(obj),actual_dependency_files=len(paths),compiled_frontier=False,disassembly_command=args)
 for q,h in pins.items():assert sha(q)==h,q
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Author-side bounded exact source inverse and compiled closed-frontier controls only; independent adapter/full-link/current carried-input review required',source_inverse_entire_parent=True,exact_original_numeric_callback_body=True,exact_original_ASM_except_two_symbol_names=True,source_changes=6,all21_literal_objects_reused=True,all8_causal_injection_seams_preserved=True,full_refusal_retry_controller_composed=False,current142_input_domain_proved=False,execution_admitted=False,carried_domain_frontier=False,closed_before_guest_access_or_hardware=True,observed_ordinary_compiled_frontier=results,native_executed=False,worker_launched=False,archive_reader_opened=False,initializer_credit=0,accepted_count=131,superseded_artifacts=['component-preparation-r1:incorrect maskCD5 includedDF, preserved unexecuted','component-preparation-r2/component-build-r1:8D5 rawrflag guard but lacked separate assembled aflagDF guard; source frontier remained closed, preserved unexecuted'],files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True,libraries=results)))
if __name__=='__main__':main()
