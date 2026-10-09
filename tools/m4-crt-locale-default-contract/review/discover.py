"""Independent read-only exact default-locale prefix contract; no execution."""
import hashlib
import json
import ntpath
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[3]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
WORKAHEAD_SHA = 'cbccc6391f72121e2c9bda05b745beb6494a5e52cf9738507aa4b23f832b6188'
SPANS = (
    ('stub', 0x78003dd2, '6afde80200000059c3'),
    ('setmbcp-prefix', 0x78003ddb, '558bec83ec185356576a19e86ad2ffff'),
    ('lock-prefix', 0x78001055, '558bec8b450856833c8528700378008d348528700378740bff36ff1544e002785e5dc3576a18e833020000'),
)
PCS = [0x78003dd2, 0x78003dd4, 0x78003ddb, 0x78003ddc,
       0x78003dde, 0x78003de1, 0x78003de2, 0x78003de3,
       0x78003de4, 0x78003de6, 0x78001055, 0x78001056,
       0x78001058, 0x7800105b, 0x7800105c, 0x78001064,
       0x7800106b, 0x78001078, 0x78001079, 0x7800107b]


def need(value, why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, 'Duplicate JSON association')
            out[key] = value
        return out
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def key(path):
    return ntpath.normcase(ntpath.normpath(str(Path(path).absolute())))


