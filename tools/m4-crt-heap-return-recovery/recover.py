"""Fresh original caller/heap RET recovery on immutable accepted source objects."""
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
BASE = ROOT/'reports/m4-crt-heap-return-recovery'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
TOOL_SHA = 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
ACCEPT_SHA = 'cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'
FINAL_SHA = 'b4e30dc4298f70ef55b97de0119158da500656df9b51759753f1e646e755398d'
PRIOR_SHA = '90565b98f9880fa49358c40d021967af700cc598c4f35da148469bad92372b5f'
BUILD_SHA = '4ceb8fefa09bd36ba3a244295250b44ed333e36ba241e0a6a490996680bba25c'
SPANS = (
    ('heap-fragment', 0x7800183c, 0x78001843),
    ('heap-provider', 0x780039bf, 0x78003a0c),
    ('heap-after-selector', 0x780039e8, 0x78003a0c),
    ('fragment-caller-notrun', 0x78001843, 0x7800184c),
    ('mode3-and-failure-notrun', 0x7800cdc0, 0x7800cddf),
    ('mode2-prefix-notrun', 0x78003aad, 0x78003adb),
)
PCS = (0x780039e8, 0x780039eb, 0x780039f0, 0x780039f6,
       0x780039f9, 0x78003a08, 0x78003a0a, 0x78003a0b)


def need(value, why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object)


