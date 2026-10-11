from pathlib import Path
import hashlib
T=Path(__file__).resolve().parent;p=T/'compare_source_v2.py';s=p.read_text()
changes=[
 (";eq(w(m.bytes(teb_base,4))[0],b['metadata'][2],'Literal carried source FS head at normal boundary')", ""),
 ("source_FS_head=w(m.bytes(teb_base,4))[0]", "derived_source_FS_head=w(m.bytes(teb_base,4))[0],actual_observer_owned_FS_head=b['metadata'][2],intermediate_source_FS_observation=False"),
 (";eq(w(m.bytes(teb_base,4))[0],a['FShead'],'Derived installed FS head at named API entry');eq(a['FShead'],z['FShead'],'Actual API source FS head conserved')", ";eq(a['FShead'],z['FShead'],'Actual observer-owned host FS metadata unchanged')"),
 ("FS_head=a['FShead'],volatile_input_fields", "actual_observer_owned_FS_head=a['FShead'],derived_source_FS_head=w(m.bytes(teb_base,4))[0],intermediate_source_FS_observation=False,volatile_input_fields"),
 ("eq(w(m.bytes(teb_base,4))[0],w(teb)[0],'Exact literal source FS restored');fs=", "eq(w(m.bytes(teb_base,4))[0],w(teb)[0],'Exact literal source FS restored');actual_teb_after=raw('phase/0/13/TEB-after.bin');eq(w(actual_teb_after)[0],w(m.bytes(teb_base,4))[0],'Actual assembly root-return TIB head independently joins carried literal source');fs="),
 ("actual_per_instruction_chronological_trace=False,whole_stack_endpoint_claim=False", "actual_per_instruction_chronological_trace=False,intermediate_source_FS_observation=False,boundary_FS_header_scope='Read inside C++ observer after its compiler-owned host exception frame; retained raw, not source input or guest head expectation',whole_stack_endpoint_claim=False"),
 ("pin(__file__);pin(sys.executable)", "pin(R/'tools/m4-mfc1168-connected-original/compare_source_v2.py');pin(R/'tools/m4-mfc1168-connected-original/derive_compare_v3.py');pin(__file__);pin(sys.executable)")]
for old,new in changes:
 if s.count(old)!=1:raise ValueError('Exact additive FS scope hunk '+old)
 s=s.replace(old,new)
out=T/'compare_source_v3.py'
if out.exists():raise ValueError('Fresh derivative')
out.write_text(s);print(hashlib.sha256(out.read_bytes()).hexdigest())
