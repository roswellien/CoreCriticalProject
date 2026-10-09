"""Full storage observer for the additive filename seam, borrowing accepted prefix captures."""
import hashlib,json,pathlib,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-filename';ANCESTOR=ROOT/'reports/m4-crt-mainargs/root-execution-r1'
PAGES=[0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000]
SOURCE=['entry-source.bin','matherr-source.bin','control-wrapper.bin','control-thunk.bin','control-hot.bin','control-cold.bin','initterm-thunk.bin','initterm-provider.bin','mainargs-provider.bin','mainargs-builder.bin']
CHECKS=0;OVERLAY={};IDENTITY_FILES={}
def demand(ok,why):
 global CHECKS;CHECKS+=1;assert ok,why
def data(p):p=pathlib.Path(p);return OVERLAY[p] if p in OVERLAY else p.read_bytes()
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def words(p,n):b=data(p);demand(len(b)==n*4,str(p));return struct.unpack('<'+'I'*n,b)
def put(b,p,v):struct.pack_into('<I',b,p,v)
def host(a,b):
 a=data(a);b=data(b);demand(len(a)==len(b)==544,'Direct host capture layout')
 demand(a[:5]==b[:5] and a[24:28]==b[24:28] and a[512:540]==b[512:540],'Complete caller ENV/CW/SW/FTW/MXCSR')
 for i in range(8):demand(a[32+16*i:42+16*i]==b[32+16*i:42+16*i],'Caller physical raw80')
 demand(a[256:416]==b[256:416],'Caller XMM6..15')
def projection(phase,base,state,pages,source):
 demand(data(phase/'state.bin')==bytes(state),'Complete3504State and opaque storage')
 cpu=bytearray(data(base/'state-cpu.bin'))
 for state_offset,cpu_offset in [(2216,0),(2280,24),(2312,16),(2472,36)]:put(cpu,cpu_offset,struct.unpack_from('<I',state,state_offset)[0])
 demand(data(phase/'state-cpu.bin')==cpu,'Source/service declared StateCPU projection')
 for p in PAGES:demand(data(phase/f'page-{p}.bin')==bytes(pages[p]),'Complete borrowed page')
 for name in SOURCE:demand(data(phase/name)==source[name],'Complete literal source identity')
 for name in ['fx.bin','runtime-cpu.bin','crt-globals.bin','tib-0.bin','tib-4.bin','tib-24.bin']:demand(data(phase/name)==data(base/name),'Carried independent FX/RuntimeCPU/TIB/global storage')
def witness(p):
 b=data(p);demand(len(b)==536,'Actual API witness layout');return struct.unpack_from('<4I',b),b[16:276],b[276:536]
def api_identity(row,worker):
 for kind in ['api','module']:
  a=data(row/f'filename-{kind}-before.bin');b=data(row/f'filename-{kind}-after.bin');demand(a==b,'Actual native API/module identity remains stable')
  offset,extent=(72,2184)if kind=='api'else(48,2160);demand(len(a)==extent,'Exact packed native identity layout')
  digest=a[offset:offset+64].decode('ascii');path=pathlib.Path(a[offset+64:].decode('utf-16-le').split('\0')[0]);demand(len(digest)==64 and digest==sha(path),'Actual native physical module/API owner hash')
  IDENTITY_FILES[str(path)]=digest
  region_offset=32 if kind=='api'else 8;base,size,allocation,state,type_,protect,allocation_protect=struct.unpack_from('<3Q4I',a,region_offset)
  demand(state==0x1000 and type_==0x1000000,'Actual committed native image authority')
  if kind=='api':
   address,named,owner,owner_named=struct.unpack_from('<4Q',a);demand(address==named==owner_named and owner==allocation and base<=address<base+size and protect&0xf0,'Actual named/forwarded executable export owner')
  else:demand(struct.unpack_from('<Q',a)[0]==base==allocation and path.resolve()==worker.resolve(),'Actual NULL-module process worker identity, separately from guest Mech3')
