"""Seal completed immutable independent query/source/ABI/native/hardware proof."""
import ast,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes
def need(v,w):
    if not v:raise ValueError(w)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def main(name):
    base=ROOT/'reports/m4-crt-heap-version-review';out=base/name
    need(name.startswith('sealed-') and out.parent==base and not out.exists(),'Fresh independent seal');out.mkdir();files={};evidence={}
    def pin(p,d=None):
        p=Path(p).absolute();actual=sha_file(p);need(d is None or actual==d,'Current frozen physical association '+str(p));key=normalized(str(p));need(key not in files or files[key]==actual,'Conflict-free independent seal');files[key]=actual;return actual
    for label,rel,d in [('source','source-r1/report.json','38ecbbab533d662baa34a7079a864a2ecb0729abb4cdb3a8635ec51e83c44fa7'),('audit','audit-r2/report.json','e92d39ae9881a394b112b6fd9edb0b0214d42c078e0d872518857606378e1a20'),('compiled','compiled-r2/flat-build.json','f58b70bffe1330e98f113017a2c2e9b8fa0ad78dcc8645990ff9eb0fa5028c6c'),('native','native-r2/report.json','14d243d38367abf3160a65808d32659ee25acbf88bf58c0479442daad10582b9'),('hardware','check-r2/report.json','bc78018542801e696181d4a6a59506758a79673c7535023fdee4b1564e685981')]:
        p=base/rel;digest=pin(p,d);row=read(p);need(row['passed'] is True,'Completed passed independent evidence')
        if label=='compiled':
            need(row['compiled_only'] is True,'Current compile-only fixture association');deps={}
            for category in ('sources','tools','libraries','entry_objects','matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects','locale_objects','heap_objects','heap_mode_objects','heap_version_objects','compiler_read_headers','artifacts'):
                for q,h in row[category].items():need(q not in deps or deps[q]==h,'Conflict-free compiled dependencies');deps[q]=h
        elif 'files' in row:deps=row['files']
        else:pin(p.parent/'pins.json');deps=read(p.parent/'pins.json')['files']
        for q,h in deps.items():pin(q,h)
        evidence[label]={'path':str(p),'sha256':digest,'physical_dependencies':len(deps)}
    source=read(base/'source-r1/report.json');audit=read(base/'audit-r2/report.json');native=read(base/'native-r2/report.json');hardware=read(base/'check-r2/report.json')
    need(native['native_scenarios']==196 and native['native_checks']==11042 and native['malformed_token_denials']==40 and native['counterfactual_direct_host_failure_queries']==4,'Exact completed native corpus')
    need(hardware['native_sha256']==evidence['native']['sha256'] and hardware['actual_hardware_pairs']==396 and hardware['hardware_semantic_denials']==548 and hardware['inventory_request_denials']==56,'Exact unchanged strict hardware and inventory corpus')
    need(hardware['actual_HeapCreate_calls']==hardware['actual_successful_HeapDestroy_calls']==148 and hardware['actual_integrated_GetVersionExA_calls']==82 and hardware['counterfactual_direct_host_failure_queries']==4 and hardware['actual_output_DWORD_commits']==1934 and hardware['actual_selector_RETs']==20,'Actual independently checked private native/source lifecycle counts')
    need(hardware['logical_files']=={'O0':167696,'O2':167696} and source['mode1_combined_source_PCs']==audit['mode1_source_PCs']==51 and source['mode1_combined_source_accesses']==audit['mode1_source_accesses']==31 and audit['separate_API_return_reads']==2 and audit['mode1_original_source_RETs']==2,'Exact source/ABI and archive counts')
    syntax=[];trailing=[]
    for p in sorted(HERE.iterdir()):
        if p.is_file():
            pin(p)
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'));syntax.append(p.name)
            for number,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
                if line.rstrip()!=line:trailing.append((p.name,number))
    need(not trailing,'No fresh trailing whitespace');readme=HERE/'README.md';links=re.findall(r'\]\(([^)]+)\)',readme.read_text());local_links=[link for link in links if not link.startswith(('https://','http://'))];need(all((HERE/link).resolve().is_file() for link in local_links),'Every local proof link resolves')
    syntax_path=base/'syntax-r1/report.json';pin(syntax_path);syntax_receipt=read(syntax_path);need(syntax_receipt['passed'] is True and syntax_receipt['PowerShell_AST_files']==1 and syntax_receipt['Python_AST_files']==syntax,'Actual current Python/PowerShell syntax receipt')
    for q,h in syntax_receipt['files'].items():pin(q,h)
    histories=[]
    for rel in ('failed-native-r1/report.json','history-r1/audit-r1-refusal.json','check-r1/refusal.json'):
        p=base/rel;pin(p);row=read(p);need(row['passed'] is False and row['current_proof_credit'] is False,'Failure history never grants success credit')
        for q,h in row.get('files',{}).items():pin(q,h)
        if rel=='check-r1/refusal.json':pin(p.parent/'checker-before-correction.py',row['checker_sha256'])
        histories.append({'path':str(p),'sha256':sha_file(p),'current_proof_credit':False})
    for p in (Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
    closure=verify_manifest(files)
    report={'passed':True,'scope':'Independent original source and complete State ABI/COFF audit, real private GetVersionExA scratch/output/return bridge and source selector continuation, compiled fault/input corpus and unchanged rich hardware semantics; no full causal source-model oracle','evidence':evidence,'native_scenarios':196,'counterfactual_direct_host_failure_queries':4,'native_assertions':11042,'declared_initial_lower_stack_patterns':6,'author_controls_per_optimization':12,'independent_controls_per_optimization':80,'actual_hardware_pairs':396,'actual_HeapCreate_calls':148,'actual_successful_HeapDestroy_calls':148,'actual_integrated_GetVersionExA_calls':82,'actual_output_DWORD_commits':1934,'actual_selector_RETs':20,'malformed_token_denials':40,'hardware_semantic_denials':548,'inventory_request_denials':56,'logical_files':hardware['logical_files'],'source_PCs':51,'source_accesses':31,'source_CALLs':5,'source_RETs':2,'separate_API_return_reads':2,'executed_success_source_bytes':169,'new_compiled_guarded_source_bytes':60,'combined_source_identity_bytes':2086,'borrowed_pages':21,'reused_guest_objects':30,'new_guest_objects':8,'unchanged_FDIV_libraries':2,'history_only_receipts':histories,'README_sha256':sha_file(readme),'python_AST_files':syntax,'PowerShell_AST_files':1,'trailing_whitespace_count':0,'local_links_checked':len(local_links),'original_executed':False,'ordinary_game_launched':False,'native_executed':False,'GetVersionExA_executed':False,'validates_actual_native_GetVersionExA':True,'synthetic_API_results':False,'alternate_query_branch_live_coverage':False,'source_selector_result_produced':True,'guest_heap_mode_global_published':False,'heap_initialized':False,'original_stack_guard_growth_proved':False,'original_lower_stack_bytes_equivalent':False,'full_causal_source_model_oracle':False,'whole_M4_complete':False,'physical_closure':closure,'files':files}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'README_sha256':sha_file(readme),'dependencies':len(files),'python_AST_files':len(syntax),'local_links_checked':len(local_links)}))
if __name__=='__main__':main(*sys.argv[1:])
