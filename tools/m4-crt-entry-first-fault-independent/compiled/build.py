"""Own native-only first-fault causal controls with exact frozen entry objects."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-crt-entry';OUT=BASE/'independent-first-fault-compiled-r1'
SRC=Path(__file__).resolve().parent
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
PS=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
PINS={};COMMANDS=[]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Exact frozen source/artifact '+str(p));PINS[str(p)]=got;return p
def q(p):return "'"+str(p).replace("'","''")+"'"
def run(args,name,allow=False):
 args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=args,exit_code=r.returncode,log=str(p),sha256=sha(p)));need(allow or r.returncode==0,'Own actual first-fault compiled step '+name);return r.returncode,r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh independent actual control directory');OUT.mkdir(parents=True)
 try:
  prior=pin(BASE/'independent-first-fault-static-r2/report.json','f4a508cda2534aa961b37b9b2f63c6dacc9f768bf031b40652c8901502af4489');mapping=json.loads(pin(BASE/'independent-first-fault-static-r2/pins.json','477798097aacfcf80d0de49d50c26b26d540befff2bca53273d8599097b53fae').read_text())['files']
  for p,h in mapping.items():pin(p,h)
  build=pin(BASE/'first-fault-build-r4/build.json');b=json.loads(build.read_text());need(b['passed']and not b['original_executed'],'Frozen first-fault native-only candidate')
  for k in('source_files','primary_pre_call_tools','artifacts'):
   for p,h in b[k].items():pin(p,h)
  lit=OUT/'sources';lit.mkdir()
  for p in SRC.iterdir():
   if p.is_file():pin(p);(lit/p.name).write_bytes(p.read_bytes());pin(lit/p.name)
  cmake=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');compiler=pin(LLVM/'clang-cl.exe');pin(PS);pin(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');pin(sys.executable);results=[]
  for lv in('O0','O2'):
   obj=pin(BASE/'native-preparation-r1'/f'candidate-{lv}.obj');folder=OUT/lv;script=OUT/f'{lv}-build.ps1'
   script.write_text("$ErrorActionPreference='Stop'\nImport-Module "+q(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')+"\nEnter-VsDevShell -VsInstallPath "+q(VS)+" -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null\n& "+q(cmake)+" -S "+q(SRC)+" -B "+q(folder)+" -G Ninja -DCMAKE_MAKE_PROGRAM="+q(ninja)+" -DCMAKE_CXX_COMPILER="+q(compiler)+" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="+q('/DNDEBUG /clang:-'+lv)+" -DMW34_GUEST_OBJECT="+q(obj)+"\nif($LASTEXITCODE -ne 0){exit $LASTEXITCODE}\n& "+q(cmake)+" --build "+q(folder)+" --verbose\nexit $LASTEXITCODE\n")
   pin(script);run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',script],lv+'-build.log');exe=pin(folder/'controls.exe');code,output=run([exe,ROOT/'MW3/Mech3.exe',obj],lv+'-controls.log',True);results.append(dict(level=lv,exit_code=code,result=json.loads(output.strip())if code==0 else None,diagnostic=output.strip()if code else None,exe=str(exe),exe_sha256=sha(exe),object=str(obj),object_sha256=sha(obj)))
   for p in folder.rglob('*.obj'):pin(p)
  report=dict(passed=all(r['exit_code']==0 for r in results),scope='Own instrumented throwing checked-memory adapter, exact frozen complete-entry object to first deliberately unregistered required CRT service only. Whole State/pages/TIB/CPU/source events independently predicted; causal terminal faults and unentered refusals. Prefix candidate intentionally separate.',candidate_build=str(build),candidate_build_sha256=sha(build),prior_static_report=str(prior),results=results,author_fixture_model_executor_imported=False,original_executed=False,host_actual_FP_claim=False,full_SEH_dispatch=False,first_service_completed=False,full_CRT=False,whole_M4_complete=False,commands=COMMANDS)
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
  for p,h in PINS.items():need(sha(p)==h,'Final unchanged first-fault evidence')
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],bindings=len(PINS),report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