def row_check(row,baseline,index,worker):
 result=read(row/'result.json');mode=0 if index<24 else index+37
 demand(result['passed'] and result['control']==mode and result['scenario']==index,'Hash-bound row identity')
 before=row/'filename-before';ancestor=baseline/'mainargs-builder-after'
 for p in before.iterdir():demand(data(p)==data(ancestor/p.name),'Accepted predecessor complete source/State/FX/page boundary reused')
 state=bytearray(data(before/'state.bin'));pages={p:bytearray(data(before/f'page-{p}.bin'))for p in PAGES};source={n:data(before/n)for n in SOURCE}
 job=words(row/'filename-job.bin',22);mc=words(row/'mainargs-job.bin',20)
 demand(job[0]==mode and job[1]==0xa11c0000+index and job[2]==0x20001834 and not job[12],'Filename declared request/frame/terminal activity')
 demand(job[20:]==(0x78037174,0x7800bbd6),'Exact required producer boundary metadata')
 demand(job[5]==job[6] and job[18]==job[19],'Inner and final outer caller LastError restored')
 w,old,new=witness(row/'filename-witness.bin');api_called=mode not in [61,63,64,65,66,67]
 demand(bool(job[13])==api_called,'Actual API invocation credit')
 if api_called:
  api_identity(row,worker);demand(w==(260,job[1],job[3],job[4]),'Immediate actual result/LastError witness')
  demand(old==bytes(pages[0x7803b000][0x3f0:0x3f0+260]),'Full native scratch starts from actual owned guest buffer')
  demand(0<job[3]<260 and new[job[3]]==0 and new[job[3]+1:]==old[job[3]+1:],'Actual native success length/NUL/untouched tail')
 else:demand(data(row/'filename-witness.bin')==bytes(536),'No fabricated API outcome before real invocation')
 def mutation(address,value):put(pages[address&~4095],address&4095,value)
 if mode==61:mutation(0x20001834,0x7800bbd7)
 if mode==63:mutation(0x7802e018,0x343b1)
 if mode==64:mutation(0x7800bbbc,0);source['mainargs-builder.bin']=bytes(4)+source['mainargs-builder.bin'][4:]
 if mode==65:mutation(0x20001838,1)
 if mode==66:mutation(0x20001840,259)
 if mode==71:mutation(0x20001834,0x7800bbd7)
 if mode==72:put(state,2280,struct.unpack_from('<I',state,2280)[0]^1)
 stored=mode in [0,69,70];returned=mode in [0,70]
 demand(bool(job[14])==stored and bool(job[15])==returned and bool(job[16])==(mode==0),'Actual buffer/RET/required stop credit')
 if api_called:
  # The API-after checkpoint precedes its mutation observer.
  apistate=bytearray(data(before/'state.bin'));apipages={p:bytearray(data(before/f'page-{p}.bin'))for p in PAGES};projection(row/'filename-api-after',before,apistate,apipages,{n:data(before/n)for n in SOURCE})
 if stored:
  pages[0x7803b000][0x3f0:0x3f0+260]=new;projection(row/'filename-buffer-after',before,state,pages,source)
 if returned:
  put(state,2216,job[3]);put(state,2312,0x20001844);put(state,2472,0x7800bbd6);projection(row/'filename-return-after',before,state,pages,source)
 if mode==0:
  demand(job[7:18]==(5,5,0,0,1,0,1,1,1,1,0),'Complete positive filename progress/first-fault metadata')
  projection(row/'filename-commandline-before',before,state,pages,source)
  demand(result['fault_reason']==0 and result['fault_site']==0x7800bbd6 and result['fault_target']==0x78037174,'Required producer stop before command-line load')
  demand(mc[10:]==(16,6,0,1,0,1,1,2,0x7800bbd6,0x78037174),'Exact source ledger/terminal nesting')
  events=data(row/'mainargs-events.bin');demand(struct.unpack_from('<4I',events,4*16)==(5,0x7800bbd6,0x20001844,job[3]),'Declared stdcall return route');demand(struct.unpack_from('<4I',events,5*16)==(6,0x7800bbd6,0x78037174,0),'Unexecuted command-line dependency route')
 else:demand(result['fault_site']!=0x7800bbd6 or result['fault_target']!=0x78037174,'Causal row must deny before required dependency')
 for phase in ['mainargs-builder-after','mainargs-after','entry-after-fault','retry-after']:projection(row/phase,before,state,pages,source)
 for kind in ['writer','entry']:host(row/f'{kind}-host-before.bin',row/f'{kind}-host-after.bin')
 demand(mc[12]==0 and mc[14]==0 and mc[15]==1,'Outer mainargs terminal cleanup and first-fault retention')
