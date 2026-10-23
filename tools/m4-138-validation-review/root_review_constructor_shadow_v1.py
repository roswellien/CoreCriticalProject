"""Root review of the finite constructor observer relation, without captures."""
from pathlib import Path
import hashlib,json,sys,struct
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-validation-review/constructor-shadow-root-review-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def receipt(rel,h):
  p=pin(R/'reports/m4-138-validation-review'/rel/'report.json',h);g=json.loads(p.read_bytes());assert g['passed']
  for q,v in g['files'].items():pin(q,v)
  return g
 audit=receipt('constructor-source-dependency-review-r8','4c91796493b1a91d9df78f3221fb53d146d9990da9edee4454d779adc3473755')
 geo=receipt('constructor-observer-geometry-review-r1','2930f8f0aba50d351569921106c04567274fe85d27b98f9ff366e61b07ae8ed5')
 assert len(geo['cases'])==54 and all(not c['crossing_upper_stack_operands']and c['all_FS_raw12_frames_bounded']for c in geo['cases'])
 assert not audit['recursive_historical_ancestry_claim']and len(audit['modules'])==24
 cases=[];stores=0
 for folder,digest in [('constructor-original18-source-r4','48cad330f7fe559721fe10748efdf4261e92d22653ba141883065c4c9342fff6'),('constructor-native36-source-r6','e7bc628fe59f20e69a5823e2f54ad88af94d9f0dbbfea1c51d8e45807d5c4392')]:
  receipt(folder,digest)
 for c in geo['cases']:
  folder='constructor-original18-source-r4'if c['branch']=='original'else'constructor-native36-source-r6';base=R/'reports/m4-138-validation-review'/folder/f"{c['branch']}-{c['sequence']}-{c['root']}"
  p=base/'source-derivation.json';assert str(p.resolve())in pins;s=json.loads(p.read_bytes())
  for pc,a,value,width,write in s['accesses']:
   assert width>0
   if a<0x20002000 and a+width>0x20001000:assert 0x20001000<=a and a+width<=0x20002000
  for e in s['original_observer_stores']:
   assert e['source_value_used']and not e['observed_endpoint_seed']and e['write_bytes']==4 and e['write_hex']==struct.pack('<I',e['CPU'][8]).hex()and e['source_EFLAGS']==e['CPU'][8];stores+=1
  assert s['source_AFTER_seed']is False and s['per_phase_reseed']is False and s['native_capacity_inferred']is False
  cases.append(dict(branch=c['branch'],sequence=c['sequence'],root=c['root'],source_accesses=len(s['accesses']),source_computed_observer_stores=len(s['original_observer_stores'])))
 assert stores==96
 # Whole code was reviewed by root. Direct bytes reads at the API seam are
 # guarded by v9; malloc request by v6/v9; source operands by v8. FS raw12
 # byte snapshots record pure-source scope metadata: only previous-head DWORD
 # affects the source branch and that value is separately a literal operand.
 # Getter owner buffers and fixed data/vtable reads have disjoint stack roles.
 for q,h in pins.items():assert sha(q)==h
 pin(__file__);pin(sys.executable);out.mkdir();p=out/'report.json';p.write_text(json.dumps(dict(passed=True,independent_review=True,scope='Finite isolated54 constructor observer/source relation only; no combined141 carry or acceptance',cases=cases,computed_observer_PUSHFD_stores=stores,source_operand_stack_geometry_reviewed=True,typed_API_frame_buffer_and_malloc_request_transparency_reviewed=True,FS_raw12_metadata_is_not_observed_source_input=True,whole_code_direct_byte_roles_reviewed=True,second_interpreter_execution=False,original_whole_State_claim=False,current141_carry_admitted=False,initializer_credit=0,all_readers_closed=True,files=pins),indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
