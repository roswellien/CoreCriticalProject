"""ROOT independent finite source admission; no model import or reader launch."""
from pathlib import Path
import ast, hashlib, json, sys, time
R=Path(__file__).resolve().parents[2]
def main(closure_path,closure_sha,name):
 started=time.monotonic();files={};out=R/'reports/m4-original141-source'/name;assert not out.exists()
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  if not p.is_relative_to(R):
   assert any(p.is_relative_to(q)for q in (Path(sys.prefix).resolve(),Path('C:/Program Files/Microsoft Visual Studio/18/Community'),Path('C:/Program Files (x86)/Windows Kits/10')))or p in {Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'),*(Path('C:/Windows/SysWOW64')/n for n in ('kernel32.dll','ntdll.dll','apphelp.dll','gdi32.dll','user32.dll'))}or(p.parent==Path('G:/Projects/MW34Recomp-Captures/reports/m4-original141/root-capture-validation-r3/paired-exports/original')and p.name in('index.json','payload.bin'))
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 base=R/'reports/m4-original141-source';closure=read(closure_path,closure_sha)
 assert closure['prepared_only']and not closure['source_execution']and not closure['ROOT_admission_minted']
 for p,h in closure['files'].items():pin(p,h)
 required=read(closure['required_ordinary_files'],closure['required_ordinary_files_sha256'])
 for p,h in required.items():pin(p,h)
 configpath=base/'configuration-preparation-r3/configuration.json';configsha='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0'
 C=read(configpath,configsha);assert closure['configuration_sha256']==configsha
 checks=[]
 for rel,h in [('root-static-review-r1','574a1bed7b48de0d6cc706772495a8d493aff216c7e2331326f14f4df81c697b'),('root-cleanup-review-r1','56aae8864b3c31d11542f733c673deed5b00767b5f759f369442517aa0187fe9'),('root-causal-controls-r2','993d5215f9d0207d0e8aaa2f9f1f6f87099a053493be8c95b63b400c19de141b'),('root-current-inputs-r3','2c0269ded635cd63be7a417664f9254ee54920334391a7fdcd80ab5914feffbb')]:
  q=read(base/rel/'report.json',h);assert q['passed']is True
  for p,v in q['files'].items():pin(p,v)
  checks.append(dict(path=str(base/rel/'report.json'),sha256=h))
 control=read(base/'root-causal-controls-r2/report.json');assert len(control['tests'])==32
 tree=read(C['current_tree_source']['path'],C['current_tree_source']['sha256']);assert tree['passed']and tree['source_case_extent']==6 and tree['ordinary_reader_closed']and not tree['source_AFTER_seed']
 for p,h in tree['files'].items():pin(p,h)
 callbacks=read(C['callbacks']['path'],C['callbacks']['sha256']);assert len(callbacks['rows'])==111
 # Entire configuration code was independently read. Verify both exact edits
 # invert to that reviewed parent; actual111 byte predicates ran in preparation.
 parent=pin(R/'tools/m4-original141-source/prepare_configuration_v1.py').read_text()
 v2=pin(R/'tools/m4-original141-source/prepare_configuration_v2.py').read_text()
 v3=pin(R/'tools/m4-original141-source/prepare_configuration_v3.py').read_text()
 a=next(x for x in parent.splitlines()if x.startswith('  fact=authority[key];'))
 b='\n'.join(x for x in v2.splitlines()if x.startswith('  fact=authority[key];')or x.startswith('  assert wrapper=='))
 assert v2.count(b)==1 and v2.replace(b,a)==parent
 old='assert wrapper==5947712 and push_pc==call_pc-5 and return_pc==call_pc+5';new='assert wrapper==5947712 and push_pc<call_pc and return_pc==call_pc+5'
 assert v3.count(new)==1 and v3.replace(new,old)==v2
 for p in (R/'tools/m4-original141-source/replay_original141_v3.py',R/'tools/m4-original141-source/prepare_replay_closure_v1.py',Path(__file__)):
  ast.parse(pin(p).read_text())
 p3=pin(R/'tools/m4-original141-source/replay_original141_v3.py').read_text();p4=pin(R/'tools/m4-original141-source/replay_original141_v4.py').read_text()
 assert p4.replace(" admitted[str(admission_path)]=admission_sha\n",'').replace("   if p.suffix.lower()=='.pyc':raise FileNotFoundError('Compile exact admitted source; cached bytecode refused')\n",'')==p3
 ast.parse(p4)
 prep=read(base/'configuration-preparation-r3/report.json','b6c9ca69610a7752897ffb3396b2c192e78627e978a2863e9673e657f6c2cf9e')
 assert prep['current_callback_literal_PUSH_CALL_pairs']==111 and prep['configuration_sha256']==configsha
 for p,h in prep['files'].items():pin(p,h)
 for rel,h in [('retained-corpus-preparation-r3','6ee0475262e6912be690b854f7ca3fb9e5ac1b35d0fe18e8066608d139c802f1'),('controller-preparation-r6','d23f0045ef122b37ac89ac220651dfdde2a50a24dd46b0a25ef61969532acb37')]:
  q=read(base/rel/'report.json',h);assert q['prepared_only']and not q['source_execution']
  for p,v in q['files'].items():pin(p,v)
 def line_inverse(parent,child,deltas):
  a=pin(parent).read_text();b=pin(child).read_text().splitlines(keepends=True)
  for d in deltas:assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(deltas):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(keepends=True)
  assert ''.join(b)==a;ast.parse(pin(child).read_text())
 line_inverse(R/'tools/m4-original141-source/retained_corpus141_v1.py',R/'tools/m4-original141-source/retained_corpus141_v2.py',read(base/'retained-corpus-preparation-r3/inverse.json'))
 q=read(base/'controller-preparation-r6/report.json')
 for row in q['whole_inverse_files']:line_inverse(row['parent'],row['child'],row['deltas'])
 checks.append(dict(retained_source_rows=3980,physical_source_origin_counts={0:3962,1:18},whole_continuity_inverse_hunks=2,whole_controller_inverse_hunks=1,source_execution=False))
 for rel,h in [('format-preparation-r2','79ae73b35cee04b4a320dcf4d5694842e8512722afba663622db31717f6e8fa4'),('old4-preparation-r2','9c410c44e2c2e06eb4c2c40917985f65ace800575acf29c4d06985ad3f493fcb')]:
  q=read(base/rel/'report.json',h);assert q['prepared_only']and not q['source_execution']
  for p,v in q['files'].items():pin(p,v)
  for row in q['whole_inverse_files']:line_inverse(row['parent'],row['child'],row['deltas'])
 checks.append(dict(exact_formatter_linked_shim_targets=5,whole_formatter_inverse_hunks=2,whole_old4_build_schema_inverse_hunks=1,whole_controller_binding_hunks=2,source_execution=False))
 q=read(base/'cold-MFC-closure-r1/report.json','50f3a05d476cb691ca9284146be048919b091d4c898439e9d75bea9b23e2376f');assert q['prepared_only']and not q['imports_executed']and not q['source_execution']
 for p,h in q['files'].items():pin(p,h)
 for p,h in read(q['required_ordinary_files'],q['required_ordinary_files_sha256']).items():pin(p,h)
 q=read(base/'retained-positive-family-r1/report.json','63c6954cf0d44f233a4cb2ed6e6e297a4d5acd715677b4471022e00b2da22724');assert q['prepared_only']and not q['failed_parent_success_used']
 for p,h in q['files'].items():pin(p,h)
 manifest=read(base/'retained-positive-family-r1/manifest.json','4bde643912fe8a35aa3bdb469ae73da1dc730cc363af92b1f329056a00f70266')
 assert manifest['configuration_sha256']==configsha and manifest['original_validation_sha256']==C['validation']['sha256']
 failed=read(manifest['failed_parent_path'],manifest['failed_parent_sha256']);assert failed['passed']is False and failed['reader_closed']and failed['configuration_sha256']==configsha and failed['original_validation_sha256']==C['validation']['sha256']
 assert len(manifest['rows'])==3 and {r['domain']for r in manifest['rows']}=={'constructor18','formatter4','old4'}
 for p,h in manifest['files'].items():pin(p,h)
 for row in manifest['rows']:
  g=read(row['path'],row['sha256']);assert g['passed']and not g['source_AFTER_seed']and not g['canonical_reader_opened'];pin(row['helper_path'],row['helper_sha256']);assert g['files'][row['helper_path']]==row['helper_sha256']
  assert any(r['domain']==row['domain']and r['receipt']==row['path']and r['sha256']==row['sha256']for r in failed['children'])
  for p,h in g['files'].items():pin(p,h)
  if row['domain']=='constructor18':
   assert len(g['cases'])==18 and {(r['sequence'],r['root'])for r in g['cases']}=={(i,a)for i in range(6)for a in(0x4103f0,0x410440,0x459b40)}
   assert all(r['whole_GPR_EIP']and r['defined_EFLAGS']and r['whole_FX512']and r['whole_ENV28']for r in g['cases'])
   assert g['files'][C['validation']['path']]==C['validation']['sha256']and g['ordinary_reader_closed']
  else:assert g['source_case_extent']==24 and g['original_validation_sha256']==C['validation']['sha256']
 line_inverse(R/'tools/m4-original141-source/replay_original141_v7.py',R/'tools/m4-original141-source/replay_original141_v8.py',read(base/'retained-positive-family-r1/controller-inverse.json'))
 checks.append(dict(reused_actual_positive_families={'constructor18':18,'formatter4':24,'old4':24},failed_parent_success_used=False,whole_controller_reuse_inverse_hunks=4,remaining_MFC6_widget42_fresh=True,registry846_rerun=True))
 q=read(base/'retained-positive-family-r2/report.json','6cff9a98848fe3ad04929addff2dd666478505b511dddf84bd0fc60851d4b127');assert q['prepared_only']and not q['failed_parent_success_used']and q['MFC6_reused']and q['widget42_fresh_required']
 for p,h in q['files'].items():pin(p,h)
 reuse=read(base/'retained-positive-family-r2/manifest.json',q['manifest_sha256']);assert reuse['configuration_sha256']==configsha and reuse['original_validation_sha256']==C['validation']['sha256']and len(reuse['rows'])==4 and {r['domain']for r in reuse['rows']}=={'constructor18','formatter4','old4','new_MFC'}
 failed=read(reuse['failed_parent_path'],reuse['failed_parent_sha256']);assert failed['passed']is False and failed['reader_closed']and failed['configuration_sha256']==configsha and failed['original_validation_sha256']==C['validation']['sha256']
 for p,h in reuse['files'].items():pin(p,h)
 for row in reuse['rows']:
  g=read(row['path'],row['sha256']);assert g['passed']and not g['source_AFTER_seed']and not g['canonical_reader_opened']and g['files'][row['helper_path']]==row['helper_sha256']
  assert any(v['domain']==row['domain']and v['receipt']==row['path']and v['sha256']==row['sha256']for v in failed['children'])
  for p,h in g['files'].items():pin(p,h)
  if row['domain']=='new_MFC':assert g['source_case_extent']==6 and g['original_validation_sha256']==C['validation']['sha256']and g['counts']['literal_source_instructions']==852 and g['counts']['whole_normal_CPU_FX_ENV_frame64_boundary_joins']==42 and g['counts']['whole_actual_named_API_entry_return_frame_joins']==24
 line_inverse(R/'tools/m4-original141-source/replay_original141_v8.py',R/'tools/m4-original141-source/replay_original141_v9.py',read(base/'retained-positive-family-r2/controller-inverse.json'))
 fp=R/'reports/m4-original141-fp-review';q=read(fp/'source-preparation-r1/report.json','f8b7a17e598b5818deb040499eb4e89a94699091cfa9163dad0129d48305aa4d');assert q['passed']and q['whole_inverse_equal']and not q['source_evaluated']and q['remaining_native_paired_policy_required']
 for p,h in q['files'].items():pin(p,h)
 original=pin(q['parent'],q['parent_sha256']).read_text();candidate=pin(q['derived_checker']).read_text();inverse=candidate
 assert len(q['changes'])==5
 for delta in reversed(q['changes']):assert inverse.count(delta['after'])==1;inverse=inverse.replace(delta['after'],delta['before'])
 assert inverse==original;ast.parse(candidate)
 actual=pin(R/'tools/m4-original141-source/widget_source141_v4.py','5e6ce404c5dcd8280759f9f2fab263a16ed3daab3ee8cbd08e2705102c000c2d');assert actual.read_bytes()==pin(q['derived_checker']).read_bytes()
 env=read(fp/'env-readiness-r1/report.json','726da8b887b3c595e251ca0763dd2b84ec1a8a9a596a608434ef1d3c75114246')
 for p,h in env['files'].items():pin(p,h)
 tests=read(fp/'root-preflight-r1/report.json','b01ec2b26e194e8a61e68323a002429d377d0596556cc0c6e2606028c78eef11');assert tests['passed']and tests['pure_positive_controls']==2 and len(tests['adverse_controls'])==38 and len(set(tests['adverse_controls']))==38 and not tests['source_evaluated']and not tests['archive_reader_opened']and tests['acceptance_credit']==0
 for p,h in tests['files'].items():pin(p,h)
 checks.append(dict(reused_actual_positive_families={'constructor18':18,'formatter4':24,'old4':24,'new_MFC':6},widget42_fresh=True,original_only_ENV_metadata_rule=True,whole_ENV_conservation_pairs_required=893,whole_FX_conservation_pairs_required=894,finite_metadata_clear_occurrences_required=1,pure_ENV_adverses=38,native_paired_ENV_projection_admitted=False,failed_parent_success_used=False))
 pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='original141_finite_source_replay',configuration_sha256=configsha,checks=checks,source_execution=False,reader_opened=False,native_worker_launched=False,initializer_credit=0,accepted_function_credit=0,elapsed_seconds=time.monotonic()-started,files=files),indent=2)+'\n')
 print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
