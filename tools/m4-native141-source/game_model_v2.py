"""Additive constructor model with BEFORE import binding and shift timing."""
from pathlib import Path
import importlib.util,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_source_frozen_parent',R/'tools/m4-native141-source/game_model.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;ActualAPIs=P.ActualAPIs;source_program=P.source_program
class Machine(P.Machine):
 def read(self,address,size=4,domain='source',pc=None):
  site=self.word(2472)if pc is None else pc
  fact=self.constructor_imports.get((site,address))if self.constructor_active and domain=='source'else None
  if fact is None:return super().read(address,size,domain,pc)
  # Read the exact branch-owned raw DWORD before any inherited canonical-IAT
  # projection. Older native-only raw admissions must not inspect it first.
  value=I.Machine.read(self,address,size,domain,pc)
  I.need(size==4 and value==fact['raw']and fact['target']and fact.get('owning_named_input',False),'Exact typed own-BEFORE named import observation')
  self.import_projections.append((14,site,address,value,fact['target'],0,0,0));return fact['target']
 def step(self):
  row=self.program.get(self.cursor);active=self.constructor_active
  oldcount=None
  if active and row is not None and row['mnemonic']in('sar','shr','shl'):
   oldcount=self.operand(row['decoded_operands'][1])&31
  result=super().step()
  if oldcount is not None:
   # P.step samples count after a shift; a register destination may be CL.
   # Restore the precise architectural lifetime from the incoming count.
   pc=row['pc']
   if oldcount:
    for name in('CF','PF','ZF','SF'):self.arch_undefined.pop(name,None)
    self.arch_undefined['AF']=pc
    if oldcount==1:self.arch_undefined.pop('OF',None)
    else:self.arch_undefined['OF']=pc
  return result
def from_original_before(domain):
 """Synthesize an internal State from actual architecture, never an AFTER."""
 cpu=bytes.fromhex(domain['BEFORE_CPU_hex']);I.need(len(cpu)==40,'Whole actual original CPU40 BEFORE');values=struct.unpack('<10I',cpu)
 I.need(domain['branch']=='original'and domain['original_State_observed']is False and 'BEFORE_State_hex'not in domain,'Original has no observed Remill State')
 state=bytearray(3504)
 for name,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),values[:8]):struct.pack_into('<I',state,I.REG[name],value)
 for name,bit in BITS.items():state[I.FLAGS[name]]=(values[8]>>bit)&1
 struct.pack_into('<I',state,2472,values[9])
 bases=domain['BEFORE_segment_bases'];I.need(set(bases)==set(I.BASE),'Every actual source segment base declared')
 for name,offset in I.BASE.items():struct.pack_into('<I',state,offset,bases[name])
 I.need(bases['ds']==bases['es']==bases['ss']==0 and bases['fs']in map(int,domain['BEFORE_memory']),'Actual flat source and coherent own TIB input')
 return bytes(state)
