"""Bounded paired original/native54 initialization data and numeric contract.

Every branch retains its genuine bytes. Exact typed IAT identities and one
source-derived indeterminate representation byte are relations, not edits.
Real32 provider/API volatile registers and scratch-stack contents are retained
as observations; strict native source State/stack proof is a separate gate.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000)
IATS={0x5bb4fc:(0x780c10f0,0x1df59c),0x5bb52c:(0x78004a36,0x1decb0),0x5bb530:(0x78002fe5,0x1deca2),0x5bb6dc:(None,0x1df20c)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,s):
 if not x:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Frozen paired input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable paired input');PINS[str(p)]=v;return p
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def equal(a,b,s):need(a==b,s)
def delta(a,b):return [dict(offset=i,original=x,native=y)for i,(x,y)in enumerate(zip(a,b))if x!=y]
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;need(not out.exists(),'Fresh paired policy');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];field_rows=[]
 try:
  original_report=json.loads(pin(ROOT/'reports/m4-onexit-source/original-run-r5/report.json','dbf50bb8d64645565b7b1f7ff6a622eae4257cb8fae5a188a06cb329b907143a').read_bytes());need(original_report['passed'],'Corrected actual original run')
  gates={'original-game-source-r4':'0c346bbc0c5fd2d33a39eb0db6f68a78ce057fe28dd6f53c14fca5bf036a9597','native-game-prefix-r3':'b157c5ce5761ec9e1ab9ffdc9f6d616b667ac46550dbf4f283bb46aff040c0c5','native-game-prefix-r4':'28a89032ec734f0432ea304144df626f61d67018dcf5cdb502ab57dc5383cefa','connected-native-source-r2':'c2f439bb528cdd8b660908909b835fed638bfc0190ba55cfd1cc89ee7e997188','field-analysis-r1':'bd127e908fe3056a986f3977e35e86bd1084086fb92a5e997bc36c49bdd9dfa0','zero-fsqrt-hardware-r1':'4bb43cc941d3925fda389109124da3999950bbb730c6da1f481edeeff3b18f0a'}
  for n,h in gates.items():need(json.loads(pin(ROOT/'reports/m4-onexit-source'/n/'report.json',h).read_bytes())['passed'],'Admitted source gate '+n)
  prep=json.loads(pin(ROOT/'reports/m4-onexit-source/original-preparation-r8/report.json','a70e53ed7b8867e514afc7342728cf549b740bd7d04de4b3a30657dd9f415476').read_bytes());need(prep['changed_input_pages'][0]['base']==0x5f4000 and not prep['source_code_changed'],'Correct raw/BSS provenance only')
  nr=pin(ROOT/'reports/m4-joint-startup54-root/execution-r6/report.json','796ed2ea41261b9949b6b1a12d963ce53d4d83bf4b0158c7f15559e3f4a9bafb');need(json.loads(nr.read_bytes())['passed'],'Current native run')
  D=load('paired_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('paired_old_numeric',ROOT/'tools/m4-joint-startup27-review/observe.py');m,_,_,_=J.models();G=load('paired_original_source',ROOT/'tools/m4-onexit-source/compare_original_game_v4.py');G.PINS=PINS
  roots={r['entry']:r['registration']['callback']for r in json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc').read_bytes())}
  order=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes())['selected_order'];ori=D.DirectSet(Path(original_report['original_capture']),pin)
  for level in ('O0','O2'):
   native=D.DirectSet(nr.parent/level/'transport.json',pin)
   for seq in range(6):
    expected_callbacks=[];values={}
    for phase,item in enumerate(order):
     a=ori.data(f'phase/{seq}/{phase}.bin');b=native.data(f'sequence-{seq}/phase-{phase}.bin');entry=item['entry'];equal(a[:32],b[:32],'Exact original/native sequence association/status');need(words(a,32)[0]==1 and words(b,32)[0]in(0,1),'Declared original/native service activity tag')
     observation=dict(level=level,sequence=seq,phase=phase,entry=entry,CPU_before_original_hex=a[36:76].hex(),CPU_before_native_hex=b[36:76].hex(),CPU_after_original_hex=a[76:116].hex(),CPU_after_native_hex=b[76:116].hex(),CPU_before_differences=delta(a[36:76],b[36:76]),CPU_after_differences=delta(a[76:116],b[76:116]),FX_before_differences=delta(a[116:628],b[116:628]),FX_after_differences=delta(a[628:1140],b[628:1140]),ENV_before_original_hex=a[2164:2192].hex(),ENV_before_native_hex=b[2164:2192].hex(),ENV_after_original_hex=a[2192:2220].hex(),ENV_after_native_hex=b[2192:2220].hex(),nonstack_pages=[])
     for side,co,fo,eo,mo,no in (('before',36,116,2164,2276,2276),('after',76,628,2192,121060,71908)):
      ca=words(a,co,10);cb=words(b,co,10)
      for index in (0,3,4,5,6,7,9):equal(ca[index],cb[index],'Exact EAX/nonvolatile/ESP/return-PC '+side);counts['exact_CPU_field_checks']+=1
      # ECX and flags are equal at every normal initializer return; retain
      # actual volatile outputs at SPI and its immediate caller input seam.
      spi_boundary=phase==(25 if side=='after' else 26)
      if not spi_boundary:
       equal(ca[1],cb[1],'ECX outside literal SPI volatile seam');equal(ca[8],cb[8],'EFLAGS outside literal SPI volatile seam');counts['additional_CPU_field_checks']+=2
      # Physical MXCSR_MASK is a CPU capability descriptor. It is imported
      # only by hardwarefx under the frozen accepted numeric policy.
      equal(m.hardwarefx(b[fo:fo+512]),a[fo:fo+512],'Whole hardware FX projection: CW/TOP/status/raw80/SIMD');counts['whole_hardware_FX_projection_checks']+=1
      equal(a[eo:eo+12],b[eo:eo+12],'Exact x87 control/status/tag and reserved words');counts['exact_x87_environment_head_checks']+=1
      metadata_boundary=phase in ((25,26,27)if side=='after' else(26,27,28))
      if not metadata_boundary:equal(a[eo:eo+28],b[eo:eo+28],'Exact complete ENV outside finite SPI metadata interval');counts['whole_ENV_checks']+=1
      for i,page in enumerate(PAGES):
       original=a[mo+i*4096:mo+(i+1)*4096];actual=b[no+i*4096:no+(i+1)*4096]if i<17 else native.data(f'sequence-{seq}/phase-{phase}-{side}-page-{page}.bin')
       if page==0x20001000:continue
       differences=delta(original,actual);declared=set()
       if page==0x5bb000:
        for address,(target,raw)in IATS.items():
         off=address&4095;need(words(actual,off)[0]==raw,'Pinned native raw owning-IAT identity');need(target is None or words(original,off)[0]==target,'Actual32 owning-IAT target')
         if target is None:need(words(original,off)[0]!=raw and words(original,off)[0]!=0,'Actual32 SPI worker shim target')
         declared.update(range(off,off+4));counts['owning_IAT_identity_checks']+=1
       if page==0x609000:
        field=0x9e8
        if phase==26:
         if side=='before':
          values={'original_before':original[field],'native_before':actual[field],'original_derived':(words(a,36,10)[1]>>24)&255,'native_derived':(words(b,36,10)[1]>>24)&255}
         else:
          equal(original[field],values['original_derived'],'Literal original PUSH ECX/local highbyte derivation');equal(actual[field],values['native_derived'],'Literal native PUSH ECX/local highbyte derivation')
          field_rows.append(dict(level=level,sequence=seq,address=0x6099e8,write_PC=0x49d5d5,constructor_before_ECX_original=words(a,36,10)[1],constructor_before_ECX_native=words(b,36,10)[1],original_after=original[field],native_after=actual[field],**values));counts['own_branch_field_derivations']+=2
        if phase>26 or(phase==26 and side=='after'):
         equal(original[field],values['original_derived'],'Original indeterminate field carries');equal(actual[field],values['native_derived'],'Native indeterminate field carries');declared.add(field);counts['indeterminate_field_carry_checks']+=2
       need(all(x['offset']in declared for x in differences),'No undeclared paired byte difference '+str((level,seq,phase,side,hex(page),differences[:10])))
       # Preserve physical observations including exact raw unequal bytes.
       observation['nonstack_pages'].append(dict(side=side,page=page,original_sha256=hashlib.sha256(original).hexdigest(),native_sha256=hashlib.sha256(actual).hexdigest(),differences=differences));counts['whole_nonstack_page_relations']+=1
     if entry in roots:
      callback=roots[entry];expected_callbacks.append(callback);need(words(a,76)[0]==callback and words(b,76)[0]==callback,'Exact original/native onexit callback return')
      registry=native.data(f'sequence-{seq}/phase-{phase}-after-registry.bin');summary=struct.unpack('<32Q',registry);need(summary[9]==len(expected_callbacks) and summary[7]-summary[6]==4*len(expected_callbacks) and summary[8]>=4*len(expected_callbacks),'Native actual owned registry extent/count; exact contents proven by persistent source gate')
      need(words(a,241792,len(expected_callbacks))==tuple(expected_callbacks),'Original carried callback vector');counts['registration_return_order_checks']+=1
     rows.append(observation);counts['paired_phases']+=1
    equal(ori.data(f'cleanup/{seq}/registry.bin'),struct.pack('<26I',*expected_callbacks),'Exact original complete callback vector');counts['paired54_sequences']+=1
   native.close()
  ori.close()
  for module in (J,m):
   for p,h in getattr(module,'PINS',{}).items():pin(p,h if isinstance(h,str)else h['sha256'])
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for label,value in (('paired-observations.json',rows),('indeterminate-field.json',field_rows)):
   (out/label).write_text(json.dumps(value,indent=2)+'\n');pin(out/label)
  report=dict(passed=passed,scope='Bounded selected54 initialization relation against fresh genuine original54: entire28 nonstack pages, callback return/order, complete numeric FX projection and finite API metadata seams, backed by strict persistent native source State/CPU/FX/ENV/full29pages',counts=dict(counts),paired_initialization_data_contract=passed,original_record_bytes=242304,native_record_bytes=159716,original_and_native_bytes_modified=False,blanket_page_mask=False,owning_IAT_projection_addresses=list(IATS),indeterminate_relation_address=0x6099e8,indeterminate_relation='Each branch literal PUSH ECX/MOV AL,[ESP+3] highbyte independently derived from its genuine constructor BEFORE; raw values retained and exact carry checked. Known selected suffix and recovered UI/container/cleanup consumers do not read byte0; whole-game dynamic aliases are excluded.',crossbranch_CPU_contract='EAX, nonvolatile GPRs, ESP, returnPC exact at every phase. ECX/EFLAGS exact outside one finite SPI return/immediate input seam. EDX and real32 API volatile outputs retained as observed typed boundary state; strict native full CPU/State separately modeled, no whole original API volatile equality claimed.',crossbranch_numeric_contract='Frozen hardwarefx capability-mask projection only; exact CW/TOP/status/raw80/SIMD all phases. Exact ENV head throughout; actual SPI FIP/FOP/FDP metadata retained on finite phases25..27 until next original/literal source FP overwrites it. Exact complete ENV otherwise.',original_provider_scratch_stack_crossbranch_equal=False,native_full_stack_source_proven=True,whole_game_liveness_proven=False,FSQRT_scope='Exact measured default-zero constructor inputs in six CW/TOP cases; broader nonzero/denormal Remill behavior excluded.',initializers_added_by_this_report=0,whole_M4_complete=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])

