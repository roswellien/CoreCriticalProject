"""Asset-free production-recipe fixture for watched flat guest accesses."""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, re
import flat_projection_watch as watch

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'local/gpu-projection-bypass-r1/flat-watch-fixture'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source='target triple = "x86_64-pc-windows-msvc"\n'
 for width,ty in watch._cleanup.FLAT_TY.items():
  # Numeric basic blocks and PHI nodes deliberately exercise LLVM inlining CFG.
  source+=f'''
define {ty} @mw34_attach_watch{width}_body(ptr %state, i32 %address, ptr %memory) {{
  %v = call {ty} @__remill_read_memory_{width}(ptr %memory, i32 %address)
  %m = call ptr @__remill_write_memory_{width}(ptr %memory, i32 %address, {ty} %v)
  ret {ty} %v
}}
declare {ty} @__remill_read_memory_{width}(ptr, i32)
declare ptr @__remill_write_memory_{width}(ptr, i32, {ty})
'''
 source+='''
define void @mw34_attach_watch_store_body(ptr %state, i32 %address, ptr %memory, i32 %value) {
  %m = call ptr @__remill_write_memory_32(ptr %memory, i32 %address, i32 %value)
  ret void
}

define i32 @mw34_attach_watch_phi_body(ptr %state, i32 %address, ptr %memory) {
  %1 = load i32, ptr %state
  %2 = call i32 @__remill_read_memory_32(ptr %memory, i32 %address)
  %3 = icmp eq i32 %1, 7
  br i1 %3, label %4, label %6
4:
  %5 = add i32 %2, 1
  br label %8
6:
  %7 = add i32 %2, 2
  br label %8
8:
  %9 = phi i32 [ %5, %4 ], [ %7, %6 ]
  %10 = call ptr @__remill_write_memory_32(ptr %memory, i32 %address, i32 %9)
  ret i32 %9
}
define void @mw34_attach_watch80_body(ptr %state, i32 %address, ptr %memory) {
  %raw = alloca [10 x i8], align 1
  %r = call ptr @__remill_read_memory_f80(ptr %memory, i32 %address, ptr %raw)
  %w = call ptr @__remill_write_memory_f80(ptr %memory, i32 %address, ptr %raw)
  ret void
}
declare ptr @__remill_read_memory_f80(ptr, i32, ptr)
declare ptr @__remill_write_memory_f80(ptr, i32, ptr)
define float @mw34_attach_watch_fp_body(ptr %state, i32 %address, ptr %memory) {
  call void asm sideeffect "", "~{memory},~{dirflag},~{fpsr},~{flags}"()
  %a = call float @__remill_read_memory_f32(ptr %memory, i32 %address)
  %b = fadd float %a, 1.000000e+00
  call void asm sideeffect "", "~{memory},~{dirflag},~{fpsr},~{flags}"()
  ret float %b
}
'''
 # State and guest token intentionally retain the production noalias ABI.
 # The observer must receive both explicitly, or State PC stores can disappear.
 source=re.sub(r'^define [^\n]+',lambda m:m.group(0).replace('ptr %state','ptr noalias %state').replace('ptr %memory','ptr noalias %memory'),source,flags=re.M)
 source=re.sub(r'^(define [^\n]+\{)\n',r'\1\n  %watch_pc = getelementptr i8, ptr %state, i32 4\n',source,flags=re.M)
 source=re.sub(r'^(  %[\w.]+ = call [^\n]*@__remill_(read|write)_memory_[^\n]+)$',lambda m:'  store i32 '+str(0x540985 if m.group(2)=='read' else 0x540994)+', ptr %watch_pc, align 1\n'+m.group(1),source,flags=re.M)
 (OUT/'source.ll').write_text(source)
 source,cleanup=watch._cleanup.transform(source)
 source,annotate=watch._cleanup.annotate(source)
 source,strict=watch._cleanup.strict_x87(source)
 assert strict['strict_applied']==1
 stats={};source=watch.watched_flat_mem(source,stats)
 assert stats['flat_watch_unhandled_count']==0 and stats['flat_watch_f80_reads']==1 and stats['flat_watch_f80_writes']==1
 # Unknown widths and unsupported CFG call forms are classified, never silently
 # counted as covered. No unsupported call is changed into a fabricated result.
 unknown={}
 watch.watched_flat_mem('  %v = call ptr @__remill_read_memory_f128(ptr %memory, i32 %address, ptr %raw)\n',unknown)
 assert unknown['flat_watch_unhandled']=={'read_f128':1}
 invoked={}
 watch.watched_flat_mem('  %v = invoke ptr @__remill_write_memory_f80(ptr %memory, i32 %address, ptr %raw) to label %ok unwind label %fail\n',invoked)
 assert invoked['flat_watch_unhandled']=={'write_f80':1}
 try:
  watch.watched_flat_mem(source,{})
 except ValueError:
  pass
 else:
  raise AssertionError('Repeated instrumentation accepted')
 try:
  watch.watched_flat_mem('  %v = call i32 @__remill_read_memory_32(ptr %memory, i32 %address)\n',{})
 except ValueError:
  pass
 else:
  raise AssertionError('Guest access without an explicit State argument accepted')
 source+=f'''
define void @fixture_range(ptr noalias %state, ptr noalias %memory, i32 %address, i32 %size, i32 %write) uwtable {{
  call void @{watch.HELPER}(ptr %state, ptr %memory, i32 %address, i32 %size, i32 %write)
  ret void
}}
'''
 (OUT/'watched.ll').write_text(source)
 script=OUT/'run.ps1'
 script.write_text('''$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
'''+f'''& '{LLVM/'clang.exe'}' -O2 -c '{OUT/'watched.ll'}' -o '{OUT/'watched.obj'}'
if($LASTEXITCODE){{throw 'Watch IR compile failed'}}
& '{LLVM/'opt.exe'}' '-passes=default<O2>' -S '{OUT/'watched.ll'}' -o '{OUT/'optimized.ll'}'
if($LASTEXITCODE){{throw 'Watch optimize failed'}}
& '{LLVM/'clang-cl.exe'}' /nologo /std:c++20 /O2 /MD /EHsc '{ROOT/'tools/remaster-launcher/test_flat_projection_watch.cpp'}' '/Fe:{OUT/'fixture.exe'}' '/Fo:{OUT/'fixture.obj'}' /link '{OUT/'watched.obj'}'
if($LASTEXITCODE){{throw 'Watch C++ compile failed'}}
Set-Location '{OUT}'
& '{OUT/'fixture.exe'}'
exit $LASTEXITCODE
''')
 run=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],capture_output=True,text=True)
 (OUT/'run.log').write_text(run.stdout+run.stderr)
 result=dict(exit_code=run.returncode,cleanup=cleanup,annotate=annotate,strict=strict,watch=stats)
 files=[Path(__file__),Path(watch.__file__),watch._path,ROOT/'tools/remaster-launcher/test_flat_projection_watch.cpp',OUT/'source.ll',OUT/'watched.ll',LLVM/'clang.exe',LLVM/'opt.exe']
 result['pins']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 (OUT/'closure.json').write_text(json.dumps(result,indent=2))
 print(run.stdout+run.stderr);print(json.dumps(result,indent=2));raise SystemExit(run.returncode)

if __name__=='__main__':main()
