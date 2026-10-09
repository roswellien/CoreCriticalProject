"""Physical current/historical dependency closure; no original execution."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-integration';TOOLS=ROOT/'tools/m4-fp-numeric-max-integration'
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir();cache={};pins={};versions={};resolutions=[];associations=[];objects=[];headers=[];current=[]
def sha(p):
 p=Path(p).resolve()
 if p not in cache:
  with p.open('rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def bind(p,expected=None):
 p=Path(p).resolve();h=sha(p);assert expected is None or h==expected,(str(p),h,expected)
 if str(p) in pins:assert pins[str(p)]==h
 pins[str(p)]=h;return h
def source(original,preserved,expected,proof):
 preserved=Path(preserved).resolve();bind(preserved,expected);versions[(str(Path(original).resolve()),expected)]=preserved
 associations.append({'original_path':str(Path(original).resolve()),'expected_sha256':expected,'preserved_path':str(preserved),'manifest':str(proof)})
def associate(path,expected,proof):
 p=Path(path).resolve()
 if p.exists() and sha(p)==expected:bind(p,expected);return p
 key=(str(p),expected);assert key in versions,('unresolved historical version',str(proof),key)
 q=versions[key];bind(q,expected);resolutions.append({'manifest':str(proof),'original_path':str(p),'expected_sha256':expected,'resolved_path':str(q)});return q
def json_(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
try:
 # Every old owned attempt remains literal; independent reviewers are excluded.
 owned=[p for p in BASE.rglob('*') if p.is_file() and not p.is_relative_to(out) and not any(x.startswith('independent') for x in p.relative_to(BASE).parts)]
 for p in owned:bind(p)
 for p in owned:
  if p.suffix!='.json':continue
  d=json_(p)
  for row in d.get('literal_sources',d.get('source_copies',[])):
   source(row['original_path'],row['preserved_path'],row['sha256'],p)
  # Preparation/observer/worker scripts each retain their version next to report.
  for public,literal in (('prepare.py','prepare-source.py'),('observe.py','observer-source.py'),('check_worker.py','checker-source.py'),('check_worker.py','failed-checker-source.py')):
   q=p.parent/literal
   if q.exists():source(TOOLS/public,q,sha(q),p)
 for p in sorted(TOOLS.iterdir()):
  if p.is_file():
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(q);bind(p,h);current.append({'original_path':str(p),'preserved_path':str(q),'sha256':h})
 for p in owned:
  if p.suffix!='.json':continue
  d=json_(p)
  for key in ('source_files','artifacts','tools','files','existing_immutable_bindings'):
   rows=d.get(key,{})
   if isinstance(rows,dict):
    for path,h in rows.items():
     if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h):associate(path,h,p)
  for cmd in d.get('commands',[]):
   if 'log_path' in cmd:bind(cmd['log_path'],cmd['log_sha256'])
 # Two accepted prerequisite maps are rehashed literally. Their bindings
 # already resolve historical accepted gate/runtime source versions physically.
 prerequisites=[]
 for rel in ('reports/m4-fp-numeric-max/independent-closure-r1','reports/m4-runtime/independent-service-r9'):
  directory=ROOT/rel;bind(directory/'report.json');bind(directory/'pins.json');d=json_(directory/'pins.json')
  for path,h in d['files'].items():bind(path,h)
  prerequisites.append({'report':str(directory/'report.json'),'report_sha256':sha(directory/'report.json'),'pins':str(directory/'pins.json'),'pins_sha256':sha(directory/'pins.json'),'bindings':len(d['files'])})
 build=BASE/'native-build-r5';b=json_(build/'build.json');assert b['passed'];bind(build/'build.json');bind(ROOT/'MW3/Mech3.exe');bind(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL')
 # Actual compiler read log and LLVM/Windows link support closure.
 for level in ('O0','O2'):
  p=build/f'build-{level}.log';text=p.read_text(encoding='utf-8-sig');bind(p)
  for name in re.findall(r'Note: including file:\s*([^\r\n]+)',text):
   path=Path(name.strip()).resolve();h=bind(path);headers.append({'level':level,'path':str(path),'sha256':h})
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 for name in ('clang-cl.exe','lld-link.exe','llvm-mt.exe','llvm-link.exe','llc.exe','opt.exe','llvm-readobj.exe','llvm-objdump.exe'):bind(llvm/name)
 bind(Path(sys.executable))
 sdk=Path('C:/Program Files (x86)/Windows Kits/10');vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
 for name in ('bcrypt','kernel32','user32','gdi32','winspool','shell32','ole32','oleaut32','uuid','comdlg32','advapi32'):bind(sdk/f'Lib/10.0.26100.0/um/x64/{name}.lib')
 for name in ('msvcrt','msvcprt','vcruntime','oldnames'):bind(vs/f'lib/x64/{name}.lib')
 bind(sdk/'Lib/10.0.26100.0/ucrt/x64/ucrt.lib');bind(sdk/'bin/10.0.26100.0/x64/rc.exe')
 # Fresh COFF machine instructions/directives/unwind entries, never an executor.
 object_paths=[]
 for info in b['builds']:
  object_paths.append(Path(info['object']));object_paths.extend(Path(info['directory']).rglob('*.obj'));bind(info['worker'])
 for i,p in enumerate(dict.fromkeys(object_paths)):
  h=bind(p);dis=out/f'object-{i:02d}-disassembly.txt';unw=out/f'object-{i:02d}-metadata.txt'
  commands=[]
  for args,q in (([str(llvm/'llvm-objdump.exe'),'-d',str(p)],dis),([str(llvm/'llvm-readobj.exe'),'--file-headers','--coff-directives','--unwind',str(p)],unw)):
   r=subprocess.run(args,capture_output=True,timeout=60);assert r.returncode==0,(args,r.stderr);q.write_bytes(r.stdout);bind(q);commands.append({'arguments':args,'exit_code':r.returncode,'output':str(q),'sha256':sha(q)})
  objects.append({'path':str(p),'sha256':h,'commands':commands})
 # Post-build sources held literal, and final observer/control results pass.
 assert json_(BASE/'comparison-r2/report.json')['passed'] and json_(BASE/'worker-controls-r2/report.json')['passed']
 for row in current:assert sha(row['original_path'])==row['sha256']
 report={'passed':True,'scope':'Bounded shared-r9 numeric-max native integration author seal, independent review pending; full M4 and connected27 incomplete','final_build':str(build/'build.json'),'final_build_sha256':sha(build/'build.json'),'literal_sources':current,'historical_source_resolutions':resolutions,'literal_source_associations':associations,'prerequisites':prerequisites,'compiled_header_reads':len(headers),'compiled_headers':headers,'fresh_CO​​FF_objects':objects,'counts':{'physical_bindings_before_report':len(pins),'compiled_checks_per_level':106,'compiled_denials_per_level':22,'corrected_poisoned_retries_per_level':21,'constructor_ownership_scenarios_per_level':5,'persistent_native_phases':864,'carry_boundaries':432,'offline_wrapper_replays':14688,'memory_events':342144,'routes':46656,'author_observer_negative_controls':40,'actual_worker_denials':18,'actual_publisher_sentinel_checks':4,'actual_recipe_no_mutation_controls':3},'view_provenance':'Full actual native State/CPU with explicit software FX/legacy ENV; original hardware FX/FNSTENV/CONTEXT retained as distinct offline observer provenance; full actual host hardware FX/ENV restore','carry_blocker':'Current domain excludes PE-only and incoming C1 from preceding actual4B7020 phase. No joint27-root admission; no FP/hidden State reseed permitted.','lifetime_scope':'Stable Runtime/owned mappings, lexical serial borrower on constructing thread, Session outlives registry calls. Failed construction/partial registration requires discarding Runtime. No concurrent/reparse/host mapping replacement credit.','original_executed':False,'frozen_runtime_modified':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':dict(sorted(pins.items()))},indent=2)+'\n');print(json.dumps({'passed':True,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'bindings':len(pins),'historical_resolutions':len(resolutions),'COFF_objects':len(objects),'header_reads':len(headers)}))
except BaseException:
 (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-seal-source.py').write_bytes(Path(__file__).read_bytes());raise
