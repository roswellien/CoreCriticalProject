"""Exact additive FDIV writer lift. No original or native code execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-fdiv'
sys.path.insert(0, str(ROOT / 'tools/m4-crt-control-integration'))
from prepare import PE

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
RECOVERY_SHA = 'c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd'
SEMANTICS_SHA = '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca'
ENTRIES = (0x78004254, 0x7800426B, 0x780042A3, 0x780042CF,
           0x7802C070, 0x780042E1, 0x780042F7, 0x7800432C, 0x7800439F)


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def prepare(out):
    require(out.parent == BASE and not out.exists(), 'Fresh immediate private preparation required')
    recovery = BASE / 'source-recovery-r1/report.json'
    require(sha(recovery) == RECOVERY_SHA, 'Frozen exact writer recovery required')
    recovered = json.loads(recovery.read_text())
    provider_path = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = PE(provider_path, PROVIDER_SHA, 0x78000000)
    require(pe.export('_adjust_fdiv')['address'] == 0x78037C2C, 'Exact provider data export')
    for slot, name, raw in ((0x7802E098, 'GetModuleHandleA', 0x345D2),
                           (0x7802E0D0, 'GetProcAddress', 0x346AC)):
        owner = pe.import_slot(slot)
        require(owner['library'].lower() == 'kernel32.dll' and owner['name'] == name
                and owner['original_iat_value'] == raw, 'Exact provider API ownership')
    dense = bytearray([0xCC] * (0x7802C0AE - 0x78004254))
    ranges = []
    pages = {}
    for item in recovered['source_spans']:
        va, size = item['address'], item['size_bytes']
        data = pe.bytes(va, size, True)
        require(hashlib.sha256(data).hexdigest() == item['sha256'], 'Literal recovered RX source')
        dense[va - 0x78004254:va - 0x78004254 + size] = data
        ranges.append(item)
        for index, value in enumerate(data):
            address = va + index
            pages.setdefault(address & ~4095, bytearray([0xCC] * 4096))[address & 4095] = value
    # Import metadata and source strings share the original readonly IAT page.
    pages[0x7802E000] = bytearray(pe.bytes(0x7802E000, 4096))
    pages[0x78037000] = bytearray(pe.bytes(0x78037000, 4096))
    permissions = {p: 5 for p in pages}
    permissions[0x7802E000] = 1
    permissions[0x78037000] = 3
    # Three fallback operands are exact readonly slices; no expected arithmetic.
    constants = bytearray([0xCC] * 4096)
    for item in recovered['fallback_constants']:
        data = pe.bytes(item['address'], 8)
        require(hashlib.sha256(data).hexdigest() == item['sha256'], 'Literal fallback constant')
        # 7802FFC8 is on a distinct page from the two 780300xx operands.
        p = item['address'] & ~4095
        pages.setdefault(p, bytearray([0xCC] * 4096))[item['address'] & 4095:(item['address'] & 4095) + 8] = data
        permissions[p] = 1
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    lift = ROOT / 'local/tools/remill-x87-control-repair/remill-lift-control-21.exe'
    semantics = ROOT / 'local/tools/remill-x87-control-repair/semantics/x86.bc'
    require(sha(semantics) == SEMANTICS_SHA, 'Frozen repaired semantics')
    out.mkdir(parents=True)
    (out / 'prepare-source.py').write_bytes(Path(__file__).read_bytes())
    (out / 'dense-lift.bin').write_bytes(dense)
    pack = b'MW4FDIP1' + struct.pack('<I', len(pages)) + b''.join(
        struct.pack('<II', p, permissions[p]) + pages[p] for p in sorted(pages))
    (out / 'pack.bin').write_bytes(pack)
    commands = []

    def run(program, arguments, log):
        result = subprocess.run([str(program), *arguments], capture_output=True)
        (out / log).write_bytes(result.stdout + result.stderr)
        commands.append(dict(program=str(program), arguments=arguments,
                             exit_code=result.returncode, log=str(out / log)))
        require(result.returncode == 0, 'Required static preparation command')

    try:
        for entry in ENTRIES:
            flags = ['--arch=x86', '--os=windows', '--address=' + str(0x78004254),
                     '--entry_address=' + str(entry), '--bytes=' + dense.hex(),
                     '--semantics_dir=' + str(semantics.parent),
                     '--ir_out=' + str(out / f'guest-{entry:x}.ll')]
            flags_path = out / f'flags-{entry:x}.txt'
            flags_path.write_text('\n'.join(flags) + '\n')
            run(lift, ['--flagfile=' + str(flags_path)], f'lift-{entry:x}.log')
        run(llvm / 'llvm-link.exe', [*(str(out / f'guest-{entry:x}.ll') for entry in ENTRIES),
                                    '-S', '-o', str(out / 'guest.ll')], 'link.log')
        run(llvm / 'opt.exe', ['-passes=verify', '-disable-output', str(out / 'guest.ll')], 'verify.log')
        text = (out / 'guest.ll').read_text()
        definitions = set(re.findall(r'^define ptr @([^ (]+)', text, re.M))
        require(definitions == {f'sub_{entry:x}' for entry in ENTRIES}, 'Exact nine complete original routine definitions')
        require('__remill_missing_block' not in text, 'No missing original CFG block')
        externs = re.findall(r'^declare[^\n]*@([^ (]+)', text, re.M)
        report = dict(passed=True, scope='Exact static nine-body writer/dependency lift; no execution or initialized data acceptance',
                      provider_sha256=PROVIDER_SHA, recovery_sha256=RECOVERY_SHA, entries=list(ENTRIES),
                      source_ranges=ranges, source_instruction_union=recovered['unique_writer_dependency_instructions'],
                      pack_sha256=sha(out / 'pack.bin'), pages=[dict(address=p, permissions=permissions[p]) for p in sorted(pages)],
                      guest_sha256=sha(out / 'guest.ll'), semantics_sha256=SEMANTICS_SHA,
                      external_helpers=externs, commands=commands, original_executed=False, native_executed=False,
                      whole_M4_complete=False)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        inputs = [Path(__file__), ROOT / 'tools/m4-crt-control-integration/prepare.py', recovery,
                  provider_path, semantics, lift, llvm / 'llvm-link.exe', llvm / 'opt.exe']
        files = {str(p): sha(p) for p in inputs}
        files.update({str(p): sha(p) for p in out.iterdir() if p.is_file()})
        (out / 'pins.json').write_text(json.dumps(dict(files=files), indent=2) + '\n')
        print(json.dumps(dict(passed=True, nine_complete_CFGs=True, external_helpers=externs,
                              report_sha256=sha(out / 'report.json'))))
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    prepare(parser.parse_args().output.resolve())
