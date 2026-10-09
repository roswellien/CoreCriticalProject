"""Author source observer: decoded MOV/CALL/RET/TEST and frozen author FDIV model.

No independent/root oracle is imported. Native execution inputs are original
BEFORE only; the real Windows BOOL is an observation with owner provenance.
"""
import hashlib,importlib.util,json,pathlib,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-data'
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000)
OFF=dict(zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi','eip'),(2216,2248,2264,2232,2312,2328,2280,2296,2472)))
AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
def sha(p):
 with pathlib.Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def put(b,o,v,n=4):b[o:o+n]=int(v).to_bytes(n,'little')
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def import_author(path):
 spec=importlib.util.spec_from_file_location('author_frozen_fdiv_replay',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def cpu(s):
 flags=int.from_bytes(s[2080:2088],'little')
 for o,bit in AF:flags=(flags&~(1<<bit))|((s[o]&1)<<bit)
 return [u(s,OFF[k])[0]for k in ('eax','ecx','edx','ebx','esp','ebp','esi','edi')]+[flags,u(s,2472)[0]]
def decode(pe,path,start,stop,out,label):
 tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
 cp=subprocess.run([str(tool),'-d','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={stop}',str(path)],capture_output=True)
 (out/(label+'.txt')).write_bytes(cp.stdout);(out/(label+'.stderr')).write_bytes(cp.stderr);assert cp.returncode==0
 program={}
 for line in cp.stdout.decode().splitlines():
  m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z]+)\s*(.*?)\s*$',line)
  if m:
   pc=int(m[1],16);code=bytes.fromhex(m[2]);assert pe.bytes(pc,len(code))==code
   ops=re.sub(r'\s*<[^>]*>','',m[4]).strip();program[pc]=(len(code),m[3],ops.split(', ')if ops else [])
 return program
