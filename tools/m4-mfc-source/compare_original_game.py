"""Actual original constructor effects from complete original BEFORE inputs.

Provider-created stack bytes are retained for a separate typed-provider proof;
this receipt compares every other entire game page and the exact zero-vector
x87 constructor, plus source-derived registration CALL arguments and order.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={};MFC_IMPORTS=[]
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000)
MEM0,MEM1,END=2276,145636,288996
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
 for address,value in((0x5bb4fc,0x1df59c),(0x5bb6dc,raw_spi),(0x5bb52c,0x1decb0),(0x5bb530,0x1deca2),(0x5bb670,0x1df886),(0x5bb4bc,0x80000337)):
  if address==0x5bb4bc:need(words(memory[0x5bb000],address&4095)[0]==0x5f401ea0,'Original MFC ordinal owning loader relocation')
  if address==0x5bb4fc:need(words(memory[0x5bb000],address&4095)[0]==0x780c10f0,'Original numeric loader relocation')
  if address==0x5bb52c:need(words(memory[0x5bb000],address&4095)[0]==0x78004a36,'Original actual onexit export relocation')
  if address==0x5bb670:need(words(memory[0x5bb000],address&4095)[0]==0x78010a6d,'Original actual strdup export relocation')
  if address==0x5bb530:need(words(memory[0x5bb000],address&4095)[0]==0x78002fe5,'Original actual dllonexit export relocation')
  struct.pack_into('<I',memory[0x5bb000],address&4095,value)
 for slot,raw,target in MFC_IMPORTS:
  need(words(memory[0x5f498000],slot&4095)[0]==target,'Exact authenticated whole MFC loaded import');struct.pack_into('<I',memory[0x5f498000],slot&4095,raw)
 return memory
def original_state(m,G,before_cpu,b):
 s=bytearray(m.seed(before_cpu,words(b,4)[0],words(b,20)[0],words(b,24)[0]));s[2768:3280]=b[116:628]
 sw=struct.unpack_from('<H',b,118)[0]
 for bit,o in G.SF:s[o]=(sw>>bit)&1
 for n in range(8):s[2486+16*n:2496+16*n]=b[148+16*n:158+16*n]
 env=b[2164:2192];struct.pack_into('<H',s,2774,struct.unpack_from('<H',env,18)[0]);struct.pack_into('<I',s,2776,words(env,12)[0]);struct.pack_into('<H',s,2780,struct.unpack_from('<H',env,16)[0]);struct.pack_into('<I',s,2784,words(env,20)[0]);struct.pack_into('<H',s,2788,struct.unpack_from('<H',env,24)[0])
 return bytes(s)
def main(name):
 out=ROOT/'reports/m4-mfc-source'/name;need(not out.exists(),'Fresh source comparison output');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[]
 try:
  PE=own(ROOT/'tools/analysis/pe.py','exact_game_PE');raw_game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(raw_game)
  for a,v in ((0x5bb4fc,0x1df59c),(0x5bb6dc,0x1df20c),(0x5bb52c,0x1decb0),(0x5bb530,0x1deca2)):
   off,_=pe.rva_range(a-0x400000,4);need(words(raw_game,off)[0]==v,'Exact raw source IAT projection')
  G=own(ROOT/'tools/m4-mfc-source/game_model.py','exact_game_model');old=own(ROOT/'tools/m4-joint-startup27-review/observe.py','old_numerical_projection');m,_,_,_=old.models();D=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','exact_saved_archive')
  report_path=pin(ROOT/'reports/m4-mfc-source/original-run-r3/report.json','a50819520282272712899cb64faedd8d568c08a22d6d25e65fbc18358571faa0');r=json.loads(report_path.read_bytes());need(r['passed'],'Genuine original execution passed')
  reader=D.DirectSet(r['original_capture'],pin);global MFC_IMPORTS;MFC_IMPORTS=[(v[0],v[1],v[2])for v in struct.iter_unpack('<7I',reader.data('mfc-import-ledger.bin'))];need(len(MFC_IMPORTS)==511,'Exact511 named original MFC imports')
  try:
   roots=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes());lookup={r['entry']:r for r in roots};contract=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json').read_bytes());order=contract['selected_order'];program,callbacks=G.source_program();raw_spi=0x1df20c
   for seq in range(6):
    previous=None;seen=[]
    for phase,item in enumerate(order):
     b=reader.data(f'phase/{seq}/{phase}.bin');need(len(b)==291456 and words(b,0,5)==(seq,words(b,4)[0],phase,item['slot'],item['entry']),'Original exact phase association')
     if previous is not None:
      need(b[MEM0:MEM1]==previous[MEM1:END],'Entire32 original pages carry');need(b[116:628]==previous[628:1140]and b[2164:2192]==previous[2192:2220],'Original full FX/ENV carry')
      expected=list(words(previous,76,10));expected[4]=0x20001800;expected[9]=item['entry'];need(words(b,36,10)==tuple(expected),'Every original CPU field carried without phase reseed')
     previous=b;entry=item['entry']
     if entry not in lookup:continue
     memory=normalize_memory(b[MEM0:MEM1],raw_spi);after=normalize_memory(b[MEM1:END],raw_spi);cpu=words(b,36,10);state=original_state(m,G,cpu,b);machine=G.Machine(state,b[116:628],b[36:76],memory,program=program,callbacks=callbacks)
     machine.call_stack.append((entry,0x20001800,0x410a80,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0))
     allocation_calls=[];api=reader.data(f'phase/{seq}/{phase}/api-ledger.bin');allocs=[(k//104,words(api,k,26))for k in range(0,len(api),104)if words(api,k+96)[0]==0];bindings=json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json').read_bytes())
     def finite_malloc(model,target):
      site=model.PCs[-1];need(target==0x780012b3 and site in(0x78010a7e,0x5f401eb5),'Only exact strdup/MFC malloc cdecl source frontier');need(len(allocation_calls)<len(allocs),'One authentic original allocation fact per actual constructor malloc')
      ai,fact=allocs[len(allocation_calls)];request=int.from_bytes(model.bytes(model.reg('esp')+4,4),'little');rounded=(request+15)&~15;need(fact[21]==0 and fact[22]==rounded and fact[10]!=0,'True original HeapAlloc scalar/request identity');initial=reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');capacity=words(reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/size.bin'))[0];need(capacity==len(initial)and capacity>=rounded,'Full genuine allocation BEFORE guest write backing')
      pointer=fact[10];need(not any(p<=pointer<p+len(v)for p,v in model.memory.items()),'Disjoint actual heap pointer');model.memory[pointer]=bytearray(initial);owner=dict(pointer=pointer,request=request,rounded=rounded,capacity=capacity,API_index=ai,site=site,initial_sha256=hashlib.sha256(initial).hexdigest())
      if site==0x5f401eb5:
       frame=model.call_stack[-2];binding=next(v for v in bindings if v['root']==entry and v['CALL_pc']==frame[3]);owner['binding']=binding;need(request==binding['requested_size'],'Literal actual MFC source request')
      allocation_calls.append(owner);model.api_return(site,0,pointer)
     machine.run(stop=lambda x:x.cursor==0x78004a36,api=finite_malloc)
     if entry in [r['entry']for r in roots if 'string'in r]:
      source=lookup[entry]['string'];need(len(allocation_calls)==int(source['actual_strdup_called']),'Measured null constructor or one actual strdup call')
      if allocation_calls:
       owner=allocation_calls[0];raw=bytes.fromhex(source['bytes_hex']);need(owner['request']==len(raw) and machine.bytes(owner['pointer'],len(raw))==raw,'Literal source strlen/malloc/strcpy byte flow')
       meta=words(reader.data(f'phase/{seq}/{phase}/strings/{entry}/meta.bin'),0,6);need(meta[:5]==(entry,source['source'],lookup[entry]['objects'][0]['address']+4,owner['pointer'],len(raw)),'Actual live ownership typed identity');need(reader.data(f'phase/{seq}/{phase}/strings/{entry}/bytes.bin')[:len(raw)]==raw,'Actual duplicated NULinclusive bytes');counts['original_string_byteflows']+=1
      else:counts['original_null_descriptor_constructors']+=1
     for owner in allocation_calls:
      if 'binding'not in owner:continue
      binding=owner['binding'];mi=bindings.index(binding);meta=words(reader.data(f'phase/{seq}/{phase}/mfc/{mi}/meta.bin'),0,8);need(meta[:5]==tuple(binding[k]for k in('root','CALL_pc','requested_size','object','publication'))and meta[5:]==(owner['pointer'],owner['capacity'],mi),'Exact actual original MFC object typed owner/publication');need(machine.bytes(binding['publication'],4)==struct.pack('<I',owner['pointer']),'Source literal MFC object publication');need(machine.bytes(owner['pointer'],owner['capacity'])==reader.data(f'phase/{seq}/{phase}/mfc/{mi}/bytes.bin'),'Every actual owned MFC byte from initial BEFORE and source writes, including untouched padding');counts['actual_MFC_source_owned_byteflows']+=1
     callback=lookup[entry]['registration']['callback'];frame=machine.reg('esp');need(machine.bytes(frame,4)==struct.pack('<I',0x5ac124)and machine.bytes(frame+4,4)==struct.pack('<I',callback),'Original BEFORE-derived genuine provider frame and literal callback')
     for p in PAGES:
      if p==0x20001000:continue
      need(machine.memory[p]==after[p],'Whole constructor game page '+hex(p)+' at root '+hex(entry));counts['whole_nonstack_page_checks']+=1
     # Source provider return is outside this prefix receipt. Whole stack/API
     # effects remain observed and must be compared by the provider lane.
     begin,next_,capacity,mode=words(b,290928,4);seen.append(callback);need(mode==1 and next_-begin==4*len(seen)and capacity>=4*len(seen),'Actual registry append count/capacity')
     need(words(b,290944,len(seen))==tuple(seen),'Exact source literal callback order in actual vector')
     if entry==0x4c58c0:
      need(machine.fp_depth==0 and len(machine.FP_PCs)==26,'Exact reached default-zero FP path')
      fx,env=m.proj(machine.state);need(m.hardwarefx(fx)==b[628:1140],'BEFORE-only exact zero raw80/status/TOP/CW/full hardware FX');need(env==b[2192:2220],'Literal final FP metadata and full original ENV')
      counts['BEFORE_only_zero_FP_checks']+=1;counts['reached_zero_FP_instructions']+=len(machine.FP_PCs)
     rows.append(dict(sequence=seq,phase=phase,entry=entry,callback=callback,provider_frame=frame,source_instructions=len(machine.PCs),source_accesses=len(machine.accesses),FP_PC_sequence=machine.FP_PCs));counts['constructor_prefixes']+=1
   for module in (m,):
    for p,h in module.PINS.items():pin(p,h)
   for p in (ROOT/'tools/m4-onexit-review/provider_model.py',ROOT/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py',ROOT/'tools/m4-crt-locale-batch-model-review/batch.py',ROOT/'reports/m4-onexit-source/game-callbacks-r2/report.json',ROOT/'reports/m4-onexit-source/game-callbacks-r2/callbacks.json',Path(__file__)):pin(p)
   passed=True
  finally:reader.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'prefixes.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'prefixes.json');report=dict(passed=passed,scope='Actual original game constructor prefix from complete original BEFORE; all34 nonstack pages, literal callback CALL/order, six exact default-zero x87 paths. Provider stack/volatile-return effects remain a separate proof.',counts=dict(counts),source_AF_representatives='Exact sealed callback zero choices; actual original undefined flags remain retained observations',AFTER_machine_seed=False,AFTER_numeric_oracle_used=False,whole_stack_compared=False,original_heap_padding_modeled=True,actual_MFC_malloc_calls=35*6 if passed else counts['actual_MFC_source_owned_byteflows'],mode1_malloc_fact_scope='True original HeapAlloc typed result/rounded request supplies the admitted malloc scalar only; literal strdup/strlen/strcpy byteflow computed from source BEFORE. Each genuine HeapAlloc initial full backing is admitted as an actual API BEFORE result; all MFC unwritten padding is carried and compared literally.',initializer_credit=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])

