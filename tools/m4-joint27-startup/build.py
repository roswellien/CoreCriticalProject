"""Fresh compile/link-only joint27 recipe. No worker execution in this file."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint27-startup';LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community');CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
ap=argparse.ArgumentParser();ap.add_argument('--derived',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();derived=Path(a.derived).resolve();out=Path(a.output).resolve();assert derived.parent==out.parent==BASE
trees={level:ROOT/f'build/m4-joint27-{out.name}-{level}' for level in ('O0','O2')};assert not out.exists() and not any(p.exists()for p in trees.values()),'All report/build directories must be fresh before mutation'
g=read(derived/'generation.json');assert g['passed']
for p,h in g['original_sources'].items()|g['generated_sources'].items():assert sha(p)==h,(p,h)
old=read(ROOT/'reports/m4-mixed-startup/native-r3/build.json');gates=old['prior_gates']
for name,(p,h)in gates.items():assert sha(ROOT/p)==h,(name,p)
out.mkdir();sources={};copies=[];commands=[];tools={};objects={};workers={};failure=None
def run(args,log):
 args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,capture_output=True);p=out/log;p.write_bytes(r.stdout+r.stderr);commands.append(dict(command=args,exit_code=r.returncode,log=str(p),log_sha256=sha(p)));tools[args[0]]=sha(args[0]);print(json.dumps(dict(program=Path(args[0]).name,log=log,exit_code=r.returncode)),flush=True);assert r.returncode==0,(args,r.stderr.decode(errors='replace')[-4000:])
try:
 for folder in ('tools/m4-joint27-startup','tools/m4-initializer-chain','tools/m4-integer-startup','tools/m4-runtime','tools/m4-startup','runtime','local/tools/remill-v6.0.1/remill-6.0.1/include'):
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and p.suffix in ('.cpp','.h','.hpp','.py','.ps1','.txt','.inc') and '__pycache__'not in p.parts:sources[str(p)]=sha(p)
 sources.update(g['original_sources']);sources.update(g['generated_sources']);sources[str(derived/'generation.json')]=sha(derived/'generation.json');sources[str(derived/'pins.json')]=sha(derived/'pins.json')
 for p,h in sources.items():
  q=out/'sources'/Path(p).relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(Path(p).read_bytes());assert sha(q)==h;copies.append(dict(original_path=p,preserved_path=str(q),sha256=h))
 os.environ['TEMP']=str(out);os.environ['TMP']=str(out);os.environ['TMPDIR']=str(out)
 codes={row['entry']:row['code']for row in read(ROOT/'reports/m4-fp-native/lift-r1/report.json')['roots']}
 for level,tree in trees.items():
  directory=out/level;directory.mkdir();obj=[];bindings=[]
  for component in g['ancestor_generation']['components']:
   group=[]
   for i,path in enumerate(component['modules']):
    module=derived/'derived'/Path(path).relative_to(Path(old['generation']).parent);verified=directory/f'{component["name"]}-{i}-verified.ll';artifact=directory/f'{component["name"]}-{i}.obj'
    run([LLVM/'opt.exe','-passes=verify','-S',module,'-o',verified],f'{level}-{component["name"]}-{i}-verify.log');run([LLVM/'llc.exe','-filetype=obj','-'+level,verified,'-o',artifact],f'{level}-{component["name"]}-{i}-llc.log');obj.append(str(artifact));group.append(artifact)
   for i,entry in enumerate(component['entries']):
    c=codes[entry];assert sha(c['path'])==c['sha256'];artifact=group[i if component['name']=='cosine' else 0];bindings.append('{0x%x,%d,"%s","%s","%s",&%s}'%(entry,c['size_bytes'],c['sha256'],sha(artifact),gates[component['name']][1],component['name']))
  linked=directory/'numeric-linked.ll';verified=directory/'numeric-verified.ll';numeric=directory/'numeric.obj'
  run([LLVM/'llvm-link.exe','-S',*[derived/'numeric-ir'/f'{x}-runtime.ll' for x in ('4c19f0','4c1a00','780c10f0')],'-o',linked],f'{level}-numeric-link.log');run([LLVM/'opt.exe','-passes=verify','-S',linked,'-o',verified],f'{level}-numeric-verify.log');run([LLVM/'llc.exe','-filetype=obj','-'+level,verified,'-o',numeric],f'{level}-numeric-llc.log');obj.append(str(numeric))
  prior={'chain':ROOT/f'reports/m4-initializer-chain/runtime-preflight-3/native-{level}.obj','integer':ROOT/f'reports/m4-integer-startup/batch-r2/native-{level}.obj'}
  for p in prior.values():obj.append(str(p))
  header='#pragma once\nnamespace mw34::m4_mixed {\nstruct FpBinding {std::uint32_t entry,bytes;const char*code,*object,*gate;m4_runtime::NativeEntry native;};\n'
  for name,p in prior.items():header+=f'inline constexpr const char*{name}_object="{sha(p)}",*{name}_gate="{gates[name][1]}";\n'
  header+=f'inline constexpr const char*numeric_object="{sha(numeric)}",*numeric_gate="{sha(derived/"generation.json")}";\n';header+='inline constexpr std::array<FpBinding,10>fp_bindings{{'+','.join(bindings)+'}};\n}\n';(directory/'mixed_bindings.hpp').write_text(header)
  flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid-offsetof'
  run([CMAKE,'-G','Ninja','-S',ROOT/'tools/m4-joint27-startup','-B',tree,f'-DMW34_DERIVED={derived}',f'-DMW34_BINDINGS={directory}',f'-DMW34_OBJECTS={";".join(obj)}',f'-DCMAKE_CXX_COMPILER={LLVM}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log');run([CMAKE,'--build',tree,'--parallel','8'],f'{level}-build.log')
  worker=tree/'mw34_joint27.exe';workers[level]=str(worker);objects[level]={p:sha(p)for p in obj}
  run([VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe','-C',tree,'-t','deps'],f'{level}-dependencies.txt')
 for p,h in sources.items():assert sha(p)==h,('Source changed during compilation',p)
except BaseException:
 failure=traceback.format_exc();(out/'failure.txt').write_text(failure);print(failure,flush=True)
finally:
 artifacts={str(p):sha(p)for p in out.rglob('*')if p.is_file()}
 for tree in trees.values():
  if tree.exists():
   for p in tree.rglob('*'):
    if p.is_file():artifacts[str(p)]=sha(p)
 tools[str(Path(sys.executable).resolve())]=sha(sys.executable)
 report=dict(passed=failure is None,scope='Fresh joint27 compile/link only. No executable invocation; source/ownership/COFF review required before bounded captures',failure=failure,generation=str(derived/'generation.json'),generation_sha256=sha(derived/'generation.json'),sources=sources,literal_sources=copies,commands=commands,tools=tools,artifacts=artifacts,objects=objects,workers=workers,prior_gates=gates,original_executed=False,worker_executed=False,full_ledger_completed=False,whole_M4_complete=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
if failure:raise SystemExit(1)
