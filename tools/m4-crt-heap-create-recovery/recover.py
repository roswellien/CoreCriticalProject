"""Fresh static HeapCreate return contract and original source continuation."""
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
BASE = ROOT/'reports/m4-crt-heap-create-recovery'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

PROVIDER_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
ACCEPT_SHA = 'a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d'
SOURCE_SHA = '4706dd8c297247de56da28566f4c3e2b4891c68cc8db8deb28dc604608b5498b'
TOOL_SHA = 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
SPANS = (
    ('attach-fragment',0x7800183c,0x78001843),
    ('attach-after-return',0x78001843,0x7800184c),
    ('heap-initializer',0x780039bf,0x78003a0c),
    ('post-HeapCreate-success',0x780039d6,0x780039e8),
    ('heap-destroy-and-zero-return',0x7800cdd0,0x7800cddf),
    ('mode-selector-hot',0x78003a0c,0x78003a80),
    ('mode-selector-module-fallback',0x78003a80,0x78003aad),
    ('mode-selector-cold',0x7800ccc5,0x7800cdc0),
    ('mode3-entry',0x7800cdc0,0x7800cdd0),
    ('mode3-initializer',0x7800cfa2,0x7800cfea),
    ('mode2-prefix',0x78003aad,0x78003adb),
)
PREFIX = (0x7800183c,0x7800183e,0x780039bf,0x780039c1,0x780039c3,
          0x780039c7,0x780039cc,0x780039cf,0x780039d0)
SUCCESS = (0x780039d6,0x780039d8,0x780039dd,0x780039e3)
ZERO = (0x780039d6,0x780039d8,0x780039dd,0x7800cddc,0x7800cdde)


def need(value,why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)


