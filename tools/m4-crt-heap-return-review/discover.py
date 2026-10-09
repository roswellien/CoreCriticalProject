"""Independently recover the authentic mode-1 heap initializer continuation/RET."""
import hashlib,json,ntpath,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASELINE_SHA='cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'
PCS=[0x780039e8,0x780039eb,0x780039f0,0x780039f6,0x780039f9,0x78003a08,0x78003a0a,0x78003a0b]
def need(v,w):
    if not v:raise ValueError(w)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def key(p):return ntpath.normcase(ntpath.normpath(str(Path(p).absolute())))
def cmp_flags(left,right):
    value=(left-right)&0xffffffff
    return int(left<right)+int(value==0)*0x40+int((value&255).bit_count()%2==0)*4+int(bool(value&0x80000000))*0x80+int(bool((left^right^value)&0x10))*0x10+int(bool(((left^right)&(left^value))&0x80000000))*0x800
def main(name):
    base=ROOT/'reports/m4-crt-heap-return-review';out=base/name
    need(name.startswith('source-') and out.parent==base and not out.exists(),'Fresh independent original source contract');out.mkdir(parents=True)
    provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';baseline=ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json';old=ROOT/'reports/m4-crt-heap-version-review/source-r1/report.json';decode=ROOT/'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'
    need(sha(provider)==PROVIDER_SHA and sha(baseline)==BASELINE_SHA and sha(old)=='38ecbbab533d662baa34a7079a864a2ecb0729abb4cdb3a8635ec51e83c44fa7','Exact frozen accepted original source/version-query gate')
    pe=PEImage(provider.read_bytes())
    def source(a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    spans={}
    for label,address,count,expected in [('caller',0x780039e8,19,'83f803a3045003780f84ca93000083f802750d'),('success',0x78003a08,4,'6a0158c3')]:
        raw=source(address,count);need(raw==bytes.fromhex(expected),'Exact independent original continuation '+label);p=out/(label+'.bin');p.write_bytes(raw);spans[label]=dict(entry=address,end=address+count,bytes=count,sha256=sha(p))
    provider_ir=ROOT/'reports/m4-crt-heap-init/preparation-r2/provider-host.ll';oldprep=ROOT/'reports/m4-crt-heap-version/preparation-r2/report.json';oldbuild=ROOT/'reports/m4-crt-heap-version/build-r3/build.json';guarded=source(0x780039bf,77)
    need(hashlib.sha256(guarded).hexdigest()=='72922b45de858dc84ab5a08a8626acf0fca8487bd1e1cba955a3c0afba30e6ba','Both continuation spans already inside immutable full77-byte provider guard')
    need(guarded[0x39e8-0x39bf:0x39fb-0x39bf]==source(0x780039e8,19) and guarded[0x3a08-0x39bf:]==source(0x78003a08,4),'Exact existing provider coverage, not additional guarded source')
    ir=provider_ir.read_text();need('define ptr @mw34_heap_init_provider_body' in ir and 'tail call ptr @__remill_function_return' in ir and 'declare ptr @sub_78003a0c' in ir and 'declare ptr @sub_78003aad' in ir,'Immutable whole-provider typed IR already contains caller branches and authentic initializer RET')
    build=json.loads(oldbuild.read_text());need(len(build['entry_objects'])==38 and len(build['libraries'])==2 and json.loads(oldprep.read_text())['source_identity_bytes']==2086,'Accepted existing 38 COFF/two library/source closure')
    oldobjects={key(ROOT/('reports/m4-crt-heap-init/preparation-r2/provider-'+level+'.obj')):sha(ROOT/('reports/m4-crt-heap-init/preparation-r2/provider-'+level+'.obj')) for level in ('O0','O2')}
    linked_objects={key(Path(p)):d for p,d in build['entry_objects'].items()};need(all(linked_objects.get(p)==d for p,d in oldobjects.items()),'Both existing provider COFF objects are actual accepted linked inputs')
    rows={}
    for line in decode.read_text().splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
        if m and int(m[1],16) in PCS:
            address=int(m[1],16);raw=bytes.fromhex(m[2]);need(raw==source(address,len(raw)),'Exact original decoded source');rows[address]=dict(pc=address,bytes=len(raw),bytes_hex=raw.hex(),opcode=m[3],operands=m[4])
    need(set(rows)==set(PCS) and sum(rows[a]['bytes'] for a in PCS)==23,'Eight authentic continuation PCs and 23 bytes')
    raw_global=struct.unpack('<I',source(0x78035004,4))[0]
    alternatives=[]
    for value in (0,1,2,3,0xffffffff):
        order=PCS[:3]
        if value!=3:order+=PCS[3:5]
        if value not in (2,3):order+=PCS[5:]
        alternatives.append(dict(selector_result=value,PC_order=order,global_store=value,frontier='unadmitted mode3 cold branch7800CDC0' if value==3 else 'unadmitted mode2 source780039FB before CALL78003AAD' if value==2 else 'initializer RET78003A0B to fragment78001843',defined_flags=cmp_flags(value,3 if value==3 else 2),formula_only=True,native_result_injected=False))
    report=dict(passed=True,scope='Independent authentic mode-1 initializer caller/global-store/RET source contract; static recovery only',provider_sha256=PROVIDER_SHA,baseline_acceptance_sha256=BASELINE_SHA,spans=spans,decoded_instructions=[rows[p] for p in PCS],new_guarded_source_bytes=0,newly_admitted_existing_source_bytes=23,combined_source_identity_bytes=2086,existing_provider_span=dict(entry=0x780039bf,bytes=77,sha256=hashlib.sha256(guarded).hexdigest(),unchanged_COFF_objects=oldobjects),mode1_new_source_PCs=8,mode1_combined_source_PCs=59,mode1_new_source_accesses=4,mode1_combined_source_accesses=35,mode1_new_executed_source_bytes=23,mode1_combined_executed_source_bytes=192,mode1_original_source_CALLs=5,mode1_original_source_RETs=3,separate_API_return_reads=2,borrowed_pages=21,new_compiled_objects_expected=0,reused_guest_objects_expected=38,unchanged_FDIV_libraries_expected=2,mode_global=dict(address=0x78035004,raw_file_initial_DWORD=raw_global,source_PC=0x780039eb,successful_actual_selector_result=1),source_access_order=[dict(pc=0x780039eb,address=0x78035004,value=1,width=4,write=1),dict(pc=0x78003a08,address=0x20001854,value=1,width=4,write=1),dict(pc=0x78003a0a,address=0x20001854,value=1,width=4,write=0),dict(pc=0x78003a0b,address=0x20001858,value=0x78001843,width=4,write=0)],genuine_initializer_return_contract=dict(source_PC=0x78003a0b,frame=0x20001858,genuine_return=0x78001843,final_EAX=1,final_ESP=0x2000185c,final_EIP=0x78001843,carried_original_other_GPRs=True,carried_State_bytes=3504,carried_FX_bytes=512,RuntimeCPU_carried=True,final_defined_arithmetic_flags=cmp_flags(1,2),original_fragment_TEST1843_executed=False),private_native_contract=dict(full_native_HANDLE_live_until_initializer_RET=True,same_actual_HeapDestroy_cleanup_after_finite_source_exit=True,full148_byte_query_witness_preserved=True,actual_output_DWORD_commits=37,separate_API_return_reads=2,native_version_results_not_injected=True,alternate_actual_environment_import_bounded_before_API=True),selector_formula_controls=alternatives,mode1_source_execution_credit=False,initializer_source_return_proved=False,native_executed=False,original_executed=False,ordinary_game_launched=False,full_heap_initialization_complete=False,whole_M4_complete=False)
    files={key(p):sha(p) for p in [Path(__file__),ROOT/'tools/analysis/pe.py',provider,baseline,old,decode,provider_ir,oldprep,oldbuild,*map(Path,oldobjects),*out.iterdir()] if p.is_file()};p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');files[key(p)]=sha(p);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');need(all(sha(p)==h for p,h in files.items()),'Exact original source physical closure');print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'),source_PCs=59,source_accesses=35,new_guarded_source_bytes=0)))
if __name__=='__main__':main(sys.argv[1])
