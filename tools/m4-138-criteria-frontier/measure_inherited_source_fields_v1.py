"""Narrow retained-repair/legacy field composition and four exact renames/two identities."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def at(d,f):
 for k in f.split('.'):d=d[int(k)]if isinstance(d,list)else d[k]
 return d
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 baseline=read(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json','ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7')
 frontier_path=R/'reports/m4-138-criteria-frontier/bounded-frontier-r3/report.json';frontier=read(frontier_path);assert frontier['passed']and frontier['historical_legacy_all10_physical_inputs_rehashed']and frontier['historical_preflight_all83_physical_inputs_rehashed']
 closure_path=R/'reports/m4-tree-review/source138-closure-r1/report.json';closure=read(closure_path,'fc2453e5a9ff713d122f73e3a165edbdcc43da1b31c18f8bae787e6d6b43b38b');assert closure['passed']and closure['source_provider_sha256']=='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'
 code=pin(R/'tools/m4-138-controls-review/seal_source6_closure.py',closure['files'][str((R/'tools/m4-138-controls-review/seal_source6_closure.py').resolve())]).read_text();assert 'for record in(current_preparation,current_preflight):'in code and 'joint131-source-preflight-r4/report.json'in code
 current=read(R/'reports/m4-joint-startup138-source/preparation-r11/report.json','addd156cf83cf33776395bc55e958af83a1cdbca61ebcfc2af2d07ad9c821d72');entry=pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py',closure['files'][str((R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py').resolve())]).read_text();assert "J=load('persistent54_accepted27',ROOT/'tools/m4-joint-startup27-review/observe.py')"in entry and 'm,c,inst,schedule=J.models()'in entry
 measured={};bindings=[];histcounts={}
 for label in('source_preflight','source_legacy_flags'):
  b=baseline['gates'][label];d=read(R/b['path'],b['sha256']);assert d['passed'];histcounts[label]=len(d['files']);measured[label]={}
  for p,h in d['files'].items():assert frontier['files'].get(p)==closure['files'].get(p)==h;pin(p,h)
  for field,old in b['equal'].items():
   value=at(d,field);assert type(value)is type(old)and value==old
   # Use distinct flat field leaves per gate, preserving every original target.
   target=field.replace('.','__');assert target not in measured[label];measured[label][target]=value
   bindings.append(dict(gate=label,baseline_field=field,baseline_expected=old,current_field='measured.'+label+'.'+target,current_expected=value,physical_domain='Unchanged accepted131 adjacent-TIB representation repair'if label=='source_preflight'else'Unchanged26 inherited physical legacy roots/two DEC-JNE ZF loops',reason='Every original physical proof input remains exact in current source6closure; historical repair/legacy scope is composed with separately proven current138 source. This is not wholewidget-extension invariance or newcapture evidence.'))
 assert histcounts=={'source_preflight':83,'source_legacy_flags':10}
 repair=read(R/'reports/m4-joint-startup131-source/preparation-r6/report.json','fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8');assert repair['nonTIB_memory_change']is False and repair['persistent_original_layout_restored']is True
 inverses=[]
 for old,new,key in [('mfc_source.py','mfc_source_layout.py','layout_changes'),('mfc_source_v3.py','mfc_source_v4.py','snapshot_changes'),('compare_provider_v5.py','compare_provider_v6.py','reader_changes')]:
  base=R/'tools/m4-joint-startup131';a=pin(base/old,closure['files'][str((base/old).resolve())]).read_text();b=pin(base/new,closure['files'][str((base/new).resolve())]).read_text();derived=a
  for change in repair[key]:assert derived.count(change['before'])==1;derived=derived.replace(change['before'],change['after'])
  assert derived==b;inverse=b
  for change in reversed(repair[key]):assert inverse.count(change['after'])==1;inverse=inverse.replace(change['after'],change['before'])
  assert inverse==a;inverses.append(dict(parent=old,current=new,changes=len(repair[key]),whole_forward_and_reverse_exact=True))
 # Pure proof witness validates retained TIB scope, without deriving a machine.
 purepath=R/'reports/m4-joint-startup131-source/preflight-r5/pure-TIB-layout-equivalence.json';pure=read(purepath,closure['files'][str(purepath.resolve())]);assert pure['synthetic_transport']and not pure['native_API_lifecycle_or_phase_claim'];assert repair['normalized_span']==[0x7ffde004,8]and repair['original_spans']==[[0x7ffde004,4],[0x7ffde008,4]]
 recommendations=read(frontier_path.parent/'predicate-recommendations.json',frontier['files'][str((frontier_path.parent/'predicate-recommendations.json').resolve())])
 extras=[r for r in recommendations if r['audit_status']in('explicit_same_domain_rename_candidate','physical_current_policy_identity_candidate')];assert len(extras)==6
 for row in extras:
  c=row['candidate'];label=row['gate'];field=row['baseline_field'];old=baseline['gates'][label]['equal'][field]
  if row['audit_status']=='explicit_same_domain_rename_candidate':d=read(R/c['path'],c['sha256']);value=at(d,c['field']);reason='Exact measured separately named same-domain field; retains fieldtype and distinct obligation.'
  else:
   d=frontier;value=at(d,c['field']);physical=pin(c['physical_source_path'],value);assert value==sha(physical);reason='Physically current named MFC helper/comparer identity, separate from policy/semantic approval.'
  assert type(value)is type(old)and value==c['expected'];assert not isinstance(old,bool)or value==old
  target=field.replace('.','__');measured.setdefault(label,{});assert target not in measured[label];measured[label][target]=value
  bindings.append(dict(gate=label,baseline_field=field,baseline_expected=old,current_field='measured.'+label+'.'+target,current_expected=value,physical_domain=row['physical_domain'],reason=reason,physical_source_candidate=c))
 assert len(bindings)==22 and len({(b['gate'],b['baseline_field'])for b in bindings})==22 and len({b['current_field']for b in bindings})==22
 # Baseline841 remains unchanged; bindings below are candidates, not allowances.
 assert sum(len(g['equal'])for g in baseline['gates'].values())==841
 q=out/'candidate-field-relations.json';q.write_text(json.dumps(bindings,indent=2)+'\n');pin(q);q=out/'inherited-exact-inverses.json';q.write_text(json.dumps(inverses,indent=2)+'\n');pin(q);pin(__file__)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Narrow22 measured field-composition candidates:16 unchanged inherited repair/legacy predicates,4 actual renamed schema fields,2 physical policy identities; no authoritative translation',measured=measured,baseline_predicates_retained=841,inherited_repair_fields=9,inherited_legacy_fields=7,renamed_same_domain_fields=4,physical_policy_identity_fields=2,historical_physical_file_counts=histcounts,current_source6_sha256=closure['source_provider_sha256'],current_source_preparation_sha256=sha(R/'reports/m4-joint-startup138-source/preparation-r11/report.json'),inherited_nonTIB_memory_change_scope='Only exact adjacent-TIB two-DWORD representation repair; no claim that widget extension leaves nonTIB memory unchanged',inherited_nonTIB_memory_change=False,whole_inherited_forward_inverse_files_checked=3,synthetic_TIB_transport_is_not_capture=True,current_138_complete_source_gate_remains_separate=True,authoritative_allowance_created=False,criteria_translation_reviewed=False,configuration_created=False,source_machine_executed=False,worker_executed=False,raw_export_reader_opened=False,capture_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
