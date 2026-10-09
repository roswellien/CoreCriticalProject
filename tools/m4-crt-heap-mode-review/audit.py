"""Independent complete State ABI, immutable objects and bounded source review."""
import difflib, importlib.util, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from manifests import verify_manifest, normalized, unique_object
from capture_bundle import sha_file
def need(v,w):
    if not v: raise ValueError(w)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
def main(preparation,build_path,name):
    prep,build_path=Path(preparation).absolute(),Path(build_path).absolute()
    base=ROOT/'reports/m4-crt-heap-mode-review';out=base/name
    need(name.startswith('audit-') and out.parent==base and not out.exists(),'Fresh independent read-only audit');out.mkdir();files={}
    def pin(p,d=None):
        p=Path(p).absolute();actual=sha_file(p);need(d is None or d==actual,'Exact immutable source association '+str(p));k=normalized(str(p));need(k not in files or files[k]==actual,'Conflict-free source proof');files[k]=actual;return actual
    pin(ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json','e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326')
    pin(prep/'report.json','0791244218aa159177f3ea0ccd1b312085710b836af0e72da609e2f6870db3f3');pin(prep/'pins.json','58065e118f728e9ef40056b7aa8d974f53906e42c70c6e962148500a446c8765')
    pin(build_path);build=read(build_path);p=read(prep/'report.json');old_path=ROOT/'reports/m4-crt-heap-create/build-r1/build.json';pin(old_path,'28b96699f22ade5daaaab35fa15b63d16debbd3995eafd8e4e790bb57de7cd9e');old=read(old_path)
    need(build['passed'] is True and build['preparation_sha256']==sha_file(prep/'report.json') and normalized(build['preparation_path'])==normalized(str(prep/'report.json')),'Stable candidate exact preparation binding')
    need((p['new_guest_objects'],p['reused_guest_objects'],p['source_PCs'],p['source_accesses'],p['separate_API_return_reads'],p['borrowed_pages'],p['prior_pages_preserved'])==(4,26,39,24,1,20,18),'Exact bounded source/State/mapping counts')
    need((p['new_compiled_source_bytes'],p['success_executed_source_bytes'],p['source_identity_bytes'])==(86,132,2026),'Exact compiled/full identity versus dynamic byte extents')
    need(p['scheduler_store_count']==0 and p['scheduler_State_projection']=='EIP only' and p['Policy_and_TIB_unchanged'] is True,'Explicit State-only scheduling and declared lower research page')
    for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
        for path,d in build[category].items():pin(path,d)
    for path,d in read(prep/'pins.json')['files'].items():pin(path,d)
    need(len(build['entry_objects'])==30 and len(old['entry_objects'])==26 and all(build['entry_objects'].get(k)==v for k,v in old['entry_objects'].items()),'All twenty-six accepted guest COFF objects immutable plus four new objects')
    need(build['libraries']==old['libraries'] and len(build['libraries'])==2,'Two immutable FDIV libraries')
    body=(prep/'heap_mode_binding.inc').read_text();header=(prep/'heap_mode.hpp').read_text();comp=(prep/'composition.cpp').read_text();obs=(prep/'observations.hpp').read_text();driver=(prep/'main_v2.inc').read_text()
    for t in ('mg::Context*const admitted_parent_','HANDLE owned_handle_','sizeof(HANDLE)==8','admitted_probe_frame_','lower_initial_','lower_expected_','initial_lower_stack()'):
        need(t in header,'Reviewed immutable private source/owner input '+t)
    for t in ('p!=known||owner!=known||binding!=known||admitted_binding!=known','parent!=admitted_parent_','admitted_parent_->first','owned_handle_=::HeapCreate(0,4096,0);','const auto actual=owned_handle_;','const auto ok=::HeapDestroy(actual);','if(ok){++destroy_successes_;owned_handle_=nullptr','witness[8]=GetLastError();','witness[10]=GetLastError();','old_create_before!=create_before||old_create_after!=create_after||old_destroy_before!=destroy_before||old_destroy_after!=destroy_after','probe_returned=true;depth=3;event(8','query_reached=true;event(9','m4_runtime::FaultReason::unresolved_import','Only four exact XOR/TEST','word(offset(value,2))!=373','lower_expected_'):
        need(t in body,'Read-only source/API contract action '+t)
    start=body[body.index('[[noreturn]]void Binding::start'):]
    need('state.gpr.rip.dword=fragment;' in start and 'state.gpr.rsp.dword=' not in start and 'runtime.memory().store' not in start and 'runtime.cpu()=' not in body,'Only State PC projected by host scheduler')
    need(body.count('::HeapCreate(0,4096,0)')==1 and body.count('::HeapDestroy(actual)')==1 and '::GetVersionExA(' not in body,'One real heap API path and no query execution')
    need('std::array<unsigned,20>composition_pages' in obs and 'memory().map({0x78005000}' in driver and 'memory().map({0x20000000}' in driver and 'hm::has_authority()' in comp and 'returned(s,a,p)' in comp,'Explicit new mapping inputs and typed source probe RET routing')
    source=ROOT/'reports/m4-crt-heap-mode-review/source-r1';pin(source/'report.json','813350c744665fc61435d9d7cf1d1ba3fb8c8fe8dc8944b6c4538ec7b7488ce0');pin(source/'pins.json','dadcf394dc2e2ee99795f438818d21a40ddd6650b99620fe2b3a1992eab2d931')
    for path,d in read(source/'pins.json')['files'].items():pin(path,d)
    oldprep=ROOT/'reports/m4-crt-heap-create/preparation-r2';differences={};unchanged=[]
    for original in oldprep.iterdir():
        if original.suffix not in ('.cpp','.hpp','.inc'):continue
        candidate=prep/original.name;need(candidate.exists(),'Every earlier source component retained');pin(original);pin(candidate)
        if candidate.read_bytes()==original.read_bytes():unchanged.append(original.name)
        else:differences[original.name]=''.join(difflib.unified_diff(original.read_text().splitlines(True),candidate.read_text().splitlines(True),fromfile='heap-create/'+original.name,tofile='heap-mode/'+original.name))
    oldaudit=ROOT/'tools/m4-crt-heap-init-review/audit.py';pin(oldaudit);spec=importlib.util.spec_from_file_location('frozen_state_coff_audit',oldaudit);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(llvm/'LLVM-C.dll');pin(llvm/'llvm-readobj.exe');api=A.LLVM(llvm/'LLVM-C.dll');records={}
    for kind,address,extent in (('selector',0x78003a0c,37),('probe',0x780058b5,49)):
        guest,host=prep/(kind+'-guest.ll'),prep/(kind+'-host.ll');pin(guest);pin(host);ga=A.layouts(guest,'sub_'+format(address,'x'),api);ha=A.layouts(host,'mw34_heap_mode_'+kind+'_body',api)
        need(ga['pointer_bytes']==4 and ha['pointer_bytes']==8 and ga['types']==ha['types'] and ha['types']['struct.State']['size']==3504,'Complete named guest32/host64 State ABI identical');need('target datalayout = "'+A.HOST_LAYOUT+'"' in host.read_text(),'Actual AMD64 layout');records[kind]={'entry':address,'compiled_guarded_bytes':extent,'ABI':ha}
        for level in ('O0','O2'):
            obj=prep/(kind+'-'+level+'.obj');pin(obj);need(build['entry_objects'].get(str(obj))==sha_file(obj) or any(normalized(k)==normalized(str(obj)) and v==sha_file(obj) for k,v in build['entry_objects'].items()),'New object actual production link association')
            r=subprocess.run([str(llvm/'llvm-readobj.exe'),'--file-headers','--symbols','--unwind',str(obj)],capture_output=True,timeout=30);need(r.returncode==0,'Actual COFF reader zero exit');text=r.stdout.decode();need('IMAGE_FILE_MACHINE_AMD64' in text and 'mw34_heap_mode_'+kind+'_body' in text and 'RuntimeFunction' in text,'Actual AMD64 typed source symbol/unwind');q=out/(kind+'-'+level+'-coff.txt');q.write_bytes(r.stdout);pin(q)
    for path in (Path(__file__),Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/lifting/host_adapter.py'):pin(path)
    closure=verify_manifest(files);report={'passed':True,'scope':'Independent source/private ownership/complete State ABI and immutable COFF review; no native or causal model execution','preparation_path':str(prep/'report.json'),'preparation_sha256':sha_file(prep/'report.json'),'build_path':str(build_path),'build_sha256':sha_file(build_path),'reused_guest_objects':26,'new_guest_objects':4,'unchanged_FDIV_libraries':2,'new_compiled_guarded_bytes':86,'executed_success_bytes':132,'source_PCs':39,'source_accesses':24,'separate_API_return_reads':1,'borrowed_pages':20,'prior_pages_preserved':18,'source_records':records,'unchanged_source_components':unchanged,'additive_source_differences':differences,'undefined_AF_sites':[0x780039bf,0x780039d6,0x780058db,0x780058c5],'undefined_AF_artifact_representative':0,'original_executed':False,'native_executed':False,'GetVersionExA_executed':False,'original_stack_guard_growth_proved':False,'original_lower_stack_bytes_equivalent':False,'full_causal_source_model_oracle':False,'heap_mode_selected':False,'heap_initialized':False,'whole_M4_complete':False,'physical_closure':closure}
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');pin(q);(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'report_sha256':sha_file(q),'pins_sha256':sha_file(out/'pins.json'),'physical_dependencies':len(files)}))
if __name__=='__main__':main(*sys.argv[1:])
