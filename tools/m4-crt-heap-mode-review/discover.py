"""Independent static selector/probe contract and explicit fresh stack-input domain."""
import hashlib,json,ntpath,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASELINE_SHA='e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326'
SELECTOR=[0x78003a0c,0x78003a0d,0x78003a0f,0x78003a14,0x78003a19,0x78003a1f,0x78003a20,0x78003a21,0x78003a2b]
PROBE=[0x780058b5,0x780058b6,0x780058bb,0x780058bf,0x780058d0,0x780058d6,0x780058db,0x780058dd,0x780058e2,0x780058c1,0x780058c3,0x780058c5,0x780058c7,0x780058c9,0x780058cb,0x780058ce,0x780058cf]
PCS=SELECTOR[:4]+PROBE+SELECTOR[4:]
def need(v,w):
    if not v:raise ValueError(w)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def key(p):return ntpath.normcase(ntpath.normpath(str(Path(p).absolute())))
def logic_flags(left,right):
    result=(left&right)&0xffffffff
    return int(result==0)*0x40+int((result&255).bit_count()%2==0)*4+int(bool(result&0x80000000))*0x80
def main(name):
    base=ROOT/'reports/m4-crt-heap-mode-review';out=base/name
    need(name.startswith('source-') and out.parent==base and not out.exists(),'Fresh static selector/probe review');out.mkdir(parents=True)
    provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';baseline=ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json';decode=ROOT/'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'
    need(sha(provider)==PROVIDER_SHA and sha(baseline)==BASELINE_SHA,'Exact original provider and frozen heap-create acceptance')
    pe=PEImage(provider.read_bytes())
    def source(a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    need(source(0x78003a0c,37)==bytes.fromhex('558becb82c120000e89c1e00008d8568ffffff5350c78568ffffff94000000ff15a0e00278'),'Exact unpatched selector prefix through genuine query CALL')
    need(source(0x780058b5,49)==bytes.fromhex('513d001000008d4c2408730f2bc88bc485018be18b088b400450c381e9001000002d0010000085013d0010000072ddebea'),'Exact complete original dynamic stack probe')
    imports=[dict(library=r['library'],**s) for r in pe.imports() for s in r['symbols'] if s['iat_rva']==0x2e0a0]
    need(imports==[dict(library='KERNEL32.dll',iat_rva=0x2e0a0,name='GetVersionExA',hint=373)] and source(0x7802e0a0,4)==struct.pack('<I',0x34600),'Unique original named query import and raw IAT')
    spans={}
    for label,address,count in (('selector-prefix',0x78003a0c,37),('stack-probe',0x780058b5,49),('probe-RX-page',0x78005000,4096)):
        p=out/(label+'.bin');p.write_bytes(source(address,count));spans[label]=dict(entry=address,end=address+count,bytes=count,sha256=sha(p))
    rows={}
    for line in decode.read_text().splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
        if m and int(m[1],16) in PCS+[0x780058e4]:
            address=int(m[1],16);raw=bytes.fromhex(m[2]);need(raw==source(address,len(raw)),'Decoded exact original instruction');rows[address]=dict(pc=address,bytes=len(raw),bytes_hex=raw.hex(),opcode=m[3],operands=m[4])
    need(set(rows)==set(PCS+[0x780058e4]) and len(PCS)==26,'Exact selector/probe execution path without loop-back JMP')
    accesses=[
        (0x78003a0c,0x20001850,'carried original EBP','write','Selector PUSH saves genuine carried EBP'),
        (0x78003a14,0x2000184c,0x78003a19,'write','Selector actual probe CALL return'),
        (0x780058b5,0x20001848,'carried original ECX','write','Probe PUSH saves carried ECX'),
        (0x780058db,0x20000850,'declared initial lower-page DWORD','read','First page touch after EAX122C-1000→22C'),
        (0x780058c5,0x20000624,'declared initial lower-page DWORD','read','Final touch after ECX0850-22C→0624; EAX1848'),
        (0x780058c9,0x20001848,'carried original ECX','read','Source restores saved ECX'),
        (0x780058cb,0x2000184c,0x78003a19,'read','Source loads original probe return into EAX'),
        (0x780058ce,0x20000620,0x78003a19,'write','Source relocates actual return below allocated frame'),
        (0x780058cf,0x20000620,0x78003a19,'read','Genuine probe RET reads relocated source return'),
        (0x78003a1f,0x20000620,'carried original EBX','write','Selector PUSH saves EBX over consumed probe return'),
        (0x78003a20,0x2000061c,0x200017b8,'write','Selector PUSH passes genuine version structure pointer'),
        (0x78003a21,0x200017b8,0x94,'write','Only source MOV initializes version structure size'),
        (0x78003a2b,0x7802e0a0,0x34600,'read','Actual unique source query IAT read'),
        (0x78003a2b,0x20000618,0x78003a31,'write','Actual query CALL return word before ESP/target publication')]
    patterns=[]
    for number,(first,final) in enumerate(((0,0),(4,8),(12,0x48),(1,0x80000000),(0x200,0x20000000),(0xffffffff,0xffffffff))):
        data=bytearray(4096);struct.pack_into('<I',data,0x850,first);struct.pack_into('<I',data,0x624,final);p=out/f'declared-lower-input-{number}.bin';p.write_bytes(data)
        patterns.append(dict(id=number,source='Fresh owned guest stack input before any worker source execution; not captured original memory',first_test_word=first,final_test_word=final,first_test_defined_flags=logic_flags(first,0x22c),final_test_defined_flags=logic_flags(final,0x20001848),source_AF_representative=0,path=str(p),sha256=sha(p)))
    report=dict(passed=True,scope='Independent static original selector/probe and declared initial lower-stack domain through actual OS-query CALL; no query outcome or native execution',provider_sha256=PROVIDER_SHA,baseline_acceptance_sha256=BASELINE_SHA,spans=spans,query_import=imports[0],raw_query_target=0x34600,new_compiled_source_bytes=86,new_guarded_source_bytes=86,new_executed_source_bytes=84,combined_executed_source_bytes=132,combined_source_identity_bytes=2026,new_source_PCs=26,combined_source_PCs=39,new_source_accesses=14,combined_source_accesses=24,combined_actual_source_CALLs=5,separate_HeapCreate_API_return_reads=1,genuine_probe_RET_count=1,probe_loopback_JMP_executed=False,PC_order=PCS,decoded_source_instructions=[rows[p] for p in PCS],new_access_order=[dict(pc=p,address=a,value=v,width=4,operation=o,meaning=m) for p,a,v,o,m in accesses],mapping_contract=dict(prior_mappings=18,additional_raw_RX_page=0x78005000,additional_declared_owned_lower_stack_page=0x20000000,total_mappings=20,lower_stack_mapped_upfront_only=True,original_policy_stack_low=0x20001000,original_policy_and_TIB_metadata_preserved=True,original_guard_growth_equivalence=False,lower_stack_original_capture_equivalence=False),declared_initial_lower_inputs=patterns,expected_query_frame=dict(State_EIP=0x34600,State_ESP=0x20000618,State_EBP=0x20001850,State_EAX=0x200017b8,State_ECX='restored carried ECX',return_word=0x78003a31,argument_pointer=0x200017b8,argument_bytes=4,source_structure_size_DWORD=0x94,query_called=False),flags_contract=dict(first_read_fault_pre_TEST_defined_flags=0,second_read_fault_pre_TEST_defined_flags=0x14,ordinary_zero_final_flags=0x44,final_TEST_mask=0x20001848,final_flags_derive_declared_lower_page_word=True,SF_always_zero_for_this_mask=True,undefined_AF_sites=[0x780039bf,0x780039d6,0x780058db,0x780058c5],generated_AF_representative=0,universal_original_AF_equivalence=False),required_review=['Never reseed State/FX or lower input after source execution starts','Preserve all18 prior mappings and nominal Policy/TIB metadata; qualify fresh page separately from original stack guard growth','Check generated probe CALL/PUSH/read/subtract/relocated-PUSH/RET order with partial store before ESP/EIP publication','Probe RET validates actual relocated source word and saved ECX, cannot synthesize return or restore selector EBP early','HeapCreate private full HANDLE stays live through probe/query frontier; every failure destroys exact private handle once','Only actual source MOV writes version size94; query import stays unresolved without OS call or invented version/mode','Private current authority and immutable parent deny stale/side tokens before dereference; poisoned retry preserves State/FX/all20pages/records','Exact four AF helper sites are qualified by generated progress, not universal undefined AF claim'],source_mode_selector_RET_executed=False,GetVersionExA_executed=False,query_outcome_invented=False,mode_selected=False,heap_initialized=False,original_executed=False,native_executed=False,whole_M4_complete=False)
    files={key(p):sha(p) for p in (Path(__file__),ROOT/'tools/analysis/pe.py',provider,baseline,decode,*out.iterdir()) if p.is_file()};p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');files[key(p)]=sha(p);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');need(all(sha(p)==h for p,h in files.items()),'Exact static input/output physical closure');print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'),new_source_PCs=26,new_accesses=14,combined_source_PCs=39,combined_source_accesses=24)))
if __name__=='__main__':main(sys.argv[1])
