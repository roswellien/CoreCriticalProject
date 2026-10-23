"""Exact45 typed work-ahead recipe; no giant report read or config/allowance."""
from pathlib import Path
import ast,collections,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def read(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip');raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return json.loads(raw)
 parent_path=R/'reports/m4-138-controls-review/root-criterion-delta-proposal-r6/report.json';parent=read(parent_path,'626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505')
 frontier_path=parent_path.parent/'remaining-45-field-frontier.json';frontier=read(frontier_path,parent['files'][str(frontier_path)]);assert len(frontier)==45
 support_path=R/'reports/m4-138-criteria-frontier/strict24-named-facet-mapping-r4/report.json';support=read(support_path,'1028927da7779907245248406caa3ec8cb664fd3910d959ad8815b799cf1ef40')
 union_path=R/'reports/m4-138-preresource-strict-review/root-aggregate-admission-r1/report.json';union=read(union_path,'4e1f23cf8be6ff2db1362a71f5141c51cf2bd51bf702fe8d911e61cc7f036f4c')
 assert union['passed']is True and union['case_count']==24 and union['whole_dependency_count']==1167180 and union['aggregate_executed']is False
 union_file=union_path.parent/'whole-ordinary-union.json';assert union['files'][str(union_file)]=='f23f11811167b0ad125bafd6bd5ea93d492dbb0d9f6084ec9978a14ba24a01ff'
 manifest=union_path.parent/'aggregate-manifest.json';assert union['files'][str(manifest)]=='6e7bf035598fad79a4b6b67eb030ffc9825158c85856255975d5dd47a083da16'
 # Giant union and manifests are references only: ROOT already authenticated
 # all1,167,180 physical dependencies; eventual fresh acceptance expands them.
 named_path=R/'reports/m4-138-preresource-strict-review/root-named-CS24-TLS64-r1/report.json';named=read(named_path,'88bb674315463694c75fcd21c62a0f3bf5151a2ba5a55149994e1489074f5265')
 assert named['passed']is True and named['all_bounded_readers_closed']is True and named['counts']==dict(whole_borrowed_guestCS24_prefixes=12,source_TLS_refusal_frame64=2)
 assert named['whole_raw_inventory_rehashed']is False and named['source_seed_from_AFTER']is False and named['worker_executed']is False and named['initializer_credit']==0
 batch_path=R/'reports/m4-138-preresource-strict-review/root-strict-remaining23-r1/report.json';assert named['files'][str(batch_path)]=='2cf7c24beaa1bf64ce79861c1b08c2ade3e3498acbde8c697f819119341ec654'
 mapping=[]
 for row in frontier:
  gate=row['gate'];f=row['baseline_field'];value=None;source=None;requires=[];domain=''
  if gate=='controls_preparation':
   domain='legacy12 input contract plus separately retained current8 input and scoped observation limits'
   value=12 if f=='control_cases'else False;source='actual strict24 distinct modes'if f=='control_cases'else'all24 explicit scope limits + separately required current8 scope review'
   requires=['current8_preparation_composite_source_review','terminal_legacy24_aggregate','current8_closed_inputs_and_scope']
  elif gate=='controls_prelaunch':
   domain='legacy12 physical prefix/compiler/source domain; current8 physical build retained separately'
   if f=='counts.whole_linked_control_functions':value=7;source='ROOT exact deduplicated whole7 ledger; O0four/O2three, NOT15joins'
   elif f=='counts.actual_compiler_TLS_cells':value=56;source='ROOT current legacy prefix compiler occurrences, NOTcurrent8 64 or runtime frame64'
   elif f=='counts.whole_authored_public_faults':value=12;source='actual strict24 distinct legacy modes, not current8 faults'
   requires=['complete_legacy_prefix_compiled_source_review','terminal_legacy24_aggregate','current8_physical_root_review']
  elif gate in('controls','controls_review')and f.startswith('counts.'):
   field=f.split('.',1)[1];domain='exact legacy24 original-MFC semantic counter domain plus mandatory current16 whole controls closure'
   if field in named['counts']:value=named['counts'][field];source='named_source_supplement.counts.'+field
   elif field in union['counts']:value=union['counts'][field];source='ROOT whole24 admission measured counts.'+field+'; actual terminal aggregate still required'
   elif field=='whole_export_targets_authenticated':
    domain='distinct full sealed raw union current16 plus legacy24 (never physical-dependency count alone)'
    source='future actual independently measured raw path union, each payload authenticated';requires.append('current16_terminal_fullraw_and_legacy24_raw_inventory_join')
   else:raise AssertionError((gate,f))
   requires+=['terminal_legacy24_aggregate','closed_legacy24_physical_union','current16_terminal_fullraw','current16_independent_semantic_resource_source_equivalence']
   if gate=='controls_review':requires.append('whole_named_composite_independent_raw_review')
  elif f in('whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):
   domain='explicit scoped observation exclusions';value=False;source='all24 explicit limitations plus mandatory current8 source/serializer observation-limit review';requires=['current8_closed_inputs_and_scope','terminal_legacy24_aggregate']
  elif f in('initializer_credit','capture_archives_opened'):
   domain='actual composite reviewer/source/controller scope';value=0;source='future measured reviewer/controller properties, never inferred from fullraw progress';requires=['whole_named_composite_independent_raw_review']
  elif f in('execution_sha256','controls_verification_sha256'):
   domain='exact current immutable producing/composite lineage'
   source='closed current8 execution gate SHA + separately pinned legacy24 lineage'if f=='execution_sha256'else'exact controls composite physical SHA'
   requires=['terminal_legacy24_aggregate','current16_terminal_fullraw','measured_complete_composite_lineage']
  elif f in('passed','raw_exports_all_logical_entries','raw_export_readers_closed','all_bounded_readers_closed'):
   domain='complete named old+new current controls semantic/raw/lifetime/inventory/reader closure'
   source='future exhaustive actual joined predicate; no passed-only/default true'
   requires=['terminal_legacy24_aggregate','current16_terminal_fullraw','whole_named_composite_independent_raw_review','measured_complete_composite_lineage']
  else:raise AssertionError((gate,f))
  if value is not None:
   assert type(value)is type(row['baseline_expected'])
   if isinstance(value,bool):assert value is row['baseline_expected']
  mapping.append(dict(gate=gate,baseline_field=f,baseline_expected=row['baseline_expected'],baseline_type=type(row['baseline_expected']).__name__,composite_field=f,measured_support_value=value,support_source=source,physical_domain=domain,mandatory_receipt_roles=sorted(set(requires)),binding_status='pending_actual_composite_measurement',current_expected=None,current_report_path=None,current_report_sha256=None,no_allowance=True))
 assert len(mapping)==45 and collections.Counter(x['gate']for x in mapping)==dict(controls_preparation=3,controls_prelaunch=7,controls=18,controls_review=17)
 semantic_path=R/'tools/m4-138-controls-review/acceptance138_semantics_v3.py';s=semantic_path.read_text();pins[str(semantic_path)]=hashlib.sha256(semantic_path.read_bytes()).hexdigest()
 old="    typed_equal(rows['controls_build']['preparation_sha256'],gates['controls_preparation']['sha256'],'Current connected control preparation')"
 new="""    if rows['controls_preparation'].get('scope_identity')=='current138_controls_preparation_composite_v1':
        underlying=rows['controls_preparation']['underlying_current8_preparation']
        typed_equal(underlying['sha256'],'f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e','Exact immutable current8 source preparation')
        need(has(rows['controls_preparation'],ROOT/underlying['path'],underlying['sha256']),'Scoped physical current8 preparation edge')
        typed_equal(rows['controls_build']['preparation_sha256'],underlying['sha256'],'Actual current8 build consumes immutable preparation')
        legacy=rows['controls_preparation']['underlying_legacy12_preparation']
        typed_equal(legacy['sha256'],'8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c','Exact separate actual legacy12 prefix preparation')
        need(has(rows['controls_preparation'],ROOT/legacy['path'],legacy['sha256']),'Scoped physical legacy12 preparation edge')
    else:
        typed_equal(rows['controls_build']['preparation_sha256'],gates['controls_preparation']['sha256'],'Current connected control preparation')"""
 assert s.count(old)==1;t=s.replace(old,new);assert t.count(new)==1 and t.replace(new,old)==s;ast.parse(t)
 p=out/'acceptance138_semantics_composite_candidate_v1.py';p.write_text(t);pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 for leaf,value in [('pending45-terminal-field-mapping.json',mapping),('necessary-semantic-source-inverse.json',[dict(before=old,after=new)])]:
  p=out/leaf;p.write_text(json.dumps(value,indent=2)+'\n');pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 recipe=dict(scope='Finite mapping/source-code recipe only; no config, Root allowance or acceptance',rows=45,all841_baseline_types_and_values_must_remain_unchanged=True,all_other796_proposal_rows_must_remain_byte_equal=True,no_boolean_flips=True,no_type_coercion=True,no_success_field_collapsing=True,distinct45_current_targets_required=True,authoritative_relation_kind='identity only SAME path AND SAME typed value; otherwise exact substantive separately ROOT-reviewed finite delta even for equal-value aliases',known_closed_receipts=dict(named_supplement=dict(path=str(named_path),sha256=pins[str(named_path)],counts=named['counts']),legacy24_whole_union=dict(path=str(union_path),sha256=pins[str(union_path)],physical_dependencies=1167180,union_path=str(union_file),union_sha256='f23f11811167b0ad125bafd6bd5ea93d492dbb0d9f6084ec9978a14ba24a01ff',manifest_path=str(manifest),manifest_sha256='6e7bf035598fad79a4b6b67eb030ffc9825158c85856255975d5dd47a083da16')),pending_mandatory_CLI_receipts=['actual terminal legacy24 aggregate path+SHA','actual terminal current16 fullraw path+SHA/closed durable DB/inventory whole byte proof','current16 independent whole semantic/source/GDI-owner/retry/equivalence receipt joins','complete legacy24+current16 distinct raw inventory union measured coverage','separately reviewed composite preparation/source/current8 observation-limit report','separately reviewed composite prelaunch complete old7/current8 source+link report','actual controls composite report and complete independent scoped controls_review report'],lineage_requirements=['Current8 controls execution/build/current8 prep f413 unchanged and scoped','Separate legacy12 prefix prep8a322/build9a656 and actual24 executable lineage retained','Controls review physically binds exact new controls composite SHA, not only current8 verifier88e0 or terminal raw report','All reported source/module/tool/compiler/runtime/header/ordinary/canonical-parent proofs stay in fresh physical acceptance union','Expand complete legacy1,167,180 union and fullraw every-row measured content SHA/size; keep semantic and raw logical counts distinct; no giant dictionary/metadata-only count substitution'],semantics_candidate_executed=False,ROOT_allowance_created=False,configuration_created=False,acceptance_executed=False)
 p=out/'ROOT-terminal-composition-recipe.json';p.write_text(json.dumps(recipe,indent=2)+'\n');pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in(Path(__file__).resolve(),Path(sys.executable).resolve()):pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 report=dict(passed=True,scope='Exact pending45 typed recipe plus source-only necessary composite lineage derivative; no terminal aggregate/fullraw read/run',pending_fields=45,named_CS24_TLS64_facet_closed=True,legacy24_union_ROOT_closed=True,legacy24_aggregate_still_required=True,current16_terminal_fullraw_still_required=True,large_union_files_opened=False,semantic_checker_executed=False,worker_executed=False,archive_reader_opened=False,configuration_created=False,allowance_created=False,accepted_function_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
