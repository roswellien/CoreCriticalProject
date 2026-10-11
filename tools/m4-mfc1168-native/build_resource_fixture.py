"""Compile each finite13-object literal fixture; no native execution here."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(preparation,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};commands=[];workers={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or a==h,(str(p),h,a);assert str(p)not in pins or pins[str(p)]==a;pins[str(p)]=a;return p
 def run(args,label):
  args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=R,capture_output=True,timeout=240,creationflags=0x08000000);(out/label).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=label));print(json.dumps(dict(log=label,exit_code=r.returncode)),flush=True);assert r.returncode==0,label
 try:
  p=json.loads(pin(preparation,digest).read_bytes());assert p['passed'];prep=Path(preparation).parent
  for q,h in p['files'].items():pin(q,h)
  pin(__file__);pin(R/'tools/m4-mfc1168-native/build_fixture.py');pin(R/'tools/m4-mfc1168-native/derive_build_v2.py');pin(R/'tools/m4-mfc1168-native/build_fixture.ps1');os.environ['TEMP']=os.environ['TMP']=str(out)
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';cmake=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
  run([llvm/'clang.exe','--target=x86_64-pc-windows-msvc','-c',prep/'hardware_boundary.s','-o',out/'hardware_boundary.obj'],'hardware-compile.log');pin(out/'hardware_boundary.obj');pin(llvm/'clang-cl.exe');pin(ninja);pin(R/'tools/m4-mfc1168-native/derive_resource_build.py');pin(R/'tools/m4-mfc1168-native/build_resource_fixture.ps1')
  for level in('O0','O2'):
   tree=out/f'build-{level}';flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([cmake,'-G','Ninja','-S',prep,'-B',tree,f'-DCMAKE_MAKE_PROGRAM={ninja}',f'-DCMAKE_CXX_COMPILER={llvm}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}',f'-DMW34_ROOT={R}',f'-DMW34_LEVEL={level}',f'-DMW34_REMILL={p["remill_include"]}',f'-DMW34_HARDWARE_OBJECT={out}/hardware_boundary.obj',f'-DMW34_OBJECTS={";".join(p["objects"][level])}'],f'{level}-configure.log')
   run([cmake,'--build',tree,'--parallel','4'],f'{level}-build.log');worker=pin(tree/'mfc1168-native.exe');workers[level]=dict(path=str(worker),sha256=sha(worker),literal_objects=p['objects'][level])
  for q,h in pins.items():assert sha(q)==h,(q,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Compiled O0/O2 actual registered Runtime fixture; execution unstarted',preparation=str(preparation),preparation_sha256=digest,workers=workers,commands=commands,files=pins,artifacts={str(q):sha(q)for q in out.rglob('*')if q.is_file()},native_executed=False,initializer_credit=0)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'build.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
