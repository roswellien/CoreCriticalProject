"""Independent exact-source parser prefix contract; no original/native run."""
import hashlib, json, pathlib, re, struct, subprocess, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-parser-prefix'
FILES = {}

def need(value, why):
    if not value:
        raise ValueError(why)

def pin(path):
    path = pathlib.Path(path).absolute()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    need(str(path) not in FILES or FILES[str(path)] == digest, 'Unchanged source binding')
    FILES[str(path)] = digest
    return raw

class PE:
    def __init__(self, path):
        self.raw = pin(path)
        pe = struct.unpack_from('<I', self.raw, 0x3c)[0]
        need(self.raw[:2] == b'MZ' and self.raw[pe:pe+4] == b'PE\0\0', 'Source PE signature')
        machine, count, _, _, _, size, _ = struct.unpack_from('<HHIIIHH', self.raw, pe+4)
        opt = pe+24
        need(machine == 0x14c and struct.unpack_from('<H', self.raw, opt)[0] == 0x10b, 'Literal x86 PE32 source')
        self.base = struct.unpack_from('<I', self.raw, opt+28)[0]
        self.sections = []
        for n in range(count):
            p = opt+size+40*n
            virtual, rva, raw_size, offset = struct.unpack_from('<IIII', self.raw, p+8)
            permission = struct.unpack_from('<I', self.raw, p+36)[0] & 0xe0000000
            self.sections.append((rva, virtual, raw_size, offset, permission))

    def read(self, address, size):
        rva = address-self.base
        matches = [s for s in self.sections if s[0] <= rva and rva+size <= s[0]+s[2]]
        need(len(matches) == 1, 'Unique complete raw-backed parser source')
        section = matches[0]
        offset = section[3]+rva-section[0]
        return self.raw[offset:offset+size]

