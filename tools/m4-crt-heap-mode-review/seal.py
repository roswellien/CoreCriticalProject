"""Seal completed immutable independent proof; no native execution or new API call."""
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
    base=ROOT/'reports/m4-crt-heap-mode-review';out=base/name
    need(name.startswith('sealed-') and out.parent==base and not out.exists(),'Fresh sealed independent receipt');out.mkdir();files={};evidence={}
    def pin(p,d=None):
        p=Path(p).absolute();a=sha_file(p);need(d is None or a==d,'Current frozen independent physical association '+str(p));k=normalized(str(p));need(k not in files or files[k]==a,'Conflict-free seal');files[k]=a;return a
    for label,rel,d in [('source','source-r1/report.json','813350c744665fc61435d9d7cf1d1ba3fb8c8fe8dc8944b6c4538ec7b7488ce0'),('audit','audit-r1/report.json','8ec61c385a275aaf6fca985020f8e057ce715628131d762a99aba2f56b48323f'),('native','native-r1/report.json','b9e0de2f41b9a0f1180d18a0fc9936fd5a884e9f451011c821ad8708782f8596'),('hardware','check-r2/report.json','f2581beffde5458ba5d2c2efb4107d94af1af05bf892c84692b48f12d16e18f3')]:
        p=base/rel;digest=pin(p,d);row=read(p);need(row['passed'] is True,'Completed passed independent proof')
        if 'files' in row:deps=row['files']
        else:pin(p.parent/'pins.json');deps=read(p.parent/'pins.json')['files']
        for q,h in deps.items():pin(q,h)
        evidence[label]={'path':str(p),'sha256':digest,'top_level_keys':list(row),'physical_dependencies':len(deps)}
    native=read(base/'native-r1/report.json');hardware=read(base/'check-r2/report.json')
    need(native['native_scenarios']==132 and hardware['actual_hardware_pairs']==264 and hardware['hardware_semantic_denials']==548 and hardware['actual_HeapCreate_calls']==hardware['actual_successful_HeapDestroy_calls']==84,'Exact current completed fixture/HW ownership counts')
    syntax=[];trailing=[]
    for p in HERE.iterdir():
        if p.is_file():
            pin(p)
            if p.suffix=='.py':ast.parse(p.read_text());syntax.append(p.name)
            for number,line in enumerate(p.read_text().splitlines(),1):
                if line.rstrip()!=line:trailing.append((p.name,number))
    need(not trailing,'No new trailing whitespace');readme=HERE/'README.md';links=re.findall(r'\]\(([^)]+)\)',readme.read_text());need(all((HERE/link).resolve().is_file() for link in links),'Every local proof link resolves')
    history=base/'history-r1/check-r1-refusal.json';pin(history)
    for q,h in read(history)['files'].items():pin(q,h)
    syntax_path=base/'syntax-r1/report.json';pin(syntax_path);syntax_receipt=read(syntax_path);need(syntax_receipt['passed'] is True and syntax_receipt['PowerShell_AST_files']==1,'Actual PowerShell parser accepts fresh build file')
    for q,h in syntax_receipt['files'].items():pin(q,h)
    for p in (Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
    closure=verify_manifest(files)
    report={'passed':True,'scope':'Immutable independent source/private ownership/State ABI/COFF audit plus compiled probe fault/input corpus and unchanged rich hardware semantics; no full causal source-model oracle','evidence':evidence,'native_scenarios':132,'native_assertions':native['native_checks'],'declared_initial_lower_stack_patterns':6,'author_controls_per_optimization':12,'independent_controls_per_optimization':48,'actual_hardware_pairs':264,'actual_HeapCreate_calls':84,'actual_successful_HeapDestroy_calls':84,'malformed_token_denials':native['malformed_token_denials'],'hardware_semantic_denials':548,'inventory_request_denials':hardware['inventory_request_denials'],'source_PCs':39,'source_accesses':24,'separate_API_return_reads':1,'executed_success_source_bytes':132,'new_compiled_guarded_source_bytes':86,'borrowed_pages':20,'reused_guest_objects':26,'new_guest_objects':4,'history_only_receipts':[{'path':str(history),'sha256':sha_file(history),'current_proof_credit':False}],'README_sha256':sha_file(readme),'python_AST_files':syntax,'PowerShell_AST_files':1,'trailing_whitespace_count':0,'local_links_checked':len(links),'original_executed':False,'ordinary_game_launched':False,'GetVersionExA_executed':False,'original_stack_guard_growth_proved':False,'original_lower_stack_bytes_equivalent':False,'new_nonzero_caller_error_fixture':False,'full_causal_source_model_oracle':False,'heap_mode_selected':False,'heap_initialized':False,'whole_M4_complete':False,'physical_closure':closure,'files':files}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'README_sha256':sha_file(readme),'dependencies':len(files),'python_AST':len(syntax),'local_links':len(links)}))
if __name__=='__main__':main(*sys.argv[1:])
