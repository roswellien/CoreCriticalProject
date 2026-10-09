"""Additive physical closure for the selected mixed-runtime candidate."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'reports/m4-mixed-startup'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def key(p):return str(Path(p).absolute()).replace('\\','/').casefold()
def pin_map(document):
 mapping=document.get('files',document.get('bindings',{}))
 if isinstance(mapping,dict):
  result={}
  for p,value in mapping.items():
   if isinstance(value,str):result[p]=value
   elif isinstance(value,dict) and isinstance(value.get('sha256'),str):
    if 'path' in value and key(value['path'])!=key(p):raise ValueError('Descriptor key/path disagree')
    result[p]=value['sha256']
   else:raise ValueError('Unsupported explicit dictionary pin descriptor')
  return result
 if isinstance(mapping,list):
  result={}
  for row in mapping:
   p,h=row['path'],row['sha256']
   if p in result and result[p]!=h:raise ValueError('Conflicting path in explicit descriptor pin map')
   result[p]=h
  return result
 raise ValueError('Unsupported independent physical pin map')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--original-seal',required=True);ap.add_argument('--observer-controls',required=True);a=ap.parse_args()
 out=Path(a.output).absolute();out.relative_to(AREA);out.mkdir(parents=True,exist_ok=False)
 files={};replacement=[];commands=[];prior_admission=[];literal=[]
 def pin(p,h=None):
  p=Path(p).absolute();actual=sha(p)
  if h is not None and actual!=h:raise ValueError('Physical closure hash differs: '+str(p))
  previous=files.get(str(p))
  if previous is not None and previous!=actual:raise ValueError('Conflicting physical closure: '+str(p))
  files[str(p)]=actual;return actual
 # Frozen independent component maps are physically retained; selected input
 # admission below checks their exact path/hash binding, not merely a gate name.
 candidate=read(AREA/'native-r3/build.json');pin(AREA/'native-r3/build.json')
 if not candidate['passed']:raise ValueError('Final actual native candidate did not complete')
 prior={};prior_physical={};transitive_source_maps=[]
 for name,(relative,expected) in candidate['prior_gates'].items():
  report=ROOT/relative;pin(report,expected);pins=report.parent/'pins.json';pin(pins)
  d=read(pins);mapping=pin_map(d)
  for p,h in mapping.items():
   if not isinstance(h,str):raise ValueError('Independent map is not an explicit SHA map')
   prior.setdefault(key(p),set()).add(h)
   prior_physical.setdefault(p,set()).add(h)
 # Some peers deliberately resolve old logical sources to literal copies.
 # Their hash-bound build manifests preserve the exact logical path/SHA link.
 # Resolve that link explicitly rather than treating a matching basename as
 # proof or rewriting the older physical map to point at today's source.
 for p,hashes in prior_physical.items():
  if Path(p).name!='build.json':continue
  actual=sha(p)
  if actual not in hashes:raise ValueError('Reviewed source-map manifest changed: '+p)
  manifest=read(p);pin(p,actual)
  for field in ['sources','source_files']:
   mapping=manifest.get(field,{})
   if not isinstance(mapping,dict):continue
   admitted=[]
   for source,h in mapping.items():
    if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h):prior.setdefault(key(source),set()).add(h);admitted.append(dict(path=source,sha256=h))
   if admitted:transitive_source_maps.append(dict(manifest=p,manifest_sha256=actual,field=field,identities=admitted))
 generation=read(candidate['generation']);pin(candidate['generation'],candidate['generation_sha256'])
 for p,h in generation['original_sources'].items():
  if h not in prior.get(key(p),set()):raise ValueError('Mixed derivative input lacks exact prior reviewed identity: '+p)
  pin(p,h);prior_admission.append(dict(path=p,sha256=h))
 for p,h in generation['generated_sources'].items():pin(p,h)
 # Preserve all actual builds (including the failed fixture comparison) without
 # rewriting a historical map to bind the latest public source at an old path.
 for run in ['native-r1','native-r2','native-r3']:
  build_path=AREA/run/'build.json';build=read(build_path);pin(build_path)
  before=read(AREA/run/'source-before.json');pin(AREA/run/'source-before.json')
  if before!=build['sources']:raise ValueError('Literal precompile source table differs from final build')
  for i,(p,h) in enumerate(build['sources'].items()):
   copy=AREA/run/'source-copies'/f'{i:04d}-{Path(p).name}';pin(copy,h)
   if sha(p)==h:pin(p,h)
   else:replacement.append(dict(build=str(build_path),logical_path=p,expected_sha256=h,literal_copy=str(copy),literal_copy_sha256=h))
  for section in ['tools','artifacts']:
   for p,h in build[section].items():pin(p,h)
  for level,objects in build['objects'].items():
   for p,h in objects.items():pin(p,h)
  if run=='native-r3':
   for level,objects in build['objects'].items():
    for p,h in objects.items():
     if 'runtime-preflight-3' in p or '/batch-r2/' in p.replace('\\','/'):
      if h not in prior.get(key(p),set()):raise ValueError('Linked old integer object is not the reviewed artifact')
 # Gate source and complete original-side provenance are explicit inputs.
 original=Path(a.original_seal).absolute();pin(original)
 if not read(original)['passed']:raise ValueError('Original-side closure failed')
 original_pins=original.parent/'pins.json';pin(original_pins)
 original_map=read(original_pins)
 for p,h in pin_map(original_map).items():pin(p,h)
 observer=Path(a.observer_controls).absolute();pin(observer)
 if not read(observer)['passed']:raise ValueError('Connected observer controls failed')
 comparison=AREA/'original-comparison-r4/report.json';pin(comparison)
 if not read(comparison)['passed']:raise ValueError('Connected native/original comparison failed')
 for folder in ['pre-compile-recipe-failure-r1','pre-compile-gate-path-failure-r1','native-r1-fixture-diagnostic-r1','pre-domain-controls-r1','original-comparison-r1','original-comparison-r2','original-comparison-r3','author-review-r1','author-review-r2','author-review-r3']:
  directory=AREA/folder
  if directory.exists():
   for p in directory.rglob('*'):
    if p.is_file():pin(p)
 for level in ['O0','O2']:
  controls=read(AREA/'native-r3'/f'{level}-compiled-controls.json')
  if controls!={'passed':True,'positive_callbacks':10,'invalid_context_denials':90,'poisoned_reuse_denials':80}:raise ValueError('Actual compiled context control extent differs')
  report=AREA/f'worker-controls-{level}-r1/report.json';pin(report)
  if read(report)['actual_worker_denials']!=6 or not read(report)['passed']:raise ValueError('Worker controls failed')
  for p in report.parent.rglob('*'):
   if p.is_file():pin(p)
 for directory in [ROOT/'tools/m4-mixed-startup',ROOT/'tests/m4-mixed-startup']:
  for p in directory.rglob('*'):
   if p.is_file() and p.suffix in ['.py','.cpp','.hpp','.ps1','.txt','.asm'] and '__pycache__' not in p.parts:
    h=pin(p);copy=out/'literal-public'/p.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes());pin(copy,h);literal.append(dict(source=str(p),copy=str(copy),sha256=h))
 p=ROOT/'docs/m4-mixed-startup-experiment.md';h=pin(p);copy=out/'literal-public/docs/m4-mixed-startup-experiment.md';copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes());pin(copy,h);literal.append(dict(source=str(p),copy=str(copy),sha256=h))
 # Actual compiler dependency lists identify SDK/STL/Remill headers. Their
 # hashes are explicitly post-build association, not execution-time tracing.
 dependencies=set()
 for level in ['O0','O2']:
  path=AREA/'native-r3'/f'{level}-actual-dependencies.txt';pin(path)
  for line in path.read_text(encoding='utf-8-sig').splitlines():
   if re.match(r'^\s+[A-Za-z]:[\\/]',line):
    p=Path(line.strip());
    if not p.is_file():raise ValueError('Actual compiler dependency missing: '+str(p))
    pin(p);dependencies.add(str(p))
    relative=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else ''
    old_prefixes=('tools/m4-initializer-chain/','tools/m4-integer-startup/','tools/m4-runtime/','tools/m4-startup/','runtime/','local/tools/remill-v6.0.1/')
    if relative.startswith(old_prefixes) and sha(p) not in prior.get(key(p),set()):raise ValueError('Actual borrowed compiler source/header lacks exact reviewed identity: '+str(p))
 objdump=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe';pin(objdump)
 objects=set()
 for group in candidate['objects'].values():objects.update(group)
 for p in candidate['artifacts']:
  if p.endswith('.cpp.obj') and ('bridge-' in p or p.endswith('native_main.cpp.obj')):objects.add(p)
 dumps=out/'compiled-objects';dumps.mkdir()
 for i,p in enumerate(sorted(objects)):
  pin(p);command=[str(objdump),'--disassemble','--reloc','--x86-asm-syntax=intel',p];result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log=dumps/f'{i:02d}-{Path(p).name}.txt';log.write_bytes(result.stdout);pin(log)
  commands.append(dict(command=command,exit_code=result.returncode,output=str(log),sha256=sha(log)))
  if result.returncode:raise ValueError('Actual COFF decode failed')
 pins_path=out/'pins.json';pins_path.write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8')
 report=dict(passed=True,reviewer='author; separate complete integration review required',scope='26 selected import-free initializers in table order on persistent r9 image/State, default image operands,12maskedCW,emptyTOP0/7; remaining118roots and completeCRT/MFC/menu paths open',original_phases=1248,native_phases=2496,complete_State_bytes_per_native_phase=7008,observed_pages_per_phase=11,compiled_context_checks_per_level=180,actual_worker_denials=12,current_reviewed_derivative_inputs=prior_admission,explicit_transitive_source_maps=transitive_source_maps,historical_source_replacements=replacement,literal_public_sources=literal,physical_bindings=len(files),pins_path=str(pins_path),pins_sha256=sha(pins_path),actual_compiler_dependency_files=len(dependencies),dependency_hash_timing='Post-build current file association to actual Ninja dependency lists, not full execution-time tracing',actual_compiled_object_decodes=commands,original_seal=str(original),connected_observer_controls=str(observer),full_ledger_completed=False,status_scope='Final C1/C0/C2/C3 and dead raw80 match observations; standalone independent proved C1 subsets do not automatically prove connected final-store flags; no unmasked/occupied-stack/general-input admission')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,bindings=len(files),historical_source_replacements=len(replacement),literal_sources=len(literal))))
if __name__=='__main__':main()