def main(output):
    need(output.parent == BASE and output.name.startswith('independent-') and not output.exists(), 'Fresh independent source receipt')
    output.mkdir(parents=True)
    provider = ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = PE(provider)
    need(FILES[str(provider)] == '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7', 'Exact provider authority')
    source = pe.read(0x7800bc48, 436)
    need(hashlib.sha256(source).hexdigest() == 'b372b4c114b8ecb170208ad508f2541c73262c3b44cfa2e7626e06a5be61fd8b', 'Exact complete436-byte parser')
    tool = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    pin(tool)
    command = [str(tool), '--disassemble', '--x86-asm-syntax=intel', str(provider)]
    result = subprocess.run(command, capture_output=True)
    need(result.returncode == 0, 'Fresh tool-only source decode')
    (output/'provider-decode.stdout').write_bytes(result.stdout)
    (output/'provider-decode.stderr').write_bytes(result.stderr)
    rows = []
    for line in result.stdout.decode().splitlines():
        match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)', line)
        if match and 0x7800bc48 <= int(match[1], 16) < 0x7800bdfc:
            pc = int(match[1], 16)
            raw = bytes.fromhex(match[2])
            need(pe.read(pc, len(raw)) == raw, 'Every freshly decoded instruction matches physical source')
            rows.append(dict(pc=pc, bytes=raw.hex(), mnemonic=match[3], operands=match[4].split(' <')[0].strip()))
    need(b''.join(bytes.fromhex(row['bytes']) for row in rows) == source, 'All436 source bytes decoded exactly')
    need(not any(row['mnemonic'] == 'call' for row in rows), 'Literal parser has no outgoing source CALL')
    code = {row['pc']: row for row in rows}
    path = [0x7800bc48,0x7800bc49,0x7800bc4b,0x7800bc4e,0x7800bc51,0x7800bc52,0x7800bc53,0x7800bc56,0x7800bc59,0x7800bc5a,0x7800bc5d,0x7800bc63,0x7800bc66,0x7800bc68,0x7800bc72,0x7800bc75,0x7800bcd5,0x7800bcd7,0x7800bcd9,0x7800bce0,0x7800bce2,0x7800bce3,0x7800bce6]
    need(code[0x7800bc53]['bytes'] == '832100' and code[0x7800bc5d]['bytes'] == 'c70001000000', 'Source ANDzero and count-one stores')
    need(code[0x7800bce6]['bytes'] == 'f683e179037804', 'Actual first unquoted lead-byte classification load')
    need(pe.read(0x780379e0, 257) == bytes(257), 'Uninitialized source-file table identity only')
    witness_path = ROOT/'reports/m4-crt-commandline-carry/root-execution-r1/native-O0/row-0/commandline-api-bytes.bin'
    witness = pin(witness_path)
    need(witness[0] == 0x44 and witness[-1] == 0 and not 0 in witness[:-1], 'Frozen D-leading actual input selects this static path')
    workahead = ROOT/'reports/m4-crt-mainargs/recovery-r3'
    guest = pin(workahead/'normal_parser-guest.ll')
    host = pin(workahead/'normal_parser-host.ll')
    need(b'define ptr @sub_7800bc48(' in guest and b'define ptr @mw34_mainargs_normal_parser_body(' in host and b'@mw34_mainargs_normal_parser_undefined_8()' in host, 'Prior static complete parser and typed-symbol workahead association')
    for name in ('normal_parser-source.bin','normal_parser-O0.obj','normal_parser-O2.obj'):
        pin(workahead/name)
    need(pin(workahead/'normal_parser-source.bin') == source, 'Static object source is same complete436 bytes')
    pin(__file__)
    for p in output.iterdir():
        if p.is_file():
            pin(p)
    # Values on entry come from the real preceding CALL. Saved register values
    # stay symbolic until BEFORE-derived/runtime evidence is supplied.
    accesses = [
        (0x7800bc48,0x20001828,'incoming EBP',4,1),
        (0x7800bc4b,0x20001840,0x2000184c,4,0),
        (0x7800bc4e,0x2000183c,0x20001850,4,0),
        (0x7800bc51,0x20001824,'incoming EBX',4,1),
        (0x7800bc52,0x20001820,0x7803b3f0,4,1),
        (0x7800bc53,0x2000184c,'preexisting local value',4,0),
        (0x7800bc53,0x2000184c,0,4,1),
        (0x7800bc56,0x20001838,0,4,0),
        (0x7800bc59,0x2000181c,0x33000000,4,1),
        (0x7800bc5a,0x20001834,0,4,0),
        (0x7800bc5d,0x20001850,1,4,1),
        (0x7800bc63,0x20001830,0x33000000,4,0),
        (0x7800bc72,0x33000000,0x44,1,0),
        (0x7800bcd5,0x2000184c,0,4,0),
        (0x7800bcd5,0x2000184c,1,4,1),
        (0x7800bce0,0x33000000,0x44,1,0)]
    for p, digest in FILES.items():
        need(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() == digest, 'Final physical source closure')
    report = dict(passed=True, scope='Independent exact source/decode and prefix ABI prerequisite; candidate execution pending',
        source_begin=0x7800bc48, source_end=0x7800bdfc, source_bytes=436, source_sha256=hashlib.sha256(source).hexdigest(),
        decoded_instructions=rows, current_D_leading_path=path, visited_PCs_including_stop=23,
        successful_accesses_before_locale=16, accesses=accesses, required_stop_PC=0x7800bce6, required_stop_address=0x78037a25,
        stop_before_locale_load=True, locale_table_initialized=False, TEST_AF_representative_PCs=[0x7800bc66,0x7800bcd7],
        stop_registers=dict(EAX=0x33000001,EBX=0x44,ECX=0x2000184c,EDX='incoming upper24 bits with DL44',ESI=0,EDI=0,EBP=0x20001828,ESP=0x2000181c),
        locals=dict(character_count_at=0x2000184c,character_count=1,argument_slots_at=0x20001850,argument_slots=1),
        actual_call_frame=0x2000182c, real_return=0x7800bbfc, args=[0x33000000,0,0,0x20001850,0x2000184c],
        partial_order=['Each actual PUSH writes before ESP publication','ANDzero reads old count then writes0 before flags','INCcount reads old count then writes increment before flags','BCE0 reads input before DL publication','BCE2 increments EAX before locale dependency','No locale load or parser RET executes'],
        command=dict(argv=command,exit_code=result.returncode), files=FILES, native_worker_executed=False, original_executed=False, game_launched=False,
        argument_outputs=False, complete_sizing=False, parser_RET=False, whole_M4_complete=False)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=True,source_bytes=436,successful_accesses=16,required_stop_PC=hex(0x7800bce6))))

if __name__ == '__main__':
    need(len(sys.argv) == 2, 'recover_contract.py fresh independent output directory')
    main(pathlib.Path(sys.argv[1]).absolute())
