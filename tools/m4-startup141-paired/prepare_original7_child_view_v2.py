"""Prepare pure typed child-view controls from bounded real receipt metadata.

Synthetic case selectors test binding guards; no actual source artifact rows or
export payloads are evaluated. Large child artifact whole hashes remain a future
admitted consumer prerequisite, not a claim of this preparation.
"""
from pathlib import Path
import ast,copy,hashlib,json

R=Path(__file__).resolve().parents[2]

def main():
 out=R/'reports/m4-startup141-paired/original7-child-view-preparation-r1';assert not out.exists()
 files={}
 def read(p):
  p=Path(p).resolve();assert p.stat().st_size<4*1024*1024 and p.suffix in('.json','.py')
  raw=p.read_bytes();files[str(p)]=hashlib.sha256(raw).hexdigest();return raw
 hp=R/'tools/m4-startup141-paired/original7_child_view_v1.py';raw=read(hp);tree=ast.parse(raw.decode());env={};exec(compile(tree,str(hp),'exec'),env)
 aggpath=R/'reports/m4-original141-source/source-r7/report.json';agg=json.loads(read(aggpath));assert files[str(aggpath)]==env['AGGREGATE_SHA']
 op=R/'reports/m4-original141/source-preparation-r6/selected-order.json';order=json.loads(read(op));packets={}
 for family,(folder,h,roots,leaves)in env['FAMILIES'].items():
  rp=R/folder/'report.json';report=json.loads(read(rp));assert files[str(rp)]==h
  refs={leaf:dict(path=str(rp.parent/leaf),sha256=report['files'][str(rp.parent/leaf)])for leaf in leaves}
  rows=[]
  for sequence in range(6):
   for root,phase in roots:
    row=dict(sequence=sequence,root=root,phase=phase)
    if family=='constructor18':row=copy.deepcopy(next(r for r in report['cases']if(r['sequence'],r['root'])==(sequence,root)))
    if family=='tree':
     q=Path(str(rp.parent)+'-case-'+str(sequence))/'report.json';row=dict(sequence=sequence,path=str(q),sha256=report['files'][str(q)],source=dict(sequence=sequence,phase=phase))
    rows.append(row)
  packets[family]=dict(report_path=str(rp),report_sha256=h,report=report,artifacts=refs,rows=rows)
 def invoke(a=agg,p=packets,o=order,h=env['AGGREGATE_SHA'],path=str(aggpath)):
  return env['build_view'](path,h,a,p,o)
 result=invoke();assert len(result['cases'])==120 and result['accepted_function_credit']==0 and result['complete_paired141_gate']is False
 controls=[dict(name='positive_real_metadata_synthetic_case_selectors',rejected=False)]
 mutations=[
  ('altered_aggregate_sha',lambda a,p,o:a.update(raw_export_report_sha256='0'*64)),
  ('wrong_original_validation',lambda a,p,o:a.update(original_validation_sha256='0'*64)),
  ('source_AFTER_seed',lambda a,p,o:a.update(source_AFTER_seed=True)),
  ('whole_original_State_claim',lambda a,p,o:a.update(whole_original_State_claim=True)),
  ('whole_original846_CPU_claim',lambda a,p,o:a.update(full_original846_CPU_execution_claim=True)),
  ('missing_family',lambda a,p,o:p.pop('tree')),
  ('duplicate_family_children',lambda a,p,o:a['children'].__setitem__(5,copy.deepcopy(a['children'][0]))),
  ('report_path_alias',lambda a,p,o:p['tree'].update(report_path=p['new_MFC']['report_path'])),
  ('report_SHA_alias',lambda a,p,o:p['tree'].update(report_sha256=p['new_MFC']['report_sha256'])),
  ('artifact_namespace_substitution',lambda a,p,o:p['widget']['artifacts']['source-derivations.json'].update(path=p['formatter4']['artifacts']['source-derivations.json']['path'])),
  ('artifact_SHA_substitution',lambda a,p,o:p['widget']['artifacts']['source-derivations.json'].update(sha256='0'*64)),
  ('duplicate_case',lambda a,p,o:p['formatter4']['rows'].__setitem__(1,copy.deepcopy(p['formatter4']['rows'][0]))),
  ('missing_case',lambda a,p,o:p['old4']['rows'].pop()),
  ('wrong_sequence',lambda a,p,o:p['new_MFC']['rows'][0].update(sequence=6)),
  ('wrong_root',lambda a,p,o:p['formatter4']['rows'][0].update(root=0x5ae3e4)),
  ('wrong_phase',lambda a,p,o:p['widget']['rows'][0].update(phase=15)),
  ('wrong_selected_order',lambda a,p,o:o[86].update(entry=0x5ae3e4)),
  ('tree_child_case_namespace',lambda a,p,o:p['tree']['rows'][0].update(path=p['tree']['rows'][1]['path'])),
  ('tree_child_case_sha',lambda a,p,o:p['tree']['rows'][0].update(sha256='0'*64)),
  ('constructor_endpoint_claim',lambda a,p,o:p['constructor18']['rows'][0].update(whole_FX512=False)),
  ('invent_native_widget_ENV',lambda a,p,o:p['widget']['report'].update(native_ENV_projection_proven=True)),
  ('invent_paired_widget_ENV',lambda a,p,o:p['widget']['report'].update(paired_ENV_projection_proven=True)),
  ('invent_widget_shutdown',lambda a,p,o:p['widget']['report'].update(source_shutdown_executed=True)),
  ('invent_tree_State',lambda a,p,o:p['tree']['report'].update(whole_original_State_claim=True)),
 ]
 for name,change in mutations:
  a,p,o=copy.deepcopy((agg,packets,order));change(a,p,o);rejected=False
  try:invoke(a,p,o)
  except(AssertionError,KeyError,ValueError):rejected=True
  assert rejected,name;controls.append(dict(name=name,rejected=True))
 out.mkdir(parents=True)
 q=out/'synthetic-controls.json';q.write_text(json.dumps(dict(pure_controls=True,controls=controls,actual_child_artifact_rows_executed=False,actual_source_view_created=False),indent=2)+'\n');files[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
 inventory=[dict(family=f,report_path=env['location'](folder+'/report.json'),report_sha256=h,case_extent=6*len(roots),roots_and_phases=[dict(root=r,phase=p)for r,p in roots],required_artifact_leaves=list(leaves),available_claims=env['CLAIMS'][f])for f,(folder,h,roots,leaves)in env['FAMILIES'].items()]
 q=out/'family-contract.json';q.write_text(json.dumps(inventory,indent=2)+'\n');files[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
 files[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 q=out/'preparation-only.json';q.write_text(json.dumps(dict(prepared_only=True,helper_source_AST_checked=True,pure_controls=len(controls),adverses=len(mutations),real_six_report_identity_metadata_checked=True,actual_artifact_rows_not_consumed=True,all_artifact_bytes_physical_rehash_pending=True,caller_authenticated_whole_artifacts_required=True,typed_view_actual_execution_pending=True,whole_original_State_claim=False,complete_pair_gate=False,eligibility_declared=False,source_models_executed=False,export_reader_opened=False,canonical_reader_opened=False,worker_launched=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))

if __name__=='__main__':main()
