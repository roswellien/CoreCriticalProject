"""Recover the complete physical three-FCOS root as unadapted guest IR."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or expected == value, (path, expected, value)
        assert str(path) not in pins or pins[str(path)] == value
        pins[str(path)] = value
        return path

    prep_path = pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/report.json',
                    'aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df')
    prep = json.loads(prep_path.read_bytes())
    assert prep['passed'] and prep['source_instruction_rows'] == 19
    contracts = json.loads(pin(prep_path.parent / 'instruction-contracts.json').read_bytes())
    sys.path.insert(0, str(ROOT / 'tools/analysis'))
    from pe import PEImage
    pin(ROOT / 'tools/analysis/pe.py')
    game_path = pin(ROOT / 'MW3/Mech3.exe',
                    '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    pe = PEImage(game_path.read_bytes())
    for row in contracts['instructions']:
        offset, _ = pe.rva_range(row['pc'] - pe.image_base, row['width'])
        assert pe.data[offset:offset + row['width']] == bytes.fromhex(row['bytes_hex'])
    start = contracts['source_span']['start']
    end = contracts['source_span']['end_exclusive']
    offset, _ = pe.rva_range(start - pe.image_base, end - start)
    code = pe.data[offset:offset + end - start]
    assert len(code) == 121 and code[5:16] == b'\x90' * 11
    (out / '4b64f0.bin').write_bytes(code)
    repair_path = pin(ROOT / 'reports/x87-repair/toolchain/repair.json')
    repair = json.loads(repair_path.read_bytes())
    lifter = pin(repair['remill_lifter_path'],
                 'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38')
    semantics = pin(repair['repaired_semantics_path'],
                    '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca')
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    commands = []

    def run(name, args):
        result = subprocess.run(list(map(str, args)), cwd=ROOT, capture_output=True, timeout=60)
        (out / (name + '.stdout')).write_bytes(result.stdout)
        (out / (name + '.stderr')).write_bytes(result.stderr)
        commands.append(dict(command=list(map(str, args)), exit_code=result.returncode))
        assert result.returncode == 0, name

    guest = out / '4b64f0.ll'
    run('lift', [lifter, '--arch=x86', '--os=windows', f'--address={start}',
                 '--bytes=' + code.hex(), '--semantics_dir=' + str(semantics.parent),
                 '--ir_out=' + str(guest)])
    run('assemble', [pin(llvm / 'llvm-as.exe'), guest, '-o', out / '4b64f0.bc'])
    run('verify', [pin(llvm / 'opt.exe'), '-passes=verify', '-disable-output', out / '4b64f0.bc'])
    source = guest.read_text()
    assert re.findall(r'^define .*?@([^ (]+)', source, re.M) == ['sub_4b64f0']
    assert len(re.findall(r'call x86_fp80 @cosl', source)) == 3
    pin(__file__)
    for path in out.iterdir():
        pin(path)
    report = dict(passed=True, scope='Exact physical compound three-FCOS guest IR only',
                  root=start, source_instruction_rows=19, reachable_source_bytes=110,
                  contiguous_source_bytes=121, guest_IR=str(guest), guest_IR_sha256=sha(guest),
                  source_contracts=str(prep_path.parent / 'instruction-contracts.json'),
                  source_contracts_sha256=sha(prep_path.parent / 'instruction-contracts.json'),
                  FCOS_count=3, commands=commands, native_executed=False,
                  initializer_credit=0, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), guest_IR=str(guest))))


if __name__ == '__main__':
    main(sys.argv[1])
