"""Direct numerical host observation; immutable earlier control history retained."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/m4-fp-numeric-max-integration/independent-direct-host-r1'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
PS=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={};COMMANDS=[]
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));PINS[str(p)]=v;return p
def q(p):return "'"+str(p).replace("'","''")+"'"
def run(argv,name):
 argv=list(map(str,argv));r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p)));need(r.returncode==0,'Actual direct probe step '+name);return r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh probe');OUT.mkdir(parents=True)
 try:
  src=Path(__file__).resolve().parent;lit=OUT/'sources';lit.mkdir()
  for p in list(src.iterdir())+[src.parent/'controls.cpp']:
   if p.is_file():pin(p);(lit/p.name).write_bytes(p.read_bytes());pin(lit/p.name)
  cmake=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');compiler=pin(LLVM/'clang-cl.exe');pin(PS);pin(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
  b=ROOT/'reports/m4-fp-numeric-max-integration/native-build-r5';pin(b/'build.json','ad8c4b5f2e869da3fe664dc835ef59e529a156e95e3917da3ea170aab092a9cc');results=[]
  for level in ('O0','O2'):
   obj=pin(b/f'native-{level}.obj');folder=OUT/level;script=OUT/f'{level}-build.ps1'
   script.write_text("$ErrorActionPreference='Stop'\nImport-Module "+q(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')+"\nEnter-VsDevShell -VsInstallPath "+q(VS)+" -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null\n& "+q(cmake)+" -S "+q(src)+" -B "+q(folder)+" -G Ninja -DCMAKE_MAKE_PROGRAM="+q(ninja)+" -DCMAKE_CXX_COMPILER="+q(compiler)+" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="+q('/DNDEBUG /clang:-'+level)+" -DMW34_INDEPENDENT_OBJECT="+q(obj)+"\nif($LASTEXITCODE -ne 0){exit $LASTEXITCODE}\n& "+q(cmake)+" --build "+q(folder)+" --verbose\nexit $LASTEXITCODE\n");pin(script)
   run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',script],f'{level}-build.log');exe=pin(folder/'probe.exe');raw=OUT/f'{level}.bin'
   r=json.loads(run([exe,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',obj,raw],f'{level}-probe.log'));pin(raw);need(r['passed'] and r['after_capture_before_restore'],'Direct capture ordering');results.append(dict(level=level,result=r))
   for p in folder.rglob('*.obj'):pin(p)
  report=dict(passed=True,scope='Direct actual host snapshots across unchanged r5 Session, before any harness restore; observation only',results=results,commands=COMMANDS,original_executed=False)
  p=OUT/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p);pin(sys.executable)
  for p,h in PINS.items():need(sha(p)==h,'Stable final probe dependency')
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
