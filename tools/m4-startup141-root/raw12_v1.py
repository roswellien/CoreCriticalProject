"""Full live game SEH record joins against actual MFC checkpoints; no AFTER seed."""
import struct,re
LOW=0x20001000;HIGH=LOW+4096

def need(v,m):
 if not v:raise ValueError(m)
def rows(raw,fmt):
 n=struct.calcsize(fmt);need(len(raw)%n==0,"Exact typed extent");return list(struct.iter_unpack(fmt,raw))
def prove(seed,fsbase,access,events,calls,points,root):
 need(len(seed)==4096 and len(points)==2*len(calls),"Own BEFORE whole stack and exact two checkpoints per actual CALL")
 shadow=bytearray(seed);frames=[];head=events[0][3] if events else None;ei=ci=joins=0
 def raw12(frame):
  need(LOW<=frame and frame+12<=HIGH,"Full source record on own stack");return bytes(shadow[frame-LOW:frame-LOW+12])
 for pc,address,value,width,write in access:
  need(width in(1,2,4)and write in(0,1),"Finite source access")
  if address==fsbase:
   need(ei<len(events),"Every source FS operand has actual typed event");e=events[ei];ei+=1
   need(e[:5]==(root,pc,write,head,value) and e[8:]==(0,0,0,0),"Exact current source/FS event join")
   if not write:need(e[5]==0 and value==head,"Exact FS read")
   elif e[5]==1:
    record=raw12(value);need(struct.unpack_from("<I",record)[0]==head,"Whole new source record predecessor");frames.append((value,head,e[7]));head=value
   else:
    need(e[5]==2 and frames,"Only exact LIFO source restore");frame,previous,invocation=frames.pop();need(head==frame and value==previous and struct.unpack_from("<I",raw12(frame))[0]==previous and e[7]>=invocation,"Whole source record and same predecessor restored");head=value
   need(e[6]==len(frames),"Exact source FS depth")
  if write and LOW<=address and address+width<=HIGH:
   shadow[address-LOW:address-LOW+width]=value.to_bytes(width,"little")
   for frame,previous,_ in frames:need(struct.unpack_from("<I",raw12(frame))[0]==previous,"No intervening corruption of live predecessor")
  if ci<len(calls) and (pc,address,value,width,write)==(calls[ci][1],calls[ci][3],calls[ci][4],4,1):
   call=calls[ci];need(call[0]==root and call[4]==call[1]+5,"Actual direct owning source CALL")
   for side in range(2):
    cpu,page=points[ci*2+side];need(len(cpu)==40 and len(page)==4096,"Whole actual checkpoint CPU and full stack")
    c=struct.unpack("<10I",cpu);need(c[4]==call[3]+4*side and c[9]==(call[2]if side==0 else call[4]),"Exact owning MFC entry/return CPU")
    need(struct.unpack_from("<I",page,call[3]-LOW)[0]==call[4],"Full actual source CALL return word")
    for frame,_,_ in frames:
     need(page[frame-LOW:frame-LOW+12]==raw12(frame),"All twelve bytes of every live source record at actual MFC boundary");joins+=1
   ci+=1
 need(ci==len(calls) and ei==len(events) and not frames and joins>0,"All CALL/checkpoint/FS facts consumed and complete source scopes balanced")
 return dict(actual_MFC_checkpoints=len(points),live_frame_raw12_comparisons=joins,source_FS_events=len(events))
def validate(data,seq,selected):
 prefix=f"sequence-{seq}/";base=prefix+"selected/";names=[]
 for key in data.entries:
  m=re.fullmatch(re.escape(base)+r"registry-checkpoint-(\d+)-name.bin",key)
  if m:
   value=data.data(key)
   if value in(b"constructor-mfc-before",b"constructor-mfc-after"):names.append((int(m[1]),value))
 names.sort();need(len(names)==16 and [v for _,v in names]==[v for _ in range(8)for v in(b"constructor-mfc-before",b"constructor-mfc-after")],"Exact eight real MFC calls with strict alternating checkpoints")
 points=[]
 for index,_ in names:
  point=base+f"registry-checkpoint-{index}";points.append((data.data(point+"-cpu.bin"),data.data(point+f"-page-{LOW}.bin")))
 cursor=0;out=[]
 for root in(0x4103f0,0x410440,0x459b40):
  stem=prefix+f"Constructors/root-{root}/";before={part:data.data(stem+"before/"+part+".bin")for part in("accesses","calls","FS-events")};after={part:data.data(stem+"after/"+part+".bin")for part in before}
  for part in before:need(after[part].startswith(before[part]),"Exact unchanged cumulative constructor prefix")
  access=rows(after["accesses"][len(before["accesses"]):],"<IIQII");events=rows(after["FS-events"][len(before["FS-events"]):],"<12I");calls=rows(after["calls"][len(before["calls"]):],"<12I")
  phase=next(i for i,v in enumerate(selected)if v["entry"]==root);native=data.data(prefix+f"phase-{phase}.bin");state=data.data(stem+"before/State.bin");need(len(native)==159716 and len(state)==3504,"Own actual constructor BEFORE")
  fsbase=struct.unpack_from("<I",state,2168)[0];seed=native[43236:47332];result=prove(seed,fsbase,access,events,calls,points[cursor:cursor+2*len(calls)],root);cursor+=2*len(calls);out.append(dict(root=root,**result))
 need(cursor==16,"All constructor checkpoints consumed exactly once");return out
