"""Ordinary841 baseline field inventory and measured closed-gate proposals, not configuration."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
MAP={
'parent':'reports/m4-joint-startup131-root/acceptance-r1/report.json',
'native_preparation':'reports/m4-joint-startup138/preparation-r4/report.json',
'native_build':'reports/m4-joint-startup138/build-r5/build.json',
'native_prelaunch':'reports/m4-tree-review/joint138-prelaunch-r10/report.json',
'native_execution':'reports/m4-joint-startup138-root/execution-r3/report.json',
'original_preparation':'reports/m4-startup138-original/preparation-r8/report.json',
'original_build':'reports/m4-startup138-original/build-r5/build.json',
'original_prelaunch':'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json',
'original_execution':'reports/m4-startup138-original/original-execution-r2/report.json',
'original_validation':'reports/m4-startup138-original/original-validation-r3/report.json',
'original_source':'reports/m4-startup138-original/mfc-source-r2/report.json',
'original_source_review':'reports/m4-138-validation-review/independent-mfc-source-r2/report.json',
'original_old_source':'reports/m4-startup138-original/inherited-source-r5/report.json',
'original_old_source_review':'reports/m4-tree-review/original138-inherited-independent-r1/report.json',
'source_preparation':'reports/m4-joint-startup138-source/preparation-r11/report.json',
'source_provider':'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json',
'source_provider_review':'reports/m4-tree-review/source138-provider-independent-r1/report.json',
'source_new_mfc_review':'reports/m4-tree-review/source138-mfc-independent-r1/report.json',
'source_closure':'reports/m4-tree-review/source138-closure-r1/report.json',
'pair_preparation':'reports/m4-startup138-paired/comparer-preparation-r15/report.json',
'pair_policy_review':'reports/m4-startup138-paired/root-policy-admission-r8/report.json',
'paired':'reports/m4-startup138-paired/paired-r5/report.json',
'paired_review':'reports/m4-138-semantic-review/semantic-review-r2/report.json',
'loaded_input_relation':'reports/m4-tree-review/loaded-input138-r1/report.json',
'controls_preparation':'reports/m4-joint-startup138/controls-preparation-r4/report.json',
'controls_build':'reports/m4-joint-startup138/controls-build-r2/build.json',
'controls_prelaunch':'reports/m4-tree-review/joint138-controls-prelaunch-r4/report.json',
'controls_execution':'reports/m4-joint-startup138/context-controls-execution-r1/report.json',
'controls_equivalence':'reports/m4-138-controls-review/equivalence-r1/report.json'}
DOMAIN={
'parent':('Accepted131 inventory lineage','The next connected inventory retains accepted131 as its parent rather than accepted130; parent counts and physical receipt identities change to that sealed chain.'),
'native':('Physical138 current native worker and linked one-Session service','Seven physical widget slots extend the retained131 order; the current linked service/build5 and actual execution3 implement that138-root schedule.'),
'original':('Genuine original138 build5 observer/source3 carried chronology','Current genuine original138 uses the same138 physical slot order, six828-phase cases, current exact observer targets, APIinitial growth backing and separately sealed own BEFORE source proofs.'),
'source':('Literal138 source6 twelve-case69-page provider/widget execution','Current source6 reaches both levels and all six domains with69 own pages,108 callbacks and actual widget/GDI/FS/font/growth source joins; inherited rules retain exact physical current compilation lineage.'),
'pair':('Current138 comparer53-hunk preparation15 and actual paired5 finite output','All53 inverse hunks preserve accepted131 rules and add physical Game/provider module partition with exact72 registrar joins, terminal writer and treephase83. ROOTpolicy8 independently seals current finite domains. Paired5 executed all1656 current phases. Actual ROOT semantic-review2 independently rederives retained owner/API/FS/provider/tree/formatter and twelve MFC whole-row/raw-target relations under separately hashed root execution2; whole-machine observations remain attributed to paired5 and fullraw controls/acceptance remains separate.'),
'loaded':('Current own-original3/native3 MFC loaded bootstrap and complete input carry','The current independently authenticated bootstrap pages retain exact own inputs; current source6 widget operands and API carry are included in the same finite loaded-page relation.'),
'controls':('Current carried138 Context refusal/private retry and GDI resources','The current controls exercise actual post-creation refusal after135 carried roots and15owned fonts; current build/Context causes and retry scope change while acceptance still requires complete raw expansion and exact current link.')}
PENDING={
'source_preflight':'Current final consumer independent preflight binding must be supplied; do not select an older prepared consumer by caption.',
'source_legacy_flags':'Require explicit retained/current legacy flag gate binding and field-domain relation; unchanged inherited fields alone do not choose this gate.',
'pair_policy_review':'Await ROOT exact final preparation11 policy seal and corresponding closed physical review; earlier policy receipts are not interchangeable.',
'paired':'Fullpair4 terminal report pending; no expected values guessed from geometry or previous failed runs.',
'paired_review':'Independent exact current fullpair output/raw-policy review pending.',
'controls':'Current verifier exists but its giant controls receipt fields are not parsed here; fullraw closure/expanded durable inventory remains pending.',
'controls_review':'Bind exact complete independent current controls review after fullraw closure; readiness is not acceptance.'}
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def at(v,path):
 for k in path.split('.'):v=v[int(k)]if isinstance(v,list)else v[k]
 return v
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def read(p):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';pins[str(p)]=sha(p);return json.loads(p.read_bytes())
 baseline=read(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json');assert len(baseline['gates'])==33 and sum(len(g['equal'])for g in baseline['gates'].values())==841
 for path,h in [('reports/m4-startup138-paired/paired-r5/report.json','5d5a4e5082512617f972e383868004d3c1fbbc79fe1679d365431ab119d8a42e'),('reports/m4-startup138-paired/paired-root-output-review-r1/report.json','4cfcab5cc2b59f1564b462aafaa62138b87040215fb265987d3ea8d34bb8919c'),('reports/m4-startup138-paired/root-policy-admission-r8/report.json','42238616edc7beacd6ed0d3937b6221323dcc6775c174e4e94ee8925027ce297'),('reports/m4-startup138-paired/configuration-r8/report.json','93ec4b6291af7ebf6af3cb4c860becfc759bdb9ae5c8da80c7f2bf25d2ae76ec'),('reports/m4-startup138-paired/comparer-preparation-r15/report.json','a7047c9a755c1e989ef1a6b15fd0072c5e7b6a7e99d5efff64391937dab217bc'),('reports/m4-startup138-paired/comparer-self-preflight-r11/report.json','30809431c71226a3020f9c7426d88558aa1cfa44980849ca7623e2c45d10479b')]:
  r=read(R/path);assert r['passed']and pins[str((R/path).resolve())]==h

 for path,h in [('reports/m4-138-semantic-review/semantic-review-r2/report.json','dd3a095b343ad8e037a99603c1560989eddbbf94fdaf0454aa11074ce5b50db4'),('reports/m4-138-semantic-review/root-semantic-execution-r2/report.json','567944eef26f2d198ab61e80b662060fce85f651b963b044fdaee3416ff1aa66')]:
  r=read(R/path);assert r['passed']and pins[str((R/path).resolve())]==h
 rows=[];gates={};deltas={};counts={}
 for label,prior in baseline['gates'].items():
  current=read(R/MAP[label])if label in MAP else None
  if current is not None:assert current['passed']is True;gates[label]=dict(path=MAP[label],sha256=pins[str((R/MAP[label]).resolve())],binding_status='closed ordinary receipt candidate; independent role/criteria admission pending')
  else:gates[label]=dict(path=None,sha256=None,binding_status='unresolved',reason=PENDING[label])
  domain,reason=DOMAIN['parent'if label=='parent'else next(k for k in DOMAIN if label.startswith(k))]
  for field,old in prior['equal'].items():
   item=dict(gate=label,baseline_field=field,baseline_expected=old,current_field=None,current_expected=None,status='unresolved',physical_domain=domain,reason=reason)
   if current is None:item['unresolved_reason']=PENDING[label]
   else:
    try:value=at(current,field)
    except (KeyError,IndexError,TypeError,ValueError):item['unresolved_reason']='Baseline field absent from current receipt; reviewer must bind a distinct equivalent measured field, not passed.'
    else:
     if type(value)is not type(old):item['unresolved_reason']='Actual current field type differs; same-type finite target must be independently established.';item['observed_current_type']=type(value).__name__
     elif isinstance(old,bool)and value!=old:item['unresolved_reason']='Retained Boolean invariant changed; finite_delta cannot authorize this change.';item['observed_current_value']=value
     else:
      item.update(current_field=field,current_expected=value,status='identity_candidate'if old==value else'finite_delta_candidate')
      if old!=value:
       delta=dict(baseline_expected=old,current_field=field,current_expected=value,physical_domain=domain+' / '+field,reason=reason+' Exact changed measured predicate: '+field+'.');deltas.setdefault(label,{})[field]=delta;item.update(physical_domain=delta['physical_domain'],reason=delta['reason'])
   rows.append(item);counts[item['status']]=counts.get(item['status'],0)+1
 assert len(rows)==841 and len({(r['gate'],r['baseline_field'])for r in rows})==841
 assert len([r for r in rows if r['gate']=='paired_review'and r['status']=='unresolved'])==0
 assert counts['unresolved']==133
 for label in baseline['gates']:
  targets=[r['current_field']for r in rows if r['gate']==label and r['current_field']is not None];assert len(targets)==len(set(targets))
 for leaf,value in [('criterion-841-proposal.json',rows),('candidate-33-gate-bindings.json',gates),('finite-delta-proposal.json',deltas)]:
  p=out/leaf;p.write_text(json.dumps(value,indent=2)+'\n');pins[str(p.resolve())]=sha(p)
 for p in [Path(__file__),R/'tools/m4-138-controls-review/acceptance138_v3.py',R/'tools/m4-138-controls-review/acceptance138_criteria_v1.py',R/'tools/m4-138-controls-review/configure_acceptance138_v3.py',R/'reports/m4-138-controls-review/acceptance138-machinery-preparation-r4/required-bindings-template.json']:pins[str(p.resolve())]=sha(p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Reviewer-ready measured ordinary field inventory only; role/schema gaps explicit, no configuration or criteria allowances admitted',baseline_gates=33,baseline_predicates=841,candidate_closed_gate_paths=len(MAP),counts=counts,all841_typed_targets_resolved=False,criteria_translation_reviewed=False,required_current_gates=39,additional_six_gates_remain_separate=True,paired_output_consistency_receipt_is_not_fullraw_review=True,paired_review_binds_actual_ROOT_semantic_rederivation=True,ROOT_semantic_execution_sha256='567944eef26f2d198ab61e80b662060fce85f651b963b044fdaee3416ff1aa66',current_fullraw_controls_and_expansion_pending=True,configuration_created=False,fullraw_report_opened=False,archive_reader_opened=False,acceptance_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(sha256=sha(q),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
