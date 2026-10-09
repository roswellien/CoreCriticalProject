"""Fresh own compiled controls linked only to exact frozen production FDIV lib."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-crt-fdiv';OUT=BASE/'independent-compiled-r3'
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
def run(argv,name):
 argv=list(map(str,argv));r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p),sha256=sha(p)));need(r.returncode==0,'Actual own compiled step '+name);return r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh own controls');OUT.mkdir(parents=True)
 try:
  a=pin(BASE/'author-review-r1/report.json','c3398673510bc8ff28079173d486d8dfe73b1c481541927e37fccfbb94cc99e1');pin(BASE/'author-review-r1/pins.json','2d3272ed71e22449c4564cbfd728712a3cf9b00c69a2629c73f1369807123d42');build=pin(BASE/'native-build-r3/build.json');b=json.loads(build.read_text());need(b['passed'],'Frozen production gate')
  for p,h in b['sources'].items():pin(p,h)
  src=Path(__file__).resolve().parent;lit=OUT/'sources';lit.mkdir()
  for p in src.iterdir():
   if p.is_file():pin(p);(lit/p.name).write_bytes(p.read_bytes());pin(lit/p.name)
  cmake=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');pin(PS);pin(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');compiler=pin(LLVM/'clang-cl.exe');assembler=pin(LLVM/'clang.exe')
  asm=OUT/'boundary.obj';run([assembler,'-c',src/'boundary.s','-o',asm],'assembly.log');pin(asm);results=[]
  for level in ('O0','O2'):
   lib=pin(ROOT/f'build/m4-fdiv-native-build-r3-{level}/fdiv_registry.lib');need(b['artifacts'][str(lib)]==sha(lib),'Exact frozen library artifact consumed');folder=OUT/level;script=OUT/f'{level}-build.ps1'
   script.write_text("$ErrorActionPreference='Stop'\nImport-Module "+q(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')+"\nEnter-VsDevShell -VsInstallPath "+q(VS)+" -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null\n& "+q(cmake)+" -S "+q(src)+" -B "+q(folder)+" -G Ninja -DCMAKE_MAKE_PROGRAM="+q(ninja)+" -DCMAKE_CXX_COMPILER="+q(compiler)+" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="+q('/DNDEBUG /clang:-'+level)+" -DMW34_OWN_BOUNDARY="+q(asm)+" -DMW34_FDIV_LIBRARY="+q(lib)+"\nif($LASTEXITCODE -ne 0){exit $LASTEXITCODE}\n& "+q(cmake)+" --build "+q(folder)+" --verbose\nexit $LASTEXITCODE\n");pin(script)
   run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',script],f'{level}-build.log');exe=pin(folder/'controls.exe');r=json.loads(run([exe,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',BASE/'native-derived-r1/pack.bin'],f'{level}-controls.log').strip());need(r['passed'] and r['compiled_positive_writers']==12 and r['entered_faults']==15 and r['FNCLEX_words']==65536,'Actual own bounded extent');results.append(dict(level=level,result=r,exe=str(exe),sha256=sha(exe)))
   for p in folder.rglob('*.obj'):pin(p)
  report=dict(passed=True,scope='Own dirty-State native-only fixtures/actual API and first-fault/partial ownership/outside-assembly host-boundary controls; author fixtures/models/executor unused',candidate_build=str(build),candidate_build_sha256=sha(build),author_report_sha256=sha(a),results=results,commands=COMMANDS,isolated_late_fixture_scope='Direct negative bridge checks with actual OS prep, not complete compiled writer/OS NULL observations',original_or_provider_execution=False,full_M4_complete=False)
  p=OUT/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p);pin(sys.executable)
  for p,h in PINS.items():need(sha(p)==h,'Stable source/control identity')
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
