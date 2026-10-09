"""Exact-source preparation for the CRT callback-registration leaf.

No original machine code is executed. The callback is stored as a guest DWORD,
never invoked or treated as a native pointer by this preparation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-crt'))
from recover_provider import PE, IMAGE_SHA, PROVIDER_SHA


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(out):
    need(out.is_relative_to(ROOT / 'reports/m4-crt-matherr') and not out.exists(),
         'Fresh private matherr preparation')
    game = PE(ROOT / 'MW3/Mech3.exe', IMAGE_SHA)
    provider = PE(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', PROVIDER_SHA)
    export = provider.exports()['__setusermatherr']
    need(export['address'] == 0x7800b38f, 'Actual named provider entry')
    imports = [i for i in game.imports() if i.get('name') == '__setusermatherr'
               and i['library'].lower() == 'msvcrt.dll']
    need(len(imports) == 1, 'Exact game named import ownership')
    code = provider.read(export['rva'], 17)
    need(code == bytes.fromhex('8b4424048325b892037800a3c4b00378c3'),
         'Complete actual MOV/AND/MOV/RET source')
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    lifter = ROOT / 'local/tools/remill-x87-control-repair/remill-lift-control-21.exe'
    semantics = ROOT / 'local/tools/remill-x87-control-repair/semantics/x86.bc'
    need(sha(semantics) == '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca',
         'Exact repaired semantics identity')
    out.mkdir(parents=True)
    (out / 'prepare-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        (out / 'source.bin').write_bytes(code)
        commands = []
        args = [str(llvm / 'llvm-objdump.exe'), '--disassemble', '--x86-asm-syntax=intel',
                '--start-address=0x7800b38f', '--stop-address=0x7800b3a0', str(provider.path)]
        result = subprocess.run(args, capture_output=True)
        (out / 'decode.txt').write_bytes(result.stdout + result.stderr)
        commands.append({'arguments': args, 'exit_code': result.returncode})
        need(result.returncode == 0, 'Actual source decode')
        flags = ['--arch=x86', '--os=windows', '--address=' + str(0x7800b38f),
                 '--entry_address=' + str(0x7800b38f), '--bytes=' + code.hex(),
                 '--semantics_dir=' + str(semantics.parent), '--ir_out=' + str(out / 'guest.ll')]
        # Decimal values are checked against the actual source address before launch.
        need(int(flags[2].split('=')[1]) == 0x7800b38f
             and int(flags[3].split('=')[1]) == 0x7800b38f, 'Exact lift source address')
        (out / 'flags.txt').write_text('\n'.join(flags) + '\n')
        result = subprocess.run([str(lifter), *flags], capture_output=True)
        (out / 'lift.log').write_bytes(result.stdout + result.stderr)
        commands.append({'program': str(lifter), 'flags_file': str(out / 'flags.txt'),
                         'exit_code': result.returncode})
        need(result.returncode == 0, 'Complete leaf lift')
        guest = (out / 'guest.ll').read_text()
        need(re.findall(r'^define ptr @([^ (]+)', guest, re.M) == ['sub_7800b38f']
             and '__remill_missing_block' not in guest, 'Only complete actual leaf')
        report = {'passed': True, 'scope': 'Exact source/lift preparation only; no original/native execution acceptance',
                  'provider_export': export, 'game_import': imports[0],
                  'entry': 0x7800b38f, 'end_exclusive': 0x7800b3a0,
                  'source_sha256': sha(out / 'source.bin'), 'guest_IR_sha256': sha(out / 'guest.ll'),
                  'argument_bytes': 4, 'callee_pop_bytes': 0,
                  'zeroed_global': 0x780392b8, 'callback_pointer_global': 0x7803b0c4,
                  'defined_flags_mask': 0x8c5, 'defined_flags_result': 0x44,
                  'undefined_AF_excluded': True, 'callback_invoked': False,
                  'commands': commands, 'whole_M4_complete': False}
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        inputs = [Path(__file__), ROOT / 'tools/m4-crt/recover_provider.py', game.path,
                  provider.path, lifter, semantics, llvm / 'llvm-objdump.exe']
        files = {str(p): sha(p) for p in inputs}
        files.update({str(p): sha(p) for p in out.iterdir() if p.is_file()})
        (out / 'pins.json').write_text(json.dumps({'files': files}, indent=2) + '\n')
        print(json.dumps({'passed': True, 'source_bytes': 17, 'report_sha256': sha(out / 'report.json')}))
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('output', type=Path)
    main(p.parse_args().output.resolve())
