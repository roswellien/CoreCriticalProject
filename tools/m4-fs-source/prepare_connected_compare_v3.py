"""Add exact native shared-owner source access/publication ledger checks."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];t=(ROOT/'tools/m4-fs-source/compare_connected_v2.py').read_text()
def change(a,b):
 global t
 assert t.count(a)==1,a
 t=t.replace(a,b)
change('fs_observations=[];current_root=[0]','fs_observations=[];current_root=[0];owned_source_rows=[];publication_source_rows=[];source_owners={};response_owner=[None]')
change('class ObservedGame(G.Machine):','''def observe_owned(model,address,value,size,pc,write):
      if current_root[0]not in{r['root']for r in fsbindings}or pc>=0x78000000:return
      owners=[v for v in source_owners.values()if v['guest']<=address and address+size<=v['guest']+v['requested']]
      need(len(owners)<=1,'Unique literal FS owned source access')
      if owners:
       owner=owners[0];owned_source_rows.append((current_root[0],pc,address,size,value,int(write),owner['root'],owner['CALL_pc'],owner['guest'],owner['generation'],owner['native'],address-owner['guest']))
      if not write or size!=4:return
      for fi,binding in enumerate(fsbindings):
       if current_root[0]!=binding['root']or pc!=binding['publication_PC']:continue
       row=next((v for v in source_owners.values()if v['root']==binding['root']and v['CALL_pc']==binding['CALL_pc']),None)
       if row is None or value!=row['guest']:continue
       parent=binding['publication_owner'];target=binding['publication'];parent_row=None
       if parent:
        parent_row=next(v for v in source_owners.values()if v['root']==parent['root']and v['CALL_pc']==parent['CALL_pc']);target=parent_row['guest']+parent['offset']
       need(address==target,'Literal FS publication address derived from exact owner/root/CALL plus offset')
       publication_source_rows.append((current_root[0],pc,address,value,row['generation'],row['native'],binding['CALL_pc'],parent_row['generation']if parent_row else 0,parent_row['guest']if parent_row else 0,parent['offset']if parent else 0,binding['object']))
     class ObservedGame(G.Machine):''')
change('observe_FS(self,address,v,size,self.word(2472)if pc is None else pc,False);return v','observe_FS(self,address,v,size,self.word(2472)if pc is None else pc,False);observe_owned(self,address,v,size,self.word(2472)if pc is None else pc,False);return v')
change('observe_FS(self,address,value,size,self.word(2472)if pc is None else pc,True);return super().write(address,value,size,domain,pc)','observe_FS(self,address,value,size,self.word(2472)if pc is None else pc,True);observe_owned(self,address,value,size,self.word(2472)if pc is None else pc,True);return super().write(address,value,size,domain,pc)')
change('machine,responses=B.bootstrap(before,facts,heap,material,ObservedGame,program,callbacks,oldpc,oldsp)','''machine,responses=B.bootstrap(before,facts,heap,material,ObservedGame,program,callbacks,oldpc,oldsp)
     def observe_API(model,target):
      prior=len(responses.allocations);frames=list(model.call_stack);responses(model,target)
      if len(responses.allocations)==prior:return
      need(len(responses.allocations)==prior+1,'One true native allocation result per literal API')
      if current_root[0]not in{v['root']for v in fsbindings}:return
      candidates=[v for v in fsbindings if v['root']==current_root[0]and any(f[3]==v['CALL_pc']for f in frames)]
      need(len(candidates)==1,'Genuine source game allocator CALL frame identifies dynamic owner');binding=candidates[0];allocation=responses.allocations[-1];need(allocation['requested']==binding['requested_size'],'Literal caller request independently matches true native API allocation');need(allocation['guest']not in source_owners,'One acquired live shared source owner');source_owners[allocation['guest']]=dict(allocation,root=binding['root'],CALL_pc=binding['CALL_pc'])''')
change('G.complete_root(machine,api=responses)','G.complete_root(machine,api=observe_API)')
change("mfc_records=list(struct.iter_unpack('<32Q',a.data(stem+'mfc-allocation-witnesses.bin')));need(len(mfc_records)==45,'Actual native45 MFC owners')",'''actual_accesses=list(struct.iter_unpack('<16Q',a.data(stem+'fs-owned-accesses.bin')));need(len(actual_accesses)==len(owned_source_rows),'All and only actual FS owned access rows')
     for expected,row in zip(owned_source_rows,actual_accesses):
      need(row[0]==1 and row[2:14]==expected,'Exact actual native owned access values, root/PC/width/direction/creation root/CALL/guest/generation/full-native/offset from source BEFORE');counts['exact_owned_source_access_ledger_relations']+=1
     actual_publications=list(struct.iter_unpack('<16Q',a.data(stem+'fs-owned-publications.bin')));need(len(actual_publications)==len(publication_source_rows)==10,'Ten genuine committed transient publication events')
     for expected,row in zip(publication_source_rows,actual_publications):
      need(row[0]==1 and row[2:12]==expected[:10]and row[13]==expected[10]and row[14:]==(0,0),'Exact dynamic/static publication root/PC/address/alias/generation/full-native/parent owner/offset/static object source relation');counts['exact_dynamic_publication_ledger_relations']+=1
     mfc_records=list(struct.iter_unpack('<32Q',a.data(stem+'mfc-allocation-witnesses.bin')));need(len(mfc_records)==45,'Actual native45 MFC owners')''')
p=ROOT/'tools/m4-fs-source/compare_connected_v3.py';assert not p.exists();p.write_text(t)
