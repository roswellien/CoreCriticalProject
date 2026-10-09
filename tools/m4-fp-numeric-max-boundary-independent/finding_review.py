"""Own raw/object closure of the failed frozen invoke admission test.

No author model, fixture, executor, or process execution is imported or used.
"""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-fp-numeric-max-host-boundary'
OUT=BASE/'independent-boundary-finding-r1'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={};COMMANDS=[]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Frozen identity '+str(p));PINS[str(p)]=got;return p
def js(p,h=None):return json.loads(pin(p,h).read_text())
def model(b):
 need(b[:8]==b'MW4NBI01'and struct.unpack_from('<4I',b,8)==(1,525,1248,0)and len(b)==24+525*1248,'Exact independent failed framing')
 kinds={};status_failures=0
 cws=[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f]
 for i in range(525):
  r=b[24+i*1248:24+(i+1)*1248];tag=struct.unpack_from('<8I',r);ident,kind,actual,expected,target,ret,borrow,thread=tag;kinds[kind]=kinds.get(kind,0)+1
  need(ident==i and target==0x4c19f0 and ret==(0x12345678 if kind==5 else 0x410a80) and borrow==(0 if kind==8 else 1) and thread==(1 if kind==7 else 0),'Own exact call/refusal tags')
  before,after=r[32:640],r[640:1248];cw=cws[(i//2+3)%12]if i<432 else 0xb7f
  need(struct.unpack_from('<2HB',before)==(cw,0x3a20,0x81),'Actual installed occupied TOP7/depth2/PE+C1 host input')
  need(struct.unpack_from('<7I',before,512)==(0xffff0000|cw,0xffff3a20,0xffff3ffc,0x33445566,0x01230023,0x99aabbcc,0xffff002b),'Actual complete authored and then hardware-observed legacy input')
  need(before[:5]==after[:5]and before[6:28]==after[6:28]and before[512:540]==after[512:540]and before[544:608]==after[544:608],'Actual outside-C++ numeric metadata/MXCSR/ENV/nonvolatile GPR restoration')
  for j in range(8):need(before[32+j*16:42+j*16]==after[32+j*16:42+j*16],'Actual host raw80 bank retained; dead storage observations separate')
  for j in range(6,16):
   wanted=bytes((0x65+j*17+k*29)&255 for k in range(16));a=160+j*16
   need(before[a:a+16]==after[a:a+16]==wanted,'Actual seeded ABI XMM6..15 restoration')
  if kind==9:need(i==524 and actual==1 and expected==0,'Concrete successful malformed-shadow misadmission');status_failures+=1
  else:need(actual==expected and expected==int(kind in(1,8)),'All preceding required successes and denials passed')
 need(kinds=={1:438,2:12,3:41,4:29,5:1,6:1,7:1,8:1,9:1}and status_failures==1,'Complete actual causal extent')
 return kinds
def controls(b):
 labels=[]
 for label,off in [('before CW',24+32),('after status',24+640+2),('after raw80',24+640+32),('after ENV',24+640+512),('after NV XMM',24+640+256),('after NV GPR',24+640+544),('alias outcome',24+524*1248+8),('unsafe header acceptance',20)]:
  x=bytearray(b);x[off]^=1
  try:model(x)
  except ValueError:labels.append(label)
  else:raise ValueError('Own causal observer missed '+label)
 return labels
def run(args,name):
 r=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append({'command':list(map(str,args)),'exit_code':r.returncode,'log':str(p),'sha256':sha(p)});need(r.returncode==0,'Read-only own artifact decode');return r.stdout.decode(errors='replace')
def main():
 need(not OUT.exists(),'Fresh own failed-gate closure');OUT.mkdir(parents=True)
 try:
  compiled=js(BASE/'independent-compiled-r1/report.json','393e07cde65bf4056b8bfe1acfd5c494038dc788b7c9eea1063919287912a5a9');need(not compiled['passed']and all(x['exit_code']==1 for x in compiled['results']),'Both actual normative alias controls failed')
  p=BASE/'independent-compiled-r1/pins.json';mapping=js(p,'2a7212bcfa09de6c41d7e250ef1b2e8a7f7bc687530d05d6e11c9da18d168338')['files']
  for p,h in mapping.items():pin(p,h)
  src=Path(__file__).resolve();(OUT/'review-source.py').write_bytes(src.read_bytes());pin(src);pin(OUT/'review-source.py')
  results=[]
  for result in compiled['results']:
   b=Path(result['raw']).read_bytes();kinds=model(b);results.append(dict(level=result['level'],raw_sha256=sha(result['raw']),records=525,numeric_GPR_NV_XMM_restoration_records=525,kinds=kinds,rejects=controls(b),misadmissions=1))
  header=pin(BASE/'derivation-r4/session.hpp');text=header.read_text();need('bool invoke(GuestAddress target,GuestAddress return_pc,bool acquire_borrow=true)noexcept' in text,'Exact production outer invoke')
  need('s.sw.ie<<0' in text and 'const auto sticky=sw&~0x3800U' in text and '(sticky!=0&&sticky!=2&&sticky!=34)' in text,'Exact integer alias route from raw IE2 to admitted DE2')
  own=(ROOT/'tools/m4-fp-numeric-max-boundary-independent/controls.cpp').read_text();need('f.s.sw.ie=2;f.s.sw.de=0' in own and 'boundary(*f.session,9,false)'in own,'Own direct compiled nonboolean State mutation independent from author fixture')
  readobj=pin(LLVM/'llvm-readobj.exe');dump=pin(LLVM/'llvm-objdump.exe');decodes=[]
  for lv in('O0','O2'):
   p=next((BASE/'independent-compiled-r1'/lv).rglob('controls.cpp.obj'));pin(p);meta=run([readobj,'--unwind','--relocations','--symbols',p],lv+'-own-coff.txt');code=run([dump,'-d','--print-imm-hex',p],lv+'-own-code.txt');need('own_nmx_invoke'in meta and'__CxxFrameHandler3'in meta and'fxsave'in code and'fxrstor'in code and'fldenv'in code,'Actual compiled Session invoke/guard/EH numerical paths');decodes.append(str(p))
  p=pin(BASE/'independent-compiled-r1/boundary.obj');meta=run([readobj,'--unwind','--relocations','--symbols',p],'own-assembly-coff.txt');code=run([dump,'-d','--print-imm-hex',p],'own-assembly-code.txt');need('own_nmx_invoke' in meta, 'Actual direct assembly return route');need(all('SAVE_XMM128 reg=XMM'+str(i)in meta for i in range(6,16))and'fxsave'in code and'fldenv'in code,'Actual assembly nonvolatile unwind and hardware input/capture instructions');decodes.append(str(p))
  report=dict(passed=True,acceptance=False,scope='Independent compiled/raw proof of numerical boundary restoration and concrete malformed raw FPU shadow admission failure',candidate=compiled['candidate_build'],candidate_session_sha256=sha(header),own_compiled_report_sha256=sha(BASE/'independent-compiled-r1/report.json'),results=results,raw_records=1050,compiled_checks_before_failure_per_level=25491,expected_alias_denial_failed_levels=2,compiled_object_decodes=3,decodes=decodes,source_contract='Raw IE=2 and DE=0 project via status() as DE=2; coherent softwareFX passes sticky domain and complete invoke succeeds. Canonical measured corpus remains unchanged; explicit0/1 shadow admission needed for invalid-State denial.',host_scope='Complete ENV28/x87 CW/SW/tag/raw80/MXCSR and nonvolatile GPR/XMM6..15 after actual invoke return before any harness restoration; host XMM0..5/reserved FX bytes unclaimed',author_fixture_model_or_executor_imported=False,original_executed=False,whole_M4_complete=False,commands=COMMANDS)
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
  for p,h in PINS.items():need(sha(p)==h,'Stable frozen failure evidence')
  (OUT/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n');print(json.dumps({'passed':True,'acceptance':False,'bindings':len(PINS),'report_sha256':sha(OUT/'report.json'),'pins_sha256':sha(OUT/'pins.json')}))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
