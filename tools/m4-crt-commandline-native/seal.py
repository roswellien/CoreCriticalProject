"""Durable physically rehashable author closure for the bounded command-line gate."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-commandline-native'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(out):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir();physical={};replacements=[];copies=[];commands=[]
 def pin(p,expected=None):
  p=Path(p).resolve();assert p.is_file(),p;h=sha(p);assert expected is None or h==expected,(p,'identity mismatch');prior=physical.get(str(p));assert prior is None or prior==h;physical[str(p)]=h;return h
 # All current public sources are literal-preserved before sealing. Private
 # old snapshots and failed evidence remain separate and are never overwritten.
 for base in (ROOT/'tools/m4-crt-commandline-native',ROOT/'tests/m4-crt-commandline-native'):
  for p in sorted(base.rglob('*')):
   if p.is_file() and '__pycache__' not in str(p):
    h=pin(p);copy=out/'literal'/p.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes());pin(copy,h);copies.append(dict(original=str(p),preserved=str(copy),sha256=h))
 doc=ROOT/'docs/m4-crt-commandline-native-contract.md';h=pin(doc);copy=out/'literal'/doc.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(doc.read_bytes());pin(copy,h);copies.append(dict(original=str(doc),preserved=str(copy),sha256=h))
 # Private gate history, not unrelated project/user files.
 for p in sorted(BASE.rglob('*')):
  if p.is_file() and not p.is_relative_to(out):pin(p)
 for p in sorted((ROOT/'build').glob('m4-cmd-*')):
  for f in sorted(p.rglob('*')):
   if f.is_file():pin(f)
 for p in sorted((ROOT/'build').glob('m4-crt-commandline-native-*')):
  for f in sorted(p.rglob('*')):
   if f.is_file():pin(f)
 # Source maps always resolve to their build's exact literal copies when a live
 # old path differs. Each historical association is explicit; old maps stay.
 for report in sorted(BASE.glob('*/build.json')):
  j=json.loads(report.read_text(encoding='utf-8-sig'))
  for key in ('source_files','sources','tools','tool_files','artifacts','inputs'):
   for original,h in j.get(key,{}).items():
    p=Path(original)
    if p.is_file() and sha(p)==h:pin(p,h);continue
    c=report.parent/'sources'/p.relative_to(ROOT);pin(c,h);replacements.append(dict(build=str(report),historical_path=str(p),physical_literal=str(c),sha256=h,reason='Original historical source path now superseded; exact literal build copy retained'))
 # Rehash r9's entire consumed component maps without changing its layout.
 r9=ROOT/'reports/m4-runtime/context-r9/build.json';pin(r9,'12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5');j=json.loads(r9.read_text(encoding='utf-8-sig'))
 for key in('source_files','tool_files','artifacts'):
  for p,h in j.get(key,{}).items():pin(p,h)
 for p in ('MW3/Mech3.exe','local/mw3-staged/Shared_DLLs/MSVCRT.DLL','tools/analysis/pe.py','tools/lifting/host_adapter.py','local/tools/remill-x87-control-repair/remill-lift-control-21.exe','local/tools/remill-x87-control-repair/semantics/x86.bc') :pin(ROOT/p)
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');pin(ninja)
 def run(argv,path):
  q=subprocess.run(list(map(str,argv)),capture_output=True,timeout=60);path.write_bytes(q.stdout+q.stderr);pin(path);assert q.returncode==0;commands.append(dict(command=list(map(str,argv)),exit=q.returncode,log=str(path),log_sha256=sha(path)));return q.stdout.decode(errors='strict')
 deps=set()
 for folder in ('build/m4-cmd-native-build-r3-O0','build/m4-cmd-native-build-r3-O2','build/m4-cmd-controls-compiled-controls-r5-O0','build/m4-cmd-controls-compiled-controls-r5-O2'):
  text=run([ninja,'-C',ROOT/folder,'-t','deps'],out/(Path(folder).name+'-deps.txt'))
  for line in text.splitlines():
   if line.startswith('    '):
    p=Path(line.strip())
    if p.is_file():pin(p);deps.add(str(p.resolve()))
 for tlog in (ROOT/'build/m4-crt-commandline-native-original-build-r3').rglob('*.read.*.tlog'):
  raw=tlog.read_bytes();text=raw.decode('utf-16') if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else raw.decode('utf-16-le') if raw else '';pin(tlog)
  for line in text.splitlines():
   for part in (line[1:].split('|') if line.startswith('^') else [line]):
    p=Path(part)
    if p.is_file():pin(p);deps.add(str(p.resolve()))
 # Actual loaded-owner API files are hashes from the native/original raw model.
 comp=BASE/'comparison-r4/report.json';assert json.loads(comp.read_text())['passed']
 for _,p,h in json.loads(comp.read_text())['owning_windows_files']:pin(p,h)
 for p in ('C:/Python314/python.exe','C:/Windows/System32/kernelbase.dll','C:/Windows/SysWOW64/kernelbase.dll'):pin(p)
 # Actual emitted objects and typed bridge relocations/unwind tables, never a
 # reconstructed or guessed compiled-function association.
 pin(llvm/'llvm-objdump.exe');pin(llvm/'llvm-readobj.exe');objects=[]
 for level in('O0','O2'):
  objects.append(BASE/f'native-build-r3/writer-{level}.obj')
  b=ROOT/f'build/m4-cmd-native-build-r3-{level}'
  objects.extend([b/'CMakeFiles/commandline_registry.dir/registry.cpp.obj',b/'CMakeFiles/commandline_native.dir/native_worker.cpp.obj'])
  b=ROOT/f'build/m4-cmd-controls-compiled-controls-r5-{level}'
  objects.extend(b.rglob('controls.cpp.obj'));objects.extend(b.rglob('publisher_controls.cpp.obj'))
 objects.extend((ROOT/'build/m4-crt-commandline-native-original-build-r3/commandline_original.dir/Release').glob('original*.obj'))
 for i,p in enumerate(objects):
  pin(p);run([llvm/'llvm-objdump.exe','-d','--x86-asm-syntax=intel','-r',p],out/f'object-{i}-decode.txt');run([llvm/'llvm-readobj.exe','--unwind',p],out/f'object-{i}-unwind.txt')
 assert len(objects)==12,len(objects)
 # Freeze report-scoped physically hashable files; own report/pins are external
 # final links, avoiding recursive hashes/cycles.
 bindings=[dict(path=p,sha256=h,bytes=Path(p).stat().st_size) for p,h in sorted(physical.items())]
 for b in bindings:assert sha(b['path'])==b['sha256']
 pins=out/'pins.json';pins.write_text(json.dumps(dict(bindings=bindings,historical_replacements=replacements,literal_sources=copies),indent=2))
 report=dict(passed_author_closure=True,pins_sha256=sha(pins),bindings=len(bindings),literal_sources=len(copies),historical_replacements=len(replacements),objects=len(objects),postbuild_read_dependencies=len(deps),commands=commands,native_build_sha256=sha(BASE/'native-build-r3/build.json'),original_build_sha256=sha(BASE/'original-build-r3/build.json'),capture_sha256=sha(BASE/'capture-repaired-normal-r1/capture.json'),comparison_sha256=sha(comp),compiled_controls_sha256=sha(BASE/'compiled-controls-r5/build.json'),worker_controls_sha256=sha(BASE/'worker-controls-normal-r1/report.json'),scope='Actual compiled eleven-byte provider writer plus explicit authored JMP/capture; own host query/read-only owning guest buffer and real game data-global route.384original/768native. No fabricated original RET, full CRT attach or connected startup/menu.',proof_limits=['Current/post-build dependency hashes do not establish full execution-time tool/process closure','Original State and per-access events remain unobserved; native fullState/volatile preservation is a representative policy','Normal Windows corpus; sandbox failures/history retained','Tiny typed abort real C++ unwind denial controls; old noexcept longjmp C0000409 parameter7 remains preserved','Sequential private ordinary dirs only; concurrent/reparse/host mapping attacks excluded','Observer-source-preservation-r1 explicitly excludes wrong reconstruction-attempt file from historical-source association'])
 (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(report_sha256=sha(out/'report.json'),pins_sha256=sha(pins),bindings=len(bindings),objects=len(objects))))
if __name__=='__main__':main(sys.argv[1])
