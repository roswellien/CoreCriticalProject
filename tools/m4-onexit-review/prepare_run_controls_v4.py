"""Add explicit cleanup observation counts without changing any control gate."""
from pathlib import Path
H=Path(__file__).parent
p=H/'run_controls_v4.py';assert not p.exists();s=(H/'run_controls_v3.py').read_text()
a="rich_hardware_pairs=0,physical_API_proofs=0,actual_native_moves=0,partial_transfer_faults=0)"
b="rich_hardware_pairs=0,physical_API_proofs=0,actual_native_moves=0,partial_transfer_faults=0,\n                                           independent_postdestroy_identity_pairs=0,candidate_destroy_after_missing=0)"
assert s.count(a)==1;s=s.replace(a,b)
a="                            actual_after=e.identity(archive,f'case-{selected}/first-cleanup-api-after',pin)"
b=a+"\n                            metrics['candidate_destroy_after_missing']+=1;metrics['independent_postdestroy_identity_pairs']+=1"
assert s.count(a)==1;s=s.replace(a,b)
a="                    cleanup_API_identity_scope="
b="                    cleanup_identity=dict(independent_measurement_immediately_after_finish=True,native_before_vs_independent_after_equal=True,candidate_after_identity_observed=False,typed_source_same_HANDLE_actual_success=True,independent_pairs=metrics['independent_postdestroy_identity_pairs'],candidate_after_absent=metrics['candidate_destroy_after_missing']),\n                    cleanup_API_identity_scope="
assert s.count(a)==1;s=s.replace(a,b);p.write_text(s)
print('Derived fresh explicit cleanup attestation checker')
