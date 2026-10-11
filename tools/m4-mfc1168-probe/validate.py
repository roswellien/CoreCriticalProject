"""Bounded genuine observations and persistent literal cached-path replay.

All source memory starts at genuine BEFORE. Only four measured Win32 volatile
responses enter external calls. Source instructions and backing writes are
derived, never copied from trace AFTER. No native or initializer credit.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact physical '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def raw(p):return pin(p).read_bytes()
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def load(p,tag):s=importlib.util.spec_from_file_location(tag,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def eq(a,b,label):need(a==b,label+' '+str((a,b))[:500])
def cpu_context(b):return tuple(u(b,o)[0]for o in(176,172,168,164,196,180,160,156,192,184))
def clean_cpu(c):c=list(c);c[8]&=~0x10100;return tuple(c)
def main(execution,h,name):
 out=B/name;need(not out.exists(),'Fresh bounded validation');out.mkdir();passed=False;counts=collections.Counter();observations=[];source_result={}
 try:
  e=read(execution,h);need(e['passed'],'Both genuine modes passed');b=read(e['build'],e['build_sha256']);need(b['passed'],'Actual compiled x86 worker');pin(b['worker'],b['worker_sha256']);prep=read(Path(b['preparation'])/'report.json',b['preparation_sha256'])
  for p,h0 in prep['files'].items():pin(p,h0)
  root=Path(execution).parent;contract=read(Path(b['preparation'])/'instruction-contracts.json');need(not contract['descriptor_gaps'],'Complete descriptor extent');rows={x['pc']:x for x in contract['instructions']};imports=read(Path(b['preparation'])/'api-imports.json')
  for mode in('normal','trace'):
   p=root/mode;eq(raw(p/'COMPLETE.txt'),b'complete','Complete fresh writer');endpoint=u(raw(p/'endpoint.bin'),0,8);need(endpoint[:2]==(0,0)and endpoint[3:7]==(0x7365a4,0x20008004,0x410a80,0x20008000),'Normal root returns fixed game object and exact frame')
   before=u(raw(p/'BEFORE/domain/domain.bin'),0,10);after=u(raw(p/'AFTER/domain/domain.bin'),0,10);eq(before,after,'Actual current-thread/manager/TLS/global identity carried');need(before[2]==0x5f4cb008 and before[3]==1 and before[5]==3 and before[6]==before[0]+0xe1c and before[7]and before[4],'Actual manager/TLS slot/cache inputs')
   capacities={};owner_inputs=[]
   for stem in('manager-array','thread','thread-array','thread-object','global-object'):
    meta=u(raw(p/f'BEFORE/domain/{stem}/meta.bin'),0,8);post=u(raw(p/f'AFTER/domain/{stem}/meta.bin'),0,8);eq(meta,post,'Whole actual live backing identity '+stem);need(meta[7]==1 and meta[6]>0,'Actual positive GlobalSize/LocalSize backing extent');initial=raw(p/f'BEFORE/domain/{stem}/bytes.bin');final=raw(p/f'AFTER/domain/{stem}/bytes.bin');eq(len(initial),meta[6],'Complete initial backing');goal=bytearray(initial)
    if stem=='global-object':need(meta[0]==before[4]and meta[6]==0x1090,'Exact cached result/4240B extent');goal[0x14]=0;struct.pack_into('<I',goal,0x1040,0x421)
    eq(bytes(goal),final,'Literal whole backing including untouched tails '+stem);owner_inputs.append(dict(role=stem,pointer=meta[0],extent=meta[6],initial_hex=initial.hex(),source_final_hex=bytes(goal).hex()));capacities[stem]=meta[6];counts['complete_actual_backing_byteflows']+=1
   thread=bytes.fromhex(next(x['initial_hex']for x in owner_inputs if x['role']=='thread'));array=bytes.fromhex(next(x['initial_hex']for x in owner_inputs if x['role']=='thread-array'));obj=bytes.fromhex(next(x['initial_hex']for x in owner_inputs if x['role']=='thread-object'));eq(u(thread,8,2),(3,next(x['pointer']for x in owner_inputs if x['role']=='thread-array')),'Current-thread count/array exact');eq(u(array,4)[0],next(x['pointer']for x in owner_inputs if x['role']=='thread-object'),'Slot1 actual thread object');eq(u(obj,4)[0],0,'Actual thread object+4 isNULL before1168')
   for module in('MFC','CRT'):
    meta=raw(p/f'BEFORE/{module}/metadata.bin');eq(meta,raw(p/f'AFTER/{module}/metadata.bin'),'Whole loaded module page geometry')
    for page,protect,type_,owner in struct.iter_unpack('<4I',meta):need(type_==0x1000000 and owner in(0x5f400000,0x78000000),'Actual loaded MEM_IMAGE pages');eq(raw(p/f'BEFORE/{module}/{page}.bin'),raw(p/f'AFTER/{module}/{page}.bin'),'Full loaded page restore/carry');counts['whole_loaded_module_page_endpoint_pairs']+=1
   eq(raw(p/'BEFORE/game/7561216.bin'),raw(p/'AFTER/game/7561216.bin'),'Fixed game object whole page unchanged')
   eq(raw(p/'ENV-before.bin'),raw(p/'ENV-after.bin'),'Whole rootENV28 preserved');eq(raw(p/'FX-before.bin'),raw(p/'FX-after.bin'),'Whole rootFX512 preserved');eq(raw(p/'host-ENV-before.bin'),raw(p/'host-ENV-after.bin'),'Whole hostENV28 restored')
   observations.append(dict(mode=mode,endpoint=endpoint,domain=before,backings=owner_inputs,capacities=capacities,no_1168_preinvoke=True,no_TLS_or_locale_seed=True,cached_thread_path=True,cached_global_fallback=True,new_allocations=0,new_callbacks=0))
  p=root/'normal';data=raw(p/'boundaries/records.bin');need(len(data)==7*664,'Seven complete raw boundaries');boundaries=[]
  expected=(0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca);normal_ptr=observations[0]['domain'][4]
  for i,pc in enumerate(expected):
   x=data[i*664:(i+1)*664];c=u(x,0,10);eq(c[9],pc,'Exact source boundary PC');eq(x[40:552],raw(p/'FX-before.bin'),'Complete actual boundaryFX512');eq(x[552:580],raw(p/'ENV-before.bin'),'Complete actual boundaryENV28');counts['normal_full_CPU_FX_ENV_frame_boundaries']+=1
   if i in(1,2,3,4):eq(c[0],normal_ptr,'Actual result distinct from fixed game object');eq(u(x,656,2),(normal_ptr,0x1090),'Whole returned provider extent')
   if i==0:eq(u(x,580,4),(0x5ae3ad,0x5ae3e0,0,0x421),'MFC1168 actual entered source frame')
   if i==5:eq(u(x,580,2),(0x5ae3ca,0xfffffffd),'True cdecl _setmbcp signed−3 frame')
   boundaries.append(dict(index=i,CPU=c,FX512_hex=x[40:552].hex(),ENV28_hex=x[552:580].hex(),frame64_hex=x[580:644].hex(),metadata=u(x,644,5)))
  a=raw(p/'named-API/records.bin');need(len(a)==8*668,'Eight actual named API raw sides');named=[];names=('TlsGetValue','EnterCriticalSection','GetACP','LeaveCriticalSection');targets=u(raw(p/'named-API/targets.bin'),0,4)
  for i in range(4):
   x=a[2*i*668:(2*i+1)*668];z=a[(2*i+1)*668:(2*i+2)*668];c=u(x,0,10);d=u(z,0,10);argc=0 if i==2 else 1;eq(u(x,644,3),(i,0,argc),'API entry kind/phase/count');eq(u(z,644,3),(i,1,argc),'API return kind/phase/count');eq(c[9],targets[i],'True named API target');eq(d[9],u(x,580)[0],'Actual source return joins original saved word');eq(d[4],c[4]+4*(argc+1),'Actual stdcall cleanup');eq(tuple(d[k]for k in(3,5,6,7)),tuple(c[k]for k in(3,5,6,7)),'Actual nonvolatile API registers preserved');eq(x[40:580],z[40:580],'Whole actual API FX512/ENV28 preserved');counts['normal_named_full_API_pairs']+=1
   if i==0:eq(u(x,584)[0],3,'Actual TlsGetValue index3');eq(d[0],observations[0]['domain'][7],'Actual API TLS result joins untouched raw TEB slot')
   if i==2:eq(d[0],1252,'Actual GetACP response1252')
   named.append(dict(API=names[i],target=targets[i],CPU_before=c,CPU_after=d,FX512_before_hex=x[40:552].hex(),FX512_after_hex=z[40:552].hex(),ENV28_before_hex=x[552:580].hex(),ENV28_after_hex=z[552:580].hex(),frame64_hex=x[580:644].hex(),return_frame64_hex=z[580:644].hex(),meta_before=u(x,644,6),meta_after=u(z,644,6),module_path=raw(p/f'named-API/{i}-path.txt').decode(),module_sha256=raw(p/f'named-API/{i}-sha256.txt').decode(),entry64_hex=raw(p/f'named-API/{i}-entry64.bin').hex()))
  # Fresh trace source and every mutable input are separate from the normal process.
  p=root/'trace';schema=u(raw(p/'trace/schema.bin'),0,6);eq(schema,(1768,1600,44,716,142,4),'Measured exact cached domain geometry');events=raw(p/'trace/events.bin');api=raw(p/'trace/APIs.bin');facts=[];api_facts=[]
  for i in range(142):
   x=events[i*1768:(i+1)*1768];head=u(x,0,8);need(head[0]==i and head[1]in rows and head[3]==head[1]+1 and head[4]==rows[head[1]]['opcode']and head[5]==len(rows[head[1]]['cells']),'Exact physical source event/descriptor');facts.append(dict(index=i,PC=head[1],next_PC=head[2],before=clean_cpu(cpu_context(x[32:748])),after=clean_cpu(cpu_context(x[748:1464])),FX_before=x[236:748],FX_after=x[952:1464],cells=[u(x,1464+j*44,11)for j in range(head[5])],raw_before_hex=x[32:748].hex(),raw_after_hex=x[748:1464].hex()));counts['actual_raw_CONTEXT_sides']+=2
  for i in range(4):
   x=api[i*1600:(i+1)*1600];head=u(x,0,10);need(head[0]==i and head[6]==1,'Actual complete API interval');v=imports[head[4]];eq(v['name'],names[i],'Measured exact four named API order');api_facts.append(dict(index=i,source_PC=head[1],target=head[2],return_PC=head[3],argc=head[5],API=v['name'],before=clean_cpu(cpu_context(x[40:756])),after=clean_cpu(cpu_context(x[756:1472])),frame64_hex=x[1472:1536].hex(),return_frame64_hex=x[1536:1600].hex(),metadata=head,FX_before=x[244:756],FX_after=x[960:1472]))
  I=load(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','probe_literal_integer');D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','probe_decode');F=load(R/'tools/m4-formatting-source/flag_domain.py','probe_flag_definedness')
  program={pc:D.instruction_contract(dict(pc=pc,width=r['width'],bytes_hex=r['bytes_hex'],mnemonic=r['mnemonic'],operands=r['operands']))for pc,r in rows.items()};memory={}
  for module in('MFC','CRT'):
   for page,protect,type_,owner in struct.iter_unpack('<4I',raw(p/f'BEFORE/{module}/metadata.bin')):memory[page]=bytearray(raw(p/f'BEFORE/{module}/{page}.bin'))
  for f in(p/'BEFORE/game-physical').glob('*.bin'):memory[int(f.stem)]=bytearray(raw(f))
  for page,protect,type_,owner in struct.iter_unpack('<4I',raw(p/'BEFORE/domain/TEB/metadata.bin')):memory[page]=bytearray(raw(p/f'BEFORE/domain/TEB/{page}.bin'))
  memory[0x20000000]=bytearray(raw(p/'stack-before.bin'))
  for o in observations[1]['backings']:memory[o['pointer']]=bytearray.fromhex(o['initial_hex'])
  lm=u(raw(p/'BEFORE/CRT-codepage-lock/meta.bin'),0,4);need(lm[0]==0x7803708c and lm[1]>0 and lm[2:]==(24,1),'Actual codepage lock25 borrowed input');memory[lm[1]]=bytearray(raw(p/'BEFORE/CRT-codepage-lock/bytes.bin'))
  first=u(raw(p/'CPU-before.bin'),0,10);state=bytearray(3504)
  for reg,v in zip(I.REG,first[:8]):struct.pack_into('<I',state,I.REG[reg],v)
  # Dict insertion order of REG is intentionally not CPU order; fill explicitly.
  for reg,v in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),first[:8]):struct.pack_into('<I',state,I.REG[reg],v)
  for flag,bit in F.BITS.items():state[I.FLAGS[flag]]=(first[8]>>bit)&1
  struct.pack_into('<I',state,2472,first[9]);struct.pack_into('<I',state,I.BASE['fs'],observations[1]['domain'][0]);initial_flags=first[8]
  class Literal(I.Machine):
   def cpu_now(self):
    flags=initial_flags
    for flag,bit in F.BITS.items():flags=(flags&~(1<<bit))|(int(bool(self.flag(flag)))<<bit)
    return tuple(self.reg(k)for k in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
   def step(self):
    if self.cursor==0x780014b4:
     need(self.call_stack and self.call_stack[-1][0]==0x5f40107d and self.call_stack[-1][2]==0x5f4010b5,'Exact imported EH special-return source identity');self.call_stack.pop()
    return super().step()
  m=Literal(state,raw(p/'FX-before.bin'),struct.pack('<10I',*first),memory,program=program,callbacks={});domain={};API_index=0;flag_rows=[]
  for fact in facts:
   pc=fact['PC'];eq(m.cursor,pc,'Literal rooted order');eq(F.project(m.cpu_now(),domain),F.project(fact['before'],domain),'Literal fullCPU before exact defined flags');eq(m.fx,fact['FX_before'],'Literal wholeFX before');eq(m.bytes(m.reg('esp'),64),bytes.fromhex(fact['raw_before_hex'])[0:0] if False else events[fact['index']*1768+1640:fact['index']*1768+1704],'Complete source stack64 before')
   before_access=len(m.accesses);next_domain=F.advance(m,program[pc],domain);m.step();domain=next_domain
   eq(F.project(m.cpu_now(),domain),F.project(fact['after'],domain),'Literal fullCPU after exact defined flags');eq(m.fx,fact['FX_after'],'Literal wholeFX after');counts['literal_full_CPU_FX_sides']+=2
   actual=[]
   for c in fact['cells']:
    address,width,rd,wr,seg,bvalid,aval,blo,bhi,alo,ahi=c;need(bvalid and aval,'Complete genuine operand pre/post readable')
    if rd:actual.append((pc,address,blo|(bhi<<32),width,0))
    if wr:actual.append((pc,address,alo|(ahi<<32),width,1))
   # The descriptor has read/write flags; separate source order may differ only
   # for two independent implicit cells, so compare the exact multiset.
   eq(sorted(m.accesses[before_access:]),sorted(actual),'Every actual operand agrees with carried literal source');counts['literal_actual_operand_relations']+=len(actual);flag_rows.append(dict(PC=pc,undefined_flags=dict(domain)))
   if m.cursor not in program and m.cursor!=0x410a80:
    need(API_index<len(api_facts),'Finite external named API frontier');a=api_facts[API_index];eq((m.cursor,pc),(a['target'],a['source_PC']),'Actual named API entered from literal instruction');eq(F.project(m.cpu_now(),domain),F.project(a['before'],domain),'Complete actual API entryCPU from literal source');eq(m.bytes(m.reg('esp'),64).hex(),a['frame64_hex'],'Whole API source frame derived');need(a['argc']==(0 if a['API']=='GetACP'else 1),'Finite exact API argument count');eq(tuple(a['before'][k]for k in(3,5,6,7)),tuple(a['after'][k]for k in(3,5,6,7)),'Actual API nonvolatile fields unchanged')
    if a['API']=='TlsGetValue':eq(u(bytes.fromhex(a['frame64_hex']),4)[0],3,'Actual literal TLS index');eq(a['after'][0],observations[1]['domain'][7],'TLS raw slot/result ownprocess join')
    elif a['API']=='GetACP':eq(a['after'][0],1252,'Measured finite ACP1252 input')
    else:eq(u(bytes.fromhex(a['frame64_hex']),4)[0],lm[1],'Borrowed lock25 exact API argument')
    m.api_return(pc,a['argc'],a['after'][0]);eq(m.reg('esp'),a['after'][4],'Literal actual API return cleanup');eq(m.cursor,a['return_PC'],'Exact saved source API return word');m.reg('ecx',a['after'][1]);m.reg('edx',a['after'][2])
    for flag,bit in F.BITS.items():m.flag(flag,(a['after'][8]>>bit)&1)
    domain={};eq(m.cpu_now(),a['after'],'Whole finite actual Win32 volatile response');eq(m.fx,a['FX_after'],'Whole actual API FX remains source input');API_index+=1;counts['literal_actual_API_frames']+=1
  eq(API_index,4,'Exactly four finite APIs');eq(m.cursor,0x410a80,'Literal root returned');eq(m.cpu_now(),u(raw(p/'CPU-after.bin'),0,10),'Entire source-derived root CPU40 endpoint')
  for o in observations[1]['backings']:eq(m.bytes(o['pointer'],o['extent']).hex(),o['source_final_hex'],'Entire independently source-derived provider backing')
  callbacks=(0x5f4053fe,0x5f40b293);need(not set(callbacks)&set(m.PCs),'Both lazy callbacks unentered');eq(len(m.PCs),142,'Exact recovered reached closure142');fs=[x for x in m.accesses if x[1]==observations[1]['domain'][0]and x[4]];eq(len(fs),2,'One exact FS install/restore pair');counts['literal_FS_writes']=2
  reached=[program[pc]for pc in sorted(set(m.PCs))];counts['literal_reached_instructions']=len(m.PCs);counts['literal_unique_PCs']=len(reached)
  source_result=dict(root=0x5ae3e4,PCs=m.PCs,accesses=m.accesses,API_relations=[{k:v for k,v in a.items()if not k.startswith('FX')}for a in api_facts],backings=observations[1]['backings'],CPU_after=m.cpu_now(),FS_source_writes=fs,call_stack_empty=not m.call_stack,no_AFTER_or_trace_post_state_seed=True,source_state_hex=bytes(m.state).hex())
  for filename,value in [('actual-domain-observations.json',observations),('actual-normal-boundaries.json',boundaries),('actual-named-API-boundaries.json',named),('source-derivations.json',source_result),('reached-instruction-contracts.json',dict(instructions=reached,flag_lifetimes=flag_rows)),('actual-trace-observations.json',[{k:(v.hex()if isinstance(v,bytes)else v)for k,v in f.items()}for f in facts])]:
   p0=out/filename;p0.write_text(json.dumps(value,indent=2)+'\n');pin(p0)
  pin(__file__);pin(sys.executable);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual cached current-thread/MFC global fallback domain, exact142-instruction rooted literal source replay, normal MFC/_setmbcp and four named API completeCPU-FX-ENV-frame joins; lazy callbacks/unobserved codepages remain uncredited',execution=str(execution),execution_sha256=h,counts=dict(counts),normal_cached_domain_only=True,native_executed=False,initializer_credit=0,source_AFTER_seed=False,source_callback_credit=0,capture_archive_reader_opened=False,all_bounded_readers_closed=True,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
