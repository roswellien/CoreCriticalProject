"""Independent complete130 configuration/source/evidence review.

Reads bounded receipts and source only. Capture identities are merged without
opening their payloads; the actual acceptor must subsequently rehash all files.
"""
from pathlib import Path
import ast, collections, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
LABELS=set('parent native_preparation cleanup_review preparation build abi link resource build_review prelaunch original_preparation original_build original_run original_validation original_review old_owner_source current_original_source current_original_review source_provider_preflight source_provider_preparation_review native source_provider source_provider_review source_provider_closure pair_preparation pair_policy_review paired paired_review loaded_input_relation mixed_controls_build mixed_controls_execution mixed_controls mixed_controls_review controls_equivalence formatter_fixture_source formatter_fixture_witnesses formatter_fixture_review formatter_controls formatter_controls_review formatter_control_applicability cosine_runtime cosine_runtime_review'.split())
BOUNDED=set('whole_M4_complete native_game_launch_complete native_menu native_Training native_DllMain full_native_CRT_attach full_native_MFC_attach MSVCP_lazy_or_Sleep_path general_formatter general_trigonometric_equivalence whole_original_provider_stack_equality whole_original_TIB_equality whole_game_alias_liveness handler_execution exception_dispatch allocation_NULL_paths original_postRET_observed opaque_loaded_pointer_targets_proven'.split())
EXTENT=dict(selected_roots=130,new_roots=5,original_sequences=6,original_phases=780,native_sequences=12,native_phases=1560,callbacks_per_sequence=101,whole_source_pages=46,literal_objects_per_level=397,compiled_objects_per_level=30,capture_objects_per_level=2,linked_inputs_per_level=429,live_owners_per_sequence=92,MFC_owners_per_sequence=68,duplicate_owners_per_sequence=19,formatter_owners_per_sequence=4,source_State_bytes=3504,source_CPU_bytes=40,source_FX_bytes=512,source_ENV_bytes=28)
FIELDS=('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts')
EXPECTED={
 'parent':'856ba8bd458e178f4a9afd91ff24299becc4debef76ee17c359da0f741165d51',
 'native_preparation':'1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3',
 'preparation':'060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c',
 'build':'1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53',
 'native':'57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1',
 'original_validation':'91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca',
 'current_original_source':'2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624',
 'current_original_review':'8365b62801e51146ec68bfbe597971745919c8722f2e9c411325a775376af186',
 'source_provider':'1ac217828913db6c1efe91cb6a1b3c410b946bac883064856311e2845e7fdbfd',
 'source_provider_review':'0ce541ced0ea79b76c4eef4d935119e537f9401b71534047001f0736a2413a78',
 'source_provider_closure':'a831d215c1465ebf6af484416e8ccba600da73515a9c7ca9507ee869a0062e4c',
 'source_provider_preparation_review':'15ad63ce1738e13ae89e094d3302287225617b6c3067a0ec38a1aa1930b4f7e1',
 'loaded_input_relation':'66f3b663b5c66da5d40e217fb40b2686c2b2c402dd3f2640f977db9a6d1f7ba4',
 'paired':'ef497ae584b87c19d9896dbcbea37ccbb0a41e232b3e7f7fad58747d5ad98fe3',
 'paired_review':'9549c3e2a9a8abf86d421e618c8b6b1bbdbe69afc59efdfafadbde685e92fffe',
 'mixed_controls':'0d54d90ef2c01934d460d36a848c415b1753b4a2fc9cd7679e249c8844a140e3',
 'controls_equivalence':'ec3533c584a0fded0d838a666ddc0598d236f09a24af4ea9e730bc1bf6b898c7',
 'formatter_control_applicability':'ef8d2e1a9cad97b0104f545eee3cd599c3bb2b9f20646bd34841ac2664a53704',
}
PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:need(k not in d,'No duplicate JSON field');d[k]=v
 return d
def norm(p):return str(Path(p).resolve()).replace('\\','/').casefold()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.part'),'No capture payload reads');need(p.stat().st_size<=32*1024*1024,'Bounded configuration/source/receipt input');a=sha(p);need(h is None or h==a,'Actual exact configuration review input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable review source');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'),object_pairs_hook=unique)
def load(name,p):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def field(v,s):
 for p in s.split('.'):v=v[int(p)]if isinstance(v,list)else v[p]
 return v
def has(r,p,h):return any(norm(k)==norm(p)and v==h for f in FIELDS for k,v in r.get(f,{}).items())
def literal_assign(source,name):
 t=ast.parse(source);return next(ast.literal_eval(n.value)for n in t.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id==name for v in n.targets))
