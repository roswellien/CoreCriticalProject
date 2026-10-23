"""Immutable fourteen-field proposal6 composition; ROOT executes after review."""
from pathlib import Path
import collections, copy, hashlib, json, sys, traceback
R=Path(__file__).resolve().parents[2]
PARENT_SHA='9e4d9dd58f34bafae4c8a4368f1fbaa0c89b91ffd3ca1e895d14470505534f3d'
REVIEW_SHA='cb1d8b5fd4eae31ba3c062289b54de5e1f2c1ef4245a1b911652a45da0f7ff10'
CURRENT_SHA='4c961184ef9442788eef3eba69bd37dc85427f123d4494ed30d6fa7e0123f83f'
EXPECTED_FIELDS={
 'worker_launched','source_AFTER_seed','whole_new_manager_CRT_TIB_endpoint_observations_declared',
 'counts.whole_genuine_borrowed_BEFORE_relations','counts.exact_consumed_pointer_projections',
 'counts.finite_three_CRT_cell_source_relations','counts.owning_raw_IAT_relations',
 'counts.whole_current_typed_bridge_functions','counts.whole_typed_bridge_relocation_targets',
 'counts.actual_missing_thunk_source_CALL_targets','counts.whole_linked_literal_functions',
 'counts.whole_linked_changed_adapter_functions','counts.whole_hardware_caller_boundaries',
 'counts.current_compiler_dependency_paths'}

def typed_equal(a,b):return type(a)is type(b)and a==b
def value_at(obj,field):
 for part in field.split('.'):obj=obj[part]
 return obj

def compose(rows,candidates,current,current_path):
 assert len(rows)==841 and len({(r['gate'],r['baseline_field'])for r in rows})==841
 assert len(candidates)==14 and {r['baseline_field']for r in candidates}==EXPECTED_FIELDS
 original=copy.deepcopy(rows);result=copy.deepcopy(rows);bykey={(r['gate'],r['baseline_field']):r for r in result};targets=set();changes=[]
 for c in candidates:
  assert c['gate']=='controls_prelaunch'and c['authoritative_allowance']is False and c['authoritative_composite_gate_still_required']is True
  key=(c['gate'],c['baseline_field']);r=bykey[key];assert r['status']=='unresolved'
  assert typed_equal(r['baseline_expected'],c['baseline_expected']) and c['baseline_type']==type(r['baseline_expected']).__name__
  assert Path(c['current_report_path']).resolve()==current_path.resolve()and c['current_report_sha256']==CURRENT_SHA
  assert c['current_field']=='measurements.current8_shared_MFC_prelaunch.'+c['baseline_field']
  target=(str(current_path.resolve()),c['current_field']);assert target not in targets;targets.add(target)
  actual=value_at(current,c['current_field']);assert typed_equal(actual,c['current_expected'])and type(actual)is type(r['baseline_expected'])
  if isinstance(actual,bool):assert actual is r['baseline_expected'],'No Boolean flip'
  status='identity_candidate'if typed_equal(actual,r['baseline_expected'])else'finite_delta_candidate'
  assert c['status']==status and isinstance(c['physical_domain'],str)and c['physical_domain'].strip()and isinstance(c['reason'],str)and c['reason'].strip()
  if status=='finite_delta_candidate':assert c['baseline_field']=='counts.current_compiler_dependency_paths'and r['baseline_expected']==16118 and actual==16092
  r.update(current_field=c['current_field'],current_expected=actual,status=status,physical_domain=c['physical_domain'],reason=c['reason'],current_report_path=str(current_path.resolve()),current_report_sha256=CURRENT_SHA,independent_ROOT_allowance_still_required=True)
  r.pop('unresolved_reason',None);changes.append(copy.deepcopy(c))
 changed={(c['gate'],c['baseline_field'])for c in candidates}
 for old,new in zip(original,result):
  assert old['gate']==new['gate']and old['baseline_field']==new['baseline_field']and typed_equal(old['baseline_expected'],new['baseline_expected'])
  if (old['gate'],old['baseline_field'])not in changed:assert new==old,'Other827 rows changed'
 assert sum(x!=y for x,y in zip(original,result))==14
 counts=dict(collections.Counter(r['status']for r in result));assert counts==dict(identity_candidate=613,finite_delta_candidate=183,unresolved=45),counts
 assert sum(r['gate']=='controls_prelaunch'and r['status']=='unresolved'for r in result)==7
 return result,changes,counts

