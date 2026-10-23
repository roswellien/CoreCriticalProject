"""Immutable exact source-audit derivative; no checker/ROOT admission run."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-138-preresource-strict-review/named-facets-preparation-r2';assert not out.exists();out.mkdir();pins={}
 def pin(p):p=Path(p).resolve();pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
 parent=pin(R/'tools/m4-138-preresource-strict-review/review_named_facets_v1.py');old=parent.read_text();s=old;deltas=[]
 def replace(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);deltas.append(dict(before=a,after=b))
 replace('  p=Path(p).resolve();assert p.suffix.lower()not in(\'.mwb\',\'.mwi\',\'.zip\')and p.name!=\'transport.json\';assert sha(p)==h;assert pins.setdefault(str(p),h)==h;return p',"""  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  if 'audit_policy'in locals_for_audit:locals_for_audit['audit_policy'].begin_hash(p,h)
  actual=sha(p)
  if 'audit_policy'in locals_for_audit:locals_for_audit['audit_policy'].end_hash(p,h,actual)
  assert actual==h;assert pins.setdefault(str(p),h)==h;return p""")
 replace('  with Path(p).open(\'rb\')as f:return hashlib.file_digest(f,\'sha256\').hexdigest()','  with Path(p).open(\'rb\')as f:return hashlib.file_digest(f,\'sha256\').hexdigest()') if False else None
 replace(' out=R/\'reports/m4-138-preresource-strict-review\'/name;assert not out.exists();out.mkdir();pins={};passed=False;cases=[];counts=collections.Counter()'," out=R/'reports/m4-138-preresource-strict-review'/name;assert not out.exists();out.mkdir();pins={};passed=False;cases=[];counts=collections.Counter();locals_for_audit={}")
 replace(" try:\n  batch_path=ordinary", """ try:
  Audit=module(R/'tools/m4-138-preresource-strict-review/source_read_audit_v1.py','named_source_read_audit')
  audit_policy=Audit.Reads({**declared,str(admission_path):admission_sha},out);locals_for_audit['audit_policy']=audit_policy;audit_policy.install()
  for p,h in declared.items():pin(p,h)
  batch_path=ordinary""")
 replace("   for p,h in pins.items():assert sha(p)==h", "   for p,h in pins.items():assert sha(p)==h") if False else None
 replace("all_bounded_readers_closed=True,whole_raw_inventory_rehashed=False", "all_bounded_readers_closed=True,source_only_read_audit=True,audited_read_paths=sorted(audit_policy.reads)if 'audit_policy'in locals_for_audit else [],cached_pyc_refused_paths=sorted(audit_policy.pyc_refusals)if 'audit_policy'in locals_for_audit else [],whole_raw_inventory_rehashed=False")
 inverse=s
 for d in reversed(deltas):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
 assert inverse==old;ast.parse(s)
 checker=out/'review_named_facets_v2.py';checker.write_text(s);pin(checker)
 # Materialized report-resident checker needs repo root one parent farther.
 oldroot='R=Path(__file__).resolve().parents[2]';newroot='R=Path(__file__).resolve().parents[3]';assert s.count(oldroot)==1
 checker.write_text(s.replace(oldroot,newroot));pins[str(checker)]=hashlib.sha256(checker.read_bytes()).hexdigest();deltas.append(dict(before=oldroot,after=newroot));ast.parse(checker.read_text())
 # Required map includes only ordinary metadata/current source/cold imports.
 # Raw identities are looked up from each same-case exact strict receipt only.
 batch_path=pin(R/'reports/m4-138-preresource-strict-review/root-strict-remaining23-r1/report.json');batch=json.loads(batch_path.read_bytes());assert pins[str(batch_path)]=='2cf7c24beaa1bf64ce79861c1b08c2ade3e3498acbde8c697f819119341ec654'
 for row in batch['strict_cases']:
  p=Path(row['report']);pins[str(p)]=row['sha256'];p=Path(row['raw_execution']);pins[str(p)]=row['raw_execution_sha256']
 build_path=pin(R/'reports/m4-138-preresource-controls/build-r4/build.json');build=json.loads(build_path.read_bytes());prep_path=pin(build['preparation']);prep=json.loads(prep_path.read_bytes());pin(prep['parent_preparation'])
 for path in('tools/m4-138-preresource-strict-review/source_read_audit_v1.py','tools/m4-138-preresource-strict-review/named_facets_v1.py','tools/m4-mfc1168-native/persistent_source.py','tools/m4-crt-locale-batch-model-review/interpreter_v2.py','tools/m4-formatting-source/flag_domain.py','reports/m4-mfc1168-probe/native-contracts-r1/contracts.json'):pin(R/path)
 for name in('copy.py','weakref.py','copyreg.py','_weakrefset.py','types.py','_collections_abc.py','abc.py'):pin(Path(sys.base_prefix)/'Lib'/name)
 pin(sys.executable);pin(__file__)
 required=dict(pins);map_path=out/'required-ordinary-input-map.json';map_path.write_text(json.dumps(required,indent=2)+'\n');pin(map_path)
 delta_path=out/'whole-source-inverse.json';delta_path.write_text(json.dumps(deltas,indent=2)+'\n');pin(delta_path)
 recipe=dict(scope='Unexecuted source-only exact5-hunk audit derivative; ROOT admission still required',scope_identity='current138_preresource_named_facets',required_ordinary_map=str(map_path),required_ordinary_map_sha256=pins[str(map_path)],command=[sys.executable,'-B',str(checker),'<ROOT admission JSON>','<ROOT admission SHA>','root-named-CS24-TLS64-r1'],required_measured_assertions=dict(whole_borrowed_guestCS24_prefixes=12,source_TLS_refusal_frame64=2),case_raw_policy='Only after SAME current strict receipt.files streamed exact path/hash declaration and whole content hash; direct raw import/read cannot bypass audit',cold_import_policy='Reject all cached.pyc via FileNotFoundError; only exact admitted .py/known seven Python stdlib sources, no unlisted project reads',ROOT_admission_created=False,checker_executed=False)
 p=out/'ROOT-recipe.json';p.write_text(json.dumps(recipe,indent=2)+'\n');pin(p)
 report=dict(passed=True,scope='Code/source-only preparation and required ordinary map; no authoritative ROOT admission or checker run',whole_parent_source_inverse=True,exact_hunks=len(deltas),named_12CS24_2TLS64_assertions_retained=True,source_only_audit=True,cold_import_sources_declared=7,raw_dependency_declarations_not_expanded=True,checker_executed=False,source_machine_executed=False,worker_executed=False,canonical_reader_opened=False,ROOT_admission_created=False,accepted_function_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest());print(hashlib.sha256(checker.read_bytes()).hexdigest())
if __name__=='__main__':main()