def main(configuration,name):
 out=ROOT/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh complete130 configuration review');out.mkdir(parents=True)
 counts=collections.Counter();union={};rows={};passed=False;error=None
 def absorb(r):
  for f in FIELDS:
   for p,h in r.get(f,{}).items():
    need(isinstance(h,str)and len(h)==64 and all(c in'0123456789abcdef'for c in h),'Exact declared physical SHA256');k=norm(p);need(k not in union or union[k]==h,'Conflict-free retained physical union');union[k]=h
 try:
  pin(__file__)
  config=read(configuration,'92185ae1025cc8df3afa4bfc45a0cdffd7a9d42790b1e8096632bd26e078561b')
  spec=read(config['review_specification'],'6b5297e8b6ec4994eeb7e724b9670a051a184fbc5d36416150468eb72f1eee64')
  need(set(config)=={'gates','extent','bounded_scope','configuration_source','configuration_source_sha256','requirements_source','requirements_source_sha256','review_specification','review_specification_sha256'},'Complete exact frozen configuration schema')
  need(len(LABELS)==42 and set(config['gates'])==set(spec)==LABELS,'Every independent required42 gate present exactly once')
  need(set(config['extent'])==set(EXTENT)and all(type(config['extent'][k])is type(v)and config['extent'][k]==v for k,v in EXTENT.items()),'Exact independently enumerated typed130 extent')
  need(set(config['bounded_scope'])==BOUNDED and all(type(v)is bool and v is False for v in config['bounded_scope'].values()),'Every explicit finite-project exclusion retained')
  accept_path=ROOT/'tools/m4-joint-startup130/acceptance.py';accept=pin(accept_path,'89af0dd9e986064d30761ab0d9f9127b0bb750dcecb57323ec246bbb2fa428a8').read_text()
  A=load('independent_acceptance130',accept_path)
  need(literal_assign(accept,'REQUIRED')==LABELS and literal_assign(accept,'BOUNDED')==BOUNDED and A.EXTENT==EXTENT,'Acceptor source agrees with independent scope inventory')
  for token in ("type(actual) is type(expected)","set(config['extent']) == set(EXTENT)","set(config['gates']) == REQUIRED","closure = verify_manifest(PINS)","closure['metadata_only_cache_used'] is False","review['gates_reviewed'] == len(REQUIRED)","has(review, configuration, sha(configuration))","has(review, __file__, sha(__file__))","len(parent_archives) == 253 and len(old_archives) == 166","len(inherited) == len(normalized_inherited) == 206","normalized_inherited == current_inherited","inventory_is_project_completion_percentage=False","connected_roots=130 if passed else 125","remaining_inventory_roots=14 if passed else 19"):
   need(token in accept,'Mandatory actual acceptor scope/schema/physical-rehash guard '+token)
  manifests=pin(ROOT/'tools/m4-pipeline/manifests.py').read_text();need("with Path(path).open('rb') as stream"in manifests and "hashlib.file_digest(stream, 'sha256')"in manifests and 'metadata_only_cache_used=False'in manifests,'Actual full union verifier physically streams all old/new inputs')
  freezer=pin(config['configuration_source'],config['configuration_source_sha256']).read_text()
  requirements=pin(config['requirements_source'],config['requirements_source_sha256']).read_text();RQ=load('reviewed_current130_requirements',config['requirements_source'])
  need(set(RQ.ROWS)==LABELS,'Every final gate has a literal measured requirement; no pending fallback')
  for token in ("set(item) == {'path', 'equal'}","receipt['passed'] is True","type(actual) is type(expected)","review_specification_sha256=sha(source)","requirements_source_sha256=sha(Path(__file__).with_name('requirements.py'))"):
   need(token in freezer,'Typed immutable specification freezer '+token)
  need('No overriding frozen measured requirements'in requirements and 'Every pending semantic gate supplied'in requirements,'Requirement supplement cannot replace existing gates')
  for label,item in config['gates'].items():
   need(set(item)=={'path','sha256','equal'}and len(item['equal'])>=2,'Exact substantial typed gate schema '+label)
   need(spec[label]==dict(path=item['path'],equal=item['equal']),'Frozen specification and configuration correspond exactly '+label)
   p=(ROOT/item['path']).resolve();need(p.is_relative_to(ROOT)and p.suffix=='.json','Named local workspace gate')
   row=read(p,item['sha256']);need(row['passed']is True,'Actual passed gate '+label)
   relative,equal=RQ.ROWS[label];need(item['path']=='reports/'+relative and item['equal']==equal,'Exact declared final source requirement '+label)
   for key,expected in item['equal'].items():actual=field(row,key);need(type(actual)is type(expected)and actual==expected,'Actual exact typed predicate '+label+':'+key);counts['typed_measured_predicates_reviewed']+=1
   if label in EXPECTED:need(item['sha256']==EXPECTED[label],'Exact independently reviewed current/historical gate '+label)
   rows[label]=row;absorb(row);A.absorb(row)
   sibling=p.parent/'pins.json'
   if sibling.exists():
    manifest=read(sibling);need(set(manifest)=={'files'},'Exact sibling dependency manifest');absorb(manifest);A.absorb(manifest);counts['sibling_manifests_reviewed']+=1
   counts['passed_gate_receipts_reviewed']+=1
  need(counts['typed_measured_predicates_reviewed']==574,'All actual574 frozen predicates reviewed')
  # Exercise the exact final acceptor evidence edges and complete semantic
  # checker without calling its full payload hash stage or main procedure.
  A.semantic_checks(rows,config['gates']);counts['actual_acceptor_semantic_preflight']=1
  for p,h in A.PINS.items():
   k=norm(p);need(k not in union or union[k]==h,'Actual checker-declared physical union agrees');union[k]=h
  edges=[(l,'build')for l in('abi','link','resource','prelaunch')]+[(l,'native')for l in('source_provider','paired')]+[(l,'original_validation')for l in('original_review','old_owner_source','current_original_source')]
  edges += [('cleanup_review','native_preparation'),('build_review','abi'),('build_review','link'),('build_review','resource'),('current_original_review','current_original_source'),('source_provider_preparation_review','source_provider'),('source_provider_review','source_provider'),('source_provider_closure','source_provider'),('loaded_input_relation','source_provider'),('loaded_input_relation','native'),('paired_review','paired'),('paired','loaded_input_relation'),('paired','source_provider'),('paired','current_original_source'),('paired','current_original_review'),('mixed_controls','mixed_controls_execution'),('mixed_controls_review','mixed_controls'),('controls_equivalence','mixed_controls_build'),('controls_equivalence','build'),('formatter_fixture_review','formatter_fixture_source'),('formatter_controls_review','formatter_controls'),('formatter_control_applicability','formatter_controls'),('formatter_control_applicability','native_preparation'),('cosine_runtime_review','cosine_runtime')]
  for left,right in edges:
   item=config['gates'][right];need(has(rows[left],ROOT/item['path'],item['sha256']),'Independent exact physical evidence edge '+left+' -> '+right);counts['exact_physical_evidence_edges']+=1
  for left,right,key in [('preparation','parent','parent_acceptance_sha256'),('preparation','native_preparation','native_preparation_sha256'),('build','preparation','preparation_sha256'),('native','build','build_sha256'),('original_build','original_preparation','preparation_sha256'),('original_run','original_build','build_sha256'),('original_validation','original_build','build_sha256'),('mixed_controls_execution','mixed_controls_build','build_sha256'),('loaded_input_relation','original_validation','original_validation_sha256'),('loaded_input_relation','native','native_execution_sha256'),('loaded_input_relation','source_provider','native_source_sha256'),('paired','native','native_execution_sha256'),('paired','source_provider','native_source_report_sha256'),('paired','current_original_source','original_combined_source_sha256'),('paired','current_original_review','original_combined_review_sha256')]:
   need(rows[left][key]==config['gates'][right]['sha256'],'Independently reviewed actual current lineage '+left+' -> '+right);counts['actual_execution_lineage_edges']+=1
  need(rows['parent']['connected_roots']==125 and rows['parent']['remaining_inventory_roots']==19 and rows['parent']['native_game_launch_complete']is False,'Current accepted125 is startup inventory only')
  order=rows['preparation']['selected_order'];new={0x4df610,0x4e0710,0x4e0810,0x4e1ca0,0x4b64f0}
  need(len(order)==130 and len({r['entry']for r in order})==len({r['slot']for r in order})==130 and set(rows['preparation']['new_roots'])==new,'Exact five new distinct roots')
  need(next(i for i,r in enumerate(order)if r['entry']==0x4b64f0)==76 and next(i for i,r in enumerate(order)if r['entry']==0x4b7f70)==78,'Current physical compound/tree phase positions')
  parent_p=rows['parent']['gates']['preparation'];old=read(ROOT/parent_p['path'],parent_p['sha256']);need([r for r in order if r['entry']not in new]==old['selected_order'],'All accepted125 table entries and slots retain complete relative order')
  parent_archives={norm(p):h for p,h in rows['parent']['files'].items()if Path(p).suffix.lower()=='.mwb'}
  old_archives={norm(p):h for p,h in old['inherited_capture_payload_hashes_reused'].items()}
  need(len(parent_archives)==253 and len(old_archives)==166,'Actual accepted-parent complete union and older preparation subset have distinct exact domains')
  need(all(union.get(p)==h for p,h in parent_archives.items()),'Every accepted-parent archive remains independently retained in current full physical union');counts['retained_complete_parent_archive_identities']=253
  inherited_maps=[]
  for label in('preparation','build','native'):
   r=rows[label];need(r['full_dependency_acceptance_rehash_required']is True,'All current stages require final full rehash');raw=r['inherited_capture_payload_hashes_reused'];retained={norm(p):h for p,h in raw.items()};need(len(raw)==len(retained)==206 and all(union.get(p)==h for p,h in retained.items()),'Every actual206 composer-reused archive identity retained in final union');need(all(retained.get(p)==h for p,h in old_archives.items()),'Every older166 preparation identity retained within current206 map');inherited_maps.append(retained);counts['retained_current_inherited_archive_identity_joins']+=206;counts['retained_older_preparation_archive_identity_joins']+=166
  need(inherited_maps[0]==inherited_maps[1]==inherited_maps[2],'Whole exact206 reused map propagates unchanged through preparation/build/execution')
  for level in rows['controls_equivalence']['levels']:
   need(level['only_permitted_difference']==[4,8]and level['all_non_timestamp_bytes_equal']is True and level['code_data_relocation_symbol_bytes_equal']is True and all(4<=i<8 for i in level['actual_differing_offsets']),'Only four COFF timestamp bytes are permitted differences')
   need(level['actual_compiler_dependencies']==485 and level['linked_common_literals']==396 and level['linked_final_literals']==397,'Every actual library dependency/header and final literal compiled interface accounted');counts['current_controls_library_equivalence_levels']+=1
  historical=rows['formatter_control_applicability'];need(historical['whole_historical_actual_faults_rerun_in_current_library']is False and historical['old_predicates_preserved_in_finite_domain']is True and historical['changed_shared_cleanup_observed_in_current_controls']is True,'Historical26 faults retain historical scope; current18 faults/20 retries cover changed cleanup')
  need(rows['controls_equivalence']['full130_fault_history_claimed']is False and rows['mixed_controls']['full_caller_FX512_equality_claim']is False,'Control proof scope is precise current library and architectural host numeric fields')
  loaded=rows['loaded_input_relation'];need(loaded['prior125_difference_list_reused']is False and loaded['whole_page_mask']is False and loaded['opaque_pointer_target_equivalence']is False,'Current complete finite loader delta/access audit, no target equivalence or wildcard')
  need(rows['source_provider']['candidate_AFTER_machine_seed']is False and rows['source_provider']['per_phase_BEFORE_machine_seed']is False and rows['source_provider']['native_CS40_opaque_copy']is False,'Single genuine bootstrap and complete persistent source reconstruction')
  need(rows['source_provider_review']['independent_trigonometric_prediction']is False and rows['cosine_runtime']['independent_trigonometric_prediction']is False,'Finite measured numerical oracle is not independent generic cosine prediction')
  need(rows['paired']['original_provider_scratch_stack_crossbranch_equal']is False and rows['paired']['native_full_stack_source_proven']is True and rows['paired']['Lockit_original_postRET_observed']is False,'Full native stack source equality and bounded original observation timing are distinct')
  counts['declared_conflict_free_union_identities']=len(union);counts['current_original_source_reader_sessions']=1
  passed=True
 except BaseException as exc:error=repr(exc);(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  artifact=out/'reviewed-gates-and-dependency-identities.json';artifact.write_text(json.dumps(dict(gates=locals().get('config',{}).get('gates',{}),declared_dependency_identities=union),indent=2)+'\n');pin(artifact)
  report=dict(passed=passed,scope='Independent complete frozen42-gate selected130 source/schema/current evidence/typed count review; final physical union rehash remains mandatory and is not performed here',gates_reviewed=counts['passed_gate_receipts_reviewed'],predicates_reviewed=counts['typed_measured_predicates_reviewed'],configuration_sha256=sha(configuration),acceptance_source_sha256=sha(ROOT/'tools/m4-joint-startup130/acceptance.py'),counts=dict(counts),error=error,capture_archives_opened=0,full_dependency_union_rehashed=False,inventory_is_project_completion_percentage=False,whole_M4_complete=False,native_game_launch_complete=False,historical_formatter_faults_rerun_claim=False,files=PINS)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),gates_reviewed=report['gates_reviewed'],predicates_reviewed=report['predicates_reviewed'],counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
