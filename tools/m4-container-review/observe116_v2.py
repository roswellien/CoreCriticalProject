"""One persistent original-BEFORE source machine across selected116 native roots.

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
sys.path.insert(0,str(Path(__file__).resolve().parent))
import final_observer116_v2 as V
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000)
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
from exact_equal import equal

def projection(m,state):
 fx,env=m.proj(state);return fx[:6]+bytes(18)+fx[24:],env
def main(native_report,original_report,name):
 out=ROOT/'reports/m4-container-review'/name;need(not out.exists(),'Fresh persistent source comparison');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[]
 try:
  nr=json.loads(pin(native_report).read_bytes());need(nr['passed'],'All current actual native116 sequences complete')
  G=load('persistent54_game',ROOT/'tools/m4-container-source/game_model.py');D=load('persistent54_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('persistent54_accepted27',ROOT/'tools/m4-joint-startup27-review/observe.py');S=load('persistent54_accepted28',ROOT/'tools/m4-joint-startup28-source-review/observe_v3.py');PE=load('persistent54_PE',ROOT/'tools/analysis/pe.py');m,c,inst,schedule=J.models();m.PAGES=list(PAGES);J.PAGES=PAGES;S.PAGES=PAGES
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(game);provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes()
  def initial_page(p):
   if p==0x5f4cc000:
    mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());return mfc.read(mfc.rva_range(p-mfc.image_base,4096)[0],4096)
   if p==0x5f498000:return pin(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-raw-page.bin','751e6229f4c61085d8e23814a5079e40fa99d411bd0f50ceb010f56d753b2d67').read_bytes()
   if p==0x780c1000:return provider[0x1000:0x2000]
   if p==0x78115000:return provider[0x54c00:0x55c00]
   need(p!=0x20001000,'Stack must be genuine bootstrap BEFORE input');r=bytearray(4096)
   for sec in pe.sections:
    lo=max(p,pe.image_base+sec['virtual_address']);hi=min(p+4096,pe.image_base+sec['virtual_address']+sec['raw_size'])
    if hi>lo:off=sec['raw_offset']+lo-pe.image_base-sec['virtual_address'];r[lo-p:hi-p]=game[off:off+hi-lo]
   return bytes(r)
  op=pin(original_report);original_receipt=json.loads(op.read_bytes());need(original_receipt['passed'],'Fresh full116 original execution proof');ori=D.DirectSet(original_receipt['original_capture'],pin)
  rootrows=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes());roots={r['entry']:r['registration']['callback']for r in rootrows};program,callbacks=G.source_program();static=out/'static';static.mkdir();material=B.material(static,pin)
  order=json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==116,'Exact full116 source order')
  for level in ('O0','O2'):
   a=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)
   try:
    for seq in range(6):
     stem=f'sequence-{seq}/cleaned/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)
     V.configure(G,m,a,seq,level,pin)
     before['memory']=dict(before['memory'])
     for page in PAGES:
      if page==0x5f4cc000:
       physical=initial_page(page)
       if page in before['memory']:equal(before['memory'][page],physical,'Declared native complete raw physical MFC data BEFORE input')
       before['memory'][page]=physical
      elif page not in before['memory']:before['memory'][page]=initial_page(page)
     machine,responses=B.bootstrap(before,facts,heap,material,G.Machine,program,callbacks,oldpc,oldsp)
     equal(bytes(machine.state),a.data(f'sequence-{seq}/caller-projection-before/State.bin'),'True bootstrap resulting State')
     cpu=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME+4,0x92837465,0x56473829,0xaabbccdd,0x202,BROKER);m.statecpu(machine.state,cpu);machine.cursor=BROKER;machine.cpu=struct.pack('<10I',*cpu);machine.fx=projection(m,machine.state)[0]
     equal(bytes(machine.state),a.data(f'sequence-{seq}/caller-projection-after/State.bin'),'Single declared caller CPU projection State');equal(machine.cpu,a.data(f'sequence-{seq}/caller-projection-after/CPU.bin'),'Single declared caller CPU projection CPU');equal(machine.fx,a.data(f'sequence-{seq}/caller-projection-after/FX.bin'),'Single declared caller projection FX');expected_callbacks=[]
     for phase,item in enumerate(order):
      entry=item['entry'];b=a.data(f'sequence-{seq}/phase-{phase}.bin');o=ori.data(f'phase/{seq}/{phase}.bin');need(words(b,0,5)==(seq,words(b,4)[0],phase,item['slot'],entry),'Exact actual root association')
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
       V.begin(machine);machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses);V.end(machine);expected_callbacks.append(roots[entry]);responses.completed_registry(machine,expected_callbacks);counts['literal_registration_roots']+=1
      else:
       if entry==S.ENTRY:goal=S.spi_goal(tuple(cpu),before_pages,b[157212:158424],True);after_state=m.afterstate(machine.state,goal['after'],entry,o,[]);counts['finite_SPI_roots']+=1
       elif entry==0x4c19f0:goal,after_state,cp,events=J.numeric_goal(c,bytes(machine.state),before_pages);counts['BEFORE_numeric_roots']+=1
       else:
        oracle=o[153828:305380]
        if entry in m.FP:
         original_before=o[2276:153828]
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
     need(len(expected_callbacks)==88,'All88 actual callback registrations carried');counts['persistent116_sequences']+=1
     V.finish(machine,responses,expected_callbacks,G)
   finally:a.close()
  ori.close();pin(__file__)
  for module in (J,m,c,S):
   for path,h in getattr(module,'PINS',{}).items():pin(path,h if isinstance(h,str)else h['sha256'])
  for p in (ROOT/'tools/m4-onexit-review/provider_bridge.py',ROOT/'tools/m4-onexit-review/provider_capture.py',ROOT/'tools/m4-onexit-review/provider_responses_v2.py',ROOT/'tools/m4-onexit-review/provider_responses.py',ROOT/'tools/m4-onexit-source/game_model.py',ROOT/'tools/m4-container-source/game_model.py'):pin(p)
  need(V.COUNTS['complete116_provider_sequences']==12,'All12 complete independent116 provider sequences')
  for file in (Path(__file__).with_name('final_observer116_v2.py'),ROOT/'tools/m4-strings-review/final_observer_v2.py',ROOT/'tools/m4-mfc-review/provider_model.py',ROOT/'tools/m4-mfc-review/provider_interface.py'):
   pin(file)
  pin(Path(__file__).with_name('exact_equal.py'));pin(Path(__file__).with_name('event_model.py'));pin(Path(__file__).with_name('string_observer116.py'));pin(ROOT/'tools/m4-fs-source/game_model.py')
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'phases.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'phases.json');report=dict(passed=passed,scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native116 game State/FX/CPU/ENV and entire37pages in actual table order',counts=dict(counts),provider_counts=dict(V.COUNTS),provider_sequences=V.ROWS,per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False,old_numerical_oracle_scope='Accepted10FPunits use finite current original scalar outputs and raw80/status, exact source operand domain checked; no whole original machine input',paired_original_game_equivalence=False,SPI_indeterminate_byte_policy_pending=True,whole_provider_checkpoints_review_separate=False,worker_post_HeapDestroy_identity_observed=True,initializer_credit=False,whole_M4_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])