def main(name):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'recovery-r[1-9][0-9]*', name), 'Fresh simple recovery name')
    out = workspace_path(BASE/name, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate-child recovery output')
    loader = ROOT/'tools/m4-crt/recover_provider.py'
    spec = importlib.util.spec_from_file_location('heap_return_original_pe', loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provider = ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = module.PE(provider, PROVIDER_SHA)
    tool = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    accepted = ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json'
    final = ROOT/'reports/m4-crt-heap-version-root/final-check-r1/report.json'
    previous = ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1/report.json'
    production = ROOT/'reports/m4-crt-heap-version/build-r3/build.json'
    need(sha(tool) == TOOL_SHA, 'Exact disassembler')
    for path, digest in ((accepted, ACCEPT_SHA), (final, FINAL_SHA), (previous, PRIOR_SHA), (production, BUILD_SHA)):
        need(sha(path) == digest and read(path)['passed'] is True, 'Immutable successful gate/source/build anchor')
    prior, build = read(previous), read(production)
    files = {}

    def add(path, digest=None):
        path = Path(path).absolute()
        actual = sha(path)
        key = normalized(str(path))
        need(digest is None or actual == digest, 'Exact pinned input '+str(path))
        need(key not in files or files[key] == actual, 'Consistent physical identity')
        files[key] = actual

    for path in (Path(__file__), Path(__file__).with_name('README.md'), Path(sys.executable), loader,
                 provider, tool, accepted, final, previous, production,
                 ROOT/'tools/m4-pipeline/manifests.py', ROOT/'tools/m4-pipeline/paths.py'):
        add(path)
    initial = verify_manifest(files)
    out.mkdir(parents=True)
    spans, instructions, commands = {}, {}, []

    def section(address, count):
        matches = [s for s in pe.sections if s[0] <= address-pe.base and address-pe.base+count <= s[0]+s[2]]
        need(len(matches) == 1, 'Complete single raw-file-backed section')
        rva, virtual, raw, offset, flags = matches[0]
        return dict(rva=rva, virtual_bytes=virtual, raw_bytes=raw, raw_offset=offset,
                    permissions=flags & 0xe0000000, readable=bool(flags & 0x40000000),
                    writable=bool(flags & 0x80000000), executable=bool(flags & 0x20000000))

    for label, start, end in SPANS:
        argv = [str(tool), '-d', '--x86-asm-syntax=intel', '--start-address='+hex(start),
                '--stop-address='+hex(end), str(provider)]
        decoded = subprocess.run(argv, capture_output=True, timeout=30)
        need(decoded.returncode == 0, 'Fresh bounded original disassembly')
        rows = []
        for line in decoded.stdout.decode('utf-8').splitlines():
            match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)', line)
            if not match:
                continue
            pc, raw = int(match[1], 16), bytes.fromhex(match[2])
            need(start <= pc < end and pc+len(raw) <= end and pe.read(pc-pe.base, len(raw)) == raw,
                 'Every source instruction belongs to exact original bytes')
            row = dict(pc=pc, bytes_hex=raw.hex(), width=len(raw), mnemonic=match[3],
                       operands=match[4].split(' <')[0].replace('\t', ' ').strip())
            need(pc not in instructions or instructions[pc] == row, 'Overlapping decode agrees exactly')
            instructions[pc] = row
            rows.append(row)
        raw = pe.read(start-pe.base, end-start)
        need(b''.join(bytes.fromhex(row['bytes_hex']) for row in rows) == raw, 'Complete contiguous original span')
        for suffix, value in (('.bin', raw), ('-decode.stdout', decoded.stdout), ('-decode.stderr', decoded.stderr)):
            path = out/(label+suffix)
            publish_bytes(path, value)
            add(path)
        spans[label] = dict(start=start, end_exclusive=end, bytes=end-start,
                            sha256=sha(out/(label+'.bin')), section=section(start, end-start), instructions=rows)
        commands.append(dict(argv=argv, exit_code=0, original_body_executed=False))
    for label in ('heap-fragment', 'heap-provider'):
        need(spans[label]['sha256'] == prior['spans'][label]['sha256'], 'Full previously admitted source body unchanged')
    for pc, raw in ((0x780039e8, '83f803'), (0x780039eb, 'a304500378'), (0x780039f0, '0f84ca930000'),
                    (0x780039f6, '83f802'), (0x780039f9, '750d'), (0x78003a08, '6a01'),
                    (0x78003a0a, '58'), (0x78003a0b, 'c3')):
        need(instructions[pc]['bytes_hex'] == raw, 'Exact final source path instruction')
    need(sum(instructions[pc]['width'] for pc in PCS) == 23, 'Exactly 23 additional executed source bytes')

    object_receipts = []
    prep = ROOT/'reports/m4-crt-heap-init/preparation-r2'
    need(sha(prep/'report.json') == 'ef86361916eece8b4bfba1893341a403fcd3a6a02af272fde907ccb2bd2667fc',
         'Exact original full-provider lifting receipt')
    original_lift = read(prep/'report.json')['source_bodies']['provider']
    need(pe.read(0x39bf, 77) == (prep/'provider-source.bin').read_bytes(), 'Existing full77B source/lift authority')
    for path in (prep/'provider-source.bin', prep/'provider-guest.ll', prep/'provider-host.ll', prep/'report.json'):
        add(path)
    host_ir = (prep/'provider-host.ll').read_text()
    need(sha(prep/'provider-host.ll') == original_lift['host_sha256'], 'Exact originally adapted complete provider IR')
    need('define ptr @mw34_heap_init_provider_body(' in host_ir
         and 'call ptr @sub_78003a0c(' in host_ir
         and 'tail call ptr @__remill_function_return(' in host_ir,
         'Existing complete lifted body contains real selector CALL and initializer RET transport')
    need(host_ir.index('%326 = call noundef ptr @__remill_write_memory_32') <
         host_ir.index('store i32 %322, ptr %320'), 'Existing PUSH checks write before ESP publication')
    need(host_ir.index('store i32 %396, ptr %394') <
         host_ir.index('%400 = call noundef i32 @__remill_read_memory_32') <
         host_ir.index('store i32 %400, ptr %EAX'), 'Existing POP publishes ESP before read and EAX after')
    need(host_ir.index('%410 = call noundef i32 @__remill_read_memory_32') <
         host_ir.index('store i32 %410, ptr %411') < host_ir.index('store i32 %413, ptr %405') <
         host_ir.index('%417 = tail call ptr @__remill_function_return'), 'Existing RET checks read before EIP/ESP and return bridge')
    for level in ('O0', 'O2'):
        path = prep/('provider-'+level+'.obj')
        entries = [(p, h) for p, h in build['entry_objects'].items() if normalized(p) == normalized(str(path))]
        need(len(entries) == 1, 'Exact prior production provider object')
        digest = entries[0][1]
        add(path, digest)
        argv = [str(tool), '--file-headers', '--syms', str(path)]
        decoded = subprocess.run(argv, capture_output=True, timeout=30)
        need(decoded.returncode == 0 and b'coff-x86-64' in decoded.stdout
             and b'mw34_heap_init_provider_body' in decoded.stdout, 'Original admitted AMD64 object symbol/type')
        for suffix, value in (('.stdout', decoded.stdout), ('.stderr', decoded.stderr)):
            output = out/('provider-'+level+'-COFF'+suffix)
            publish_bytes(output, value)
            add(output)
        object_receipts.append(dict(level=level, path=str(path), sha256=digest,
            exported_symbol='mw34_heap_init_provider_body', full_original_source_bytes=77,
            newly_compiled=False, complete_lift_authority_reused=True))

    data = {}
    for label, address, count in (('heap-globals-file', 0x78035000, 8), ('heap-globals-page', 0x78035000, 4096)):
        raw = pe.read(address-pe.base, count)
        path = out/(label+'.bin')
        publish_bytes(path, raw)
        add(path)
        data[label] = dict(address=address, bytes=count, sha256=sha(path), section=section(address, count),
                           new_mapping=False, original_file_identity_only=True)
    need(pe.read(0x35000, 8) == bytes(8), 'Original raw handle/mode DWORD identity is zero only in source file')
    need(data['heap-globals-page']['section']['writable'] and not data['heap-globals-page']['section']['executable'],
         'Existing full heap-global page is RW')
    imports = []
    for slot in (0x7802e0a8, 0x7802e0a4):
        owner = [i for i in pe.imports() if i['iat'] == slot]
        need(len(owner) == 1, 'Unique carried source heap import owner')
        imports.append(dict(**owner[0], raw_IAT=struct.unpack('<I', pe.read(slot-pe.base, 4))[0],
                            original_API_executed=False, new_source_CALL_at_this_continuation=False))
    need(imports[0]['name'] == 'HeapCreate' and imports[1]['name'] == 'HeapDestroy', 'Carried named heap lifetime imports')

    added_ledger = [
        dict(ordinal=32, pc=0x780039eb, address=0x78035004, address_expression='DSBASE+0x78035004',
             width=4, write=True, value=1, effect='Only genuine original mode-global publication'),
        dict(ordinal=33, pc=0x78003a08, address=0x20001854, address_expression='SSBASE+P-12',
             width=4, write=True, value=1, effect='Actual PUSH1; replaces already consumed selector return word'),
        dict(ordinal=34, pc=0x78003a0a, address=0x20001854, address_expression='SSBASE+P-12',
             width=4, write=False, value=1, effect='Actual POPEAX; restores initializer ESP P-8'),
        dict(ordinal=35, pc=0x78003a0b, address=0x20001858, address_expression='SSBASE+P-8',
             width=4, write=False, value=0x78001843, effect='Actual source RET reads original fragment CALL frame'),
    ]
    prior_ledger = prior['carried_source_access_ledger']+prior['conditional_mode1_added_source_access_ledger']
    need(len(prior_ledger) == 31 and len(prior['conditional_mode1_all_source_PCs']) == 51, 'Exact accepted prior source ledgers')
    all_ledger = prior_ledger+added_ledger
    all_PCs = prior['conditional_mode1_all_source_PCs']+list(PCS)
    publish_bytes(out/'qualifying-source-ledger.json', (json.dumps(dict(PCs=all_PCs, accesses=all_ledger), indent=2)+'\n').encode())
    add(out/'qualifying-source-ledger.json')
    failure = ROOT/'reports/m4-crt-heap-version-review/failed-native-r1/report.json'
    add(failure, '33b04d1f74afbbccb3cec2b33fb2f85119e7f1e29ba5837f9a3cef912a701811')
    need(read(failure)['current_proof_credit'] is False and read(failure)['validator_weakened'] is False,
         'Historical hardware refusal remains uncredited and validator unchanged')
    report = dict(
        passed=True, schema='mw34-m4-heap-return-static-recovery-v1',
        scope='Fresh static original heap-mode publication and initializer RET contract; STOP before fragment caller',
        provider_sha256=PROVIDER_SHA, accepted_heap_version_sha256=ACCEPT_SHA,
        accepted_final_check_sha256=FINAL_SHA, prior_static_source_sha256=PRIOR_SHA,
        carried_production_build_sha256=BUILD_SHA, spans=spans, commands=commands,
        reused_provider_objects=object_receipts, data=data, carried_imports=imports,
        qualifying_added_source_PCs=list(PCS), qualifying_all_source_PCs=all_PCs,
        qualifying_added_source_access_ledger=added_ledger, qualifying_all_source_access_ledger=all_ledger,
        counts=dict(prior_source_PCs=51, added_source_PCs=8, qualifying_total_source_PCs=59,
            prior_source_accesses=31, added_source_accesses=4, qualifying_total_source_accesses=35,
            added_source_writes=2, added_source_reads=2, qualifying_source_CALLs=5,
            qualifying_source_RETs=3, additional_initializer_RET=1, added_executed_source_bytes=23,
            qualifying_executed_source_bytes=192, full_heap_provider_authority_bytes=77,
            local_total_guarded_identity_bytes=230, total_source_identity_bytes=2086,
            new_guarded_source_bytes=0, new_guest_objects=0, preserved_guest_objects=38,
            prior_mappings=21, total_mappings=21, separate_API_return_reads=2,
            separate_API_output_DWORD_stores=37),
        entry_contract=dict(EIP=0x780039e8, ESP=0x20001858, EAX=1, parent_ESP=0x20001860,
            DSBASE=0, SSBASE=0, EBP='Source-restored EBP0', EBX='Source-restored EBX0',
            original_fragment_return_word_address=0x20001858, original_fragment_return_word=0x78001843,
            cdecl_argument_address=0x2000185c, cdecl_argument_value=1,
            heap_handle_global_address=0x78035000, heap_handle_global='Actual nonzero opaque registered token',
            heap_mode_global_address=0x78035004, heap_mode_global_before=0,
            private_HANDLE_registry_live=True, admission_requires_actual_query_BOOL_and_output=True,
            not_from_previous_cleaned_up_AFTER_snapshot=True),
        qualifying_return_contract=dict(EIP=0x78001843, ESP=0x2000185c, EAX=1,
            source_RET_PC=0x78003a0b, source_RET_read_address=0x20001858,
            heap_mode_global_value_after=1, genuine_mode_publication_by_source_MOV=True,
            handle_global_unchanged=True, cdecl_argument_still_present=True, cdecl_argument_cleanup_executed=False,
            fragment_caller_TEST1843_executed=False, fragment_caller_POP1845_executed=False,
            all_other_State_FX_generic_CPU_and_call_records_carried=True),
        existing_lift_checked_access_order=dict(
            original_source_instructions_preserved=True,
            PUSH3A08='Checked SSBASE+(ESP-4) write precedes State ESP decrement publication',
            POP3A0A='Existing generated IR publishes State ESP+4 before checked read at SSBASE+oldESP; EAX publication follows successful read',
            RET3A0B='Checked read at SSBASE+oldESP precedes State EIP/next-PC publication, then State ESP+4 publication, then return bridge',
            denied_POP_read_partial_State_ESP=0x20001858,
            denied_POP_read_does_not_publish_new_EAX=True,
            denied_RET_read_partial_State_ESP=0x20001858,
            denied_RET_read_does_not_publish_return_EIP=True,
            native_original_exception_order_universal_equivalence=False),
        flags=dict(first_CMP_pc=0x780039e8, first_CMP_operation='1-3',
            first_CMP_defined=dict(CF=1, PF=0, AF=1, ZF=0, SF=1, OF=0),
            JE39F0_taken=False, last_CMP_pc=0x780039f6, last_CMP_operation='1-2',
            final_defined=dict(CF=1, PF=1, AF=1, ZF=0, SF=1, OF=0), JNE39F9_taken=True,
            MOV_PUSH_POP_RET_preserve_flags=True, DF_and_nonarithmetic_flags_carried=True,
            new_undefined_AF_sites=0, carried_qualified_AF_representatives={str(pc): 0 for pc in
                (0x780039bf, 0x780039d6, 0x780058db, 0x780058c5, 0x78003a31)},
            undefined_AF_universal_original_equivalence=False),
        source_authority=dict(new_provider_lift_required=False, existing_full77B_lift_includes_remaining36B=True,
            original_complete_lift_receipt_sha256='ef86361916eece8b4bfba1893341a403fcd3a6a02af272fde907ccb2bd2667fc',
            original_adapted_provider_IR_sha256=original_lift['host_sha256'],
            remaining_static_span_bytes=36, qualifying_remaining_bytes=23, existing_O0_O2_objects_unchanged=True,
            new_objects=0, new_mappings=0, source_identity_deduplication='23 executed bytes already inside the full77B provider in accepted2086B identity'),
        chronology=dict(healthy_original_mainargs_before_projection='State EIP only at fragment183C; no host ESP or memory store',
            source_CALL_chain='FragmentCALL183E -> heap provider -> selectorCALL39E3 -> genuine selectorRET3A7F -> original provider continuation',
            selector_RET_transport='Return into existing lifted provider CALL continuation while private HANDLE authority remains live; no synthetic EIP/EAX/global seed',
            expected_local_depth='Selector3 -> provider2 -> initializerRET fragment1 -> typed stop/cleanup0',
            source_mode_global_progress='Private expected mode0 until successful actual MOV39EB, then1; failed store must not credit publication',
            initializer_RET_transport='Checked original return-word read then actual State ESP/EIP update; typed stop at fragment1843 before caller source executes',
            generic_Runtime_CPU_preserved=True, generic_Runtime_call_records_added=0,
            private_HANDLE_live_at_source_initializer_RET=True,
            bounded_terminal_cleanup='Release the same full64-bit owned HANDLE through checked named HeapDestroy after stop or partial fault; revoke owner',
            guest_globals_not_cleared_by_research_cleanup=True,
            post_cleanup_guest_token_not_a_live_resource_claim=True,
            accepted_previous_after_registry_already_closed=True),
        failure_controls=[
            dict(site=0x780039eb, ordinal=32, kind='RW mode-page permission/range/source-state guard',
                 required='No guest mode publication on failed original store; CMP39E8 flags already real; release private HANDLE'),
            dict(site=0x78003a08, ordinal=33, kind='Checked actual stack PUSH store',
                 required='Keep already published mode; no successful push/initializerRET credit on denied write; release private HANDLE'),
            dict(site=0x78003a0a, ordinal=34, kind='Checked POP read/changed source word',
                 required='Actual PUSH precedes POP; existing IR publishes ESP1858 before checked read at1854, EAX only after successful read; no initializerRET credit on denied read or modified input'),
            dict(site=0x78003a0b, ordinal=35, kind='RET read range/permission/changed original return word/foreign target',
                 required='Admit only exact original1843 target/frame after actual read; no caller or return success credit on fault; release private HANDLE'),
            dict(kind='Postpublication/RET observer failure and ownership retry',
                 required='Preserve actual partial source effects, ensure once-only fullHANDLE release, deny reuse/owner mismatch without source replay'),
            dict(kind='Production query alternate or API failure',
                 required='Actual full BOOL/output chooses existing ENV frontier; no fabricated mode1/2/3, no ENV API execution at this gate'),
        ],
        proposed_capture_contract=dict(ordinary_checkpoint_count=44, added_checkpoint_count=4,
            added_checkpoints=[
                dict(name='heap-return-mode-store-before', source_pc=0x780039eb, ESP=0x20001858, completed_source_accesses=31),
                dict(name='heap-return-mode-store-after', source_pc=0x780039eb, ESP=0x20001858, completed_source_accesses=32),
                dict(name='heap-return-initializer-return-before', source_pc=0x78003a0b, ESP=0x20001858, completed_source_accesses=34),
                dict(name='heap-return-initializer-return-after', source_pc=0x78001843, ESP=0x2000185c, completed_source_accesses=35, private_HANDLE_live=True)],
            distinct_new_progress_DWORDs=8, proposed_new_job_DWORDs=72,
            capture_schema_is_declared_experiment_metadata_not_original_structure=True),
        future_dependencies=dict(mode2='Original CALL39FB ->78003AAD; not executed on qualifyingmode1',
            mode3='Original JE39F0 ->7800CDC0 then mode3 initializer; not executed',
            mode2_or3_failure='Original cold source may CALL named HeapDestroy and returnzero; not a substitute for research private cleanup',
            actual_alternate_query='Source reaches unresolved GetEnvironmentVariableA CALL3A5C; not executed',
            next_fragment_caller='TEST1843; POP ECX1845 consumes still-present cdeclarg; JE1846; excluded from this gate'),
        manifest_sensitive_API_universal_original_equivalence=False,
        declared_lower_stack_original_capture=False, original_guard_stack_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False, historical_HW_refusal_current_success_credit=False,
        original_provider_or_native_API_or_game_executed=False, source_initializer_RET_executed=False,
        heap_mode_global_published=False, heap_initialized=False, original_attach_proved=False,
        full_CRT_or_full_allocator_graph_complete=False, whole_M4_complete=False,
        initial_physical_closure=initial, files=files)
    report['physical_closure'] = verify_manifest(files)
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report['pins_sha256'] = sha(out/'pins.json')
    report['seconds'] = (time.perf_counter_ns()-started)/1e9
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k in ('passed', 'schema', 'scope', 'counts', 'pins_sha256', 'physical_closure', 'seconds')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
