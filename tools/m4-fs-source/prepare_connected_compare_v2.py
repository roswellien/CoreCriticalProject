"""Add source-only FS trace and whole ten-owner endpoint joins to109 scaffold."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];t=(ROOT/'tools/m4-fs-source/compare_connected.py').read_text()
def change(a,b):
 global t
 assert t.count(a)==1,a
 t=t.replace(a,b)
change("counts=collections.Counter();rows=[]","counts=collections.Counter();rows=[];FS_rows=[];owner_rows=[];header_rows=[]")
change("for level in ('O0','O2'):","""fsbindings=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes())
  FS_SPECS={0x4e78d7:(0,0x4e78d0,0x5b986b),0x4e78de:(1,0x4e78d0,0x5b986b),0x4e799f:(2,0x4e78d0,0x5b986b),0x48f297:(0,0x48f290,0x5b5233),0x48f29e:(1,0x48f290,0x5b5233),0x48f360:(2,0x48f290,0x5b5233),0x4d48f7:(0,0x4d48f0,0x5b8538),0x4d48fe:(1,0x4d48f0,0x5b8538),0x4d4948:(2,0x4d48f0,0x5b8538)}
  for level in ('O0','O2'):""")
change("machine,responses=B.bootstrap(before,facts,heap,material,G.Machine,program,callbacks,oldpc,oldsp)","""fs_observations=[];current_root=[0]
     def observe_FS(model,address,value,size,pc,write):
      if address!=0x7ffde000 or pc not in FS_SPECS:return
      kind,group,handler=FS_SPECS[pc];need(size==4 and write==(kind!=0),'Exact literal source normal FS access')
      prior=int.from_bytes(model.bytes(address,4),'little');record=model.reg('esp')if kind==1 else prior
      raw=model.bytes(record,12)if record!=0xffffffff else None
      fs_observations.append(dict(level=level,sequence=seq,root=current_root[0],PC=pc,kind=kind,group_entry=group,handler=handler,before_head=prior,after_head=value if write else prior,entry_ESP=model.reg('esp')+8 if kind==0 else None,ESP=model.reg('esp'),record_address=record,record_hex=raw.hex()if raw is not None else None))
     class ObservedGame(G.Machine):
      def read(self,address,size=4,domain='source',pc=None):
       v=super().read(address,size,domain,pc);observe_FS(self,address,v,size,self.word(2472)if pc is None else pc,False);return v
      def write(self,address,value,size=4,domain='source',pc=None):
       observe_FS(self,address,value,size,self.word(2472)if pc is None else pc,True);return super().write(address,value,size,domain,pc)
     machine,responses=B.bootstrap(before,facts,heap,material,ObservedGame,program,callbacks,oldpc,oldsp)""")
change("entry=item['entry'];b=a.data", "entry=item['entry'];current_root[0]=entry;root_access_start=len(machine.accesses);b=a.data")
change("G.complete_root(machine,api=responses);expected_callbacks.append", """G.complete_root(machine,api=responses)
       if entry==0x4d4830:
        local=machine.accesses[root_access_start:];writes=[(i,v)for i,v in enumerate(local)if v[0]==0x4d4922 and v[1]==0x60b51c and v[3:]==(1,1)];need(len(writes)==1,'One literal new FS header source write');wi,write=writes[0];reads=[(i,v)for i,v in enumerate(local[:wi])if v[0]==0x4d4914 and v[3:]==(1,0)];need(len(reads)==1,'Exact literal local byte read');ri,read=reads[0];need(write[2]==read[2],'Literal AL copy to static header');stores=[(i,v)for i,v in enumerate(local[:ri])if v[4]and v[1]<=read[1]<v[1]+v[3]]
        if stores:
         si,store=stores[-1];need((store[2]>>(8*(read[1]-store[1])))&255==read[2],'Exact last source store byte provenance');provenance=dict(kind='dominating_source_store',index=si,pc=store[0],address=store[1],value=store[2],width=store[3])
        else:
         offset=PAGES.index(0x20001000)*4096+read[1]-0x20001000;need(before_pages[offset]==read[2],'Actual carried literal branch BEFORE stack byte provenance');provenance=dict(kind='carried_source_BEFORE_stack_byte',address=read[1],value=before_pages[offset],no_root_source_store_before_read=True)
        header_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,field=0x60b51c,write_pc=write[0],value=write[2],read_pc=read[0],read_address=read[1],branch_BEFORE_cpu=list(cpu),provenance=provenance))
       expected_callbacks.append""")
change("need(len(expected_callbacks)==81,'All81 actual callback registrations carried');counts['persistent109_sequences']+=1", """need(len(expected_callbacks)==81,'All81 actual callback registrations carried')
     need(len(fs_observations)==21,'All21 literal normal FS accesses derived from one bootstrap BEFORE')
     fsframes=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')));rawrecords=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')));need(len(fsframes)==7 and len(rawrecords)==14,'Exact seven actual native frame records and fourteen12B snapshots')
     model_stack=[];frame_index=0
     for event in fs_observations:
      if event['kind']==0:
       f=fsframes[frame_index];need(f[:4]==(1,frame_index,event['root'],event['group_entry'])and f[5]==event['entry_ESP']and f[7]==event['PC']and f[8]==event['before_head']and f[9]==f[5]-12 and f[10]==event['handler']and f[11]==0xffffffff,'Actual native CALL/record literal source relation');need(f[12]==len(model_stack)and f[13]==(model_stack[-1][1]+1 if model_stack else 0),'Actual nested frame parent and depth');need(f[15]==f[19]==f[21]==1 and f[17]==f[8]==f[22]and f[24:26]==(0x7ffde000,0xffffffff),'All normal frame installs/saved-load/restores/RET with explicit runtime sentinel');model_stack.append((f,frame_index));frame_index+=1
      else:
       f,fi=model_stack[-1];point=81 if event['kind']==1 else 84;records=[r for r in rawrecords if r[2]==fi and r[4]==point];need(len(records)==1,'One actual whole12B observation at exact source point');r=records[0];need(r[0]==1 and r[3]==event['root']and r[5]==event['PC']and r[6]==event['record_address']and r[7]==12,'Actual native12B source PC/address/width');equal(struct.pack('<3I',*r[8:11]).hex(),event['record_hex'],'All twelve native installed/restored bytes computed solely from source BEFORE');counts['actual_native12B_source_relations']+=1
       if event['kind']==2:model_stack.pop()
      FS_rows.append(event);counts['native_FS_source_accesses']+=1
     need(not model_stack,'Every source normal nested frame closes')
     mfc_records=list(struct.iter_unpack('<32Q',a.data(stem+'mfc-allocation-witnesses.bin')));need(len(mfc_records)==45,'Actual native45 MFC owners')
     for fi,binding in enumerate(fsbindings):
      records=[r for r in mfc_records if r[2]==binding['root']and r[4]==binding['CALL_pc']];need(len(records)==1,'Unique actual source owner/root/CALL');r=records[0];owned=next(v for v in responses.allocations if v['generation']==r[18]);need(owned['guest']==r[16]and owned['native']==r[17]and owned['requested']==binding['requested_size']and owned['live'],'Genuine native API allocation and literal MFC source owner joined');initial=a.data(stem+f'locale-allocation-{r[18]}-initial.bin');equal(initial,owned['initial'],'Exact original native API BEFORE backing');expected=a.data(stem+f'locale-allocation-{r[18]}-expected.bin');equal(machine.bytes(r[16],4096),expected,'Whole native shared owner page from API initial bytes and persistent literal source writes');equal(expected,a.data(stem+f'locale-allocation-{r[18]}-owned-page.bin'),'Whole actual native guest page matches source prediction');owner_rows.append(dict(level=level,sequence=seq,index=fi,root=binding['root'],CALL_pc=binding['CALL_pc'],guest=r[16],fullNative=r[17],generation=r[18],request=binding['requested_size'],extent=r[19],expected_sha256=hashlib.sha256(expected).hexdigest()));counts['whole_native_shared_owner_source_relations']+=1
     counts['persistent109_sequences']+=1""")
change("(out/'phases.json').write_text(json.dumps(rows,indent=2)+'\\n');pin(out/'phases.json');report=", """for filename,value in(('FS-source-derivations.json',FS_rows),('shared-owner-relations.json',owner_rows),('new-header-derivations.json',header_rows)):(out/filename).write_text(json.dumps(value,indent=2)+'\\n');pin(out/filename)
  (out/'phases.json').write_text(json.dumps(rows,indent=2)+'\\n');pin(out/'phases.json');report=""")
p=ROOT/'tools/m4-fs-source/compare_connected_v2.py';assert not p.exists();p.write_text(t)
