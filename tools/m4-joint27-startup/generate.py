"""Prepare new joint27 observer/source derivatives; never compile or execute."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint27-startup'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir();pins={};literal=[];generated={}
def bind(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or h==actual,(str(p),h,actual);pins[str(p)]=actual;return actual
def preserve(p):
 p=Path(p).resolve();q=out/'ancestors'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(p);bind(q,h);literal.append(dict(original_path=str(p),preserved_path=str(q),sha256=h))
def write(p,text):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);generated[str(p)]=bind(p)
accept=ROOT/'reports/m4-fp-numeric-max-carry/root-component-acceptance-r2/report.json';bind(accept,'fe713df4600d61acb3ac1eb6ea80963c1dc225d5e73fa3032795dc1905ca7706');bind(accept.with_name('pins.json'))
prep=BASE/'preparation-r2/report.json';bind(prep,'e77a7ad83aa6ded97f92affe77f4f1d5c0c55f2898f5bbe06802021a2ed00680');bind(prep.with_name('pins.json'))
old=ROOT/'reports/m4-mixed-startup/native-derived-r2';g=json.loads((old/'generation.json').read_text());preserve(old/'generation.json')
protocol=ROOT/'tools/m4-mixed-startup/native_protocol.hpp';preserve(protocol);s=protocol.read_text()
changes=[
 ('std::array<std::uint32_t,11> pages{','std::array<std::uint32_t,14> pages{'),
 ('0x60b000,0x20001000};','0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000};'),
 ('std::array<std::uint32_t,26> entries{','std::array<std::uint32_t,27> entries{'),
 ('0x4b7020,0x4c78f0','0x4b7020,0x4c19f0,0x4c78f0'),
 ('11*4096','14*4096'),
 ('  std::array<Route,2> routes;','  std::array<Route,2> routes;\n  std::array<std::byte,4084> numeric_checkpoint{};\n  std::array<std::uint32_t,110> numeric_PC_events{};\n  std::array<std::uint32_t,15> runtime_routes{};\n  std::uint32_t numeric_phase{},host_observation_kind{};'),
 ('sizeof(Common)==92388&&sizeof(Native)==103468','sizeof(Common)==116964&&sizeof(Native)==132636'),
 ('std::memcpy(fx.data(),&s.x87,512);','std::memcpy(fx.data(),&s.x87,512);std::memset(fx.data()+6,0,18);')]
for a,b in changes:assert s.count(a)==1,a;s=s.replace(a,b)
write(out/'joint_protocol.hpp',s)
for p,h in g['generated_sources'].items():
 p=Path(p);bind(p,h);preserve(p);q=out/'derived'/p.relative_to(old);s=p.read_text();s=s.replace(protocol.as_posix(),(out/'joint_protocol.hpp').as_posix());write(q,s)
header=ROOT/'reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/session.hpp';bind(header,'22bef4a73a171b9900b0376d7d2c3022d208b5e8b2c6159ccad2d060834da9b1');preserve(header);s=header.read_text()
a=' void(*test_after_event)(Session&,unsigned){};';assert s.count(a)==1;s=s.replace(a,' void(*observe_root_entry)(Session&){}; // New observational hook, null outside joint27 records.\n'+a)
a='try{source_check();admit_fp();auto token=';assert s.count(a)==1;s=s.replace(a,'try{source_check();admit_fp();if(observe_root_entry)observe_root_entry(*this);auto token=')
write(out/'session.hpp',s)
for p in (ROOT/'reports/m4-fp-numeric-max-integration/preparation-r4').glob('*-runtime.ll'):preserve(p);write(out/'numeric-ir'/p.name,p.read_text())
source=ROOT/'tools/m4-mixed-startup/native_main.cpp';preserve(source);main=source.read_text();seed=main[main.index('static void seed('):main.index('static void register_all(')];write(out/'seed.inc',seed)
host=ROOT/'reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/native.cpp';preserve(host);h=host.read_text();caller=h[h.index('struct Host {'):h.index('static void seed(State')];write(out/'caller_observer.inc',caller)
# Retain complete actual predecessor/following records, not summary hashes only.
build=ROOT/'reports/m4-mixed-startup/native-r3'
for level in ('O0','O2'):
 p=build/f'native-{level}.bin';bind(p);f=p.open('rb');q=out/f'predecessor-tuples-{level}.bin'
 with q.open('wb') as dst:
  dst.write(b'MW4J27P1'+struct.pack('<6I',1,int(level[1]),48,206936,11,2))
  for seq in range(48):f.seek(32+(seq*26+17)*103468);pair=f.read(206936);assert len(pair)==206936;dst.write(pair)
 f.close();generated[str(q)]=bind(q)
for p in (ROOT/'tools/m4-joint27-startup/native_main.cpp',ROOT/'tools/m4-joint27-startup/CMakeLists.txt',ROOT/'tools/m4-joint27-startup/build.py',ROOT/'tools/m4-joint27-startup/build.ps1'):
 preserve(p)
preserve(Path(__file__).resolve())
report=dict(passed=True,scope='Prepared concrete source/observer derivatives only; no executable invocation',literal_sources=literal,original_sources=pins,generated_sources=generated,ancestor_generation=g,canonical_acceptance=str(accept),canonical_acceptance_sha256=sha(accept),
 source_changes=['Observation-only numeric admitted root-entry callback before compiled guest body','14-page common observer including realIAT/provider RX/RO; FX metadata zero separately from fullState/ENV','New whole-table status-return numerical boundary around all27calls, internal catches and lexical owner cleanup','Unchanged copied guest LLVM numeric/26 modules and arithmetic/tag/C1/source/ownership semantics'],
 whole_loop_boundary='Context::invoke_selected_table noexcept bool; stable Runtime/State/Session persists, one Borrow and NumericHostBoundary cover entire27-loop. No rawRuntime preservation claim.',
 execution_precondition='Freeze compiled COFF/source/recipe and parent independent source/ownership review before any worker execution',source_after_execution_input=False,original_executed=False,whole_M4_complete=False)
(out/'generation.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'generation.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(dict(passed=True,generation_sha256=sha(out/'generation.json'),pins_sha256=sha(out/'pins.json'),literal_sources=len(literal),generated=len(generated))))
