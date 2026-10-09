"""Independent literal attach fragment / heap-create frontier; no execution."""
import hashlib
import json
import ntpath
import re
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASELINE_SHA = '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e'
PCS = [0x7800183c,0x7800183e,0x780039bf,0x780039c1,0x780039c3,0x780039c7,0x780039cc,0x780039cf,0x780039d0]

def need(v,w):
    if not v: raise ValueError(w)
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def key(p): return ntpath.normcase(ntpath.normpath(str(Path(p).absolute())))

def main(name):
    base = ROOT / 'reports/m4-crt-heap-init-review'
    out = base / name
    need(name.startswith('source-') and out.parent == base and not out.exists(),'Fresh independent source output')
    out.mkdir(parents=True)
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    old = ROOT / 'reports/m4-crt-locale-default-root/root-acceptance-r2/report.json'
    decode = ROOT / 'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'
    need(sha(provider)==PROVIDER_SHA and sha(old)==BASELINE_SHA,'Exact original provider and accepted locale anchor')
    pe = PEImage(provider.read_bytes())
    need(pe.image_base==0x78000000,'Original source PE base')
    def source(a,n): return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    fragment = bytes.fromhex('6a01e87c210000')
    heap = bytes.fromhex('33c06a003944240868001000000f94c050ff15a8e00278')
    spans = {}
    for label,a,raw in (('attach-fragment',0x7800183c,fragment),('heap-prefix',0x780039bf,heap),('heap-identity',0x780039bf,source(0x780039bf,77))):
        need(source(a,len(raw))==raw,'Independent original literal source span')
        p = out/(label+'.bin'); p.write_bytes(raw)
        spans[label] = dict(entry=a,end=a+len(raw),bytes=len(raw),sha256=sha(p))
    rows={}
    for line in decode.read_text().splitlines():
        m = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
        if m and int(m[1],16) in PCS:
            a,raw = int(m[1],16),bytes.fromhex(m[2]); need(source(a,len(raw))==raw,'Decoded instruction agrees with current source')
            rows[a] = dict(pc=a,bytes_hex=raw.hex(),mnemonic=m[3],operands=m[4].split(' <')[0].replace('\t',' ').strip())
    need(set(rows)==set(PCS),'All nine original instructions decoded')
    raw=bytes.fromhex(rows[0x7800183e]['bytes_hex'])
    need(raw[0]==0xe8 and 0x78001843+struct.unpack('<i',raw[1:])[0]==0x780039bf,'Literal original attach-fragment direct CALL')
    need(bytes.fromhex(rows[0x780039d0]['bytes_hex'])==bytes.fromhex('ff15a8e00278'),'Literal source memory-indirect CALL')
    imports=[dict(library=r['library'],**s) for r in pe.imports() for s in r['symbols'] if s['iat_rva']==0x2e0a8]
    need(imports==[dict(library='KERNEL32.dll',iat_rva=0x2e0a8,name='HeapCreate',hint=411)],'Unique original HeapCreate import metadata')
    token=struct.unpack('<I',source(0x7802e0a8,4))[0]
    need(token==0x3461e,'Raw import token is not a measured native function pointer')
    entry=0x20001860; heap_frame=entry-8
    accesses=[dict(pc=pc,address=a,value=v,width=4,operation=op,meaning=w) for pc,a,v,op,w in [
        (0x7800183c,entry-4,1,'write','literal attach fragment argument PUSH'),
        (0x7800183e,heap_frame,0x78001843,'write','actual fragment CALL return word'),
        (0x780039c1,entry-12,0,'write','HeapCreate maximum size PUSH'),
        (0x780039c3,entry-4,1,'read','CMP reads actual source argument after previous PUSH'),
        (0x780039c7,entry-16,0x1000,'write','HeapCreate initial size PUSH'),
        (0x780039cf,entry-20,0,'write','SETE-selected HeapCreate options PUSH'),
        (0x780039d0,0x7802e0a8,token,'read','actual raw import-target read before CALL store'),
        (0x780039d0,entry-24,0x780039d6,'write','actual HeapCreate source CALL return word'),
    ]]
    report=dict(passed=True,scope='Independent static literal attach fragment and heap initializer prefix to first HeapCreate refusal',provider_sha256=PROVIDER_SHA,
        baseline_acceptance_sha256=BASELINE_SHA,spans=spans,executed_prefix_PC_order=PCS,decoded_source_instructions=[rows[p] for p in PCS],source_access_order=accesses,
        completed_source_accesses_expected=8,executed_PCs_expected=9,actual_source_CALLs_expected=2,new_compiled_bytes=84,executed_prefix_bytes=30,new_source_identity_bytes=84,total_source_identity_bytes=1940,
        host_scheduling=dict(parent_ESP=entry,entry_ESP=entry,entry_PC=0x7800183c,project_only_carried_State_EIP=True,guest_stack_store=False,generic_Runtime_CPU_preserved=True,
            Runtime_call_records=11,Runtime_call_record_added=False,original_DllMain_or_attach_execution=False),
        mapping_contract=dict(total_mappings=17,all_prior_mappings_preserved=True,new_mapping=False,heap_global_page_78035000_mapped=False),
        stop=dict(source_CALL_PC=0x780039d0,import_slot=0x7802e0a8,raw_import_token=token,import_metadata=imports[0],frame=entry-24,return_word=0x780039d6,arguments=[0,0x1000,0],HeapCreate_executed=False),
        expected_terminal_registers=dict(EAX=0,ESP=entry-24,EIP=token,other_registers='unchanged from carried input'),
        expected_terminal_arithmetic_flags=dict(CF=0,PF=0,AF=0,ZF=0,SF=0,OF=0),
        early_XOR_flags=dict(CF=0,PF=1,AF='architecturally undefined; exact lifted representative must be documented separately',ZF=1,SF=0,OF=0),
        source_flags_notes='CMP argument1 against EAX0 overwrites all six arithmetic flags after successful load; source access observer fault before CMP publication retains preceding XOR flags including its compiler representative AF.',
        review_requirements=[
            'Use exact private known parent and active authority for opaque/side/stale-pointer refusals before casts or dereferences',
            'Host scheduler sets only State EIP at healthy actual mainargs-before; no stack reseed or synthetic Runtime record',
            'Check eight source accesses in original instruction order, with IAT read before actual CALL store',
            'Retain actual partial source stores before generated ESP/target publication and CMP read before flags',
            'Refuse after actual HeapCreate CALL publication, before native API, result, handle/mode write or source RET',
            'Firstfault ownership and immutable source/control associations survive terminal token changes, exceptions and poisoned retries',
            'Keep all17 existing mappings, full3504State/512FX/40CPU; no heap-global-page or prior locale/parser execution',
            'Actual native rich544B host captures and unchanged raw80/fulllegacy/nonvolatileXMM validator; actual caller LastError',
        ],original_executed=False,native_executed=False,HeapCreate_executed=False,heap_handle_published=False,heap_mode_selected=False,heap_initialized=False,locale_initialized=False,whole_M4_complete=False)
    paths=[Path(__file__),ROOT/'tools/analysis/pe.py',provider,decode,old,*out.iterdir()]
    files={key(p):sha(p) for p in paths if p.is_file()}
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');files[key(p)]=sha(p)
    (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8')
    need(all(sha(p)==h for p,h in files.items()),'Full current physical input/output identity')
    print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'),source_accesses=8,source_PCs=9,HeapCreate_frame=hex(entry-24))))

if __name__=='__main__': main(sys.argv[1])
