"""Retain computed MFC BEFORE and seven literal boundary proof snapshots.

The frozen v2 evaluator, capture reads and comparisons are unchanged. These
additional exports are taken from the persistent computed machine and literal
step inputs, never from candidate BEFORE/AFTER equality targets.
"""
from pathlib import Path
import hashlib,importlib.util,struct
ROOT=Path(__file__).resolve().parents[2]
parent=ROOT/'tools/m4-joint-startup131/mfc_source_v2.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='13e96927079d84483e2cb4017154601304b0fab10a41f4713071f21bfa111406'
spec=importlib.util.spec_from_file_location('joint131_mfc_source_defined_parent',parent)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
layout_path=ROOT/'tools/m4-joint-startup131/mfc_source_layout.py'
assert hashlib.sha256(layout_path.read_bytes()).hexdigest()=='32b4a5059a37015fd14d9fd7f5bbcd5a5eeebae7943459a60a75730a45d7efe8'
layout_spec=importlib.util.spec_from_file_location('joint131_mfc_exact_TIB_layout',layout_path)
L=importlib.util.module_from_spec(layout_spec);layout_spec.loader.exec_module(L)
BOUNDARIES=(0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca)

class Extension(M.Extension):
 def __init__(self,preparation,pin):
  super().__init__(preparation,pin);pin(parent);pin(layout_path)
  view=ROOT/'reports/m4-mixed-startup/independent-review-r1/review.py'
  pin(view,'53832a5587972840620254c792bcd732d805f411553386822ca0afb2530795c3')
  s=importlib.util.spec_from_file_location('joint131_mfc_boundary_State_projection',view)
  self._projection=importlib.util.module_from_spec(s);s.loader.exec_module(self._projection)
  self._snapshots=[];base=self.literal.Literal;outer=self
  class SnapshotLiteral(base):
   def step(self):
    if self.cursor in BOUNDARIES:
     _,env=outer._projection.proj(bytes(self.state))
     outer._snapshots.append(dict(PC=self.cursor,CPU=list(self.cpu_now()),State_hex=bytes(self.state).hex(),FX_hex=self.fx.hex(),ENV28_hex=env.hex(),frame64_hex=self.bytes(self.reg('esp'),64).hex(),source_instruction_index=len(self.PCs),source_access_index=len(self.accesses),scope='Literal-derived before-instruction snapshot, not an actual native boundary observation'))
    return super().step()
  self.literal.Literal=SnapshotLiteral
 def phase(self,machine,*args,**kwargs):
  # Copy the independently computed caller before the frozen parent mutates it.
  state=bytes(machine.state);cpu=struct.pack('<10I',*machine.projected_cpu());fx=machine.fx
  memory={a:bytes(b)for a,b in machine.memory.items()};input_domain=dict(getattr(machine,'_source_undefined_flags',{}));self._snapshots=[]
  result=L.Extension.phase(self,machine,*args,**kwargs);machine._source_undefined_flags=dict(result['final_undefined_flags']);self.counts['MFC_defined_flag_consumers']+=len(result['defined_flag_consumers'])
  M.M.eq([r['PC']for r in self._snapshots],list(BOUNDARIES),'All seven literal normal boundary snapshots in source order')
  lifetimes=result['flag_lifetimes']
  for row in self._snapshots:
   n=row['source_instruction_index'];row['undefined_flags_before']=dict(lifetimes[n-1]['undefined_flags'])if n else {}
   row['defined_flag_consumer']=next((r for r in result['defined_flag_consumers']if r['PC']==row['PC']),None)
  requirements=[(pc,self.contracts['instructions'][i]['width'])for i,pc in enumerate(result['source_PCs'])]
  # Source instructions may be in a different contract-list order.
  widths={r['pc']:r['width']for r in self.contracts['instructions']}
  requirements=[(pc,widths[pc])for pc in result['source_PCs']]
  requirements += [(a,w)for _,a,_,w,_ in result['source_accesses']]
  requirements += [(r['CPU_before'][4],64)for r in result['source_API_relations']]
  requirements += [(r['CPU'][4],64)for r in self._snapshots]
  requirements += [(a,n)for a,n,_ in result['whole_regions']]
  selected={}
  for address,width in requirements:
   owners=[(a,b)for a,b in memory.items()if a<=address and address+width<=a+len(b)]
   if not owners and (address,width)==(0x7ffde004,8) and len(memory.get(0x7ffde004,b''))==len(memory.get(0x7ffde008,b''))==4:
    selected[str(0x7ffde004)]=memory[0x7ffde004].hex();selected[str(0x7ffde008)]=memory[0x7ffde008].hex()
    M.M.eq(memory[0x7ffde004]+memory[0x7ffde008],bytes.fromhex(result['TIB_region_representation'][0]['joined_BEFORE_hex']),'Exact proof export original computed TIB parts')
   else:
    M.M.need(len(owners)==1,'Exactly one computed BEFORE owner for every exported source requirement')
    a,b=owners[0];selected[str(a)]=b.hex()
  _,env=self._projection.proj(state)
  result.update(source_computed_BEFORE=dict(State_hex=state.hex(),CPU_hex=cpu.hex(),FX_hex=fx.hex(),ENV28_hex=env.hex(),memory=selected,carried_undefined_flags=input_domain,scope='Independently computed persistent BEFORE, source-required complete regions; candidate snapshots are equality targets only'),source_normal_boundaries=self._snapshots,source_boundary_scope='Seven literal-derived snapshots, no intermediate native observer claim')
  self.counts['MFC_literal_normal_boundary_snapshots']+=len(self._snapshots)
  self.counts['MFC_computed_BEFORE_exports']+=1
  return result
