"""Seal independent current proof and explicit history-only refusals; no native execution."""
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
    base=ROOT/'reports/m4-crt-heap-create-review';out=base/name
    need(name.startswith('sealed-') and out.parent==base and not out.exists(),'Fresh independent current seal');out.mkdir()
    history=base/'history-r1';need(not history.exists(),'Fresh immutable history notes');history.mkdir()
    notes=[('check_initial_name_lookup',None,'Direct checker invocation refused before output creation because the adapted schema omitted the need helper; no native rerun or execution claim.'),('check-r1',base/'check-r1','Direct checker invocation refused because its expected nonzero incoming error was incorrect. Actual captured scheduler incoming/restored LastError was zero. Fixed in fresh check-r2; native-r1 unchanged.'),('caller-error-r1',base/'caller-error-r1','Separate checker refused a generic path object unsupported by the frozen hardware validator. O0 native and pack stages had passed. Fresh caller-error-r2 reused these exact O0 stages/archive, executed O2 once, and used the frozen LogicalReader.')]
    refusal_paths=[]
    for label,location,detail in notes:
        p=history/(label+'-recorded-refusal.json');publish_bytes(p,(json.dumps({'observed_result':'checker-only refusal','detail':detail,'original_output_directory':str(location) if location else None,'record_source':'Observed direct tool output, recorded afterward; not a measured zero-exit stage receipt','native_rerun_due_to_checker':False,'proof_credit':False},indent=2)+'\n').encode());refusal_paths.append(p)
    historical=[]
    for directory,meaning in [('compiled-r1','Failed fixture compilation: serializer expected fd::HostIdentity rather than m4_cmd_native::ApiIdentity; no worker executed.'),('compiled-r2','Passed compile superseded before execution by explicit handling of author terminal throw occurring before the independent duplicate-cleanup callback.')]:
        p=base/directory/'flat-build.json';historical.append({'path':str(p),'sha256':sha_file(p),'meaning':meaning,'current_proof_credit':False})
    files={};evidence={}
    def pin(p,d=None):
        p=Path(p).absolute();a=sha_file(p);need(d is None or a==d,'Current independent proof dependency');k=normalized(str(p));need(k not in files or files[k]==a,'Conflict-free sealed physical proof');files[k]=a;return a
    for label,rel,d in [('source','source-r1/report.json','6a4140b0cfc704153b42b872e1907ead032c9ee9cb0e986bc0957972be9247b8'),('audit','audit-r1/report.json','00e42495fd39f4257fc99e90da8d04e68c8bcfba1b185ca66db9be400891b912'),('native','native-r1/report.json','8ec6a42d377b0f823a3a76b92d588da1c7e86ca75a966c7b37f7860f1aef4294'),('hardware','check-r2/report.json','9228468d55e4ff35ad3c8fae063d7edbf815c2cb3e7e87facabbd2417c032808'),('caller_error','caller-error-r2/report.json','3f2a62df28cf4d0d1622b0a4f10b8908177cb2db2a47e9e2e6751831cefcbd52')]:
        p=base/rel;pin(p,d);row=read(p);need(row['passed'] is True,'Exact passed independent receipt')
        if 'files' in row:deps=row['files']
        else:
            pins=p.parent/'pins.json';pin(pins);deps=read(pins)['files']
        for q,h in deps.items():pin(q,h)
        evidence[label]={'path':str(p),'sha256':d,'top_level_keys':list(row),'physical_dependencies':len(deps)}
    for p in refusal_paths:pin(p)
    for row in historical:pin(row['path'],row['sha256'])
    syntax=[];trailing=[]
    for p in HERE.iterdir():
        if p.is_file():
            pin(p)
            if p.suffix=='.py':ast.parse(p.read_text());syntax.append(p.name)
            for number,line in enumerate(p.read_text().splitlines(),1):
                if line.rstrip()!=line:trailing.append((p.name,number))
    need(not trailing,'No new trailing whitespace')
    readme=HERE/'README.md';links=re.findall(r'\]\(([^)]+)\)',readme.read_text());local=[link for link in links if not link.startswith(('https://','http://'))]
    need(all((HERE/link).resolve().is_file() for link in local),'Every local current README link resolves')
    pin(Path(sys.executable));pin(ROOT/'tools/m4-pipeline/manifests.py');pin(ROOT/'tools/m4-pipeline/paths.py');closure=verify_manifest(files)
    report={'passed':True,'scope':'Sealed independent exact current source/API ownership review plus compiled hostile corpus and separate explicit nonzero host-error fixture; no complete causal source-model oracle','evidence':evidence,'native_scenarios':144,'native_assertions':6850,'actual_hardware_pairs':288,'actual_HeapCreate_calls':80,'actual_successful_HeapDestroy_calls':80,'malformed_token_denials':36,'hardware_semantic_denials':548,'inventory_API_ownership_denials':27,'source_PCs':13,'source_accesses':10,'separate_API_return_reads':1,'executed_success_source_bytes':48,'reused_heap_COâ€‹FF_source_bytes':84,'borrowed_pages':18,'reused_guest_objects':26,'new_guest_objects':0,'history_only_compiles':historical,'checker_refusals':[{'path':str(p),'sha256':sha_file(p)} for p in refusal_paths],'README_sha256':sha_file(readme),'python_AST_files':syntax,'trailing_whitespace_count':0,'local_links_checked':len(local),'original_executed':False,'ordinary_game_launched':False,'full_causal_source_model_oracle':False,'heap_initialized':False,'mode_selector_body_executed':False,'whole_M4_complete':False,'physical_closure':closure,'files':files}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'README_sha256':sha_file(readme),'dependencies':len(files),'python_AST':len(syntax),'local_links':len(local)}))
if __name__=='__main__':main(*sys.argv[1:])
