"""Read-only recovery of the exact CRT floating-division flag writer.

All input bytes, decoded instructions and lifted material stay in ignored
reports. This script does not load the provider or execute original code.
"""
import hashlib, importlib.util, json, re, struct, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
RANGES = ((0x78004254, 0x780042e1), (0x7802c070, 0x7802c0ae),
          (0x780042e1, 0x78004410), (0x7801129b, 0x78011318))

def need(value, why):
    if not value:
        raise ValueError(why)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def pin(path, expected=None):
    path = Path(path).resolve(); got = sha(path)
    need(expected is None or expected == got, 'Exact input identity: ' + str(path))
    PINS[str(path)] = got
    return path

def main(out):
    need(out.is_relative_to(ROOT/'reports/m4-crt-fdiv') and not out.exists(), 'Fresh private recovery directory')
    parser = pin(ROOT/'tools/analysis/pe.py', 'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec = importlib.util.spec_from_file_location('fdiv_pe_metadata', parser)
    pe = importlib.util.module_from_spec(spec); spec.loader.exec_module(pe)
    provider_path = pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    game_path = pin(ROOT/'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    provider_raw = provider_path.read_bytes(); provider = pe.PEImage(provider_raw)
    game = pe.PEImage(game_path.read_bytes())
    def raw_at(address, count):
        offset, _ = provider.rva_range(address-provider.image_base, count)
        return provider_raw[offset:offset+count]
    def permission(address, count, wanted):
        return any(s['virtual_address'] <= address-provider.image_base and address-provider.image_base+count <= s['virtual_address']+s['raw_size'] and s['characteristics'] & 0xe0000000 == wanted for s in provider.sections)
    need(provider.image_base == 0x78000000 and game.image_base == 0x400000, 'Exact PE bases')
    export = [e for e in provider.exports() if '_adjust_fdiv' in e['names']]
    need(len(export) == 1 and export[0]['ordinal'] == 158 and export[0]['rva'] == 0x37c2c and 'forwarder' not in export[0], 'Exact named data export')
    imported = [(lib['library'], s) for lib in game.imports() for s in lib['symbols'] if s['iat_rva']+game.image_base == 0x5bb508]
    need(len(imported) == 1 and imported[0][0].casefold() == 'msvcrt.dll' and imported[0][1]['name'] == '_adjust_fdiv', 'Exact game data IAT owner')
    decoder = pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe', 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    command = [str(decoder), '-d', '--x86-asm-syntax=intel', str(provider_path)]
    result = subprocess.run(command, capture_output=True)
    need(result.returncode == 0 and not result.stderr, 'Fresh exact provider decode')
    instructions = {}
    for line in result.stdout.decode().splitlines():
        match = re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$', line)
        if not match:
            continue
        address = int(match[1], 16); body = bytes.fromhex(match[2])
        need(raw_at(address, len(body)) == body and permission(address, len(body), 0x60000000), 'Every decoded instruction matches exact file-backed RX')
        need(address not in instructions, 'Unique instruction start')
        instructions[address] = dict(address=address, size=len(body), mnemonic=match[3], operands=match[4].strip(), bytes_hex=body.hex())
    def walk(entry, admitted):
        todo = [entry]; seen = set(); edges = []; calls = []
        while todo:
            pc = todo.pop()
            if pc in seen:
                continue
            row = instructions.get(pc)
            need(row is not None and admitted(pc, row['size']), 'Complete bounded CFG at ' + hex(pc))
            seen.add(pc); next_pc = pc+row['size']; op = row['mnemonic']
            target_match = re.match(r'^0x([0-9a-f]+)(?:\s|$)', row['operands'])
            target = int(target_match[1], 16) if target_match else None
            if op == 'ret':
                continue
            if op == 'call':
                calls.append(dict(site=pc, target=target, operands=row['operands'], return_pc=next_pc))
            elif op.startswith('j'):
                need(target is not None, 'Only direct branch admitted')
                edges.append((pc, target)); todo.append(target)
                if op == 'jmp':
                    continue
            edges.append((pc, next_pc)); todo.append(next_pc)
        return dict(entry=entry, instructions=[instructions[p] for p in sorted(seen)], edges=edges, calls=calls)
    admitted = lambda a,n: any(start <= a and a+n <= end for start,end in RANGES)
    roots = [0x78004254, 0x7800426b, 0x780042a3, 0x780042cf, 0x7802c070, 0x780042e1, 0x780042f7, 0x7800432c, 0x7800439f]
    graphs = [walk(entry, admitted) for entry in roots]
    pcs = {r['address'] for graph in graphs for r in graph['instructions']}
    control_path = pin(ROOT/'reports/m4-crt-control/independent-review-r4/report.json', 'b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56')
    control = json.loads(control_path.read_text())
    control_pcs = {r['address'] for graph in graphs[5:] for r in graph['instructions']}
    accepted_domain = set(control['source_model']['exact_model_source_PC_coverage']) | {int(p,16) for p in control['source_model']['unexecuted_static_PCs']}
    need(control_pcs == accepted_domain and len(control_pcs) == 148, 'Complete accepted hot/cold control dependency, including two retained static PCs')
    parent = walk(0x78004227, lambda a,n: 0x78004227 <= a and a+n <= 0x78004254)
    need(instructions[0x780018ab]['mnemonic'] == 'call' and instructions[0x780018ab]['operands'].startswith('0x78004227 '), 'Static DLL attach call into callback orchestrator')
    callback = struct.unpack('<I', raw_at(0x78037c28, 4))[0]
    need(callback == 0x78004254 and permission(0x78037c28, 32, 0xc0000000), 'Actual source-file callback pointer and owned RW data')
    provider_imports = [(lib['library'],s) for lib in provider.imports() for s in lib['symbols']]
    api_imports = []
    for address,name in ((0x7802e098,'GetModuleHandleA'), (0x7802e0d0,'GetProcAddress')):
        matches = [(lib,s) for lib,s in provider_imports if s['iat_rva']+provider.image_base == address]
        need(len(matches) == 1 and matches[0][0].casefold() == 'kernel32.dll' and matches[0][1]['name'] == name, 'Actual named provider OS IAT owner')
        api_imports.append(dict(slot=address, library=matches[0][0], symbol=matches[0][1], raw_IAT_value=struct.unpack('<I',raw_at(address,4))[0]))
    names = [provider.rva_string(a-provider.image_base) for a in (0x7802e404,0x7802e3e8)]
    need(names == ['KERNEL32','IsProcessorFeaturePresent'], 'Actual lookup names')
    constants = []
    for address,value in ((0x78030018,3145727.0), (0x78030010,4195835.0), (0x7802ffc8,1.0)):
        body = raw_at(address,8); actual = struct.unpack('<d',body)[0]
        need(actual == value and permission(address,8,0x40000000), 'Exact RO fallback binary64 operand')
        constants.append(dict(address=address,value=actual,sha256=hashlib.sha256(body).hexdigest()))
    refs = [r for r in instructions.values() if re.search(r'(?<![0-9a-f])0x78037c2c(?![0-9a-f])',r['operands'])]
    need([r['address'] for r in refs] == [0x7800425e,0x78028d53,0x7802c6d4], 'Exact direct text references')
    pointer_stores = [r for r in graphs[1]['instructions'] if r['mnemonic']=='mov' and r['operands'].startswith('dword ptr [')]
    need(len(pointer_stores)==6 and instructions[0x78004268]['mnemonic']=='fnclex', 'Six related function-pointer stores and final exception clearing')
    history=ROOT/'reports/m4-crt-fdiv/source-recovery-attempt-r1'
    pin(history/'review-source.py');pin(history/'failure.json')
    out.mkdir(parents=True)
    (out/'provider-text-llvm.txt').write_bytes(result.stdout);pin(out/'provider-text-llvm.txt')
    spans = []
    for start,end in RANGES:
        body=raw_at(start,end-start);path=out/f'source-{start:x}.bin';path.write_bytes(body);pin(path)
        spans.append(dict(address=start,size_bytes=end-start,file_offset=provider.rva_range(start-provider.image_base,end-start)[0],sha256=sha(path)))
    report = dict(passed=True,scope='Exact static writer/dependency recovery only; initialized data and native service execution unaccepted',data_export=export[0],game_import=imported[0],source_value=struct.unpack('<I',raw_at(0x78037c2c,4))[0],initialized_value_measured=False,source_callback_global=0x78037c28,source_callback_value=callback,static_attach_call=instructions[0x780018ab],callback_orchestrator=parent,writer_root=0x78004254,complete_graphs=graphs,unique_writer_dependency_instructions=len(pcs),accepted_control_dependency_instructions=len(control_pcs),provider_API_imports=api_imports,dynamic_lookup_names=names,dynamic_call_site=0x780042cc,dynamic_argument=0,dynamic_return_pc=0x780042ce,fallback_constants=constants,function_pointer_stores=pointer_stores,direct_global_references=refs,source_spans=spans,command=command,decoded_RX_instructions=len(instructions),all_decoded_bytes_match_source=True,limitations=['Source callback pointer establishes static linkage; complete process/DLL attach is not executed or accepted','The dynamic Windows query result must be measured; the file value zero is not initialized state','Fallback branch performs x87 arithmetic, comparisons, status transfer and two returns; no fallback result is assumed','Full controlfp hot/cold CFG is reused only as exact accepted dependency identity; this writer needs its own connected native review','Function-pointer values remain 32-bit guest addresses and require exact typed dispatch if later used','Linear text reference inventory does not prove absence of indirect aliases','No original instructions executed, no provider load, no IAT replacement, no native startup/menu acceptance'],whole_M4_complete=False)
    rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp)
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py');pin(Path(__file__));pin(sys.executable)
    (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,dependency_instructions=len(pcs),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'),native_accepted=False)))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
