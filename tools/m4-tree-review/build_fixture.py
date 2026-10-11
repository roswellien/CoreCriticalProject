"""Fresh O0/O2 link of isolated selected-tree fixture and frozen literal objects."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(preparation,digest,name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
 pins,commands,workers={},[],{};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or a==h,(str(p),h,a);assert str(p)not in pins or pins[str(p)]==a;pins[str(p)]=a;return p
 def run(args,log):
  args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=R,capture_output=True,timeout=240,creationflags=0x08000000)
  (out/log).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=log))
  print(json.dumps(dict(log=log,exit_code=r.returncode)),flush=True);assert r.returncode==0,log
 try:
  path=pin(preparation,digest);p=json.loads(path.read_bytes());assert p['passed'];prep=path.parent
  for q,h in(p['sources']|p['files']).items():pin(q,h)
  pin(__file__);pin(R/'tools/m4-tree-review/build_fixture.ps1')
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
  cmake=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
  ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
  os.environ['TEMP']=os.environ['TMP']=str(out)
  run([llvm/'clang.exe','--target=x86_64-pc-windows-msvc','-c',prep/'capture.s','-o',prep/'capture.obj'],'capture.log');pin(prep/'capture.obj')
  for level in('O0','O2'):
   tree=out/f'build-{level}';flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([cmake,'-G','Ninja','-S',prep,'-B',tree,f'-DCMAKE_MAKE_PROGRAM={ninja}',f'-DMW34_ROOT={R}',f'-DMW34_PREP={p["connected_include"]}',f'-DMW34_LEVEL={level}',
        f'-DMW34_REGISTRY={p["native_library"]}',f'-DMW34_REGISTRY_INCLUDE={p["native_include"]}',f'-DMW34_OBJECTS={";".join(p["objects"][level])}',
        f'-DMW34_WRITER={R}/reports/m4-capture-direct/build-r4/capture_direct-{level}.obj',f'-DCMAKE_CXX_COMPILER={llvm}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log')
   run([cmake,'--build',tree,'--parallel','6'],f'{level}-build.log')
   worker=pin(tree/'mw34_joint_startup124.exe');workers[level]=dict(path=str(worker),sha256=sha(worker),literal_objects=p['objects'][level])
  for q,h in pins.items():assert sha(q)==h,(q,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
 finally:
  artifacts={str(q):sha(q)for q in out.rglob('*')if q.is_file()}
  report=dict(passed=passed,scope='Fresh compiled O0/O2 isolated actual Runtime-selected tree fixture; source/native execution still pending',preparation=str(preparation),preparation_sha256=digest,
              native_preparation=p['native_preparation']if'p'in locals()else None,native_preparation_sha256=p['native_preparation_sha256']if'p'in locals()else None,
              workers=workers,commands=commands,sources=pins,artifacts=artifacts,native_executed=False,initializer_credit=0)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
  print(json.dumps(dict(passed=passed,sha256=sha(out/'build.json'))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
