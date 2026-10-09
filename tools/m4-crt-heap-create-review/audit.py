"""Independent current source, private OS ownership, State ABI and reused COFF audit."""
import importlib.util,json,sys,subprocess,difflib
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest,normalized,unique_object
from capture_bundle import sha_file

def need(v,w):
    if not v:raise ValueError(w)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
def main(preparation,build_path,name):
    prep,build_path=Path(preparation).absolute(),Path(build_path).absolute()
    base=ROOT/'reports/m4-crt-heap-create-review';out=base/name
    need(name.startswith('audit-') and out.parent==base and not out.exists(),'Fresh independent read-only audit')
    out.mkdir();files={}
    def pin(p,d=None):
        p=Path(p).absolute();actual=sha_file(p);need(d is None or actual==d,'Current exact source dependency: '+str(p));k=normalized(str(p));need(k not in files or files[k]==actual,'Conflict-free physical audit');files[k]=actual;return actual
    baseline=ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json'
    pin(baseline,'a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d')
    pin(prep/'report.json','b85a555d6d14ef97afd5547aef0b6bba96aae1597e72aed40e1d41a33562d1e9')
    pin(prep/'pins.json','da6895282c9a30dedaf01dd84dc83b059f4a59d20f77e5f1c18a3e3c1b54017a')
    pin(build_path,'28b96699f22ade5daaaab35fa15b63d16debbd3995eafd8e4e790bb57de7cd9e')
    old_path=ROOT/'reports/m4-crt-heap-init/build-r1/build.json';pin(old_path,'b319a82d8c9d61d4db269de520684b1b7e9caa6e7636a125bdaa63cbf8d15104')
    old,build=read(old_path),read(build_path);p=read(prep/'report.json')
    need(build['passed'] is True and build['preparation_sha256']==sha_file(prep/'report.json') and normalized(build['preparation_path'])==normalized(str(prep/'report.json')),'Actual stable exact candidate build')
    need(p['reused_guest_objects']==26 and p['new_guest_objects']==0 and p['borrowed_pages']==18 and p['prior_pages_preserved']==17 and p['scheduler_store_count']==0 and p['scheduler_State_projection']=='EIP only','Bounded current preparation declarations')
    need(p['source_PCs']==13 and p['source_accesses']==10 and p['success_executed_source_bytes']==48 and p['separate_API_return_reads']==1,'Exact source counts distinct from typed API return model')
    need(build['entry_objects']==old['entry_objects'] and len(build['entry_objects'])==26,'Every accepted guest COFF object reused byte-for-byte')
    need(build['libraries']==old['libraries'] and len(build['libraries'])==2,'Both accepted FDIV libraries unchanged')
    for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
        for path,d in build[category].items():pin(path,d)
    for path,d in read(prep/'pins.json')['files'].items():pin(path,d)
    body=(prep/'heap_create_binding.inc').read_text();header=(prep/'heap_create.hpp').read_text();comp=(prep/'composition.cpp').read_text();obs=(prep/'observations.hpp').read_text();driver=(prep/'main_v2.inc').read_text()
    required=['mg::Context*const admitted_parent_','HANDLE owned_handle_','sizeof(HANDLE)==8','known_handle()','actual_destroy_calls()','successful_destroy_calls()','token_valid(unsigned value)']
    for text in required:need(text in header,'Explicit private full-HANDLE authority: '+text)
    for text in ['p!=known||owner!=known||binding!=known||admitted_binding!=known','if(authority&&authority!=this)authority->deny','parent!=admitted_parent_','admitted_parent_->first','old_create_before!=create_before||old_create_after!=create_after||old_destroy_before!=destroy_before||old_destroy_after!=destroy_after','owned_handle_=::HeapCreate(0,4096,0);','const auto actual=owned_handle_;','const auto ok=::HeapDestroy(actual);','if(ok){++destroy_successes_;owned_handle_=nullptr','if(control!=121)','witness[8]=GetLastError();','witness[10]=GetLastError();','const auto observed_error=GetLastError();','state.gpr.rax.dword=guest_result_;state.gpr.rsp.dword=admitted_frame_;state.gpr.rip.dword=api_ret;','if(access_count==8)published=true;','pc==api_ret&&access_count==8&&undefined_count==1&&api_returned','struct Cleanup','owner=nullptr;authority=nullptr;']:
        need(text in body,'Reviewed bounded host/source ownership action: '+text)
    start=body[body.index('[[noreturn]]void Binding::start'):]
    need('state.gpr.rip.dword=fragment;' in start and 'state.gpr.rsp.dword=' not in start and 'runtime.memory().store' not in start and 'runtime.cpu()=' not in body,'Explicit bootstrap has only StatePC projection and no host guest stack store')
    need(body.count('::HeapCreate(0,4096,0)')==1 and body.count('::HeapDestroy(actual)')==1,'Actual OS calls use fixed privately owned API arguments')
    need('guest_result_=token' in body and 'guest_result_=static_cast' not in body,'Opaque fixed guest DWORD is independent from native HANDLE')
    need('std::array<unsigned,18>composition_pages' in obs and 'memory().map({0x78035000}' in driver and 'hc::has_authority()' in comp,'One source-backed new raw RW page and typed private authority routing')
    oldprep=ROOT/'reports/m4-crt-heap-init/preparation-r2';differences={};unchanged=[]
    for original in oldprep.iterdir():
        if original.suffix not in ('.cpp','.hpp','.inc'):continue
        candidate=prep/original.name;need(candidate.exists(),'Every prior composition source carried forward')
        pin(original);pin(candidate)
        if original.read_bytes()==candidate.read_bytes():unchanged.append(original.name)
        else:differences[original.name]=''.join(difflib.unified_diff(original.read_text().splitlines(True),candidate.read_text().splitlines(True),fromfile='heap-init/'+original.name,tofile='heap-create/'+original.name))
    old_audit=ROOT/'tools/m4-crt-heap-init-review/audit.py';pin(old_audit)
    spec=importlib.util.spec_from_file_location('frozen_state_coff_audit',old_audit);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(llvm/'LLVM-C.dll');pin(llvm/'llvm-readobj.exe')
    api=A.LLVM(llvm/'LLVM-C.dll');records={}
    for kind,address,extent in (('fragment',0x7800183c,7),('provider',0x780039bf,77)):
        guest,host=oldprep/(kind+'-guest.ll'),oldprep/(kind+'-host.ll');pin(guest);pin(host)
        ga=A.layouts(guest,'sub_'+format(address,'x'),api);ha=A.layouts(host,'mw34_heap_init_'+kind+'_body',api)
        need(ga['pointer_bytes']==4 and ha['pointer_bytes']==8 and ga['types']==ha['types'] and ha['types']['struct.State']['size']==3504,'Unchanged complete named guest32/host64 State ABI')
        need('target datalayout = "'+A.HOST_LAYOUT+'"' in host.read_text(),'Actual unchanged AMD64 host ABI')
        records[kind]={'entry':address,'guarded_and_compiled_bytes':extent,'ABI':ha}
        for level in ('O0','O2'):
            obj=oldprep/(kind+'-'+level+'.obj');pin(obj)
            result=subprocess.run([str(llvm/'llvm-readobj.exe'),'--file-headers','--symbols','--unwind',str(obj)],capture_output=True,timeout=30)
            need(result.returncode==0,'Independent reused COFF reader zero exit');txt=result.stdout.decode();need('IMAGE_FILE_MACHINE_AMD64' in txt and 'mw34_heap_init_'+kind+'_body' in txt and 'RuntimeFunction' in txt,'Actual retained AMD64 symbol and exception unwind')
            q=out/(kind+'-'+level+'-coff.txt');q.write_bytes(result.stdout);pin(q)
    for path in (Path(__file__),Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/lifting/host_adapter.py'):pin(path)
    closure=verify_manifest(files)
    report={'passed':True,'scope':'Independent source/API ownership, full named State ABI, immutable 26-object COFF audit; no native execution or causal source-model oracle','preparation_path':str(prep/'report.json'),'preparation_sha256':sha_file(prep/'report.json'),'build_path':str(build_path),'build_sha256':sha_file(build_path),'reused_guest_objects':26,'new_guest_objects':0,'reused_heap_objects':4,'unchanged_FDIV_libraries':2,'compiled_guarded_heap_bytes':84,'executed_success_prefix_bytes':48,'source_PCs':13,'source_accesses':10,'separate_API_return_reads':1,'borrowed_pages':18,'prior_pages_preserved':17,'source_records':records,'unchanged_source_components':unchanged,'additive_source_differences':differences,'private_HANDLE_bytes':8,'guest_token':0x48450001,'API_incoming_and_restored_LastError_reads_actual':True,'undefined_AF_artifact_representative':0,'undefined_AF_sites':[0x780039bf,0x780039d6],'heap_initialized':False,'mode_selector_body_executed':False,'original_attach_executed':False,'original_executed':False,'native_executed':False,'full_causal_source_model_oracle':False,'physical_closure':closure}
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');pin(q);(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'report_sha256':sha_file(q),'pins_sha256':sha_file(out/'pins.json'),'physical_dependencies':len(files)}))
if __name__=='__main__':main(*sys.argv[1:])
