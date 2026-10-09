"""Record actual fresh static compile/link/run commands for the mixed candidate."""
from pathlib import Path
import argparse,hashlib,json,subprocess,traceback,os,re
ROOT=Path(__file__).resolve().parents[2]
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
GATES={
 'first':('reports/m4-fp-directed/independent-review-r1/author-association-r1/report.json','28ae2c88de7209cdbaeecaef50fe5457c7831391a09a6c276c24f6692f04aefb'),
 'simple':('reports/m4-fp-simple-batch/independent-review-r1/report.json','dd4d77184ff54213867435d9328bb524cabfc884c29bab9145b01034e4f05f05'),
 'sqrt':('reports/m4-fp-sqrt/independent-review-r1/report.json','c0b4cbfa83bd44ec38a885c066531d746844d3fb3650e5fa5620fba2795330ab'),
 'cosine':('reports/m4-fp-transcendental/independent-review-r1/author-association-r1/report.json','e1013e456e4cd5bee1a11312a3cd686eee81fbdc81372c60a7dcead5135cf4d0'),
 'sincos':('reports/m4-fp-trigonometric/independent-review-r1/closure-r1/report.json','0659a2b96c78f47fc1876fd8bfb7206fc67c159d82cfbf099ac675b78196afef'),
 'atan':('reports/m4-fp-trigonometric/independent-review-r1/closure-r1/report.json','0659a2b96c78f47fc1876fd8bfb7206fc67c159d82cfbf099ac675b78196afef'),
 'chain':('reports/m4-initializer-chain/independent-review/r6/report.json','d1969f101977a620a69278a587f4632d71060251550481d34855ae5b25fedd37'),
 'integer':('reports/m4-integer-startup/independent-review/r3/report.json','6804a3834186b57c9db89e94f5a3f476fb3e3945af392d0c6b0357cc4b23fc02'),
 'runtime':('reports/m4-runtime/independent-service-r9/report.json','27a48065b1d9e046a138379d6ded99bc691e4813a0337a9b7709afe920035886'),
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--derived',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 derived=Path(args.derived).absolute();derived.relative_to(ROOT/'reports/m4-mixed-startup')
 out=Path(args.output).absolute();out.relative_to(ROOT/'reports/m4-mixed-startup')
 builds={level:ROOT/f'build/m4-mixed-startup-{out.name}-{level}' for level in ['O0','O2']}
 if out.exists() or any(p.exists() for p in builds.values()):raise ValueError('Entirely fresh mixed run/build folders required')
 generation=read(derived/'generation.json')
 for p,h in generation['original_sources'].items()|generation['generated_sources'].items():
  if sha(p)!=h:raise ValueError(f'Derivative source differs: {p}')
 for name,(p,h) in GATES.items():
  if sha(ROOT/p)!=h:raise ValueError(f'Frozen gate differs {name}')
 out.mkdir(parents=True);commands=[];tools={};sources={};objects={};workers={};failure=None
 def run(argv,log):
  argv=list(map(str,argv));p=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  path=out/log;path.write_bytes(p.stdout);commands.append(dict(command=argv,exit_code=p.returncode,log=str(path),log_sha256=sha(path)))
  print(json.dumps(dict(command=Path(argv[0]).name,log=log,exit_code=p.returncode)),flush=True)
  if Path(argv[0]).is_file():tools[argv[0]]=sha(argv[0])
  if p.returncode:raise RuntimeError(f'Command failed; preserved {log}: '+p.stdout.decode(errors='replace')[-6000:])
  return p.stdout
 try:
  # Literal identities before any compilation; copies survive future source edits.
  for folder in ['tools/m4-mixed-startup','tools/m4-initializer-chain','tools/m4-integer-startup','tools/m4-runtime','tools/m4-startup','runtime','local/tools/remill-v6.0.1/remill-6.0.1/include']:
   for p in (ROOT/folder).rglob('*'):
    if p.is_file() and p.suffix in ['.hpp','.h','.cpp','.ps1','.py','.txt'] and '/original/' not in p.as_posix() and '__pycache__' not in p.parts:sources[str(p)]=sha(p)
  sources.update(generation['original_sources']);sources.update(generation['generated_sources']);sources[str(derived/'generation.json')]=sha(derived/'generation.json')
  snapshots=out/'source-copies';snapshots.mkdir()
  for i,(p,h) in enumerate(sources.items()):
   content=Path(p).read_bytes();destination=snapshots/f'{i:04d}-{Path(p).name}';destination.write_bytes(content)
  (out/'source-before.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
  os.environ['TEMP']=str(out);os.environ['TMP']=str(out);os.environ['TMPDIR']=str(out)
  code={r['entry']:r['code'] for r in read(ROOT/'reports/m4-fp-native/lift-r1/report.json')['roots']}
  for level,build in builds.items():
   directory=out/level;directory.mkdir();obj=[];bindings=[]
   for component in generation['components']:
    group=[]
    for i,module in enumerate(component['modules']):
     verified=directory/f'{component["name"]}-{i}-verified.ll';artifact=directory/f'{component["name"]}-{i}.obj'
     run([LLVM/'opt.exe','-passes=verify','-S',module,'-o',verified],f'{level}-{component["name"]}-{i}-verify.log')
     run([LLVM/'llc.exe','-filetype=obj','-'+level,verified,'-o',artifact],f'{level}-{component["name"]}-{i}-llc.log')
     obj.append(str(artifact));group.append(str(artifact))
    for i,entry in enumerate(component['entries']):
     c=code[entry];p=Path(c['path']);require_hash=c['sha256']
     if sha(p)!=require_hash:raise ValueError('Frozen original FP code identity changed')
     object_path=group[i if component['name']=='cosine' else 0]
     bindings.append('{0x%x,%d,"%s","%s","%s",&%s}' % (entry,c['size_bytes'],require_hash,sha(object_path),GATES[component['name']][1],component['name']))
   old={
    'chain':ROOT/f'reports/m4-initializer-chain/runtime-preflight-3/native-{level}.obj',
    'integer':ROOT/f'reports/m4-integer-startup/batch-r2/native-{level}.obj'}
   for name,p in old.items():obj.append(str(p))
   objects[level]={p:sha(p) for p in obj}
   header='''#pragma once
namespace mw34::m4_mixed {
struct FpBinding {std::uint32_t entry,bytes;const char *code,*object,*gate;m4_runtime::NativeEntry native;};
'''
   for name,p in old.items():header+=f'inline constexpr const char *{name}_object="{sha(p)}",*{name}_gate="{GATES[name][1]}";\n'
   header+='inline constexpr std::array<FpBinding,10> fp_bindings{{'+','.join(bindings)+'}};\n}\n'
   (directory/'mixed_bindings.hpp').write_text(header,encoding='utf-8')
   flags=('/Od' if level=='O0' else '/O2')+' /DNDEBUG '+('-Wno-invalid-'+'offsetof')
   run([CMAKE,'-G','Ninja','-S',ROOT/'tools/m4-mixed-startup','-B',build,f'-DMW34_DERIVED={derived}',f'-DMW34_BINDINGS={directory}',f'-DMW34_OBJECTS={";".join(obj)}',f'-DMW34_REMILL_INCLUDE={ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include','-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log')
   run([CMAKE,'--build',build,'--parallel','8'],f'{level}-build.log')
   worker=build/'mw34_m4_mixed_native.exe';workers[level]=str(worker)
   run([worker,'--layout'],f'{level}-layout.json')
   run([worker,'--check-context',ROOT/'MW3/Mech3.exe'],f'{level}-compiled-controls.json')
   run([worker,ROOT/'MW3/Mech3.exe',out/f'native-{level}.bin'],f'{level}-actual.log')
   cache=(build/'CMakeCache.txt').read_text(encoding='utf-8-sig');(out/f'{level}-CMakeCache.txt').write_text(cache,encoding='utf-8')
   for m in re.finditer(r'^CMAKE_(?:CXX_COMPILER|AR|LINKER|MT|RC_COMPILER|MAKE_PROGRAM):(?:FILEPATH|STRING)=(.+)$',cache,re.M):
    p=Path(m[1]);tools[str(p)]=sha(p)
   ninja=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
   run([ninja,'-C',build,'-t','deps'],f'{level}-actual-dependencies.txt')
  for p,h in sources.items():
   if sha(p)!=h:raise ValueError('Source changed during build: '+p)
 except Exception as error:
  failure=str(error);(out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');print(failure,flush=True)
 finally:
  artifacts={str(p):sha(p) for p in out.rglob('*') if p.is_file()}
  for b in builds.values():
   if b.exists():
    for p in b.rglob('*'):
     if p.is_file() and p.suffix in ['.obj','.lib','.exe','.pdb','.ninja']:artifacts[str(p)]=sha(p)
  report=dict(passed=failure is None,scope='Actual candidate selected26-root shared-runtime execution only; differential comparison/peer integration review and full CRT/M4 remain open',failure=failure,generation=str(derived/'generation.json'),generation_sha256=sha(derived/'generation.json'),sources=sources,commands=commands,tools=tools,artifacts=artifacts,objects=objects,workers=workers,prior_gates=GATES,image_path=str(ROOT/'MW3/Mech3.exe'),image_sha256=sha(ROOT/'MW3/Mech3.exe'),full_ledger_completed=False)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 if failure:raise SystemExit(1)
if __name__=='__main__':main()
