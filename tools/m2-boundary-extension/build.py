"""Prepare immutable authored block identities and record offline tool evidence."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from adapt import adapt, BLOCKS
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage

LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
REMILL = ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1'
OUT = ROOT / 'reports/m2-boundary-extension'
COMMANDS=[]
FIXTURE_HASH = '61b236a2a8402d96c48a28340203ae08f1351cf7b3f095ab4b4b817e38e6c667'
GAME_HASH = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(args):
    print('Running:', Path(str(args[0])).name, flush=True)
    argv=[str(a) for a in args]
    child=subprocess.run(argv,check=True,capture_output=True,text=True)
    COMMANDS.append({'argv':argv,'stdout':child.stdout,'stderr':child.stderr})
    return child

def import_evidence():
    image_path = ROOT / 'MW3/Mech3.exe'
    raw = image_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != GAME_HASH:
        raise ValueError('Observed import evidence requires admitted MW3 executable')
    image = PEImage(raw)
    csv = ROOT / 'games/mw3/docs/imports-mw3-us-1-2-retail.csv'
    import csv as csv_module
    rows = list(csv_module.DictReader(csv.read_text().splitlines()))
    # Keep the static import inventory separate from the actual CALL instruction.
    selected = [row for row in rows if row.get('symbol') == 'timeGetTime' or row.get('name') == 'timeGetTime']
    if not selected:
        selected = [row for row in rows if 'timeGetTime' in row.values()]
    if len(selected) != 1 or 'WINMM.dll' not in selected[0].values() or '0x001BB75C' not in selected[0].values():
        raise ValueError('Observed WINMM import inventory changed')
    sites = []
    for va in (0x5996d6, 0x599716):
        off, _ = image.rva_range(va-image.image_base, 6)
        code = raw[off:off+6]
        if hashlib.sha256(code).hexdigest() != '03e2e573ac330f34ca026208ee571724c355c291b4b2d3320d06fca676b5978e':
            raise ValueError('Observed IAT CALL instruction changed')
        sites.append({'guest_pc': va, 'size': 6, 'file_offset': off,
                      'instruction_sha256': hashlib.sha256(code).hexdigest(),
                      'operation': 'indirect CALL through guest32 IAT slot'})
    record = {'schema_version': 1, 'image_sha256': GAME_HASH, 'image_base': image.image_base,
              'provider': 'WINMM.dll', 'symbol': 'timeGetTime', 'iat_rva': 0x1bb75c,
              'iat_guest_va': 0x5bb75c, 'import_csv_sha256': sha(csv),
              'sites': sites, 'scope': 'static called-import evidence; reachability and game timing semantics unknown'}
    (OUT / 'observed-import.json').write_text(json.dumps(record, indent=2)+'\n')

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'tests/m2-boundary-extension/calls.s'
    run([LLVM/'llvm-mc.exe', '-triple=i686-pc-windows-msvc', '-filetype=obj', source, '-o', OUT/'calls.obj'])
    run([LLVM/'llvm-objcopy.exe', '--dump-section', f'.text={OUT / "calls.bin"}', OUT/'calls.obj'])
    if sha(OUT/'calls.bin') != FIXTURE_HASH:
        raise ValueError('Authored fixture machine-code identity changed')
    raw = (OUT/'calls.bin').read_bytes()
    (OUT/'original-disassembly.txt').write_text(run([LLVM/'llvm-objdump.exe', '--disassemble', '--x86-asm-syntax=intel', OUT/'calls.obj']).stdout)
    for name, (address, size) in BLOCKS.items():
        guest, host = OUT/f'{name}-guest.ll', OUT/f'{name}-host.ll'
        data = raw[address-0x10000000:address-0x10000000+size]
        run([REMILL/'build/bin/lift/remill-lift-21.exe', '--arch=x86', '--os=windows', f'--address={address}', f'--bytes={data.hex()}', f'--ir_out={guest}'])
        adapt(LLVM/'LLVM-C.dll', guest, host, OUT/f'{name}-layout.json', name)
        run([LLVM/'opt.exe', '-passes=default<O2>', '-S', host, '-o', OUT/f'{name}-host-O2.ll'])
        for level in ('O0','O2'):
            ir = host if level=='O0' else OUT/f'{name}-host-O2.ll'
            obj = OUT/f'{name}-{level}.obj'
            run([LLVM/'llc.exe', '-filetype=obj', '-'+level, ir, '-o', obj])
            (OUT/f'{name}-{level}-disassembly.txt').write_text(run([LLVM/'llvm-objdump.exe', '--disassemble', '--x86-asm-syntax=intel', obj]).stdout)
            symbols=run([LLVM/'llvm-nm.exe','--undefined-only',obj]).stdout
            layout=json.loads((OUT/f'{name}-layout.json').read_text())
            allowed=set(layout['bridges'])
            actual=set(re.findall(r'\bU\s+(\S+)',symbols))
            if not actual<=allowed:raise ValueError('Unexpected native object helper: '+repr(actual-allowed))
            (OUT/f'{name}-{level}-symbols.txt').write_text(symbols)
    import_evidence()
    (OUT/'prepare-commands.json').write_text(json.dumps({'commands':COMMANDS},indent=2)+'\n')

def record():
    artifacts = {p.name: sha(p) for p in OUT.iterdir() if p.is_file() and (p.suffix in ('.ll','.obj') or p.name=='calls.bin' or p.name.endswith(('-layout.json','-disassembly.txt','-symbols.txt')) or p.name=='prepare-commands.json')}
    sources = {}
    for folder in (HERE, ROOT/'tests/m2-boundary-extension'):
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                sources[str(p.relative_to(ROOT)).replace('\\','/')] = sha(p)
    for p in (ROOT/'tools/lifting/host_adapter.py', ROOT/'runtime/memory/guest_memory.cpp', ROOT/'runtime/memory/guest_memory.hpp', ROOT/'runtime/core/guest_address.hpp',ROOT/'docs/m2-boundary-extension-contract.md'):
        sources[str(p.relative_to(ROOT)).replace('\\','/')] = sha(p)
    workers = {'reference': OUT/'build-reference/Release/m2_reference.exe',
               'O0': OUT/'build-O0/m2_native.exe', 'O2': OUT/'build-O2/m2_native.exe'}
    worker_evidence={}
    for key,path in workers.items():
        target=OUT/f'worker-{key}-pe.txt'
        target.write_text(run([LLVM/'llvm-readobj.exe','--file-headers','--coff-imports',path]).stdout)
        worker_evidence[target.name]=sha(target)
    map_path=OUT/'build-reference/m2_reference.map'
    matches=re.findall(r'^\s*\w+:\w+\s+_?m2_live_bridge\s+([0-9a-fA-F]+)',map_path.read_text(),re.M)
    if len(matches)!=1:raise ValueError('Original bridge link-map identity missing')
    shim_rva=int(matches[0],16)-0x18000000
    if not 0<shim_rva<0x100000:raise ValueError('Invalid original shim RVA')
    record = {'schema_version': 1, 'scope': 'authored M2 call/global/import/indirect routing probe',
              'fixture_sha256': FIXTURE_HASH, 'blocks': {k: {'entry':v[0], 'size':v[1]} for k,v in BLOCKS.items()},
              'remill_commit': '0e324aee8c67a63ec759ef379dcfafa0b3cb1448',
              'remill_lifter_sha256': sha(REMILL/'build/bin/lift/remill-lift-21.exe'),
              'semantics_sha256': sha(REMILL/'build/lib/Arch/X86/Runtime/x86.bc'), 'llvm_version': '21.1.8',
              'remill_state_header_sha256': sha(REMILL/'include/remill/Arch/X86/Runtime/State.h'),
              'tools': {name:sha(LLVM/name) for name in ('LLVM-C.dll','llvm-mc.exe','llvm-objcopy.exe','llvm-objdump.exe','llvm-nm.exe','llvm-readobj.exe','opt.exe','llc.exe','clang-cl.exe')},
              'workers': {k: {'path':str(v), 'sha256':sha(v)} for k,v in workers.items()},
              'source_hashes':sources, 'artifacts':artifacts, 'observed_import_sha256':sha(OUT/'observed-import.json'),
              'worker_evidence':worker_evidence,'original_shim_rva':shim_rva,
              'original_link_map':{'path':str(map_path),'sha256':sha(map_path),'preferred_base':0x18000000,'actual_base':'recorded per live execution; environmental relocation allowed'},
              'provider_contract':{'selection':'same selected guest timer bridge for controlled and live','identities':['deterministic-uint32','WINMM.timeGetTime'],'provider_calls_per_case':1,'bridge_calls_per_case':1,'guest_host_pointer_casts':0,'live_requests':8,'live_df':0,'live_unused_timer':0,'direct_argument':'actual [ESP+4] reload after EAX poison 0xa5a5f00d'},
              'routing_contract': {'guest_address_bits':32, 'state_bytes':3504, 'contexts':'one isolated context per request',
                                  'direct_and_indirect_shared':True, 'replacement_original_route':True, 'unknown_targets':'reject with PC and target'}}
    record['route_selection']={name:{'guest_pc':v[0], 'original':f'mw34_block_{v[0]:x}',
        'selected': 'authored_timeGetTime_bridge' if name=='timer' else f'mw34_block_{v[0]:x}',
        'callee_cleanup_bytes':4 if name=='direct' else 0,
        'kind':'continuation' if name.startswith('after_') or name=='entry' else 'callee'} for name,v in BLOCKS.items()}
    record['source_identity']=hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (OUT/'build.json').write_text(json.dumps(record, indent=2)+'\n')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    args=parser.parse_args()
    record() if args.record else prepare()
