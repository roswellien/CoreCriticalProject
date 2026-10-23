"""Exhaustive physical-index partition, with literal constructor12B proof."""
import struct
def need(v,s):
 if not v:raise ValueError(s)
def partition(a,stem,o,roots):
 frames=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')))
 records=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')))
 need(len(frames)==35 and len(records)==70,'All28 legacy plus7 constructor frames and all70 whole12B observations')
 new=[(i,f)for i,f in enumerate(frames)if f[2]in roots];old=[(i,f)for i,f in enumerate(frames)if f[2]not in roots]
 need(len(new)==7 and len(old)==28,'Exact source-root partition covers every physical frame')
 need(all(r[2]<len(frames)and r[3]==frames[r[2]][2]for r in records),'Every raw observation binds its actual whole physical frame/root')
 obs=o.constructor_FS_observations;need(len(obs)==21,'All21 independently computed literal constructor FS operands')
 stack=[];cursor=0;used=set();joins=[]
 for event in obs:
  if event['kind']==0:
   need(cursor<len(new),'Each genuine constructor FS read owns one physical frame');i,f=new[cursor];cursor+=1
   need(f[0]==1 and f[2]==event['root']and f[3]==event['group_entry']and f[5]==event['entry_ESP']and f[7]==event['PC']and f[8]==event['before_head']and f[10]==event['handler']and f[11]==0xffffffff and f[12]==len(stack)and f[13]==(stack[-1][0]+1 if stack else 0),'Whole source constructor frame/root/entry/handler/nesting joins genuine physical index')
   stack.append((i,f))
  else:
   need(stack,'Only live same-source constructor frame can install/restore');i,f=stack[-1];point=81 if event['kind']==1 else 84
   match=[(ri,r)for ri,r in enumerate(records)if r[2]==i and r[4]==point];need(len(match)==1,'Exactly one complete physical12B checkpoint per literal constructor scope write');ri,r=match[0]
   need(ri not in used and r[0]==1 and r[3]==event['root']and r[5]==event['PC']and r[6]==event['record_address']and r[7]==12,'Exact same constructor frame/address/PC/12B domain')
   need(struct.pack('<3I',*r[8:11]).hex()==event['record_hex'],'All12 actual constructor frame bytes equal persistent literal source pushes/stores')
   used.add(ri);joins.append(dict(physical_frame_index=i,physical_record_index=ri,root=event['root'],source_PC=event['PC'],bytes=12,source_hex=event['record_hex']))
   if event['kind']==2:stack.pop()
 need(not stack and cursor==7 and len(used)==14,'All seven constructor source frames and14 actual12B observations exhaustively proved')
 newids={i for i,_ in new};need(used=={i for i,r in enumerate(records)if r[2]in newids},'No extra/missing constructor raw observations masked by partition')
 mapping={i:n for n,(i,f)in enumerate(old)};oldframes=[]
 for i,f in old:
  row=list(f)
  if row[13]:need(row[13]-1 in mapping,'Legacy nesting reference points only to exact retained legacy source frame');row[13]=mapping[row[13]-1]+1
  oldframes.append(tuple(row))
 oldrecords=[]
 for ri,r in enumerate(records):
  if r[2]in mapping:
   row=list(r);row[2]=mapping[r[2]];oldrecords.append(tuple(row))
 need(len(oldrecords)==56 and len(used)+len(oldrecords)==len(records),'All70 records conserved; exact56 legacy observations remain')
 o.constructor_FS_partition=dict(physical_frames=35,physical_records=70,legacy_index_map=[dict(physical=i,legacy=n)for i,n in mapping.items()],constructor_source_joins=joins,whole_union_exhaustive=True,source_seed=False)
 return oldframes,oldrecords
