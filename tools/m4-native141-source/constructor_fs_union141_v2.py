"""Keep actual normal FS journal and constructor component journal separate.

No constructor rows are fabricated in the inherited normal-frame schema.
Constructor raw records are reconstructed only from committed native game
stack writes, whose whole component journal equals the literal source journal.
"""
import struct

def need(v,s):
 if not v:raise ValueError(s)

def partition(a,stem,o,roots):
 frames=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')))
 records=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')))
 need(len(frames)==28 and len(records)==56,'Exact inherited normal28 frames and56 whole12B observations')
 need(all(f[2]not in roots for f in frames),'Constructor component frames never fabricated as normal provider frames')
 need(all(r[2]<len(frames)and r[3]==frames[r[2]][2]for r in records),'Every inherited raw record binds actual normal frame/root')
 obs=o.constructor_FS_observations
 need(len(obs)==21 and [e['root']for e in obs]==[roots[0]]*9+[roots[1]]*9+[roots[2]]*3,'Exact21 source constructor events in physical root chronology')
 joins=[];serial=0;allrows=[]
 for root in roots:
  base=stem+'Constructors/root-'+str(root)+'/'
  prior=a.data(base+'before/accesses.bin');last=a.data(base+'after/accesses.bin')
  need(last.startswith(prior)and len(prior)%24==len(last)%24==0,'Whole append-only native component source-access prefix')
  accesses=list(struct.iter_unpack('<IIQII',last[len(prior):]))
  first=a.data(base+'before/FS-events.bin');lastfs=a.data(base+'after/FS-events.bin')
  need(lastfs.startswith(first)and len(first)%48==len(lastfs)%48==0,'Whole append-only native component FS prefix')
  actual=list(struct.iter_unpack('<12I',lastfs[len(first):]))
  events=[e for e in obs if e['root']==root];expected=[];stack=[];written={};cursor=0
  for event in events:
   kind=event['kind'];pc=event['PC'];value=event['before_head']if kind==0 else event['after_head']
   hits=[i for i in range(cursor,len(accesses))if accesses[i][0]==pc and accesses[i][2]==value and accesses[i][3:]==(4,0 if kind==0 else 1)]
   need(len(hits)==1,'Exactly one actual committed game FS operand for literal source event')
   index=hits[0]
   for apc,address,av,width,write in accesses[cursor:index+1]:
    if write:
     need(width in(1,2,4)and 0<=av<(1<<(8*width)),'Whole typed committed scalar source write')
     raw=av.to_bytes(width,'little')
     for offset,byte in enumerate(raw):written[address+offset]=byte
   cursor=index+1
   if kind==0:
    need(event['after_head']==event['before_head'],'Genuine source FS read preserves head')
    expected.append((root,pc,0,event['before_head'],event['after_head'],0,len(stack),serial,0,0,0,0))
    stack.append(dict(group=event['group_entry'],handler=event['handler'],previous=event['before_head'],frame=event['entry_ESP']-12,installed=False))
   else:
    need(stack,'Same-root source installation/restoration has genuine predecessor read');frame=stack[-1]
    need(frame['group']==event['group_entry']and frame['handler']==event['handler']and frame['frame']==event['record_address'],'Exact physical source scope/handler/frame ownership')
    address=event['record_address']
    need(all(address+i in written for i in range(12)),'All12 constructor record bytes derive from actual earlier committed source writes')
    raw=bytes(written[address+i]for i in range(12))
    need(raw.hex()==event['record_hex'],'Entire actual committed source-write record equals literal source12B; no AFTER seed')
    previous,handler,scope=struct.unpack('<3I',raw)
    need(previous==frame['previous']and handler==frame['handler'],'Exact source-owned predecessor and handler')
    if kind==1:
     need(not frame['installed']and scope==0xffffffff and event['before_head']==previous and event['after_head']==address,'Literal constructor frame installation and initial scope')
     frame['installed']=True;serial+=1;depth=len(stack)
    else:
     need(kind==2 and frame['installed']and scope==0 and event['before_head']==address and event['after_head']==previous,'Literal constructor restore uses source-written current scope and predecessor')
     stack.pop();depth=len(stack)
    expected.append((root,pc,1,event['before_head'],event['after_head'],kind,depth,serial,0,0,0,0))
    joins.append(dict(root=root,source_PC=pc,kind=kind,component_access_index=index,record_address=address,bytes=12,actual_committed_write_hex=raw.hex(),source_hex=event['record_hex']))
  need(not stack and actual==expected,'Exhaustive actual constructor FS-event delta equals source reads/install/restores/depth/serial')
  need(a.data(base+'after/FS-frames.bin')==b'','Actual constructor component FS scopes returned empty')
  allrows.extend(expected)
 need(serial==7 and len(joins)==14 and len(allrows)==21,'All7 constructor frames and14 source-owned12B install/restore records separately proved')
 o.constructor_FS_partition=dict(normal_physical_frames=28,normal_physical_records=56,constructor_component_frames=7,constructor_component_events=21,constructor_committed_source_records=14,constructor_source_joins=joins,normal_and_component_domains_separate=True,whole_union_exhaustive=True,source_seed=False)
 return frames,records
