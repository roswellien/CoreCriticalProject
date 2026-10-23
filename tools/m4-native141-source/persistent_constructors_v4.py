"""Prepared constructor dispatch in the existing persistent widget Machine.

No phase machine inputs are accepted. Shared responses retain all API indices,
heap aliases, generation counters, allocation lifetime and reverse cleanup.
"""
from pathlib import Path
import copy,importlib.util,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('persistent141_constructor_source',Path(__file__).with_name('game_model_v9.py'))
C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
I=C.I;ROOTS=C.ROOTS;G=C.G
begin_root=G.begin_root;complete_root=G.complete_root
PREPARATION=R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json'
def source_program():return C.source_program(PREPARATION)
def owner_role(m,a):
 raw=m.bytes(a['guest'],a['mapped'])
 I.need(a['live'] and 0<a['requested']<=a['extent']<=a['mapped'],'Whole carried live provider owner geometry')
 return dict(guest=a['guest'],requested=a['requested'],extent=a['extent'],mapped_bytes=a['mapped'],initial_hex=raw[:a['extent']].hex(),mapped_tail_hex=raw[a['extent']:].hex(),generation=a['generation'],native=a['native'],capacity=a.get('capacity',0),live=True)
class Machine(C.Machine):
 def begin_constructor(self,root):
  self.arch_undefined=dict(getattr(self,'_source_undefined_flags',{}))
  return super().begin_constructor(root)
 def end_constructor(self):
  outer=dict(getattr(self,'_source_undefined_flags',{}))
  I.need(set(outer)==set(self.arch_undefined),'Constructor resulting undefined flags must equal outer persistent instruction domain')
  def site(v):return v['PC']if isinstance(v,dict)else v
  I.need(all(site(outer[n])==site(self.arch_undefined[n])for n in outer),'Exact source producer provenance survives constructor flag-domain return')
  result=super().end_constructor();self._source_undefined_flags=outer
  return result
 def synchronize_constructor_owners(self,responses):
  # Values come only from the independently computed carried source memory.
  # This refreshes role metadata after genuine prior source API transitions.
  self.constructor_owners=[owner_role(self,a)for a in responses.allocations if a['live']]
 def admit_constructor_imports(self):
  prover=getattr(self,'constructor_named_input_prover',None)
  I.need(callable(prover),'Current physical named-module/IAT/provider proof must be installed before constructor source import projection')
  # Named physical provider identity is a separate mandatory caller proof.
  for pc,address,target in ((0x5abd1a,0x5bb4c8,0x5f401782),(0x5abd26,0x5bb4bc,0x5f401ea0),(0x5ac11e,0x5bb52c,0x78004a36)):
   raw=int.from_bytes(self.bytes(address,4),'little')
   I.need(prover(self,pc,address,raw,target),'Exact current named physical provider and carried owning import cell')
   self.constructor_imports[pc,address]=dict(raw=raw,target=target,owning_named_input=True)
 def run_carried_constructor(self,root,responses):
  I.need(root in ROOTS and not self.constructor_active,'One genuine current selected constructor')
  self.synchronize_constructor_owners(responses);self.admit_constructor_imports()
  self.begin_constructor(root);frame=self.reg('esp');ret=int.from_bytes(self.bytes(frame,4),'little')
  before=dict(State=bytes(self.state),CPU=tuple(self.projected_cpu()),FX=bytes(self.fx),memory={a:bytes(b)for a,b in self.memory.items()},response_index=responses.index,generation=responses.generation)
  self.run(lambda m:m.cursor==ret,api=responses)
  self.end_constructor();I.need(self.reg('esp')==frame+4 and not self.call_stack and self.fp_depth==0,'Whole genuine source constructor RET and balanced FS')
  return before
def response_class(Base):
 class Responses(Base):
  def __call__(self,m,target):
   active=getattr(m,'constructor_active',False);before=self.index;count=len(self.allocations)
   super().__call__(m,target)
   if active:
    I.need(self.index==before+1,'Every constructor source API consumes the same persistent fact ledger')
    if len(self.allocations)>count:
     I.need(len(self.allocations)==count+1 and self.facts[before]['name']=='HeapAlloc','One genuine source HeapAlloc birth')
     a=self.allocations[-1];I.need(a['requested']in(12,4) and a['extent']==16,'Exact constructor source request and literal rounded API extent')
     m.add_owner(owner_role(m,a))
    for o in m.constructor_owners:
     a=next((v for v in self.allocations if v['generation']==o['generation']),None)
     if a is not None:o['live']=a['live']
 return Responses
