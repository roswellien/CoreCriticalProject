"""Bounded original-only string footprint calibration, without native/original execution."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-strings-review'/name;need(not out.exists(),'Fresh source model calibration');out.mkdir(parents=True);pins={};rows=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Frozen model input '+str(p));pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  proof=json.loads(pin(ROOT/'reports/m4-strings-review/interface-r1/report.json','94942936381f5cea0052361b9ecc11300183e76fbf60084e4573859a1b8c6f34').read_bytes());need(proof['passed'],'Original-only interface audit')
  S=load('calibrated_string_source_model',ROOT/'tools/m4-strings-review/provider_model.py');program,callbacks=S.source_program(pin(proof['instruction_contracts'],proof['instruction_contracts_sha256']));I=S.I
  def machine(source,body,arguments):
   state=bytearray(3504)
   for n,reg in enumerate(I.REG):struct.pack_into('<I',state,I.REG[reg],0x41320100+n*0x10101)
   struct.pack_into('<I',state,I.REG['esp'],0x20001800);struct.pack_into('<I',state,2472,0x410a80)
   for key,value in dict(CF=1,PF=0,AF=1,ZF=0,SF=1,DF=0,OF=1).items():state[I.FLAGS[key]]=value
   m=S.Machine(state,bytes(512),bytes(40),{0x20001000:bytes(4096),0x34000000:source,0x35000000:bytes([0xCD])*4096},program=program,callbacks=callbacks)
   for index,arg in enumerate(arguments):m.store_bytes(0x20001800+4*index,struct.pack('<I',arg))
   before=bytes(m.state);m.invoke_external(body,0xffffff01);return m,before
  for alignment in range(4):
   for length in range(33):
    for high in(False,True):
     start=0x34000100+alignment;payload=bytes((0x80 if high else 0x41)+(n%31)for n in range(length))+b'\0';source=bytearray([0xA9]*4096);source[start-0x34000000:start-0x34000000+len(payload)]=payload
     length_model,length_before=machine(source,0x78002f32,(start,));need(length_model.reg('eax')==length,'Exact literal computedstrlen');need(length_model.reg('esp')==0x20001800 and length_model.reg('esi')==struct.unpack_from('<I',length_before,I.REG['esi'])[0]and length_model.reg('edi')==struct.unpack_from('<I',length_before,I.REG['edi'])[0],'Literalstrlen externalRET/unchangednonvolatiles')
     expected_end=start+len(payload)if start%4 and len(payload)<=4-start%4 else(start+len(payload)+3)&~3
     lf=S.footprint(length_model.string_observations,start,len(payload));need(lf['read_end']==expected_end,'Actual literalalignedDWORD read extends through terminalword')
     destination=0x35000103;copy_model,copy_before=machine(source,0x78002fab,(destination,start));need(copy_model.reg('eax')==destination and copy_model.bytes(destination,len(payload))==payload,'Literalstrcpy returnsdestandcopiesNUL');need(copy_model.bytes(destination+len(payload),8)==bytes([0xCD])*8,'No sourcecopywritesbeyondNUL');need(copy_model.reg('edi')==struct.unpack_from('<I',copy_before,I.REG['edi'])[0],'Literalstrcpy preservesEDIthroughgenuinePUSH/POP')
     cf=S.footprint(copy_model.string_observations,start,len(payload),destination);need(cf['read_end']==expected_end and cf['committed_write_bytes']==len(payload),'Exact sourcecopyalignedread/committedwritefootprints')
     rows.append(dict(alignment=alignment,length=length,high_bytes=high,strlen=lf,strcpy=cf))
  # The local NULL branch is physically decoded and modeled, but unsupported
  # selected-family native admission must refuse it; this gives it no credit.
  null,before=machine(bytes(4096),0x78010a6d,(0,));need(null.reg('eax')==0 and not any(pc in(0x78002f32,0x780012b3,0x78002fab)for pc in null.PCs),'LiteralNULLbranchreturnszerobeforestrlen/malloc/strcpy')
  for module in list(sys.modules.values()):
   path=getattr(module,'__file__',None)
   if path:
    path=Path(path).resolve()
    if path.is_relative_to(ROOT/'tools')and path.is_file():pin(path)
  pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'computed-footprints.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'computed-footprints.json');report=dict(passed=passed,scope='Original-only literal source model calibration over264 BEFORE input domains:4sourcealignments,33NULpositions,low/highnonzero bytes; no original/native/APIexecution',computed_strlen_runs=len(rows),computed_strcpy_runs=len(rows),local_null_branch_model_only=True,native_null_input_admitted=False,native_alloc_failure_admitted=False,AFTER_machine_seed=False,host_strlen_strcpy_used=False,initializer_credit=0,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),cases=len(rows))))
if __name__=='__main__':main(sys.argv[1])
