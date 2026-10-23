"""Compile typed ABI/source site and genuine API wrapper objects only."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-loader-message-review/ABI-build-r1';assert not out.exists();out.mkdir();pins={};runs=[];cl=Path(shutil.which('cl.exe'));objdump=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p)
 for level,option in [('O0','/Od'),('O2','/O2')]:
  dst=out/level;dst.mkdir()
  for name in('abi_witness','native_loader_provider'):
   source=Path(__file__).with_name(name+'.cpp');obj=dst/(name+'.obj');cmd=[str(cl),'/nologo','/c','/MD','/EHsc','/std:c++17',option,'/Fo'+str(obj),str(source)];result=subprocess.run(cmd,capture_output=True);p=dst/(name+'-compile.stdout');p.write_bytes(result.stdout);pin(p);p=dst/(name+'-compile.stderr');p.write_bytes(result.stderr);pin(p);assert result.returncode==0;pin(source);pin(obj);runs.append(dict(command=cmd,exit_code=result.returncode))
   result=subprocess.run([str(objdump),'--syms','--disassemble','--x86-asm-syntax=intel',str(obj)],capture_output=True,check=True);p=dst/(name+'-physical.txt');p.write_bytes(result.stdout);pin(p)
 for p in[cl,objdump,Path(__file__),Path(__file__).with_suffix('.ps1'),Path(sys.executable)]:pin(p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Both O0/O2 object compile/static ABI width/frame offset assertions and true Win64 LoadLibraryA/GetProcAddress wrapper; no linking/execution or complete hardware/source call witness',runs=runs,wide_module_export_handles=True,source_frame_sizes=[8,12],source_sites=[0x575f3a,0x575f54],native_module_owner_execution=False,source_volatile_CPU_FX_error_witness_pending=True,active_context_thread_module_alias_authentication_pending=True,actual_module_file_identity_runtime_pending=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