def snapshot(row,name):return {p.name:p.read_bytes()for p in (row/name).iterdir()if p.is_file()}
class Entry:
 def __init__(self,before,program,provider):
  self.s=bytearray(before['state.bin']);self.r=dict(zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu(self.s)[:8]));self.flags=cpu(self.s)[8];self.pc=0x5ac3a0;self.program=program;self.provider=provider;self.mem={}
  for a in PAGES:self.mem[a]=bytearray(before[f'page-{a}.bin'])
  self.mem[0x78038ee8]=bytearray(before['crt-globals.bin']);self.mem[0x7ffde000]=bytearray(before['tib-0.bin'])
  self.events=[];self.routes=[dict(site=0xfffffff0,target=0x5ac3a0,return_pc=0xfffffff0,import_=False,completed=False)];self.data=[];self.visited=[];self.undefined=[]
 def cell(self,a,n):
  for base,b in self.mem.items():
   if base<=a and a+n<=base+len(b):return b,a-base
  raise AssertionError('Owned memory operand')
 def load(self,a,pc,event=True):
  b,o=self.cell(a,4);v=u(b,o)[0]
  if event:self.events.append((pc,a,v,4,0))
  return v
 def store(self,a,v,pc,event=True):
  b,o=self.cell(a,4);put(b,o,v&0xffffffff)
  if event:self.events.append((pc,a,v&0xffffffff,4,1))
 def address(self,op):
  expr=op[op.index('[')+1:op.index(']')].replace(' ','');total=0
  for term in re.findall(r'[+-]?[^+-]+',expr):
   sign=-1 if term.startswith('-')else 1;term=term.lstrip('+-');total+=sign*(self.r[term]if term in self.r else int(term,0))
  if 'fs:'in op:total+=0x7ffde000
  return total&0xffffffff
 def value(self,op,pc):
  if op in self.r:return self.r[op]
  if 'ptr'in op:return self.load(self.address(op),pc)
  return int(op,0)&0xffffffff
 def assign(self,op,v,pc):
  if op in self.r:self.r[op]=v&0xffffffff
  else:self.store(self.address(op),v,pc)
 def push(self,v,pc):self.r['esp']=(self.r['esp']-4)&0xffffffff;self.store(self.r['esp'],v,pc)
 def project(self,pc,flat=False):
  for k,o in OFF.items():put(self.s,o,pc if k=='eip'else self.r[k])
  for o,bit in AF:self.s[o]=(self.flags>>bit)&1
  if flat:put(self.s,2080,self.flags,8)
 def provider_call(self,start):
  pc=start
  for _ in range(3):
   size,op,args=self.provider[pc]
   if op=='mov':
    src=args[1];v=self.r[src]if src in self.r else self.load(self.address(src),pc,False)if 'ptr'in src else int(src,0)&0xffffffff
    if args[0]in self.r:self.r[args[0]]=v
    else:self.store(self.address(args[0]),v,pc,False)
   elif op=='ret':ret=self.load(self.r['esp'],pc,False);self.r['esp']+=4;return ret
   else:raise AssertionError('Original provider body opcode')
   pc+=size
  raise AssertionError('Provider return absent')
 def run(self):
  calls={0x5ac3cf:(0x5bb5a4,0x78004625),0x5ac3ec:(0x5bb57c,0x7800462f),0x5ac3fa:(0x5bb504,0x78004635)}
  for _ in range(64):
   size,op,args=self.program[self.pc];pc=self.pc;self.visited.append(pc);next_pc=pc+size
   if op=='push':self.push(self.value(args[0],pc),pc)
   elif op=='mov':
    if pc==0x5ac408:
     raw=self.load(0x5bb508,pc);v=0x78037c2c;value=self.load(v,pc,False);self.data.append((pc,0x5bb508,raw,v,value));self.r['eax']=v
    else:self.assign(args[0],self.value(args[1],pc),pc)
   elif op=='add':
    a=self.value(args[0],pc);b=self.value(args[1],pc);v=(a+b)&0xffffffff
    flags=int(a+b>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^b^v)&16))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^b)&(a^v))&0x80000000))<<11)
    self.flags=(self.flags&~0x8d5)|flags;self.assign(args[0],v,pc)
   elif op=='test':
    v=self.value(args[0],pc)&self.value(args[1],pc);self.flags=(self.flags&~0x8d5)|(int((v&255).bit_count()%2==0)<<2)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7);self.undefined.append(pc)
   elif op=='jne':
    if not self.flags&0x40:next_pc=int(args[0],0)
   elif op=='call':
    target=self.value(args[0],pc);self.push(next_pc,pc)
    if pc in calls:
     slot,provider=calls[pc];assert self.provider_call(provider)==next_pc;self.project(next_pc,True)
     self.routes.append(dict(site=pc,target=slot,return_pc=next_pc,import_=True,completed=True))
    elif pc==0x5ac415:
     assert target==0x5ac5c0 and self.program[target][1:] == ('ret',[])
     self.project(target,True);self.visited.append(target);assert self.load(self.r['esp'],target)==next_pc;self.r['esp']+=4;self.project(next_pc,True)
     self.routes.append(dict(site=pc,target=target,return_pc=next_pc,import_=False,completed=True))
    elif pc==0x5ac428:
     self.project(target);runtime_cpu=[self.r[k]for k in ('eax','ecx','edx','ebx','esp','ebp','esi','edi')]+[self.flags,pc];runtime_cpu[4]+=4
     return bytes(self.s),struct.pack('<10I',*runtime_cpu)
    else:raise AssertionError('Unreviewed actual source call')
   else:raise AssertionError('Unreviewed source opcode '+op)
   self.pc=next_pc
  raise AssertionError('Next required dependency absent')
