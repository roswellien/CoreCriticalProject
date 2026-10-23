"""Physical exact budget derivative source preflight; old gates retained."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-startup141-runway'
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or v==h,(str(p),h,v);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prior=read(R/'reports/m4-138-validation-review/full141-source-delta-review-r5/report.json','ad41a14303e37bc6fc4ab1cdf5878ad1adf61d3ee8443409aef5705205f42200');assert prior['passed']and not prior['selected_relation_metadata_correction_pending']
 for p,h in prior['files'].items():pin(p,h)
 old=read(B/'preparation-r2/report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c');new=read(B/'preparation-r3/report.json','98b3f726249ef233ccdc63855cd5c735aa2ff01cc8717494b686bec34dafb46e');service=read(B/'service-preparation-r2/report.json','4483a6256bdbdc99482636fac97c6913be9a809d39e42686cb14757a00df8ad0');build=read(B/'service-build-r2/build.json','e060132b0c7ebca5a82f86efe1a6874546d69a64709fbc6fe795884956462aa9');assert all(r['passed']for r in(old,new,service,build))
 for r in(new,service,build):
  for p,h in r['files'].items():pin(p,h)
 for parent in (B/'preparation-r2').rglob('*'):
  if not parent.is_file()or parent.name=='report.json':continue
  child=B/'preparation-r3'/parent.relative_to(B/'preparation-r2');a=pin(parent,old['files'][str(parent.resolve())]).read_bytes();b=pin(child,new['files'][str(child.resolve())]).read_bytes()
  if parent.name=='onexit_session.hpp':assert b.replace(b'service-preparation-r2',b'service-preparation-r1')==a and b!=a
  else:assert a==b
  relations.append(dict(parent=str(parent),child=str(child),whole_bytes_equal=a==b))
 for parent in (B/'service-preparation-r1').iterdir():
  if not parent.is_file()or parent.name=='report.json':continue
  child=B/'service-preparation-r2'/parent.name;a=pin(parent).read_bytes();b=pin(child).read_bytes()
  if parent.name=='locale_batch_operations.inc':assert a.count(b'live_allocations()>92')==b.count(b'live_allocations()>98')==1 and b.replace(b'live_allocations()>98',b'live_allocations()>92')==a
  else:assert a==b
 contract=read(B/'service-preparation-r2/live-allocation-budget-contract.json');assert contract['passed']and contract['new_live_cap']==contract['old_live_cap']+3*contract['new_births_per_root']==98;assert len(contract['literal54_birth_proofs'])==54
 # The builder consumes these complete corrected current service units at both levels.
 for level,info in build['levels'].items():assert str(B/'service-preparation-r2/locale_batch_operations.inc')in info['actual_header_dependencies'];assert str(B/'service-preparation-r2/session_impl.inc')in info['actual_header_dependencies']
 for key in('selected_order','objects','constructor_libraries','widget_libraries','current_registration_callbacks','source_roots','source_sequences','selected_phases','Runtime_translations','Runtime_calls_per_sequence'):assert new[key]==old[key]
 pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Exact full141 inherited source proof transfer through whole file inverse; only allocationcap92to98 and canonical service header rebinding. Current worker full-link review and strictsource/runtime count checks remain required.',selected_relation_metadata_correction_pending=False,exact_service_unit_inverse=True,all_old141_inputs_unchanged_except_service_binding=True,source_relations=relations,budget_contract=contract,initializer_credit=0,archive_reader_opened=False,execution_admitted=False,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
