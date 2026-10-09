"""Fresh, bounded original-byte recovery; never executes the provider or game."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-locale-default-recovery'
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
PREVIOUS_SHA = 'cbccc6391f72121e2c9bda05b745beb6494a5e52cf9738507aa4b23f832b6188'
PARSER_ACCEPT_SHA = 'b78c296b69dc15abf6b88d4901c8742875ca25de417497233e0687ee2704b964'
SPANS = (
    ('attach-scheduling', 0x7800188c, 0x780018a6),
    ('default-stub', 0x78003dd2, 0x78003ddb),
    ('setmbcp-hot', 0x78003ddb, 0x78003e84),
    ('resolver-hot', 0x78003e84, 0x78003eb1),
    ('lock', 0x78001055, 0x780010b0),
    ('lock-cold', 0x7800bba4, 0x7800bbbc),
    ('unlock', 0x7800129e, 0x780012b3),
    ('malloc-frontier', 0x780012b3, 0x78001300),
    ('setmbcp-cold', 0x7800e4e4, 0x7800e615),
    ('codepage-to-lcid', 0x7800e615, 0x7800e648),
    ('explicit-singlebyte-reset', 0x7800e648, 0x7800e671),
)
PREFIX_PCS = [
    0x78003dd2, 0x78003dd4, 0x78003ddb, 0x78003ddc, 0x78003dde,
    0x78003de1, 0x78003de2, 0x78003de3, 0x78003de4, 0x78003de6,
    0x78001055, 0x78001056, 0x78001058, 0x7800105b, 0x7800105c,
    0x78001064, 0x7800106b, 0x78001078, 0x78001079, 0x7800107b,
]


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def main(name):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'recovery-r[1-9][0-9]*', name), 'Simple fresh recovery name')
    out = workspace_path(BASE / name, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate recovery output')
    source = ROOT / 'tools/m4-crt/recover_provider.py'
    spec = importlib.util.spec_from_file_location('locale_default_pe', source)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = mod.PE(provider, PROVIDER_SHA)
    tool = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    previous = ROOT / 'reports/m4-crt-locale-workahead/recovery-r2/report.json'
    accepted = ROOT / 'reports/m4-crt-parser-prefix/root-acceptance-r1/report.json'
    need(sha(previous) == PREVIOUS_SHA and sha(accepted) == PARSER_ACCEPT_SHA, 'Frozen prior static and accepted parser receipts')
    need(read_json(accepted)['passed'] is True, 'Accepted bounded parser receipt')
    exports = pe.exports()
    imports = pe.imports()
    need(exports['_setmbcp']['address'] == 0x78003ddb, 'Original exported _setmbcp identity')
    need(exports['_lock']['address'] == 0x78001055, 'Original exported _lock identity')
    need(exports['malloc']['address'] == 0x780012b3, 'Original exported malloc identity')
    files = {}

    def add(path, expected=None):
        path = Path(path).absolute()
        key = normalized(str(path))
        digest = sha(path) if expected is None else expected
        need(key not in files or files[key] == digest, 'Stable unique binding ' + str(path))
        files[key] = digest
        return path

    for path in (Path(__file__), Path(__file__).with_name('README.md'), source,
                 provider, tool, previous, accepted, Path(sys.executable),
                 ROOT / 'tools/m4-pipeline/manifests.py', ROOT / 'tools/m4-pipeline/paths.py'):
        add(path)
    initial_check = verify_manifest(files)
    out.mkdir(parents=True)

    def section(address, count):
        rows = [s for s in pe.sections if s[0] <= address - pe.base
                and address - pe.base + count <= s[0] + s[2]]
        need(len(rows) == 1, 'Unique file-backed section extent')
        rva, virtual, raw, offset, flags = rows[0]
        return dict(rva=rva, virtual_bytes=virtual, raw_bytes=raw, raw_offset=offset,
                    permissions=flags & 0xe0000000,
                    executable=bool(flags & 0x20000000), readable=bool(flags & 0x40000000),
                    writable=bool(flags & 0x80000000))

    spans = {}
    instructions = {}
    commands = []
    for label, start, end in SPANS:
        command = [str(tool), '-d', '--x86-asm-syntax=intel',
                   '--start-address=' + hex(start), '--stop-address=' + hex(end), str(provider)]
        result = subprocess.run(command, capture_output=True, timeout=60)
        stdout = out / (label + '-decode.stdout')
        stderr = out / (label + '-decode.stderr')
        publish_bytes(stdout, result.stdout)
        publish_bytes(stderr, result.stderr)
        need(result.returncode == 0, 'Fresh selected-span disassembly succeeded')
        rows = []
        for line in result.stdout.decode('utf-8').splitlines():
            match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)', line)
            if match:
                pc = int(match[1], 16)
                code = bytes.fromhex(match[2])
                need(start <= pc < end and pc + len(code) <= end, 'Bounded decoded instruction')
                need(pe.read(pc - pe.base, len(code)) == code, 'Decoded bytes match exact original PE')
                row = dict(pc=pc, bytes_hex=code.hex(), mnemonic=match[3],
                           operands=match[4].split(' <')[0].replace('\t', ' ').strip())
                need(pc not in instructions or instructions[pc] == row, 'No contradictory decode')
                instructions[pc] = row
                rows.append(row)
        code = pe.read(start - pe.base, end - start)
        need(b''.join(bytes.fromhex(row['bytes_hex']) for row in rows) == code,
             'Complete contiguous source span ' + label)
        need([row['pc'] for row in rows] == sorted(row['pc'] for row in rows), 'Decoded source order')
        path = out / (label + '.bin')
        publish_bytes(path, code)
        for artifact in (stdout, stderr, path):
            add(artifact)
        spans[label] = dict(start=start, end_exclusive=end, bytes=len(code), sha256=sha(path),
                            instructions=rows, section=section(start, len(code)))
        commands.append(dict(argv=command, exit_code=result.returncode,
                             stdout=str(stdout), stderr=str(stderr), provider_body_executed=False))

    def exact(pc, code):
        need(instructions[pc]['bytes_hex'] == code, 'Exact key instruction ' + hex(pc))

    for pc, code in ((0x780018a1, 'e82c250000'), (0x78003dd2, '6afd'),
                     (0x78003dd4, 'e802000000'), (0x78003de4, '6a19'),
                     (0x78003de6, 'e86ad2ffff'), (0x7800105c, '833c852870037800'),
                     (0x78001079, '6a18'), (0x7800107b, 'e833020000')):
        exact(pc, code)
    prefix_rows = [instructions[pc] for pc in PREFIX_PCS]
    data = {}
    for label, address, count in (
            ('lock-slots-file-identity', 0x78037028, 32 * 4),
            ('mbctype-file-identity', 0x780379e0, 257),
            ('codepage-descriptors', 0x780378d0, 240),
            ('codepage-metadata-file-identity', 0x780379c0, 0x20),
            ('extra-metadata-file-identity', 0x78037ae4, 8),
            ('newmode-file-identity', 0x78037150, 4)):
        raw = pe.read(address - pe.base, count)
        path = out / (label + '.bin')
        publish_bytes(path, raw)
        add(path)
        data[label] = dict(address=address, bytes=count, sha256=sha(path), section=section(address, count))
    slot25 = struct.unpack('<I', pe.read(0x7803708c - pe.base, 4))[0]
    slot17 = struct.unpack('<I', pe.read(0x7803706c - pe.base, 4))[0]
    need(slot25 == 0 and slot17 != 0, 'Exact source-file lock slots')
    table = pe.read(0x780379e0 - pe.base, 257)
    need(table == bytes(257), 'Uninitialized source-file table identity only')
    owners = []
    for iat in (0x7802e03c, 0x7802e044, 0x7802e048, 0x7802e0c4, 0x7802e0c8, 0x7802e0cc):
        found = [item for item in imports if item['iat'] == iat]
        need(len(found) == 1, 'Unique original API import owner')
        owners.append(dict(**found[0], raw_IAT=struct.unpack('<I', pe.read(iat - pe.base, 4))[0],
                           section=section(iat, 4)))

    # Affine addresses are relative to a declared live initializer entry ESP S.
    # No source machine state, API outcome, flag or page is invented here.
    accesses = [
        (0x78003dd2, 'S-4', True, '0xfffffffd'),
        (0x78003dd4, 'S-8', True, '0x78003dd9'),
        (0x78003ddb, 'S-12', True, 'entry.EBP'),
        (0x78003de1, 'S-40', True, 'entry.EBX'),
        (0x78003de2, 'S-44', True, 'entry.ESI'),
        (0x78003de3, 'S-48', True, 'entry.EDI'),
        (0x78003de4, 'S-52', True, '25'),
        (0x78003de6, 'S-56', True, '0x78003deb'),
        (0x78001055, 'S-60', True, 'S-12'),
        (0x78001058, 'S-52', False, '25'),
        (0x7800105b, 'S-64', True, 'entry.ESI'),
        (0x7800105c, '0x7803708c', False, '0'),
        (0x78001078, 'S-68', True, 'entry.EDI'),
        (0x78001079, 'S-72', True, '24'),
        (0x7800107b, 'S-76', True, '0x78001080'),
    ]
    ledger = [dict(ordinal=i + 1, pc=pc, address_expression=address, bytes=4,
                   write=write, value_expression=value)
              for i, (pc, address, write, value) in enumerate(accesses)]
    need(len(PREFIX_PCS) == 20 and len(ledger) == 15, 'Exact default-prefix path and source access inventory')
    report = dict(
        passed=True, scope='Fresh static original default-locale path through its first malloc CALL frontier',
        provider_sha256=PROVIDER_SHA, provider_base=pe.base, previous_static_sha256=PREVIOUS_SHA,
        accepted_parser_sha256=PARSER_ACCEPT_SHA, spans=spans, commands=commands, data=data,
        API_owners=owners,
        default_path=dict(entry=0x78003dd2, selector=-3, selector_DWORD=0xfffffffd,
                          original_attach_call=0x780018a1, original_attach_return=0x780018a6,
                          original_predecessor_call=0x78001897, original_predecessor_target=0x78003d9a,
                          original_predecessor_return=0x7800189c,
                          predecessor_result_store=0x7800189c,
                          original_attach_executed=False,
                          source_instruction_count=20, source_instructions=prefix_rows,
                          successful_source_memory_accesses=15, accesses=ledger,
                          external_API_calls=0, locale_table_accesses=0, resolved_codepage=False),
        CALL_frames=[
            dict(site=0x78003dd4, target=0x78003ddb, return_word=0x78003dd9,
                 target_ESP='S-8', argument_address='S-4', argument=0xfffffffd, convention='cdecl'),
            dict(site=0x78003de6, target=0x78001055, return_word=0x78003deb,
                 target_ESP='S-56', argument_address='S-52', argument=25, convention='cdecl'),
            dict(site=0x7800107b, target=0x780012b3, return_word=0x78001080,
                 target_ESP='S-76', argument_address='S-72', argument=24, convention='cdecl'),
        ],
        first_unresolved_frontier=dict(call_site=0x7800107b, target=0x780012b3,
            refuse_before_target_body=True, actual_return_word=0x78001080,
            EIP=0x780012b3, ESP='S-76', EBP='S-60', EAX=25, ESI=0x7803708c,
            EBX='entry.EBX', ECX='entry.ECX', EDX='entry.EDX', EDI='entry.EDI',
            flags=dict(CF=0, PF=1, AF=0, ZF=1, SF=0, OF=0,
                       defining_PC=0x7800105c, other_flags='entry flags retained; DF is not consumed in this prefix'),
            source_CALL_memory_write_completed=True, malloc_executed=False,
            allocator_result_or_RETURN_proved=False, lock_acquired_or_published=False),
        lock_storage=dict(slot_base=0x78037028, admitted_lock_id=25,
            slot25_address=0x7803708c, slot25_file_DWORD=slot25,
            slot17_address=0x7803706c, slot17_file_DWORD=slot17,
            file_bytes_prove_initialized_critical_sections=False,
            first_return_dependency='malloc(24) at real CALL107B; do not substitute a native generic allocation result',
            subsequent_dependencies=[
                'NULL malloc outcome branches1085 to _amsg_exit17 at BBA6→BADB',
                'Non-NULL malloc outcome calls lock17 at108D→1055 before slot25 publication',
                'Under lock17, source slot25 reread1092 selects InitializeCriticalSection IAT2E03C at109D or free1390 atBBB1',
                'Publication store10A3 precedes unlock17 CALL10A7→129E',
                'Source jumps10AE→106D and enters lock25 via IAT2E044 at106F',
                'Lock helper RET1077 restores savedESI/EBP and reads actualreturn3DEB; it leaves lock25 held',
                'No source lock/API/body may be admitted from a nonzero file pointer alone',
            ]),
        default_initialization_dependencies=[
            'Reviewed allocation/lock initialization/publication/enter/leave/failure/free ownership',
            'Malloc source12B3 reads newmode37150 and calls12C5; source12E3 reaches FS:0 SEH read/write12F2/12F9 before heap dispatch',
            'Only after actual lock25 RETURN3DEB does selector resolver3DEE→3E84 run',
            'Selector−3 records37AE8=1 and tailcalls actual GetACP via IAT2E0C8 at3EAB',
            'Resolved codepage compares against live379C0; equal branch cannot prove initialized table if prior ownership is absent',
            'Otherwise built-in descriptors932/936/949/950/1361 or actual GetCPInfo results drive table stores',
            'Full classification helper3EB1 and its string type/locale map dependencies remain separately unclosed',
        ],
        RET_contracts=dict(
            default_stub=dict(RET_PC=0x78003dda, required_prior_setmbcp_return=0x78003dd9,
                              pop_ECX_PC=0x78003dd9, after_RET_ESP='S+4', return_word='actual entry return word at S',
                              ECX_after='0xfffffffd from source selector pop', EAX_after='actual _setmbcp outcome'),
            setmbcp=dict(RET_PC=0x78003e83, common_epilogue=0x78003e75,
                          unlock25_call=0x78003e77, unlock25_return=0x78003e7c,
                          returned_status='EAX=ESI from reviewed source branch outcome',
                          saved_nonvolatiles='EDI/ESI/EBX restored; LEAVE restores actual prior EBP; cdecl selector remains on stack'),
            lock=dict(RET_PC=0x78001077, return_word=0x78003deb,
                      restored='ESI and EBP from actual saved source words',
                      retained_lock_id_argument_at='S-52', native_lock_ownership_required=True)),
        smallest_admissible_native_experiment=dict(
            kind='Explicitly scheduled default-locale initializer subexperiment, isolated x64 original-byte translation',
            source_entries=[0x78003dd2, 0x78003ddb, 0x78001055],
            terminal=0x780012b3, terminal_reason='Required original malloc/lock allocation remains unresolved',
            source_instruction_count=20, completed_source_memory_accesses=15,
            frame_depth_bytes=76, preconditions=[
                'Use a fresh healthy accepted carried State3504/FX512 and its existing owned mappings; never reset the poisoned parser-stop binding or seed a second machine state',
                'Declare explicit scheduling site and live ESP S/return-word ownership; do not label an artificial schedule as original attach CALL18A1',
                'The live stack contains sufficient checked writable extent S−76 through S−1; preserve all unread locals and actual entry return word',
                'Exact source byte ownership for all admitted bodies; slot25 live value must equal the admitted file-start lifecycle value0 and be readonly for this bounded prefix',
                'Complete genuine CALL stores3DD4/3DE6/107B and enforce frames/arguments/return-word checks from current typed owner',
                'Deny source dispatch outside the admitted path, nonzero/stale lockslot, malformed owner/token/frame, permission/range violations, observer mutation or exception; preserve the first fault and cleanup on unwind',
                'Compare full State/FX/RuntimeCPU/all pre-existing mappings against a separate original-byte model and preserve actual host FP/LastError',
                'Stop at12B3 before its first global read/push; retain source CALL1080/argument24 and all partial stores without manufacturing allocator/lock/API success',
            ],
            grants=['Real default-selector push and nested translated CALL frames', 'Real _setmbcp prologue and lock25 lazy-allocation source prefix'],
            withholds=['Original attach/DllMain order', 'Allocator execution or result', 'Initialized/acquired lock25/17',
                       'GetACP/GetCPInfo or resolved default codepage', 'Initialized lead-byte table',
                       'Any initializer or parser RET', 'Full parser sizing/output', 'M4 or native game completion']),
        alternative_reset=dict(entry=0x7800e648, end_exclusive=0x7800e671,
            import_free=True, called_directly_by_default_stub=False,
            source_call_site=0x7800e5de, source_return=0x7800e5e3,
            conditional_source_reachability=[
                'Resolved codepage zero at3E04 branches toE5DE',
                'GetCPInfo result!=1 branches3E34→E5D5; nonzero default-selector marker37AE8 selectsE5DE',
                'Its conditional original call still requires the earlier actual lock/resolver/API lifecycle; direct bootstrap use is a separately declared schedule',
            ],
            required_domain='Explicit separately reviewed C/single-byte bootstrap schedule; never substitute for selector−3/defaultACP path',
            preconditions=['DF must be0 in carried state; REP/STOS uses source ES/flat guest-memory contract',
                           'Writable owned full257-byte table plus metadata379C0/379C8/379CC/379D0/379D4/37AE4',
                           'Actual source stack stores/pops/RET and EDI save/restore must be retained',
                           'Checked bounded REP stores and current typed initializer owner; lifecycle/generation establishes table producer provenance'],
            actual_table_store_bytes=257, actual_metadata_store_bytes=24,
            metadata_stores=[0x780379c0, 0x780379d4, 0x78037ae4, 0x780379c8, 0x780379cc, 0x780379d0],
            metadata_not_written=[0x78037ae8],
            native_admitted=False, default_ANSI_codepage_proved=False, attach_proved=False),
        source_file_zeros_are_initialization_proof=False,
        original_executed=False, game_executed=False, native_executed=False,
        locale_initialized=False, parser_sizing_completed=False, whole_M4_complete=False,
        selected_initializer_coverage_unchanged=dict(selected=27, inventory=144),
        historical_receipts_recursively_expanded=False,
        initial_dependency_check=initial_check,
    )
    report['final_dependency_check'] = verify_manifest(files)
    report['elapsed_seconds'] = (time.perf_counter_ns() - started) / 1e9
    report['files'] = dict(sorted(files.items()))
    report_path = out / 'report.json'
    publish_bytes(report_path, (json.dumps(report, indent=2) + '\n').encode())
    add(report_path)
    publish_bytes(out / 'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2) + '\n').encode())
    print(json.dumps(dict(passed=True, report=str(report_path), report_sha256=sha(report_path),
                         pins_sha256=sha(out / 'pins.json'), source_instruction_count=20,
                         completed_source_memory_accesses=15, terminal='0x780012b3',
                         locale_initialized=False, original_executed=False)))


if __name__ == '__main__':
    main(sys.argv[1])
