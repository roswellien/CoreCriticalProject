"""Independent read-only joint initializer ABI/source/object receipt; no worker run."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint27-startup';OUT=BASE/'independent-static-r1'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={};COMMANDS=[]
ENT=(0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c19f0,0x4c78f0,0x4c7940,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0)
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000)
def need(b,m):
 if not b:raise ValueError(m)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();actual=sha(p);need(h is None or actual==h,'Physical identity '+str(p));PINS[str(p)]=actual;return p
def data(p,h=None):return json.loads(pin(p,h).read_text())
def flat(p,h=None):
 d=data(p,h)['files']
 for p,h in d.items():pin(p,h)
 return len(d)
def run(args,name):
 args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=60);p=OUT/name;p.write_bytes(r.stdout+r.stderr);pin(p);need(r.returncode==0,'Read-only decode '+name);COMMANDS.append(dict(command=args,exit_code=r.returncode,log=str(p)));return r.stdout.decode(errors='replace')
def source_check(s):
 need(s.count('seed(r_,repeat,cw,top);')==1,'Single construction seed')
 start=s.index('bool invoke_selected_table(');end=s.index('void snapshot_numeric(',start);loop=s[start:end]
 need('seed('not in loop and 'memset('not in loop and 'mark_remill_seeded('not in loop,'No whole-loop state reseed')
 need(loop.count('ni::NumericHostBoundary boundary(admitted_cw_)')==1 and loop.count('ni::Session::Borrow borrow(*session_)')==1,'One outer numerical boundary and lexical owner')
 need(loop.index('ni::NumericHostBoundary')<loop.index('try{')<loop.index('ni::Session::Borrow')<loop.index('for(const auto&item:ledger.items())'),'Boundary encompasses internal cleanup and full actual table loop')
 need(')noexcept{'in loop and 'catch(...)'in loop and 'return ok;'in loop and 'throw;'in loop,'Status-return outer catch encloses nested rethrow')
 need('canonical();require(r_.cpu().esp==frame+4' in loop and 'r_.call_direct(item.target,{broker})' in loop,'Canonical guard then actual persistent dispatcher call')
 need('phase==27&&r_.calls().size()==29&&r_.translation_count()==28' in loop and '!ledger.completed()&&!ledger.failed()' in loop,'Selected subset preserves full-ledger incomplete status')
 need('require(!attempted_&&!failed_' in loop and 'attempted_=true' in loop and 'failed_=true;if(!first_.kind)'in loop,'Single-shot Context and immutable first refusal')
 need('caller.capture();summary.host_before=caller.before.b' in s and 'context.invoke_selected_table(seq,repeat,top,records);caller.capture()' in s,'Actual outside-return numerical capture before harness cleanup')
 need('raw_before.capture();observation=&record;'in loop and 'raw_after.capture();snapshot_numeric(record)'in loop and 'record.host_observation_kind=2' in loop,'Numeric raw phase checkpoints distinctly internal')
 return loop
def main():
 need(not OUT.exists(),'Fresh independent static receipt');OUT.mkdir(parents=True)
 try:
  src=Path(__file__).resolve();(OUT/'review-source.py').write_bytes(src.read_bytes());pin(src);pin(OUT/'review-source.py');pin(sys.executable)
  author=data(BASE/'author-build-review-r2/report.json','751d586a9a17d9d06d9bad33f76c6a1c1caff47421888618083411fef6802f55');count=flat(BASE/'author-build-review-r2/pins.json','902c95bf6a56afa4a07873b5bf2d3b515bc623420dfaa62e736864ea7c092509');need(author['passed'] and not author['worker_executed'] and not author['original_executed'],'Compile-only author scope')
  build=data(BASE/'build-only-r1/build.json','695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5');gen=data(BASE/'derived-r1/generation.json','85043cc17fe60dd352251dfa643d39f3bed69c2c8d122dd51efd69bdbd80abd7')
  for m in ('sources','tools','artifacts'):
   for p,h in build[m].items():pin(p,h)
  for m in ('original_sources','generated_sources'):
   for p,h in gen[m].items():pin(p,h)
  old26=data(ROOT/'reports/m4-mixed-startup/independent-review-r1/report.json','3c4f6b2903efeca37f08b2119b1dc87d374a39cc2284079ccc26abfd30db9f96');flat(ROOT/'reports/m4-mixed-startup/independent-review-r1/pins.json','50faf5a4e2cba43ed96e24c9de827d73bc5247aee67cebe5572291086d8ee845')
  canonical=data(ROOT/'reports/m4-fp-numeric-max-carry/independent-canonical-closure-r1/report.json','4bba2d6167d14e371153b78ed12261209951fb0271e494f1601362ada6214395');flat(ROOT/'reports/m4-fp-numeric-max-carry/independent-canonical-closure-r1/pins.json','296cad9283fb38266e2aa7f3157ea4a7977a98f1552a3358f6deb422412a9cf3')
  s=pin(ROOT/'tools/m4-joint27-startup/native_main.cpp','b9b3980be51a2dafbc5032d69d52539747b9b465ba3163d270d519b717930511').read_text();source_check(s)
  ancestor=pin(ROOT/'reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/session.hpp','22bef4a73a171b9900b0376d7d2c3022d208b5e8b2c6159ccad2d060834da9b1').read_text();new=pin(BASE/'derived-r1/session.hpp').read_text()
  hook=' void(*observe_root_entry)(Session&){}; // New observational hook, null outside joint27 records.\n';call='if(observe_root_entry)observe_root_entry(*this);'
  need(new.count(hook)==new.count(call)==1 and new.replace(hook,'').replace(call,'')==ancestor,'Exactly observational NULL-default header delta; no arithmetic/ownership/admission change')
  diffs=[]
  for p in (BASE/'derived-r1/derived').rglob('*'):
   if not p.is_file():continue
   a=pin(ROOT/'reports/m4-mixed-startup/native-derived-r2'/p.relative_to(BASE/'derived-r1/derived'));b=pin(p);x,y=a.read_text(),b.read_text()
   # Every changed CPP/header line is exclusively the observer-header include.
   n=lambda t:re.sub(r'#include "[^"]*native_protocol\.hpp"','#include "OBSERVATION_PROTOCOL"',re.sub(r'#include "[^"]*joint_protocol\.hpp"','#include "OBSERVATION_PROTOCOL"',t))
   need(n(x)==n(y),'Reversible observer-only component derivative '+str(p));diffs.append(dict(path=str(p),literal_equal=x==y))
  for label in ('4c19f0','4c1a00','780c10f0'):
   a=pin(ROOT/f'reports/m4-fp-numeric-max-integration/preparation-r4/{label}-runtime.ll');b=pin(BASE/f'derived-r1/numeric-ir/{label}-runtime.ll');need(a.read_bytes()==b.read_bytes(),'Exact unchanged complete numeric LLVM '+label)
  oldmain=pin(ROOT/'tools/m4-mixed-startup/native_main.cpp').read_text();need((BASE/'derived-r1/seed.inc').read_text()==oldmain[oldmain.index('static void seed('):oldmain.index('static void register_all(')],'Identical accepted26 one-time dirtyState seed')
  host=pin(BASE/'derived-r1/caller_observer.inc').read_text();oldhost=pin(ROOT/'tools/m4-fp-numeric-max-carry/native.cpp').read_text();need(host==oldhost[oldhost.index('struct Host {'):oldhost.index('static void seed(State')],'Identical direct numeric caller observation fixture')
  protocol=pin(BASE/'derived-r1/joint_protocol.hpp').read_text()
  for key,expected in [('pages',PAGES),('entries',ENT)]:
   found=re.search(key+r'\{([^}]+)\}',protocol).group(1);need(tuple(int(x,0)for x in found.split(','))==expected,'Exact explicit '+key)
  common=9*4+2*40+4*512+4*28+2*14*4096;native=common+2*3504+10*4+192*20+2*96+4084+110*4+15*4+2*4;sequence=12*4+2*512+2*28+2*3504+2*14*4096
  need((common,native,sequence)==(116964,132636,122824),'Independent packed wire size sums')
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();u16=lambda a:struct.unpack_from('<H',game,a)[0];u32=lambda a:struct.unpack_from('<I',game,a)[0];nt=u32(0x3c);opt=nt+24;ib=u32(opt+28);need(u16(nt+4)==0x14c and ib==0x400000,'Exact x86 source image')
  def va(a,n=4):
   rr=a-ib;matches=[]
   for i in range(u16(nt+6)):
    o=opt+u16(nt+20)+40*i;vs,rva,size,raw=struct.unpack_from('<4I',game,o+8)
    if rva<=rr and rr+n<=rva+size:matches.append(raw+rr-rva)
   need(len(matches)==1,'Unique original raw-backed VA');return game[matches[0]:matches[0]+n]
  table=[(a,struct.unpack('<I',va(a))[0])for a in range(0x5e0000,0x5e0244,4)];selected=[(a,b)for a,b in table if b in ENT];need(len(table)==145 and sum(b!=0 for a,b in table)==144 and tuple(b for a,b in selected)==ENT,'Independent actual full initializer table and selected order');need(selected[18]==(0x5e016c,0x4c19f0),'Actual inserted numeric slot')
  negative=[]
  for name,old,newstr in [('extra seed','canonical();require','seed(r_,0,0x37f,0);canonical();require'),('outer boundary','ni::NumericHostBoundary boundary(admitted_cw_)','ni::NumericHostBoundary misplaced(admitted_cw_)'),('lexical owner','ni::Session::Borrow borrow(*session_)','ni::Session::Borrow omitted(*session_)'),('actual call','r_.call_direct(item.target,{broker})','r_.call_direct({ni::root},{broker})'),('partial ledger','!ledger.completed()&&!ledger.failed()','ledger.completed()&&!ledger.failed()'),('stable first refusal','failed_=true;if(!first_.kind)','failed_=true;if(true)'),('outside capture','records);caller.capture()','records);caller.restore();caller.capture()'),('count','phase==27&&r_.calls().size()==29','phase==27&&r_.calls().size()==27')]:
   need(old in s,'Independent mutation seam '+name)
   try:source_check(s.replace(old,newstr,1))
   except ValueError:negative.append(name)
   else:raise ValueError('Independent source control failed to reject '+name)
  readobj=pin(LLVM/'llvm-readobj.exe');dump=pin(LLVM/'llvm-objdump.exe');objects=[]
  for lv in ('O0','O2'):
   p=pin(ROOT/f'build/m4-joint27-build-only-r1-{lv}/CMakeFiles/mw34_joint27.dir/native_main.cpp.obj');meta=run([readobj,'--symbols','--relocations','--unwind',p],lv+'-outer-coff.txt');code=run([dump,'-d','--print-imm-hex',p],lv+'-outer-code.txt');need('invoke_selected_table'in meta and '__CxxFrameHandler3'in meta and 'NumericHostBoundary'in meta,'Actual C++ outer loop and EH unwind metadata');need(all(x in code for x in('fxsave','fnstenv','fxrstor','fldenv','fninit','fldcw')),'Actual numerical ownership instructions');objects.append(str(p))
   p=pin(BASE/f'build-only-r1/{lv}/numeric.obj');meta=run([readobj,'--symbols','--relocations','--unwind',p],lv+'-numeric-coff.txt');code=run([dump,'-d','--print-imm-hex',p],lv+'-numeric-code.txt');need(all(x in meta for x in('mw34_nmx_entry_4c19f0','mw34_nmx_entry_4c1a00','mw34_nmx_entry_780c10f0','mw34_nmx_fld_commit','mw34_nmx_fstp_commit','mw34_nmx_call')) and meta.count('RuntimeFunction {')>=3,'Actual unchanged numeric complete three-root object and typed routes');objects.append(str(p))
  report=dict(passed=True,scope='Independent compile-only source/inverse-derivative/table/packed ABI/actual object association; no joint27 worker execution or acceptance',author_bindings_rehashed=count,selected_slots=[dict(slot=a,entry=b)for a,b in selected],component_derivatives=diffs,numeric_IR_literal_unchanged=3,packed_schema=dict(common=common,phase=native,sequence=sequence,pages=14,State=3504),source_control_rejections=negative,fresh_COFF_decodes=len(objects),objects=objects,carry='One resident3504State, RuntimeFX and14pages; constructor seed once only. Actual source-table calls include predecessor4B7020 then numeric4C19F0 then following4C78F0; observation hook at actual entered root, no state reseeding.',ownership='Whole-loop NumericHostBoundary outside try; Borrow/internal catches cleanup before status return. Context is single-attempt even for preentry owner/thread refusals; refusal poisons Context but may leave Runtime/Session unentered. Entered failures preserve first diagnostic and poisoned Runtime; these distinctions still need actual compiled controls.',host_scope='Actual outside-return caller capture is distinct from inner numeric phase snapshots. Numerical ENV/x87/CW/SW/tag/raw80/MXCSR; no full volatile SIMD/reserved-FX preservation claim. Construction/destruction outside invocation unclaimed.',limits=['No new joint raw captures reviewed','No actual joint27 fault controls yet','Full144-root ledger intentionally incomplete','Existing26 original proof and numeric separate proof do not establish connected27 original hardware equivalence','Postbuild physical tool/header/object identities, not process-time attestation'],author_or_root_comparator_model_imported=False,original_executed=False,native_executed=False,full_CRT=False,whole_M4_complete=False,commands=COMMANDS)
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
  for p,h in PINS.items():need(sha(p)==h,'Final stable physical review binding '+p)
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(PINS),report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
