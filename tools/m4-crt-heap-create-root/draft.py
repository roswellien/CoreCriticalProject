"""Exercise the new source model on immutable BEFORE inputs; no API runs."""
import json
from pathlib import Path
import struct
import sys
import time
sys.dont_write_bytecode = True
from consumer import F, M
from before import expected, PAGE
from prefix import predict, source_material
ROOT = F.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import verify_manifest
from paths import publish_bytes, workspace_path


def main(directory):
    started = time.perf_counter_ns()
    out = workspace_path(directory,reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-create-root':
        raise ValueError('Fresh source model draft directory')
    out.mkdir()
    for path in Path(__file__).parent.glob('*.py'):
        F.pin(path)
    accepted = F.pin(ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json',
        'a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d')
    admission = json.loads(accepted.read_bytes())
    production = F.pin(admission['receipts']['author_execution']['path'],
        admission['receipts']['author_execution']['sha256'])
    previous = json.loads(production.read_bytes())
    program,providers,maths,ctrl,init,args,argv,source,commands = M.source_material(out)
    heap_program,pages,heap_commands = source_material(out)
    source.update(pages)
    wp,pp,gp = M.R.source_material()
    original = F.pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',F.ORIGINAL_SHA)
    payloads = [M.R.project(v) for v in M.R.originals(original.read_bytes())[:24]]
    rows = []
    for level in ('O0','O2'):
        receipt = previous['levels'][level]
        with CaptureBundle(F.pin(receipt['bundle'],receipt['bundle_sha256']),receipt['bundle_sha256']) as reader:
            root = F.LogicalPath(reader,'root')
            for index,payload in enumerate(payloads):
                row = F.LogicalPath(reader,f'row-{index}',root.inventory)
                entry,earlier = expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,level)
                derived = predict(entry,heap_program,0x48450001)
                page_files=[name for name in derived['phases']['heap-create-before'] if name.startswith('page-')]
                if len(page_files) != 18 or derived['API_return_access'] != (0x780039d0,0x20001848,0x780039d6,4,0):
                    raise ValueError('Authentic eighteen-page seam and distinct API return read '+repr((page_files,derived['API_return_access'])))
                untouched = bytearray(entry.mem[PAGE])
                struct.pack_into('<I',untouched,0,0x48450001)
                if derived['memory'][PAGE] != untouched:
                    raise ValueError('Only source handle DWORD changed in raw heap page')
                if derived['phases']['heap-create-api-returned']['state.bin'][2472:2476] != struct.pack('<I',0x780039d6):
                    raise ValueError('Declared stdcall return PC')
                rows.append(dict(level=level,index=index,source_PCs=len(derived['PCs']),source_accesses=len(derived['accesses']),
                    source_CALLs=len(derived['routes']),separate_API_return_reads=1,
                    prior_phases=len(earlier),heap_phases=len(derived['phases']),pages=18,
                    terminal_EIP=0x78003a0c,terminal_ESP=derived['mode_frame'],token=derived['token']))
    for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
        for path,digest in module.PINS.items():
            F.pin(path,digest)
    for path in out.iterdir():
        if path.is_file():
            F.pin(path)
    closure=verify_manifest(F.PHYSICAL)
    report=dict(passed=True,scope='Draft original-BEFORE source model with declared guest API ABI return; no current native or API proof',
        rows=rows,ordinary_BEFORE_models=len(rows),source_PCs=13,source_accesses=10,separate_API_return_reads=1,
        host_guest_stack_or_global_stores=0,mappings=18,old_pages_preserved=17,new_raw_RW_page=PAGE,
        compiled_source_bytes=84,executed_source_bytes=48,total_source_identity_bytes=1940,
        original_x86_API_internals_equivalence=False,undefined_AF_universal_equivalence=False,
        current_native_compared=False,native_executed=False,HeapCreate_executed=False,heap_initialized=False,
        original_attach_proved=False,whole_M4_complete=False,source_commands=commands+heap_commands,
        files=F.PHYSICAL,physical_closure=closure,seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','files','source_commands')}))


if __name__=='__main__':
    main(*sys.argv[1:])
