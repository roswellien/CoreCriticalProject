"""Read-only output-consistency review, never a raw comparer or acceptance gate alone."""
from pathlib import Path
import copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
EXPECTED={
 'paired_phases':1656,'paired131_sequences':12,
 'typed_format_registrar_end_source_joins':72,
 'whole_nonstack_page_relations':221904,
 'separate_whole_loader_page_input_relations':3312,
 'whole45_nonstack_page_endpoint_relations':225216,
 'Lockit_paired_complete12B_normal_FS_relations':96,
 'Lockit_paired_bounded_API_semantic_relations':96,
 'Lockit_actual_owner_publication_activations':96,
 'Lockit_branch_field_source_derivations':216,
 'Lockit_whole_native_owned_carries':288,
 'whole_exact_loaded_input_endpoint_relations':3312,
 'paired_new_format_owners':48,'paired_new_format_cdecl_lifetimes':144,
 'paired_new_format_cdecl_boundary_relations':288,
 'paired_new_mixed_MFC_owners':36,'paired_new_mixed_source_owned_writes':120,
 'paired_new_mixed_publications':36,'paired_new_mixed_bounded_API_relations':24,
 'paired_new_mixed_FS_install_restore12B_relations':48,
 'paired_MFC_source_PC_occurrences':1704,'paired_MFC_ordered_operand_relations':1356,
 'paired_MFC_normal_boundary_relations':84,'paired_MFC_named_API_lifetimes':48,
 'paired_MFC_whole_borrowed_role_byteflows':60,
 'paired_MFC_whole_borrowed_endpoint_pairs':120,
 'paired_MFC_source_FS_install_restore_relations':24,
 'paired_MFC_whole_region_endpoint_relations':288,
 'paired_MFC_whole_module_input_relations':24}
IDENTITIES={
 'raw_export_source_report_sha256':'40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052',
 'native_source_report_sha256':'40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052',
 'native_execution_sha256':'2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6',
 'comparer_preparation_sha256':'a7047c9a755c1e989ef1a6b15fd0072c5e7b6a7e99d5efff64391937dab217bc',
 'original_combined_source_sha256':'7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4',
 'original_combined_review_sha256':'8b3056e286e82bad611875ee6c4ac04fc040a4a082fe8a4cf14e5980ee94bc6a',
 'original_new_MFC_source_sha256':'6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801',
 'loaded_input_relation_report_sha256':'379e86517363d5abf25830b3805bb41ff5fe8b104a9e2349131e045c4a5cacec'}
def need(v,label):
 if not v:raise ValueError(label)
