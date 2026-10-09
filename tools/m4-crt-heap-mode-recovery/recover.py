"""Exact original selector/probe static recovery, stopping before GetVersionExA."""
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
BASE = ROOT/'reports/m4-crt-heap-mode-recovery'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
ACCEPT_SHA = 'e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326'
SOURCE_SHA = '16e6d7f70c7b23747de90182e34f73471112108524d161b243db5603626a9f7c'
TOOL_SHA = 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
SPANS = (
    ('heap-fragment',0x7800183c,0x78001843),
    ('heap-provider',0x780039bf,0x78003a0c),
    ('selector-prefix',0x78003a0c,0x78003a31),
    ('stack-probe',0x780058b5,0x780058e6),
    ('selector-hot-static',0x78003a0c,0x78003a80),
    ('selector-fallback-static',0x78003a80,0x78003aad),
    ('selector-cold-static',0x7800ccc5,0x7800cdc0),
)
SELECTOR = (0x78003a0c,0x78003a0d,0x78003a0f,0x78003a14,
            0x78003a19,0x78003a1f,0x78003a20,0x78003a21,0x78003a2b)
PROBE = (0x780058b5,0x780058b6,0x780058bb,0x780058bf,0x780058d0,
         0x780058d6,0x780058db,0x780058dd,0x780058e2,0x780058c1,
         0x780058c3,0x780058c5,0x780058c7,0x780058c9,0x780058cb,0x780058ce,0x780058cf)
NEW = SELECTOR[:4]+PROBE+SELECTOR[4:]


def need(value,why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)


def subflags(a,b):
    result = (a-b)&0xffffffff
    return dict(CF=int(a<b),PF=int((result&255).bit_count()%2 == 0),
                AF=int(bool((a^b^result)&16)),ZF=int(result == 0),SF=result>>31,
                OF=int(bool(((a^b)&(a^result))&0x80000000)))


