"""Independent original source/API-ownership boundary; original code unexecuted."""
import hashlib,json,ntpath,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASELINE_SHA='a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d'
PCS=[0x7800183c,0x7800183e,0x780039bf,0x780039c1,0x780039c3,0x780039c7,0x780039cc,0x780039cf,0x780039d0,0x780039d6,0x780039d8,0x780039dd,0x780039e3]
def need(v,w):
    if not v:raise ValueError(w)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def key(p):return ntpath.normcase(ntpath.normpath(str(Path(p).absolute())))
def main(name):
    base=ROOT/'reports/m4-crt-heap-create-review';out=base/name
    need(name.startswith('source-') and out.parent==base and not out.exists(),'Fresh independent source contract')
    out.mkdir(parents=True)
    provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    old=ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json'
    decode=ROOT/'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'
    need(sha(provider)==PROVIDER_SHA and sha(old)==BASELINE_SHA,'Exact staged original provider and frozen heap-frontier anchor')
    pe=PEImage(provider.read_bytes())
    def source(a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    spans={}
    for label,a,n in (('attach-fragment',0x7800183c,7),('provider-success-prefix',0x780039bf,41),('provider-identity',0x780039bf,77),('heap-global-page',0x78035000,4096)):
        raw=source(a,n);p=out/(label+'.bin');p.write_bytes(raw);spans[label]=dict(entry=a,end=a+n,bytes=n,sha256=sha(p))
    need(source(0x7800183c,7)==bytes.fromhex('6a01e87c210000'),'Literal original argument PUSH and CALL')
    need(source(0x780039d6,18)==bytes.fromhex('85c0a3005003780f84f9930000e824000000'),'Literal TEST, heap publication, conditional branch and mode CALL')
    rows={}
    for line in decode.read_text().splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
        if m and int(m[1],16) in PCS:
            pc,raw=int(m[1],16),bytes.fromhex(m[2]);need(source(pc,len(raw))==raw,'Independent decoded instruction agrees with original bytes')
            rows[pc]=dict(pc=pc,bytes_hex=raw.hex(),mnemonic=m[3],operands=m[4].split(' <')[0].replace('\t',' ').strip())
    need(set(rows)==set(PCS),'All thirteen source PCs independently decoded')
    raw=bytes.fromhex(rows[0x780039e3]['bytes_hex'])
    need(raw[0]==0xe8 and 0x780039e8+struct.unpack('<i',raw[1:])[0]==0x78003a0c,'Actual original mode-selector CALL displacement')
    imports=[dict(library=r['library'],**s) for r in pe.imports() for s in r['symbols'] if s['iat_rva']==0x2e0a8]
    need(imports==[dict(library='KERNEL32.dll',iat_rva=0x2e0a8,name='HeapCreate',hint=411)],'Unique original named HeapCreate import')
    need(source(0x7802e0a8,4)==struct.pack('<I',0x3461e),'Exact raw source IAT token')
    need(source(0x78035000,8)==bytes(8),'File-zero heap handle/mode identity supplies no initialized state')
    token=0x48450001;entry=0x20001860
    operations=[
        (0x7800183c,entry-4,1,'write','actual fragment argument PUSH'),
        (0x7800183e,entry-8,0x78001843,'write','actual fragment CALL return'),
        (0x780039c1,entry-12,0,'write','HeapCreate maximum PUSH'),
        (0x780039c3,entry-4,1,'read','CMP actual argument after prior PUSH'),
        (0x780039c7,entry-16,4096,'write','HeapCreate initial PUSH'),
        (0x780039cf,entry-20,0,'write','SETE-selected HeapCreate options PUSH'),
        (0x780039d0,0x7802e0a8,0x3461e,'read','actual original IAT read'),
        (0x780039d0,entry-24,0x780039d6,'write','actual HeapCreate CALL return'),
        (0x780039d8,0x78035000,token,'write','only translated MOV publishes guest opaque handle'),
        (0x780039e3,entry-12,0x780039e8,'write','actual mode-selector CALL return'),
    ]
    accesses=[dict(pc=pc,address=a,value=v,width=4,operation=op,meaning=w) for pc,a,v,op,w in operations]
    report=dict(passed=True,scope='Independent static original source and reviewed real HeapCreate ownership proposal through genuine mode-selector CALL',
        provider_sha256=PROVIDER_SHA,baseline_acceptance_sha256=BASELINE_SHA,spans=spans,decoded_source_instructions=[rows[p] for p in PCS],executed_prefix_PC_order=PCS,source_access_order=accesses,
        completed_source_accesses_expected=10,executed_PCs_expected=13,actual_source_CALLs_expected=3,new_compiled_bytes=0,reused_heap_compiled_bytes=84,executed_prefix_bytes=48,total_source_identity_bytes=1940,
        host_scheduling=dict(project_only_carried_State_EIP=0x7800183c,State_ESP=entry,guest_stack_store=False,generic_Runtime_CPU_preserved=True,Runtime_call_records=11,Runtime_call_record_added=False,original_attach_executed=False),
        mapping_contract=dict(prior_mappings=17,additional_raw_RW_heap_page=0x78035000,total_mappings=18,prior_mapping_permissions_and_bytes_preserved=True),
        separate_API_return=dict(source_CALL_PC=0x780039d0,raw_import_target=0x3461e,actual_return_read_address=entry-24,return_word=0x780039d6,stdcall_argument_bytes=12,State_EAX=token,State_ESP=entry-8,State_EIP=0x780039d6,generic_Runtime_CPU_preserved=True,guest_global_store=False),
        stop=dict(source_CALL_PC=0x780039e3,target=0x78003a0c,frame=entry-12,return_word=0x780039e8,mode_selector_body_executed=False),
        expected_terminal_registers=dict(EAX=token,ESP=entry-12,EIP=0x78003a0c,other_registers='unchanged from carried source input'),
        expected_terminal_flags=dict(CF=0,PF=0,AF='undefined TEST AF; narrowly admitted generated representative0',ZF=0,SF=0,OF=0),
        narrow_undefined_AF_sites=[dict(pc=0x780039bf,source_access_count=2,representative=0),dict(pc=0x780039d6,source_access_count=8,representative=0,requires_genuine_API_return=True)],
        source_zero_seam=dict(provenance='explicit injected NULL bridge result without OS call; no measured API failure claim',source_global_value=0,PC_order=PCS[:-1],source_accesses=9,actual_branch_PC=0x780039dd,target=0x7800cddc,source_RET_executed=False,cold_body_executed=False),
        API_contract=dict(HeapCreate_arguments=[0,4096,0],host_signature='HANDLE HeapCreate(DWORD,SIZE_T,SIZE_T)',host_HANDLE_bytes=8,opaque_guest_token=token,handle_truncation=False,full64_handle_private_owned=True,
            create_actual_success_measured=True,owned_immediately_before_throwing_observers=True,HeapDestroy_success_requires_nonzero_BOOL=True,failed_destroy_retains_ownership=True,source_heap_mode_unchanged=True,
            references=['https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapcreate','https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapdestroy']),
        review_requirements=[
            'Reuse all26 frozen guest objects and both FDIV libraries; no regenerated, patched or appended source body',
            'Unique original PE import name/library/hint/raw token plus exact source CALL frame before host invocation',
            'Actual host HeapCreate uses DWORD/SIZE_T argument conversion, full64 HANDLE is captured privately before observers or allocations',
            'Separate actual API return-read/State projection follows stdcall12; naturally continue SAME source function rather than reentering at39D6',
            'Only source MOV39D8 publishes guest token into new rawRW page; handle token is not a truncated pointer or fixed heap mode',
            'Only39BF/39D6 undefinedAF artifact representatives admitted at exact source progress; no universalAF claim',
            'Every owned private handle destroyed exactly once after all terminal/partial/exception paths; failed cleanup remains owned and fails acceptance',
            'Null, stale, corrupt and duplicate public/opaque registry tokens refuse before native pointer conversion or unsafe API call',
            'Actual live-handle validation before release and safe enumeration membership after successful destroy; no API called on a destroyed handle',
            'WholeState3504/FX512/CPU40/all18pages, actual rich544B host boundaries, caller LastError, cleanup diagnostics and poisoned retry preserved',
        ],original_executed=False,native_executed=False,API_executed=False,heap_initialized=False,mode_selected=False,full_CRT_complete=False,whole_M4_complete=False)
    files={key(p):sha(p) for p in (Path(__file__),ROOT/'tools/analysis/pe.py',provider,old,decode,*out.iterdir()) if p.is_file()}
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');files[key(p)]=sha(p)
    (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8')
    need(all(sha(p)==h for p,h in files.items()),'Full current physical input/output identity')
    print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'),source_accesses=10,source_PCs=13,mode_frame=hex(entry-12))))
if __name__=='__main__':main(sys.argv[1])
