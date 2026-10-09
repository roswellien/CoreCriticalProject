"""Actual original constructor effects from complete original BEFORE inputs.

Provider-created stack bytes are retained for a separate typed-provider proof;
this receipt compares every other entire game page and the exact zero-vector
x87 constructor, plus source-derived registration CALL arguments and order.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000)
MEM0,MEM1,END=2276,121060,239844
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical input identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def own(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def normalize_memory(data,raw_spi):
 memory={p:bytearray(data[i*4096:(i+1)*4096])for i,p in enumerate(PAGES)}
 for address,value in((0x5bb4fc,0x1df59c),(0x5bb6dc,raw_spi),(0x5bb52c,0x1decb0),(0x5bb530,0x1deca2)):
  if address==0x5bb4fc:need(words(memory[0x5bb000],address&4095)[0]==0x780c10f0,'Original numeric loader relocation')
  if address==0x5bb52c:need(words(memory[0x5bb000],address&4095)[0]==0x78004a36,'Original actual onexit export relocation')
  if address==0x5bb530:need(words(memory[0x5bb000],address&4095)[0]==0x78002fe5,'Original actual dllonexit export relocation')
  struct.pack_into('<I',memory[0x5bb000],address&4095,value)
 return memory
def original_state(m,G,before_cpu,b):
 s=bytearray(m.seed(before_cpu,words(b,4)[0],words(b,20)[0],words(b,24)[0]));s[2768:3280]=b[116:628]
 sw=struct.unpack_from('<H',b,118)[0]
 for bit,o in G.SF:s[o]=(sw>>bit)&1
 for n in range(8):s[2486+16*n:2496+16*n]=b[148+16*n:158+16*n]
 env=b[2164:2192];struct.pack_into('<H',s,2774,struct.unpack_from('<H',env,18)[0]);struct.pack_into('<I',s,2776,words(env,12)[0]);struct.pack_into('<H',s,2780,struct.unpack_from('<H',env,16)[0]);struct.pack_into('<I',s,2784,words(env,20)[0]);struct.pack_into('<H',s,2788,struct.unpack_from('<H',env,24)[0])
 return bytes(s)
def main(name,transport):
 out=ROOT/'reports/m4-onexit-source'/name;need(not out.exists(),'Fresh native prefix output');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];differences=[]
 try:
  G=own(ROOT/'tools/m4-onexit-source/game_model_v2.py','native_literal_game_model');old=own(ROOT/'tools/m4-joint-startup27-review/observe.py','native_numerical_projection');m,_,_,_=old.models();D=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','native_saved_direct')
  reader=D.DirectSet(Path(transport).resolve(),pin)
  roots=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes());lookup={r['entry']:r for r in roots};contract=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes());order=contract['selected_order'];program,callbacks=G.source_program();oldpages=PAGES[:17]
  need(reader.words('native-header.bin',6)==(1,6,54,324,17,159716),'Native direct protocol')
  for seq in range(6):
   previous=None
   for phase,item in enumerate(order):
    key=f'sequence-{seq}/phase-{phase}.bin'
    if key not in reader.entries:continue
    b=reader.data(key);entry=item['entry'];need(len(b)==159716 and words(b,0,5)==(seq,words(b,4)[0],phase,item['slot'],entry),'Native exact phase association')
    if entry not in lookup:continue
    memory={p:bytearray(b[2276+i*4096:2276+(i+1)*4096])for i,p in enumerate(oldpages)};after={p:bytearray(b[71908+i*4096:71908+(i+1)*4096])for i,p in enumerate(oldpages)}
    for p in PAGES[17:]:
     memory[p]=bytearray(reader.data(f'sequence-{seq}/phase-{phase}-before-page-{p}.bin'));after[p]=bytearray(reader.data(f'sequence-{seq}/phase-{phase}-after-page-{p}.bin'))
    cpu=words(b,36,10);state=b[141540:145044];need(words(state,2312)[0]==0x20001800 and words(state,2472)[0]==entry,'Native source root frame State BEFORE')
    machine=G.Machine(state,b[116:628],b[36:76],memory,program=program,callbacks=callbacks)
    machine.call_stack.append((entry,0x20001800,0x410a80,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0))
    machine.run(stop=lambda x:x.cursor==0x78004a36)
    callback=lookup[entry]['registration']['callback'];frame=machine.reg('esp');need(machine.bytes(frame,4)==struct.pack('<I',0x5ac124)and machine.bytes(frame+4,4)==struct.pack('<I',callback),'Native BEFORE-derived genuine provider CALL frame')
    for p in PAGES:
     if p==0x20001000:continue
     if machine.memory[p]!=after[p]:differences.append(dict(sequence=seq,phase=phase,entry=entry,page=p,byte_differences=[i for i,(a,z)in enumerate(zip(machine.memory[p],after[p]))if a!=z]))
     counts['whole_nonstack_page_checks']+=1
    if entry==0x4c58c0:
     need(machine.fp_depth==0 and len(machine.FP_PCs)==26,'Native exact zero-vector source path');fx,env=m.proj(machine.state)
     for field,expected,actual in (('nativeStateFXProjection',fx[:6]+bytes(18)+fx[24:],b[628:1140]),('ENV',env,b[2192:2220]),('raw80_slots',b''.join(machine.fp_slots()),b''.join(b[145044+2486+16*n:145044+2496+16*n]for n in range(8)))):
      if expected!=actual:differences.append(dict(sequence=seq,phase=phase,entry=entry,field=field,expected_hex=expected.hex(),actual_hex=actual.hex()))
     counts['BEFORE_only_zero_FP_checks']+=1
    rows.append(dict(sequence=seq,phase=phase,entry=entry,callback=callback,provider_frame=frame,source_instructions=len(machine.PCs),FP_PC_sequence=machine.FP_PCs));counts['constructor_prefixes']+=1
  reader.close()
  for module in (m,):
   for p,h in module.PINS.items():pin(p,h)
  for p in (ROOT/'tools/m4-onexit-review/provider_model.py',ROOT/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py',ROOT/'tools/m4-crt-locale-batch-model-review/batch.py',Path(__file__)):pin(p)
  need(counts['constructor_prefixes']>0,'Actual native prefix observations');passed=not differences
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'prefixes.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'prefixes.json');(out/'differences.json').write_text(json.dumps(differences,indent=2)+'\n');pin(out/'differences.json')
  report=dict(passed=passed,scope='Bounded native game constructor prefix from each actual native BEFORE; whole28 nonstack pages and exact zero-vector numerical state. Diagnostic only, provider stack and persistent whole54 comparison remain pending.',counts=dict(counts),AFTER_machine_seed=False,AFTER_numeric_oracle_used=False,whole_stack_compared=False,persistent_machine_proven=False,initializer_credit=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts),differences=len(differences))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
