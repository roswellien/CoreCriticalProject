"""Execute only finalizer3 pure typed-row policy, never its main/import/I/O."""
from pathlib import Path
import ast,copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(output):
 out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True);p=R/'tools/m4-controls-terminal-composite/finalize45_v3.py';tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');start=next(i for i,n in enumerate(fn.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='original'for t in n.targets));stop=next(i for i,n in enumerate(fn.body)if isinstance(n,ast.Assert)and're.fullmatch'in ast.unparse(n));body=fn.body[start:stop];code=compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(p)+'::pure-rows','exec')
 rp=R/'reports/m4-138-controls-review/root-criterion-delta-proposal-r6/criterion-841-proposal.json';mp=R/'reports/m4-138-criteria-frontier/terminal45-typed-recipe-r1/pending45-terminal-field-mapping.json';dp=R/'reports/m4-controls-terminal-composite/field-disposition-r1/per-field-disposition.json';rows=json.loads(rp.read_text());mapping=json.loads(mp.read_text());disposition=json.loads(dp.read_text());reports={g:{}for g in ('controls_preparation','controls_prelaunch','controls','controls_review')};gates={g:dict(path=str(out/g),sha256=('a'if g=='controls'else'b')*64)for g in reports};proofs={}
 def assign(d,k,v):
  parts=k.split('.')
  for part in parts[:-1]:d=d.setdefault(part,{})
  d[parts[-1]]=v
 def at(d,k):
  for part in k.split('.'):d=d[part]
  return d
 for m,d in zip(mapping,disposition):
  v=d['supported_value_before_composer']
  if v is None:v='a'*64 if m['baseline_type']=='str'else 10691906
  assign(reports[m['gate']],m['composite_field'],v);proofs[m['gate']+':'+m['baseline_field']]=dict(actual_report_sha256=gates[m['gate']]['sha256'],actual_field=m['composite_field'],actual_value=v,substantive_ROOT_reviewed=True,physical_domain=m['physical_domain'],reason='Synthetic scoped proof only; actual named physical source admission remains required before any production run.')
 for d in reports.values():d['passed']=True
 reports['controls_review'].update(controls_sha256='a'*64,all_named_composite_domains_independently_reviewed=True,all_scoped_physical_edges_verified=True,whole_composite_union_expanded=True)
 M=dict(actual_composite_gates=gates,independent_field_reviews=proofs)
 def run(ma=mapping,re=reports,manifest=M):
  env=dict(copy=copy,json=json,Path=Path,typed=lambda a,b:type(a)is type(b)and a==b,at=at,read=lambda r:re[next(g for g,v in gates.items()if v['path']==r['path'])],rows=copy.deepcopy(rows),mapping=copy.deepcopy(ma),M=copy.deepcopy(manifest));exec(code,env);return env
 positive=run();assert len(positive['result'])==841 and len(positive['changes'])==45 and sum(x['status']=='identity_candidate'for x in positive['result'])==613 and sum(x['status']=='finite_delta_candidate'for x in positive['result'])==228
 assert all(json.dumps(o)==json.dumps(n)for o,n in zip(rows,positive['result'])if o['status']!='unresolved');rejects=[]
 def bad(name,mut):
  ma,re,m=copy.deepcopy((mapping,reports,M));mut(ma,re,m)
  try:run(ma,re,m)
  except (AssertionError,KeyError):rejects.append(name);return
  raise AssertionError('Must refuse '+name)
 bad('wrong-scoped-report-SHA',lambda ma,re,m:m['independent_field_reviews']['controls_preparation:control_cases'].__setitem__('actual_report_sha256','0'*64))
 bad('missing-causal-reason',lambda ma,re,m:m['independent_field_reviews']['controls_preparation:control_cases'].__setitem__('reason',''))
 bad('missing-domain',lambda ma,re,m:m['independent_field_reviews']['controls_preparation:control_cases'].__setitem__('physical_domain',''))
 bad('Boolean-scope-flip',lambda ma,re,m:re['controls_preparation'].__setitem__('old_registry_private_vectors_retry_claim',True))
 bad('counter-type-coercion',lambda ma,re,m:re['controls_preparation'].__setitem__('control_cases',True))
 bad('partial45-domain',lambda ma,re,m:ma.pop())
 bad('unexpanded-review',lambda ma,re,m:re['controls_review'].__setitem__('whole_composite_union_expanded',False))
 bad('wrong-new-controls-link',lambda ma,re,m:re['controls_review'].__setitem__('controls_sha256','0'*64))
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,pure_original_finalizer_AST_row_policy_used=True,finalizer_imported=False,finalizer_main_invoked=False,configurator_imported=False,synthetic_scoped_proofs_not_ROOT_admission=True,actual_parent_rows=841,other796_complete_serialized_rows_unchanged=True,retained_parent_identity=613,retained_parent_finite=183,finalizer_new_finite_candidate_rows=45,necessary_configuration_translations_must_be_derived_separately=True,adverse_controls=rejects,allowance_created=False,configuration_created=False,accepted_function_credit=0,files={str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in (p,rp,mp,dp,Path(__file__).resolve())}),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),adverses=len(rejects))))
if __name__=='__main__':main(sys.argv[1])
