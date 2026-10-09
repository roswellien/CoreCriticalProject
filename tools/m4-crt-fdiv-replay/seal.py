"""Physical author closure for additive FDIV original-BEFORE replay research."""
import argparse,hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-replay'
EXPECTED={
 'reports/m4-crt-fdiv-replay/native-build-r1/build.json':'eff3aaacbf1610986403ea8bf029289d265c8595eba791c4030de2cad4d517ad',
 'reports/m4-crt-fdiv-replay/preparation-r1/report.json':'b4e36d5fd4966b4c4e9ab1a5b0564f699e5c6f851cc2e6bbeb643e99dd85ec3f',
 'reports/m4-crt-fdiv-replay/run-normal-r1/report.json':'9965638d34f8b04762b037c39ce8f6b64b6604a82e324d60777ced89fec39b07',
 'reports/m4-crt-fdiv-replay/author-model-r1/report.json':'b9ce1240b69c0787bdce31b11ca550bbcf519d026068224907126c27d98d72f4',
 'reports/m4-crt-fdiv-replay/worker-controls-normal-r2/report.json':'b84ca6aca336ec5c136a06f6347604e8fedd50431f74eeb10c8fb68f5630ea68',
 'reports/m4-crt-fdiv/independent-native-closure-r2/report.json':'463403fd5751828c8b575a30e60743f28dbd79a34fafed221387e145615d65b1',
 'reports/m4-crt-fdiv-reference/root-pre-execution-review-r2/report.json':'1ad3d36de177a8c3a54ee49e52b1ee4a64ce280bcba098b892abaa188787c83a',
 'reports/m4-crt-fdiv-reference/run-normal-r1/report.json':'4d5b66e3b48a808b722b0b38e921d11a8e716b1fe06f79516364283c5f0261e6',
 'reports/m4-crt-fdiv-reference/observations-r1/report.json':'229ddb12152f31820c4ba2d42d141b58156a3217b1554c972c18038354fec8a0',
}
MAPS=[
 'reports/m4-crt-fdiv/independent-native-closure-r2/pins.json',
 'reports/m4-crt-fdiv-reference/root-pre-execution-review-r2/pins.json',
 'reports/m4-crt-fdiv-reference/observations-r1/pins.json',
 'reports/m4-crt-fdiv-reference/run-normal-r1/pins.json',
 'reports/m4-crt-fdiv-replay/preparation-r1/pins.json',
 'reports/m4-crt-fdiv-replay/launch-recipe-r1/pins.json',
 'reports/m4-crt-fdiv-replay/run-normal-r1/pins.json',
 'reports/m4-crt-fdiv-replay/author-model-r1/pins.json',
 'reports/m4-crt-fdiv-replay/worker-controls-normal-r1/pins.json',
 'reports/m4-crt-fdiv-replay/worker-controls-normal-r2/pins.json',
]
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,m):
 if not v:raise ValueError(m)
def save(p,v):
 with pathlib.Path(p).open('x',encoding='utf-8')as f:f.write(json.dumps(v,indent=2)+'\n')