def main(build_name,execution_name,out_name):
 global CHECKS
 build=BASE/build_name;execution=BASE/execution_name;out=BASE/out_name;demand(out.parent==BASE and not out.exists(),'Fresh observer namespace');out.mkdir()
 b=read(build/'build.json');e=read(execution/'report.json');demand(b['passed'] and e['passed'] and e['build_sha256']==sha(build/'build.json'),'Actual build/execution association')
 inputs={str(pathlib.Path(__file__).resolve()):sha(__file__),str(build/'build.json'):sha(build/'build.json'),str(execution/'report.json'):sha(execution/'report.json'),str(ROOT/'reports/m4-crt-mainargs/root-acceptance-r1/report.json'):sha(ROOT/'reports/m4-crt-mainargs/root-acceptance-r1/report.json')};passed=False
 try:
  for level in ['O0','O2']:
   for i in range(36):
    row=execution/level/f'row-{i}';baseline=ANCESTOR/f'native-{level}'/f'row-{i if i<24 else 0}';row_check(row,baseline,i,pathlib.Path(b['workers'][level]))
    for p in row.rglob('*'):
     if p.is_file():inputs[str(p)]=sha(p)
    for p in(baseline/'mainargs-builder-after').iterdir():inputs[str(p)]=sha(p)
   unit=execution/level/'units';host(unit/'units-host-before.bin',unit/'units-host-after.bin');errors=words(unit/'caller-error.bin',2);demand(errors[0]==errors[1],'Unit final host LastError boundary')
   for size in [0,1,8,260]:
    w,old,new=witness(unit/f'capacity-{size}.bin');demand(w[:2]==(size,0xface0123) and new[size:]==old[size:],'Actual bounded unit request/tail')
    if size in [0,1,8]:demand(w[2:]==(size,122),'Actual modern Windows zero/truncated result/error');
    if size in [1,8]:demand(new[size-1]==0,'Actual truncation includes NUL')
    if size==260:demand(0<w[2]<size and new[w[2]]==0 and new[w[2]+1:]==old[w[2]+1:],'Actual successful unit complete tail')
   for p in unit.iterdir():inputs[str(p)]=sha(p)
  inputs.update(IDENTITY_FILES)
  denials=0
  for level in ['O0','O2']:
   row=execution/level/'row-0';baseline=ANCESTOR/f'native-{level}'/'row-0';worker=pathlib.Path(b['workers'][level])
   probes=[row/'filename-witness.bin',row/'filename-job.bin',row/'filename-api-before.bin',row/'filename-module-before.bin']
   for phase in ['filename-before','filename-buffer-after','filename-return-after','filename-commandline-before','retry-after']:
    probes.extend(row/phase/name for name in ['state.bin','fx.bin','state-cpu.bin','runtime-cpu.bin']+SOURCE+[f'page-{p}.bin'for p in PAGES])
   for p in probes:
    original=data(p)
    for offset in sorted({0,len(original)-1}):
     changed=bytearray(original);changed[offset]^=1;OVERLAY[p]=bytes(changed);denied=False
     try:row_check(row,baseline,0,worker)
     except (AssertionError,UnicodeError,ValueError):denied=True
     finally:OVERLAY.clear()
     demand(denied,f'Meaningful selected capture corruption must be denied: {p}:{offset}');denials+=1
  for p,h in inputs.items():demand(sha(p)==h,'Physical evidence remains immutable')
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Complete additive filename storage/OS witness/terminal observer with frozen accepted prefix captures',checks=CHECKS,selected_capture_corruption_denials=denials if passed else 0,positive_sequences=48 if passed else 0,causal_sequences=24 if passed else 0,actual_API_unit_cases=8 if passed else 0,ordinary_host_pairs=146 if passed else 0,build_path=str(build/'build.json'),build_sha256=sha(build/'build.json'),execution_path=str(execution/'report.json'),execution_sha256=sha(execution/'report.json'),files=inputs,full_State3504_FX512_pages16_source1140=True,guest_TEB_LastError_written=False,volatile_native_x86_API_effects_claimed=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='files'}))
if __name__=='__main__':main(*sys.argv[1:])
