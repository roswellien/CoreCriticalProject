"""Validate genuine finite-domain hardware observations; never predict FCOS results."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-cosine-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable identity');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def hword(b,o=0):return struct.unpack_from('<H',b,o)[0]
def main(path,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh additive validation');out.mkdir(parents=True);passed=False;bundle=None;counts=collections.Counter();observed=[]
 try:
  execution=read(path,digest);need(execution['passed'],'Genuine fresh execution');build=read(execution['build_path'],execution['build_sha256']);need(build['passed']and build['sequences']==build['phases']==6 and build['roots']==1 and build['record_bytes']==356992,'Finite genuine six-case worker');pin(build['worker'],build['worker_sha256'])
  prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['source_instruction_rows']==19 and prep['source_instruction_bytes']==110 and not prep['predicted_outputs_supplied_to_execution']and not prep['host_cos_expected_output_used']and not prep['source_after_seed'],'Exact physical finite source; no predicted results')
  for p,h in prep['files'].items():pin(p,h)
  pack=pin(Path(build['preparation'])/'pages.bin',prep['pack_sha256']).read_bytes();need(pack[:8]==b'MW4J124P','Source page pack');packed={}
  for i in range(words(pack,8)[0]):
   o=12+i*4104;page,permission=words(pack,o,2);packed[page]=(permission,pack[o+8:o+4104])
  need(packed[0x5e8000][0]==2 and packed[0x5c9000][0]==0,'Physical writable output and immutable input source page')
  pages=prep['observed_pages'];need(len(pages)==43,'Fixed full43-page geometry')
  spec=importlib.util.spec_from_file_location('cosine_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));direct=importlib.util.module_from_spec(spec);spec.loader.exec_module(direct);bundle=direct.DirectSet(Path(execution['original_capture']),pin)
  pin(__file__);pin(sys.executable)
  need(bundle.data('COMPLETE.txt')==b'complete','Successful physical writer completion')
  scalar={0x5e886c:0x7f7fffff,0x5e8870:0x40400000,0x5e8874:0x40c00000,0x5e8878:0x3f800000,0x5e887c:0,0x5e888c:0x42480000,0x5e8890:0}
  FP=[(0x4b6500,0x4b6506,0x4b6546,0x5c93d0,0x5e8880),(0x4b654c,0x4b6552,0x4b6554,0x5c93d8,0x5e8884),(0x4b655a,0x4b6560,0x4b6562,0x5c93e0,0x5e8888)]
  for sequence,(repeat,cw,top)in enumerate(prep['source_CW_TOP_cases']):
   data=bundle.data(f'phase/{sequence}/0.bin');need(len(data)==356992 and words(data,0,9)==(sequence,repeat,0,0x5e0160,0x4b64f0,cw,top,0,1),'Actual successful original source phase and full host restoration')
   before,after=words(data,36,10),words(data,76,10);need(before[4]==0x20001800 and before[9]==0x4b64f0 and after[0]==0 and after[4]==before[4]+4 and after[9]==0x410a80,'Source XOR EAX and RET');need(all(before[j]==after[j]for j in (1,2,3,5,6,7)),'Source callee-saved/untouched registers')
   need((after[8]&~0x8d5)==(before[8]&~0x8d5)and(after[8]&0x8c5)==0x44,'Source architectural XOR flags; AF undefined explicitly excluded')
   fx0,fx1=data[116:628],data[628:1140];env0,env1=data[2164:2192],data[2192:2220]
   need(hword(fx0)==hword(fx1)==hword(env0)==hword(env1)==cw,'Actual carried source CW')
   need(hword(fx0,2)>>11&7==hword(fx1,2)>>11&7==top and hword(env0,4)>>11&7==hword(env1,4)>>11&7==top,'Three literal FLD/FCOS/FSTP preserve actual TOP')
   need(fx0[4]==fx1[4]==0 and hword(env0,8)==hword(env1,8)==0xffff,'Empty actual x87 stack before/after')
   need(not(hword(fx1,2)&0x400)and not(hword(env1,4)&0x400),'Actual default finite FCOS input range admitted by C2 clear')
   need(fx0[24:]==fx1[24:],'Actual MXCSR/XMM/opaque non-x87 FX bytes conserved')
   need(words(env1,12)[0]==0x4b6562 and words(env1,20)[0]==0x5e8888,'Actual last literal x87 store instruction/data attribution')
   need(data[1140:1652]==data[1652:2164] and data[2220:2248]==data[2248:2276],'Actual full host FP/ENV restoration')
   def image(side,address,n):
    o=(2276 if side=='before'else 178404)+pages.index(address&~4095)*4096+(address&4095);return data[o:o+n]
   inputs=[];outputs=[]
   for item,(loadpc,cospc,storepc,address,destination)in zip(prep['source_default_inputs'],FP):
    raw=bytes.fromhex(item['bytes_hex']);need(image('before',address,8)==image('after',address,8)==raw==packed[address&~4095][1][address&4095:(address&4095)+8],'Genuine untouched physical double input carried in full source page')
    inputs.append(dict(address=address,bytes_hex=raw.hex(),F64=struct.unpack('<d',raw)[0],FLD_pc=loadpc,FCOS_pc=cospc,FSTP_pc=storepc));v=image('after',destination,4);outputs.append(dict(address=destination,bytes_hex=v.hex(),F32=struct.unpack('<f',v)[0],source_FSTP_pc=storepc,observed_only=True));counts['actual_FCOS_input_output_occurrences']+=1
   for address,value in scalar.items():need(words(image('after',address,4))[0]==value,'Exact literal scalar MOV source effect');counts['literal_scalar_stores']+=1
   for page in pages:
    a=image('before',page,4096);b=image('after',page,4096)
    if page==0x5e8000:
     expected=bytearray(a)
     for address,value in scalar.items():struct.pack_into('<I',expected,address&4095,value)
     for output in outputs:expected[output['address']&4095:(output['address']&4095)+4]=bytes.fromhex(output['bytes_hex'])
     need(b==expected,'Full output source page effects only at seven scalar and three observed FP slots')
    else:need(a==b,'Complete unrelated source page conservation '+hex(page))
    counts['whole_page_endpoint_relations']+=2
   for prefix in ('fs-event','lockit','nullfree','vtable'):
    stem=f'phase/{sequence}/0/';need(words(bundle.data(stem+prefix+'-count.bin'))==(0,),'No unrelated source observer invoked')
   need(bundle.data(f'cleanup/{sequence}/registry.bin')==b'','Actual no source callback registered')
   counts['actual_root_phases']+=1;counts['full_CPU_endpoints']+=2;counts['full_FX512_endpoints']+=2;counts['full_ENV28_endpoints']+=2;counts['full_host_restoration_relations']+=1
   observed.append(dict(sequence=sequence,repeat=repeat,CW=cw,TOP=top,BEFORE_CPU=list(before),AFTER_CPU=list(after),BEFORE_FX512_hex=fx0.hex(),AFTER_FX512_hex=fx1.hex(),BEFORE_ENV28_hex=env0.hex(),AFTER_ENV28_hex=env1.hex(),inputs=inputs,outputs=outputs,x87_status_before=hword(fx0,2),x87_status_after=hword(fx1,2),last_source_x87_store_pc=words(env1,12)[0],last_source_x87_data_address=words(env1,20)[0],XOR_AF_architecturally_undefined=True,host_restored=True))
  need(counts['actual_root_phases']==6 and counts['actual_FCOS_input_output_occurrences']==18 and counts['literal_scalar_stores']==42 and counts['whole_page_endpoint_relations']==516,'Exact complete six-case extent');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if bundle is not None:bundle.close();bundle=None
  artifact=out/'actual-cosine-endpoints.json';artifact.write_text(json.dumps(observed,indent=2)+'\n');pin(artifact)
  report=dict(passed=passed,scope='Genuine six-case finite input FCOS root hardware endpoints and full memory effects; observed FSTP values are not predicted/model seeds',execution_path=str(path),execution_sha256=digest,build_path=str(execution['build_path'])if 'execution'in locals()else None,counts=dict(counts),observations=str(artifact),observations_sha256=sha(artifact),files=PINS,source_after_seed=False,host_cos_expected_output_used=False,predicted_FP_outputs_used_as_expected=False,source_native_equivalence=False,initializer_credit=False,inherited_capture_reader_opened=False,reader_closed=True)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,counts=dict(counts),sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
