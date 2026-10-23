"""Immutable841 perfield measured candidate composition; no allowances/configuration."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def at(d,f):
 for k in f.split('.'):d=d[int(k)]if isinstance(d,list)else d[k]
 return d
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();out.mkdir();pins={}
 def read(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return json.loads(p.read_bytes())
 parent=R/'reports/m4-138-controls-review/criterion-delta-proposal-r3';g=read(parent/'report.json','f9639908dc663a96f833dc18f97f71b06d5c52b4c23fb716e4788419222d4889');rows=read(parent/'criterion-841-proposal.json',g['files'][str((parent/'criterion-841-proposal.json').resolve())]);gates=read(parent/'candidate-33-gate-bindings.json',g['files'][str((parent/'candidate-33-gate-bindings.json').resolve())]);assert len(rows)==841
 # All841 baseline identities/types are immutable even where their values change.
 baseline=read(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json','ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7');assert len(baseline['gates'])==33 and sum(len(v['equal'])for v in baseline['gates'].values())==841
 schema_path=R/'reports/m4-138-criteria-frontier/root-schema-measurements-r6/report.json';schema=read(schema_path,'143240fa5d5c35e6a6d1149b58aef20d9381c39846a1cf015307663356c91943');assert schema['passed']and not schema['worker_launched']and not schema['allowance_created']
 inherited_path=R/'reports/m4-138-criteria-frontier/root-inherited-source-field-measurements-r1/report.json';inherited=read(inherited_path,'eb4dd5ebf5ee7188dc6869300ceca62a7269271b8ddc08b7bbb9a0e52cd1218c');assert inherited['passed']and inherited['historical_physical_file_counts']=={'source_preflight':83,'source_legacy_flags':10}
 cp=inherited_path.parent/'candidate-field-relations.json';relations=read(cp,inherited['files'][str(cp.resolve())]);assert len(relations)==22
 by={(r['gate'],r['baseline_field']):r for r in rows};added=[]
 def bind(label,field,path,record,target,domain,reason):
  r=by[label,field];assert r['status']=='unresolved';old=baseline['gates'][label]['equal'][field];assert type(r['baseline_expected'])is type(old)and r['baseline_expected']==old
  value=at(record,target);assert type(value)is type(old);assert not isinstance(old,bool)or value==old
  r.update(current_field=target,current_expected=value,current_report_path=str(path.resolve()),current_report_sha256=pins[str(path.resolve())],status='identity_candidate'if value==old else'finite_delta_candidate',physical_domain=domain,reason=reason,authoritative_role_or_allowance_admission=False);r.pop('unresolved_reason',None)
  gates[label].setdefault('perfield_supplement_reports',{})[str(path.resolve())]=pins[str(path.resolve())];gates[label]['single_authoritative_composite_gate_still_required']=True
  added.append(dict(gate=label,baseline_field=field,current_field=target,current_expected=value,current_report_path=str(path.resolve()),physical_domain=domain,reason=reason))
 for c in relations:
  bind(c['gate'],c['baseline_field'],inherited_path,inherited,c['current_field'],c['physical_domain'],c['reason'])
 schema_counts=Counter()
 for r in rows:
  if r['status']!='unresolved':continue
  label=r['gate'];field=r['baseline_field'];key='source_preparation_inherited_TIB'if label=='source_preparation'else label
  if key not in schema['measurements']:continue
  target='measurements.'+key+'.'+field
  try:value=at(schema,target)
  except(KeyError,IndexError,TypeError,ValueError):continue
  domain={'native_prelaunch':'Current positive worker physical borrowed5/pointer6/CRT3/IAT7 and14bridges/539calls/TLS/link/caller/build dependency domains; counts from currentpositive compile only','original_preparation':'Current genuine original observer43recordpages and exact12MFC domainlayout + trueTIB8192/prerequisite observation-only scope','original_prelaunch':'Current original observer132wholepackpages, actualliteral packdelta/unchanged6observerfiles/currentcompiled MFCASM/formattertargets and266owned workerCL.read inputs','source_preparation':'Inherited adjacent-TIB puremodel representation repair only; does not describe widget extension or wholecurrent sourcepreparation'}[label]
  reason='Actual ROOTschema6 physically measured exact same named baseline obligation. Every scalar/Boolean keeps its type and domain; no success-collapse.'
  if label=='native_prelaunch'and field=='counts.whole_unchanged_positive_component_files':
   assert value==75 and schema['measurements']['native_prelaunch']['counts']['whole_inherited_positive_file_domain']==77 and schema['measurements']['native_prelaunch']['counts']['whole_exact_inverse_positive_component_files']==2
   reason='Exactly75wholebyteequal positive files plus two separately proven changed-file inverses. This field counts only75unchanged;77total with2finite inverses is a different physical scope. No changed-file Boolean is relabeled unchanged; no controlworker equivalence claim.'
  if label=='original_prelaunch'and field=='counts.whole_unchanged_accepted_observers':
   assert value==6 and len(schema['measurements']['original_prelaunch']['changed_old_observer_files'])==3
   reason='Exactly6wholeunchanged observer files; the three genuinely changed files have a separate unresolved/currentcompiled inverse scope, never wholebytes-equal.'
  if label=='source_preparation':reason='Retained exactTIBrepair named field; nonTIB_memory_change=False concerns that representation-only repair, not new widgets/current wholememory.'
  bind(label,field,schema_path,schema,target,domain,reason);schema_counts[label]+=1
 assert schema_counts=={'native_prelaunch':17,'original_preparation':4,'original_prelaunch':6,'source_preparation':5}
 # Ensure all841 distinct obligations and unique target paths survive composition.
 assert len(by)==841
 for label in baseline['gates']:
  selected=[r for r in rows if r['gate']==label and r['current_field']is not None];assert len({r['current_field']for r in selected})==len(selected)
 counts=Counter(r['status']for r in rows);assert counts['unresolved']==79
 deltas={}
 for r in rows:
  if r['status']=='finite_delta_candidate':
   d={k:r[k]for k in('baseline_expected','current_field','current_expected','physical_domain','reason')};deltas.setdefault(r['gate'],{})[r['baseline_field']]=d
 for leaf,data in [('criterion-841-proposal.json',rows),('candidate-33-gate-bindings.json',gates),('finite-delta-proposal.json',deltas),('new-54-measured-field-relations.json',added),('remaining-79-field-frontier.json',[r for r in rows if r['status']=='unresolved'])]:
  p=out/leaf;p.write_text(json.dumps(data,indent=2)+'\n');pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(Path(__file__))
 r=dict(passed=True,scope='Immutable841 typed candidate field composition from actualROOTschema6 and ROOT22 inheritedmeasurements; authoritative wholegate/allowance composition remains open',baseline_gates=33,baseline_predicates=841,counts=dict(counts),new_measured_field_candidates=54,inherited_or_renamed_or_identity_fields=22,current_same_named_schema_fields=32,schema_fields_by_gate=dict(schema_counts),remaining_by_gate=dict(Counter(r['gate']for r in rows if r['status']=='unresolved')),all841_typed_targets_resolved=False,single_authoritative_composite_gate_still_required=True,controls_worker_physical_equivalence_inferred_from_positive_worker=False,genuinely_changed_positive_files_not_counted_unchanged=True,authoritative_allowance_created=False,criteria_translation_reviewed=False,configuration_created=False,worker_executed=False,raw_export_reader_opened=False,capture_archive_reader_opened=False,fullraw_report_opened=False,initializer_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'sha256':sha(p),'counts':dict(counts),'remaining':r['remaining_by_gate']}))
if __name__=='__main__':main(sys.argv[1])
