"""Own actual outer-invoke causal fixtures; original/provider code never runs."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-fp-numeric-max-host-boundary'
OUT=BASE/'independent-compiled-r1'
SESSION=BASE/'derivation-r4'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
PS=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
PINS={};COMMANDS=[]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen dependency '+str(p));PINS[str(p)]=v;return p
def q(p):return "'"+str(p).replace("'","''")+"'"
def run(argv,name,allow_failure=False):
 argv=list(map(str,argv));r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p),sha256=sha(p)));need(allow_failure or r.returncode==0,'Actual own compiled step '+name);return r.returncode,r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh own boundary controls');OUT.mkdir(parents=True)
 try:
  report=pin(BASE/'author-review-r1/report.json','efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a');pin(BASE/'author-review-r1/pins.json','4abbd1d60ef7bba49ac434279f79090924700da169450f77119b8bba3897011e');build=pin(BASE/'native-build-r3/build.json','118a7579fb096d211b9ddfdc4ee3d19ba522ea95de6e0715c60f6469aadb90ad');b=json.loads(build.read_text());need(b['passed'],'Candidate native-build-r3')
  for p,h in b['source_files'].items():pin(p,h)
  pin(SESSION/'session.hpp');src=Path(__file__).resolve().parent;lit=OUT/'sources';lit.mkdir()
  for p in src.iterdir():
   if p.is_file():pin(p);(lit/p.name).write_bytes(p.read_bytes());pin(lit/p.name)
  cmake=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');pin(PS);pin(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');compiler=pin(LLVM/'clang-cl.exe');assembler=pin(LLVM/'clang.exe');asm=OUT/'boundary.obj';run([assembler,'-c',src/'boundary.s','-o',asm],'assembly.log');pin(asm);results=[]
  for level in ('O0','O2'):
   obj=pin(BASE/'native-build-r3'/f'native-{level}.obj');need(b['artifacts'][str(obj).replace('\\','\\\\')]==sha(obj) if str(obj) not in b['artifacts'] else b['artifacts'][str(obj)]==sha(obj),'Exact final compiled guest object')
   folder=OUT/level;script=OUT/f'{level}-build.ps1';script.write_text("$ErrorActionPreference='Stop'\nImport-Module "+q(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')+"\nEnter-VsDevShell -VsInstallPath "+q(VS)+" -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null\n& "+q(cmake)+" -S "+q(src)+" -B "+q(folder)+" -G Ninja -DCMAKE_MAKE_PROGRAM="+q(ninja)+" -DCMAKE_CXX_COMPILER="+q(compiler)+" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="+q('/DNDEBUG /clang:-'+level)+" -DMW34_GUEST_OBJECT="+q(obj)+" -DMW34_BOUNDARY_OBJECT="+q(asm)+" -DMW34_SESSION_DIR="+q(SESSION)+"\nif($LASTEXITCODE -ne 0){exit $LASTEXITCODE}\n& "+q(cmake)+" --build "+q(folder)+" --verbose\nexit $LASTEXITCODE\n");pin(script);run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',script],f'{level}-build.log');exe=pin(folder/'controls.exe');code,output=run([exe,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',obj,OUT/f'{level}-boundary.bin'],f'{level}-controls.log',True);raw=pin(OUT/f'{level}-boundary.bin');results.append(dict(level=level,exit_code=code,result=json.loads(output.strip()) if code==0 else None,diagnostic=output.strip() if code else None,raw=str(raw),raw_sha256=sha(raw),exe=str(exe),exe_sha256=sha(exe)))
   for p in folder.rglob('*.obj'):pin(p)
  outcome=dict(passed=all(x['exit_code']==0 for x in results),scope='Own outside-C++-return numeric invoke fixtures with actual success/fault/refusal/unsafe-State denials and full ABI/FP snapshots; original code not executed',candidate_build=str(build),candidate_build_sha256=sha(build),candidate_session=str(SESSION/'session.hpp'),candidate_session_sha256=sha(SESSION/'session.hpp'),prior_own_helper_derivation=str(src/'derivation.json'),results=results,commands=COMMANDS,author_fixture_model_or_executor_imported=False,original_executed=False,whole_M4_complete=False)
  p=OUT/'report.json';p.write_text(json.dumps(outcome,indent=2)+'\n');pin(p);pin(sys.executable)
  for p,h in PINS.items():need(sha(p)==h,'All inputs/results unchanged')
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=outcome['passed'],report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
