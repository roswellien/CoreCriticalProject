"""Independent exact-source contract for the version bridge and selector continuations."""
import hashlib,json,ntpath,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASELINE_SHA='fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154'
BRANCH=[0x78003a31,0x78003a33,0x78003a35,0x78003a3c,0x78003a3e,0x78003a45]
COLD=[0x7800ccc5,0x7800ccc7,0x7800ccc8,0x78003a7d,0x78003a7e,0x78003a7f]
ENV=[0x78003a4b,0x78003a51,0x78003a56,0x78003a57,0x78003a5c]
def need(v,w):
    if not v:raise ValueError(w)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def key(p):return ntpath.normcase(ntpath.normpath(str(Path(p).absolute())))
def logic_flags(value):
    return int(value==0)*0x40+int((value&255).bit_count()%2==0)*4+int(bool(value&0x80000000))*0x80
def cmp_flags(left,right):
    value=(left-right)&0xffffffff
    return int(left<right)+int(value==0)*0x40+int((value&255).bit_count()%2==0)*4+int(bool(value&0x80000000))*0x80+int(bool((left^right^value)&0x10))*0x10+int(bool(((left^right)&(left^value))&0x80000000))*0x800
def main(name):
    base=ROOT/'reports/m4-crt-heap-version-review';out=base/name
    need(name.startswith('source-') and out.parent==base and not out.exists(),'Fresh independent exact-source contract');out.mkdir()
    provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';baseline=ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json';old=ROOT/'reports/m4-crt-heap-mode-review/source-r1/report.json';decode=ROOT/'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'
    need(sha(provider)==PROVIDER_SHA and sha(baseline)==BASELINE_SHA,'Exact original provider and accepted frozen stack-probe gate')
    need(sha(old)=='813350c744665fc61435d9d7cf1d1ba3fb8c8fe8dc8944b6c4538ec7b7488ce0','Immutable independent prior source contract')
    pe=PEImage(provider.read_bytes())
    def source(a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    spans={}
    for label,address,count,expected in [('branch',0x78003a31,26,'85c0741683bd78ffffff02750d83bd6cffffff050f837a920000'),('environment',0x78003a4b,23,'8d85d4edffff68901000005068b8e30278ff159ce00278'),('cold',0x7800ccc5,8,'6a0158e9b06dffff'),('epilogue',0x78003a7d,3,'5bc9c3'),('cold-RX-page',0x7800c000,4096,None)]:
        raw=source(address,count);need(expected is None or raw==bytes.fromhex(expected),'Exact independent new original bytes '+label);p=out/(label+'.bin');p.write_bytes(raw);spans[label]=dict(entry=address,end=address+count,bytes=count,sha256=sha(p))
    imports={}
    for slot,name,hint in [(0x2e0a0,'GetVersionExA',373),(0x2e09c,'GetEnvironmentVariableA',273)]:
        matches=[dict(library=d['library'],**s) for d in pe.imports() for s in d['symbols'] if s['iat_rva']==slot]
        need(len(matches)==1 and matches[0]['library']=='KERNEL32.dll' and matches[0]['name']==name,'Exact independent named import')
        if name=='GetVersionExA':need(matches[0]['hint']==hint,'Previously admitted unique query hint')
        imports[name]=dict(**matches[0],raw_target=struct.unpack('<I',source(0x78000000+slot,4))[0])
    rows={};pcset=set(BRANCH+COLD+ENV)
    for line in decode.read_text().splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
        if m and int(m[1],16) in pcset:
            address=int(m[1],16);raw=bytes.fromhex(m[2]);need(raw==source(address,len(raw)),'Exact independent original decode');rows[address]=dict(pc=address,bytes=len(raw),bytes_hex=raw.hex(),opcode=m[3],operands=m[4])
    need(set(rows)==pcset and len(pcset)==17,'Exact finite discontiguous new source inventory')
    actual_mode_access=[(0x78003a35,0x200017c8,'native scratch dwPlatformId',0),(0x78003a3e,0x200017bc,'native scratch dwMajorVersion',0),(0x7800ccc5,0x2000061c,1,1),(0x7800ccc7,0x2000061c,1,0),(0x78003a7d,0x20000620,'carried original EBX',0),(0x78003a7e,0x20001850,'carried original EBP',0),(0x78003a7f,0x20001854,0x780039e8,0)]
    alternatives=[]
    for result,platform,major,label in [(1,2,6,'actual modern NT-like response'),(0,2,6,'BOOL zero'),(1,1,6,'other platform'),(1,2,4,'older major'),(1,2,5,'major threshold exactly5'),(1,2,0xffffffff,'unsigned large major')]:
        mode1=result!=0 and platform==2 and major>=5
        order=BRANCH[:2]
        if result:
            order+=BRANCH[2:4]
            if platform==2:order+=BRANCH[4:]
        order+=COLD if mode1 else ENV
        alternatives.append(dict(label=label,native_BOOL_DWORD=result,platform=platform,major=major,conditional_frontier='genuine selector RET to caller39E8' if mode1 else 'genuine GetEnvironmentVariableA import CALL3A5C',PC_order=order,source_TEST_AF_representative=0,final_defined_flags=cmp_flags(major,5) if mode1 else logic_flags(result) if not result else cmp_flags(platform,2) if platform!=2 else cmp_flags(major,5),native_query_invented=False,formula_only=True))
    report=dict(passed=True,scope='Independent original source contract for private native GetVersionExA bridge and finite witness-dependent selector continuation; static recovery, no native execution',provider_sha256=PROVIDER_SHA,baseline_acceptance_sha256=BASELINE_SHA,spans=spans,imports=imports,decoded_instructions=[rows[p] for p in BRANCH+COLD+ENV],new_guarded_source_bytes=60,prior_guarded_source_bytes=86,combined_source_identity_bytes=2086,mode1_new_executed_source_bytes=37,mode1_combined_executed_source_bytes=169,mode1_new_source_PCs=12,mode1_combined_source_PCs=51,mode1_new_source_accesses=7,mode1_combined_source_accesses=31,mode1_original_source_CALLs=5,mode1_original_source_RETs=2,separate_API_return_reads=2,API_return_contract=dict(frame=0x20000618,genuine_return=0x78003a31,argument_word_address=0x2000061c,argument_pointer=0x200017b8,structure_bytes=148,std_call_pop_bytes=8,EIP=0x78003a31,ESP=0x20000620,EAX='actual native BOOL low DWORD',all_other_State_and_FX_carried=True),private_query_contract=dict(scratch_bytes=148,initial_bytes='exact checked guest bytes at genuine source pointer',result_bytes='all actual native scratch bytes after API, including BOOL0 without assuming unchanged output',guest_copy_origin='native API witness, no original machine outcome equivalence',preflight_read_and_write='full extent before native invocation',copy_commits='finite observed per-DWORD committed API-output ledger independent from original source accesses',LastError='actual caller/API/restored reads',API_identity='loaded named export/owner/physical module identity before and after',manifest_scope='returned version depends on calling worker application manifest and compatibility context'),mode1_new_source_access_order=[dict(pc=p,address=a,value=v,width=4,write=w) for p,a,v,w in actual_mode_access],response_formula_controls=alternatives,mapping_contract=dict(prior_mappings=20,new_raw_RX_page=0x7800c000,total_mappings=21,lower_stack_page='declared research input preserved from accepted gate',Policy_stack_low=0x20001000,Policy_and_TIB_unchanged=True,original_guard_growth_equivalence=False),defined_flags=dict(new_TEST_site=0x78003a31,undefined_AF_representative=0,universal_AF_equivalence=False,mode1_final_flags='literal CMP native major,5; PUSH/POP/JMP/POP/LEAVE/RET preserve arithmetic flags'),genuine_mode_return=dict(EIP=0x780039e8,ESP=0x20001858,EAX=1,EBP='genuine source LEAVE restores carried original EBP',EBX='genuine source POP restores carried original EBX',guest_global_mode_store_executed=False),expected_overlap=dict(native_output_start=0x200017b8,native_output_end=0x2000184c,overwritten_prior_saved_ECX=0x20001848,probe_return_word=0x2000184c,outside_output=True,selector_saved_EBP=0x20001850,outside_output_EBP=True,selector_return=0x20001854,outside_output_return=True),new_compiled_objects_expected=8,reused_guest_objects_expected=30,source_mode_selector_RET_executed=False,native_query_executed=False,mode_result_produced=False,heap_initialized=False,original_executed=False,native_executed=False,whole_M4_complete=False)
    files={key(p):sha(p) for p in [Path(__file__),ROOT/'tools/analysis/pe.py',provider,baseline,old,decode,*out.iterdir()] if p.is_file()};p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');files[key(p)]=sha(p);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');need(all(sha(p)==h for p,h in files.items()),'Exact independent static physical closure');print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'),new_guarded_source_bytes=60,mode1_source_PCs=51,mode1_accesses=31)))
if __name__=='__main__':main(sys.argv[1])