def main(name):
 assert name and Path(name).name==name
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();out.mkdir();pins={};passed=False;details={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'and p.stat().st_size<32*1024*1024
  raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return raw
 def read(p,h=None):return json.loads(pin(p,h))
 try:
  parent_path=R/'reports/m4-138-controls-review/criterion-delta-proposal-r5-r4/report.json';parent=read(parent_path,PARENT_SHA)
  assert parent['passed']is True and parent['criteria']==841 and parent['status_counts']==dict(identity_candidate=600,finite_delta_candidate=182,unresolved=59)
  rows_path=parent_path.parent/'criterion-841-proposal.json';bindings_path=parent_path.parent/'candidate-33-gate-bindings.json'
  rows=read(rows_path,parent['files'][str(rows_path)]);bindings=read(bindings_path,parent['files'][str(bindings_path)]);assert len(bindings)==33
  review_path=R/'reports/m4-138-criteria-frontier/root-current-controls-field-review-r1/report.json';review=read(review_path,REVIEW_SHA)
  assert review['passed']is True and review['current8_fields']==14 and review['current8_identity_candidates']==13 and review['current8_finite_delta_candidates']==1 and review['legacy7_pending']is True
  assert review['worker_executed']is False and review['canonical_reader_opened']is False and review['authoritative_allowance']is False
  candidate_path=review_path.parent/'current14-field-candidates.json';candidates=read(candidate_path,review['files'][str(candidate_path)])
  current_path=R/'reports/m4-138-criteria-frontier/root-current8-physical-review-r5/report.json';current=read(current_path,CURRENT_SHA);assert current['passed']is True
  result,changes,counts=compose(rows,candidates,current,current_path)
  oldbindings=copy.deepcopy(bindings)
  b=bindings['controls_prelaunch'];b.setdefault('perfield_supplement_reports',{})[str(current_path)]=CURRENT_SHA;b['single_authoritative_composite_gate_still_required']=True
  assert all(bindings[k]==oldbindings[k]for k in bindings if k!='controls_prelaunch')
  adverse=[]
  def reject(label,change):
   altered=copy.deepcopy(candidates);change(altered)
   try:compose(rows,altered,current,current_path)
   except (AssertionError,KeyError):adverse.append(label);return
   raise AssertionError('Adverse accepted: '+label)
  reject('duplicate current target',lambda c:c[1].update(current_field=c[0]['current_field']))
  reject('Boolean flip',lambda c:c[0].update(current_expected=True))
  reject('baseline typed value mutation',lambda c:c[0].update(baseline_expected=0))
  reject('scalar type coercion',lambda c:next(x for x in c if x['baseline_field']=='counts.whole_current_typed_bridge_functions').update(current_expected=True))
  reject('success-only field collapse',lambda c:c[0].update(current_field='passed'))
  reject('arbitrary finite count',lambda c:next(x for x in c if x['baseline_field']=='counts.current_compiler_dependency_paths').update(current_expected=16100))
  reject('missing physical reason',lambda c:c[0].update(reason=''))
  reject('wrong source receipt',lambda c:c[0].update(current_report_sha256='0'*64))
  for leaf,data in [('criterion-841-proposal.json',result),('candidate-33-gate-bindings.json',bindings),('new-14-current-controls-field-relations.json',changes),('remaining-45-field-frontier.json',[x for x in result if x['status']=='unresolved'])]:
   p=out/leaf;p.write_text(json.dumps(data,indent=2)+'\n');pin(p)
  details=dict(criteria=841,distinct_criteria=841,new_fields=14,status_counts=counts,all_other827_rows_identical=True,types_and_baseline_values_unchanged=True,Boolean_values_unchanged=True,legacy7_controls_prelaunch_unresolved=True,adverse_controls=adverse,parent_report_path=str(parent_path),parent_report_sha256=PARENT_SHA,ROOT_field_review_path=str(review_path),ROOT_field_review_sha256=REVIEW_SHA)
  passed=True
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());pin(out/'failure.txt')
 finally:
  pin(__file__);pin(sys.executable)
  report=dict(passed=passed,scope='Proposal6 recommendations only; exact14 ROOT-reviewed field translations; no acceptance allowance/configuration',**details,full_raw_controls_closed_claim=False,fresh_full_union_required=True,worker_executed=False,archive_reader_opened=False,allowance_created=False,configuration_created=False,accepted_function_credit=0,files=pins)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
 if not passed:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
