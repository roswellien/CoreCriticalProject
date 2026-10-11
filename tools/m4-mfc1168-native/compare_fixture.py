"""Independent literal replay from actual native BEFORE and four typed API seams.

All142 original instructions execute in the independent integer interpreter.
Actual native AFTER bytes are comparison targets only, never model inputs.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:550])
def pin(p,h=None):
 p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Exact input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable file');PINS[str(p)]=a;return p
def raw(p):return pin(p).read_bytes()
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def u(b,n=1,o=0):return struct.unpack_from('<'+'I'*n,b,o)
def main(execution,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh independent comparison');out.mkdir();passed=False;counts=collections.Counter();results=[]
 try:
  e=read(execution,digest);need(e['passed'],'Both actual native workers passed');b=read(e['build'],e['build_sha256']);need(b['passed'],'Actual compiled workers');prep=read(b['preparation'],b['preparation_sha256']);need(prep['passed'],'Exact BEFORE-only preparation')
  for p,h in b['files'].items():pin(p,h)
  for r in e['runs'].values():
   for p,h in r['outputs'].items():pin(p,h)
  contracts=read(Path(prep['native_contracts']).parent/'contracts.json');layout=read(Path(b['preparation']).parent/'before-layout.json')
  I=load(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','mfc_native_source_integer');D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','mfc_native_source_decoder');F=load(R/'tools/m4-formatting-source/flag_domain.py','mfc_native_source_flags')
  program={r['pc']:r for r in contracts['instructions']};need(len(program)==142,'Exact complete142 source rows')
  initial_input=raw(prep['input_pack']);cursor=12;input_blocks={}
  for _ in range(u(initial_input,o=8)[0]):
   address,size,permission=u(initial_input,3,cursor);cursor+=12;input_blocks[address]=initial_input[cursor:cursor+size];cursor+=size
  eq(cursor,len(initial_input),'Complete exact BEFORE-only pack');thread=contracts['thread_contract'];cs=next(x for x in layout if x['role']=='Borrowed initialized opaque guest CS24')['address']
  class Literal(I.Machine):
   def cpu_now(self):
    flags=self.initial_flags
    for flag,bit in F.BITS.items():flags=(flags&~(1<<bit))|(int(bool(self.flag(flag)))<<bit)
    return tuple(self.reg(k)for k in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
   def step(self):
    if self.cursor==0x780014b4:
     need(self.call_stack and self.call_stack[-1][0]==0x5f40107d and self.call_stack[-1][2]==0x5f4010b5,'Literal special EH imported return current source frame');self.call_stack.pop();outer=self.call_stack;self.call_stack=[]
     try:return super().step()
     finally:self.call_stack=outer
    return super().step()
  for level in('O0','O2'):
   p=Path(execution).parent/level;schema=u(raw(p/'schema.bin'),10);eq(schema,(24,352,113,4,3504,40,512,len(layout),1,1),'Actual exact native output geometry')
   before_state=raw(p/'before/State.bin');before_cpu=raw(p/'before/CPU.bin');before_fx=raw(p/'before/FX.bin');eq(len(before_state),3504,'Whole actual BEFORE State');eq(len(before_cpu),40,'Whole actual BEFORE CPU');eq(len(before_fx),512,'Whole actual BEFORE FX')
   memory={r['address']:bytearray(raw(p/f'before/blocks/{r["address"]}.bin'))for r in layout};entry=u(before_cpu,10);eq(entry[4:5],(0x20008000,),'Registered Runtime actual entry frame');eq(entry[9],0x5ae3e4,'Registered Runtime actual root')
   for a,source in input_blocks.items():
    goal=bytearray(source)
    if a==0x20000000:struct.pack_into('<I',goal,0x8000,0xfffffff0)
    eq(bytes(memory[a]),bytes(goal),'Entire genuine BEFORE input, with actual dispatcher return token only');counts['BEFORE_only_block_joins']+=1
   m=Literal(before_state,before_fx,before_cpu,memory,program=program,callbacks={});m.initial_flags=entry[8];m.call_stack.append((0x5ae3e4,entry[4],0xfffffff0,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0))
   api_raw=raw(p/'APIs.bin');need(len(api_raw)==4*352,'Four complete actual native typed API records');api_rows=[]
   for index in range(4):
    x=api_raw[index*352:(index+1)*352];words=struct.unpack_from('<16Q',x);a=u(x,10,128);z=u(x,10,168);api_rows.append(dict(words=words,before=a,after=z,frame64=x[208:272],CS_before=x[272:312],CS_after=x[312:352]))
   api_index=0;domain={};flags=[]
   while m.cursor!=0xfffffff0:
    need(m.cursor in program,'No cold/lazy frontier admitted');row=program[m.cursor];eq(m.bytes(row['pc'],row['width']),bytes.fromhex(row['bytes_hex']),'Literal normal physical instruction source span');domain=F.advance(m,row,domain);m.step();flags.append(dict(PC=row['pc'],undefined_flags=dict(domain)))
    if m.cursor not in program and m.cursor!=0xfffffff0:
     need(api_index<4,'Finite actual external frontier');a=api_rows[api_index];spec=contracts['normal_APIs'][api_index];w=a['words'];result=next(x['guest']for x in contracts['borrowed_backings']if x['role']=='thread')if api_index==0 else 1252 if api_index==2 else 0
     eq(w[:8],(1,api_index,spec['source_PC'],spec['source_target'],spec['argc'],m.reg('esp'),spec['return_PC'],result),'Exact actual typed source API invocation')
     eq(m.cursor,spec['source_target'],'Literal source IAT target');eq(m.cpu_now(),a['before'],'Complete actual typed API guest entry CPU40');eq(m.bytes(m.reg('esp'),64),a['frame64'],'Complete literal source API cdecl/stdcall frame64');need(w[9]>0 and w[10]!=0xffffffff and w[11]>0,'Actual native current thread/TLS resource identity')
     if api_index==0:eq(w[8],w[11],'Actual native TlsGetValue raw returned own current association');eq(w[12],w[7],'Typed guest borrowed-thread result');eq(w[13],0,'TLS leaves native CS unheld')
     if api_index==2:eq(w[8],1252,'Actual native GetACP1252 result')
     # Host CS40 layout is DebugInfo64/LockCount32/Recursion32/Owner64/...
     before_depth=struct.unpack_from('<I',a['CS_before'],12)[0];after_depth=struct.unpack_from('<I',a['CS_after'],12)[0];owner_after=struct.unpack_from('<Q',a['CS_after'],16)[0]
     eq((before_depth,after_depth),((0,1)if api_index==1 else(1,0)if api_index==3 else(0,0)if api_index==0 else(1,1)),'Actual native40 current recursion phase');eq(owner_after,w[9]if after_depth else 0,'Actual native40 owner/current-host-thread relation')
     transports=[]
     if api_index in(1,3):
      depth=1 if api_index==1 else 0;values=(0xfffffffe if depth else 0xffffffff,depth,thread['current_process_thread']if depth else 0);transports=[(cs+4+4*i,struct.pack('<I',value))for i,value in enumerate(values)]
     # Guest EAX represents the typed result; all other volatile guest inputs
     # are intentionally retained. Native response data is explicit seam only.
     m.api_return(spec['source_PC'],spec['argc'],w[7],transports);domain={};eq(m.cpu_now(),a['after'],'Complete source-derived explicit typed guest API return CPU40');api_index+=1;counts['complete_typed_API_CPU_frame_joins']+=1
   eq(api_index,4,'Exactly four actual APIs');eq(len(m.PCs),142,'Exact rooted source142');eq(m.PCs,read(R/'reports/m4-mfc1168-probe/validation-r6/source-derivations.json')['PCs'],'Same genuine normal rooted PC order');eq(bytes(m.state),raw(p/'after/State.bin'),'Entire source-derived3504 native State');eq(m.fx,raw(p/'after/FX.bin'),'Entire512 native FX retained');eq(struct.pack('<10I',*m.cpu_now()),raw(p/'after/CPU.bin'),'Entire source-derived native CPU40');counts['whole_State3504_CPU40_FX512_endpoint_joins']+=1
   for row in layout:address=row['address'];eq(m.bytes(address,row['size']),raw(p/f'after/blocks/{address}.bin'),'Every complete source-derived backing/page/stack/TEB endpoint');counts['whole_declared_memory_endpoint_joins']+=1
   access_raw=raw(p/'accesses.bin');actual=[(pc,address,value,width,writing)for pc,address,value,width,writing in struct.iter_unpack('<IIQII',access_raw)];eq(actual,m.accesses,'All113 actual ordered source operands/values');counts['ordered_literal_operand_joins']+=len(actual)
   eq(m.call_stack,[],'All literal source frames empty');fs=[r for r in m.accesses if r[1]==thread['source_TEB']and r[4]];eq(len(fs),2,'One source-defined imported EH install/restore');counts['source_FS_install_restore_rows']+=2
   lifecycle=struct.unpack('<8Q',raw(p/'lifecycle.bin'));eq(lifecycle,(1,api_rows[0]['words'][9],api_rows[0]['words'][10],4,0,1,1,1),'Actual TLS clear/free and native CS cleanup receipt')
   results.append(dict(level=level,root=0x5ae3e4,source_PCs=m.PCs,source_accesses=m.accesses,source_API_relations=[{k:(v.hex()if isinstance(v,bytes)else v)for k,v in r.items()}for r in api_rows],FS_source_writes=fs,borrowed_backings=[dict(role=x['role'],guest=x['guest'],extent=x['extent'],initial_hex=bytes(memory[x['guest']]).hex(),source_final_hex=m.bytes(x['guest'],x['extent']).hex())for x in contracts['borrowed_backings']],source_State_hex=bytes(m.state).hex(),source_CPU=m.cpu_now(),source_FX_hex=m.fx.hex(),call_stack_empty=True,no_AFTER_seed=True,flag_lifetimes=flags))
  path=out/'source-derivations.json';path.write_text(json.dumps(results,indent=2)+'\n');pin(path);pin(__file__);pin(sys.executable)
  for q,h in PINS.items():eq(sha(q),h,'Stable successful input read')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual one-registered-root O0/O2 literal MFC1168 cached-domain replay from own BEFORE; complete State/CPU/FX and declared284 memory extents, four typed native TLS/CS/GetACP seams',execution=str(execution),execution_sha256=digest,counts=dict(counts),files=PINS,source_AFTER_seed=False,initializer_credit=0,unobserved_callbacks_codepages_denied=True,capture_archive_reader_opened=False,all_bounded_readers_closed=True)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
