"""One persistent original-BEFORE source machine across selected124 native roots.

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
import capture as C
import responses_v2 as R
import continuity as A
import header_derivations as H
# Reuse the frozen bootstrap implementation with the additive typed API class.
B.R=R
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000)
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
 if len(a)!=len(b)or a!=b:raise ValueError(label+' '+str(first_diff(a,b)))
def projection(m,state):
 fx,env=m.proj(state);return fx[:6]+bytes(18)+fx[24:],env
def main(native_report,name):
 out=ROOT/'reports/m4-lockit-source'/name;need(not out.exists(),'Fresh persistent source comparison');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];FS_rows=[];header_rows=[];indirect_rows=[];lockit_rows=[];lockit_headers=[];continuity_rows=[]
 try:
  nr=json.loads(pin(native_report).read_bytes());need(nr['passed'],'All current actual native124 sequences complete')
  V=load('literal120_indirect_trace',ROOT/'tools/m4-next-source/indirect_trace.py');pin(V.P);G=load('persistent54_game',ROOT/'tools/m4-lockit-source/game_model.py');D=load('persistent54_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('persistent54_accepted27',ROOT/'tools/m4-joint-startup27-review/observe.py');S=load('persistent54_accepted28',ROOT/'tools/m4-joint-startup28-source-review/observe_v3.py');PE=load('persistent54_PE',ROOT/'tools/analysis/pe.py');m,c,inst,schedule=J.models();m.PAGES=list(PAGES);J.PAGES=PAGES;S.PAGES=PAGES
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(game);provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes()
  mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
  cp=PE.PEImage(provider);prep=pin(ROOT/'reports/m4-lockit-native/preparation-r3/report.json','4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d');prep_data=json.loads(prep.read_bytes());loaded_RW=pin(prep_data['loaded_input_page'],prep_data['loaded_input_page_sha256']).read_bytes();loaded_IAT=pin(prep_data['loaded_IAT_page'],prep_data['loaded_IAT_page_sha256']).read_bytes();pin(prep_data['loaded_original_bootstrap_report'],prep_data['loaded_original_bootstrap_sha256']);need(len(loaded_RW)==len(loaded_IAT)==4096 and int.from_bytes(loaded_RW[0x658:0x65c],'little')==2,'Complete actual original postDllMain input domain')
  def initial_page(p):
   if p==0x78145000:return loaded_RW
   if p==0x78146000:return loaded_IAT
   if p==0x7810a000:
    result=bytearray(4096)
    for sec in cp.sections:
     lo=max(p,cp.image_base+sec['virtual_address']);hi=min(p+4096,cp.image_base+sec['virtual_address']+sec['raw_size'])
     if hi>lo:offset=sec['raw_offset']+lo-cp.image_base-sec['virtual_address'];result[lo-p:hi-p]=provider[offset:offset+hi-lo]
    return bytes(result)
   if p==0x5f4cc000:
    result=bytearray(4096)
    for sec in mfc.sections:
     lo=max(p,mfc.image_base+sec['virtual_address']);hi=min(p+4096,mfc.image_base+sec['virtual_address']+sec['raw_size'])
     if hi>lo:offset=sec['raw_offset']+lo-mfc.image_base-sec['virtual_address'];result[lo-p:hi-p]=mfc.data[offset:offset+hi-lo]
    return bytes(result)
   if p==0x5f498000:return pin(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-raw-page.bin','751e6229f4c61085d8e23814a5079e40fa99d411bd0f50ceb010f56d753b2d67').read_bytes()
   if p==0x780c1000:return provider[0x1000:0x2000]
   if p==0x78115000:return provider[0x54c00:0x55c00]
   need(p!=0x20001000,'Stack must be genuine bootstrap BEFORE input');r=bytearray(4096)
   for sec in pe.sections:
    lo=max(p,pe.image_base+sec['virtual_address']);hi=min(p+4096,pe.image_base+sec['virtual_address']+sec['raw_size'])
    if hi>lo:off=sec['raw_offset']+lo-pe.image_base-sec['virtual_address'];r[lo-p:hi-p]=game[off:off+hi-lo]
   return bytes(r)
  op=pin(ROOT/'reports/m4-lockit-original/original-validation-r2/report.json','4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)
  rootrows=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/fixed-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/lockit-roots.json').read_bytes());roots={r['entry']:r['registration']['callback']for r in rootrows};program,callbacks=G.source_program();static=out/'static';static.mkdir();material=B.material(static,pin)
  order=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==124,'Exact selected124 rooted table order')
  FS_SPECS={0x4e78d7:(0,0x4e78d0,0x5b986b),0x4e78de:(1,0x4e78d0,0x5b986b),0x4e799f:(2,0x4e78d0,0x5b986b),0x48f297:(0,0x48f290,0x5b5233),0x48f29e:(1,0x48f290,0x5b5233),0x48f360:(2,0x48f290,0x5b5233),0x4d48f7:(0,0x4d48f0,0x5b8538),0x4d48fe:(1,0x4d48f0,0x5b8538),0x4d4948:(2,0x4d48f0,0x5b8538)}
  for f in json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/FS-frame-contracts.json').read_bytes()):
   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])
  for f in json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/FS-frame-contracts.json').read_bytes()):
   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])
  for f in json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/FS-frame-contracts.json').read_bytes()):
   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])
  FS_READ_BIAS={0x4125a0:0,0x500cd0:0}
  for level in ('O0','O2'):
   a=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)
   continuity_rows.append(dict(level=level,**A.audit(a,m,J)));pin(ROOT/'tools/m4-lockit-source/continuity.py')
   try:
    for seq in range(6):
     stem=f'sequence-{seq}/selected/';checkpoint_index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,checkpoint_index)
     before['memory']=dict(before['memory'])
     for page in PAGES:
      if page not in before['memory']:before['memory'][page]=initial_page(page)
      if page in (0x7810a000,0x78145000,0x78146000):equal(before['memory'][page],initial_page(page),'Explicit complete original provider input page association'+hex(page))
     fs_observations=[];current_root=[0]
     def observe_FS(model,address,value,size,pc,write):
      if address!=0x7ffde000 or pc not in FS_SPECS:return
      kind,group,handler=FS_SPECS[pc];need(size==4 and write==(kind!=0),'Exact normal literal source FS access');prior=int.from_bytes(model.bytes(address,4),'little');record=model.reg('esp')if kind==1 else prior;raw=model.bytes(record,12)if record!=0xffffffff else None;fs_observations.append(dict(level=level,sequence=seq,root=current_root[0],PC=pc,kind=kind,group_entry=group,handler=handler,source_call_frame=list(model.call_stack[-1])if kind==0 else None,before_head=prior,after_head=value if write else prior,entry_ESP=model.reg('esp')+FS_READ_BIAS.get(pc,8) if kind==0 else None,ESP=model.reg('esp'),record_address=record,record_hex=raw.hex()if raw is not None else None))
     class ObservedMachine(G.Machine):
      def step(self):
       V.before_step(self);result=super().step();V.after_step(self);return result
      def read(self,address,size=4,domain='source',pc=None):
       v=super().read(address,size,domain,pc)
       if domain=='source':observe_FS(self,address,v,size,self.word(2472)if pc is None else pc,False)
       return v
      def write(self,address,value,size=4,domain='source',pc=None):
       if domain=='source':observe_FS(self,address,value,size,self.word(2472)if pc is None else pc,True)
       return super().write(address,value,size,domain,pc)
     machine,responses=B.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp)
     resource=a.words(stem+'lockit-resource.bin',8,'Q');image_raw=a.data(stem+'lockit-native-images.bin');need(len(image_raw)==320,'Exactly eight genuine native CS40 images');images=[image_raw[n:n+40]for n in range(0,len(image_raw),40)];responses.associate_lockit(machine,resource,images,loaded_RW[0x640:0x658]);counts['actual_native_CS_resource_associations']+=1
     for suffix in ('before','after'):
      association=C.checkpoint(a,checkpoint_index,'lockit-resource-association-'+suffix);equal(bytes(machine.state),association['state'],'Explicit resource association preserves whole guest State');equal(machine.cpu,association['cpu'],'Explicit resource association preserves whole guest CPU');equal(machine.fx,association['fx'],'Explicit resource association preserves whole guest FX')
      for page in PAGES:
       if page in association['memory']:equal(machine.bytes(page,4096),association['memory'][page],'Explicit resource association preserves entire source page'+hex(page))
     V.configure(machine,lambda model:projection(m,model.state),dict(level=level,sequence=seq))
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
       machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses)
       if entry==0x4d4830:
        local=machine.accesses[root_access_start:];writes=[(i,v)for i,v in enumerate(local)if v[0]==0x4d4922 and v[1]==0x60b51c and v[3:]==(1,1)];need(len(writes)==1,'One literal new FS header source write');wi,write=writes[0];reads=[(i,v)for i,v in enumerate(local[:wi])if v[0]==0x4d4914 and v[3:]==(1,0)];need(len(reads)==1,'Exact literal local byte read');ri,read=reads[0];need(write[2]==read[2],'Literal AL copy to static header');stores=[(i,v)for i,v in enumerate(local[:ri])if v[4]and v[1]<=read[1]<v[1]+v[3]]
        if stores:
         si,store=stores[-1];need((store[2]>>(8*(read[1]-store[1])))&255==read[2],'Exact last source store byte provenance');provenance=dict(kind='dominating_source_store',index=si,pc=store[0],address=store[1],value=store[2],width=store[3])
        else:
         offset=PAGES.index(0x20001000)*4096+read[1]-0x20001000;need(before_pages[offset]==read[2],'Actual carried literal branch BEFORE stack byte provenance');provenance=dict(kind='carried_source_BEFORE_stack_byte',address=read[1],value=before_pages[offset],no_root_source_store_before_read=True)
        header_rows.append(dict(level=level,sequence=seq,phase=phase,root=entry,field=0x60b51c,write_pc=write[0],value=write[2],read_pc=read[0],read_address=read[1],branch_BEFORE_cpu=list(cpu),provenance=provenance))
       lockit_headers+=H.derive(machine,root_access_start,entry,before_pages,PAGES,cpu,level,seq,phase);expected_callbacks.append(roots[entry]);responses.completed_registry(machine,expected_callbacks);counts['literal_registration_roots']+=1
      else:
       if entry==S.ENTRY:goal=S.spi_goal(tuple(cpu),before_pages,b[157212:158424],True);after_state=m.afterstate(machine.state,goal['after'],entry,o,[]);counts['finite_SPI_roots']+=1
       elif entry==0x4c19f0:goal,after_state,cp,events=J.numeric_goal(c,bytes(machine.state),before_pages);counts['BEFORE_numeric_roots']+=1
       else:
        oracle=o[178404:354532]
        if entry in m.FP:
         original_before=o[2276:178404]
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
     need(len(expected_callbacks)==96,'All96 actual callback registrations carried');responses.lockit_complete();need(len(machine.lockit_import_proofs)==8 and len(machine.lockit_state_reads)==8,'All eight literal owning imports and authentic state reads');lockit_rows.append(dict(level=level,sequence=seq,imports=machine.lockit_import_proofs,state_reads=machine.lockit_state_reads,API_relations=responses.lockit_relations));counts['literal_Lockit_CALL_RET_pairs']+=8;counts['actual_native_CS40_source_API_relations']+=8;need(len(fs_observations)==57,'All57 normal game FS source accesses from one bootstrap BEFORE');fsframes=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')));rawrecords=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')));need(len(fsframes)==19 and len(rawrecords)==38,'Actual19 normal game frames and38 complete12B snapshots');stack=[];index=0
     for event in fs_observations:
      if event['kind']==0:
       f=fsframes[index];need(f[0]==1 and f[2]==event['root']and f[3]==event['group_entry']and f[5]==event['entry_ESP']and f[7]==event['PC']and f[8]==event['before_head']and f[10]==event['handler']and f[11]==0xffffffff and f[12]==len(stack)and f[13]==(stack[-1][1]+1 if stack else 0),'Exact normal native frame from literal source pushes/previous head/nested metadata');stack.append((f,index));index+=1
      else:
       f,fi=stack[-1];point=81 if event['kind']==1 else 84;found=[r for r in rawrecords if r[2]==fi and r[4]==point];need(len(found)==1,'One actual12B frame observation per reached source MOV');r=found[0];need(r[0]==1 and r[3]==event['root']and r[5]==event['PC']and r[6]==event['record_address']and r[7]==12,'Actual complete12B source address/PC/width');equal(struct.pack('<3I',*r[8:11]).hex(),event['record_hex'],'Entire actual native12B record from persistent literal BEFORE pushes/scope stores');counts['actual_native12B_source_relations']+=1
       if event['kind']==2:stack.pop()
      FS_rows.append(event);counts['native_FS_source_accesses']+=1
     need(not stack and index==19,'All normal nested game frames close');need(not machine.indirect_pending and len(machine.indirect_derivations)==6,'All six literal fixed indirect CALL/RET prefixes')
     actual_calls=list(struct.iter_unpack('<32Q',a.data(stem+'vtable-call-witnesses.bin')));need(len(actual_calls)==6,'Six actual rooted native indirect CALL/RET records');actual_source=list(struct.iter_unpack('<IIQII',a.data(stem+'locale-source-accesses.bin')))
     for vi,derived in enumerate(machine.indirect_derivations):
      w=actual_calls[vi];binding=V.INPUTS[(derived['root'],derived['CALL_pc'])]
      need(w[:8]==(1,vi,derived['root'],derived['CALL_pc'],derived['slot'],derived['target'],derived['target'],derived['CALL_pc'])and w[9]==binding['entry_ECX']and w[14:22]==(derived['ENTRY_BEFORE']['ESP'],derived['return_pc'],(binding['argument'] or 0),binding['RET_cleanup'],derived['RET_AFTER']['ESP'],derived['RET_AFTER']['CPU'][0],derived['RET_pc'],1),'Actual native cell/source CALL/RET/frame/argument/cleanup result joins literal prefix')
      if derived['CALL_pc']==0x59ff6e:need(w[10:12]==(binding['source_vtable'],binding['source_vtable'])and w[12]and w[13],'Derived-slot call has genuine committed vptr publication and actual source read indices')
      elif derived['CALL_pc']==0x59fdc5:need(w[10:12]==(binding['source_vtable'],binding['source_vtable'])and w[12]and w[13]==0,'Absolute cell call binds committed publication and has no fabricated instance-vptr read index')
      else:need(w[10:14]==(0,0,0,0),'Fixed standalone cell has no instance-vptr observation')
      need(w[24]==w[25]==derived['ENTRY_BEFORE']['FS0']==derived['RET_AFTER']['FS0']and w[26]==w[27]and w[28]==w[29]and w[30:]==(0,0),'Actual indirect prefix produces no API/owner/FS effects')
      need(w[8]==w[22]and actual_source[w[8]]==(derived['CALL_pc'],derived['slot'],derived['target'],4,0),'Actual exact physical cell read begins source prefix')
      equal([list(r)for r in actual_source[w[22]:w[23]]],derived['source_accesses'],'Entire actual native helper CALL/body/RET source access prefix from persistent BEFORE')
      if binding.get('source_vtable'):
       need(actual_source[w[12]]==(binding['dominating_vtable_store_PC'],binding['source_object'],binding['source_vtable'],4,1),'Actual dominating source vptr publication in exact source ledger')
       if derived['CALL_pc']==0x59ff6e:need(actual_source[w[13]]==(0x59ff64,binding['source_object'],binding['source_vtable'],4,0),'Actual subsequent source instance-vptr read before derived slot')
      derived['actual_native_source_access_prefix']=[list(r)for r in actual_source[w[22]:w[23]]];counts['whole_native_indirect_source_access_prefixes']+=1
      joins=[]
      for suffix,key in(('entered','ENTRY_BEFORE'),('returned','RET_AFTER')):
       checkpoint_name=f'vtable-call-{vi}-{suffix}';actual=C.checkpoint(a,checkpoint_index,checkpoint_name);prediction=derived[key]
       equal(actual['state'].hex(),prediction['State_hex'],'Entire actual indirect boundary State from persistent BEFORE source');equal(actual['cpu'],struct.pack('<10I',*prediction['CPU']),'Entire actual indirect boundary CPU GPR/flags/PC');equal(actual['fx'].hex(),prediction['FX_hex'],'Whole actual indirect boundary FX from persistent source')
       equal(actual['memory'][0x20001000][prediction['ESP']-0x20001000:prediction['ESP']-0x20001000+16].hex(),prediction['frame_hex'],'Actual complete indirect source CALL/RET stack words');joins.append(dict(name=checkpoint_name,state_sha256=hashlib.sha256(actual['state']).hexdigest(),CPU_hex=actual['cpu'].hex(),FX_sha256=hashlib.sha256(actual['fx']).hexdigest()));counts['actual_native_indirect_full_State_CPU_FX_boundary_joins']+=1
      derived['actual_native_witness']=list(w);derived['actual_native_checkpoints']=joins
     indirect_rows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=6;counts['actual_native_indirect_CALL_RET_joins']+=6;counts['persistent124_sequences']+=1
   finally:a.close();a.entries.clear();a.bundles.clear();del a
  ori.close();ori.entries.clear();ori.bundles.clear();pin(__file__)
  for module in (J,m,c,S):
   for path,h in getattr(module,'PINS',{}).items():pin(path,h if isinstance(h,str)else h['sha256'])
  for p in (ROOT/'tools/m4-onexit-review/provider_bridge.py',ROOT/'tools/m4-onexit-review/provider_capture.py',ROOT/'tools/m4-onexit-review/provider_responses_v2.py',ROOT/'tools/m4-onexit-review/provider_responses.py',ROOT/'tools/m4-onexit-source/game_model.py',ROOT/'tools/m4-next-source/game_model.py'):pin(p)
  need(len(lockit_headers)==108,'All nine exact new header byte source derivations across12cases');pin(ROOT/'tools/m4-lockit-source/header_derivations.py')
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for filename,value in(('FS-source-derivations.json',FS_rows),('new-header-derivations.json',header_rows),('indirect-source-derivations.json',indirect_rows),('Lockit-source-derivations.json',lockit_rows),('Lockit-header-derivations.json',lockit_headers),('native-continuity.json',continuity_rows)):(out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
  (out/'phases.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'phases.json');report=dict(passed=passed,scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native124 game State/FX/CPU/ENV and entire43pages in actual table order',counts=dict(counts),per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False,old_numerical_oracle_scope='Accepted10FPunits use finite current original scalar outputs and raw80/status, exact source operand domain checked; no whole original machine input',paired_original_game_equivalence=False,SPI_indeterminate_byte_policy_pending=True,whole_provider_checkpoints_review_separate=True,initializer_credit=False,whole_M4_complete=False,loaded_state2_source_input=True,native_CS40_opaque_copy=False,guest_CS24_semantic_output=True,native_DllMain_credit=False,native_continuity=continuity_rows,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])


