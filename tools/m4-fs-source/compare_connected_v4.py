"""One persistent original-BEFORE source machine across selected109 native roots.

New game/provider instructions are modeled literally. Accepted old FP units
retain their finite original numerical oracle only, with exact source inputs
checked. No candidate phase BEFORE/AFTER machine reseeds the persistent model.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_bridge as B
import provider_capture as C
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000)
FRAME=0x20001800;BROKER=0x410a80
PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen source model input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical input');PINS[str(p)]=v;return p
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def first_diff(a,b):return [(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:16]
def equal(a,b,label):
 if len(a)!=len(b) or a!=b:raise ValueError(label+' '+str(first_diff(a,b)))
def projection(m,state):
 fx,env=m.proj(state);return fx[:6]+bytes(18)+fx[24:],env
def main(native_report,name):
 out=ROOT/'reports/m4-fs-source'/name;need(not out.exists(),'Fresh persistent source comparison');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];FS_rows=[];owner_rows=[];header_rows=[]
 try:
  nr=json.loads(pin(native_report).read_bytes());need(nr['passed'],'All current actual native109 sequences complete')
  G=load('persistent54_game',ROOT/'tools/m4-fs-source/game_model.py');D=load('persistent54_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('persistent54_accepted27',ROOT/'tools/m4-joint-startup27-review/observe.py');S=load('persistent54_accepted28',ROOT/'tools/m4-joint-startup28-source-review/observe_v3.py');PE=load('persistent54_PE',ROOT/'tools/analysis/pe.py');m,c,inst,schedule=J.models();m.PAGES=list(PAGES);J.PAGES=PAGES;S.PAGES=PAGES
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(game);provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes()
  def initial_page(p):
   if p==0x5f498000:return pin(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-raw-page.bin','751e6229f4c61085d8e23814a5079e40fa99d411bd0f50ceb010f56d753b2d67').read_bytes()
   if p==0x780c1000:return provider[0x1000:0x2000]
   if p==0x78115000:return provider[0x54c00:0x55c00]
   need(p!=0x20001000,'Stack must be genuine bootstrap BEFORE input');r=bytearray(4096)
   for sec in pe.sections:
    lo=max(p,pe.image_base+sec['virtual_address']);hi=min(p+4096,pe.image_base+sec['virtual_address']+sec['raw_size'])
    if hi>lo:off=sec['raw_offset']+lo-pe.image_base-sec['virtual_address'];r[lo-p:hi-p]=game[off:off+hi-lo]
   return bytes(r)
  op=pin(ROOT/'reports/m4-fs-source/original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)
  rootrows=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots={r['entry']:r['registration']['callback']for r in rootrows};program,callbacks=G.source_program();static=out/'static';static.mkdir();material=B.material(static,pin)
  order=json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order']
  fsbindings=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes())
  FS_SPECS={0x4e78d7:(0,0x4e78d0,0x5b986b),0x4e78de:(1,0x4e78d0,0x5b986b),0x4e799f:(2,0x4e78d0,0x5b986b),0x48f297:(0,0x48f290,0x5b5233),0x48f29e:(1,0x48f290,0x5b5233),0x48f360:(2,0x48f290,0x5b5233),0x4d48f7:(0,0x4d48f0,0x5b8538),0x4d48fe:(1,0x4d48f0,0x5b8538),0x4d4948:(2,0x4d48f0,0x5b8538)}
  for level in ('O0','O2'):
   a=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)
   try:
    for seq in range(6):
     stem=f'sequence-{seq}/selected/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)
     before['memory']=dict(before['memory'])
     for page in PAGES:
      if page not in before['memory']:before['memory'][page]=initial_page(page)
     fs_observations=[];current_root=[0];owned_source_rows=[];publication_source_rows=[];source_owners={};response_owner=[None]
     def observe_FS(model,address,value,size,pc,write):
      if address!=0x7ffde000 or pc not in FS_SPECS:return
      kind,group,handler=FS_SPECS[pc];need(size==4 and write==(kind!=0),'Exact literal source normal FS access')
      prior=int.from_bytes(model.bytes(address,4),'little');record=model.reg('esp')if kind==1 else prior
      raw=model.bytes(record,12)if record!=0xffffffff else None
      fs_observations.append(dict(level=level,sequence=seq,root=current_root[0],PC=pc,kind=kind,group_entry=group,handler=handler,source_call_frame=list(model.call_stack[-1])if kind==0 else None,before_head=prior,after_head=value if write else prior,entry_ESP=model.reg('esp')+8 if kind==0 else None,ESP=model.reg('esp'),record_address=record,record_hex=raw.hex()if raw is not None else None))
     def observe_owned(model,address,value,size,pc,write):
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
     class ObservedGame(G.Machine):
      def read(self,address,size=4,domain='source',pc=None):
       v=super().read(address,size,domain,pc);observe_FS(self,address,v,size,self.word(2472)if pc is None else pc,False);observe_owned(self,address,v,size,self.word(2472)if pc is None else pc,False);return v
      def write(self,address,value,size=4,domain='source',pc=None):
       observe_FS(self,address,value,size,self.word(2472)if pc is None else pc,True);observe_owned(self,address,value,size,self.word(2472)if pc is None else pc,True);return super().write(address,value,size,domain,pc)
     machine,responses=B.bootstrap(before,facts,heap,material,ObservedGame,program,callbacks,oldpc,oldsp)
     def observe_API(model,target):
      prior=len(responses.allocations);frames=list(model.call_stack);responses(model,target)
      if len(responses.allocations)==prior:return
      need(len(responses.allocations)==prior+1,'One true native allocation result per literal API')
      if current_root[0]not in{v['root']for v in fsbindings}:return
      candidates=[v for v in fsbindings if v['root']==current_root[0]and any(f[3]==v['CALL_pc']for f in frames)]
      need(len(candidates)==1,'Genuine source game allocator CALL frame identifies dynamic owner');binding=candidates[0];allocation=responses.allocations[-1];need(allocation['requested']==binding['requested_size'],'Literal caller request independently matches true native API allocation');need(allocation['guest']not in source_owners,'One acquired live shared source owner');source_owners[allocation['guest']]=dict(allocation,root=binding['root'],CALL_pc=binding['CALL_pc'])
     equal(bytes(machine.state),a.data(f'sequence-{seq}/caller-projection-before/State.bin'),'True bootstrap resulting State')
     cpu=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME+4,0x92837465,0x56473829,0xaabbccdd,0x202,BROKER);m.statecpu(machine.state,cpu);machine.cursor=BROKER;machine.cpu=struct.pack('<10I',*cpu);machine.fx=projection(m,machine.state)[0]
     equal(bytes(machine.state),a.data(f'sequence-{seq}/caller-projection-after/State.bin'),'Single declared caller CPU projection State');equal(machine.cpu,a.data(f'sequence-{seq}/caller-projection-after/CPU.bin'),'Single declared caller CPU projection CPU');equal(machine.fx,a.data(f'sequence-{seq}/caller-projection-after/FX.bin'),'Single declared caller projection FX');expected_callbacks=[]
     for phase,item in enumerate(order):
      entry=item['entry'];current_root[0]=entry;root_access_start=len(machine.accesses);b=a.data(f'sequence-{seq}/phase-{phase}.bin');o=ori.data(f'phase/{seq}/{phase}.bin');need(words(b,0,5)==(seq,words(b,4)[0],phase,item['slot'],entry),'Exact actual root association')
      need(machine.reg('esp')==FRAME+4 and machine.cursor==BROKER and not machine.call_stack,'Persistent caller RETURN before next source root')
      machine.write(FRAME,BROKER,domain='research',pc=BROKER);cpu=list(machine.projected_cpu());cpu[4]=FRAME;cpu[9]=entry
      if entry in roots or entry==0x4c19f0:m.statecpu(machine.state,cpu)
      else:machine.state=bytearray(m.beforestate(machine.state,cpu,entry))
      machine.cpu=struct.pack('<10I',*cpu);machine.cursor=entry;equal(bytes(machine.state),b[141540:145044],f'{level} seq{seq} phase{phase} full State BEFORE carry')
      before_pages=b''.join(machine.bytes(p,4096)for p in PAGES)
      for i,p in enumerate(PAGES):
       expected=before_pages[i*4096:(i+1)*4096];actual=b[2276+i*4096:2276+(i+1)*4096]if i<17 else a.data(f'sequence-{seq}/phase-{phase}-before-page-{p}.bin');equal(expected,actual,f'{level} seq{seq} phase{phase} whole BEFORE page'+hex(p));counts['whole_page_BEFORE']+=1
      fx,env=projection(m,machine.state);equal(machine.cpu,b[36:76],'Whole source CPU BEFORE');equal(fx,b[116:628],'Whole source FX BEFORE');equal(env,b[2164:2192],'Whole source ENV BEFORE')
      if entry in roots:
       machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=observe_API)
       if entry==0x4d4830:
        local=machine.accesses[root_access_start:];writes=[(i,v)for i,v in enumerate(local)if v[0]==0x4d4922 and v[1]==0x60b51c and v[3:]==(1,1)];need(len(writes)==1,'One literal new FS header source write');wi,write=writes[0];reads=[(i,v)for i,v in enumerate(local[:wi])if v[0]==0x4d4914 and v[3:]==(1,0)];need(len(reads)==1,'Exact literal local byte read');ri,read=reads[0];need(write[2]==read[2],'Literal AL copy to static header');stores=[(i,v)for i,v in enumerate(local[:ri])if v[4]and v[1]<=read[1]<v[1]+v[3]]
        if stores:
         si,store=stores[-1];need((store[2]>>(8*(read[1]-store[1])))&255==read[2],'Exact last source store byte provenance');provenance=dict(kind='dominating_source_store',index=si,pc=store[0],address=store[1],value=store[2],width=store[3])
        else:
         offset=PAGES.index(0x20001000)*4096+read[1]-0x20001000;need(before_pages[offset]==read[2],'Actual carried literal branch BEFORE stack byte provenance');provenance=dict(kind='carried_source_BEFORE_stack_byte',address=read[1],value=before_pages[offset],no_root_source_store_before_read=True)
        header_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,field=0x60b51c,write_pc=write[0],value=write[2],read_pc=read[0],read_address=read[1],branch_BEFORE_cpu=list(cpu),provenance=provenance))
       expected_callbacks.append(roots[entry]);responses.completed_registry(machine,expected_callbacks);counts['literal_registration_roots']+=1
      else:
       if entry==S.ENTRY:goal=S.spi_goal(tuple(cpu),before_pages,b[157212:158424],True);after_state=m.afterstate(machine.state,goal['after'],entry,o,[]);counts['finite_SPI_roots']+=1
       elif entry==0x4c19f0:goal,after_state,cp,events=J.numeric_goal(c,bytes(machine.state),before_pages);counts['BEFORE_numeric_roots']+=1
       else:
        oracle=o[145636:288996]
        if entry in m.FP:
         original_before=o[2276:145636]
         for ins in inst[entry]:
          if ins['mnemonic']in ('fld','fild','fmul','fdiv'):
           import re
           hit=re.search(r'\[(0x[0-9a-f]+)\]',ins['operands'])
           if hit:
            address=int(hit[1],16);width=8 if 'qword'in ins['operands'] else 4;offset=PAGES.index(address&~4095)*4096+(address&4095);equal(before_pages[offset:offset+width],original_before[offset:offset+width],'Accepted finite old FP exact source operand');counts['old_FP_input_witnesses']+=1
         counts['bounded_old_FP_oracle_roots']+=1
        goal=m.phasegoal(entry,tuple(cpu),before_pages,oracle,inst[entry],schedule);after_state=m.afterstate(machine.state,goal['after'],entry,o,inst[entry])
       machine.state=bytearray(after_state)
       for i,page in enumerate(PAGES):machine.store_bytes(page,goal['pages'][i*4096:(i+1)*4096])
       machine.cursor=BROKER
      machine.cpu=B.cpu(machine.state);machine.fx=projection(m,machine.state)[0]
      equal(bytes(machine.state),b[145044:148548],f'{level} seq{seq} phase{phase} entire State AFTER source');equal(machine.cpu,b[76:116],'Whole source CPU AFTER');fx,env=projection(m,machine.state);equal(fx,b[628:1140],'Whole source FX AFTER');equal(env,b[2192:2220],'Whole source ENV AFTER')
      for i,p in enumerate(PAGES):
       actual=b[71908+i*4096:71908+(i+1)*4096]if i<17 else a.data(f'sequence-{seq}/phase-{phase}-after-page-{p}.bin');equal(machine.bytes(p,4096),actual,f'{level} seq{seq} phase{phase} whole AFTER page'+hex(p));counts['whole_page_AFTER']+=1
      need(machine.reg('esp')==FRAME+4 and machine.cursor==BROKER and not machine.call_stack,'Exact persistent source RETURN');rows.append(dict(level=level,sequence=seq,phase=phase,entry=entry,registry_calls=len(expected_callbacks),finite_API_index=responses.index));counts['persistent_phases']+=1
     need(len(expected_callbacks)==81,'All81 actual callback registrations carried')
     need(len(fs_observations)==21,'All21 literal normal FS accesses derived from one bootstrap BEFORE')
     fsframes=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')));rawrecords=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')));need(len(fsframes)==7 and len(rawrecords)==14,'Exact seven actual native frame records and fourteen12B snapshots')
     model_stack=[];frame_index=0
     for event in fs_observations:
      if event['kind']==0:
       f=fsframes[frame_index];need(f[:4]==(1,frame_index,event['root'],event['group_entry'])and f[5]==event['entry_ESP']and f[7]==event['PC']and f[8]==event['before_head']and f[9]==f[5]-12 and f[10]==event['handler']and f[11]==0xffffffff,'Actual native CALL/record literal source relation');need(f[12]==len(model_stack)and f[13]==(model_stack[-1][1]+1 if model_stack else 0),'Actual nested frame parent and depth');need(f[15]==f[19]==f[21]==1 and f[17]==f[8]==f[22]and f[24:26]==(0x7ffde000,0xffffffff),'All normal frame installs/saved-load/restores/RET with explicit runtime sentinel');call=event['source_call_frame'];spec={0x4e78d0:(0x4e78de,0x4e7997,0x4e799f,0x4e79aa),0x48f290:(0x48f29e,0x48f353,0x48f360,0x48f36b),0x4d48f0:(0x4d48fe,0x4d492a,0x4d4948,0x4d4953)}[event['group_entry']];need((f[4],f[5],f[6],f[23])==(call[3],call[1],call[2],call[0]),'Actual original source CALL site/frame/return and retained tail-entry metadata');need((f[14],f[16],f[18],f[20])==spec,'Exact actual source install/saved-load/restore/RET PCs');model_stack.append((f,frame_index));frame_index+=1
      else:
       f,fi=model_stack[-1];point=81 if event['kind']==1 else 84;records=[r for r in rawrecords if r[2]==fi and r[4]==point];need(len(records)==1,'One actual whole12B observation at exact source point');r=records[0];need(r[0]==1 and r[3]==event['root']and r[5]==event['PC']and r[6]==event['record_address']and r[7]==12,'Actual native12B source PC/address/width');equal(struct.pack('<3I',*r[8:11]).hex(),event['record_hex'],'All twelve native installed/restored bytes computed solely from source BEFORE');counts['actual_native12B_source_relations']+=1
       if event['kind']==2:model_stack.pop()
      FS_rows.append(event);counts['native_FS_source_accesses']+=1
     need(not model_stack,'Every source normal nested frame closes')
     actual_accesses=list(struct.iter_unpack('<16Q',a.data(stem+'fs-owned-accesses.bin')));need(len(actual_accesses)==len(owned_source_rows),'All and only actual FS owned access rows')
     for expected,row in zip(owned_source_rows,actual_accesses):
      need(row[0]==1 and row[2:14]==expected,'Exact actual native owned access values, root/PC/width/direction/creation root/CALL/guest/generation/full-native/offset from source BEFORE');counts['exact_owned_source_access_ledger_relations']+=1
     actual_publications=list(struct.iter_unpack('<16Q',a.data(stem+'fs-owned-publications.bin')));need(len(actual_publications)==len(publication_source_rows)==10,'Ten genuine committed transient publication events')
     for expected,row in zip(publication_source_rows,actual_publications):
      need(row[0]==1 and row[2:12]==expected[:10]and row[13]==expected[10]and row[14:]==(0,0),'Exact dynamic/static publication root/PC/address/alias/generation/full-native/parent owner/offset/static object source relation');counts['exact_dynamic_publication_ledger_relations']+=1
     mfc_records=list(struct.iter_unpack('<32Q',a.data(stem+'mfc-allocation-witnesses.bin')));need(len(mfc_records)==45,'Actual native45 MFC owners')
     for fi,binding in enumerate(fsbindings):
      records=[r for r in mfc_records if r[2]==binding['root']and r[4]==binding['CALL_pc']];need(len(records)==1,'Unique actual source owner/root/CALL');r=records[0];owned=next(v for v in responses.allocations if v['generation']==r[18]);need(owned['guest']==r[16]and owned['native']==r[17]and owned['requested']==binding['requested_size']and owned['live'],'Genuine native API allocation and literal MFC source owner joined');initial=a.data(stem+f'locale-allocation-{r[18]}-initial.bin');equal(initial,owned['initial'],'Exact original native API BEFORE backing');expected=a.data(stem+f'locale-allocation-{r[18]}-expected.bin');equal(machine.bytes(r[16],4096),expected,'Whole native shared owner page from API initial bytes and persistent literal source writes');equal(expected,a.data(stem+f'locale-allocation-{r[18]}-owned-page.bin'),'Whole actual native guest page matches source prediction');owner_rows.append(dict(level=level,sequence=seq,index=fi,root=binding['root'],CALL_pc=binding['CALL_pc'],guest=r[16],fullNative=r[17],generation=r[18],request=binding['requested_size'],extent=r[19],expected_sha256=hashlib.sha256(expected).hexdigest()));counts['whole_native_shared_owner_source_relations']+=1
     counts['persistent109_sequences']+=1
   finally:a.close()
  ori.close();pin(__file__)
  for module in (J,m,c,S):
   for path,h in getattr(module,'PINS',{}).items():pin(path,h if isinstance(h,str)else h['sha256'])
  for p in (ROOT/'tools/m4-onexit-review/provider_bridge.py',ROOT/'tools/m4-onexit-review/provider_capture.py',ROOT/'tools/m4-onexit-review/provider_responses_v2.py',ROOT/'tools/m4-onexit-review/provider_responses.py',ROOT/'tools/m4-onexit-source/game_model.py',ROOT/'tools/m4-fs-source/game_model.py'):pin(p)
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for filename,value in(('FS-source-derivations.json',FS_rows),('shared-owner-relations.json',owner_rows),('new-header-derivations.json',header_rows)):(out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
  (out/'phases.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'phases.json');report=dict(passed=passed,scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native109 game State/FX/CPU/ENV and entire35pages in actual table order',counts=dict(counts),per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False,old_numerical_oracle_scope='Accepted10FPunits use finite current original scalar outputs and raw80/status, exact source operand domain checked; no whole original machine input',paired_original_game_equivalence=False,SPI_indeterminate_byte_policy_pending=True,whole_provider_checkpoints_review_separate=True,initializer_credit=False,whole_M4_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])


