"""Ordinary report-only readiness; never executes comparer or opens payloads."""
from pathlib import Path
import hashlib,json,sys,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-startup141-paired/readiness-r1';out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve()
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 parent=pin(R/'reports/m4-startup138-paired/comparer-preparation-r15/paired138.py');s=parent.read_text(encoding='utf-8');ast.parse(s)
 pair=read(R/'reports/m4-startup138-paired/paired-r5/report.json');assert pair['passed']
 config=read(R/'reports/m4-startup138-paired/configuration-r8/configuration.json')
 source=read(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3');assert source['passed']and source['reader_closed']
 native=read(R/'reports/m4-startup141-root/execution-r2/report.json','536eeb8c62c9de8276e46d727907faea417b91a22c2cbae5ceaf1d3e721b5d0f271d610' if False else '536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6');assert native['passed']and set(native['runs'])=={'O0','O2'}
 read(R/'reports/m4-startup141-root/validation-r1/report.json','00406b1d901fe996e0d15f9281048ff6222d6bae5ceaf1d3e721b5d0f271d610')
 original=next(row for row in source['paired_exports']if row['branch']=='original');assert 'm4-startup138-original' in original['transport_path']
 q=out/'inherited-comparer138.py';q.write_bytes(parent.read_bytes());pin(q)
 requirements=[
 ('original_identity','Require current successful original141 strict/source/export/independent source policy; native source6 original export is OLD138 and unusable for current141.'),
 ('source_stack','Fresh original141 eleven rebased PUSHFD points, source-defined flags and undefinedness, ordered shadow stores, every later live operand and whole own-stack equality; old isolated37 spec cannot establish this.'),
 ('inherited_inverse','Retain all53 inherited typed relations and full predicates through exact finite inverses. Change frozen stale identities/domain counters only after actual current proofs.'),
 ('execution_schema','Current native execution uses runs O0/O2, inherited comparer levels list. Require exact current build/preparation and each actual capture identity.'),
 ('constructor_domains','Three physical inserted roots at slots13/14/39; same carried State/Game/CPU/FX/owners, own birth/NULL/getter cleanup and named actual imports. No isolated own-BEFORE reseed.'),
 ('pages','69 existing pages plus separate whole5F2000 BEFORE/AFTER on every141 phase. Derive1692 phases,230112 nonstack endpoint joins and3384 global5F2000 endpoints.'),
 ('FS','Global normal28 frames56 records remains exact; constructor7 frames14 raw12 records21 events separately source-owned, never fake merged35/70 global ledger.'),
 ('MFC_owners','Old68 plus6 constructor kind4 =74 exact same-source chronology. Whole16Q/32Q fields and allocation capacities retained; no constant ordinal shift.'),
 ('registry','108 to111 physical callbacks/root order, real growth births, whole capacities/lifetimes and cleanup; widget phases17/18/19/50/137/138/139, MFC15.'),
 ('observer_and_loader','Actual rebased linked observer spans and current dynamic module/IAT/144 named bindings; exact whole-page relations only, no generic hash mutation exception.'),
 ('ABI','Original critical section24B/native40B typed semantic relation, raw zeroPC retained and modeled CPU target distinct; inherited finite crossbranch CPU/FX/ENV policy stays strict.'),
 ('scope','Six actual numerical cases/default zero FSQRT; source shutdown callback execution remains false. Manual cleanup identity cannot claim callback/native game/rendering execution.')]
 p=out/'requirements.json';p.write_text(json.dumps([dict(gate=a,evidence=b)for a,b in requirements],indent=2)+'\n',encoding='utf-8');pin(p);pin(__file__)
 report=dict(passed=True,readiness_only=True,comparer_execution_admitted=False,original141_source_gate_pending=True,old_original_export_reuse_rejected=True,inherited_configuration_gates=[k for k,v in config.items()if isinstance(v,dict)and 'path'in v],current_native_source_pass=True,required_phases=1692,required_nonstack_page_endpoints=230112,required_constructor_global_page_endpoints=3384,canonical_reader_opened=False,ordinary_payload_reader_opened=False,worker_launched=False,initializer_credit=0,accepted_function_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
