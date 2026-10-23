"""Pure missing named predicates; bounded raw facade and source imports external.

No directory enumeration or worker. ROOT wrapper must authenticate every a.data
dependency against its exact current strict receipt's scoped declarations.
"""
import struct,hashlib
def need(v,msg):
 if not v:raise ValueError(msg)
def eq(a,b,msg):need(a==b,msg)

def guest_CS24(a,mode,inputs,case):
 stem=f'control-{mode}/MFC/';address=inputs['guest_CS'];eq(address,0x33007000,'Exact current typed guest CS24 source role')
 rows=list(struct.iter_unpack('<2I',a.data(stem+'entry/memory-index.bin')))
 eq(len({p for p,n in rows}),len(rows),'Unique whole own-entry extent identities')
 owners=[(p,n)for p,n in rows if p<=address and address+24<=p+n];eq(owners,[(address,24)],'Exact separate opaque guestCS24 source backing')
 before=a.data(stem+f'entry/memory-{address}-24.bin');after=a.data(stem+'refused/guestCS24.bin');eq((len(before),len(after)),(24,24),'Both complete source opaque24 observations')
 access=list(struct.iter_unpack('<IIQII',a.data(stem+'refused/accesses.bin')));eq([list(r)for r in access],case['source_access_prefix'],'Exactly independently reviewed source causal operand chronology')
 committed=access[:-1]if mode==7 else access
 need(not any(w and p<address+24 and address<p+n for pc,p,v,n,w in committed),'Literal refused prefix makes no guestCS24 writes; no generic write mask')
 eq(before,after,'Whole opaque guestCS24 retained before refused source API transport')
 return dict(mode=mode,source_address=address,whole_bytes=24,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),whole_source_operands=len(access))

def TLS_frame64(a,mode,inputs,case,literal,contracts):
 eq(mode,11,'Exact named zero-argument source TLS refusal mode')
 stem='control-11/';prefix=stem+'MFC/'
 access=list(struct.iter_unpack('<IIQII',a.data(prefix+'refused/accesses.bin')));eq(len(access),17,'Complete literal zero TLS argument prefix')
 eq([list(r)for r in access],case['source_access_prefix'],'Sealed independent current source prefix')
 eq(access[-4],(0x5f401010,0x5f4cb008,0,4,0),'Actual current zero TLS-index source read')
 eq(access[-3],(0x5f401010,0x200017d8,0,4,1),'Literal actual zero source argument push')
 eq(access[-2][:2],(0x5f401012,0x5f498330),'Exact owning TLS IAT CALL operand')
 eq(access[-2][3:],(4,0),'Whole read IAT target')
 target=access[-2][2];need(target!=0,'Actual projected owning TLS service target; physical named owner closure remains retained strict proof')
 eq(access[-1],(0x5f401012,0x200017d4,0x5f401018,4,1),'Literal committed source return push')
 eq(a.data(prefix+'refused/APIs.bin'),b'','Typed argument denial precedes source API record')
 actual_cpu=struct.unpack('<10I',a.data(prefix+'refused/CPU.bin'));eq((actual_cpu[4],actual_cpu[9]),(0x200017d4,target),'Actual live refused source CALL CPU')
 frames=list(struct.iter_unpack('<4I',a.data(prefix+'refused/frames.bin')))
 eq(frames[-1],(target,actual_cpu[4],0x5f401018,0x5f401012),'Current true CALL frame target/source/return')
 need('Typed guest TLS index3/borrowed CS24 argument'in a.data(stem+'refusal.txt').decode(),'Actual precise typed source argument refusal')
 state=a.data(prefix+'entry/State.bin');fx=a.data(prefix+'entry/FX.bin');cpu=a.data(prefix+'entry/CPU.bin');eq((len(state),len(fx),len(cpu)),(3504,512,40),'Complete own BEFORE architecture inputs')
 memory={}
 for address,size in struct.iter_unpack('<2I',a.data(prefix+'entry/memory-index.bin')):
  need(address not in memory,'Own source input extent unique');memory[address]=a.data(prefix+f'entry/memory-{address}-{size}.bin');eq(len(memory[address]),size,'Whole own source input backing')
 own=a.data(prefix+'entry/Native.bin');eq(len(own),159716,'Whole admitted current own root BEFORE')
 eq(own[36:76],cpu,'Own BEFORE CPU cut');eq(own[141540:145044],state,'Own BEFORE State cut')
 own_pages=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
 for i,address in enumerate(own_pages):
  data=own[2276+i*4096:2276+(i+1)*4096];eq(len(data),4096,'Whole own BEFORE source page')
  for base,b in memory.items():
   lo=max(base,address);hi=min(base+len(b),address+4096)
   if lo<hi:eq(b[lo-base:hi-base],data[lo-address:hi-address],'Source own BEFORE overlapping backing equality')
  if address not in memory:memory[address]=data
 program={r['pc']:r for r in contracts['instructions']};eq(len(program),142,'Exactly inherited physically reviewed original-MFC source body domain')
 c=struct.unpack('<10I',cpu);m=literal.Literal(state,fx,cpu,memory,program=program,callbacks={});m.inputs=inputs;m.initial_flags=c[8]
 m.call_stack.append((0x5ae3e4,c[4],0x410a80,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0))
 while len(m.accesses)<17:
  need(m.cursor in program and m.steps<128,'Exact bounded literal TLS CALL source frontier');m.step()
 eq(m.accesses,access,'Every actual TLS refusal operand independently predicted from own BEFORE')
 eq(tuple(m.cpu_now()),actual_cpu,'Whole refused CPU40 independently predicted, no AFTER CPU seed')
 page=a.data(stem+'retry-before/memory-536875008-4096.bin');eq(len(page),4096,'Whole actual refused source stack page')
 frame=actual_cpu[4];actual=page[frame-0x20001000:frame-0x20001000+64];eq(len(actual),64,'All64 actual refused source CALL bytes')
 eq(actual,m.bytes(frame,64),'All64 source CALL frame bytes independently predicted from own BEFORE')
 eq(struct.unpack_from('<2I',actual),(0x5f401018,0),'Exact return and zero TLS argument')
 return dict(mode=11,source_CALL_PC=0x5f401012,source_push_PC=0x5f401010,source_frame=frame,source_target=target,source_return=0x5f401018,whole_CPU_bytes=40,whole_frame_bytes=64,source_CPU_sha256=hashlib.sha256(struct.pack('<10I',*m.cpu_now())).hexdigest(),source_frame_sha256=hashlib.sha256(actual).hexdigest(),source_steps=m.steps,source_API_entered=False,AFTER_seed=False)
