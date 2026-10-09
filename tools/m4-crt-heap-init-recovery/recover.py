"""Fresh exact heap-initializer source recovery; no provider/API/game execution."""
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
BASE = ROOT / 'reports/m4-crt-heap-init-recovery'
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
ACCEPT_SHA = '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e'
ALLOCATION_SHA = '883ffaa436cf2376994fcbeb9807bb547fc3df54e3e220a87cf55cfa8c46388d'
SPANS = (
    ('attach-fragment', 0x7800183c, 0x78001843),
    ('attach-predecessor', 0x78001823, 0x7800183c),
    ('attach-after', 0x78001843, 0x7800184c),
    ('heap-initializer', 0x780039bf, 0x78003a0c),
    ('mode-selector-hot', 0x78003a0c, 0x78003a80),
    ('mode-selector-cold', 0x7800ccc5, 0x7800cdc0),
    ('mode3-and-failure-cold', 0x7800cdc0, 0x7800cddf),
    ('mode3-initializer', 0x7800cfa2, 0x7800cfea),
    ('mode2-prefix', 0x78003aad, 0x78003adb),
)
PREFIX = [0x7800183c, 0x7800183e, 0x780039bf, 0x780039c1,
          0x780039c3, 0x780039c7, 0x780039cc, 0x780039cf, 0x780039d0]