def main(name):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'recovery-r[1-9][0-9]*',name),'Simple fresh recovery name')
    out = workspace_path(BASE/name,reports=True)
    need(out.parent == BASE and not out.exists(),'Fresh immediate report directory')
    loader = ROOT/'tools/m4-crt/recover_provider.py'
    spec = importlib.util.spec_from_file_location('heap_create_original_pe',loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    provider = ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = mod.PE(provider,PROVIDER_SHA)
    tool = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    accepted = ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json'
    prior_source = ROOT/'reports/m4-crt-heap-init-recovery/recovery-r1/report.json'
    need(sha(tool) == TOOL_SHA,'Exact frozen LLVM disassembler')
    need(sha(accepted) == ACCEPT_SHA and read(accepted)['passed'],'Accepted actual HeapCreate CALL frontier')
    need(sha(prior_source) == SOURCE_SHA and read(prior_source)['passed'],'Frozen earlier static source contract')
    prior = read(prior_source)
    files = {}

    def add(path,digest=None):
        path = Path(path).absolute()
        key,value = normalized(str(path)),sha(path) if digest is None else digest
        need(sha(path) == value and (key not in files or files[key] == value),'Unique exact physical source identity')
        files[key] = value
        return path

    for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),
                 loader,provider,tool,accepted,prior_source,
                 ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):
        add(path)
    initial = verify_manifest(files)
    out.mkdir(parents=True)
    spans,instructions,commands = {},{},[]

    def section(address,count):
        matches = [s for s in pe.sections if s[0] <= address-pe.base
                   and address-pe.base+count <= s[0]+s[2]]
        need(len(matches) == 1,'One complete file-backed PE section')
        rva,virtual,raw,offset,flags = matches[0]
        return dict(rva=rva,virtual_bytes=virtual,raw_bytes=raw,raw_offset=offset,
                    permissions=flags&0xe0000000,readable=bool(flags&0x40000000),
                    writable=bool(flags&0x80000000),executable=bool(flags&0x20000000))

    for label,start,end in SPANS:
        argv = [str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),
                '--stop-address='+hex(end),str(provider)]
        result = subprocess.run(argv,capture_output=True,timeout=60)
        need(result.returncode == 0,'Fresh exact selected-span decode')
        rows = []
        for line in result.stdout.decode('utf-8').splitlines():
            match = re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
            if match:
                pc,code = int(match[1],16),bytes.fromhex(match[2])
                need(start <= pc < end and pc+len(code) <= end,'Bounded whole source instruction')
                need(pe.read(pc-pe.base,len(code)) == code,'Every fresh instruction byte matches pinned provider')
                row = dict(pc=pc,bytes_hex=code.hex(),mnemonic=match[3],
                           operands=match[4].split(' <')[0].replace('\t',' ').strip())
                need(pc not in instructions or instructions[pc] == row,'Overlapping source spans agree')
                instructions[pc] = row
                rows.append(row)
        raw = pe.read(start-pe.base,end-start)
        need(b''.join(bytes.fromhex(row['bytes_hex']) for row in rows) == raw,'Contiguous full source span '+label)
        for suffix,value in (('.bin',raw),('-decode.stdout',result.stdout),('-decode.stderr',result.stderr)):
            path = out/(label+suffix)
            publish_bytes(path,value)
            add(path)
        spans[label] = dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(out/(label+'.bin')),
                            section=section(start,end-start),instructions=rows)
        commands.append(dict(argv=argv,exit_code=0,original_body_executed=False))
    for pc,raw in ((0x780039d6,'85c0'),(0x780039d8,'a300500378'),(0x780039dd,'0f84f9930000'),
                   (0x780039e3,'e824000000'),(0x7800cdd0,'ff3500500378'),
                   (0x7800cdd6,'ff15a4e00278'),(0x7800cddc,'33c0'),(0x7800cdde,'c3')):
        need(instructions[pc]['bytes_hex'] == raw,'Exact continuation/cleanup source bytes')
    for label in ('attach-fragment','heap-initializer'):
        need(spans[label]['sha256'] == prior['spans'][label]['sha256'],'Unchanged complete previously accepted lifted source')
    need(tuple(prior['executed_source_prefix_PCs']) == PREFIX,'Exact admitted earlier source PC chain')

    # Capture original import descriptors, INT entries, hints/names and raw IATs.
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
    for slot in (0x7802e0a8,0x7802e0a4,0x7802e0a0,0x7802e09c,0x7802e098,0x7802e094,0x7802e0b0,0x7802e038):
        matches = [item for item in pe.imports() if item['iat'] == slot]
        need(len(matches) == 1,'Unique original import owner')
        item = matches[0]
        candidates = []
        for descriptor in descriptors:
            offset = slot-pe.base-descriptor['first_thunk_RVA']
            if descriptor['library'] != item['library'] or offset < 0 or offset%4:
                continue
            lookup = (descriptor['original_first_thunk_RVA'] or descriptor['first_thunk_RVA'])+offset
            try:
                name_rva = struct.unpack('<I',pe.read(lookup,4))[0]
                if name_rva & 0x80000000 or pe.text(name_rva+2) != item.get('name'):
                    continue
            except (ValueError,UnicodeError):
                continue
            candidates.append((descriptor,lookup,name_rva))
        need(len(candidates) == 1,'Unique original descriptor/lookup-name provenance')
        descriptor,lookup,name_rva = candidates[0]
        name_bytes = pe.read(name_rva,2+len(item['name'])+1)
        owners.append(dict(**item,raw_IAT=struct.unpack('<I',pe.read(slot-pe.base,4))[0],
            IAT_hex=pe.read(slot-pe.base,4).hex(),IAT_section=section(slot,4),descriptor=descriptor,
            lookup_address=pe.base+lookup,lookup_hex=pe.read(lookup,4).hex(),
            hint_name_address=pe.base+name_rva,hint_name_hex=name_bytes.hex(),hint=struct.unpack('<H',name_bytes[:2])[0],
            runtime_import_resolution_observed=False,API_executed=False))
    create = next(item for item in owners if item['iat'] == 0x7802e0a8)
    destroy = next(item for item in owners if item['iat'] == 0x7802e0a4)
    need((create['library'],create['name'],create['raw_IAT']) == ('KERNEL32.dll','HeapCreate',0x3461e),
         'Exact original HeapCreate named raw import')
    need((destroy['library'],destroy['name']) == ('KERNEL32.dll','HeapDestroy'),'Exact original HeapDestroy named import')
    publish_bytes(out/'import-metadata.json',(json.dumps(owners,indent=2)+'\n').encode())
    add(out/'import-metadata.json')
    data = {}
    for label,address,count in (('heap-globals-file-identity',0x78035000,8),('heap-page-file-identity',0x78035000,4096)):
        raw = pe.read(address-pe.base,count)
        publish_bytes(out/(label+'.bin'),raw)
        add(out/(label+'.bin'))
        data[label] = dict(address=address,bytes=count,sha256=sha(out/(label+'.bin')),
            section=section(address,count),first_eight_bytes_hex=raw[:8].hex(),initialized_heap_proved=False)
    need(pe.read(0x78035000-pe.base,8) == bytes(8),'Raw source handle/mode file identity only')
    need(data['heap-page-file-identity']['section']['writable'] and not data['heap-page-file-identity']['section']['executable'],
         'Original new page is writable and non-executable')
    need(data['heap-page-file-identity']['sha256'] == prior['data']['heap-page-file-identity']['sha256'],
         'Independent fresh page agrees with frozen raw identity')
    prior_ledger = prior['source_access_ledger']
    success_accesses = [
        dict(ordinal=9,pc=0x780039d8,address=0x78035000,value='T: opaque nonzero guest token',width=4,write=True),
        dict(ordinal=10,pc=0x780039e3,address=0x20001854,value=0x780039e8,width=4,write=True),
    ]
    zero_accesses = [
        dict(ordinal=9,pc=0x780039d8,address=0x78035000,value=0,width=4,write=True),
        dict(ordinal=10,pc=0x7800cdde,address=0x20001858,value=0x78001843,width=4,write=False),
    ]
    documentation = [
        dict(title='Microsoft HeapCreate',url='https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapcreate',
            verified_UTC_date='2026-10-08',facts=['HANDLE return; DWORD options and two SIZE_T sizes',
            'Success returns the newly created private heap handle; failure returns NULL with GetLastError',
            'Maximum size zero permits growth; initial size is rounded to the system page size'],API_executed=False),
        dict(title='Microsoft HeapDestroy',url='https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapdestroy',
            verified_UTC_date='2026-10-08',facts=['Accepts the handle returned by HeapCreate',
            'Success returns nonzero and releases the private heap, invalidating its handle',
            'Failure returns zero with GetLastError; no successful cleanup may be inferred'],API_executed=False),
        dict(title='Microsoft x86 stdcall',url='https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170',
            verified_UTC_date='2026-10-08',facts=['Win32 API uses stdcall; callee removes its arguments',
            'x64 accepts but ignores the stdcall keyword, using the host x64 ABI'],API_executed=False),
    ]
    publish_bytes(out/'primary-API-contracts.json',(json.dumps(documentation,indent=2)+'\n').encode())
    add(out/'primary-API-contracts.json')
    report = dict(schema='mw34-m4-heap-create-static-recovery-v1',passed=True,
        scope='Fresh original HeapCreate-return/source-continuation contracts; static recovery only',
        provider_sha256=PROVIDER_SHA,accepted_heap_init_sha256=ACCEPT_SHA,prior_static_source_sha256=SOURCE_SHA,
        spans=spans,commands=commands,API_owners=owners,data=data,primary_API_references=documentation,
        carried_prefix_PCs=list(PREFIX),carried_prefix_source_accesses=prior_ledger,
        success_contract=dict(token='T is an opaque nonzero DWORD bound to a full-width live native HANDLE and current owner/epoch',
            continuation_PCs=list(SUCCESS),all_original_source_PCs=list(PREFIX+SUCCESS),
            added_source_instructions=4,total_source_instructions=13,added_source_accesses=2,total_source_accesses=10,
            added_source_access_ledger=success_accesses,executed_source_bytes=48,compiled_guarded_source_bytes=84,
            stop_before_mode_selector_body=True,source_stop_site=0x780039e3,source_stop_target=0x78003a0c,
            EIP=0x78003a0c,ESP=0x20001854,EAX='T',actual_source_return_word=0x780039e8,
            handle_global_address=0x78035000,handle_global_value='T written only by original MOV39D8',
            mode_global_address=0x78035004,mode_global_produced=False,source_initializer_RET_executed=False,
            zero_branch_taken=False,HeapDestroy_source_executed=False,full_heap_initializer_complete=False),
        API_return_bridge=dict(source_call=0x780039d0,source_IAT=0x7802e0a8,raw_target=0x3461e,
            named_API='KERNEL32.dll!HeapCreate',actual_source_arguments=[0,4096,0],
            argument_addresses=[0x2000184c,0x20001850,0x20001854],
            required_guest_return_read=dict(address=0x20001848,value=0x780039d6,width=4,write=False),
            guest_return_read_separate_from_original_source_accesses=True,
            separate_bridge_return_accesses=1,source_plus_return_bridge_accesses_on_success=11,
            original_x86_convention='stdcall',guest_return_pop_bytes=4,guest_argument_pop_bytes=12,
            ESP_before=0x20001848,ESP_after=0x20001858,EIP_after=0x780039d6,EAX_after='T on real nonzero handle;0 on real NULL',
            declared_State_effects=['EAX','ESP','EIP'],guest_memory_stores=0,generic_Runtime_CPU_preserved=True,
            no_universal_original_volatile_register_or_flag_equivalence=True,full_host_handle_narrowed=False,
            arguments_widened_exactly_to_native_SIZE_T=True,API_executed_by_this_recovery=False),
        flag_contract=dict(carried_prefix=prior['flag_contract'],new_TEST_pc=0x780039d6,
            TEST=dict(CF=0,OF=0,ZF='1 iff T==0',SF='(T>>31)&1',PF='1 iff popcount(T&255) is even',
                AF='Architecturally undefined; exact-PC-qualified compiled representative required'),
            new_undefined_AF_site=0x780039d6,all_other_carried_flags_unchanged=True,
            success_MOV_JE_CALL_leave_TEST_flags=True,
            zero_branch_XOR_pc=0x7800cddc,zero_branch_terminal=dict(EAX=0,CF=0,PF=1,ZF=1,SF=0,OF=0,
                AF='Further undefined source-PC-qualified representative atCDDC'),
            no_fixed_token_value_or_sign_or_parity_assumed=True),
        minimum_zero_frontier=dict(required_API_result='Real NULL or explicitly labeled synthetic source control',
            continuation_PCs=[0x780039d6,0x780039d8,0x780039dd],
            total_source_instructions=12,total_source_accesses=9,source_global_zero_store=True,
            EIP=0x7800cddc,ESP=0x20001858,EAX=0,stop_before_unadmitted_cold_XOR=True,
            last_flags_PC=0x780039d6,CF=0,PF=1,ZF=1,SF=0,OF=0,
            AF='Declared representative only atTEST39D6; coldXORCDDC has not executed',
            source_RET_executed=False,HeapDestroy_executed=False,source_initializer_success=False),
        zero_heap_contract=dict(scope='Complete original cold branch static evidence only; not currently admitted or compiled',
            required_API_result='Actual HeapCreate returned NULL; synthetic NULL fixture is source-only control evidence',
            continuation_PCs=list(ZERO),all_original_source_PCs=list(PREFIX+ZERO),
            total_source_instructions=14,total_source_accesses=10,added_source_access_ledger=zero_accesses,
            executed_source_bytes=46,API_return_bridge_read_is_separate=True,
            source_RET_pc=0x7800cdde,EIP_after_RET=0x78001843,ESP_after_RET=0x2000185c,EAX=0,
            cdecl_argument_retained_at=0x2000185c,source_handle_store=0,source_mode_store=False,
            HeapDestroy_called=False,source_initializer_success=False,attach_caller_after1843_unexecuted=True,
            ordinary_nonzero_mode_frontier_not_reached=True),
        mapping_contract=dict(prior_mappings=17,new_mapping=0x78035000,new_mapping_bytes=4096,total_mappings=18,
            permissions='RW',first_reached_source_access=0x780039d8,
            copy_source_identity_at_admission=True,source_file_zero_means_initialized_heap=False,
            all_prior_machine_State_FX_CPU_call_records_preserved=True,
            host_guest_execution_stores=0,host_heap_global_publication_forbidden=True,
            token_publication_only_original_source=True,mode35004_unproduced=True),
        lifecycle_outcomes=[
            dict(kind='real_success',requirements=['Actual named HeapCreate(0,4096,0) returns nonzero full host HANDLE',
                'Registry accepts unique nonzero token bound to full handle/current owner/epoch before State publication',
                'Checked original stdcall return then genuine MOV and mode CALL; stop before3A0C body'],
                initialized_heap_proved=False),
            dict(kind='real_NULL',requirements=['Record actual NULL/GetLastError; no fabricated token or registry ownership',
                'A separately admitted zero branch may perform actual source globalzero store and RET',
                'No HeapDestroy of NULL and no successful initializer credit']),
            dict(kind='forced_API_refusal',requirements=['Explicit test control refuses before native HeapCreate',
                'No handle/registry/API return or source continuation/global store',
                'Diagnostic cannot be labeled an actual HeapCreate failure']),
            dict(kind='registry_rollback',requirements=['Actual nonzero handle exists but registration cannot admit it',
                'Refuse before EAX/token/stdcall publication or continuation',
                'Attempt real host HeapDestroy once; record full handle, actual BOOL/error and exact lifecycle',
                'Successful destruction can close ownership; failed destruction remains visible, never fabricated']),
            dict(kind='post_gate_host_cleanup',requirements=['Destroy only the full experiment-owned live handle',
                'Record actual native outcome and invalidate token on successful destruction; deny stale/foreign/double access',
                'No host guest-global reset or State reseed; published token remains terminal poisoned machine evidence',
                'Cleanup is host lifecycle evidence and does not execute original CDD0/CDD6']),
            dict(kind='original_later_failure_cleanup_unexecuted',requirements=['Source mode2 or3 initializer actually returns0',
                'CDD0 reads78035000 and pushes token; CDD6 readsHeapDestroyIAT2E0A4 thenpushesretCDDC',
                'Reviewed token-to-full-handle transport and actual API return must be separately admitted',
                'SourceCDDC discardsDestroy result, returns0 without clearing handle global'])],
        future_source_cleanup=dict(pcs=[0x7800cdd0,0x7800cdd6,0x7800cddc,0x7800cdde],
            HeapDestroy_source_IAT=0x7802e0a4,HeapDestroy_raw_IAT=destroy['raw_IAT'],
            source_call_return=0x7800cddc,original_API_argument_bytes=4,
            generic_entry_ESP='Q: actual initializer frame after mode-specific calls',
            source_PUSH_handle_accesses=[dict(pc=0x7800cdd0,address=0x78035000,width=4,write=False,value='ownedT'),
                dict(pc=0x7800cdd0,address='Q-4',width=4,write=True,value='ownedT')],
            source_CALL_accesses=[dict(pc=0x7800cdd6,address=0x7802e0a4,width=4,write=False,value=destroy['raw_IAT']),
                dict(pc=0x7800cdd6,address='Q-8',width=4,write=True,value=0x7800cddc)],
            heap_global_cleared_by_source=False,currently_executed=False),
        future_dependencies=[
            'First unadmitted selector instruction3A0C PUSH EBP would require its own genuine checked stack write',
            'Mode selector3A14 calls stack probe58B5 for122C bytes; current lower stack extent must not be assumed sufficient',
            'GetVersionExA viaIAT2E0A0 at3A2B writes actual checked94-byte OSVERSIONINFOA and returns a witnessed result',
            'Alternative GetEnvironmentVariableA viaIAT2E09C at3A5C uses string7802E3B8 and actual1090-byte checked output',
            'Cold mode environment parsing requires original strncmp/strchr/strtol/strstr helpers and real string extents',
            'Fallback3A80 requires GetModuleHandleA viaIAT2E098 and checked MZ/PE/subsystem reads; mode2/3 cannot be hardcoded',
            'Actual selector RETURN39E8 precedes CMP3 at39E8 and actual mode store35004 at39EB',
            'Mode3 invokesCFA2 withthreshold3F8 and genuineHeapAlloc140 atCFAF; mode2 invokes3AAD and VirtualAlloc3AD7',
            'Later HeapDestroy, heap allocator ownership, guest SEH, locale allocation and parser sizing remain unclosed'],
        required_native_controls=[
            'Exact named API/IAT, pre-call frame/three args/return word and checked permissions before host side effects',
            'Fresh live owner/epoch and token identity; reject zero/stale/foreign/colliding handles without pointer truncation',
            'Full18pageState3504FX512CPU40 comparison; originalMOV alone publishes token; sourceCALL alone writes39E8',
            'Qualified undefinedAF only39BF and39D6 for ordinary success; CDDC only in separately admitted zero path',
            'First-fault source global write and modeCALL return-push ordering with exact partial effects, no reseed',
            'ForcedAPIrefusal, registry rollback, cleanup outcome, observer exceptions, LastError/FP restoration and poisoned retry',
            'No fabricated native success/NULL/mode and no originalmodebody/RET/attach credit'],
        limitations=['Static identity and source/ABI contracts do not prove actual API execution or result',
            'Opaque token correctness is an ownership/lifecycle relation, not equality to original or truncated host pointer bits',
            'Finite bridge EAX/ESP/EIP effects do not establish all original Win32 volatile-register or flag outcomes',
            'No mode selector body, mode publication, allocator initialization, original attach or fullM4 completion is established'],
        native_executed=False,original_executed=False,game_executed=False,API_executed=False,
        host_handle_created=False,host_guest_execution_stores=0,heap_initialized=False,
        mode_selected=False,original_attach_proved=False,whole_M4_complete=False,
        historical_receipts_recursively_expanded=False,initial_dependency_check=initial,
        final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    path = out/'report.json'
    publish_bytes(path,(json.dumps(report,indent=2)+'\n').encode())
    add(path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,schema=report['schema'],report_sha256=sha(path),pins_sha256=sha(out/'pins.json'),
        success_source_PCs=13,success_source_accesses=10,success_separate_API_return_accesses=1,
        HeapDestroy_raw_IAT=hex(destroy['raw_IAT']),heap_page_sha256=data['heap-page-file-identity']['sha256'],API_executed=False)))


if __name__ == '__main__':
    main(sys.argv[1])
