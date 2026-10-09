"""Author physical closure of additive carry/canonical variant, not peer acceptance."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry';TOOLS=ROOT/'tools/m4-fp-numeric-max-carry'
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
cache={};pins={};versions={};associations=[];resolutions=[];current=[];headers=[];objects=[]
def sha(p):
 p=Path(p).resolve()
 if p not in cache:
  with p.open('rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def bind(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or h==actual,(str(p),h,actual)
 assert str(p) not in pins or pins[str(p)]==actual;pins[str(p)]=actual;return actual
def data(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def source(p,q,h,proof):
 p=Path(p).resolve();q=Path(q).resolve();bind(q,h);versions[(str(p),h)]=q;associations.append(dict(original_path=str(p),preserved_path=str(q),sha256=h,manifest=str(proof)))
def associate(p,h,proof):
 p=Path(p).resolve()
 if p.exists() and sha(p)==h:bind(p,h);return
 q=versions.get((str(p),h));assert q is not None,('unresolved literal source version',str(p),h,str(proof));bind(q,h);resolutions.append(dict(original_path=str(p),expected_sha256=h,resolved_path=str(q),manifest=str(proof)))
try:
 owned=[p for p in BASE.rglob('*') if p.is_file() and not p.is_relative_to(out) and 'compiler-temp' not in p.parts and not any(s.startswith('independent') for s in p.relative_to(BASE).parts)]
 for p in owned:bind(p)
 for p in owned:
  if p.suffix=='.json':
   d=data(p)
   for row in d.get('literal_sources',[]):source(row['original_path'],row['preserved_path'],row['sha256'],p)
   for row in d.get('source_copies',[]):source(row['original_path'],row.get('preserved',row.get('preserved_path')),row.get('build_sha256',row.get('sha256')),p)
  if p.name=='generator-source.py':source(TOOLS/('prepare_canonical.py' if 'canonical' in p.parent.name else 'prepare_native.py'),p,sha(p),p.parent)
  if p.name in ('observer-source.py','failed-observer-source.py'):
   name='observe_canonical_flags.py' if 'canonical-flag' in p.parent.name else 'observe_canonical_legacy.py' if 'canonical-legacy' in p.parent.name else 'observe_hardware.py' if p.parent.name.startswith('hardware') else 'observe_native.py'
   source(TOOLS/name,p,sha(p),p.parent)
 for p in sorted(TOOLS.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(q);bind(p,h);current.append(dict(original_path=str(p),preserved_path=str(q),sha256=h));source(p,q,h,out)
 for p in owned:
  if p.suffix!='.json':continue
  d=data(p)
  for key in ('source_files','artifacts','tools','files','existing_immutable_bindings'):
   for name,h in d.get(key,{}).items():
    if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h):associate(name,h,p)
  for c in d.get('commands',[]):
   if 'log_path' in c:bind(c['log_path'],c['log_sha256'])
 prereqs=[]
 for rel in ('reports/m4-fp-numeric-max-host-boundary/author-review-r1','reports/m4-fp-numeric-max-host-boundary/independent-compiled-r1','reports/m4-fp-numeric-max-host-boundary/independent-boundary-finding-r1','reports/m4-fp-numeric-max-integration/author-review-r1','reports/m4-fp-numeric-max/independent-closure-r1','reports/m4-runtime/independent-service-r9'):
  p=ROOT/rel;bind(p/'report.json');bind(p/'pins.json');d=data(p/'pins.json')
  for name,h in d['files'].items():associate(name,h,p/'pins.json')
  prereqs.append(dict(report=str(p/'report.json'),report_sha256=sha(p/'report.json'),pins=str(p/'pins.json'),pins_sha256=sha(p/'pins.json'),bindings=len(d['files'])))
 build=BASE/'native-canonical-r1';b=data(build/'build.json');assert b['passed'];bind(build/'build.json')
 for name in ('canonical-carry-observation-r1','canonical-legacy-observation-r1','canonical-flag-observation-r3'):assert data(BASE/name/'report.json')['passed']
 assert not data(BASE/'native-baseline-observation-r1/report.json')['passed']
 ancestor=BASE/'native-preparation-repair-r2/session.hpp';candidate=BASE/'native-preparation-canonical-r1/session.hpp'
 old=ancestor.read_text();new=candidate.read_text();needle='void admit_fp(){auto sw=status(s_),top=(sw>>11)&7;';guard='void admit_fp(){for(const auto byte:std::array<std::uint8_t,11>{s_.sw.ie,s_.sw.de,s_.sw.ze,s_.sw.oe,s_.sw.ue,s_.sw.pe,s_.sw.sf,s_.sw.c0,s_.sw.c1,s_.sw.c2,s_.sw.c3})if(byte>1)deny("Noncanonical FP shadow flag byte rejected");auto sw=status(s_),top=(sw>>11)&7;'
 assert old.count(needle)==1 and old.replace(needle,guard)==new
 source_delta=dict(previous=str(ancestor),previous_sha256=bind(ancestor),candidate=str(candidate),candidate_sha256=bind(candidate),only_change='Eleven byte<=1 admission check before status projection; no mutation/normalization of rejected values')
 for level in ('O0','O2'):
  p=build/f'build-{level}.log';bind(p)
  for name in re.findall(r'Note: including file:\s*([^\r\n]+)',p.read_text(encoding='utf-8-sig')):
   q=Path(name.strip()).resolve();headers.append(dict(level=level,path=str(q),sha256=bind(q)))
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 for name in ('clang-cl.exe','lld-link.exe','llvm-mt.exe','llvm-link.exe','llc.exe','opt.exe','llvm-readobj.exe','llvm-objdump.exe'):bind(llvm/name)
 bind(sys.executable);sdk=Path('C:/Program Files (x86)/Windows Kits/10');vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
 for name in ('bcrypt','kernel32','user32','gdi32','winspool','shell32','ole32','oleaut32','uuid','comdlg32','advapi32'):bind(sdk/f'Lib/10.0.26100.0/um/x64/{name}.lib')
 for name in ('msvcrt','msvcprt','vcruntime','oldnames'):bind(vs/f'lib/x64/{name}.lib')
 bind(sdk/'Lib/10.0.26100.0/ucrt/x64/ucrt.lib');bind(sdk/'bin/10.0.26100.0/x64/rc.exe')
 paths=[]
 for info in b['builds']:paths.append(Path(info['object']));paths.extend(Path(info['directory']).rglob('*.obj'));bind(info['worker']);bind(info['legacy_worker'])
 for i,p in enumerate(dict.fromkeys(paths)):
  row=dict(path=str(p),sha256=bind(p),commands=[])
  for args,q in (([str(llvm/'llvm-objdump.exe'),'-d',str(p)],out/f'object-{i:02d}-disassembly.txt'),([str(llvm/'llvm-readobj.exe'),'--file-headers','--coff-directives','--unwind',str(p)],out/f'object-{i:02d}-metadata.txt')):
   r=subprocess.run(args,capture_output=True,timeout=60);assert r.returncode==0,(args,r.stderr);q.write_bytes(r.stdout);row['commands'].append(dict(arguments=args,exit_code=0,output=str(q),sha256=bind(q)))
  objects.append(row)
 identity=[]
 for level in ('O0','O2'):
  p=build/f'native-{level}.obj';q=ROOT/f'reports/m4-fp-numeric-max-integration/native-build-r5/native-{level}.obj';assert sha(p)==sha(q);identity.append(dict(level=level,current=str(p),ancestor=str(q),sha256=bind(p)));bind(q)
 for row in current:assert sha(row['original_path'])==row['sha256']
 report=dict(passed=True,acceptance='Author tested/sealed candidate only; independent canonical/carry compiled and raw review pending',final_build=str(build/'build.json'),final_build_sha256=sha(build/'build.json'),source_delta=source_delta,literal_sources=current,historical_source_resolutions=resolutions,literal_source_associations=associations,prerequisites=prereqs,compiled_header_reads=len(headers),compiled_headers=headers,fresh_COFF_objects=objects,unchanged_guest_object_identity=identity,
  changes_separate=['Measured incoming PE/C1 status domain extension','Source-defined no-overflow FLD C1=0 at typed commit, exact strict numeric IR unchanged','New eleven-shadow-byte canonical admission before projection'],
  counts=dict(physical_bindings_before_report=len(pins),final_build_sources=len(b['source_files']),final_build_tools=len(b['tools']),final_build_artifacts=len(b['artifacts']),canonical_assertions_per_level=661,malformed_scenarios_per_level=66,corrected_poisoned_retries_per_level=66,direct_flag_records=264,inherited_checks_per_worker=106,carry_phases=41472,carry_boundaries=2304,narrow_phases=15552,narrow_carry_boundaries=432,total_native_numeric_phases=57024,memory_events=1254528,routes=171072,canonical_observer_negative_controls=80,canonical_scope_positive_controls=12,carry_observer_negative_controls=64,carry_scope_positive_controls=12,narrow_observer_negative_controls=40,narrow_scope_positive_controls=6,hardware_authored_records=36864,hardware_observer_negative_controls=40),
  source_authority=dict(url='https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf',edition='253666-060US',sections='FLD3-353;FST/FSTP3-387',rule='No-overflow FLD clears C1. Incoming sticky PE does not establish a new precision exception or final FSTP rounding-direction credit'),
  host_scope='Required Session.invoke noexcept status-return API owns numerical restoration after internal catch/owner cleanup. Direct actual FX/ENV captures precede harness cleanup: CW/SW/TOP/tags/all8raw80/MXCSR/fullENV28. VolatileSIMD/reservedFX are observations only.',
  FP_scope='Coherent live depth0/1/7,TOP0/7,twelve maskedCW,16 authored f32inputs,sticky0/2/32/34,C1=0/1. FLD C1zero is source-defined; final FSTP C1/C0/C2/C3/dead storage remain observations, not credited from incoming PE.',
  malformed_scope='Malformed bytes are rejected and not granted numeric equivalence. Diagnostic BEFORE view uses exact unsigned OR and uint16 truncation solely to serialize refused inputs.',
  failure_provenance='Frozen numerical C1 baseline and failed compile remain literal. Frozen host-r3 misadmission and peer finding preserved. New author observer r1 wrongly assumed allzero defaultView; r2 reused canonical-only status projection on malformedFF; literal failed sources/diagnostics bound before r3 observer correction.',
  safety='Outer host guard FNINIT empties/clears hardware before loading temporary guest CW. Malformed software flags are rejected before numeric instruction execution. Wrong owner/thread and unsupported guest CW/status admission controls are independently quantified separately; no raw Runtime restoration claim.',
  excluded='No original process execution, full startup/table27 admission, arbitrary live values, unmasked numeric equivalence, mapping replacement/concurrency/reparse publication, raw Runtime calls or external constructor/borrow failures.',original_after_execution_input=False,original_executed=False,frozen_runtime_modified=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':dict(sorted(pins.items()))},indent=2)+'\n')
 print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),bindings=len(pins),historical_resolutions=len(resolutions),objects=len(objects),header_reads=len(headers))))
except BaseException:
 (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-seal-source.py').write_bytes(Path(__file__).read_bytes());raise