def observe(row,program,providers,R,fd_program,pack,game,bindings,override=None):
 inp=(row/'input.bin').read_bytes();record=(row/'writer-record.bin').read_bytes();R.native(record,inp,fd_program,pack,game,bindings)
 writer=snapshot(row,'writer-after');before=snapshot(row,'entry-before-invoke');projected=snapshot(row,'entry-projected');after=snapshot(row,'entry-after-fault');retry=snapshot(row,'retry-after')
 if override:after.update(override)
 assert writer['state.bin']==record[3532:7036] and writer['fx.bin']==record[7548:8060]
 assert before['state.bin']==writer['state.bin'] and before['fx.bin']==writer['fx.bin']
 for n in before:
  if n not in ('runtime-cpu.bin',):assert before[n]==writer[n],n
 expected_runtime=cpu(writer['state.bin']);expected_runtime[4]=0x20001904;expected_runtime[9]=0xfffffff0
 assert before['runtime-cpu.bin']==struct.pack('<10I',*expected_runtime)
 projected_state=bytearray(writer['state.bin']);put(projected_state,2312,0x20001900);put(projected_state,2472,0x5ac3a0)
 assert projected['state.bin']==projected_state and projected['state-cpu.bin']==struct.pack('<10I',*cpu(projected_state))
 for n in projected:
  if n.startswith('page-')or n in('fx.bin','crt-globals.bin','entry-source.bin','tib-0.bin','tib-4.bin','tib-24.bin'):
   want=bytearray(before[n])
   if n=='page-536875008.bin':put(want,0x900,0xfffffff0)
   assert projected[n]==want,n
 model=Entry(projected,program,providers);state,runtime_cpu=model.run();assert after['state.bin']==state and after['runtime-cpu.bin']==runtime_cpu
 assert after['state-cpu.bin']==struct.pack('<10I',*cpu(state)) and after['fx.bin']==writer['fx.bin']
 for a in PAGES:assert after[f'page-{a}.bin']==model.mem[a],f'wholepage {a:x}'
 assert after['crt-globals.bin']==model.mem[0x78038ee8]and after['tib-0.bin']==model.mem[0x7ffde000]
 for n in('tib-4.bin','tib-24.bin','entry-source.bin'):assert after[n]==before[n]
 assert retry==after,'Entire failed prefix unchanged after poisoned retry'
 assert (row/'entry-events.bin').read_bytes()==b''.join(struct.pack('<5I',*x)for x in model.events)
 assert (row/'data-routes.bin').read_bytes()==b''.join(struct.pack('<5I',*x)for x in model.data)
 assert (row/'undefined-events.bin').read_bytes()==b''.join(struct.pack('<I',x)for x in model.undefined)==struct.pack('<I',0x5ac41f)
 routes=[{('import'if k=='import_'else k):v for k,v in x.items()}for x in model.routes];assert read(row/'calls.json')==routes
 result=read(row/'result.json');assert result['passed']and result['source_events']==34 and result['writer_events']==97 and result['fault_site']==0x5ac428 and result['fault_target']==0x5bb50c and result['poisoned_retry']and not result['whole_M4_complete']
 assert result['actual_query_BOOL']==model.data[0][4]==u(after['page-10096640.bin'],0x7e4)[0]
 return model
def host(row):
 for name in('writer','entry'):
  if not(row/(name+'-host-before.bin')).exists():continue
  a=(row/(name+'-host-before.bin')).read_bytes();b=(row/(name+'-host-after.bin')).read_bytes();assert len(a)==len(b)==544
  assert a[512:540]==b[512:540]and a[:5]==b[:5]and a[24:28]==b[24:28]
  for i in range(8):assert a[32+16*i:42+16*i]==b[32+16*i:42+16*i]
  assert a[256:416]==b[256:416]and any(a[256:416])
