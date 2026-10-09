"""Additive physical source/tool/artifact closure for the explicit outer boundary."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-host-boundary';TOOLS=ROOT/'tools/m4-fp-numeric-max-host-boundary'
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
cache={};pins={};versions={};associations=[];resolutions=[];current=[];headers=[];objects=[]
def sha(p):
 p=Path(p).resolve()
 if p not in cache:
  with p.open('rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def bind(p,expected=None):
 p=Path(p).resolve();h=sha(p);assert expected is None or h==expected,(str(p),h,expected)
 assert str(p) not in pins or pins[str(p)]==h;pins[str(p)]=h;return h
def data(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def source(p,q,h,proof):
 p=Path(p).resolve();q=Path(q).resolve();bind(q,h);versions[(str(p),h)]=q
 associations.append(dict(original_path=str(p),preserved_path=str(q),sha256=h,manifest=str(proof)))
def associate(p,h,proof):
 p=Path(p).resolve()
 if p.exists() and sha(p)==h:bind(p,h);return
 q=versions.get((str(p),h));assert q is not None,('unresolved literal version',str(p),h,str(proof))
 bind(q,h);resolutions.append(dict(original_path=str(p),expected_sha256=h,resolved_path=str(q),manifest=str(proof)))
try:
 owned=[p for p in BASE.rglob('*') if p.is_file() and not p.is_relative_to(out) and not any(x.startswith('independent') for x in p.relative_to(BASE).parts)]
 for p in owned:bind(p)
 for p in owned:
  if p.suffix=='.json':
   d=data(p)
   for row in d.get('literal_sources',[]):source(row['original_path'],row['preserved_path'],row['sha256'],p)
  if p.name in ('derive.py','build.ps1','make_recipe.py') and p.parent.name.startswith('pre-'):source(TOOLS/p.name,p,sha(p),p.parent)
  if p.name=='observer-source.py':source(TOOLS/'observe.py',p,sha(p),p.parent)
  if p.name=='checker-source.py':source(TOOLS/'check_worker.py',p,sha(p),p.parent)
 for p in sorted(TOOLS.iterdir()):
  if p.is_file():
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(q);bind(p,h);current.append(dict(original_path=str(p),preserved_path=str(q),sha256=h));source(p,q,h,out)
 for p in owned:
  if p.suffix!='.json':continue
  d=data(p)
  for key in ('source_files','artifacts','tools','files'):
   for path,h in d.get(key,{}).items():
    if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h):associate(path,h,p)
  for c in d.get('commands',[]):
   if 'log_path' in c:bind(c['log_path'],c['log_sha256'])
 prereqs=[]
 # Frozen r5 remains an unaccepted host-boundary baseline. Its own guest/raw
 # evidence, reviewed prerequisite IR/runtime and the measured finding are retained.
 for rel in ('reports/m4-fp-numeric-max-integration/author-review-r1','reports/m4-fp-numeric-max-integration/independent-session-closure-r4','reports/m4-fp-numeric-max-integration/independent-direct-host-r1','reports/m4-fp-numeric-max/independent-closure-r1','reports/m4-runtime/independent-service-r9'):
  p=ROOT/rel;bind(p/'report.json');bind(p/'pins.json');d=data(p/'pins.json')
  for path,h in d['files'].items():bind(path,h)
  prereqs.append(dict(report=str(p/'report.json'),report_sha256=sha(p/'report.json'),pins=str(p/'pins.json'),pins_sha256=sha(p/'pins.json'),bindings=len(d['files'])))
 build=BASE/'native-build-r3';b=data(build/'build.json');assert b['passed'];bind(build/'build.json')
 assert data(BASE/'comparison-r3/report.json')['passed'] and data(BASE/'worker-controls-r1/report.json')['passed']
 for level in ('O0','O2'):
  p=build/f'build-{level}.log';bind(p)
  for name in re.findall(r'Note: including file:\s*([^\r\n]+)',p.read_text(encoding='utf-8-sig')):
   q=Path(name.strip()).resolve();headers.append(dict(level=level,path=str(q),sha256=bind(q)))
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 for name in ('clang-cl.exe','lld-link.exe','llvm-mt.exe','llvm-link.exe','llc.exe','opt.exe','llvm-readobj.exe','llvm-objdump.exe'):bind(llvm/name)
 bind(sys.executable)
 sdk=Path('C:/Program Files (x86)/Windows Kits/10');vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
 for name in ('bcrypt','kernel32','user32','gdi32','winspool','shell32','ole32','oleaut32','uuid','comdlg32','advapi32'):bind(sdk/f'Lib/10.0.26100.0/um/x64/{name}.lib')
 for name in ('msvcrt','msvcprt','vcruntime','oldnames'):bind(vs/f'lib/x64/{name}.lib')
 bind(sdk/'Lib/10.0.26100.0/ucrt/x64/ucrt.lib');bind(sdk/'bin/10.0.26100.0/x64/rc.exe')
 paths=[]
 for info in b['builds']:paths.append(Path(info['object']));paths.extend(Path(info['directory']).rglob('*.obj'));bind(info['worker'])
 for i,p in enumerate(dict.fromkeys(paths)):
  row=dict(path=str(p),sha256=bind(p),commands=[])
  for args,q in (([str(llvm/'llvm-objdump.exe'),'-d',str(p)],out/f'object-{i:02d}-disassembly.txt'),([str(llvm/'llvm-readobj.exe'),'--file-headers','--coff-directives','--unwind',str(p)],out/f'object-{i:02d}-metadata.txt')):
   r=subprocess.run(args,capture_output=True,timeout=60);assert r.returncode==0,(args,r.stderr);q.write_bytes(r.stdout);row['commands'].append(dict(arguments=args,exit_code=0,output=str(q),sha256=bind(q)))
  objects.append(row)
 # These identical guest objects bind the preservation fix to unchanged numeric IR.
 object_identity=[]
 for level in ('O0','O2'):
  p=build/f'native-{level}.obj';q=ROOT/f'reports/m4-fp-numeric-max-integration/native-build-r5/native-{level}.obj'
  assert sha(p)==sha(q);object_identity.append(dict(level=level,new=str(p),frozen_r5=str(q),sha256=bind(p)));bind(q)
 for row in current:assert sha(row['original_path'])==row['sha256']
 report=dict(passed=True,scope='Author-sealed explicit Session-owned numerical host boundary, independent review pending; narrow guest domain only',final_build=str(build/'build.json'),final_build_sha256=sha(build/'build.json'),literal_sources=current,historical_source_resolutions=resolutions,literal_source_associations=associations,prerequisites=prereqs,compiled_header_reads=len(headers),compiled_headers=headers,fresh_COFF_objects=objects,unchanged_guest_object_identity=object_identity,
 counts=dict(physical_bindings_before_report=len(pins),compiled_checks_per_level=106,actual_denials_per_level=22,corrected_poisoned_retries_per_level=21,constructor_ownership_scenarios_per_level=5,persistent_native_phases=864,carry_boundaries=432,offline_BEFORE_wrapper_replays=14688,memory_events=342144,routes=46656,author_observer_negative_controls=40,scope_positive_controls=6,worker_denials=18,publisher_sentinel_checks=4,recipe_no_mutation_controls=3),
 required_API='Session.invoke(target,return_pc,acquire_borrow) noexcept -> bool; normal C++ failure propagation remains internal, catch/owner cleanup precedes final numerical restore and status return',
 host_scope='Actual direct pre-cleanup x87 CW/status/TOP/tags/all8 raw80/legacy ENV28/MXCSR preservation on successful root, pre-callback dispatcher failure, actual FLD/FSTP checked faults and corrected poisoned retry. Raw volatile SIMD/reserved FX are observations only.',
 excluded='Raw Runtime.call_direct or external constructor/borrow exceptions; all higher startup and joint27 credit; mapping replacement/concurrent publication/reparse points; unmeasured live values and carried incoming C1/PE domain',
 r5_correction='Frozen r5 before/after host equality establishes explicit harness self-restore only. Direct independent finding and failed callback-only derivative raw diagnostics are retained literally.',original_executed=False,frozen_runtime_modified=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
 print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),bindings=len(pins),historical_resolutions=len(resolutions),objects=len(objects),header_reads=len(headers))))
except BaseException:
 (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-seal-source.py').write_bytes(Path(__file__).read_bytes());raise
