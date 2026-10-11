"""Archive-free PE ownership/checkpoint controls on the real owned-span reader."""
from pathlib import Path
import copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name;assert not out.exists();pins={};checks=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h; pins[str(p)]=v;return p
 def load(name,p):
  sp=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
 helper=load('current138_memory_controls_widget',R/'tools/m4-joint-startup138/persistent_widgets_v4.py')
 pin(helper.GAME_OWNERSHIP.__file__)
 sys.path.insert(0,str(R/'tools/m4-crt-locale-batch-model-review'));import batch
 pin(batch.__file__);pin(batch.I.__file__)
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 pin(R/'tools/analysis/pe.py');pe=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 class Machine(batch.OwnedMachine):
  def projected_cpu(self):return [0]*10
  def word(self,offset):return struct.unpack_from('<I',self.state,offset)[0]
 def model():
  m=Machine.__new__(Machine);m.memory={}
  for base,extent,offset,raw_size in helper.GAME_OWNERSHIP.mapped_regions(pe):
   if base!=0x9a2000:m.memory[base]=bytearray(pe.data[offset:offset+raw_size]+bytes(extent-raw_size))
  m.memory[0x20001000]=bytearray(4096);m.memory[0x7ffde000]=bytearray(4096)
  for offset,value in((0,0xffffffff),(4,0x20002000),(8,0x20001000),(0x18,0x7ffde000)):struct.pack_into('<I',m.memory[0x7ffde000],offset,value)
  for page in(0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000):m.memory[page]=bytearray(4096)
  m.state=bytearray(3504);struct.pack_into('<I',m.state,2168,0x7ffde000);m.fx=bytes(512)
  return m
 def refused(label,fn):
  try:fn()
  except ValueError:checks.append(dict(label=label,refused=True));return
  raise AssertionError(label+' was not refused')
 m=model();refused('Historical missing resource owner refused',lambda:m.bytes(0x9a2000,0x53000))
 old={p:bytes(v)for p,v in m.memory.items()};m._source_game_ownership=helper.admit_game_regions(m,pe)
 assert all(bytes(m.memory[p])==v for p,v in old.items())
 assert m._source_game_ownership['added']==[dict(address=0x9a2000,bytes=0x53000,sha256=hashlib.sha256(m.bytes(0x9a2000,0x53000)).hexdigest(),region_base=0x9a2000,region_extent=0x53000,physical_raw_offset=pe.sections[-1]['raw_offset'],physical_raw_size=0x52600,source='Own physical PE raw bytes plus loader-defined zero tail')]
 assert m.bytes(0x9a2000,0x52600)==pe.data[pe.sections[-1]['raw_offset']:pe.sections[-1]['raw_offset']+0x52600]
 assert m.bytes(0x9f4600,0xa00)==bytes(0xa00)
 checks.append(dict(label='Complete physical resource raw bytes plus exact zero tail; all existing ownership bytes preserved',passed=True))
 refused('Repeated ownership admission refused',lambda:helper.admit_game_regions(m,pe))
 n=model();n.memory[0x9a3000]=bytearray(b'\xa7'*4096);n._source_game_ownership=helper.admit_game_regions(n,pe)
 assert n.bytes(0x9a3000,4096)==b'\xa7'*4096
 assert [(x['address'],x['bytes'])for x in n._source_game_ownership['added']]==[(0x9a2000,4096),(0x9a4000,0x51000)]
 checks.append(dict(label='Existing interior source span retained and uncovered ownership partitioned exactly',passed=True))
 n=model();n.memory[0x5e1000]=bytearray(b'\xa7'*4096)
 refused('Inconsistent existing source aliases refused by actual OwnedMachine reader',lambda:helper.admit_game_regions(n,pe))
 class Archive:
  def __init__(self,values):self.values=values;self.entries=values
  def data(self,name):return self.values[name]
 prefix='case/'
 values={prefix+'State.bin':bytes(m.state),prefix+'CPU.bin':bytes(40),prefix+'FX.bin':m.fx,
  prefix+'stack.bin':m.bytes(0x20001000,4096),prefix+'TIB.bin':struct.pack('<5I',0x7ffde000,0xffffffff,0x20002000,0x20001000,0x7ffde000)}
 for base,extent in m._source_game_ownership['regions']:values[prefix+f'game-region-{base}.bin']=m.bytes(base,extent)
 for page in(0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000):values[prefix+f'provider-source-page-{page}.bin']=m.bytes(page,4096)
 proof=helper.whole_checkpoint(m,Archive(values),prefix);assert len(proof['Game_regions'])==5
 checks.append(dict(label='Unchanged entire five-region checkpoint equality retained',passed=True))
 bad=dict(values);b=bytearray(bad[prefix+'game-region-10035200.bin']);b[-1]^=1;bad[prefix+'game-region-10035200.bin']=bytes(b)
 refused('Resource zero-tail endpoint corruption refused; no source seed',lambda:helper.whole_checkpoint(m,Archive(bad),prefix))
 bad=dict(values);bad[prefix+'game-region-10035200.bin']=bad[prefix+'game-region-10035200.bin'][:-4096]
 refused('Mapped resource extent shortening refused',lambda:helper.whole_checkpoint(m,Archive(bad),prefix))
 bad=dict(values);bad[prefix+'game-region-16777216.bin']=bytes(4096)
 refused('Extra unowned Game region refused',lambda:helper.whole_checkpoint(m,Archive(bad),prefix))
 assert all(bytes(m.memory[p])==v for p,v in old.items())
 pin(R/'reports/m4-joint-startup138-source/preparation-r6/report.json','846b67baf2979963a7e0d50bf81180b58880a443a3c7b8aa1a55346c1ae7483a');pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Narrow archive-free PE-loader ownership and real OwnedMachine/whole-checkpoint controls; no source/native complete138 equivalence',
  initializer_credit=0,canonical_reader_opened=False,native_execution_performed=False,complete138_source_execution=False,
  checks=checks,source_derived_resource_ownership=m._source_game_ownership,files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),checks=len(checks))))
if __name__=='__main__':main(sys.argv[1])
