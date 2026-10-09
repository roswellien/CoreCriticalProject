"""Original-only literal strlen/strcpy/strdup source closure and byte footprints.

The accepted interpreter already implements every new integer instruction. The
model records every actual literal byte/word/DWORD access, including reads after
the first NUL, and never substitutes a host string routine or candidate AFTER.
"""
from pathlib import Path
import copy,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_model as prior
I=prior.I
class Machine(prior.Machine):
 """Same source engine; dedicated string footprint observations only."""
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.string_observations=[]
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc;result=super().read(address,size,domain,pc)
  if domain=='source'and original_pc in self.string_program:self.string_observations.append((original_pc,address,result,size,0))
  return result
 def write(self,address,value,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc;super().write(address,value,size,domain,pc)
  if domain=='source'and original_pc in self.string_program:self.string_observations.append((original_pc,address,value&((1<<(size*8))-1),size,1))
 @property
 def string_program(self):return {pc for pc in self.program if 0x78002f32<=pc<=0x78002fe3 or 0x78003664<=pc<=0x780036bd or 0x78010a6d<=pc<=0x78010a97}
def source_program(path):
 q=json.loads(Path(path).read_bytes());I.need(q['schema']=='mw34-strings-independent-provider-interface-v1'and not q['AFTER_machine_seed'],'Original-only string source interface')
 return {r['pc']:r for r in q['instructions']},{int(pc):tuple(offsets)for pc,offsets in q['callbacks_by_original_PC'].items()}
def merged_program(path,accepted_path,accepted_callbacks):
 strings,callbacks=source_program(path);old,_=prior.source_program(accepted_path);I.need(not(set(strings)&set(old)),'Fresh string instructions preserve accepted provider rows')
 old.update(strings);combined=dict(accepted_callbacks)
 for pc,offsets in callbacks.items():I.need(pc not in combined or combined[pc]==offsets,'One source callback identity');combined[pc]=offsets
 return old,combined
def nul_extent(machine,pointer,maximum=1048576):
 """Declared BEFORE-only input extent; does not replace literal source reads."""
 I.need(pointer!=0 and 0<maximum<=1048576,'Nonnull bounded research string admission')
 raw=bytearray()
 for offset in range(maximum):
  value=machine.bytes(pointer+offset,1);raw.extend(value)
  if value==b'\0':return bytes(raw)
 raise ValueError('Unterminated input exceeds explicit string admission domain')
def footprint(observations,source,extent,destination=None):
 """Inspect computed literal reads/writes; values always come from the model."""
 reads=[r for r in observations if not r[4]and source<=r[1]<source+extent+4]
 writes=[r for r in observations if r[4]and destination is not None and destination<=r[1]<destination+extent]
 return dict(source=source,NUL_extent=extent,reads=reads,writes=writes,read_end=max((r[1]+r[3]for r in reads),default=source),committed_write_bytes=sum(r[3]for r in writes),AFTER_machine_seed=False)
