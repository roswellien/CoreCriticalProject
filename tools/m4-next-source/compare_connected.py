"""One persistent original-BEFORE source machine across selected120 native roots.

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
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000)
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
 out=ROOT/'reports/m4-next-source'/name;need(not out.exists(),'Fresh persistent source comparison');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];FS_rows=[];header_rows=[]
 try:
  nr=json.loads(pin(native_report).read_bytes());need(nr['passed'],'All current actual native120 sequences complete')
  G=load('persistent54_game',ROOT/'tools/m4-next-source/game_model.py');D=load('persistent54_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('persistent54_accepted27',ROOT/'tools/m4-joint-startup27-review/observe.py');S=load('persistent54_accepted28',ROOT/'tools/m4-joint-startup28-source-review/observe_v3.py');PE=load('persistent54_PE',ROOT/'tools/analysis/pe.py');m,c,inst,schedule=J.models();m.PAGES=list(PAGES);J.PAGES=PAGES;S.PAGES=PAGES
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(game);provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes()
  mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
  def initial_page(p):
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
  op=pin(ROOT/'reports/m4-vtable-original/validation-r1/report.json');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)
  rootrows=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/fixed-roots.json').read_bytes());roots={r['entry']:r['registration']['callback']for r in rootrows};program,callbacks=G.source_program();static=out/'static';static.mkdir();material=B.material(static,pin)
  order=json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order']
  FS_SPECS={0x4e78d7:(0,0x4e78d0,0x5b986b),0x4e78de:(1,0x4e78d0,0x5b986b),0x4e799f:(2,0x4e78d0,0x5b986b),0x48f297:(0,0x48f290,0x5b5233),0x48f29e:(1,0x48f290,0x5b5233),0x48f360:(2,0x48f290,0x5b5233),0x4d48f7:(0,0x4d48f0,0x5b8538),0x4d48fe:(1,0x4d48f0,0x5b8538),0x4d4948:(2,0x4d48f0,0x5b8538)}
  for f in json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/FS-frame-contracts.json').read_bytes()):
   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])
  for f in json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/FS-frame-contracts.json').read_bytes()):
   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])
  for level in ('O0','O2'):
   a=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)
   try:
    for seq in range(6):
     stem=f'sequence-{seq}/selected/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)
     before['memory']=dict(before['memory'])
     for page in PAGES:
      if page not in before['memory']:before['memory'][page]=initial_page(page)
     fs_observations=[];current_root=[0]
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
     machine,responses=B.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp)
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
      fx,env=projection(m,machine.state);equal(machine.cpu,b[36:76],'Whole source CPU BEFORE');equal(fx,b[120:628],'Whole source FX BEFORE');equal(env,b[2164:2192],'Whole source ENV BEFORE')
      if entry in roots:
       machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses)
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
        oracle=o[166120:329956]
        if entry in m.FP:
         original_before=o[2276:166120]
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
      equal(bytes(machine.state),b[145044:148548],f'{level} seq{seq} phase{phase} entire State AFTER source');equal(machine.cpu,b[76:120],'Whole source CPU AFTER');fx,env=projection(m,machine.state);equal(fx,b[628:1140],'Whole source FX AFTER');equal(env,b[2192:2220],'Whole source ENV AFTER')
      for i,p in enumerate(PAGES):
       actual=b[71908+i*4096:71908+(i+1)*4096]if i<17 else a.data(f'sequence-{seq}/phase-{phase}-after-page-{p}.bin');equal(machine.bytes(p,4096),actual,f'{level} seq{seq} phase{phase} whole AFTER page'+hex(p));counts['whole_page_AFTER']+=1
      need(machine.reg('esp')==FRAME+4 and machine.cursor==BROKER and not machine.call_stack,'Exact persistent source RETURN');rows.append(dict(level=level,sequence=seq,phase=phase,entry=entry,registry_calls=len(expected_callbacks),finite_API_index=responses.index));counts['persistent_phases']+=1
     need(len(expected_callbacks)==92,'All92 actual callback registrations carried');need(len(fs_observations)==45,'All45 normal game FS source accesses from one bootstrap BEFORE');fsframes=list(struct.iter_unpack('<32Q',a.data(stem+'fs-frame-witnesses.bin')));rawrecords=list(struct.iter_unpack('<16Q',a.data(stem+'fs-record-bytes.bin')));need(len(fsframes)==15 and len(rawrecords)==30,'Actual15 normal game frames and30 complete12B snapshots');stack=[];index=0
     for event in fs_observations:
      if event['kind']==0:
       f=fsframes[index];need(f[0]==1 and f[2]==event['root']and f[3]==event['group_entry']and f[5]==event['entry_ESP']and f[7]==event['PC']and f[8]==event['before_head']and f[10]==event['handler']and f[11]==0xffffffff and f[12]==len(stack)and f[13]==(stack[-1][1]+1 if stack else 0),'Exact normal native frame from literal source pushes/previous head/nested metadata');stack.append((f,index));index+=1
      else:
       f,fi=stack[-1];point=81 if event['kind']==1 else 84;found=[r for r in rawrecords if r[2]==fi and r[4]==point];need(len(found)==1,'One actual12B frame observation per reached source MOV');r=found[0];need(r[0]==1 and r[3]==event['root']and r[5]==event['PC']and r[6]==event['record_address']and r[7]==12,'Actual complete12B source address/PC/width');equal(struct.pack('<3I',*r[8:11]).hex(),event['record_hex'],'Entire actual native12B record from persistent literal BEFORE pushes/scope stores');counts['actual_native12B_source_relations']+=1
       if event['kind']==2:stack.pop()
      FS_rows.append(event);counts['native_FS_source_accesses']+=1
     need(not stack and index==15,'All normal nested game frames close');counts['persistent120_sequences']+=1
   finally:a.close()
  ori.close();pin(__file__)
  for module in (J,m,c,S):
   for path,h in getattr(module,'PINS',{}).items():pin(path,h if isinstance(h,str)else h['sha256'])
  for p in (ROOT/'tools/m4-onexit-review/provider_bridge.py',ROOT/'tools/m4-onexit-review/provider_capture.py',ROOT/'tools/m4-onexit-review/provider_responses_v2.py',ROOT/'tools/m4-onexit-review/provider_responses.py',ROOT/'tools/m4-onexit-source/game_model.py',ROOT/'tools/m4-next-source/game_model.py'):pin(p)
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for filename,value in(('FS-source-derivations.json',FS_rows),('new-header-derivations.json',header_rows)):(out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
  (out/'phases.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'phases.json');report=dict(passed=passed,scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native120 game State/FX/CPU/ENV and entire40pages in actual table order',counts=dict(counts),per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False,old_numerical_oracle_scope='Accepted10FPunits use finite current original scalar outputs and raw80/status, exact source operand domain checked; no whole original machine input',paired_original_game_equivalence=False,SPI_indeterminate_byte_policy_pending=True,whole_provider_checkpoints_review_separate=True,initializer_credit=False,whole_M4_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])