def main(name):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'recovery-r[1-9][0-9]*',name),'Fresh simple recovery name')
    out = workspace_path(BASE/name,reports=True)
    need(out.parent == BASE and not out.exists(),'Fresh immediate-child output')
    loader = ROOT/'tools/m4-crt/recover_provider.py'
    spec = importlib.util.spec_from_file_location('heap_mode_original_pe',loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    provider = ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = mod.PE(provider,PROVIDER_SHA)
    tool = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    accepted = ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json'
    prior_source = ROOT/'reports/m4-crt-heap-create-recovery/recovery-r1/report.json'
    need(sha(tool) == TOOL_SHA,'Exact frozen disassembler')
    need(sha(accepted) == ACCEPT_SHA and read(accepted)['passed'],'Exact accepted previous real HeapCreate gate')
    need(sha(prior_source) == SOURCE_SHA and read(prior_source)['passed'],'Exact prior static contract')
    prior = read(prior_source)
    files = {}

    def add(path,digest=None):
        path = Path(path).absolute()
        key,value = normalized(str(path)),sha(path) if digest is None else digest
        need(sha(path) == value and (key not in files or files[key] == value),'Exact unique physical pin')
        files[key] = value

    for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),loader,
                 provider,tool,accepted,prior_source,ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):
        add(path)
    initial = verify_manifest(files)
    out.mkdir(parents=True)
    spans,instructions,commands = {},{},[]

    def section(address,count):
        matches = [s for s in pe.sections if s[0] <= address-pe.base and address-pe.base+count <= s[0]+s[2]]
        need(len(matches) == 1,'One complete file-backed source section')
        rva,virtual,raw,offset,flags = matches[0]
        return dict(rva=rva,virtual_bytes=virtual,raw_bytes=raw,raw_offset=offset,
                    permissions=flags&0xe0000000,readable=bool(flags&0x40000000),
                    writable=bool(flags&0x80000000),executable=bool(flags&0x20000000))

    for label,start,end in SPANS:
        argv = [str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),
                '--stop-address='+hex(end),str(provider)]
        result = subprocess.run(argv,capture_output=True,timeout=60)
        need(result.returncode == 0,'Fresh selected exact original decode')
        rows = []
        for line in result.stdout.decode('utf-8').splitlines():
            match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
            if not match:
                continue
            pc,code = int(match[1],16),bytes.fromhex(match[2])
            need(start <= pc < end and pc+len(code) <= end,'Bounded whole source instruction')
            need(pe.read(pc-pe.base,len(code)) == code,'Every decoded byte equals the pinned original PE')
            row = dict(pc=pc,bytes_hex=code.hex(),width=len(code),mnemonic=match[3],
                       operands=match[4].split(' <')[0].replace('\t',' ').strip())
            need(pc not in instructions or instructions[pc] == row,'Overlapping spans agree')
            instructions[pc] = row
            rows.append(row)
        raw = pe.read(start-pe.base,end-start)
        need(b''.join(bytes.fromhex(row['bytes_hex']) for row in rows) == raw,'Full contiguous span '+label)
        for suffix,value in (('.bin',raw),('-decode.stdout',result.stdout),('-decode.stderr',result.stderr)):
            path = out/(label+suffix)
            publish_bytes(path,value)
            add(path)
        spans[label] = dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(out/(label+'.bin')),
                            section=section(start,end-start),instructions=rows)
        commands.append(dict(argv=argv,exit_code=0,original_body_executed=False))
    for label,old in (('heap-fragment','attach-fragment'),('heap-provider','heap-initializer')):
        need(spans[label]['sha256'] == prior['spans'][old]['sha256'],'Frozen carried lifted bytes unchanged')
    exact = {0x78003a14:'e89c1e0000',0x78003a21:'c78568ffffff94000000',0x78003a2b:'ff15a0e00278',
             0x780058b5:'51',0x780058c5:'8501',0x780058cb:'8b4004',0x780058ce:'50',0x780058cf:'c3',
             0x780058db:'8501',0x780058e4:'ebea'}
    for pc,raw in exact.items():
        need(instructions[pc]['bytes_hex'] == raw,'Exact helper/selector boundary bytes')
    need(len(NEW) == 26 and len(set(NEW)) == 26,'26 new distinct source PCs')
    need(sum(instructions[pc]['width'] for pc in NEW) == 84,'84 dynamically reached new source bytes')
    need(0x780058e4 not in NEW,'No second probe loop for allocation122C')

    directory,size = struct.unpack_from('<2I',pe.bytes,pe.opt+104)
    descriptors = []
    for index in range(size//20):
        raw = pe.read(directory+index*20,20)
        values = struct.unpack('<5I',raw)
        if not any(values):
            break
        original,timestamp,forwarder,name_rva,iat_rva = values
        descriptors.append(dict(index=index,address=pe.base+directory+index*20,raw_hex=raw.hex(),
            original_first_thunk_RVA=original,timestamp=timestamp,forwarder_chain=forwarder,
            library_name_RVA=name_rva,library=pe.text(name_rva),first_thunk_RVA=iat_rva))
    owners = []
    for slot in (0x7802e0a0,0x7802e09c,0x7802e098,0x7802e018,0x7802e0a8,0x7802e0a4):
        matches = [item for item in pe.imports() if item['iat'] == slot]
        need(len(matches) == 1,'Unique original named import')
        item = matches[0]
        candidates = []
        for descriptor in descriptors:
            offset = slot-pe.base-descriptor['first_thunk_RVA']
            if descriptor['library'] != item['library'] or offset < 0 or offset%4:
                continue
            lookup = (descriptor['original_first_thunk_RVA'] or descriptor['first_thunk_RVA'])+offset
            try:
                name_rva = struct.unpack('<I',pe.read(lookup,4))[0]
                if name_rva&0x80000000 or pe.text(name_rva+2) != item.get('name'):
                    continue
            except (ValueError,UnicodeError):
                continue
            candidates.append((descriptor,lookup,name_rva))
        need(len(candidates) == 1,'Unique original descriptor/INT/hint-name provenance')
        descriptor,lookup,name_rva = candidates[0]
        raw_name = pe.read(name_rva,2+len(item['name'])+1)
        owners.append(dict(**item,raw_IAT=struct.unpack('<I',pe.read(slot-pe.base,4))[0],
            IAT_hex=pe.read(slot-pe.base,4).hex(),IAT_section=section(slot,4),descriptor=descriptor,
            lookup_address=pe.base+lookup,lookup_hex=pe.read(lookup,4).hex(),
            hint_name_address=pe.base+name_rva,hint_name_hex=raw_name.hex(),hint=struct.unpack('<H',raw_name[:2])[0],
            runtime_import_resolution_observed=False,API_executed=False))
    query = next(item for item in owners if item['iat'] == 0x7802e0a0)
    need((query['library'],query['name'],query['raw_IAT']) == ('KERNEL32.dll','GetVersionExA',0x34600),
         'Exact GetVersionExA raw import identity')
    publish_bytes(out/'import-metadata.json',(json.dumps(owners,indent=2)+'\n').encode())
    add(out/'import-metadata.json')
    data = {}
    for label,address,count in (('stack-probe-page',0x78005000,4096),
                                ('environment-name',0x7802e3b8,len('__MSVCRT_HEAP_SELECT')+1),
                                ('global-selection-marker',0x7802f1cc,len('__GLOBAL_HEAP_SELECTED')+1)):
        raw = pe.read(address-pe.base,count)
        publish_bytes(out/(label+'.bin'),raw)
        add(out/(label+'.bin'))
        data[label] = dict(address=address,bytes=count,sha256=sha(out/(label+'.bin')),section=section(address,count))
        if label != 'stack-probe-page':
            need(raw[-1] == 0 and b'\0' not in raw[:-1],'Exact bounded source NUL string')
            data[label]['ASCII'] = raw[:-1].decode('ascii')
    need(data['stack-probe-page']['section']['executable'] and not data['stack-probe-page']['section']['writable'],
         'Fresh probe code page is RX')
    carried_PCs = prior['success_contract']['all_original_source_PCs']
    need(len(carried_PCs) == 13,'Frozen carried 13-PC source chain')
    carried_access = prior['carried_prefix_source_accesses']+prior['success_contract']['added_source_access_ledger']
    need(len(carried_access) == 10,'Frozen carried ten accesses')
    rows = (
        (0x78003a0c,0x20001850,'EBP0: carried selector-entry EBP',True),
        (0x78003a14,0x2000184c,0x78003a19,True),
        (0x780058b5,0x20001848,'ECX0: carried selector-entry ECX',True),
        (0x780058db,0x20000850,'A: declared lower-page DWORD at850',False),
        (0x780058c5,0x20000624,'B: declared lower-page DWORD at624',False),
        (0x780058c9,0x20001848,'ECX0 restored from actual source save',False),
        (0x780058cb,0x2000184c,0x78003a19,False),
        (0x780058ce,0x20000620,0x78003a19,True),
        (0x780058cf,0x20000620,0x78003a19,False),
        (0x78003a1f,0x20000620,'EBX0: carried selector-entry EBX',True),
        (0x78003a20,0x2000061c,0x200017b8,True),
        (0x78003a21,0x200017b8,148,True),
        (0x78003a2b,0x7802e0a0,0x34600,False),
        (0x78003a2b,0x20000618,0x78003a31,True),
    )
    ledger = [dict(ordinal=index+11,pc=pc,address=address,value=value,width=4,write=write)
              for index,(pc,address,value,write) in enumerate(rows)]
    need(len(ledger) == 14 and sum(r['write'] for r in ledger) == 8,'14 added accesses, eight writes/six reads')
    arithmetic = [dict(pc=pc,lhs=a,rhs=b,result=(a-b)&0xffffffff,flags=subflags(a,b)) for pc,a,b in (
        (0x780058b6,0x122c,0x1000),(0x780058d0,0x20001850,0x1000),
        (0x780058d6,0x122c,0x1000),(0x780058dd,0x22c,0x1000),(0x780058c1,0x20000850,0x22c))]
    need(arithmetic[-1]['flags'] == dict(CF=0,PF=1,AF=1,ZF=0,SF=0,OF=0),'Independent exact final SUB flags')
    references = [
        dict(title='Microsoft GetVersionExA',url='https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getversionexa',
             verified_UTC_date='2026-10-08',facts=['One in/out OSVERSIONINFOA pointer and BOOL result',
             'Caller sets size member; success is nonzero, failure zero',
             'Version output can depend on manifest and compatibility mode'],API_executed=False),
        dict(title='Microsoft OSVERSIONINFOA',url='https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-osversioninfoa',
             verified_UTC_date='2026-10-08',facts=['Five DWORD fields followed by128CHAR give148 bytes',
             'Size, major, minor, build, platform, and descriptive text fields'],API_executed=False),
        dict(title='Microsoft x86 stdcall',url='https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170',
             verified_UTC_date='2026-10-08',facts=['Win32 API callee cleans its argument slots; native x64 uses its own ABI'],API_executed=False),
    ]
    publish_bytes(out/'primary-API-contracts.json',(json.dumps(references,indent=2)+'\n').encode())
    add(out/'primary-API-contracts.json')
    report = dict(schema='mw34-m4-heap-mode-static-recovery-v1',passed=True,
        scope='Fresh source-only selector prefix and complete stack probe to first unresolved GetVersionExA CALL',
        provider_sha256=PROVIDER_SHA,accepted_heap_create_sha256=ACCEPT_SHA,prior_static_source_sha256=SOURCE_SHA,
        spans=spans,commands=commands,API_owners=owners,data=data,primary_API_references=references,
        carried_source_PCs=carried_PCs,new_selector_source_PCs=list(SELECTOR),new_probe_source_PCs=list(PROBE),
        added_source_PCs=list(NEW),all_source_PCs=carried_PCs+list(NEW),
        added_source_instruction_rows=[instructions[pc] for pc in NEW],
        carried_source_access_ledger=carried_access,added_source_access_ledger=ledger,
        all_source_access_ledger=carried_access+ledger,
        counts=dict(carried_source_instructions=13,new_selector_instructions=9,new_probe_instructions=17,
            added_source_instructions=26,total_source_instructions=39,added_source_accesses=14,
            added_source_writes=8,added_source_reads=6,total_source_accesses=24,
            separate_carried_HeapCreate_API_return_reads=1,source_plus_bridge_accesses=25,
            source_CALLs=5,added_source_CALLs=2,actual_probe_RET=1,selector_RET=0,
            new_guarded_compiled_source_bytes=86,total_heap_guarded_compiled_source_bytes=170,
            added_executed_source_bytes=84,total_heap_executed_source_bytes=132,
            full_selector_hot_static_bytes=116,selector_cold_static_bytes=251,probe_full_source_bytes=49),
        entry_contract=dict(source_EIP=0x78003a0c,source_ESP=0x20001854,
            genuine_source_return_word_at_entry=dict(address=0x20001854,value=0x780039e8),
            EAX='T: prior real HeapCreate opaque token',EBP='EBP0',ECX='ECX0',EBX='EBX0',
            generic_Runtime_CPU_preserved=True,host_EIP_ESP_projection_required=False,
            host_guest_execution_stores=0,old_API_return_bridge=prior['API_return_bridge']),
        frame_contract=dict(saved_EBP_address=0x20001850,new_EBP=0x20001850,
            allocation_bytes=0x122c,probe_CALL=0x78003a14,probe_target=0x780058b5,
            probe_entry_ESP=0x2000184c,probe_return_word=0x78003a19,
            saved_ECX_address=0x20001848,first_probe_read=0x20000850,final_probe_read=0x20000624,
            relocated_return_word_address=0x20000620,probe_RET=0x780058cf,
            probe_return_EIP=0x78003a19,probe_return_ESP=0x20000624,probe_return_EAX=0x78003a19,
            probe_return_ECX='ECX0',query_frame_ESP=0x20000618,
            source_CALL_return_word=0x78003a31,argument_address=0x2000061c,argument_pointer=0x200017b8,
            OSVERSIONINFOA_bytes=148,OSVERSIONINFOA_size_hex='0x94',structure_end_exclusive=0x2000184c,
            only_size_DWORD_initialized_by_source=True,remaining_struct_bytes_are_carried_not_API_outputs=True,
            terminal_EIP=0x34600,terminal_EAX=0x200017b8,terminal_EBP=0x20001850,
            terminal_ECX='ECX0',terminal_EBX='EBX0',terminal_other_registers_and_FX_carried=True),
        probe_ABI=dict(cdecl_argument_present=False,size_in_EAX=True,custom_stack_adjustment=True,
            return_relocated_by_actual_source_PUSH_RET=True,host_shortcut_forbidden=True,
            caller_before_probe_ESP=0x20001850,caller_after_probe_ESP=0x20000624,
            requested_size_not_returned_in_EAX=True,ECX_restored_from_source_save=True,
            outer_selector_return_39E8_untouched=True,no_second_page_loop_for_this_input=True),
        flag_contract=dict(exact_SUB_CMP_rows=arithmetic,
            probe_TEST_58DB=dict(expression='A & 0x22c',CF=0,OF=0,SF=0,ZF='1 iff result0',
                PF='Even low-byte parity of result',AF='Undefined at exact source PC780058DB'),
            terminal_TEST_58C5=dict(expression='B & 0x20001848',CF=0,OF=0,SF=0,ZF='1 iff result0',
                PF='Even low-byte parity of result',AF='Undefined at exact source PC780058C5'),
            initial_owned_page_zero_terminal=dict(CF=0,PF=1,ZF=1,SF=0,OF=0,
                AF='Declared exact-PC compiled representative, not original architectural value'),
            arithmetic_AF_sites=[0x780039bf,0x780039d6,0x780058db,0x780058c5],
            final_flags_not_independent_of_declared_lower_page=True,
            ordinary_nonzero_directed_lower_page_inputs_required=True,all_other_flags_preserved=True,
            MOV_LEA_PUSH_CALL_RET_preserve_terminal_TEST_flags=True,universal_original_AF_equivalence=False),
        mapping_contract=dict(prior_mappings=18,new_mappings=[0x20000000,0x78005000],total_mappings=20,
            owned_lower_stack=dict(address=0x20000000,bytes=4096,permissions='RW',
                provenance='Fresh explicit research input; zero only at initial admission; directed nonzero inputs separately declared',
                original_captured=False,Windows_guard_stack_growth_proved=False,
                read_DWORD_offsets=[0x850,0x624],source_write_DWORD_offsets=[0x620,0x61c,0x618],
                all_page_bytes_must_be_captured_and_compared=True),
            raw_probe_page=dict(address=0x78005000,bytes=4096,permissions='RX',
                sha256=data['stack-probe-page']['sha256'],provenance='Exact staged original file-backed code identity'),
            prior18pages_preserved=True,prior_TIB_StackLimit=0x20001000,prior_TIB_StackBase=0x20002000,
            prior_TIB_and_policy_stack_low_preserved=True,source_TIB_accesses=0,
            below_TIB_StackLimit_owned_experiment_disclosed=True,old_call_records_and_generic_CPU_preserved=True,
            host_guest_execution_stores=0,mode_global_35004_unproduced=True),
        unresolved_query_contract=dict(source_CALL=0x78003a2b,source_IAT=0x7802e0a0,raw_target=0x34600,
            named_API='KERNEL32.dll!GetVersionExA',actual_source_return=0x78003a31,
            source_argument_pointer=0x200017b8,source_size_DWORD=148,API_executed=False,
            API_returned=False,API_output_produced=False,whole_structure_initialized=False,
            future_x86_stdcall=dict(argument_bytes=4,return_word_bytes=4,ESP_before=0x20000618,
                ESP_after=0x20000620,EIP_after=0x78003a31,EAX='Actual BOOL only after separately admitted API',
                future_API_return_read_required=True,universal_original_volatile_or_flags_equivalence=False)),
        full_selector_CFG_static=dict(current_body_cut=0x78003a31,
            version_path=dict(BOOL_test=0x78003a31,platform_compare=0x78003a35,platform_value=2,
                platform_field=0x200017c8,major_compare=0x78003a3e,major_minimum=5,major_field=0x200017bc,
                success_jump=0x78003a45,cold_mode1=0x7800ccc5),
            environment_path=dict(CALL=0x78003a5c,IAT=0x7802e09c,name_pointer=0x7802e3b8,
                name='__MSVCRT_HEAP_SELECT',output_pointer=0x20000624,maximum_bytes=0x1090,
                nonzero_jump=0x78003a64,cold_entry=0x7800cccd,uppercase_source_loops=True,
                global_marker_pointer=0x7802f1cc,global_marker='__GLOBAL_HEAP_SELECTED',marker_compare_bytes=22,
                direct_calls=[dict(pc=0x7800ccfe,target=0x78010c8e,name='strncmp'),
                    dict(pc=0x7800cd1b,target=0x78010b52,name='strchr'),
                    dict(pc=0x7800cd44,target=0x78011353,name='strtol'),
                    dict(pc=0x7800cdae,target=0x78010c0e,name='strstr')],
                GetModuleFileNameA_CALL=0x7800cd79,GetModuleFileNameA_IAT=0x7802e018,
                decimal_parse_allowed_modes=[1,2,3],all_unexecuted=True),
            fallback=dict(source_CALL=0x78003a6e,target=0x78003a80,
                GetModuleHandleA_CALL=0x78003a8a,IAT=0x7802e098,argument_NULL=True,
                MZ_compare_pc=0x78003a90,e_lfanew_read_pc=0x78003a97,
                PE_signature_checked_by_this_helper=False,
                copied_bytes=['module + e_lfanew + 0x1a','module + e_lfanew + 0x1b'],
                interpretation='PE optional-header linker-version bytes, conditional on valid PE layout',
                first_copied_byte_compare=6,source_SBB_ADD_selects=[2,3],all_unexecuted=True),
            shared_epilogue=[0x78003a7d,0x78003a7e,0x78003a7f],
            selector_RET_not_reached=True,heap_mode_store_39EB_not_reached=True),
        failure_contracts=[
            'Absent/denied lower-page850 probe read must stop at58DB without later624 read, relocation or OS-query CALL',
            'Denied624 read must stop at58C5 before MOVESP58C7 and relocated return PUSH/RET',
            'Saved ECX/return reads and relocated return write/read require genuine ordered checked accesses',
            'Denied relocated-return PUSH58CE or RET58CF must not synthesize a successful helper return',
            'Denied selector size store3A21 must not reach import read/query CALL',
            'Query CALL reads IAT before checked source return write; either fault cannot grant API execution or result',
            'Translated fault diagnostics/partial State are separately audited finite-runtime semantics, not a full x86 fault restart model',
            'Raw named query target remains unresolved; no API return, version output, mode value or selector RET may be fabricated',
            'Existing real HeapCreate handle must retain host ownership and be cleaned up under the prior witnessed lifecycle even on new-prefix fault',
            'Poisoned retries preserve terminal snapshots and do not reseed or execute later jobs'],
        limitations=['Static recovery alone gives no translated native execution credit',
            'Fresh lower page is declared support input, not recovered original state or original Windows stack growth',
            'Only size DWORD is source-initialized; 148-byte extent is a future in/out API contract',
            'No current OS-version result, manifest equivalence, selected heap mode, initialized allocator, attach or full causal replay'],
        native_executed=False,original_executed=False,game_executed=False,API_executed=False,
        original_stack_growth_proved=False,selector_RET_executed=False,mode_selected=False,
        heap_initialized=False,original_attach_proved=False,full_causal_model_claim=False,whole_M4_complete=False,
        host_guest_execution_stores=0,historical_receipts_recursively_expanded=False,
        initial_dependency_check=initial,final_dependency_check=verify_manifest(files),
        elapsed_seconds=(time.perf_counter_ns()-started)/1e9,files=dict(sorted(files.items())))
    path = out/'report.json'
    publish_bytes(path,(json.dumps(report,indent=2)+'\n').encode())
    add(path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,schema=report['schema'],report_sha256=sha(path),pins_sha256=sha(out/'pins.json'),
        source_PCs=39,source_accesses=24,separate_old_API_read=1,new_guarded_bytes=86,total_mappings=20,
        terminal_EIP=hex(0x34600),terminal_ESP=hex(0x20000618),API_executed=False)))


if __name__ == '__main__':
    main(sys.argv[1])