def main(name):
    base = ROOT / 'reports/m4-crt-locale-default-contract/review'
    out = base / name
    need(name.startswith('source-') and out.parent == base and not out.exists(), 'Fresh independent source report')
    out.mkdir(parents=True)
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    decode = ROOT / 'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'
    old = ROOT / 'reports/m4-crt-locale-workahead/recovery-r2/report.json'
    need(sha(provider) == PROVIDER_SHA and sha(old) == WORKAHEAD_SHA, 'Exact original staged provider and frozen history')
    pe = PEImage(provider.read_bytes())
    need(pe.image_base == 0x78000000, 'Literal PE source base')
    def source(address, size):
        offset, _ = pe.rva_range(address - pe.image_base, size)
        return pe.read(offset, size)
    rows = {}
    for line in decode.read_text().splitlines():
        match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)', line)
        if match:
            pc, raw = int(match[1], 16), bytes.fromhex(match[2])
            need(source(pc, len(raw)) == raw, 'Decoded instruction agrees with current original file')
            rows[pc] = {'pc': pc, 'bytes_hex': raw.hex(), 'mnemonic': match[3],
                        'operands': match[4].split(' <')[0].replace('\t', ' ').strip()}
    spans = {}
    for label, address, hex_bytes in SPANS:
        raw = bytes.fromhex(hex_bytes)
        need(source(address, len(raw)) == raw, 'Independent literal opcode contract: ' + label)
        path = out / (label + '.bin')
        path.write_bytes(raw)
        spans[label] = {'entry': address, 'end': address + len(raw), 'bytes': len(raw), 'sha256': sha(path)}
    instructions = [rows[pc] for pc in PCS]
    need([row['pc'] for row in instructions if row['mnemonic'] == 'call'] ==
         [0x78003dd4, 0x78003de6, 0x7800107b], 'Three real source calls, not synthesized call instructions')
    for pc, target in ((0x78003dd4, 0x78003ddb), (0x78003de6, 0x78001055), (0x7800107b, 0x780012b3)):
        raw = bytes.fromhex(rows[pc]['bytes_hex'])
        need(raw[0] == 0xe8 and pc + 5 + struct.unpack('<i', raw[1:])[0] == target, 'Literal source relative CALL target')
    slot = 0x78037028 + 4 * 25
    need(slot == 0x7803708c and source(slot, 4) == bytes(4), 'File-backed zero slot selects lazy lock branch only')
    need(source(0x780012b3, 6) == bytes.fromhex('ff3550710378'), 'First unexecuted malloc instruction reads newmode global')
    need(source(0x780379e0, 257) == bytes(257), 'Table file identity, not initialization')
    # These expressions use only reviewed scheduling geometry and decoded source
    # instructions. No native State, parser output or runtime ledger is an input.
    entry = 0x2000185c
    operations = [
        (0x78003dd2, entry - 4, 0xfffffffd, 'write', 'stub selector PUSH'),
        (0x78003dd4, entry - 8, 0x78003dd9, 'write', 'stub source CALL return'),
        (0x78003ddb, entry - 12, 'incoming EBP', 'write', 'setmbcp saved EBP'),
        (0x78003de1, entry - 40, 'incoming EBX', 'write', 'setmbcp saved EBX'),
        (0x78003de2, entry - 44, 'incoming ESI', 'write', 'setmbcp saved ESI'),
        (0x78003de3, entry - 48, 'incoming EDI', 'write', 'setmbcp saved EDI'),
        (0x78003de4, entry - 52, 25, 'write', 'lock selector PUSH'),
        (0x78003de6, entry - 56, 0x78003deb, 'write', 'setmbcp source CALL return'),
        (0x78001055, entry - 60, entry - 12, 'write', 'lock saved EBP'),
        (0x78001058, entry - 52, 25, 'read', 'lock actual argument'),
        (0x7800105b, entry - 64, 'incoming ESI', 'write', 'lock saved ESI'),
        (0x7800105c, slot, 0, 'read', 'actual unchanged source zero lock slot'),
        (0x78001078, entry - 68, 'incoming EDI', 'write', 'lock saved EDI'),
        (0x78001079, entry - 72, 24, 'write', 'malloc byte-count PUSH'),
        (0x7800107b, entry - 76, 0x78001080, 'write', 'lock actual malloc CALL return'),
    ]
    accesses = [dict(pc=pc, address=address, value=value, width=4, operation=op, meaning=meaning)
                for pc, address, value, op, meaning in operations]
    report = {
        'passed': True, 'scope': 'Independent static original default-selector prefix with explicit host scheduling proposal',
        'provider_sha256': PROVIDER_SHA, 'spans': spans, 'executed_prefix_PC_order': PCS,
        'decoded_source_instructions': instructions, 'source_access_order': accesses,
        'completed_source_accesses_expected': 15, 'executed_PCs_expected': 20,
        'host_scheduling': {'parent_ESP': 0x20001860, 'entry_ESP': entry, 'entry_PC': 0x78003dd2,
                            'external_return_store': {'address': entry, 'value': 0xfffffff0},
                            'separate_from_source_accesses': True,
                            'project_only_carried_State_EIP_ESP': True,
                            'generic_Runtime_CPU_preserved_at_actual_mainargs_slot_frame': True,
                            'synthetic_Runtime_locale_call_record': False,
                            'actual_Runtime_call_records': {'root': 1, 'completed': 9, 'incomplete_mainargs': 1},
                            'original_attach_CALL_18A1_executed': False},
        'mapping_contract': {'prior_mappings': 16, 'additional_raw_source_RX_page': 0x78003000,
                             'total_mappings': 17, 'prior_mapping_permissions_and_bytes_preserved': True},
        'stop': {'PC': 0x780012b3, 'source_CALL_PC': 0x7800107b, 'frame': entry - 76,
                 'return_word': 0x78001080, 'argument_address': entry - 72, 'argument_bytes': 24,
                 'malloc_body_started': False, 'newmode_global_read': False},
        'expected_terminal_registers': {'EAX': 25, 'EBP': entry - 60, 'ESI': slot, 'ESP': entry - 76,
                                       'EBX_ECX_EDX_EDI': 'unchanged from carried input'},
        'expected_terminal_arithmetic_flags': {'CF': 0, 'PF': 1, 'AF': 0, 'ZF': 1, 'SF': 0, 'OF': 0},
        'undefined_flag_bridge_required': False,
        'native_review_requirements': [
            'Bind exact current source bytes, parent frame and whole carried State3504/FX512/Runtime CPU;16 prior mappings plus explicit raw RX78003000',
            'Host seam store is separate; first fault and every partial source store are retained',
            'Compare admitted opaque and side token values before dereferencing them, using a known live parent on rejection',
            'Freeze frame and control association; single current thread, serial depth1, one use and exclusive owners',
            'Each read/store checks exact source PC, next access ordinal, address, width and expected value before ledger append',
            'Stop only after actual malloc CALL writes return1080 and changes ESP, before malloc first newmode read',
            'No allocated buffer, initialized critical section, default codepage, table initialization or parser completion credit',
            'Preserve first-fault diagnostics through terminal observer exceptions and clear owner/depth/active with RAII',
            'Test partial PUSH/call stores, slot permission/value changes, wrong token, replay, stale side publication and observer State/FX/ledger mutation',
            'Check actual hardware raw80 and full legacy FP/x87/SSE preservation plus host LastError across clean and fault paths',
        ],
        'original_executed': False, 'native_executed': False, 'table_initialization_proved': False,
        'lock_initialized': False, 'locale_complete': False, 'whole_M4_complete': False,
    }
    before = {key(path): sha(path) for path in (Path(__file__), ROOT / 'tools/analysis/pe.py', provider, decode, old)}
    for path in out.iterdir():
        if path.is_file():
            before[key(path)] = sha(path)
    report_path = out / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    before[key(report_path)] = sha(report_path)
    pins = out / 'pins.json'
    pins.write_text(json.dumps({'files': before}, indent=2) + '\n', encoding='utf-8')
    need(all(sha(path) == value for path, value in before.items()), 'Full current physical input/output hash closure')
    print(json.dumps({'passed': True, 'report_sha256': sha(report_path), 'pins_sha256': sha(pins),
                      'source_accesses': 15, 'source_PCs': 20, 'malloc_frame': hex(entry - 76)}))


if __name__ == '__main__':
    main(sys.argv[1])
