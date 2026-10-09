"""Independent original-byte contract for the next bounded argv consumer.

Reuses accepted literal disassembly/IR records, checks them against staged PE
bytes, and writes only new contract evidence. No original/native code is run.
"""
import hashlib
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage


def need(ok, why):
    if not ok: raise ValueError(why)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out = ROOT / 'reports/m4-crt-commandline-carry/source-contract-r1'
    need(not out.exists(), 'Fresh owned source-contract directory required')
    files = {}
    def bind(path, digest=None):
        path = Path(path).absolute()
        actual = sha(path)
        key = ntpath.normcase(ntpath.normpath(str(path)))
        need((digest is None or actual == digest) and (key not in files or files[key] == actual),
             'Exact original/source receipt association required')
        files[key] = actual
        return path
    provider = bind(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    bind(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    pe = PEImage(provider.read_bytes())
    def raw(va, size):
        offset, _ = pe.rva_range(va-pe.image_base, size)
        return pe.data[offset:offset+size]
    prior = ROOT / 'reports/m4-crt-mainargs/recovery-r3'
    cfg_path = bind(prior / 'source-CFG.json')
    cfg = json.loads(cfg_path.read_text())['graphs']
    receipt_path = bind(prior / 'report.json', 'ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038')
    need(json.loads(receipt_path.read_text())['passed'], 'Accepted actual source recovery required')
    builder, parser = cfg['normal_argv'], cfg['normal_parser']
    need(bytes.fromhex(''.join(i['bytes'] for i in builder['instructions'])) == raw(0x7800bbbc, 140),
         'Every recovered builder instruction must equal original bytes')
    need(bytes.fromhex(''.join(i['bytes'] for i in parser['instructions'])) == raw(0x7800bc48, 436),
         'Every recovered parser instruction must equal original bytes')
    ir_path = bind(prior / 'normal_argv-host.ll')
    ir = ir_path.read_text()
    consumer = [i for i in builder['instructions'] if 0x7800bbd6 <= i['address'] < 0x7800bbfc]
    need(len(consumer) == 14 and sum(i['size'] for i in consumer) == 38,
         'Complete exact consumer up to first real parser CALL')
    need(raw(0x7800bbd6, 38).hex() == ''.join(i['bytes'] for i in consumer), 'Consumer source byte identity')
    need('%152 = call noundef zeroext i8 @__remill_read_memory_8' in ir and
         ir.index('%152 = call noundef zeroext i8 @__remill_read_memory_8') < ir.index('store i8 %156, ptr %157'),
         'Checked CMP8 read precedes every changed flag publication')
    for call_id, esp in ((212,208),(230,226),(241,237),(252,248),(264,260),(278,274)):
        need(ir.index(f'%{call_id} = call noundef ptr @__remill_write_memory_32') <
             ir.index(f'store i32 %{esp}, ptr'), 'Actual PUSH/CALL checked-store-before-ESP order')
    need(ir.index('%278 = call noundef ptr @__remill_write_memory_32') < ir.index('store i32 %269, ptr %279') <
         ir.index('%282 = call ptr @sub_7800bc48'), 'Actual return-store/ESP/target-PC-before-parser-dispatch order')
    locale = [i for i in parser['instructions'] if '0x780379e1' in i['operands']]
    need(not parser['outgoing_calls'] and len(locale) == 4, 'Exact future parser locale table frontier')
    out.mkdir(parents=True)
    (out / 'consumer-source.bin').write_bytes(raw(0x7800bbd6,38))
    (out / 'parser-source.bin').write_bytes(raw(0x7800bc48,436))
    (out / 'writer-original.bin').write_bytes(raw(0x7800188c,11))
    (out / 'classification-file-bytes.bin').write_bytes(raw(0x780379e0,257))
    required_pages = [
        dict(start=0x7800b000, permission='RX', role='Frozen whole normal builder source identity; parser entry is refused'),
        dict(start=0x78037000, permission='RW', role='Actual writer-published `_acmdln` pointer and later locale table, without file-zero initialization credit'),
        dict(start=0x7803b000, permission='RW', role='Carried native filename buffer and actual `_pgmptr` source store'),
        dict(start=0x20001000, permission='RW', role='Carried real CALL/PUSH words, two preexisting parser count locals'),
        dict(start=None, permission='R after initialization', role='New separately owned complete bounded actual ANSI command-line snapshot including NUL; live until all consumer borrowers retire'),
    ]
    accesses = [
        dict(PC=0x7800bbd6, operation='read32', address=0x78037174, value='Actual live owned GuestAddress published by the compiled writer'),
        dict(PC=0x7800bbdb, operation='write32', address=0x7803b3e0, value=0x7803b3f0),
        dict(PC=0x7800bbe3, operation='read8', address='Owned commandline GuestAddress, offset0', value='Actual first witnessed byte'),
        dict(PC=0x7800bbed, operation='write32', address=0x20001840, value=0x2000184c),
        dict(PC=0x7800bbf1, operation='write32', address=0x2000183c, value=0x20001850),
        dict(PC=0x7800bbf2, operation='write32', address=0x20001838, value=0),
        dict(PC=0x7800bbf4, operation='write32', address=0x20001834, value=0),
        dict(PC=0x7800bbf6, operation='write32', address=0x20001830, value='EDI: filename pointer if empty, commandline pointer otherwise'),
        dict(PC=0x7800bbf7, operation='write32', address=0x2000182c, value=0x7800bbfc),
    ]
    contract = dict(passed=True, scope='Static original-byte consumer and explicit producer/ownership contract; no implementation/execution/equivalence credit',
        consumer=dict(entry=0x7800bbd6,end_exclusive=0x7800bbfc,source_bytes=38,instructions=consumer,
                      actual_path_instructions=dict(empty=13,nonempty=14), source_memory_accesses=accesses),
        incoming_frame=dict(ESP=0x20001844,EBP=0x20001854,ESI=0x7803b3f0,
                            source='Carried real filename stdcall return; outer Runtime CPU remains game slot5BB514/ESP20001860'),
        branch=dict(test_PC=0x7800bbe3,branch_PC=0x7800bbe6,empty_target=0x7800bbea,
                    empty_EDI=0x7803b3f0,nonempty_move_PC=0x7800bbe8,nonempty_EDI='Actual owned commandline guest pointer',
                    no_host_pointer_truncation=True),
        flags=dict(CF=0,OF=0,AF=0,ZF='byte==0',SF='bit7 of byte',PF='even parity of full byte',
                   preserved='Every unrelated flag and State/FX byte; no FP or segment mutation in this consumer'),
        parser_boundary=dict(call_PC=0x7800bbf7,target=0x7800bc48,return_PC=0x7800bbfc,
            final_ESP=0x2000182c,final_EBP=0x20001854,final_EAX=0x20001850,
            cdecl_arguments=['EDI commandline-or-filename',0,0,0x20001850,0x2000184c],
            args_at=[0x20001830,0x20001834,0x20001838,0x2000183c,0x20001840],
            source_return_word=0x7800bbfc,call_store_executed=True,callee_executed=False,
            count_locals='184C/1850 retain prior values until a later real parser is admitted; no count/output fabricated',
            typed_route='Separate owned internal provider Context, exact current owner/token/State/PC/frame/return/argument closure; public required-dependency fault through existing cleanup/Runtime poison',
            generic_Runtime_provider_frame=False),
        partial_fault_order=dict(CMP8='Denied read leaves all flags at their pre-CMP values and later PUSHes absent',
            PUSH_CALL='Checked full DWORD memory store occurs before ESP publication; CALL then publishes target PC before typed unsupported dispatch',
            pgmptr='Actual checked source global store occurs before EDI initialization and commandline byte read'),
        producer=dict(source_PC=0x7800188c,source_return=0x78001892,source_end=0x78001897,
            source_bytes=raw(0x7800188c,11).hex(),provider_IAT=0x7802e034,
            provider_IAT_raw=int.from_bytes(raw(0x7802e034,4),'little'),provider_global=0x78037174,
            unique_named_owner='KERNEL32.dll!GetCommandLineA',
            requirement='Actual OS immutable borrowed host snapshot copied into separately owned checked guest bytes; actual compiled MOV publishes GuestAddress to global before consumer read',
            new_buffer_only_mapping=True,existing_provider_pages_borrowed=True,
            forbidden='Old standalone Registry admits/remaps three pages and fixed ESP1800; do not reuse it wholesale, reset carried State, truncate host pointer, install fake game import, or simulate DllMain/RET',
            scheduling='Author must explicitly declare new bounded producer entry/exit transport and its place in startup; actual11B writer is not an original full DllMain call-order proof'),
        required_pages=required_pages,
        future_parser=dict(entry=0x7800bc48,end_exclusive=0x7800bdfc,source_bytes=436,
            instruction_count=187,outgoing_calls=[],classification_operand_base=0x780379e1,
            classification_reads=locale,initialized_locale_state_admitted=False,
            unresolved='Byte-indexed multibyte-lead classification ownership/init; quote/backslash loops, all commandline and count-local reads/writes, null sizing/output argument branches and cdecl return closure'),
        later_boundaries=[dict(PC=0x7800bc06,target=0x780012b3,kind='malloc',reachable_only_after_actual_parser_return=True),
            dict(PC=0x7800bc16,target=0x7800badb,kind='_amsg_exit on NULL malloc',reachable_only_after_actual_parser_return=True),
            dict(PC=0x7800bc2d,target=0x7800bc48,kind='second parser with allocated output buffers',reachable_only_after_actual_allocator=True)],
        original_executed=False,native_executed=False,game_launched=False,parser_executed=False,
        argc_argv_environment_outputs=False,full_CRT=False,whole_M4_complete=False)
    (out / 'report.json').write_text(json.dumps(contract,indent=2)+'\n')
    for p in (Path(__file__),ROOT/'tools/analysis/pe.py',prior/'global-prerequisites.json',
              ROOT/'tools/m4-crt-commandline-native/registry.cpp',ROOT/'tools/m4-crt-commandline-native/registry.hpp',
              ROOT/'reports/m4-crt-commandline-native/static-r1/report.json',
              ROOT/'docs/m4-crt-commandline-native-contract.md'):
        bind(p)
    for p in out.iterdir():
        if p.is_file(): bind(p)
    for p,digest in list(files.items()): bind(p,digest)
    (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),
                         consumer_bytes=38,source_accesses=9,parser_entry_refused=0x7800bc48)))


if __name__=='__main__': main()
