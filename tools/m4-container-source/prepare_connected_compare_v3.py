"""Observation-only normal FS and saved byte witnesses in persistent116 model."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'tools/m4-container-source/compare_connected.py';q=p.with_name('compare_connected_v3.py');assert not q.exists();s=p.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a[:70];s=s.replace(a,b)
one('counts=collections.Counter();rows=[]','counts=collections.Counter();rows=[];FS_rows=[];header_rows=[]')
one("order=json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order']","""order=json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order']
  FS_SPECS={0x4e78d7:(0,0x4e78d0,0x5b986b),0x4e78de:(1,0x4e78d0,0x5b986b),0x4e799f:(2,0x4e78d0,0x5b986b),0x48f297:(0,0x48f290,0x5b5233),0x48f29e:(1,0x48f290,0x5b5233),0x48f360:(2,0x48f290,0x5b5233),0x4d48f7:(0,0x4d48f0,0x5b8538),0x4d48fe:(1,0x4d48f0,0x5b8538),0x4d4948:(2,0x4d48f0,0x5b8538)}
  for f in json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/FS-frame-contracts.json').read_bytes()):
   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['helper_entry'],f['handler'])""")
one('machine,responses=B.bootstrap(before,facts,heap,material,G.Machine,program,callbacks,oldpc,oldsp)',"""fs_observations=[];current_root=[0]
     def observe_FS(model,address,value,size,pc,write):
      if address!=0x7ffde000 or pc not in FS_SPECS:return
      kind,group,handler=FS_SPECS[pc];need(size==4 and write==(kind!=0),'Exact normal literal source FS access');prior=int.from_bytes(model.bytes(address,4),'little');record=model.reg('esp')if kind==1 else prior;raw=model.bytes(record,12)if record!=0xffffffff else None;fs_observations.append(dict(level=level,sequence=seq,root=current_root[0],PC=pc,kind=kind,group_entry=group,handler=handler,source_call_frame=list(model.call_stack[-1])if kind==0 else None,before_head=prior,after_head=value if write else prior,entry_ESP=model.reg('esp')+8 if kind==0 else None,ESP=model.reg('esp'),record_address=record,record_hex=raw.hex()if raw is not None else None))
     class ObservedMachine(G.Machine):
      def read(self,address,size=4,domain='source',pc=None):
       v=super().read(address,size,domain,pc)
       if domain=='source':observe_FS(self,address,v,size,self.word(2472)if pc is None else pc,False)
       return v
      def write(self,address,value,size=4,domain='source',pc=None):
       if domain=='source':observe_FS(self,address,value,size,self.word(2472)if pc is None else pc,True)
       return super().write(address,value,size,domain,pc)
     machine,responses=B.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp)""")
one("entry=item['entry'];b=a.data(","entry=item['entry'];current_root[0]=entry;root_access_start=len(machine.accesses);b=a.data(")
old=(ROOT/'tools/m4-fs-source/compare_connected_v4.py').read_text();start=old.index('       if entry==0x4d4830:');end=old.index('       expected_callbacks.append',start);header=old[start:end]
one("G.complete_root(machine,api=responses);expected_callbacks.append",'G.complete_root(machine,api=responses)\n'+header+'       expected_callbacks.append')
one("counts['persistent116_sequences']+=1","""need(len(fs_observations)==42,'All42 normal game FS source accesses from one bootstrap BEFORE');fsframes=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')));rawrecords=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')));need(len(fsframes)==14 and len(rawrecords)==28,'Actual14 normal game frames and28 complete12B snapshots');stack=[];index=0
     for event in fs_observations:
      if event['kind']==0:
       f=fsframes[index];need(f[0]==1 and f[2]==event['root']and f[3]==event['group_entry']and f[5]==event['entry_ESP']and f[7]==event['PC']and f[8]==event['before_head']and f[10]==event['handler']and f[11]==0xffffffff and f[12]==len(stack)and f[13]==(stack[-1][1]+1 if stack else 0),'Exact normal native frame from literal source pushes/previous head/nested metadata');stack.append((f,index));index+=1
      else:
       f,fi=stack[-1];point=81 if event['kind']==1 else 84;found=[r for r in rawrecords if r[2]==fi and r[4]==point];need(len(found)==1,'One actual12B frame observation per reached source MOV');r=found[0];need(r[0]==1 and r[3]==event['root']and r[5]==event['PC']and r[6]==event['record_address']and r[7]==12,'Actual complete12B source address/PC/width');equal(struct.pack('<3I',*r[8:11]).hex(),event['record_hex'],'Entire actual native12B record from persistent literal BEFORE pushes/scope stores');counts['actual_native12B_source_relations']+=1
       if event['kind']==2:stack.pop()
      FS_rows.append(event);counts['native_FS_source_accesses']+=1
     need(not stack and index==14,'All normal nested game frames close');counts['persistent116_sequences']+=1""")
one("(out/'phases.json').write_text", "for filename,value in(('FS-source-derivations.json',FS_rows),('new-header-derivations.json',header_rows)):(out/filename).write_text(json.dumps(value,indent=2)+'\\n');pin(out/filename)\n  (out/'phases.json').write_text")
q.write_text(s)
