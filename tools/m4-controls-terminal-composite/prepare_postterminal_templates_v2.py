"""Two-stage data templates (v2: bindings carry per-field pinned ROOT measurement sources); never finalizer/config/checker/allowance."""
from pathlib import Path
import ast,copy,hashlib,json,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
POLICY_SHA='4fa464674bd2f0b5d1558fc6e1fbe8e847d3d12267689280f6e1e73f60326b86'
BASE_SHA='ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(row):
 p=Path(row['path']).resolve();assert p.stat().st_size<32*1024*1024 and p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');assert sha(p)==row['sha256'];return json.loads(p.read_bytes())
def at(d,k):
 for part in k.split('.'):d=d[part]
 return d
def final45(request):
 assert request['schema']=='mw34-root-postterminal-final45-request-v1'
 parent=read(request['proposal6']);rows=read(request['proposal841']);mapping=read(request['mapping45']);review=read(request['ROOT_field_review'])
 assert request['proposal6']['sha256']=='626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505'and request['proposal841']['sha256']=='c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4'and request['mapping45']['sha256']=='79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756'
 assert parent['criteria']==841 and parent['status_counts']==dict(identity_candidate=613,finite_delta_candidate=183,unresolved=45)
 assert review['passed']is True and review['independent_review']is True and review['fields_reviewed']==45,'ROOT supplied substantive field review, not author approval'
 gates=request['actual_composite_gates'];assert set(gates)=={'controls_preparation','controls_prelaunch','controls','controls_review'};actual={k:read(v)for k,v in gates.items()};r=actual['controls_review'];h=gates['controls']['sha256']
 assert r['passed']is True and r['controls_sha256']==r['controls_verification_sha256']==h and r['all_bounded_readers_closed']is True and all(r[k]is True for k in('all_named_composite_domains_independently_reviewed','all_scoped_physical_edges_verified','whole_composite_union_expanded'))and r['final_input_conservation']['metadata_only_cache_used']is False
 assert len(rows)==841 and len(mapping)==45 and len(review['per_field_reviews'])==45
 given=review['per_field_reviews'];touched=set();targets=set()
 for m in mapping:
  key=m['gate']+':'+m['baseline_field'];p=given[key];v=at(actual[m['gate']],m['composite_field']);assert p['actual_report_sha256']==gates[m['gate']]['sha256']and p['actual_field']==m['composite_field']and type(p['actual_value'])is type(v)and p['actual_value']==v and p['substantive_ROOT_reviewed']is True
  assert type(v).__name__==m['baseline_type']and(type(v)is not bool or v is m['baseline_expected']);assert len(p['physical_domain'].strip())>=12 and len(p['reason'].strip())>=24
  assert key not in touched and(m['gate'],m['composite_field'])not in targets;touched.add(key);targets.add((m['gate'],m['composite_field']))
 return dict(schema='mw34-terminal45-final-candidate-input-v1',proposal6=request['proposal6'],proposal841=request['proposal841'],mapping45=request['mapping45'],actual_composite_gates=gates,independent_field_reviews=given)
def bindings(request):
 assert request['schema']=='mw34-root-postterminal-bindings-request-v1'
 parent=read(request['proposal841']);new=read(request['finalized841']);gate_review=read(request['ROOT_all39_review']);gates=request['gates']
 assert request['proposal841']['sha256']=='c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4'and len(parent)==len(new)==841
 assert gate_review['passed']is True and gate_review['independent_review']is True and gate_review['gates_reviewed']==39 and gate_review['baseline_predicates_reviewed']==841
 baseline=read(dict(path=str(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json'),sha256=BASE_SHA));policy_path=R/'tools/m4-138-controls-review/acceptance138_criteria_v1.py';assert sha(policy_path)==POLICY_SHA;P=types.ModuleType('sealed_pure_criteria_only');exec(compile(policy_path.read_text(),str(policy_path),'exec'),P.__dict__)
 source=R/'tools/m4-joint-startup131/acceptance.py';assert sha(source)=='acff64932fa310a4b3290e2a9837432f656f81b3981132b8815372f88ec78f5b';tree=ast.parse(source.read_text());base=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets));required=base|{'source_widget_journal_review','source_widget_memory_review','source_widget_semantic_review','controls_full_raw','controls_gdi_owners','controls_current_link'}
 assert set(gates)==required and len(gates)==39 and gate_review['gates']==gates
 equal={};coverage={};translations={};untouched=0;touched=0
 for old,row in zip(parent,new):
  assert(old['gate'],old['baseline_field'])==(row['gate'],row['baseline_field'])and P.typed(old['baseline_expected'],row['baseline_expected']);label=row['gate'];field=row['baseline_field'];assert P.typed(row['baseline_expected'],baseline['gates'][label]['equal'][field])
  if old['status']!='unresolved':assert json.dumps(old,ensure_ascii=True)==json.dumps(row,ensure_ascii=True);untouched+=1
  else:touched+=1
  assert row['status']!='unresolved'and label in gates and set(gates[label])=={'path','sha256'}
  measured=gate_review['measured_gate_fields'][label];assert measured['path']==gates[label]['path']and measured['sha256']==gates[label]['sha256'];value=measured['fields'][row['current_field']];assert P.typed(value,row['current_expected'])
  source=measured.get('sources',{}).get(row['current_field'])
  if source is not None:assert set(source)=={'path','sha256'}and sha(Path(source['path']))==source['sha256']and json.loads(Path(source['path']).read_bytes())['passed']is True
  delta=None
  if row['current_field']!=field or not P.typed(value,row['baseline_expected']):delta=dict(baseline_expected=row['baseline_expected'],current_field=row['current_field'],current_expected=value,physical_domain=row['physical_domain'],reason=row['reason']);translations.setdefault(label,{})[field]=delta
  relation=P.relation(field,row['baseline_expected'],value,delta);equal.setdefault(label,{})[row['current_field']]=value;assert field not in coverage.setdefault(label,{});coverage[label][field]=relation
 assert untouched==796 and touched==45
 proposed=P.validate(dict(gates={k:dict(equal=v)for k,v in equal.items()},baseline_criteria=coverage),baseline,base)
 return dict(gates=gates,field_translations=translations,field_sources={k:v['sources']for k,v in gate_review['measured_gate_fields'].items()if v.get('sources')}),dict(other796_complete_row_bytes_unchanged=True,all841_typed_fields_checked=True,necessary_finite_translations=proposed,authoritative_allowances_created=False,configuration_created=False,acceptance_executed=False,accepted_function_credit=0)
def main(stage,request_path,request_sha,output):
 request=read(dict(path=request_path,sha256=request_sha));out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True)
 if stage=='final45':value=final45(request);proof=dict(finalizer_executed=False,ROOT_field_review_passthrough_only=True,accepted_function_credit=0)
 elif stage=='bindings':value,proof=bindings(request)
 else:raise ValueError('Explicit final45 or bindings stage only')
 (out/'candidate-input.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');(out/'preparation-only.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main(*sys.argv[1:])
