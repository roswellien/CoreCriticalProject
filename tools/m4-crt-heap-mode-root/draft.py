"""Source-only original-BEFORE and declared stack-input model; no native API."""
import json
from pathlib import Path
import struct
import sys
import time
sys.dont_write_bytecode = True
from consumer import F,M
from before import expected,STACK_PAGE,PROBE_PAGE,PAGE
from prefix import predict,source_material
ROOT = F.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import verify_manifest
from paths import publish_bytes,workspace_path


def main(directory):
    started = time.perf_counter_ns()
    out = workspace_path(directory,reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-mode-root':
        raise ValueError('Fresh heap-mode draft output')
    out.mkdir()
    for path in Path(__file__).parent.glob('*.py'):
        F.pin(path)
    accepted = F.pin(ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json',
        'e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326')
    admission = json.loads(accepted.read_bytes())
    previous = json.loads(F.pin(admission['receipts']['author_execution']['path'],
                                admission['receipts']['author_execution']['sha256']).read_bytes())
    program,providers,maths,ctrl,init,args,argv,source,commands = M.source_material(out)
    heap_program,pages,heap_commands = source_material(out)
    source.update(pages)
    wp,pp,gp = M.R.source_material()
    original = F.pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',F.ORIGINAL_SHA)
    payloads = [M.R.project(v) for v in M.R.originals(original.read_bytes())[:24]]
    rows,controls = [],[]
    for level in ('O0','O2'):
        identity = previous['levels'][level]
        with CaptureBundle(F.pin(identity['bundle'],identity['bundle_sha256']),identity['bundle_sha256']) as reader:
            root = F.LogicalPath(reader,'root')
            for index,payload in enumerate(payloads):
                row = F.LogicalPath(reader,f'row-{index}',root.inventory)
                entry,earlier = expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,level)
                derived = predict(entry,heap_program,0x48450001)
                captured_pages = [name for name in derived['phases']['heap-create-before'] if name.startswith('page-')]
                F.require(len(captured_pages)==20 and len(earlier)==20 and len(derived['phases'])==12,
                          '20 mappings,20 prior phases,12 heap/selector phases')
                F.require(derived['API_return_access']==(0x780039d0,0x20001848,0x780039d6,4,0)
                          and derived['probe_return_access']==(0x780058cf,0x20000620,0x78003a19,4,0),
                          'Separate API-return read and genuine relocated probe RET')
                F.require(derived['terminal_EIP']==0x34600 and derived['terminal_ESP']==0x20000618
                          and derived['state'][M.F.FLAGS[1][0]] in (0,1), 'Genuine version-query frontier')
                before_stack = bytes(entry.mem[STACK_PAGE])
                F.require(before_stack==bytes(4096),'Explicit ordinary zero-owned stack input')
                F.require(derived['memory'][PROBE_PAGE]==entry.mem[PROBE_PAGE], 'Raw RX probe identity preserved')
                rows.append(dict(level=level,index=index,PCs=len(derived['PCs']),source_accesses=len(derived['accesses']),
                    CALLs=len(derived['routes']),probe_RET=1,separate_API_return_reads=1,pages=20,
                    terminal_EIP=0x34600,terminal_ESP=0x20000618,AF_sites=derived['undefined'],
                    expected_source_accesses=derived['accesses']))
                if index==0:
                    for value in (0,0xffffffff,8,0x40,0x1848,0x80000000):
                        stack_input = struct.pack('<I',value)*1024
                        alternate,_ = expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,level,stack_input)
                        result = predict(alternate,heap_program,0x48450001)
                        final_flags = struct.unpack_from('<I',M.D.cpu(result['state']),32)[0]&0x8d5
                        tested = value&0x20001848
                        wanted = (((tested&255).bit_count()%2==0)<<2)|((tested==0)<<6)|((tested>>31)<<7)
                        F.require(final_flags==wanted,'Source TEST flags derive actual declared lower-stack DWORD')
                        controls.append(dict(level=level,initial_lower_page_DWORD=value,final_flags=final_flags,
                            native_executed=False,original_lower_stack_captured=False))
    for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
        for path,digest in module.PINS.items():
            F.pin(path,digest)
    for path in out.iterdir():
        if path.is_file():
            F.pin(path)
    closure = verify_manifest(F.PHYSICAL)
    report = dict(passed=True,scope='Draft original-BEFORE plus explicit owned lower-stack input and source probe/query model; no current native proof',
        rows=rows,ordinary_BEFORE_models=48,declared_stack_formula_controls=controls,
        source_PCs=39,source_accesses=24,actual_source_CALLs=5,genuine_probe_RET=1,separate_API_return_reads=1,
        host_guest_execution_stores=0,mappings=20,prior_mappings_preserved=18,
        new_owned_lower_stack_page=STACK_PAGE,new_raw_RX_probe_page=PROBE_PAGE,
        lower_stack_bytes_original_observed=False,original_stack_guard_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False,ordinary_lower_stack_initial_DWORD=0,
        new_compiled_source_bytes=86,reused_heap_source_bytes=84,executed_source_bytes=132,
        total_source_identity_bytes=2026,undefined_AF_universal_equivalence=False,
        current_native_compared=False,native_executed=False,HeapCreate_executed=False,
        GetVersionExA_executed=False,heap_mode_selected=False,heap_initialized=False,
        heap_initializer_RET=False,original_attach_proved=False,whole_M4_complete=False,
        source_commands=commands+heap_commands,files=F.PHYSICAL,physical_closure=closure,
        seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','source_commands','declared_stack_formula_controls')}))


if __name__=='__main__':
    main(*sys.argv[1:])
