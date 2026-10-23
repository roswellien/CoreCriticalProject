"""Bounded named policy measurements, not criterion allowances or acceptance."""
from pathlib import Path
import ast,collections,hashlib,importlib.util,json,re,sys,textwrap,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def whole_inverse(source,hunks):
 for h in reversed(hunks):
  for pos in h['positions']:
   assert source[pos:pos+len(h['new'])]==h['new'];source=source[:pos]+h['old']+source[pos+len(h['new']):]
 return source
def source_vector(rows):
 assert len(rows)==14 and len({x['entry']for x in rows})==14 and rows[13]==dict(entry=0x5ae3e4,slot=0x5e0040)
 return rows
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={};passed=False;counts=collections.Counter();witnesses=[];candidates=[];pending=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';assert p.stat().st_size<32*1024*1024,'Bounded ordinary only';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  config=read(R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json','ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7')
  proposal=read(R/'reports/m4-138-controls-review/criterion-delta-proposal-r4/criterion-841-proposal.json')
  bindings=read(R/'reports/m4-138-controls-review/criterion-delta-proposal-r4/candidate-33-gate-bindings.json')
  def gate(n):v=bindings[n];return read(R/v['path'],v['sha256'])
  pp=gate('pair_preparation');root=gate('pair_policy_review');assert pp['passed']is True and root['passed']is True
  assert root['comparer_preparation_sha256']==bindings['pair_preparation']['sha256'] and root['current138_complete_typed_domain_policy_reviewed']is True
  hp=pin(R/'tools/m4-startup131-paired/mfc_relations_v2.py','4ab2c11a89b47d8f380d348dab8a548d3a71c529ecafc25282d362064c0dc67b');assert pp['files'][str(hp)]==root['files'][str(hp)]==pins[str(hp)]
  cp=pin(pp['comparer'],pp['comparer_sha256']);ast.parse(cp.read_text());hunks=read(cp.parent/'hunks.json',pp['files'][str(cp.parent/'hunks.json')]);assert len(hunks)==53
  parent=pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43')
  assert whole_inverse(cp.read_text(),hunks)==parent.read_text()
  policy=read(pp['policy_preparation'],pp['policy_preparation_sha256']);assert root['policy_sha256']==pp['policy_preparation_sha256'] and policy['selected_roots']==138
  pre=read(R/'reports/m4-startup138-paired/root-definition-preflight-r8/report.json',root['files'][str(R/'reports/m4-startup138-paired/root-definition-preflight-r8/report.json')])
  assert pre['passed']is True and pre['all53_hunks_exactly_invert']is True and pre['generated_main_not_invoked']is True and pre['archive_reader_opened']is False and pre['raw_export_reader_opened']is False
  for label,path,h,field,value in [('terminal','widget-terminal-writer-root-review-r2','0fadb2a271833f91851ca28b6b430748db99ad0d113b7c878c63fe800d7812cb','terminal_fields',804),('tree','tree-phase-root-review-r1','51e4aef13a576afdf694f37d19657059fb6ea14b29363580418ba5981a6ebddb','tree_phase',83),('formatter','format-module-root-review-r3','97fceac99e6d05cd2263fefa482d5205a93b711f2471352903dbcf611ec933f7','separate_CRT_publications',72)]:
   q=R/f'reports/m4-startup138-paired/{path}/report.json';r=read(q,h);assert root['files'][str(q)]==h and r['passed']is True and r['independent_review']is True and type(r[field])is int and r[field]==value
  # Authenticate reuse of the actual ROOT8 whole physical seal, without
  # re-opening/re-hashing its7.34GB preparation-input closure here.
  seal=pin(R/'tools/m4-startup138-paired/root_seal_current_policy_v3.py','d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f').read_text()
  wrapper=pin(R/'tools/m4-startup138-paired/root_seal_current_policy_v12.py',root['files'][str(R/'tools/m4-startup138-paired/root_seal_current_policy_v12.py')]).read_text()
  for marker in ("for q,v in g.get('files',{}).items():pin(q,v)","v=sha(p);assert h is None or v==h","for q,h in pins.items():assert sha(q)==h","m.main('root-definition-preflight-r2')"):
   assert marker in seal
  assert "('root-policy-admission-r2','root-policy-admission-r8')"in wrapper and "('root-definition-preflight-r2','root-definition-preflight-r8')"in wrapper
  root8edges=[]
  for p,h in pp['files'].items():assert root['files'].get(p)==h;root8edges.append(dict(path=p,sha256=h))
  assert len(root8edges)==3838
  q=out/'root8-preparation-scope-edges.json';q.write_text(json.dumps(root8edges,indent=2)+'\n');pin(q)
  # Exactly the accepted original MFC predicates, using current sealed rows.
  original_gate=read(R/'reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801')
  dp=R/'reports/m4-startup138-original/mfc-source-r2/source-derivations.json';original=read(dp,original_gate['files'][str(dp)])
  spec=importlib.util.spec_from_file_location('policy_field_mfc',hp);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
  assert M.ROOT==0x5ae3e4 and M.PHASE==13 and M.ROLES==('manager-array','thread','thread-array','thread-object','global-object')
  baseline=pin(R/'tools/m4-tree-review/review_paired131_preparation_v2.py').read_text();start=baseline.index('  for row in original:');end=baseline.index('  for marker in ',start);block=textwrap.dedent(baseline[start:end]);ast.parse(block)
  assert original_gate['passed']is True and len(original)==6
  env=dict(original=original,M=M,need=lambda v,msg: (_ for _ in()).throw(AssertionError(msg))if not v else None,counts=counts,static=witnesses)
  exec(compile(block,'retained accepted131 exact original-MFC policy predicates','exec'),env)
  expected={k[7:]:v for k,v in config['gates']['pair_policy_review']['equal'].items()if k.startswith('counts.')and k!='counts.physically_verified_preparation_files'}
  assert dict(counts)==expected
  q=out/'current-original-MFC-full-predicate-witnesses.json';q.write_text(json.dumps(witnesses,indent=2)+'\n');pin(q)
  helper=hp.read_text()
  for marker in ('Every other opaque differing input byte is never source-read','Every untouched opaque difference carries exactly in each branch','Every other differing opaque provider input byte is unconsumed','original_API_held_CS24_observed=False','native_intermediate_hardware_observation=False','Only source TIB004/008 may join','Each complete independent carried BEFORE part','Exact inverse persistent projection of the independently derived endpoint'):assert marker in helper
  measurements=dict(pair_preparation=dict(helper_sha256=pins[str(hp)],capture_reader_opened=pp['archive_reader_opened'],paired_executed=pp['source_machine_executed']),pair_policy_review=dict(counts=dict(counts),previous_ROOT8_physically_verified_preparation_files=len(root8edges)),controls_preparation={},controls_execution={},controls_equivalence={})
  # Same scoped observation limits as the unchanged accepted MFC helper;
  # these do not claim execution/observation properties of the later paired5.
  measurements['pair_policy_MFC_scope']=dict(original_API_held_CS24_observed=False,native_intermediate_hardware_observation=False,cold_or_arbitrary_alias_domain_credited=False)
  # Static current positive/control schedule proof, separate from raw retry.
  positive=read(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a');controls=gate('controls_preparation');execution=gate('controls_execution');link=read(R/'reports/m4-138-controls-review/current-link-join-r1/report.json')
  assert link['passed']is True and link['whole_Context_inverse_restores_positive']is True and link['controls_execution_sha256']==bindings['controls_execution']['sha256'] and link['shared_source_protocol_whole_bytes_identical']is True
  for leaf in ('joint_protocol.hpp','connected_inputs.hpp'):
   p=Path(positive['generated_sources'] and R/'reports/m4-joint-startup138/preparation-r4')/leaf;q=Path(bindings['controls_preparation']['path']).parent; q=R/q/leaf
   assert pin(p,positive['files'][str(p)]).read_bytes()==pin(q,controls['files'][str(q)]).read_bytes()
  for level in ('O0','O2'):
   p=R/'reports/m4-joint-startup138/preparation-r4'/level/'mfc_build_bindings.hpp';q=R/Path(bindings['controls_preparation']['path']).parent/level/'mfc_build_bindings.hpp'
   assert pin(p,positive['files'][str(p)]).read_bytes()==pin(q,controls['files'][str(q)]).read_bytes()
  source_vector(positive['selected_order'][:14]);assert controls['selected_order']==positive['selected_order']
  old_controls=read(R/config['gates']['controls_preparation']['path'],config['gates']['controls_preparation']['sha256']);assert old_controls['selected_order']==positive['selected_order'][:14]
  measurements['controls_equivalence'].update(identical_prefix_roots=14,exact_new_phase=13)
  measurements['controls_preparation']['declared_post_resource_modes']=controls['control_modes'];assert controls['control_modes']==8 and controls['control_phase']==135
  assert execution['ordinary_outputs_only']is True and execution['archive_reader_opened']is False and execution['all_workers_terminal']is True and len(execution['runs'])==16
  # Do not invent closure from the incomplete fullraw review. This controller
  # itself opens no bounded/canonical reader; a separate static call audit is
  # needed to add all_bounded_readers_closed to its producer scope.
  target={'pair_preparation','pair_policy_review','controls_preparation','controls_execution','controls_equivalence'}
  for row in proposal:
   if row['gate']not in target or row['status']!='unresolved':continue
   x=dict(row);x['candidate']=None;g=row['gate'];field=row['baseline_field'];value=None;status='pending_exact_scope_proof'
   if g=='pair_preparation':value=measurements[g][field];status='measured_bounded_preparation_field'
   elif g=='pair_policy_review' and field.startswith('counts.'):
    value=(len(root8edges)if field=='counts.physically_verified_preparation_files'else counts[field[7:]]);status=('reuse_actual_ROOT8_complete_named_preparation_domain'if field.endswith('physically_verified_preparation_files')else'measured_retained_original_MFC_predicate')
   elif g=='pair_policy_review' and field in measurements['pair_policy_MFC_scope']:value=measurements['pair_policy_MFC_scope'][field];status='unchanged_finite_MFC_observation_scope_only'
   elif g=='controls_equivalence':value=measurements[g][field[7:]];status='measured_original14_static_selection_scope_no_raw_claim'
   if status!='pending_exact_scope_proof':
    assert type(value)is type(row['baseline_expected']);x['candidate']=dict(value=value,measured_scope=status);candidates.append(x)
   else:pending.append(x)
  q=out/'candidate-field-relations.json';q.write_text(json.dumps(candidates+pending,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Bounded distinct policy/preparation/original-MFC/static14 source domain measurements and prior actual ROOT8 full pin reuse; no allowance/configuration/acceptance',measurements=measurements if'measurements'in locals()else{},candidate_fields=len(candidates),pending_fields=len(pending),fresh_ROOT8_3838_input_rehash=False,fresh_full_union_still_mandatory=True,full_raw_controls_terminal_claim=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,worker_executed=False,configuration_created=False,allowance_created=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
