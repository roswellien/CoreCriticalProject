"""Prepare complete CRT entry/control roots for native startup integration.

Reads the exact admitted image and emits private source/CFG/IR artifacts.
Does not execute original instructions, load a provider, or admit startup.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-entry'
PINS = {}
RANGES = ((0x5AC3A0, 0x5AC54E), (0x5AC586, 0x5AC59E),
          (0x5AC5A0, 0x5AC5B3), (0x5AC5C0, 0x5AC5C1),
          (0x5AC5D6, 0x5AC5DC), (0x5AE390, 0x5AE3A8),
          (0x5AE3F4, 0x5AE3FA))
ENTRIES = (0x5AC3A0, 0x5AC502, 0x5AC517, 0x5AC586,
           0x5AC592, 0x5AC598, 0x5AC5A0, 0x5AC5C0,
           0x5AC5D6, 0x5AE390, 0x5AE3F4)


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(path, expected=None):
    path = Path(path).resolve()
    digest = sha(path)
    need(expected is None or digest == expected, 'Exact input: ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'Stable input identity')
    PINS[str(path)] = digest
    return path


def prepare(out):
    need(out.parent == BASE and not out.exists(), 'Fresh immediate private output required')
    image = pin(ROOT/'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    parser = pin(ROOT/'tools/analysis/pe.py', 'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec = importlib.util.spec_from_file_location('crt_entry_pe', parser)
    pe_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pe_module)
    pe = pe_module.PEImage(image.read_bytes())
    need(pe.image_base == 0x400000 and pe.entry_point_rva + pe.image_base == ENTRIES[0], 'Actual PE entry')
    previous = pin(ROOT/'reports/m4-startup/recovery/report.json', 'ecf038ad83d439fa29181255dbbfe75ffa00c9cdb44eca83232e3a57984bd0a3')
    prior = json.loads(previous.read_text())
    need(prior['entry_point_va'] == ENTRIES[0] and prior['initializer_nonzero_count'] == 144, 'Retain original complete startup boundary')
    llvm = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    decoder = pin(llvm/'llvm-objdump.exe', 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    lift = pin(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe', 'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38')
    semantics = pin(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc', '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca')
    pin(llvm/'llvm-link.exe'); pin(llvm/'opt.exe'); pin(llvm/'LLVM-C.dll', '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb')
    out.mkdir(parents=True)
    (out/'prepare-source.py').write_bytes(Path(__file__).read_bytes())
    commands = []

    def run(tool, args, name):
        result = subprocess.run([str(tool), *args], capture_output=True)
        log = out/name
        log.write_bytes(result.stdout)
        (out/(name+'.stderr')).write_bytes(result.stderr)
        commands.append(dict(program=str(tool), arguments=args, exit_code=result.returncode, stdout=str(log), stderr=str(out/(name+'.stderr'))))
        need(result.returncode == 0, 'Static command: ' + name)
        return result.stdout

    def source(address, count):
        rva = address-pe.image_base
        offset, _ = pe.rva_range(rva, count)
        sections = [s for s in pe.sections if s['virtual_address'] <= rva and rva+count <= s['virtual_address']+s['raw_size']]
        need(len(sections) == 1 and sections[0]['characteristics'] & 0xE0000000 == 0x60000000, 'File-backed RX span')
        return pe.data[offset:offset+count]

    try:
        instructions = {}
        dense = bytearray([0xCC] * (RANGES[-1][1]-RANGES[0][0]))
        spans = []
        for start, end in RANGES:
            raw = source(start, end-start)
            path = out/f'source-{start:x}.bin'
            path.write_bytes(raw)
            dense[start-RANGES[0][0]:end-RANGES[0][0]] = raw
            spans.append(dict(address=start, size=end-start, path=str(path), sha256=sha(path)))
            decoded = run(decoder, ['-d', '--x86-asm-syntax=intel', '--start-address='+hex(start), '--stop-address='+hex(end), str(image)], f'decode-{start:x}.txt')
            for line in decoded.decode().splitlines():
                match = re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$', line)
                if not match:
                    continue
                address = int(match[1], 16); body = bytes.fromhex(match[2])
                need(start <= address < end and address+len(body) <= end and source(address, len(body)) == body, 'Exact bounded decode')
                need(address not in instructions, 'Unique decoded PC')
                instructions[address] = dict(address=address, size=len(body), mnemonic=match[3], operands=match[4].strip(), bytes_hex=body.hex())
        (out/'dense-lift.bin').write_bytes(dense)
        imports = {pe.image_base+s['iat_rva']: dict(library=lib['library'], **s) for lib in pe.imports() for s in lib['symbols']}

        def walk(entry):
            seen = set(); todo = [entry]; edges = []; calls = []; tails = []
            while todo:
                pc = todo.pop()
                if pc in seen:
                    continue
                need(pc in instructions, 'Complete bounded CFG '+hex(pc))
                row = instructions[pc]; seen.add(pc)
                op = row['mnemonic']; next_pc = pc+row['size']; body = bytes.fromhex(row['bytes_hex'])
                target_match = re.match(r'^0x([0-9a-f]+)(?:\s|$)', row['operands'])
                target = int(target_match[1], 16) if target_match else None
                memory = re.match(r'^dword ptr \[0x([0-9a-f]+)\]$', row['operands'])
                iat = int(memory[1], 16) if memory else None
                if target is not None and (op.startswith('j') or op == 'call'):
                    if body[0] in (0xE8, 0xE9):
                        encoded = next_pc+struct.unpack_from('<i', body, 1)[0]
                    elif body[0] == 0x0F and 0x80 <= body[1] <= 0x8F:
                        encoded = next_pc+struct.unpack_from('<i', body, 2)[0]
                    elif body[0] == 0xEB or 0x70 <= body[0] <= 0x7F:
                        encoded = next_pc+struct.unpack_from('<b', body, 1)[0]
                    else:
                        raise ValueError('Unsupported relative branch encoding')
                    need(target == encoded, 'Independent encoded branch target')
                if op == 'ret':
                    continue
                if op == 'call':
                    need(target in ENTRIES or iat in imports, 'Exact reached direct root or named/ordinal IAT')
                    calls.append(dict(site=pc, return_pc=next_pc, direct_target=target, iat_slot=iat, import_owner=imports.get(iat)))
                if op == 'jmp' and iat is not None:
                    need(iat in imports and body[0] == 0xFF and body[1] == 0x25 and struct.unpack_from('<I', body, 2)[0] == iat, 'Exact import tail encoding')
                    tails.append(dict(site=pc, iat_slot=iat, import_owner=imports[iat]))
                    continue
                if op.startswith('j'):
                    need(target is not None, 'Only exact direct internal branch')
                    edges.append([pc, target]); todo.append(target)
                    if op == 'jmp':
                        continue
                edges.append([pc, next_pc]); todo.append(next_pc)
            return dict(entry=entry, instructions=[instructions[p] for p in sorted(seen)], edges=edges, calls=calls, import_tails=tails)

        graphs = [walk(entry) for entry in ENTRIES]
        main = graphs[0]
        need(0x5AC502 not in {r['address'] for r in main['instructions']} and 0x5AC517 not in {r['address'] for r in main['instructions']}, 'SEH roots remain separately reached by dispatch')
        for slot, name in ((0x5BB508, '_adjust_fdiv'), (0x5BB518, '_acmdln'), (0x5BB514, '__getmainargs'), (0x5BB528, '_except_handler3'), (0x5BB51C, '_XcptFilter')):
            need(imports[slot]['library'].casefold() == 'msvcrt.dll' and imports[slot]['name'] == name, 'Exact data/SEH/argv owner')
        need(imports[0x5BB438]['library'].casefold() == 'mfc42.dll' and imports[0x5BB438]['ordinal'] == 1576, 'Exact MFC handoff ordinal')
        need(instructions[0x5AC3B6]['mnemonic'] == 'mov' and instructions[0x5AC3B6]['operands'] == 'dword ptr fs:[0x0], esp', 'Real SEH install')
        need(instructions[0x5AC531]['operands'] == 'dword ptr fs:[0x0], ecx', 'Real SEH restore')
        need(instructions[0x5AC468]['operands'] == 'dword ptr [0x5bb514]', 'Actual five-argument argv call')
        for entry in ENTRIES:
            flags = ['--arch=x86', '--os=windows', '--address='+str(RANGES[0][0]), '--entry_address='+str(entry), '--bytes='+dense.hex(), '--semantics_dir='+str(semantics.parent), '--ir_out='+str(out/f'guest-{entry:x}.ll')]
            flags_path = out/f'flags-{entry:x}.txt'
            flags_path.write_text('\n'.join(flags)+'\n')
            run(lift, ['--flagfile='+str(flags_path)], f'lift-{entry:x}.log')
        run(llvm/'llvm-link.exe', [*(str(out/f'guest-{entry:x}.ll') for entry in ENTRIES), '-S', '-o', str(out/'guest.ll')], 'link.log')
        run(llvm/'opt.exe', ['-passes=verify', '-disable-output', str(out/'guest.ll')], 'verify.log')
        text = (out/'guest.ll').read_text()
        need('__remill_missing_block' not in text, 'No missing original block')
        need(set(re.findall(r'^define ptr @([^ (]+)', text, re.M)) == {f'sub_{entry:x}' for entry in ENTRIES}, 'Exactly eleven complete root definitions')
        graph_path = out/'exact-CFG.json'
        graph_path.write_text(json.dumps(dict(graphs=graphs), indent=2)+'\n')
        report = dict(passed=True, scope='Complete exact game CRT entry and separate SEH/control/handoff root static lift; execution unadmitted', image_sha256=sha(image), source_spans=spans, entries=list(ENTRIES), exact_CFG=str(graph_path), ordinary_entry_instructions=len(main['instructions']), unique_instructions=len({r['address'] for g in graphs for r in g['instructions']}), separate_SEH_entries=[0x5AC502,0x5AC517,0x5AC586,0x5AC592], source_data_imports=[dict(slot=slot,owner=imports[slot]) for slot in (0x5BB508,0x5BB518)], calls=main['calls'], table_ranges=[[0x5E0248,0x5E024C],[0x5E0000,0x5E0244]], getmainargs=dict(site=0x5AC468, cdecl_argument_bytes=20, outputs=['EBP-0x60 argc','EBP-0x70 argv pointer','EBP-0x64 envp pointer'], expand_wildcards_global=0x736594, startup_info_local='EBP-0x6c', startup_info_source=0x736598, return_code_checked=False), SEH=dict(old_chain_local='EBP-0x10', handler=0x5AC586, scope_table=0x5D0F78, try_level_local='EBP-4', exception_pointers_local='EBP-0x14', saved_SP_local='EBP-0x18', exception_code_local='EBP-0x78', installation=0x5AC3B6, restoration=0x5AC531, native_dispatch_implemented=False), guest_IR_sha256=sha(out/'guest.ll'), external_helpers=re.findall(r'^declare[^\n]*@([^ (]+)', text, re.M), commands=commands, limitations=['Static call fallthrough retained after exit/_exit; no returning termination success invented','SEH filter and handler roots are separately lifted; full handler3/unwinding/host-fault transport remains open','No required initializer, service, provider, MFC application, callback or menu is admitted by this preparation','Original instruction bytes, complete disassembly and generated IR remain private ignored artifacts'], original_executed=False, native_executed=False, whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        pin(Path(__file__)); pin(sys.executable)
        for path in out.iterdir():
            if path.is_file():
                pin(path)
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,roots=len(ENTRIES),source_PCs=report['unique_instructions'],report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),original_executed=False,native_executed=False)))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    prepare(parser.parse_args().output.resolve())