def validate_summary(v):
 for k in ('passed','reader_closed','paired_initialization_data_contract','native_full_stack_source_proven'):need(v.get(k)is True,k)
 for k in ('capture_archive_opened','original_and_native_bytes_modified','blanket_page_mask','whole_game_liveness_proven','whole_M4_complete','loaded_input_native_DllMain_credit'):need(v.get(k)is False,k)
 need(v.get('archive_sessions_opened')==0 and v.get('initializers_added_by_this_report')==0,'No new credit or archives')
 for k,n in EXPECTED.items():need(v['counts'].get(k)==n,'Finite exact counter '+k)
 for k,h in IDENTITIES.items():need(v.get(k)==h,'Current physical identity '+k)
 need(v.get('original_record_bytes')==356992 and v.get('native_record_bytes')==159716,'Current measured record schemas')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(report_path,name):
 out=R/'reports/m4-startup138-paired'/name;need(not out.exists(),'Fresh reviewer namespace');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Ordinary review only');v=sha(p);need(h is None or h==v,'Exact physical dependency '+str(p));files[str(p)]=v;return p
 rp=pin(report_path);v=json.loads(rp.read_bytes());validate_summary(v)
 config_path=pin(v['configuration_path'],v['configuration_sha256']);config=json.loads(config_path.read_bytes());need(len(config)==16 and config['scope']=='current138-paired-frozen-gates','All15 frozen gates')
 for label,gate in config.items():
  if label=='scope':continue
  g=json.loads(pin(gate['path'],gate['sha256']).read_bytes());need(g['passed'],'Passed exact frozen gate '+label)
 need(v['comparer_preflight_sha256']==config['paired_preflight']['sha256'],'Exact independently admitted preflight')
 policy=json.loads(pin(config['paired_policy']['path'],config['paired_policy']['sha256']).read_bytes());need(policy['current138_complete_typed_domain_policy_reviewed']is True,'Independent policy seal retained');need(v['paired_policy_sha256']==config['paired_policy']['sha256'],'Exact policy gate')
 prep=json.loads(pin(config['comparer_preparation']['path'],config['comparer_preparation']['sha256']).read_bytes());decl=json.loads(pin(prep['policy_preparation'],prep['policy_preparation_sha256']).read_bytes());need((decl['selected_roots'],decl['callback_roots'],decl['total_source_pages'])==(138,108,69),'Current actual selected scope')
 # Hash ALL recorded ordinary dependencies, but never reopen capture transport/archive.
 skipped=[]
 for p,h in v['files'].items():
  path=Path(p)
  if path.suffix.lower()in('.mwb','.mwi','.zip')or path.name=='transport.json':skipped.append(p);continue
  pin(path,h if isinstance(h,str)else h['sha256'])
 def artifact(label):
  p=rp.parent/label;need(str(p.resolve())in v['files'],'Artifact physically sealed '+label);return json.loads(pin(p,v['files'][str(p.resolve())]).read_bytes())
 widgets=artifact('Widget-paired-source-relations.json');need(len(widgets)==84,'Seven roots x12 cases');cases={(l,s)for l in('O0','O2')for s in range(6)};roots={r['root']for r in widgets};need(len(roots)==7 and {(r['level'],r['sequence'],r['root'])for r in widgets}=={(l,s,r)for l,s in cases for r in roots},'Complete unique widget case/root matrix')
 for w in widgets:need(w['whole_endpoint_difference_authorization']is False and w['source_after_input_seed']is False,'Widget relations grant no generic endpoint or AFTER seed')
 terminal=[t for w in widgets for t in w['terminal_handle_field_source_writers']];need(len(terminal)==804 and sum(t['source_zero_clear']for t in terminal)==624,'Exact current source terminal fields and literal clears');need(sum(not t['source_zero_clear']for t in terminal)==180,'Exact retained positive font fields')
 for t in terminal:
  need(t['PC']in(0x5a0142,0x5a0753,0x5a0645)and t['address']==t['instance']+0x258 and t['width']==4,'Only exact source terminal full handle fields')
  if t['source_zero_clear']:need(t['PC']==0x5a0645 and t['original']==t['native']==0,'Literal source zero terminal value')
 formats=artifact('Formatting-paired-source-relations.json');need(len(formats)==48,'Four formatter roots x12 actual cases');need(len({(r['level'],r['sequence'],r['root'])for r in formats})==48,'Unique complete formatter matrix');typed=[r for f in formats for r in f['typed_registrar_end_source_joins']];need(len(typed)==72 and all(r['separate_whole_CRT_source_relation_required']is True and r['game_byte_difference_authorization']is False for r in typed),'Exact72 separately typed provider publications grant no game byte allowance')
 fonts=artifact('Font-paired-cleanup-relations.json');need(len(fonts)==180 and all(r['BOOL']==1 and r['source_callback_executed']is False for r in fonts),'180 same-instance typed manual cleanup joins, no callback execution')
 need(len(artifact('Lockit-provider-page-relations.json'))==9936,'All provider endpoint relations')
 loader=artifact('loader-page-input-relation.json');need(len(loader['observations'])==3312 and not loader['ordinary_page_mask']and not loader['ordinary_page_relation'],'Separate whole loader relation')
 # Counters/joins are output consistency. This does not repeat source machines or raw comparisons.
 pin(__file__);result=dict(passed=True,scope='Current138 output consistency and physical ordinary receipt dependencies only',pair_report_sha256=sha(rp),actual_selected_roots=138,actual_source_pages=69,actual_nonstack_pages=68,paired_cases=12,paired_phases=1656,whole_nonstack_endpoint_relations=225216,stale_frozen_captions=['selected131','all46','whole45_nonstack_page_endpoint_relations','paired131_sequences'],captions_change_neither_predicates_nor_current_counts=True,independent_raw_equivalence_reexecuted=False,full_original_provider_CPU_equivalence=False,source_callbacks_executed=False,accepted_function_credit=0,acceptance_record_update_performed=False,archives_opened=False,skipped_archive_identity_paths=skipped,files=files)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(out/'report.json'))
def preflight(name):
 out=R/'reports/m4-startup138-paired'/name;need(not out.exists(),'Fresh controls namespace');out.mkdir(parents=True)
 valid=dict(passed=True,reader_closed=True,paired_initialization_data_contract=True,native_full_stack_source_proven=True,capture_archive_opened=False,original_and_native_bytes_modified=False,blanket_page_mask=False,whole_game_liveness_proven=False,whole_M4_complete=False,loaded_input_native_DllMain_credit=False,archive_sessions_opened=0,initializers_added_by_this_report=0,counts=dict(EXPECTED),original_record_bytes=356992,native_record_bytes=159716,**IDENTITIES);validate_summary(valid);controls=[]
 for k in list(EXPECTED)+list(IDENTITIES)+['passed','reader_closed','initializers_added_by_this_report','original_record_bytes','blanket_page_mask']:
  bad=copy.deepcopy(valid)
  if k in EXPECTED:bad['counts'][k]+=1
  elif k in IDENTITIES:bad[k]='0'*64
  elif isinstance(bad[k],bool):bad[k]=not bad[k]
  else:bad[k]+=1
  try:validate_summary(bad)
  except ValueError:controls.append(k)
  else:raise ValueError('Adverse incorrectly admitted '+k)
 report=dict(passed=True,scope='Synthetic receipt-summary rejection controls only; no actual pair report/readers opened',adverses=controls,accepted_function_credit=0,files={str(Path(__file__).resolve()):sha(__file__)},pair_executed=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':
 if sys.argv[1]=='--preflight':preflight(sys.argv[2])
 else:main(sys.argv[1],sys.argv[2])