def need(value, why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def main(name):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'recovery-r[1-9][0-9]*', name), 'Simple private recovery name')
    out = workspace_path(BASE / name, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate recovery directory')
    loader = ROOT / 'tools/m4-crt/recover_provider.py'
    spec = importlib.util.spec_from_file_location('heap_init_original_pe', loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = mod.PE(provider, PROVIDER_SHA)
    tool = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    accepted = ROOT / 'reports/m4-crt-locale-default-root/root-acceptance-r2/report.json'
    allocation = ROOT / 'reports/m4-crt-locale-allocation-recovery/recovery-r2/report.json'
    need(sha(accepted) == ACCEPT_SHA and read(accepted)['passed'], 'Accepted default-locale frontier anchor')
    need(sha(allocation) == ALLOCATION_SHA and read(allocation)['passed'], 'Frozen allocation workahead anchor')
    files = {}

    def add(path):
        path = Path(path).absolute()
        key, digest = normalized(str(path)), sha(path)
        need(key not in files or files[key] == digest, 'Stable unique current dependency')
        files[key] = digest
        return path

    for path in (Path(__file__), Path(__file__).with_name('README.md'), Path(sys.executable),
                 loader, provider, tool, accepted, allocation,
                 ROOT / 'tools/m4-pipeline/manifests.py', ROOT / 'tools/m4-pipeline/paths.py'):
        add(path)
    initial = verify_manifest(files)
    out.mkdir(parents=True)
    spans, instructions, commands = {}, {}, []

    def section(address, count):
        matches = [s for s in pe.sections if s[0] <= address-pe.base
                   and address-pe.base+count <= s[0]+s[2]]
        need(len(matches) == 1, 'One complete source-file section')
        rva, virtual, raw, offset, flags = matches[0]
        return dict(rva=rva, virtual_bytes=virtual, raw_bytes=raw, raw_offset=offset,
                    permissions=flags & 0xe0000000, readable=bool(flags & 0x40000000),
                    writable=bool(flags & 0x80000000), executable=bool(flags & 0x20000000))

    for label, start, end in SPANS:
        argv = [str(tool), '-d', '--x86-asm-syntax=intel', '--start-address='+hex(start),
                '--stop-address='+hex(end), str(provider)]
        result = subprocess.run(argv, capture_output=True, timeout=60)
        need(result.returncode == 0, 'Fresh exact selected-span disassembly')
        rows = []
        for line in result.stdout.decode('utf-8').splitlines():
            match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)', line)
            if match:
                pc, code = int(match[1], 16), bytes.fromhex(match[2])
                need(start <= pc < end and pc+len(code) <= end, 'Bounded decoded instruction')
                need(pe.read(pc-pe.base, len(code)) == code, 'Every decoded source byte matches exact PE')
                row = dict(pc=pc, bytes_hex=code.hex(), mnemonic=match[3],
                           operands=match[4].split(' <')[0].replace('\t', ' ').strip())
                need(pc not in instructions or instructions[pc] == row, 'No contradictory decode')
                instructions[pc] = row
                rows.append(row)
        raw = pe.read(start-pe.base, end-start)
        need(b''.join(bytes.fromhex(row['bytes_hex']) for row in rows) == raw, 'Complete contiguous original span '+label)
        for suffix, value in (('.bin', raw), ('-decode.stdout', result.stdout), ('-decode.stderr', result.stderr)):
            path = out / (label+suffix)
            publish_bytes(path, value)
            add(path)
        spans[label] = dict(start=start, end_exclusive=end, bytes=end-start,
                            sha256=sha(out/(label+'.bin')), section=section(start, end-start), instructions=rows)
        commands.append(dict(argv=argv, exit_code=0, provider_body_executed=False))
    for pc, raw in ((0x7800183c, '6a01'), (0x7800183e, 'e87c210000'),
                    (0x780039bf, '33c0'), (0x780039c3, '39442408'),
                    (0x780039d0, 'ff15a8e00278')):
        need(instructions[pc]['bytes_hex'] == raw, 'Exact scheduling/argument/import source instruction')
    owners = []
    for slot in (0x7802e0a8, 0x7802e0a4, 0x7802e094, 0x7802e0b0,
                 0x7802e0a0, 0x7802e09c, 0x7802e098, 0x7802e038):
        rows = [item for item in pe.imports() if item['iat'] == slot]
        need(len(rows) == 1, 'Unique source import owner')
        owners.append(dict(**rows[0], raw_IAT=struct.unpack('<I', pe.read(slot-pe.base, 4))[0], section=section(slot, 4)))
    heap_create = next(row for row in owners if row['iat'] == 0x7802e0a8)
    need(heap_create['library'] == 'KERNEL32.dll' and heap_create['name'] == 'HeapCreate'
         and heap_create['raw_IAT'] == 0x3461e, 'Exact named HeapCreate original raw IAT')
    data = {}
    for label, address, count in (('heap-globals-file-identity', 0x78035000, 8),
                                   ('heap-page-file-identity', 0x78035000, 4096)):
        raw = pe.read(address-pe.base, count)
        path = out / (label+'.bin')
        publish_bytes(path, raw)
        add(path)
        data[label] = dict(address=address, bytes=count, sha256=sha(path),
                           section=section(address, count), initialized=False)
    need(pe.read(0x78035000-pe.base, 8) == bytes(8), 'Source file-zero heap handle/mode identity only')
    # P is the healthy carried parent's actual ESP, before an EIP-only schedule.
    accesses = [
        (0x7800183c, 'P-4', 1, True, 'Literal original cdecl initializer argument'),
        (0x7800183e, 'P-8', 0x78001843, True, 'Actual source CALL return to fragment caller'),
        (0x780039c1, 'P-12', 0, True, 'HeapCreate maximum size PUSH'),
        (0x780039c3, 'P-4', 1, False, 'Actual initializer argument read after maximum-size PUSH'),
        (0x780039c7, 'P-16', 0x1000, True, 'HeapCreate initial size PUSH'),
        (0x780039cf, 'P-20', 0, True, 'Actual SETE-derived flags PUSH'),
        (0x780039d0, '0x7802e0a8', 0x3461e, False, 'Original named HeapCreate raw IAT read'),
        (0x780039d0, 'P-24', 0x780039d6, True, 'Actual indirect source CALL return-word write'),
    ]
    ledger = [dict(ordinal=index+1, pc=pc, address_expression=address, value=value,
                   width=4, write=write, meaning=meaning)
              for index, (pc, address, value, write, meaning) in enumerate(accesses)]
    report = dict(passed=True, scope='Fresh original heap initializer/argument fragment through first genuine HeapCreate CALL; static only',
        provider_sha256=PROVIDER_SHA, accepted_default_locale_sha256=ACCEPT_SHA,
        allocation_workahead_sha256=ALLOCATION_SHA, spans=spans, commands=commands, API_owners=owners, data=data,
        executed_source_prefix_PCs=PREFIX, executed_source_instruction_count=9,
        successful_source_memory_accesses=8, source_access_ledger=ledger,
        bootstrap=dict(healthy_seam='Actual carried mainargs-before, before argument-provider admission',
            parent_ESP=0x20001860, scheduled_State_EIP=0x7800183c,
            host_projection_changes_only=['State.EIP'], State_ESP_changed_by_host=False,
            host_guest_memory_stores=0, host_synthetic_CALL_records=0,
            generic_Runtime_CPU_preserved=True, inherited_Runtime_call_records_preserved=True,
            actual_original_fragment_bytes=7, prior_mappings=17, additional_mappings_before_API=0,
            original_attach_or_GetVersion_executed=False,
            alternate_direct_projection_rejected_for_this_gate='Entry185C plus outer return store reads the prior mainargs return5AC46E as initializer argument; admitted fragment instead produces literal source argument1'),
        CALL_frames=[dict(site=0x7800183e, target=0x780039bf, return_word=0x78001843,
                          target_ESP=0x20001858, arguments=[1], argument_addresses=[0x2000185c], convention='cdecl'),
                     dict(site=0x780039d0, source_IAT=0x7802e0a8, original_raw_target=0x3461e,
                          named_owner='KERNEL32.dll!HeapCreate', return_word=0x780039d6,
                          target_ESP=0x20001848, arguments=[0, 0x1000, 0],
                          argument_addresses=[0x2000184c, 0x20001850, 0x20001854],
                          future_API_convention='stdcall with12-byte parameter cleanup; no API RETURN admitted now')],
        flag_contract=dict(
            initial_XOR_PC=0x780039bf, XOR_effect=dict(EAX=0, CF=0, PF=1, ZF=1, SF=0, OF=0,
                AF='Architecturally undefined; source-PC-qualified Remill representative only, never inferred from AFTER'),
            required_narrow_undefined_AF_bridge_PC=0x780039bf,
            last_defined_arithmetic_PC=0x780039c3, operation='CMP DWORD argument1,EAX0',
            terminal=dict(CF=0, PF=0, AF=0, ZF=0, SF=0, OF=0),
            SETE_PC=0x780039cc, SETE_AL=0, EAX_after_SETE=0,
            later_PUSH_and_CALL_flags_unchanged=True, all_other_carried_flags_unchanged=True),
        exact_terminal=dict(source_CALL=0x780039d0, source_IAT=0x7802e0a8,
            raw_target_EIP=0x3461e, ESP=0x20001848, return_word=0x780039d6,
            EAX=0, EBX_ECX_EDX_ESI_EDI_EBP='Carried unchanged',
            HeapCreate_arguments=[0, 0x1000, 0], actual_IAT_read=True, actual_CALL_return_write=True,
            API_executed=False, API_result_proved=False, API_RETURN_proved=False,
            heap_handle_or_mode_accessed=False, initialized_heap_proved=False),
        unexecuted_hot_continuation=[
            dict(pc=0x780039d6, effect='TEST actual HeapCreate result EAX; no result inferred'),
            dict(pc=0x780039d8, effect='Store actual result to heap handle78035000 BEFORE NULL branch39DD'),
            dict(pc=0x780039dd, effect='NULL handle branchesCDDC, XOR EAX/EAX and RETCDDE; no HeapDestroy on this source branch'),
            dict(pc=0x780039e3, effect='Successful handle calls mode selector3A0C, then39EB publishes actual mode78035004'),
            dict(pc=0x780039f0, effect='Mode3 branchesCDC0, invokesCFA2 with threshold3F8; helper requires genuine HeapAlloc(140) atCFAF'),
            dict(pc=0x780039fb, effect='Mode2 calls small-block initializer3AAD; its prefix invokes genuine VirtualAlloc at3AD7'),
            dict(pc=0x78003a02, effect='Mode2/3 initializer failure branchesCDD0, reads live heap handle, calls HeapDestroy viaIAT2E0A4 atCDD6, thenreturns0'),
            dict(pc=0x78003a08, effect='Successful mode1/2/3 path PUSH1/POPEAX/RET3A0B returns1 to actual1843'),
        ],
        mode_selector_dependencies=[
            'Source helper3A0C allocates122C bytes of guest stack via stack-probe CALL3A14→58B5',
            'Source3A2B calls actual GetVersionExA with checked94-byte OSVERSIONINFOA; success platform2/major>=5 takes explicit mode1 cold branchCCC5',
            'Otherwise GetEnvironmentVariableA at3A5C fills a1090-byte guest extent with actual bounded output; cold parsing uses original strncmp/strchr/strtol/strstr helpers',
            'Fallback3A6E→3A80 uses actual GetModuleHandleA at3A8A and checked PE-header reads to select mode2 or3 via source executable subsystem/version fields',
            'Neither current host OS nor source-file-zero mode is a witness for which real selector branch/result runs',
        ],
        future_mapping=dict(page=0x78035000, source_permissions='RW', needed_before_first_API=False,
            future_first_access=0x780039d8, initialized_from_file_zeros=False,
            handle_and_mode_producer_requires='Actual reviewed HeapCreate result and actual reviewed source selector RETURN/publication'),
        required_native_experiment_controls=[
            'Fresh healthy same3504State/512FX/17mappings and actual mainargs frame; no resetting a poisoned old initializer',
            'Exact7B fragment and full77B heap initializer source ownership; StateEIP-only explicit schedule; no host stack store or synthetic Runtime CALL',
            'Current typed owner/token/control and exact source access ordinals8, write/read operands, values, widths, permitted stack/IAT domains',
            'Single source-PC-qualified XOR39BF undefinedAF representative; deny all later undefined sites or unadmitted bodies',
            'First-fault partial PUSH/CALL stores, IAT read/permission mismatch, argument/control mutations, observer exception and stale owner/token; terminal cleanup and poisoned retry',
            'Independent original-BEFORE model and compiled controls verify fullState/FX/RuntimeCPU/all17pages and actual host FP/LastError',
            'Stop after genuine HeapCreate CALL pushes39D6 and EIP becomes original raw3461E, before any API execution or heap publication',
        ],
        limitations=['Fresh source decode is static identity and bounded control-flow evidence only',
            'Explicitly executing original183C fragment does not establish its original attach predecessors, GetVersion result or DllMain scheduling',
            'No host64 handle may be truncated into a guest DWORD; future API execution needs separately reviewed opaque handle transport and lifecycle',
            'Fullheap initializer, mode selector, success/failure cleanup, allocator/SEH, locale table and parser sizing remain unclosed'],
        native_executed=False, original_executed=False, game_executed=False, API_executed=False,
        initialized_heap_proved=False, locale_initialized=False, parser_sizing_completed=False,
        selected_initializer_coverage=dict(selected=27, inventory=144), whole_M4_complete=False,
        historical_receipts_recursively_expanded=False, initial_dependency_check=initial,
        final_dependency_check=verify_manifest(files), elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    path = out / 'report.json'
    publish_bytes(path, (json.dumps(report, indent=2)+'\n').encode())
    add(path)
    publish_bytes(out/'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True, report_sha256=sha(path), pins_sha256=sha(out/'pins.json'),
                         PCs=9, accesses=8, HeapCreate_raw_IAT=hex(heap_create['raw_IAT']), API_executed=False)))


if __name__ == '__main__':
    main(sys.argv[1])
