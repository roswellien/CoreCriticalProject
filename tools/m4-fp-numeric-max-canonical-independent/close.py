"""Independent source/actual compiled and direct hardware-boundary closure."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry';OUT=BASE/'independent-canonical-closure-r1'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={};COMMANDS=[]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen physical identity '+str(p));PINS[str(p)]=v;return p
def js(p,h=None):return json.loads(pin(p,h).read_text())
def flat(p,h=None):
 d=js(p,h)['files']
 for p,h in d.items():pin(p,h)
 return len(d)
def run(args,name):
 args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);need(r.returncode==0,'Own fresh artifact decode '+name);COMMANDS.append(dict(command=args,exit_code=r.returncode,log=str(p),sha256=sha(p)));return r.stdout.decode(errors='replace')
def raw_model(b):
 need(b[:8]==b'MW4NBI01'and struct.unpack_from('<4I',b,8)==(1,1416,1248,1)and len(b)==24+1416*1248,'Exact own successful canonical framing')
 cws=[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f];kinds={}
 for i in range(1416):
  r=b[24+i*1248:24+(i+1)*1248];ident,kind,actual,expected,target,ret,borrow,thread=struct.unpack_from('<8I',r);kinds[kind]=kinds.get(kind,0)+1
  need(ident==i and target==0x4c19f0 and ret==(0x12345678 if kind==5 else 0x410a80)and borrow==int(kind!=8)and thread==int(kind==7),'Exact own route/refusal tags')
  need(actual==expected==int(kind in(1,8)),'Actual successful/denied status for every independent case')
  before,after=r[32:640],r[640:1248];cw=cws[(i//2+3)%12]if i<1152 else 0xb7f
  need(struct.unpack_from('<2HB',before)==(cw,0x3a20,0x81),'Actual installed occupied TOP7/depth2/PE+C1 host profile')
  need(struct.unpack_from('<7I',before,512)==(0xffff0000|cw,0xffff3a20,0xffff3ffc,0x33445566,0x01230023,0x99aabbcc,0xffff002b),'Whole hardware-observed authored legacy before profile')
  need(before[:5]==after[:5]and before[6:28]==after[6:28]and before[512:540]==after[512:540]and before[544:608]==after[544:608],'Real outside-return x87 metadata/MXCSR/wholeENV/NV GPR retained')
  for j in range(8):need(before[32+j*16:42+j*16]==after[32+j*16:42+j*16],'Complete actual host raw80 bank observations retained')
  for j in range(6,16):
   off=160+16*j;wanted=bytes((0x65+j*17+k*29)&255 for k in range(16));need(before[off:off+16]==after[off:off+16]==wanted,'Seeded ABI XMM6..15 actually retained')
 need(kinds=={1:1158,2:12,3:127,4:27,5:1,6:1,7:1,8:1,9:88},'Independent fixture extent and all eleven-byte cases')
 return kinds
def controls(b):
 rejects=[]
 for label,off in [('magic',0),('header passed',20),('before CW',56),('before ENV',24+32+512),('after CW',24+640),('after SW',24+642),('after tag',24+644),('after MXCSR',24+640+24),('after raw80',24+640+32),('after ENV',24+640+512),('after NV XMM',24+640+256),('after NV GPR',24+640+544),('alias accepted',24+1240*1248+8),('wrong thread tag',24+4*1248+28),('wrong target',24+16),('bad trailing extent',len(b)-1)]:
  x=bytearray(b)
  if label=='bad trailing extent':x.pop()
  else:x[off]^=1
  try:raw_model(x)
  except ValueError:rejects.append(label)
  else:raise ValueError('Own observer missed causal change '+label)
 positives=[]
 for label,off in [('volatile XMM0 output',24+640+160),('reserved FX output',24+640+500),('record padding output',24+640+542)]:
  x=bytearray(b);x[off]^=1;raw_model(x);positives.append(label)
 return rejects,positives
def main():
 need(not OUT.exists(),'Fresh independent canonical closure');OUT.mkdir(parents=True)
 try:
  src=Path(__file__).resolve();(OUT/'review-source.py').write_bytes(src.read_bytes());pin(src);pin(OUT/'review-source.py');pin(sys.executable)
  author=js(BASE/'author-canonical-review-r1/report.json','624cedf34d980780016afac8de7234e9d3aa8cd29269c82f644caff276506ae7');author_count=flat(BASE/'author-canonical-review-r1/pins.json','e1beea2b51f3059897da62bc2aec85832a12ff5cdd19fd767cdfa8b3353c7f10');need(author_count==5346,'Exact final author physical map extent')
  compiled=js(BASE/'independent-compiled-canonical-r2/report.json','a1fe193fdc98a462c3873931337894ae3b848b7a08d087c3bdce92f623a06fe7');flat(BASE/'independent-compiled-canonical-r2/pins.json','41f22f439862bf7a5244e94c202cf5b9dc91484db1bb7faf571649e284bd0ba3');need(compiled['passed'],'Actual own compiled positive/fault matrix')
  # Historical own failed normative gate and this review's failed compile remain literal.
  flat(ROOT/'reports/m4-fp-numeric-max-host-boundary/independent-boundary-finding-r1/pins.json','4b4daf41c1ca1070f85f904e3b7383745ce51d176c3f72bf02fb5efd0730e413')
  derivation=js(ROOT/'tools/m4-fp-numeric-max-canonical-independent/r2/derivation.json')
  for p,h in derivation['prior_failure_files'].items():pin(p,h)
  correction=js(ROOT/'tools/m4-fp-numeric-max-canonical-independent/provenance_correction.json');need(correction['prior_and_current_gate_sha256']=='73a4fa0b37415a7510775d4a1939872a598168b92cc4f9b5bcf581f97e5f312e','Corrected derivation prose has no fake gate-label change')
  header=pin(BASE/'native-preparation-canonical-r1/session.hpp','22bef4a73a171b9900b0376d7d2c3022d208b5e8b2c6159ccad2d060834da9b1');ancestor=pin(BASE/'native-preparation-repair-r2/session.hpp','8940b674d2517fdd1dc8969edf564657683880cee8242f4161264d1008b810e2');a,b=ancestor.read_text(),header.read_text()
  guard='for(const auto byte:std::array<std::uint8_t,11>{s_.sw.ie,s_.sw.de,s_.sw.ze,s_.sw.oe,s_.sw.ue,s_.sw.pe,s_.sw.sf,s_.sw.c0,s_.sw.c1,s_.sw.c2,s_.sw.c3})if(byte>1)deny("Noncanonical FP shadow flag byte rejected");'
  need(b.count(guard)==1 and b.replace(guard,'')==a,'Exactly eleven byte<=1 guards before projection, no normalization or other derivative changes')
  need('void admit_fp(){'+guard+'auto sw=status(s_)'in b,'Canonical shadow rejection precedes arithmetic projection')
  need('s_.sw.c1=0; /* FLD has no stack overflow' in b and 'sticky!=544&&sticky!=546' in b,'Separately inherited carry/C1 behavior explicitly inspected')
  need('bool invoke(GuestAddress target,GuestAddress return_pc,bool acquire_borrow=true)noexcept' in b and 'catch(...){ok=false;}'in b and '~NumericHostBoundary()'in b and 'fxrstor64 %0\\n\\tfldenv %1'in b,'Outer status-return production numerical restoration after internal unwind')
  need('longjmp'not in b and'inttoptr'not in b and'ptrtoint'not in b,'No foreign jump buffer or guest pointer casts')
  own=pin(ROOT/'tools/m4-fp-numeric-max-canonical-independent/r2/controls.cpp').read_text()
  need('for(unsigned value:{2U,17U,34U,255U})for(unsigned coherent:{0U,1U})'in own and 'Canonical guard causally precedes projected status and FX coherence checks'in own,'Independent causal canonical guard fixtures')
  for imp in re.findall(r'^\s*(?:import|from)\s+(.+)$',src.read_text(),re.M):need('m4_'not in imp,'No author comparator/fixture/executor imports')
  readobj=pin(LLVM/'llvm-readobj.exe');dump=pin(LLVM/'llvm-objdump.exe');decodes=[];results=[]
  for result in compiled['results']:
   lv=result['level'];kinds=raw_model(Path(result['raw']).read_bytes());neg,pos=controls(Path(result['raw']).read_bytes());r=result['result'];need(r['checks']==68104 and r['scenarios']==710 and r['entered_faults']==127 and r['corrected_poison_retries']==127 and r['positive_phases']==1159,'Exact actual own compiled counts')
   results.append(dict(level=lv,compiled=r,direct_hardware_records=1416,kinds=kinds,negative_observer_controls=neg,scoped_positive_controls=pos))
   for label,p in [(lv+'-own',next((BASE/'independent-compiled-canonical-r2'/lv).rglob('controls.cpp.obj'))),(lv+'-guest',BASE/'native-canonical-r1'/f'native-{lv}.obj')]:
    pin(p);meta=run([readobj,'--unwind','--relocations','--symbols',p],label+'-coff.txt');code=run([dump,'-d','--print-imm-hex',p],label+'-code.txt')
    if label.endswith('-own'):need('own_nmx_invoke'in meta and'__CxxFrameHandler3'in meta and all(x in code for x in('fxsave','fxrstor','fldenv')),'Actual own inline Session status-return/EH/FP boundary compiled')
    else:need(all(x in meta for x in('mw34_nmx_fld_commit','mw34_nmx_fstp_commit','mw34_nmx_readf32','mw34_nmx_writef32')) and meta.count('RuntimeFunction {')>=3,'Exact actual compiled guest FLD/FSTP typed bridges and unwind metadata')
    decodes.append(str(p))
  p=pin(BASE/'independent-compiled-canonical-r2/boundary.obj');meta=run([readobj,'--unwind','--relocations','--symbols',p],'own-assembly-coff.txt');code=run([dump,'-d','--print-imm-hex',p],'own-assembly-code.txt');need('own_nmx_invoke'in meta and all('SAVE_XMM128 reg=XMM'+str(i)in meta for i in range(6,16))and all(x in code for x in('fxsave','fnstenv','fxrstor','fldenv')),'Direct actual outside-return capture and ABI unwind');decodes.append(str(p))
  report=dict(passed=True,scope='Independent compiled canonical eleven-byte admission and numeric Session.invoke actual numerical/ABI boundary; inherited eight-status carry model independently predicted in own bounded FLTMAX fixtures',author_physical_bindings_rehashed=author_count,actual_compiled_checks=136208,actual_compiled_scenarios=1420,success_phases=2318,actual_entered_faults=254,corrected_poison_retries=254,malformed_shadow_cases=176,direct_hardware_records=2832,negative_observer_controls=32,scoped_observer_positives=6,compiled_object_decodes=len(decodes),decodes=decodes,results=results,canonical_source_delta='Only eleven <=1 raw-byte checks before status projection relative to carry-repair-r2; no input normalization',historical_own_failure='Old r3 numeric host restoration succeeded but IE=2 raw alias completed; old normative r1 remains rejected. New own fixture compile-comment failure before execution retained; repaired own comment only. Derivation prose gate-label correction explicitly retracted because actual hashes were already identical.',preentry_vs_entered='Bad external return, nested owner, and sequential wrong-thread refused before root entry and allowed valid owner reuse; entered source/checked-memory/domain/return faults remain poisoned with first fault retained after correction.',host_scope='Actual complete ENV28, x87 CW/SW/tag/raw80/MXCSR and seeded nonvolatile XMM6..15/GPR captured after invoke status return before any harness restore. XMM0..5 and reserved/padding bytes excluded. Dead raw80 banks matched only as actual observations.',guest_scope='Own full3504 dirty State/four whole pages/22 exact events/three actual completed routes asserted by compiled source model across 1,152 two-phase status-matrix calls per level and recovered positives. No new original execution/comparison and no connected27 startup admission. Final FP condition bits/dead guest bank observations do not establish general defined-value credit.',tooling_scope='Exact currently rehashable disk source/tool/object association and fresh decode; no past process-memory attestation or full process trace.',author_fixture_model_executor_imported=False,original_executed=False,full_CRT=False,whole_M4_complete=False,commands=COMMANDS)
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
  for p,h in PINS.items():need(sha(p)==h,'Final physically stable evidence '+p)
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(PINS),report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
