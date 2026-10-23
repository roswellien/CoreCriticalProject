"""UNEXECUTED45 typed candidate mapping; no criteria allowance/configuration."""
from pathlib import Path
import copy,hashlib,json,re,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def typed(a,b):return type(a)is type(b)and a==b
def at(d,key):
 for k in key.split('.'):d=d[k]
 return d
def main(admission_path,admission_sha,manifest_path,manifest_sha,name):
 a=Path(admission_path).resolve();assert sha(a)==admission_sha;A=json.loads(a.read_bytes());assert A['passed']is True and A['terminal45_candidate_mapping_admitted']is True and A['files'][str(Path(__file__).resolve())]==sha(__file__)
 def read(row):
  p=Path(row['path']).resolve();assert p.is_file()and p.stat().st_size<32*1024*1024 and p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');assert A['files'][str(p)]==row['sha256']==sha(p);return json.loads(p.read_bytes())
 M=read(dict(path=manifest_path,sha256=manifest_sha));assert M['schema']=='mw34-terminal45-final-candidate-input-v1';assert M['proposal6']['sha256']=='626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505' and M['mapping45']['sha256']=='79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756';parent=read(M['proposal6']);assert parent['passed']is True and parent['criteria']==841 and parent['status_counts']==dict(identity_candidate=613,finite_delta_candidate=183,unresolved=45)
 assert M['proposal841']['sha256']=='c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4' and parent['files'][str(Path(M['proposal841']['path']).resolve())]==M['proposal841']['sha256'],'Exact parent841 physically declared row table';rows=read(M['proposal841']);mapping=read(M['mapping45']);assert len(rows)==841 and len({(r['gate'],r['baseline_field'])for r in rows})==841 and len(mapping)==45
 original=copy.deepcopy(rows);result=copy.deepcopy(rows);keys={(r['gate'],r['baseline_field']):r for r in result};reports={gate:read(row)for gate,row in M['actual_composite_gates'].items()};assert set(reports)=={'controls_preparation','controls_prelaunch','controls','controls_review'}
 review=reports['controls_review'];assert review['passed']is True and review['controls_sha256']==M['actual_composite_gates']['controls']['sha256']and review['all_named_composite_domains_independently_reviewed']is True and review['all_scoped_physical_edges_verified']is True and review['whole_composite_union_expanded']is True
 targets=set();changes=[]
 for m in mapping:
  key=m['gate'],m['baseline_field'];r=keys[key];assert r['status']=='unresolved'and typed(r['baseline_expected'],m['baseline_expected'])and type(r['baseline_expected']).__name__==m['baseline_type'];gate=reports[m['gate']];assert gate['passed']is True;field=m['composite_field'];value=at(gate,field);assert type(value)is type(r['baseline_expected'])
  if type(value)is bool:assert value is r['baseline_expected'],'No Boolean flip'
  actual=M['actual_composite_gates'][m['gate']];target=(str(Path(actual['path']).resolve()),field);assert target not in targets;targets.add(target)
  # Distinct new composite paths are substantive aliases even when values match.
  proof=M['independent_field_reviews'][m['gate']+':'+m['baseline_field']];assert proof['actual_report_sha256']==actual['sha256']and proof['actual_field']==field and typed(proof['actual_value'],value)and proof['substantive_ROOT_reviewed']is True and proof['physical_domain'].strip()and proof['reason'].strip()
  r.update(current_field=field,current_expected=value,current_report_path=target[0],current_report_sha256=actual['sha256'],status='finite_delta_candidate',physical_domain=proof['physical_domain'],reason=proof['reason'],independent_ROOT_allowance_still_required=True);r.pop('unresolved_reason',None);changes.append(copy.deepcopy(r))
 touched={(m['gate'],m['baseline_field'])for m in mapping};assert len(touched)==45 and touched=={(r['gate'],r['baseline_field'])for r in original if r['status']=='unresolved'}
 for old,new in zip(original,result):
  assert old['gate']==new['gate']and old['baseline_field']==new['baseline_field']and typed(old['baseline_expected'],new['baseline_expected'])
  if (old['gate'],old['baseline_field'])not in touched:assert json.dumps(old,ensure_ascii=True)==json.dumps(new,ensure_ascii=True),'Other796 complete serialized row bytes unchanged'
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir(parents=True)
 for leaf,value in(('criterion-841-proposal.json',result),('new-45-measured-candidates.json',changes)):(out/leaf).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
 (out/'preparation-only.json').write_text(json.dumps(dict(prepared=True,candidate_rows=841,new_measured_candidates=45,other796_unchanged=True,authoritative_allowance_created=False,configuration_created=False,acceptance_executed=False,worker_executed=False,accepted_function_credit=0),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main(*sys.argv[1:])
