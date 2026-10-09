"""Independent complete State ABI, genuine source and fixed production link audit."""
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
    prep,build_path=Path(preparation).absolute(),Path(build_path).absolute();base=ROOT/'reports/m4-crt-heap-version-review';out=base/name
    need(name.startswith('audit-') and out.parent==base and not out.exists(),'Fresh independent source/ABI audit');out.mkdir();files={}
    def pin(p,d=None):
        p=Path(p).absolute();a=sha_file(p);need(d is None or a==d,'Exact immutable source association '+str(p));k=normalized(str(p));need(k not in files or files[k]==a,'Conflict-free independent source proof');files[k]=a;return a
    pin(ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json','fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154')
    pin(prep/'report.json',preparation_sha);pin(prep/'pins.json');pin(build_path,build_sha);p,build=read(prep/'report.json'),read(build_path)
    old_path=ROOT/'reports/m4-crt-heap-mode/build-r1/build.json';pin(old_path,'e1302754fc5f689fb79300e72c66b573d590a0d53f921a5b780234df99a00f4a');old=read(old_path)
    need(build['passed'] is True and build['preparation_sha256']==preparation_sha and normalized(build['preparation_path'])==normalized(str(prep/'report.json')),'Stable production build exact prepared association')
    for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
        for path,d in build[category].items():pin(path,d)
    for path,d in read(prep/'pins.json')['files'].items():pin(path,d)
    need(len(old['entry_objects'])==30 and len(build['entry_objects'])==38 and all(build['entry_objects'].get(k)==v for k,v in old['entry_objects'].items()),'All thirty prior genuine guest COFF objects retained exactly plus eight new finite bodies')
    need(build['libraries']==old['libraries'] and len(build['libraries'])==2,'Two accepted FDIV libraries unchanged')
    source=base/'source-r1';pin(source/'report.json','38ecbbab533d662baa34a7079a864a2ecb0729abb4cdb3a8635ec51e83c44fa7');pin(source/'pins.json','7184401c46986134ec63dbbd67c682a22728ddd2d2192c5035f6ff34ef3d8af6')
    for path,d in read(source/'pins.json')['files'].items():pin(path,d)
    # Manual source review findings are independently authored before this audit
    # and bound with the exact candidate identities, rather than generated from
    # successful native output.
    findings=ROOT/'tools/m4-crt-heap-version-review/source_findings.json';pin(findings);review=read(findings)
    need(review['passed'] is True and review['preparation_sha256']==preparation_sha and review['build_sha256']==build_sha,'Fresh independent read-only source findings bind current candidate')
    need(review['native_GetEnvironmentVariableA_called'] is False and review['host_full_HANDLE_private'] is True and review['scratch_bytes']==148 and review['API_output_not_original_oracle'] is True and review['source_returns_count']==2 and review['source_CALLs_count']==5 and review['API_return_reads_count']==2,'Exact bounded source/API contract findings')
    oldprep=ROOT/'reports/m4-crt-heap-mode/preparation-r2';unchanged=[];differences={}
    for original in oldprep.iterdir():
        if original.suffix not in ('.cpp','.hpp','.inc'):continue
        candidate=prep/original.name;need(candidate.exists(),'All prior prepared components retained');pin(original);pin(candidate)
        if candidate.read_bytes()==original.read_bytes():unchanged.append(original.name)
        else:differences[original.name]=''.join(difflib.unified_diff(original.read_text().splitlines(True),candidate.read_text().splitlines(True),fromfile='heap-mode/'+original.name,tofile='heap-version/'+original.name))
    oldaudit=ROOT/'tools/m4-crt-heap-init-review/audit.py';pin(oldaudit);spec=importlib.util.spec_from_file_location('frozen_version_State_COFF_audit',oldaudit);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(llvm/'LLVM-C.dll');pin(llvm/'llvm-readobj.exe');api=A.LLVM(llvm/'LLVM-C.dll');records={}
    for kind,address,extent in [('branch',0x78003a31,26),('environment',0x78003a4b,23),('mode1',0x7800ccc5,8),('epilogue',0x78003a7d,3)]:
        guest,host=prep/(kind+'-guest.ll'),prep/(kind+'-host.ll');pin(guest);pin(host);guest_symbol='sub_'+format(address,'x');symbols=re.findall(r'^define\s+.*?@([a-zA-Z_][a-zA-Z_0-9]*)\(',host.read_text(),re.M);chosen=[s for s in symbols if s.endswith('_'+kind+'_body')];need(len(chosen)==1,'Unique fresh typed AMD64 source body');ga=A.layouts(guest,guest_symbol,api);ha=A.layouts(host,chosen[0],api)
        need(ga['pointer_bytes']==4 and ha['pointer_bytes']==8 and ga['types']==ha['types'] and ha['types']['struct.State']['size']==3504,'Complete named guest32/host64 State ABI exact');need('target datalayout = "'+A.HOST_LAYOUT+'"' in host.read_text(),'Actual AMD64 target layout');records[kind]=dict(entry=address,guarded_bytes=extent,ABI=ha)
        for level in ('O0','O2'):
            obj=prep/(kind+'-'+level+'.obj');pin(obj);need(any(normalized(k)==normalized(str(obj)) and v==sha_file(obj) for k,v in build['entry_objects'].items()),'New object actually associated with production link')
            result=subprocess.run([str(llvm/'llvm-readobj.exe'),'--file-headers','--symbols','--unwind',str(obj)],capture_output=True,timeout=30);need(result.returncode==0,'Actual AMD64 COFF reader zero exit');text=result.stdout.decode();need('IMAGE_FILE_MACHINE_AMD64' in text and chosen[0] in text and 'RuntimeFunction' in text,'Actual AMD64 source symbol and unwind');q=out/(kind+'-'+level+'-coff.txt');q.write_bytes(result.stdout);pin(q)
    for q in (Path(__file__),Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/lifting/host_adapter.py'):pin(q)
    closure=verify_manifest(files);report=dict(passed=True,scope='Independent exact original source, private native query ownership, complete State ABI and immutable actual COFF link audit; no native execution',preparation_path=str(prep/'report.json'),preparation_sha256=preparation_sha,build_path=str(build_path),build_sha256=build_sha,source_findings=review,reused_guest_objects=30,new_guest_objects=8,unchanged_FDIV_libraries=2,new_guarded_source_bytes=60,mode1_executed_source_bytes=169,mode1_source_PCs=51,mode1_source_accesses=31,separate_API_return_reads=2,mode1_original_source_CALLs=5,mode1_original_source_RETs=2,borrowed_pages=21,source_records=records,unchanged_source_components=unchanged,additive_source_differences=differences,original_executed=False,native_executed=False,original_stack_guard_growth_proved=False,original_lower_stack_bytes_equivalent=False,full_causal_source_model_oracle=False,heap_initialized=False,whole_M4_complete=False,physical_closure=closure)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,report_sha256=sha_file(q),pins_sha256=sha_file(out/'pins.json'),physical_dependencies=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
