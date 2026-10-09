"""Own native causal controls against exact frozen Session/guest objects.

No author executor/fixture/model import and no original/provider execution.
"""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/m4-fp-numeric-max-integration/independent-compiled-session-r3';PINS={};COMMANDS=[]
BASE=ROOT/'reports/m4-fp-numeric-max-integration/native-build-r5'
PS=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
def need(x,why):
 if not x:raise ValueError(why)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact dependency '+str(p));PINS[str(p)]=v;return p
def quote(p):return "'"+str(p).replace("'","''")+"'"
def run(args,path):
 args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);path.write_bytes(r.stdout);pin(path);COMMANDS.append(dict(command=args,exit_code=r.returncode,log=str(path),sha256=sha(path)));need(r.returncode==0,'Own actual step '+str(path));return r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh independent build/report');OUT.mkdir(parents=True)
 try:
  candidate=pin(BASE/'build.json','ad8c4b5f2e869da3fe664dc835ef59e529a156e95e3917da3ea170aab092a9cc');build=json.loads(candidate.read_text());need(build['passed'],'Frozen positive native candidate')
  for p,h in build['source_files'].items():pin(p,h)
  src=ROOT/'tools/m4-fp-numeric-max-session-independent';literal=OUT/'sources';literal.mkdir()
  for p in src.iterdir():
   if p.is_file():pin(p);(literal/p.name).write_bytes(p.read_bytes());pin(literal/p.name)
  cmake=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=pin(VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');compiler=pin(LLVM/'clang-cl.exe');pin(PS);pin(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
  results=[]
  for b in build['builds']:
   level=b['level'];folder=OUT/level;need(not folder.exists(),'Fresh actual own derived build');obj=pin(b['object'],build['artifacts'][b['object']])
   script=OUT/(level+'-build.ps1');script.write_text("$ErrorActionPreference='Stop'\nImport-Module "+quote(VS/'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')+"\nEnter-VsDevShell -VsInstallPath "+quote(VS)+" -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null\n& "+quote(cmake)+" -S "+quote(src)+" -B "+quote(folder)+" -G Ninja -DCMAKE_MAKE_PROGRAM="+quote(ninja)+" -DCMAKE_CXX_COMPILER="+quote(compiler)+" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="+quote('/DNDEBUG /clang:-'+level)+" -DMW34_INDEPENDENT_OBJECT="+quote(obj)+"\nif($LASTEXITCODE -ne 0){exit $LASTEXITCODE}\n& "+quote(cmake)+" --build "+quote(folder)+" --verbose\nexit $LASTEXITCODE\n");pin(script)
   run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',script],OUT/(level+'-build.log'))
   exe=pin(folder/'controls.exe');out=run([exe,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',obj],OUT/(level+'-controls.log'));r=json.loads(out.strip());need(r['passed'] and r['positive_phases']==436 and r['entered_faults']==12 and r['corrected_poison_retries']==12,'Actual own expected extent');results.append(dict(level=level,result=r,exe=str(exe),sha256=sha(exe)))
   for p in folder.rglob('*.obj'):pin(p)
  report=dict(passed=True,scope='Independent compiled native Session controls and input-derived State/page/access effects; no original or author fixture/model reuse',consumed_build_sha256=sha(candidate),results=results,commands=COMMANDS,original_or_provider_executed=False,whole_M4_complete=False)
  path=OUT/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');pin(path);pin(sys.executable)
  for p,h in PINS.items():need(sha(p)==h,'Final stable identity '+p)
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(path),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
