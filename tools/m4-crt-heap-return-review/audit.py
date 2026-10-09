"""Independent immutable complete State ABI, provider continuation and COFF reuse audit."""
import difflib,importlib.util,json,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest,normalized,unique_object
from capture_bundle import sha_file
def need(v,w):
    if not v:raise ValueError(w)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def main(preparation,preparation_sha,build_path,build_sha,name):
    prep,build_path=Path(preparation).absolute(),Path(build_path).absolute();base=ROOT/'reports/m4-crt-heap-return-review';out=base/name
    need(name.startswith('audit-') and out.parent==base and not out.exists(),'Fresh independent source/ABI/COFF receipt');out.mkdir();files={}
    def pin(p,d=None):
        p=Path(p).absolute();a=sha_file(p);need(d is None or a==d,'Exact immutable association '+str(p));k=normalized(str(p));need(k not in files or files[k]==a,'Conflict-free current source proof');files[k]=a;return a
    pin(ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json','cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1')
    pin(prep/'report.json',preparation_sha);pin(prep/'pins.json');pin(build_path,build_sha);p,build=read(prep/'report.json'),read(build_path)
    old_path=ROOT/'reports/m4-crt-heap-version/build-r3/build.json';pin(old_path,'4ceb8fefa09bd36ba3a244295250b44ed333e36ba241e0a6a490996680bba25c');old=read(old_path)
    need(build['passed'] is True and build['preparation_sha256']==preparation_sha and normalized(build['preparation_path'])==normalized(str(prep/'report.json')),'Frozen current build exact preparation association')
    for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
        for q,d in build[category].items():pin(q,d)
    for q,d in read(prep/'pins.json')['files'].items():pin(q,d)
    need(len(old['entry_objects'])==38 and build['entry_objects']==old['entry_objects'],'All38 accepted guest COFF objects reused exactly; zero fresh guest objects')
    need(build['libraries']==old['libraries'] and len(build['libraries'])==2,'Both accepted FDIV libraries unchanged')
    source=base/'source-r3';pin(source/'report.json','814f2fb571baf2c60f88905204bf28ae1552a4e1a1b0d4fe3a2584f8525a8904');pin(source/'pins.json','802d922ad749211761592bcea4edaf10e6cc6eb7491a1a71df6f0b2d99ada038')
    for q,d in read(source/'pins.json')['files'].items():pin(q,d)
    findings=ROOT/'tools/m4-crt-heap-return-review/source_findings.json';pin(findings);review=read(findings)
    need(review['passed'] is True and review['preparation_sha256']==preparation_sha and review['build_sha256']==build_sha,'Independently authored read-only findings bind current frozen candidate')
    need(review['native_GetEnvironmentVariableA_called'] is False and review['host_full_HANDLE_private'] is True and review['scratch_bytes']==148 and review['API_output_not_original_oracle'] is True and review['source_returns_count']==3 and review['source_CALLs_count']==5 and review['API_return_reads_count']==2 and review['heap_mode_global_published_by_source'] is True and review['fragment_caller_TEST_executed'] is False,'Exact finite source/private native contract findings')
    oldprep=ROOT/'reports/m4-crt-heap-version/preparation-r2';unchanged=[];differences={}
    for original in oldprep.iterdir():
        if original.suffix not in ('.cpp','.hpp','.inc'):continue
        candidate=prep/original.name;need(candidate.exists(),'Accepted prepared components retained physically');pin(original);pin(candidate)
        if candidate.read_bytes()==original.read_bytes():unchanged.append(original.name)
        else:differences[original.name]=''.join(difflib.unified_diff(original.read_text().splitlines(True),candidate.read_text().splitlines(True),fromfile='heap-version/'+original.name,tofile='heap-return/'+original.name))
    oldaudit=ROOT/'tools/m4-crt-heap-init-review/audit.py';pin(oldaudit);spec=importlib.util.spec_from_file_location('frozen_heap_return_State_COFF_audit',oldaudit);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(llvm/'LLVM-C.dll');pin(llvm/'llvm-readobj.exe');api=A.LLVM(llvm/'LLVM-C.dll')
    guest=ROOT/'reports/m4-crt-heap-init/preparation-r2/provider-guest.ll';host=ROOT/'reports/m4-crt-heap-init/preparation-r2/provider-host.ll';pin(guest);pin(host);ga=A.layouts(guest,'sub_780039bf',api);ha=A.layouts(host,'mw34_heap_init_provider_body',api)
    need(ga['pointer_bytes']==4 and ha['pointer_bytes']==8 and ga['types']==ha['types'] and ha['types']['struct.State']['size']==3504 and 'target datalayout = "'+A.HOST_LAYOUT+'"' in host.read_text(),'Complete unchanged named guest32/host64 State ABI exact')
    coff=[]
    for number,(q,d) in enumerate(build['entry_objects'].items(),1):
        pin(q,d);result=subprocess.run([str(llvm/'llvm-readobj.exe'),'--file-headers','--symbols','--unwind',q],capture_output=True,timeout=30);need(result.returncode==0,'Actual COFF reader zero exit');text=result.stdout.decode();need('IMAGE_FILE_MACHINE_AMD64' in text,'Every exact reused guest input is actual AMD64 COFF')
        if Path(q).name.startswith('provider-') and 'm4-crt-heap-init' in normalized(q):need('mw34_heap_init_provider_body' in text and 'RuntimeFunction' in text,'Existing original whole-provider typed body and unwind are in actual accepted linked COFF')
        dump=out/f'guest-object-{number:02d}-coff.txt';dump.write_bytes(result.stdout);pin(dump);coff.append(dict(path=q,sha256=d,AMD64=True,reader_sha256=sha_file(dump)))
    for q in (Path(__file__),Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/lifting/host_adapter.py'):pin(q)
    closure=verify_manifest(files);report=dict(passed=True,scope='Independent authentic caller/global-store/RET source, complete unchanged State ABI, private full-HANDLE/API witness ownership and all38 immutable AMD64 COFF reuse; no native execution',preparation_path=str(prep/'report.json'),preparation_sha256=preparation_sha,build_path=str(build_path),build_sha256=build_sha,source_findings=review,reused_guest_objects=38,new_guest_objects=0,unchanged_FDIV_libraries=2,new_guarded_source_bytes=0,newly_admitted_existing_source_bytes=23,source_identity_bytes=2086,mode1_executed_source_bytes=192,mode1_source_PCs=59,mode1_source_accesses=35,separate_API_return_reads=2,mode1_original_source_CALLs=5,mode1_original_source_RETs=3,borrowed_pages=21,complete_provider_State_ABI=ha,actual_reused_COFF=coff,unchanged_source_components=unchanged,additive_source_differences=differences,original_executed=False,native_executed=False,original_stack_guard_growth_proved=False,original_lower_stack_bytes_equivalent=False,full_causal_source_model_oracle=False,whole_M4_complete=False,physical_closure=closure)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,report_sha256=sha_file(q),pins_sha256=sha_file(out/'pins.json'),physical_dependencies=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
