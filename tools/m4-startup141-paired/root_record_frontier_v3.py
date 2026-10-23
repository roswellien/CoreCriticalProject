"""Record only actual finite closures; preserve all uncompleted acceptance gates."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';pins={}
 def read(p,h):
  p=Path(p).resolve();assert sha(p)==h;pins[str(p)]=h;return json.loads(p.read_bytes())
 accepted=read(R/'reports/m4-joint-startup131-root/acceptance-r1/report.json','aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061')
 assert accepted['passed']and accepted['connected_roots']==131 and accepted['remaining_inventory_roots']==13
 native=read(base/'native36-source-r9/report.json','fecb9e60d91fbcbea759af616ec285739d98f7176811160fc05e3407d5b87650')
 assert native['passed']and native['ordinary_reader_closed']and len(native['cases'])==36 and native['input_carry_policy_review_pending']is False and native['initializer_credit']==0
 assert all(c['sourcepredicted_FS4_input_and_restoration']is True and c['earlier_checkpoint_nonphase_input_dependency_present']is False and c['whole_TIB_claim']is False for c in native['cases'])
 original=read(base/'original7-layout-r2/report.json','c02017302587a5f5a1d0e2e0a08c2d43d886e8ca039a6f10db026bc965d85b0d')
 assert original['passed']and original['ordinary_reader_closed']and original['source_case_extent']==120 and not original['complete_paired141_gate']and original['accepted_function_credit']==0
 assert original['files'][original['typed_view_path']]==original['typed_view_sha256'];view=read(original['typed_view_path'],original['typed_view_sha256']);assert len(view['cases'])==120 and view['complete_paired141_gate']is False
 remaining_path=base/'current-frontier-r2/remaining-gates.json';remaining=read(remaining_path,'7ff50e0356605ffaa6e55cc03de240a351d2e0e32b1eb80de8010db156e50bb5')
 for row in remaining:
  assert row['closed']is False
  if row['domain']=='native_input_carry_FS':row.update(closed=True,evidence='native36-source-r9',closure_scope='Finite native36 own input policy only; whole TIB and independent second CPU owner carry unclaimed')
  if row['domain']=='current_original_family_view':row.update(typed_layout_closed=True,typed_layout_evidence='original7-layout-r2',inherited53_consumer_role_rebinding_closed=False,next='Use actual120 typed bindings in a separately reviewed whole53-preserving current comparer; layout cannot supply missing source/paired claims')
 pins[str(Path(__file__).resolve())]=sha(__file__)
 out=base/'root-continuation-frontier-r3';assert not out.exists();out.mkdir()
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Actual finite continuation closures and explicit unclosed current141 gates only',accepted_count=131,total_inventory=144,remaining_inventory=13,accepted_receipt_rehashed=True,historical_acceptance_union_freshly_reverified=False,new_acceptance_receipt_created=False,current_full141_comparer_exists=False,complete_paired141_gate=False,remaining_gates=remaining,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
