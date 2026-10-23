"""Prepare a bounded gate specification; never grant acceptance or run readers."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/acceptance138-specification-r1';assert not out.exists();out.mkdir()
 pins={}
 def read(rel,h=None):
  p=(R/rel).resolve();actual=sha(p);assert h is None or actual==h;(pins.__setitem__(str(p),actual));return json.loads(p.read_bytes())
 parent_path='reports/m4-joint-startup131-root/acceptance-r1/report.json'
 parent_sha='aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061'
 parent=read(parent_path,parent_sha);assert parent['passed']is True and parent['connected_roots']==131 and parent['explicit_measured_predicates']==841
 config=read('reports/m4-joint-startup131-root/configuration-r1/configuration.json')
 checker=R/'tools/m4-joint-startup131/acceptance.py';pins[str(checker)]=sha(checker)
 tree=ast.parse(checker.read_text());required=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets))
 assert set(config['gates'])==required and len(required)==33
 source_path='reports/m4-joint-startup138-source/combined-source-provider-r6/report.json'
 source_sha='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'
 source=read(source_path,source_sha);assert source['passed']is True and source['reader_closed']is True
 prep_path='reports/m4-joint-startup138/preparation-r4/report.json'
 prep=read(prep_path,'a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
 old=read('reports/m4-joint-startup131/preparation-r1/report.json')
 candidates=[dict(phase=p,entry=e,slot=s,callback=c)for p,e,s,c in [(15,0x40e250,0x5e0048,0x40e420),(16,0x40ef50,0x5e004c,0x40ef90),(17,0x40f000,0x5e0050,0x40f030),(47,0x479590,0x5e00cc,0x4795d0),(134,0x5a3c30,0x5e0234,0x5a3c60),(135,0x5a3ff0,0x5e0238,0x5a4020),(136,0x5a66f0,0x5e023c,0x5a6720)]]
 entries={c['entry']for c in candidates};order=prep['selected_order'];assert len(order)==138 and len({r['entry']for r in order})==138
 assert [r for r in order if r['entry']not in entries]==old['selected_order']
 for c in candidates:assert order[c['phase']]==dict(entry=c['entry'],slot=c['slot'])
 assert prep['current_registration_callbacks']==108
 completed={}
 for name,rel,h in [
 ('source_closure','reports/m4-tree-review/source138-closure-r1/report.json','fc2453e5a9ff713d122f73e3a165edbdcc43da1b31c18f8bae787e6d6b43b38b'),
 ('source_provider_review','reports/m4-tree-review/source138-provider-independent-r1/report.json','0636824db58e6d446f6bcca8cd4a977f5291530ad2e9b7c5f4c15b47184ee390'),
 ('source_new_mfc_review','reports/m4-tree-review/source138-mfc-independent-r1/report.json','611d89e5621dcd94282d4df5bcf5e9544bf9c0942f18c7f3ddb137acd61ea893'),
 ('source_widget_journal_review','reports/m4-138-controls-review/source6-widget-journal-physical-r2/report.json','c7978551027aa77d9e3df4452b5526af0a3e5132e8e5b1c069e86a39b27b85e9'),
 ('source_widget_memory_review','reports/m4-138-controls-review/source6-widget-memory-physical-r2/report.json','2e9cc788f24c7dddcf5a732fd851138976ba03bf43f3aef5b0527c7ddf7151ce')]:
  d=read(rel,h);assert d['passed']is True;completed[name]=dict(path=rel,sha256=h,scope='Receipt identity measured; all declared dependency bytes require final fresh union measurement')
 baseline=out/'accepted131-gate-predicates.json';baseline.write_text(json.dumps(config,indent=2)+'\n');pins[str(baseline)]=sha(baseline)
 spec=dict(scope='Specification only, not an acceptance checker, admission or count receipt',accepted_parent=dict(path=parent_path,sha256=parent_sha,connected_roots=131,entire_parent_dependency_count=len(parent['files']),retain_entire_receipt_and_all_dependencies=True),baseline=dict(checker=str(checker),checker_sha256=sha(checker),required_gate_names=sorted(required),explicit_measured_predicates=841,configuration=str(baseline),rule='Retain every applicable semantic/type/owner/resource/source/closure predicate; review explicit count/lineage/order deltas. This copy is a reference and must not be used as current138 configuration unchanged.'),candidate_roots=candidates,current_order=order,current_registration_callbacks=108,completed_current_receipts=completed,current_source=dict(path=source_path,sha256=source_sha,executed_lineage=source['executed_lineage'],counts=source['counts'],provider_counts=source['provider_counts']),additional_required_gates={
 'source_widget_semantic_review':dict(path=None,sha256=None,prepared_tool='tools/m4-138-controls-review/review_widget_semantics.py',requirements=['Independent whole reached literal Game/CRT bytes, operand widths and accepted unchanged interpreter layers','Exact State register/flag offset mapping and current widget/API source transfer domains','All84 whole State3504/CPU40/FX512 BEFORE/AFTER joins authenticated to current producing source6','All84 independent memory/raw GDI review and own typed CRT heap birth','No second interpreter execution claimed or required by accepted131 predicates']),
 'current_original_widgets':dict(path=None,sha256=None,requirements=['Actual current original138 preparation/build/whole-link/prelaunch/execution/validation chain','Independent six-sequence original source derivation with all reached seven widgets and retained old131 source proof','Whole owner/GDI/State/CPU/FX/raw backing/literal code source evidence; no verifier-only credit']),
 'current_source_equivalence':dict(path=None,sha256=None,requirements=['Reviewed explicit source prediction and projection/paired CRT indeterminate-byte policy','Current138 original/native source pairing with all inherited six-domain/FP/owner/source-metadata gates','Fresh independent paired review binding exact current inputs; no metadata-only relation']),
 'controls_full_raw_and_retry':dict(path=None,sha256=None,status='Full ordinary inventory execution owned by root; identity unresolved until sealed completion',requirements=['Admitted unchanged current context-controls checker and actual full current control execution','16 actual O0/O2 x modes1..8 cases, 10691866 outputs and 3547696 retry pairs','Independent all-and-only raw physical payload hashes/lengths and private-retry equality with final integrity','Closed durable SQLite schema/count/domain proof pinned in completed report','Independent current native138 full-link join and physical GDI owner identity, not DLL names alone']),
 'whole_dependency_union':dict(path=None,sha256=None,requirements=['Retain accepted131 entire dependency union and every current report dependency declaration','Expand every sealed controls physical-index row into acceptance union using expand_proof_inventory.py','Fresh whole-byte hash of every union entry; no metadata shortcut or manifest-name-only credit','Exact conflict-free normalized identity; all artifacts/checkers/Python/toolchains retained','All workers/readers terminal/closed; archive references preserved and no evidence overwritten']),
 'acceptance_implementation_review':dict(path=None,sha256=None,requirements=['Root-authored current acceptance checker/configuration retaining all131 predicates and explicit additive widget gates','Independent code/configuration exact source/inverse review and positive/adverse bounded preflight','Actual final acceptance execution required before changing connected_roots'])},prohibited_claims=['Capture/verifier pass alone grants accepted roots','Training replay viewer proves native game execution/rendering','Constructor or141/142 component proof grants current138 or144 acceptance','Specification or unexecuted widget supplement grants credit'],initializer_credit=0,acceptance_executed=False,accepted_count_unchanged=131)
 q=out/'gate-specification.json';q.write_text(json.dumps(spec,indent=2)+'\n');pins[str(q)]=sha(q)
 for p in [Path(__file__).resolve(),Path(sys.executable).resolve(),R/'tools/m4-138-controls-review/expand_proof_inventory.py',R/'tools/m4-138-controls-review/review_widget_semantics.py']:pins[str(p)]=sha(p)
 report=dict(passed=True,scope='Bounded specification provenance/physical selected order and current ordinary report identity review only',specification_path=str(q),specification_sha256=sha(q),baseline_gate_count=33,baseline_measured_predicates=841,parent_dependency_count=len(parent['files']),candidate_roots=7,current_callbacks=108,acceptance_executed=False,initializer_credit=0,accepted_count_unchanged=131,capture_reader_opened=False,worker_executed=False,whole_dependency_union_measured=False,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),specification_sha256=sha(q))))
if __name__=='__main__':main()
