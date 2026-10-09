"""Freeze joint27 compile-only artifacts and exact observational source deltas."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint27-startup'
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir();cache={};pins={};copies=[];headers=[];objects=[]
def sha(p):
 p=Path(p).resolve()
 if p not in cache:
  with p.open('rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def bind(p,h=None):
 p=Path(p).resolve();a=sha(p);assert h is None or h==a,(str(p),h,a);assert str(p) not in pins or pins[str(p)]==a;pins[str(p)]=a;return a
def data(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
try:
 build=BASE/'build-only-r1';b=data(build/'build.json');assert b['passed']and not b['worker_executed'];bind(build/'build.json');derived=BASE/'derived-r1';g=data(derived/'generation.json');bind(derived/'generation.json',b['generation_sha256']);bind(derived/'pins.json')
 for name,h in data(derived/'pins.json')['files'].items():bind(name,h)
 for key in ('sources','artifacts','tools'):
  for name,h in b[key].items():bind(name,h)
 for c in b['commands']:bind(c['log'],c['log_sha256'])
 for p in BASE.rglob('*'):
  if p.is_file()and not p.is_relative_to(out)and'compiler-temp'not in p.parts:bind(p)
 for p in (ROOT/'tools/m4-joint27-startup').rglob('*'):
  if p.is_file()and'__pycache__'not in p.parts:
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(p);bind(q,h);copies.append(dict(original_path=str(p),preserved_path=str(q),sha256=h))
 prerequisites=[]
 for rel in ('reports/m4-mixed-startup/independent-review-r1','reports/m4-fp-numeric-max-carry/root-component-acceptance-r2','reports/m4-fp-numeric-max-carry/author-canonical-worker-addendum-r1','reports/m4-runtime/independent-service-r9'):
  p=ROOT/rel;bind(p/'report.json');bind(p/'pins.json');d=data(p/'pins.json')
  for name,h in d['files'].items():
   if isinstance(h,dict):assert set(h)=={'sha256','size_bytes'} and Path(name).stat().st_size==h['size_bytes'];bind(name,h['sha256'])
   else:bind(name,h)
  prerequisites.append(dict(report=str(p/'report.json'),report_sha256=sha(p/'report.json'),pins=str(p/'pins.json'),pins_sha256=sha(p/'pins.json'),bindings=len(d['files'])))
 previous=ROOT/'reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/session.hpp';a=previous.read_text();n=(derived/'session.hpp').read_text()
 a=a.replace(' void(*test_after_event)(Session&,unsigned){};',' void(*observe_root_entry)(Session&){}; // New observational hook, null outside joint27 records.\n void(*test_after_event)(Session&,unsigned){};').replace('try{source_check();admit_fp();auto token=','try{source_check();admit_fp();if(observe_root_entry)observe_root_entry(*this);auto token=');assert a==n
 reversible=[];old=ROOT/'reports/m4-mixed-startup/native-derived-r2';oldprotocol=(ROOT/'tools/m4-mixed-startup/native_protocol.hpp').as_posix();newprotocol=(derived/'joint_protocol.hpp').as_posix()
 for name,h in g['ancestor_generation']['generated_sources'].items():
  p=Path(name);q=derived/'derived'/p.relative_to(old);bind(p,h);bind(q);assert q.read_text()==p.read_text().replace(oldprotocol,newprotocol);reversible.append(dict(original=str(p),new=str(q),only_change='Observer-header include path; LLVM IR files byte-identical',original_sha256=sha(p),new_sha256=sha(q)))
 for level in ('O0','O2'):
  for name in re.findall(r'Note: including file:\s*([^\r\n]+)',(build/f'{level}-build.log').read_text(encoding='utf-8-sig')):
   p=Path(name.strip());headers.append(dict(level=level,path=str(p.resolve()),sha256=bind(p)))
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 for name in ('clang-cl.exe','lld-link.exe','llvm-mt.exe','llvm-link.exe','opt.exe','llc.exe','llvm-readobj.exe','llvm-objdump.exe'):bind(llvm/name)
 sdk=Path('C:/Program Files (x86)/Windows Kits/10');vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
 for name in ('bcrypt','kernel32','user32','gdi32','winspool','shell32','ole32','oleaut32','uuid','comdlg32','advapi32'):bind(sdk/f'Lib/10.0.26100.0/um/x64/{name}.lib')
 for name in ('msvcrt','msvcprt','vcruntime','oldnames'):bind(vs/f'lib/x64/{name}.lib')
 bind(sdk/'Lib/10.0.26100.0/ucrt/x64/ucrt.lib');bind(sdk/'bin/10.0.26100.0/x64/rc.exe');bind(sys.executable)
 paths=[]
 for level in ('O0','O2'):
  paths.extend(Path(p)for p in b['objects'][level]);paths.extend((ROOT/f'build/m4-joint27-build-only-r1-{level}').rglob('*.obj'));bind(b['workers'][level])
 for i,p in enumerate(dict.fromkeys(paths)):
  row=dict(path=str(p),sha256=bind(p),commands=[])
  for args,q in (([str(llvm/'llvm-objdump.exe'),'-d',str(p)],out/f'object-{i:02d}-disassembly.txt'),([str(llvm/'llvm-readobj.exe'),'--file-headers','--coff-directives','--unwind',str(p)],out/f'object-{i:02d}-metadata.txt')):
   r=subprocess.run(args,capture_output=True,timeout=60);assert r.returncode==0,(args,r.stderr);q.write_bytes(r.stdout);row['commands'].append(dict(arguments=args,exit_code=0,output=str(q),sha256=bind(q)))
  objects.append(row)
 report=dict(passed=True,scope='Author frozen compile/link-only candidate; no worker invocation, joint27 equivalence or full M4 credit',build=str(build/'build.json'),build_sha256=sha(build/'build.json'),generation=str(derived/'generation.json'),generation_sha256=sha(derived/'generation.json'),literal_sources=copies,prerequisites=prerequisites,source_delta='Canonical Session has only NULL-default root-entry observation hook after existing source/admit checks before LLVM call; copied26 source/IR changes only observer include paths. Numeric/flag/C1/State calculation and checked bridges unchanged.',reversible_source_checks=reversible,compiled_header_reads=len(headers),compiled_headers=headers,fresh_COFF_objects=objects,
 boundary='Context::invoke_selected_table noexcept bool: one stable runtime/State/Session; one NumericalHostBoundary and Borrow across entire27-loop; catches/observation/borrow cleanup precede final numericalrestore then status return. Direct outside-return caller capture precedes caller cleanup. Raw Runtime has no preservation claim.',
 formats=dict(phases_magic='MW4J27N1',phase_header_bytes=32,phase_bytes=132636,common_bytes=116964,pages=14,phase_expected_count=1296,sequence_magic='MW4J27S1',sequence_header_bytes=24,sequence_bytes=122824,sequence_expected_count=48,numeric_checkpoint_bytes=4084,numeric_PC_events=22,numeric_real_runtime_routes=3),
 host_provenance='Sequence host fields direct outside whole-loop boundary. Component phase kind1 holds old local-scope observations; numeric phase kind2 holds actual raw internal before/after without any equality/preservation assumption. Numerical CW/SW/TOP/tags/raw80/MXCSR/fullENV scope; volatileSIMD/reservedFX observed only.',
 first_refusal_recipe='Before successful capture, independently authored compiled fixture may include frozen worker with renamed main, use public Context.runtime/state/session to trigger owner/thread/code/IAT/frame/output/FLD memory faults, then correct triggers and prove stable firstPOD refusal/whole-table numerical restoration before cleanup. No guest original bodies execute.',
 retained_predecessors='derived-r1/predecessor-tuples-O0/O2.bin retain complete prior+following actual103468-byte records for all48sequences/level; planning evidence only, never execution input',
 known_limits='No initial actual joint27 execution yet; firstrefusal controls and predictive raw review still required. Context construction/destruction external to invocation not covered. Stable owned mappings, sequential ordinary paths; no concurrent/reparse ownership claim.',
 original_executed=False,worker_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':dict(sorted(pins.items()))},indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),bindings=len(pins),objects=len(objects),header_reads=len(headers))))
except BaseException:
 (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-seal-source.py').write_bytes(Path(__file__).read_bytes());raise
