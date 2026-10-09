"""Fresh additive compiled controls; seal literal recipe/artifacts before invocation."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-joint27-startup'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community');CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';NINJA=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();out=Path(a.output).resolve();assert out.parent==BASE
trees={level:ROOT/f'build/m4-joint27-{out.name}-{level}'for level in('O0','O2')};assert not out.exists()and not any(p.exists()for p in trees.values()),'Entire output and both build trees must be fresh'
bpath=BASE/'build-only-r1/build.json';assert sha(bpath)=='695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5';b=read(bpath);assert b['passed']
sources=dict(b['sources']);sources.update({str(p.resolve()):sha(p)for p in Path(__file__).parent.rglob('*')if p.is_file()and p.suffix in('.cpp','.txt','.py','.ps1')});sources[str(bpath)]=sha(bpath)
for p,h in b['sources'].items()|b['tools'].items()|b['artifacts'].items():assert sha(p)==h,(p,h)
out.mkdir();copies=[];commands=[];tools={};artifacts={};failure=None
for p,h in sources.items():
 q=out/'sources'/Path(p).relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(Path(p).read_bytes());assert sha(q)==h;copies.append(dict(original_path=p,preserved_path=str(q),sha256=h))
def run(args,log):
 args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240);q=out/log;q.write_bytes(r.stdout+r.stderr);commands.append(dict(command=args,exit_code=r.returncode,log=str(q),log_sha256=sha(q)));tools[args[0]]=sha(args[0]);print(json.dumps(dict(log=log,exit_code=r.returncode)),flush=True);assert r.returncode==0,(args,r.stderr.decode(errors='replace')[-4000:])
try:
 os.environ['TEMP']=os.environ['TMP']=str(out);derived=BASE/'derived-r1'
 for level,tree in trees.items():
  flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid offsetof'.replace('invalid offsetof','invalid- offsetof').replace('- offsetof','-offsetof')
  run([CMAKE,'-G','Ninja','-S',Path(__file__).parent,'-B',tree,f'-DMW34_ROOT={ROOT}',f'-DMW34_DERIVED={derived}',f'-DMW34_BINDINGS={BASE}/build-only-r1/{level}',f'-DMW34_OBJECTS={";".join(b["objects"][level])}',f'-DCMAKE_CXX_COMPILER={LLVM}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log')
  run([CMAKE,'--build',tree,'--parallel','8'],f'{level}-build.log');run([NINJA,'-C',tree,'-t','deps'],f'{level}-dependencies.txt')
  worker=tree/'mw34_joint27_controls.exe';recipe={'source_bindings':sources,'objects':b['objects'][level],'worker':str(worker),'worker_sha256':sha(worker),'arguments':[str(worker),str(ROOT/'MW3/Mech3.exe'),str(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),str(out/level)],'game_sha256':sha(ROOT/'MW3/Mech3.exe'),'provider_sha256':sha(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),'original_executed':False}
  (out/f'{level}-sealed-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
  # Compile-only handoff. A separate reviewed runner will rehash this literal
  # recipe and all dependencies before invoking either bounded unit worker.
 for p,h in sources.items():assert sha(p)==h,('Changed source',p)
except BaseException:
 failure=traceback.format_exc();(out/'failure.txt').write_text(failure);print(failure,flush=True)
finally:
 for directory in [out,*trees.values()]:
  if directory.exists():
   for p in directory.rglob('*'):
    if p.is_file():artifacts[str(p)]=sha(p)
 tools[str(Path(sys.executable).resolve())]=sha(sys.executable)
 report=dict(passed=failure is None,failure=failure,sources=sources,literal_sources=copies,tools=tools,artifacts=artifacts,commands=commands,scope='Compile-only whole-loop control fixture; review before execution',original_executed=False,worker_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');artifacts[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':artifacts|sources|tools},indent=2)+'\n')
if failure:raise SystemExit(1)
