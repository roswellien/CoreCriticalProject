"""Root-owned fresh compiled controls over frozen candidate source and COFFs."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;BASE=ROOT/'reports/m4-joint-startup28-root'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(buildpath,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={};commands=[];workers={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 def run(args,log):
  args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240);(out/log).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=log));print(json.dumps(dict(log=log,exit_code=r.returncode)),flush=True);assert r.returncode==0,log
 try:
  b=json.loads(pin(buildpath,digest).read_bytes());assert b['passed']
  for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  prep=Path(b['preparation']).parent;pin(__file__);fixture=pin(HERE/'fixture_v3.inc');capture=pin(ROOT/'tools/m4-crt-allocation/capture.s')
  (out/'fixture.cpp').write_text('#define main frozen_connected28_worker_main\n#include "'+(prep/'native_main.cpp').as_posix()+'"\n#undef main\n'+fixture.read_text())
  asm=capture.read_text();anchor='  movdqu 256(%r9), %xmm6';assert asm.count(anchor)==1;asm=asm.replace(anchor,'  fxrstor64 (%r9)\n  fldenv 512(%r9)\n'+anchor);(out/'capture.s').write_text(asm)
  cm=(prep/'CMakeLists.txt').read_text();cm=cm.replace('"${MW34_PREP}/native_main.cpp"','"'+(out/'fixture.cpp').as_posix()+'"').replace('${MW34_OBJECTS} "${MW34_WRITER}"','${MW34_OBJECTS} "'+(out/'capture.obj').as_posix()+'" "${MW34_WRITER}"');(out/'CMakeLists.txt').write_text(cm)
  for p in(out/'fixture.cpp',out/'capture.s',out/'CMakeLists.txt'):pin(p)
  llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';cmake=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
  os.environ['TEMP']=os.environ['TMP']=str(out)
  run([llvm/'clang.exe','--target=x86_64-pc-windows-msvc','-c',out/'capture.s','-o',out/'capture.obj'],'asm.log');pin(out/'capture.obj')
  p=json.loads((prep/'report.json').read_bytes())
  for level in('O0','O2'):
   tree=out/f'build-{level}';flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([cmake,'-G','Ninja','-S',out,'-B',tree,f'-DMW34_ROOT={ROOT}',f'-DMW34_PREP={prep}',f'-DMW34_LEVEL={level}',f'-DMW34_OBJECTS={";".join(p["objects"][level])}',f'-DMW34_WRITER={ROOT}/reports/m4-capture-direct/build-r4/capture_direct-{level}.obj',f'-DCMAKE_CXX_COMPILER={llvm}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log')
   run([cmake,'--build',tree,'--parallel','6'],f'{level}-build.log');worker=pin(tree/'mw34_joint_startup28.exe');workers[level]=dict(path=str(worker),sha256=sha(worker),objects=p['objects'][level])
  for pp,h in pins.items():assert sha(pp)==h,(pp,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  artifacts={str(p):sha(p)for p in out.rglob('*')if p.is_file()};report=dict(passed=passed,parent_build=str(buildpath),parent_build_sha256=digest,preparation=str(prep/'report.json'),workers=workers,commands=commands,sources=pins,artifacts=artifacts,native_executed=False,whole_M4_complete=False)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|artifacts|{str(out/'build.json'):sha(out/'build.json')}),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'build.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
