"""Compile closed-frontier numeric borrowing adapter; no executable or capture."""
from pathlib import Path
import hashlib,json,subprocess,sys,os,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup142-runway/component-build-r2';assert not out.exists();out.mkdir();pins={};commands=[];libs={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def run(args,label):
  args=list(map(str,args));pin(args[0]);v=subprocess.run(args,cwd=R,capture_output=True,timeout=180,creationflags=0x08000000);q=out/label;q.write_bytes(v.stdout+v.stderr);commands.append(dict(argv=args,exit_code=v.returncode,log=str(q)));print(json.dumps(dict(log=label,exit_code=v.returncode)),flush=True);assert v.returncode==0,label
 try:
  prep=R/'reports/m4-startup142-runway/component-preparation-r3';p=json.loads(pin(prep/'report.json','353213df81b3fa35839c6024acd8e92697882de858b980af4fb1a436a97f5c08').read_bytes());assert p['passed']and not p['carried_domain_admitted']
  for q,h in p['files'].items():pin(q,h)
  pin(__file__);pin(R/'tools/m4-138-constructor-readiness/build_hypot_borrow_v2.ps1');os.environ['TEMP']=os.environ['TMP']=str(out)
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community');cmake=vs/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';ninja=vs/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
  hardware=out/'hardware_boundary.obj';run([llvm/'clang.exe','-target','x86_64-pc-windows-msvc','-c',prep/'hardware_boundary.s','-o',hardware],'hardware-compile.log');pin(hardware)
  for level in ('O0','O2'):
   tree=out/('build-'+level);flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([cmake,'-G','Ninja','-S',prep,'-B',tree,'-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_CXX_COMPILER='+str(llvm/'clang-cl.exe'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS_RELEASE='+flags,'-DMW34_ROOT='+str(R),'-DMW34_LEVEL='+level,'-DMW34_REMILL='+p['remill_include'],'-DMW34_OBJECTS='+';'.join(p['objects'][level]),'-DMW34_HARDWARE='+str(hardware)],level+'-configure.log')
   run([cmake,'--build',tree,'--parallel','4'],level+'-build.log');q=pin(tree/'hypot-borrow.lib');libs[level]=dict(path=str(q),sha256=sha(q),literal_objects=p['objects'][level],hardware=str(hardware))
   run([ninja,'-C',tree,'-t','deps'],level+'-dependencies.log')
  for q,h in pins.items():assert sha(q)==h,q
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'build.json';q.write_text(json.dumps(dict(passed=passed,scope='O0/O2 compiled static borrowing numeric libraries only, source-closed admission frontier; no executable/current full-link/prelaunch',libraries=libs,preparation=str(prep/'report.json'),preparation_sha256=sha(prep/'report.json'),commands=commands,files=pins,artifacts={str(x):sha(x)for x in out.rglob('*')if x.is_file()},carried_domain_admitted=False,native_executed=False,archive_reader_opened=False,initializer_credit=0),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
