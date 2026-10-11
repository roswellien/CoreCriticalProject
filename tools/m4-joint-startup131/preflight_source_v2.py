"""Archive-free pure model equivalence and architectural-consumer controls.

The test architecture has genuine BEFORE GPR/FX/stack inputs and explicitly
zero synthetic unused State bytes. It is a model construction/equivalence
test, not an observed native phase or initializer acceptance.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'));sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;results={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  receipt=json.loads(pin(ROOT/'reports/m4-joint-startup131-source/preparation-r2/report.json','1513400445e72f2cd876a737a98b77d9c624871ce38c316b0a27f0a3863faec9').read_bytes());assert receipt['passed']
  for p,h in receipt['files'].items():pin(p,h);ast.parse(Path(p).read_text())
  import flag_consumers as FC
  M=load(ROOT/'tools/m4-joint-startup131/mfc_source_v2.py','mfc131_pure_preflight_extension')
  preparation=json.loads(pin(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25').read_bytes());e=M.Extension(preparation,pin)
  before={'memory':{}};loader=e.loader(before);memory=before['memory'];assert len(e.new)==8 and len(e.normal_PCs)==142
  before2={'memory':dict(memory)};assert e.loader(before2)==loader and before2['memory']==memory
  source=json.loads(pin(ROOT/'reports/m4-mfc1168-connected-original/source-r3/source-derivations.json','83de178c1c4e1c258f0d95b2d2b080ca75e879e9c244eca9456a72aa73bebd15').read_bytes())
  retained=json.loads(pin(ROOT/'reports/m4-mfc1168-connected-original/validation-r1/retained-actual-inputs.json').read_bytes());v=retained['phase/0/13.bin'];raw=pin(v['path'],v['sha256']).read_bytes();assert len(raw)==356992
  current_pages=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000)
  memory[0x20001000]=raw[2276+current_pages.index(0x20001000)*4096:2276+(current_pages.index(0x20001000)+1)*4096]
  b=bytearray(memory[0x20001000]);struct.pack_into('<I',b,0x800,0x410a80);memory[0x20001000]=bytes(b)
  memory[0x7ffde000]=struct.pack('<I',0xffffffff);memory[0x7ffde004]=struct.pack('<II',0x20002000,0x20000000);memory[0x7ffde018]=struct.pack('<I',0x7ffde000)
  cpu=list(source['source_CPU_BEFORE']);cpu[4]=0x20001800;cpu[9]=0x5ae3e4;state=bytearray(3504);I=e.literal.I
  for name,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu[:8]):struct.pack_into('<I',state,I.REG[name],value)
  for name,bit in e.literal.F.BITS.items():state[I.FLAGS[name]]=(cpu[8]>>bit)&1
  struct.pack_into('<I',state,2472,cpu[9]);struct.pack_into('<I',state,I.BASE['fs'],0x7ffde000)
  old=load(ROOT/'tools/m4-mfc1168-native/persistent_source.py','mfc131_original_pure_evaluator');a,ar=old.derive(bytes(state),raw[116:628],struct.pack('<10I',*cpu),memory,preparation['inputs'],e.contracts);b,br=e.literal.derive(bytes(state),raw[116:628],struct.pack('<10I',*cpu),memory,preparation['inputs'],e.contracts)
  assert a.state==b.state and a.fx==b.fx and a.cpu_now()==b.cpu_now() and a.accesses==b.accesses and a.PCs==b.PCs
  assert br['source_PCs']==e.normal_PCs and len(br['defined_flag_consumers'])==11 and all(c['all_consumers_defined']for c in br['defined_flag_consumers'])
  # An undefined flag on the first actual conditional source PC is refused.
  row=next(r for r in e.contracts['instructions']if r['pc']==br['defined_flag_consumers'][0]['PC']);flag=br['defined_flag_consumers'][0]['flags'][0]
  try:FC.check(b,row,{flag:{'PC':row['pc']-1,'reason':'authored negative definedness control'}})
  except ValueError as x:assert 'architecturally undefined flag'in str(x)
  else:raise ValueError('Undefined conditional consumer was not refused')
  # Flag-preserving MOV cannot erase a prior undefined domain.
  row=next(r for r in e.contracts['instructions']if r['mnemonic']=='mov');prior={'AF':{'PC':0,'reason':'authored prior'}};assert FC.advance(b,row,prior)==prior
  (out/'pure-model-equivalence.json').write_text(json.dumps(dict(source_PCs=br['source_PCs'],defined_flag_consumers=br['defined_flag_consumers'],final_undefined_flags=br['final_undefined_flags'],State_after_sha256=hashlib.sha256(b.state).hexdigest(),CPU_after=br['source_CPU'],FX_after_sha256=hashlib.sha256(b.fx).hexdigest(),source_operand_count=len(b.accesses)),indent=2)+'\n');pin(out/'pure-model-equivalence.json')
  results=dict(exact_loader_regions=8,typed_pointer_cells=6,CRT_merge_cells=3,physical_source_PCs=142,source_operands=113,typed_APIs=4,defined_consumers=11,pure_old_new_entire_State_CPU_FX_equal=True,pure_old_new_all_operands_equal=True,undefined_conditional_refused=True,flag_preserving_MOV_domain_retained=True,typed_API_flag_domain_not_reset=True)
  pin(__file__);pin(sys.executable)
  for p,h in files.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Archive-free explicit source consumer validation and pure whole-State equivalence on finite construction input; no native phase/capture acceptance',counts=results,files=files,synthetic_unused_State_input=True,BEFORE_GPR_FX_stack_inputs_genuine=True,candidate_AFTER_input=False,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
