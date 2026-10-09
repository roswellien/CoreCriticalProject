"""Read-only physical planning for the next six normal FS constructor roots.

This script proves static stack geometry, not execution or admission.  All
original and native103 evidence remains immutable and is not recaptured.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import re
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-mfc-source'
ROOTS = (0x46ab30, 0x48f250, 0x4b4c10, 0x4c3250, 0x4cfe80, 0x4d4830)
GROUPS = (
    dict(graph=0x4e78d0, entry=0x4e78d0, handler=0x5b986b,
         read=0x4e78d7, install=0x4e78de, saved_load=0x4e7997,
         saved_offset=0x18, restore=0x4e799f, final_ret=0x4e79aa),
    dict(graph=0x48f260, entry=0x48f290, handler=0x5b5233,
         read=0x48f297, install=0x48f29e, saved_load=0x48f353,
         saved_offset=0x10, restore=0x48f360, final_ret=0x48f36b),
    dict(graph=0x4d4840, entry=0x4d48f0, handler=0x5b8538,
         read=0x4d48f7, install=0x4d48fe, saved_load=0x4d492a,
         saved_offset=0x10, restore=0x4d4948, final_ret=0x4d4953),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def stack_geometry(graph, graphs, allocator_abi):
    """Bounded CFG transfer of ESP offsets at normal CALL continuations.

    Calls do not execute. Their normal return geometry is authenticated by
    literal RET/RET n metadata, including the accepted MFC823 cdecl return.
    No source register, page, API result, or branch condition is modeled.
    """
    rows = {r['pc']: r for r in graph['instructions']}
    calls = {r['site']: r for r in graph['direct_calls']}
    adjacent = collections.defaultdict(list)
    for edge in graph['edges']:
        need(edge['from'] in rows and edge['to'] in rows, 'Local static CFG')
        adjacent[edge['from']].append(edge['to'])
    offsets = {graph['entry']: 0}
    todo = [graph['entry']]
    transfers = []
    while todo:
        pc = todo.pop()
        row = rows[pc]
        before = offsets[pc]
        after = before
        op = row['operands'].split(' <')[0]
        if row['mnemonic'] == 'push':
            after -= 4
        elif row['mnemonic'] == 'pop':
            need(op != 'esp', 'No dynamic POP ESP in planned frame')
            after += 4
        elif row['mnemonic'] in ('sub', 'add') and op.startswith('esp, '):
            amount = int(op.split(', ')[1], 16)
            after += (-amount if row['mnemonic'] == 'sub' else amount)
        elif row['mnemonic'] == 'call':
            target = calls[pc]['target']
            if target == 0x5abd26:
                need(allocator_abi['original_request_not_popped'] is True and
                     allocator_abi['final_SP'] == 'F+4', 'Accepted literal MFC cdecl return')
                pop = 0
                returns = [allocator_abi['allocator_RET']]
            else:
                returns = graphs[str(target)]['returns']
                widths = {r['pop_bytes'] for r in returns}
                need(len(widths) == 1, 'One exact normal callee cleanup')
                pop = widths.pop()
                returns = [r['pc'] for r in returns]
            after += pop
            transfers.append(dict(CALL_pc=pc, target=target, callee_pop_bytes=pop,
                                  literal_RET_sites=returns, executed=False))
        elif (row['mnemonic'] == 'mov' and op.startswith('esp, ')) or row['mnemonic'] in ('leave', 'enter'):
            raise ValueError('Dynamic stack geometry requires separate recovery')
        if row['mnemonic'] == 'ret':
            need(before == 0 and row['operands'] == '', 'Every normal RET restores entry ESP')
        for target in adjacent[pc]:
            if target in offsets:
                need(offsets[target] == after, 'Every static CFG join has one ESP offset')
            else:
                offsets[target] = after
                todo.append(target)
    need(len(offsets) == len(rows), 'Every local decoded row has static stack geometry')
    return offsets, transfers


def main(name):
    out = BASE / name
    need(not out.exists(), 'Fresh planning receipt')
    out.mkdir(parents=True)
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        actual = sha(path)
        need(expected is None or expected == actual, 'Exact pinned physical planning input')
        pins[str(path)] = actual
        return path

    next_report = json.loads(pin(ROOT / 'reports/m4-joint-startup103-root/next-frontier-r2/report.json',
                                '2899f9342bcd8628bd2006b168bdf920583167ef78691ff83113b88506666ccb').read_bytes())
    need(next_report['passed'] and next_report['initializer_credit'] == 0, 'Static-only parent frontier')
    remaining = json.loads(pin(ROOT / 'reports/m4-joint-startup103-root/next-frontier-r2/remaining-roots.json',
                              '824b7a12259864c9df27dd3b5f1083ab8364f935e0160958d33c7a6e6174b23f').read_bytes())
    graphs = json.loads(pin(ROOT / 'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json',
                           'da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
    mfc = json.loads(pin(ROOT / 'reports/m4-mfc-review/interface-r1/instruction-contracts.json',
                        '94fddd9fc34c0d1dff5100ae8a9f5c66b39e66854a1e5a2d07ac81966656dfeb').read_bytes())
    pe_spec = importlib.util.spec_from_file_location('normal_fs_plan_PE', pin(ROOT / 'tools/analysis/pe.py'))
    P = importlib.util.module_from_spec(pe_spec)
    pe_spec.loader.exec_module(P)
    pe = P.PEImage(pin(ROOT / 'MW3/Mech3.exe',
                      '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    selected = [r for r in remaining if r['entry'] in ROOTS]
    need(len(selected) == 6 and {r['entry'] for r in selected} == set(ROOTS), 'Exact six remaining roots')
    entries = set()
    checked = {}
    root_details = []
    for root in selected:
        need(root['imports'] == ['MFC42.DLL:823', 'MSVCRT.dll:__dllonexit', 'MSVCRT.dll:_onexit'] and
             not root['unresolved_controls'] and not root['FP_sites'], 'Exact narrow planned service family')
        off, _ = pe.rva_range(root['slot'] - pe.image_base, 4)
        need(struct.unpack_from('<I', pe.data, off)[0] == root['entry'], 'Genuine original table slot')
        entries.update(root['local_entries'])
        static_objects = []
        for entry in root['local_entries']:
            for row in graphs[str(entry)]['instructions']:
                pc = row['pc']
                raw = bytes.fromhex(row['bytes'])
                off, _ = pe.rva_range(pc - pe.image_base, len(raw))
                need(pe.data[off:off + len(raw)] == raw, 'Every planned source row physically exact')
                need(pc not in checked or checked[pc] == row, 'No inconsistent overlapping source row')
                checked[pc] = row
                match = re.fullmatch(r'ecx, (0x[0-9a-f]+)', row['operands'])
                if row['mnemonic'] == 'mov' and match:
                    static_objects.append(dict(source_PC=pc, object=int(match[1], 16)))
        frame_entries = [g['entry'] for g in GROUPS if g['graph'] in root['local_entries']]
        root_details.append(dict(entry=root['entry'], slot=root['slot'], local_entries=root['local_entries'],
                                 source_static_objects=static_objects, frame_entries=frame_entries,
                                 nested_normal_frames=root['entry'] == 0x4d4830,
                                 stored_callback_execution_claimed=False))

    frame_contracts = []
    for group in GROUPS:
        graph = graphs[str(group['graph'])]
        offsets, calls = stack_geometry(graph, graphs, mfc['ABI']['allocator'])
        rows = {r['pc']: r for r in graph['instructions']}
        first = rows[group['entry']]
        handler_row = rows[group['entry'] + 2]
        need(first['mnemonic'] == 'push' and first['operands'] == '-0x1', 'Literal initial scope -1')
        need(handler_row['mnemonic'] == 'push' and int(handler_row['operands'], 16) == group['handler'],
             'Literal stored compiler handler')
        need(rows[group['read']]['operands'] == 'eax, dword ptr fs:[0x0]' and
             rows[group['install']]['operands'] == 'dword ptr fs:[0x0], esp' and
             rows[group['restore']]['operands'] == 'dword ptr fs:[0x0], ecx', 'Exact three normal FS0 sites')
        need(offsets[group['install']] == -12 and
             offsets[group['saved_load']] + group['saved_offset'] == -12, 'Exact saved previous-chain slot')
        need(rows[group['saved_load']]['operands'] == f"ecx, dword ptr [esp + {hex(group['saved_offset'])}]",
             'Exact epilogue saved-chain operand')
        need(offsets[group['final_ret']] == 0, 'Normal RET restores entry ESP')
        handler_section = next(s for s in pe.sections if s['virtual_address'] <= group['handler'] - pe.image_base <
                               s['virtual_address'] + max(s['virtual_size'], s['raw_size']))
        need(handler_section['executable'], 'Stored handler points into original executable section')
        frame_contracts.append(dict(**group, installed_record_entry_ESP_offset=-12,
                                    record_fields=[dict(offset=0, value='Actual BEFORE FS:[0]'),
                                                   dict(offset=4, value=group['handler']),
                                                   dict(offset=8, value=0xffffffff)],
                                    epilogue_read_entry_ESP_offset=-12,
                                    normal_return_entry_ESP_offset=0,
                                    static_normal_CALL_cleanup=calls,
                                    static_ESP_offsets={str(pc): n for pc, n in sorted(offsets.items())},
                                    literal_source_rows=graph['instructions'], handler_executed=False))

    allocator_sites = sorted({r['site'] for e in entries for r in graphs[str(e)]['direct_calls']
                              if r['target'] == 0x5abd26})
    need(len(allocator_sites) == 6, 'Exact six distinct static MFC allocator CALL sites')
    fs_sites = sorted({r['pc'] for r in checked.values() if 'fs:[' in r['operands']})
    need(len(fs_sites) == 9, 'Exact three setup/restore groups')
    shared = graphs[str(0x4e78d0)]
    shared_rows = {r['pc']: r for r in shared['instructions']}
    need(shared_rows[0x4e78f7]['operands'] == 'eax, dword ptr [0x60b888]' and
         shared_rows[0x4e794b]['operands'] == 'dword ptr [0x60b888], eax' and
         shared_rows[0x4e7994]['operands'] == 'dword ptr [ebx + 0x8], eax', 'Shared registry source carry')
    read_only = dict(native_executed=False, original_executed=False, initializer_credit=0,
                     candidate103_accepted_by_this_report=False, whole_M4_complete=False)
    plan = dict(schema='mw34-next-normal-FS-static-plan-v1', roots=root_details,
                frame_contracts=frame_contracts, static_allocator_CALL_sites=allocator_sites,
                shared_registry=dict(pointer_field=0x60b888, read_PC=0x4e78f7, test_PC=0x4e78fc,
                                     branch_PC=0x4e78fe, publication_PC=0x4e794b,
                                     count_write_PC=0x4e7994, count_object_offset=8,
                                     initialization_CALL_sites=[0x4e7902, 0x4e7924],
                                     append_CALL_site=0x4e795c,
                                     roots_using_shared_helper=[r['entry'] for r in root_details if 0x4e78d0 in r['frame_entries']],
                                     dynamic_allocation_count_derived_here=False,
                                     requires_persistent_source_carry=True),
                required_next_evidence=[
                    'Capture actual32 FS:[0] and the installed twelve-byte source record at all read/install/restore sites, preserving actual BEFORE chain identity.',
                    'Derive each branch stack record from one genuine bootstrap and persistent CALL/RET, including outer4D48F0 -> inner4E78D0 -> outer -> prior-chain restoration.',
                    'Keep native guest NT_TIB ownership explicit: FS0 starts at the runtime sentinel and cannot be equated silently with the Windows host TEB chain.',
                    'Derive source allocation, linked-node writes, shared60B888 reuse, node count, pointer publications and saved-byte fields from BEFORE state and actual provider outcomes.',
                    'Reuse exact MFC823/CRT normal providers and loader identities; admit alternate entries48F290/4D48F0 and constructor tails only after physical contracts and literal lift closure.',
                    'Retain literal compiler-handler addresses as stored data. Exception dispatch, unwind, allocation failure and destructor callback execution require separate reached evidence.',
                    'Prove normal stack/FS restoration and run causal controls for a wrong predecessor, corrupt chain record, forbidden FS offset and source allocation/store failure without inventing guest exception credit.',
                ], **read_only)
    (out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    pin(out / 'plan.json')
    (out / 'physical-source-rows.json').write_text(json.dumps(sorted(checked.values(), key=lambda r: r['pc']), indent=2) + '\n')
    pin(out / 'physical-source-rows.json')
    pin(ROOT / 'tools/m4-runtime/runtime.cpp')
    pin(ROOT / 'tools/m4-runtime/runtime.hpp')
    pin(ROOT / 'reports/m4-mfc-source/original-preparation-r1/reference_x86.asm')
    pin(__file__)
    report = dict(passed=True, scope='Physically exact static six-root normal exception-chain planning; no guest execution, native build or initializer admission',
                  counts=dict(roots=6, local_entries=len(entries), unique_instruction_rows=len(checked),
                              unique_instruction_bytes=sum(len(bytes.fromhex(r['bytes'])) for r in checked.values()),
                              unique_FS_sites=9, normal_frame_groups=3, nested_frame_roots=1,
                              static_allocator_CALL_sites=6), plan=str(out / 'plan.json'), files=pins, **read_only)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(out / 'report.json'), counts=report['counts'])))


if __name__ == '__main__':
    main(sys.argv[1])
