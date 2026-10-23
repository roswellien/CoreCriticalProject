"""Immutable twenty-field candidate composition; no allowance/configuration."""
from pathlib import Path
import collections,copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();out.mkdir();pins={}
 def read(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return json.loads(p.read_bytes())
 def pin(p):
  p=Path(p).resolve();pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p.read_bytes()
 old=R/'reports/m4-138-controls-review/criterion-delta-proposal-r4';rows=read(old/'criterion-841-proposal.json','af0a862a6ca64477d31225c3757dba438e66c1aa957bf5632382746a7a4e085c');bindings=read(old/'candidate-33-gate-bindings.json','db28f2796bb2910c9bee618625a4b21c65e4e7baf8556e38bcb9ff8d1d75df4b');original=copy.deepcopy(rows)
 mp=R/'reports/m4-138-criteria-frontier/root-policy-field-measurements-r1/report.json';m=read(mp,'5bbc546137971a2a2ff0b96a9968aaaadab09baa174db33bffdbc65c55882eb0');assert m['passed']is True
 candidates=read(mp.parent/'candidate-field-relations.json',m['files'][str(mp.parent/'candidate-field-relations.json')]);assert len([x for x in candidates if x['candidate']is not None])==16
 ap=R/'reports/m4-138-criteria-frontier/root-policy-field-adverses-r1/report.json';a=read(ap,'36ad27b6859957b147ae42731dd7aa0c238d0c61b835ef29b5f0214957d33bd1');assert a['passed']is True and len(a['adverse_controls'])==17
 rp=R/'reports/m4-138-criteria-frontier/current-policy-field-recommendations-r2/report.json';recommend=read(rp,'fa0660b6dc390f9f2b604485864dea4cb3ed23c812e48a30812a518e9beb0a81')
 cp=R/'reports/m4-138-criteria-frontier/current-policy-field-controller-scope-r2/report.json';controller=read(cp,'22fbcd9545b0d8016797a85eba5746a145ef4f43008876f89a1f55d03246c733');assert controller['passed']is True and controller['bounded_reader_instances']==0 and controller['full_raw_review_closed_claim']is False
 changes={};targets=set()
 def add(g,f,value,path,field,domain,reason):
  key=(g,f);assert key not in changes and (str(path),field)not in targets;targets.add((str(path),field));changes[key]=dict(value=value,path=str(path),sha256=pins[str(path)],field=field,domain=domain,reason=reason)
 for x in candidates:
  if x['candidate']is None:continue
  g=x['gate'];f=x['baseline_field'];value=x['candidate']['value']
  if g=='pair_policy_review'and f=='counts.physically_verified_preparation_files':field='measurements.pair_policy_review.previous_ROOT8_physically_verified_preparation_files'
  elif g=='pair_policy_review'and f in m['measurements']['pair_policy_MFC_scope']:field='measurements.pair_policy_MFC_scope.'+f
  else:field='measurements.'+g+'.'+(f[7:]if g=='controls_equivalence'else f)
  v=m
  for component in field.split('.'):v=v[component]
  assert type(v)is type(value)and v==value
  add(g,f,value,mp,field,x['candidate']['measured_scope'],'ROOT-executed exact retained MFC predicates/source inverse or complete static old14 protocol/selection domain. Three MFC observation limits refer only to unchanged finite original-MFC model. Prior physical3838 seal is reused, not freshly rehashed; final full physical union remains mandatory.')
 scoped={x['field']:x['value']for x in recommend['candidate_policy_scope']};assert len(scoped)==3
 sp=out/'bounded-policy-scope-measurements.json';sp.write_text(json.dumps(dict(passed=True,scope='Supplemental bounded reviewer producer properties only; current paired main/configuration remain separate',measurements=scoped,source_recommendations_path=str(rp),source_recommendations_sha256=pins[str(rp)],worker_executed=False,archive_reader_opened=False,allowance_created=False,files={str(rp):pins[str(rp)]}),indent=2)+'\n');read(sp)
 for x in recommend['candidate_policy_scope']:
  assert x['gate']=='pair_policy_review'
  add(x['gate'],x['field'],x['value'],sp,'measurements.'+x['field'],x['scope'],x['basis'])
 x=controller['candidate'];add(x['gate'],x['field'],x['value'],cp,'candidate.value',x['named_domain'],controller['scope'])
 assert len(changes)==20 and len(rows)==841
 for row in rows:
  key=(row['gate'],row['baseline_field'])
  if key not in changes:continue
  c=changes[key];assert row['status']=='unresolved'and type(c['value'])is type(row['baseline_expected'])
  if isinstance(c['value'],bool):assert c['value']is row['baseline_expected'],'No Boolean flips'
  row.update(current_field=c['field'],current_expected=c['value'],status='finite_delta_candidate',physical_domain=c['domain'],reason=c['reason'],current_receipt_path=c['path'],current_receipt_sha256=c['sha256'],independent_ROOT_allowance_still_required=True)
  row.pop('unresolved_reason',None);bindings[row['gate']].setdefault('perfield_supplement_reports',{})[c['path']]=c['sha256'];bindings[row['gate']]['single_authoritative_composite_gate_still_required']=True
 assert len({(x['gate'],x['baseline_field'])for x in rows})==841
 assert [(x['gate'],x['baseline_field'],type(x['baseline_expected']),x['baseline_expected'])for x in rows]==[(x['gate'],x['baseline_field'],type(x['baseline_expected']),x['baseline_expected'])for x in original]
 for x,y in zip(rows,original):
  if (x['gate'],x['baseline_field'])not in changes:assert x==y
 runtime=pin(R/'tools/m4-runtime/runtime.hpp').decode();memory=pin(R/'runtime/memory/guest_memory.hpp').decode();serializer=pin(R/'reports/m4-fps-native/service-preparation-r3/session_impl.inc').decode()
 hidden=['translations_','services_','continuations_','allocations_','frames_','calls_','heap_cursor_','frozen_','remill_seeded_','poisoned_']
 for f in hidden:assert f in runtime
 assert 'Regions regions_'in memory and 'Permissions permissions'in memory and 'binding->dump' in serializer
 obligations=[dict(gate='controls_preparation',field='control_cases',baseline=12,current_distinct_domain=8,required='ROOT current old12 pre-resource/TLS64 actual cases plus strict refusal/retry/zeroAPI/owned cleanup validation. Current eight post-resource modes must remain separate.'),dict(gate='controls_preparation',field='old_registry_private_vectors_retry_claim',runtime_fields=hidden,source='tools/m4-runtime/runtime.hpp',required='Review exact serializers and Runtime member write/read paths; exported Session/Binding journals do not automatically snapshot Runtime private maps/frame vector. Preserve explicit non-observation scope unless complete member serializer and before/after whole equality exist.'),dict(gate='controls_preparation',field='full_memory_permission_snapshot_claim',fields=['GuestMemory::regions_','Region::bytes','Region::permissions'],source='runtime/memory/guest_memory.hpp',required='Exported pages are bytes only. Check source memory.map/protect/unmap and permission-bearing Region serializer; keep complete permission-map observation excluded unless exact permission-bearing snapshot exists.')]
 for x in obligations:assert next(r for r in rows if(r['gate'],r['baseline_field'])==(x['gate'],x['field']))['status']=='unresolved'
 for leaf,value in [('criterion-841-proposal.json',rows),('candidate-33-gate-bindings.json',bindings),('new-20-policy-field-relations.json',changes and [dict(gate=g,baseline_field=f,**v)for(g,f),v in changes.items()]),('controls-preparation-3-obligations.json',obligations),('remaining-59-field-frontier.json',[x for x in rows if x['status']=='unresolved'])]:
  p=out/leaf;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
 pin(__file__);pin(sys.executable);counts=dict(collections.Counter(x['status']for x in rows));assert counts==dict(identity_candidate=581,finite_delta_candidate=201,unresolved=59)
 report=dict(passed=True,scope='Proposal5 candidate composition only;20 measured domain-specific relations; no authoritative allowance/configuration/acceptance',criteria=841,distinct_criteria=841,new_fields=20,status_counts=counts,types_and_baseline_values_unchanged=True,Boolean_values_unchanged=True,all_other821_rows_identical=True,controls_preparation3_unresolved=True,full_raw_controls_closed_claim=False,fresh_full_union_required=True,worker_executed=False,archive_reader_opened=False,allowance_created=False,configuration_created=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
