"""Fresh standalone original compile; all inputs copied before compiler runs."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=Path(sys.argv[1]).resolve();assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists();out.mkdir(parents=True)
 src=ROOT/'tools/m4-fp-numeric-max';probe=ROOT/'reports/m4-fp-numeric-max/recovery-r1';cmake=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
 inputs=[p for p in src.glob('*') if p.is_file()]+[probe/'spec.hpp'];bindings={};sources=[]
 for p in inputs:
  copy=out/'sources'/p.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,copy);bindings[str(p.resolve())]=sha(p);sources.append({'path':str(p.resolve()),'sha256':sha(p),'copy':str(copy),'copy_sha256':sha(copy)})
 commands=[];passed=True
 for name,args in [('configure',[cmake,'-S',src,'-B',out/'build','-G','Visual Studio 18 2026','-A','Win32','-DMW34_PROBE_INCLUDE='+str(probe)]),('compile',[cmake,'--build',out/'build','--config','Release','--verbose'])]:
  r=subprocess.run(list(map(str,args)),capture_output=True,timeout=90);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);commands.append({'command':list(map(str,args)),'exit_code':r.returncode});passed &= r.returncode==0
  if not passed:break
 for p,digest in list(bindings.items()):assert sha(p)==digest,'Source changed during compile'
 for p in out.rglob('*'):
  if p.is_file():bindings[str(p.resolve())]=sha(p)
 bindings[str(cmake)]=sha(cmake);bindings[str(Path(sys.executable).resolve())]=sha(sys.executable)
 worker=out/'build/Release/mw34_numeric_reference.exe';report={'passed':passed,'original_worker':str(worker),'sources':sources,'bindings':bindings,'commands':commands}
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':passed,'worker':str(worker)}));assert passed
if __name__=='__main__':main()