def main(build,runs,out):
 build=pathlib.Path(build).resolve();runs=[pathlib.Path(x).resolve()for x in runs];out=pathlib.Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
 files={};bindings={}
 try:
  receipt=read(build/'build.json');assert receipt['passed']
  for group in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
   for p,h in receipt[group].items():assert sha(p)==h,p;files[p]=h
  prior=ROOT/'tools/m4-crt-fdiv-replay/validate_replay.py';assert sha(prior)=='f63425ca77092c134a5a3387f3f98d9b9f09906a3e4b6bd1cc773d577a3399c5'
  R=import_author(prior);files[str(prior)]=sha(prior);files[str(ROOT/'tools/m4-crt-fdiv/validate_native.py')]=sha(ROOT/'tools/m4-crt-fdiv/validate_native.py')
  game=R.M.PE(ROOT/'MW3/Mech3.exe');provider=R.M.PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');pack=(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin').read_bytes()
  program=decode(game,game.path,0x5ac3a0,0x5ac42e,out,'game');program.update(decode(game,game.path,0x5ac5c0,0x5ac5c1,out,'leaf'));providers=decode(provider,provider.path,0x78004625,0x7800463b,out,'provider')
  recovery=read(ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json');fd_program={i['address']:i for g in recovery['complete_graphs']for i in g['instructions']}
  for i in fd_program.values():assert provider.bytes(i['address'],i['size']).hex()==i['bytes_hex']
  positives=controls=corruptions=0;allpcs=set();rows=[]
  for level,run in zip(('O0','O2'),runs):
   assert (run/'COMPLETE').read_bytes()==b'COMPLETE'
   for i in range(36):
    row=run/f'row-{i}';result=read(row/'result.json');assert result['passed']and result['scenario']==i and result['control']==(0 if i<24 else i-23)
    host(row)
    if i<24:
     model=observe(row,program,providers,R,fd_program,pack,game,bindings);positives+=1;allpcs.update(model.visited)
     # Independent checker invocation sees causal changes in complete raw inputs/results.
     for name,offset in(('state.bin',3400),('state.bin',2768),('fx.bin',24),('page-2013491200.bin',0xc2c),('page-10096640.bin',0x7e4),('page-536875008.bin',0x880),('tib-0.bin',0)):
      altered=snapshot(row,'entry-after-fault');b=bytearray(altered[name]);b[offset]^=1;altered[name]=bytes(b)
      # Exact full model comparison used above, not an execution input.
      try:observe(row,program,providers,R,fd_program,pack,game,{},altered)
      except (AssertionError,ValueError):corruptions+=1
      else:raise AssertionError('Corruption escaped complete source model')
    else:
     controls+=1;assert result['poisoned_retry']
     stage='writer-after'if i<27 else'entry-after-fault';assert snapshot(row,'retry-after')==snapshot(row,stage)
     if i<27:assert not result['writer_complete']and not result['entry_executed']
     else:assert result['writer_complete']and result['entry_executed']and(result['fault_site'],result['fault_target'])!=(0x5ac428,0x5bb50c)
    for p in row.rglob('*'):
     if p.is_file():files[str(p)]=sha(p)
   files[str(run/'COMPLETE')]=sha(run/'COMPLETE');rows.append(dict(level=level,positive=24,causal_denials=12,source_events=816,writer_events=2328,State_bytes=3504,complete_pages=11,NT_TIB_fields=[4,8,4]))
  report=dict(passed=True,scope='Author decoded source and actual Windows result model; root independent review required',rows=rows,positive_records=positives,causal_denials=controls,
   corruption_comparisons=corruptions,source_PCs=sorted(allpcs),next_PC=0x5ac428,next_IAT=0x5bb50c,root_oracle_imported=False,
   declared_undefined_AF='0 only at5AC41F, no architectural equality credit',State_reseed_after_writer=False,original_entry_executed=False,full_CRT=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p in out.iterdir():
   if p.is_file():files[str(p)]=sha(p)
  files[str(pathlib.Path(__file__).resolve())]=sha(__file__);files.update(bindings);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1],sys.argv[2:4],sys.argv[4])
