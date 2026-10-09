"""Original-only MFC integer model and explicit named-import projection.

The accepted source engine executes all 23 new instructions literally. This
subclass records MFC reads and returns only the two loader-bound named import
addresses after preserving the physical raw source ledger. It does not allocate,
free, use host libc, or manufacture a Windows API result.
"""
from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
_spec=importlib.util.spec_from_file_location('mfc_accepted_strings_model',ROOT/'tools/m4-strings-review/provider_model.py')
strings=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(strings)
I=strings.I
class Machine(strings.Machine):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.mfc_import_reads=[]
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc
  result=super().read(address,size,domain,pc)
  if domain=='source'and size==4:
   expected={(0x5f401ea1,0x5f49814c):(0x78001498,0x780012b3),(0x5f401786,0x5f498148):(0x7800138a,0x78001390)}.get((original_pc,address))
   if expected:
    raw,target=expected;I.need(result==raw,'Exact MFC named source import relocation')
    self.mfc_import_reads.append((original_pc,address,result,target,size));return target
  return result
def source_program(path):
 data=json.loads(Path(path).read_bytes())
 I.need(data['schema']=='mw34-mfc-independent-provider-interface-v1'and not data['AFTER_machine_seed'],'Bound physical MFC source-only interface')
 return {r['pc']:r for r in data['instructions']},{int(pc):tuple(v)for pc,v in data['callbacks_by_original_PC'].items()}
def merge(program,callbacks,path):
 new,undef=source_program(path);I.need(not(set(program)&set(new)),'Additive original MFC PC domain')
 combined=dict(program);combined.update(new);result=dict(callbacks)
 for pc,offsets in undef.items():I.need(pc not in result or result[pc]==offsets,'One exact undefined callback');result[pc]=offsets
 return combined,result
