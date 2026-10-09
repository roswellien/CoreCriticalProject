"""Seal current independent source, State/COFF, native adoption, and hardware proof."""
import ast,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes

def need(ok,why):
    if not ok:raise ValueError(why)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def main(name,native_name,check_name,native_sha,check_sha):
    base=ROOT/'reports/m4-crt-heap-return-review';out=base/name
    need(name.startswith('sealed-') and out.parent==base and not out.exists(),'Fresh immutable independent seal');out.mkdir();files={};evidence={}
    def pin(p,h=None):
        p=Path(p).absolute();d=sha_file(p);need(h is None or d==h,'Current frozen physical association '+str(p));key=normalized(str(p));need(key not in files or files[key]==d,'Conflict-free independent closure');files[key]=d;return d
    specs=[('source','source-r3/report.json','814f2fb571baf2c60f88905204bf28ae1552a4e1a1b0d4fe3a2584f8525a8904'),('audit','audit-r1/report.json','634c63166c3ca327b5dbeb426ec50c09f21d28b80b42e741b862cbd8792dedb6'),('compiled','compiled-r1/flat-build.json','c5b05ccb5be8f41d547fd6d1f0f452cc5b5bd082b037f77d5f036386f0256402'),('native',native_name+'/report.json',native_sha),('hardware',check_name+'/report.json',check_sha)]
    for label,rel,h in specs:
        p=base/rel;d=pin(p,h);row=read(p);need(row['passed'] is True,'Current passed independent evidence')
        if label=='compiled':
            need(row['compiled_only'] is True,'Compile-only fixture association');deps={}
            for category in ('sources','tools','libraries','entry_objects','matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects','locale_objects','heap_objects','heap_mode_objects','heap_version_objects','compiler_read_headers','artifacts'):
                for q,value in row[category].items():need(q not in deps or deps[q]==value,'Exact reused compiled associations');deps[q]=value
        elif 'files' in row:deps=row['files']
        else:pin(p.parent/'pins.json');deps=read(p.parent/'pins.json')['files']
        for q,value in deps.items():pin(q,value)
        evidence[label]={'path':str(p),'sha256':d,'physical_dependencies':len(deps)}
    audit=read(base/'audit-r1/report.json');native=read(base/native_name/'report.json');hardware=read(base/check_name/'report.json')
    need(native['native_scenarios']==244 and native['native_checks']==15042 and native['malformed_token_denials']==44 and native['counterfactual_direct_host_failure_queries']==4 and native['native_rerun'] is False and native['adopts_actual_native_execution'] is True,'Exact completed immutable native adoption')
    need(hardware['native_sha256']==evidence['native']['sha256'] and hardware['native_scenarios']==244 and hardware['native_checks']==15042 and hardware['actual_hardware_pairs']==492 and hardware['hardware_semantic_denials']==548 and hardware['inventory_request_denials']==68,'Actual unchanged strict rich hardware/inventory corpus')
    expected={'actual_HeapCreate_calls':196,'actual_successful_HeapDestroy_calls':196,'actual_integrated_GetVersionExA_calls':132,'counterfactual_direct_host_failure_queries':4,'actual_output_DWORD_commits':4078,'actual_selector_RETs':90,'actual_initializer_RETs':24,'actual_source_mode_stores':66,'actual_initializer_RETURN_WORD_reads':28}
    need(all(hardware[k]==v for k,v in expected.items()),'Exact independently checked source/API/private lifecycle counts')
    need(audit['mode1_source_PCs']==59 and audit['mode1_source_accesses']==35 and audit['mode1_original_source_CALLs']==5 and audit['mode1_original_source_RETs']==3 and audit['separate_API_return_reads']==2 and audit['source_identity_bytes']==2086 and audit['mode1_executed_source_bytes']==192 and audit['reused_guest_objects']==38 and audit['new_guest_objects']==0 and audit['new_guarded_source_bytes']==0 and audit['borrowed_pages']==21,'Exact authentic source and unchanged guest object/ABI contract')
    packaging=read(native['packaging_path']);pin(native['packaging_path'],native['packaging_sha256']);need(packaging['passed'] is True and packaging['native_rerun'] is False and packaging['transport_limits_changed'] is False and packaging['copy_verified'] is True,'Explicit bounded same-stage publication proof')
    for level,info in native['levels'].items():
        need(info['result']['scenarios']==122 and info['result']['checks']==7521 and info['result']['malformed_token_denials']==22 and hardware['logical_files'][level]==info['logical_files'],'Exact per-optimization native/archive counts')
        need(len(info['bundles'])==2 and sum(part['logical_files'] for part in info['bundles'])==info['logical_files'] and all(part['logical_files']<=200000 for part in info['bundles']),'Bounded strict archive corpus')
    histories=[]
    for rel in ('readiness-r1/report.json','history-r1/source-r1-superseded.json','packaging-refusal-r1/report.json','hardlink-refusal-r1/report.json','check-preflight-r1/refusal.json'):
        p=base/rel;pin(p);row=read(p);need(row['passed'] is False and row['current_proof_credit'] is False,'Preserved refused/superseded history grants no proof credit')
        for q,value in row.get('files',{}).items():pin(q,value)
        if 'checker_sha256' in row:pin(p.parent/'checker-before-correction.py',row['checker_sha256'])
        histories.append({'path':str(p),'sha256':sha_file(p),'current_proof_credit':False})
    check_refusal=base/'check-r1/refusal.json'
    if check_refusal.exists():
        pin(check_refusal);row=read(check_refusal);need(row['passed'] is False and row['current_proof_credit'] is False,'Checker correction history grants no success credit')
        for q,value in row.get('files',{}).items():pin(q,value)
        histories.append({'path':str(check_refusal),'sha256':sha_file(check_refusal),'current_proof_credit':False})
    old=ROOT/'reports/m4-crt-heap-version-review/failed-native-r1/report.json';pin(old,'33b04d1f74afbbccb3cec2b33fb2f85119e7f1e29ba5837f9a3cef912a701811');histories.append({'path':str(old),'sha256':sha_file(old),'current_proof_credit':False,'identity_only':True})
    syntax=[];trailing=[]
    for p in sorted(HERE.iterdir()):
        if p.is_file():
            pin(p)
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'));syntax.append(p.name)
            for number,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
                if line.rstrip()!=line:trailing.append((p.name,number))
    need(not trailing,'Fresh source whitespace check')
    readme=HERE/'README.md';links=re.findall(r'\]\(([^)]+)\)',readme.read_text());local=[p for p in links if not p.startswith(('http://','https://'))];need(all((HERE/p).resolve().is_file() or (HERE/p).resolve()==(out/'report.json').resolve() for p in local),'Proof document links resolve or name this exact pending seal')
    syntax_path=base/'syntax-r1/report.json';pin(syntax_path);parsed=read(syntax_path);need(parsed['passed'] is True and parsed['PowerShell_AST_files']==1 and parsed['Python_AST_files']==syntax,'Actual current Python and PowerShell parser receipt')
    for q,value in parsed['files'].items():pin(q,value)
    for p in (Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
    report={'passed':True,'scope':'Independent authentic existing caller mode-store and initializer RET, unchanged complete State ABI/38 AMD64 COFF reuse, actual private API/heap lifecycle, same immutable native corpus and bounded archive union with unchanged strict rich hardware semantics; no full causal source-model oracle','evidence':evidence,'native_scenarios':244,'native_assertions':15042,'malformed_token_denials':44,'declared_initial_lower_stack_patterns':6,'author_controls_per_optimization':12,'independent_controls_per_optimization':104,'actual_hardware_pairs':492,'hardware_semantic_denials':548,'inventory_request_denials':68,**expected,'logical_files':hardware['logical_files'],'source_PCs':59,'source_accesses':35,'source_CALLs':5,'source_RETs':3,'separate_API_return_reads':2,'executed_success_source_bytes':192,'new_guarded_source_bytes':0,'newly_admitted_existing_source_bytes':23,'combined_source_identity_bytes':2086,'combined_guarded_source_bytes':230,'borrowed_pages':21,'reused_guest_objects':38,'new_guest_objects':0,'unchanged_FDIV_libraries':2,'history_only_receipts':histories,'README_sha256':sha_file(readme),'python_AST_files':syntax,'PowerShell_AST_files':1,'trailing_whitespace_count':0,'local_links_checked':len(local),'original_executed':False,'ordinary_game_launched':False,'native_executed':False,'adopts_actual_native_execution':True,'native_rerun':False,'GetVersionExA_executed':False,'validates_actual_native_GetVersionExA':True,'synthetic_API_results':False,'alternate_query_branch_live_coverage':False,'source_selector_result_produced':True,'guest_heap_mode_global_published':True,'heap_initializer_completed_for_measured_mode1':True,'fragment_caller_TEST_executed':False,'persistent_game_heap_proved':False,'heap_initialized':False,'original_stack_guard_growth_proved':False,'original_lower_stack_bytes_equivalent':False,'full_causal_source_model_oracle':False,'whole_M4_complete':False,'physical_closure':verify_manifest(files),'files':files}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());need(all((HERE/p).resolve().is_file() for p in local),'All published proof document links resolve');publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'README_sha256':sha_file(readme),'dependencies':len(files),'native_assertions':15042}))

if __name__=='__main__':main(*sys.argv[1:])