def main(out):
 out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh author closure directory');files={};checks=[]
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact frozen closure binding '+str(p));need(str(p)not in files or files[str(p)]==v,'Nonconflicting aggregate binding '+str(p));files[str(p)]=v
 for relative,h in EXPECTED.items():bind(ROOT/relative,h)
 for relative in MAPS:
  path=ROOT/relative;m=read(path);items=m.get('files',m)
  need(isinstance(items,dict)and all(isinstance(h,str)and len(h)==64 for h in items.values()),'Physical flat prerequisite map '+relative)
  for p,h in items.items():bind(p,h)
  bind(path);checks.append({'map':str(path),'sha256':sha(path),'physical_bindings_rehashed':len(items)})
 b=read(BASE/'native-build-r1/build.json')
 for group in ('sources','tools','libraries','compiler_read_headers','artifacts'):
  for p,h in b[group].items():bind(p,h)
 tooling=read(BASE/'run-normal-r1/tooling-supplement.json')
 for level,record in tooling['levels'].items():
  for tool in record['configured_tools'].values():bind(tool['path'],tool['current_sha256'])
  for kind in ('cache','rules','build_log'):bind(record[kind+'_path'],record[kind+'_sha256'])
 run=read(BASE/'run-normal-r1/report.json');model=read(BASE/'author-model-r1/report.json');controls=read(BASE/'worker-controls-normal-r2/report.json');failed=read(BASE/'worker-controls-normal-r1/failure.json')
 need(run['passed']and run['records']==48 and not run['original_native_equivalence_accepted'],'Actual observations only')
 need(model['passed']and model['native_records']==48 and model['observer_corruptions_rejected']==1152 and model['FX_difference_offsets_union']==list(range(160,176))and not model['whole_original_stack_or_fullFX_equivalence'],'Exact author source/difference scope')
 need(controls['passed']and controls['actual_controls']==14,'Exact causal worker controls')
 need(not failed['passed']and failed['observations'][-1]['actual_stderr']=='Input file unavailable\r\n'and failed['observations'][-1]['expected_diagnostic']=='Actual source open','Preserved checker expectation failure, no worker mutation')
 contract=ROOT/'docs/m4-crt-fdiv-replay-contract.md';bind(contract)
 sources=list((ROOT/'tools/m4-crt-fdiv-replay').rglob('*'));sources=[p for p in sources if p.is_file()and '__pycache__'not in str(p)]
 out.mkdir();literal=[]
 for p in sources:
  bind(p);copy=out/'sources'/p.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,copy);bind(copy,files[str(p.resolve())]);literal.append({'path':str(p),'sha256':files[str(p.resolve())],'literal_path':str(copy)})
 differences=read(BASE/'author-model-r1/observed-differences.json')['rows']
 report={'passed':True,'scope':'Frozen author closure of real-original-BEFORE native replay and explicit observed differences; independent acceptance pending',
  'actual_original_reference':{'direct_rows_used':24,'debug_rows_retained_separately':24,'direct_before_only_native_inputs':True,'AFTER_used_as_execution_input':False},
  'actual_native':{'O0_records':24,'O2_records':24,'State_bytes':3504,'owned_pages':9,'source_events':4656,'service_routes':144,'own64bitWindows_queries':True},
  'author_source_model':{'whole_BEFORE_and_after_State_pages_FX':True,'observer_corruptions_rejected':1152,'source_dependency_PCs':204},
  'observed_original_comparison':{'final32CPU_agrees_under_only_declared_ESP_outerPC_projection':True,'CW_SW_tags_raw80_MXCSR_legacy_metadata_agree':True,
   'full_FX_equal_rows':0,'all_differing_FX_byte_offsets':list(range(160,176)),
   'ECX_residual_halves_original_native':['0000','6824'],'residual_original_W_offsets':[-34,-42],
   'all_observed_stack_difference_ranges_preserved':True,'stack_differing_byte_counts':[{k:r[k]for k in('level','original_id','all_differing_observed_stack_bytes')}for r in differences],
   'IAT_transport_only_provider_differences':True,'whole_real_stack_or_fullFX_equivalence_claim':False},
  'actual_new_worker_controls':14,'preserved_control_failure':'r1 checker named missing-file diagnostic incorrectly; r2 source-only expectation corrected in a new file/path; workers/libraries/input pack unchanged',
  'build':{'path':str(BASE/'native-build-r1/build.json'),'sha256':sha(BASE/'native-build-r1/build.json'),'sources':len(b['sources']),'direct_tools':len(b['tools']),'compiler_read_headers':len(b['compiler_read_headers']),'artifacts':len(b['artifacts']),'linked_frozen_libraries':b['libraries']},
  'tooling_scope':'Supplemental post-build current hash bindings and actual verbose compiler/link/Ninja commands, distinct from configured RC/MT declarations and execution-time attestation',
  'prerequisite_maps_rehashed':checks,'literal_new_sources':literal,
  'host_FP_scope':'Internal Registry restoration checkpoints; separate accepted direct assembly boundary supplement remains scoped x87/ENV/MXCSR/nonvolatile SIMD, no volatile padding equality',
  'scope_limits':['serial fresh ordinary private paths','12 masked normalized IC0 CW; empty TOP0/SW0','successful non-NULL real Windows lookup/query only','no fallback numerical execution','no full original SIMD/Windows stack ABI equivalence','no historical process-memory attestation','no full DllMain/CRT/game entry/menus'],
  'independent_replay_acceptance':False,'whole_M4_complete':False}
 save(out/'report.json',report);bind(out/'report.json');save(out/'pins.json',{'files':files})
 print(json.dumps({'passed':True,'bindings':len(files),'new_sources':len(literal),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
