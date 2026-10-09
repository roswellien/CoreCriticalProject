"""Strict static native adaptation of two exact image-admitted game entries."""
import argparse
import ctypes as c
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, FLAG_HELPERS, digest, checked_state_offsets
from extract_image import IMAGE_SHA, PROFILES

REVIEWED_IR = {'setter': '60cf4c91d2ed5ff9857768196f06ac0aff40178f6e27f8a80f5cafdda936d62c',
               'consumer': '1e5827d9dcc1bb42795ec6f4c690e0649f995e744a2d60f3a97e36f966d6623e'}
LLVM_DLL_SHA = '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
BRIDGES = {'__remill_read_memory_32': ('i32', ['ptr', 'i32']),
           '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
           '__remill_read_memory_16': ('i16', ['ptr', 'i32']),
           '__remill_write_memory_16': ('ptr', ['ptr', 'i32', 'i16']),
           '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr'])}
COUNTS = {
    'setter': {**dict.fromkeys(FLAG_HELPERS, 1), '__remill_read_memory_32': 3,
               '__remill_write_memory_32': 5, '__remill_function_return': 1,
               'llvm.ctpop.i8': 2, '__remill_undefined_8': 1},
    'consumer': {'__remill_flag_computation_carry': 4, '__remill_flag_computation_zero': 9,
                 '__remill_flag_computation_sign': 9, '__remill_flag_computation_overflow': 6,
                 'llvm.ctpop.i8': 11, '__remill_undefined_8': 5,
                 '__remill_compare_neq': 3, '__remill_compare_sle': 2,
                 '__remill_read_memory_32': 12, '__remill_write_memory_32': 8,
                 '__remill_read_memory_16': 1, '__remill_write_memory_16': 1,
                 '__remill_function_return': 1}}
SSA = r'%[A-Za-z0-9_.$]+'
FIELDS = {2065: 'CF', 2067: 'PF', 2069: 'AF', 2071: 'ZF', 2073: 'SF', 2077: 'OF',
          2216: 'EAX', 2232: 'EBX', 2248: 'ECX', 2264: 'EDX', 2280: 'ESI', 2296: 'EDI',
          2312: 'ESP', 2328: 'EBP', 2472: 'EIP'}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def value_text(api, value):
    pointer = api.PrintValueToString(value)
    try:
        return c.string_at(pointer).decode()
    finally:
        api.DisposeMessage(pointer)


def parse_cfg(source, kind):
    entry = PROFILES[kind]['entry']
    definitions = re.findall(r'^define [^\n]+\{\n(.*?)^}', source, re.M | re.S)
    require(len(definitions) == 1 and re.findall(r'^define .*?@([^ (]+)', source, re.M) == [f'sub_{entry:x}'],
            'Expected exactly one reviewed whole-function entry')
    body = definitions[0]
    blocks, current = {'entry': []}, 'entry'
    for raw in body.splitlines():
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.$]+):', line)
        if match:
            current = match[1]
            require(current not in blocks, 'Duplicate LLVM block')
            blocks[current] = []
        else:
            blocks[current].append(line)
    edges, returns = {}, []
    for name, rows in blocks.items():
        require(rows, 'Empty LLVM block')
        tail = rows[-1]
        unconditional = re.fullmatch(r'br label %([A-Za-z0-9_.$]+)', tail)
        conditional = re.fullmatch(r'br i1 ' + SSA + r', label %([A-Za-z0-9_.$]+), label %([A-Za-z0-9_.$]+)', tail)
        if unconditional:
            edges[name] = [unconditional[1]]
        elif conditional:
            edges[name] = [conditional[1], conditional[2]]
        else:
            require(re.fullmatch(r'ret ptr ' + SSA, tail), 'Unsupported LLVM terminator/route')
            returns.append(name)
            edges[name] = []
    visited, pending = set(), ['entry']
    while pending:
        block = pending.pop()
        if block not in visited:
            require(block in edges, 'Missing LLVM CFG successor')
            visited.add(block)
            pending.extend(edges[block])
    require(visited == set(blocks), 'Unreachable/unreviewed LLVM CFG block')
    require(len(returns) == 1, 'Unexpected shared/multiple return contract')
    return body, blocks, edges, returns


def prove_af(source, kind, offsets, *, authored_final_add=None):
    """AF-only complete-use proof plus exit-store dominance over the full CFG.

    Cyclic live paths are allowed only for the independently admitted bounded
    consumer loops; every reachable exit must contain a deterministic final
    ADD AF overwrite. No undefined value may flow to branches, addresses,
    memory, other State fields, annotations or return arguments.
    """
    body, blocks, edges, returns = parse_cfg(source, kind)
    require(not re.search(r'\b(?:undef|poison|volatile|atomic|phi|inttoptr|ptrtoint)\b', body),
            'Unsupported alias/value/control in AF proof')
    calls = []
    for block, rows in blocks.items():
        for index, line in enumerate(rows):
            match = re.fullmatch(r'(' + SSA + r') = call zeroext i8 @__remill_undefined_8\(\)(?: #\d+)?', line)
            if match:
                calls.append((match[1], block, index))
    require(len(calls) == (1 if kind == 'setter' else 5), 'Unexpected AF undefined call count')
    undefined = {root for root, _, _ in calls}
    aliases = {name for name, offset in offsets.items() if offset == 2069}
    admitted_calls = set(COUNTS[kind])
    for block, rows in blocks.items():
        for line in rows:
            if 'call ' in line:
                called = re.search(r'@([^ (]+)', line)
                require(called and called[1] in admitted_calls, 'Unreviewed observer/helper in AF proof')
                has_state_alias = any(re.search(r'ptr ' + re.escape(alias) + r'(?![A-Za-z0-9_.$])', line)
                                      for alias in {'%state', *offsets})
                if has_state_alias:
                    require(called[1] == '__remill_function_return' and block in returns and
                            re.search(r'\(ptr %state, i32 ', line), 'State alias escapes before checked outer return')
            if re.search(r'store ptr %state(?![A-Za-z0-9_.$])', line):
                require(line == 'store ptr %state, ptr %STATE, align 4', 'State pointer escapes local context')
    stores = {}
    for root, block, index in calls:
        uses = [(name, n, line) for name, rows in blocks.items() for n, line in enumerate(rows)
                if re.search(re.escape(root) + r'(?![A-Za-z0-9_.$])', line)]
        require(len(uses) == 2, 'Undefined AF value leaks from its one store')
        target = next((row for row in uses if not row[2].startswith(root + ' =')), None)
        require(target is not None, 'Missing undefined AF store')
        match = re.fullmatch(r'store i8 ' + re.escape(root) + r', ptr (' + SSA + r'), align 1', target[2])
        require(match and match[1] in aliases and target[0] == block and target[1] == index + 1,
                'Undefined AF is not stored only at the adjacent reviewed AF byte')
        stores[(target[0], target[1])] = root
    af_stores = {}
    for block, rows in blocks.items():
        for index, line in enumerate(rows):
            for alias in aliases:
                if not re.search(re.escape(alias) + r'(?![A-Za-z0-9_.$])', line):
                    continue
                if line.startswith(alias + ' = getelementptr '):
                    continue
                match = re.fullmatch(r'store i8 (' + SSA + r'|0|1), ptr ' + re.escape(alias) + r', align 1', line)
                require(match is not None, 'AF byte is loaded/aliased/escaped/partially written')
                af_stores[(block, index)] = match[1]
    if kind == 'setter':
        root, block, index = calls[0]
        require(all(len(destinations) <= 1 for destinations in edges.values()), 'Setter requires unconditional continuation')
        ordered, current = [], 'entry'
        while current not in ordered:
            ordered.append(current)
            if not edges[current]:
                break
            current = edges[current][0]
        else:
            raise ValueError('Setter requires acyclic continuation')
        all_af = [(name, n) for name in ordered for n in range(len(blocks[name])) if (name, n) in af_stores]
        require(all_af and stores.get(all_af[-1]) == root, 'Setter AF is not the reviewed final store')
        require(all(value in BRIDGES for value in re.findall(r'call [^\n]*?@([^ (]+)', '\n'.join(blocks[block][index+2:]))),
                'Unknown observer after final setter AF')
        return {'policy': 'single-final-SAR-AF-arbitrary-zero', 'state_offset': 2069, 'width': 1,
                'undefined_calls': 1, 'defined_exit_flags_mask': 0xcc5,
                'architectural_AF_compatibility_claim': False, 'value_has_only_AF_store_use': True,
                'subsequent_AF_reads': 0, 'not_a_dead_store_proof': True,
                'llvm_cfg': edges, 'calls': [{'ssa': root, 'block': block, 'store_index': index + 1}]}
    # This exact final arithmetic computation is reviewed in the complete
    # consumer IR: ADD ESP,8; six flags are still produced by Remill.
    final_block, final_line, final_add = ('634', 'store i8 %653, ptr %654, align 1', '%639 = add i32 8, %637')
    # The production adapter never supplies this keyword. It allows public,
    # LLVM-verified authored CFG controls with named SSA instead of copying
    # private guest IR into the repository. The exact game IR SHA remains a
    # mandatory independent gate before production proof/adaptation.
    if authored_final_add is not None:
        final_block, final_line, final_add = authored_final_add
    matches = [(block, index) for block, rows in blocks.items() for index, line in enumerate(rows) if line == final_line]
    require(len(matches) == 1, 'Missing/altered reviewed final ADD AF store')
    final = matches[0]
    require(final[0] == final_block and af_stores.get(final) not in undefined and
            final_add in blocks[final[0]], 'Final overwrite is not the reviewed cleanup ADD')
    # Removing its block must disconnect every reachable return from entry.
    pending, visited = ['entry'], set()
    while pending:
        block = pending.pop()
        if block == final[0] or block in visited:
            continue
        visited.add(block)
        require(block not in returns, 'A reachable return bypasses final ADD AF overwrite')
        pending.extend(edges[block])
    evidence = []
    for (store_block, store_index), root in stores.items():
        block, start = store_block, store_index
        pending, visited, kills = [(block, start + 1)], set(), set()
        while pending:
            block, start = pending.pop()
            if (block, start) in visited:
                continue
            visited.add((block, start))
            killed = False
            for index in range(start, len(blocks[block])):
                value = af_stores.get((block, index))
                if value is not None and value not in undefined:
                    kills.add((block, index))
                    killed = True
                    break
                require(not blocks[block][index].startswith('ret '), 'Live undefined AF reaches a return')
            if not killed:
                pending.extend((successor, 0) for successor in edges[block])
        require(kills, 'Undefined AF lacks a deterministic overwrite on exit paths')
        evidence.append({'ssa': root, 'store_block': store_block, 'store_index': store_index,
                         'overwrites': [{'block': name, 'index': index, 'instruction': blocks[name][index]} for name, index in sorted(kills)],
                         'live_states_checked': len(visited)})
    # No additional undefined generation or AF modification exists after the
    # final store in its block or any continuation to the checked outer return.
    pending, visited = [(final[0], final[1]+1)], set()
    while pending:
        block, start = pending.pop()
        if (block, start) in visited:
            continue
        visited.add((block, start))
        require(not any((block, index) in af_stores for index in range(start, len(blocks[block]))),
                'AF modified after final ADD overwrite')
        pending.extend((successor, 0) for successor in edges[block])
    return {'policy': 'consumer-intermediate-AF-overwritten-before-every-return',
            'state_offset': 2069, 'width': 1, 'undefined_calls': 5, 'defined_exit_flags_mask': 0xcd5,
            'subsequent_AF_reads': 0, 'value_has_only_AF_store_use': True, 'final_AF_defined': True,
            'unreviewed_observers': 0, 'State_alias_escape_before_return': False,
            'final_overwrite': {'block': final[0], 'index': final[1], 'instruction': final_line},
            'final_overwrite_dominates_every_return': True, 'llvm_cfg': edges,
            'returns': returns, 'calls': evidence, 'loop_termination': 'separate pre-entry work-budget admission'}


def admit_extraction(path, kind):
    record = json.loads(path.read_text(encoding='utf-8-sig'))
    require(record['image_sha256'] == IMAGE_SHA and digest(Path(record['image_path'])) == IMAGE_SHA,
            'Wrong actual subsystem image identity')
    function = record['functions'][kind]
    for name, value in PROFILES[kind].items():
        require(function[name] == value, 'Complete actual function binding differs: ' + name)
    require(digest(Path(function['code_path'])) == PROFILES[kind]['sha256'] and
            function['all_instructions_reachable'] is True and function['outgoing_targets'] == [],
            'Wrong complete function code/dependency identity')
    for name, expected in record['source_tools'].items():
        require(digest(Path(name)) == expected, 'Extraction source/tool changed: ' + name)
    require(Path(record['global_page']['initial_path']).read_bytes() == bytes(4096), 'Wrong initial shared globals')
    return record


def adapt(dll, guest, host, record, extraction, kind):
    require(kind in PROFILES, 'Unknown subsystem entry profile')
    private = (ROOT / 'reports/m3-subsystem').resolve()
    require(all(path.resolve().is_relative_to(private) for path in (guest, host, record, extraction)),
            'Private subsystem IR/layout must remain in ignored local reports')
    require(digest(dll) == LLVM_DLL_SHA and digest(guest) == REVIEWED_IR[kind], 'Exact LLVM/complete guest IR identity differs')
    image = admit_extraction(extraction, kind)
    source = guest.read_text()
    require(not re.search(r'\b(?:undef|poison|atomic|volatile|inttoptr|ptrtoint|x86_fp80|float|double)\b', source), 'Unsupported operation family')
    upstream = ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp'
    primary = upstream.read_text()
    annotations = FLAG_HELPERS | ({'__remill_compare_neq', '__remill_compare_sle'} if kind == 'consumer' else set())
    for name in annotations:
        signature = r'bool result, \.\.\.' if name in FLAG_HELPERS else r'bool result'
        require(re.search(r'bool ' + name + r'\(' + signature + r'\)\s*\{\s*return result;\s*}', primary), 'Upstream annotation identity differs')
    require(re.search(r'uint8_t __remill_undefined_8\(void\)\s*\{\s*return 0;\s*}', primary), 'Upstream undefined contract differs')
    api = LLVM(dll)
    for name, result, args in [('SetLinkage', None, [c.c_void_p, c.c_uint]), ('IsAStoreInst', c.c_void_p, [c.c_void_p])]:
        function = getattr(api.dll, 'LLVM' + name);function.restype, function.argtypes = result, args;setattr(api, name, function)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    gd = hd = builder = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        guest_layout = api.GetDataLayoutStr(module).decode()
        gd, hd = api.CreateTargetData(guest_layout.encode()), api.CreateTargetData(HOST_LAYOUT.encode())
        require((api.PointerSize(gd), api.PointerSize(hd)) == (4, 8), 'Guest/host pointer widths differ')
        layouts = {}
        for name in re.findall(r'^%([^ =]+) = type', source, re.M):
            ty = api.GetTypeByName2(context, name.encode());require(ty and not api.IsOpaqueStruct(ty), 'Opaque/missing State type')
            def layout(data):
                return {'size': api.ABISizeOfType(data, ty), 'alignment': api.ABIAlignmentOfType(data, ty),
                        'offsets': [api.OffsetOfElement(data, ty, i) for i in range(api.CountStructElementTypes(ty))]}
            before, after = layout(gd), layout(hd);require(before == after, 'Guest/host struct layout changes: ' + name);layouts[name] = before
        require(layouts['struct.State']['size'] == 3504, 'Unexpected State size')
        entry = api.GetNamedFunction(module, f'sub_{PROFILES[kind]["entry"]:x}'.encode())
        require(entry and api.signature(entry) == ('ptr', ['ptr', 'i32', 'ptr']) and not api.IsFunctionVarArg(api.GlobalGetValueType(entry)), 'Wrong native entry signature')
        offsets = checked_state_offsets(api, entry, gd)
        policy = prove_af(source, kind, offsets)
        counts, writes = {}, []
        for block_index, block in enumerate(api.iterate(api.GetFirstBasicBlock(entry), api.GetNextBasicBlock)):
            for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                if api.IsAStoreInst(instruction):
                    text = value_text(api, instruction).strip();pointer = re.search(r', ptr (' + SSA + r'), align ', text)
                    require(pointer is not None, 'Unknown store address')
                    name = pointer[1]
                    if name in offsets:
                        offset = offsets[name];width = api.ABISizeOfType(gd, api.TypeOf(api.GetOperand(instruction, 0)))
                        require(offset in FIELDS and (width == (1 if offset < 2100 else (2 if kind == 'consumer' and offset == 2264 else 4))), 'Unreviewed State write range')
                        writes.append({'offset': offset, 'bytes': width, 'field': FIELDS[offset], 'destination_ssa': name, 'block_index': block_index, 'instruction': text})
                    else:
                        require(name in {'%MONITOR', '%STATE', '%MEMORY', '%NEXT_PC', '%BRANCH_TAKEN'}, 'Unknown State/local alias store')
                if api.IsACallInst(instruction):
                    callee = api.GetCalledValue(instruction);require(api.IsAFunction(callee), 'Indirect host IR call')
                    name = api.name(callee);counts[name] = counts.get(name, 0) + 1
        require(counts == COUNTS[kind], 'Exact bridge/identity/helper counts differ')
        builder = api.CreateBuilderInContext(context)
        nounwind = api.GetEnumAttributeKindForName(b'nounwind', 8)
        bridges, lowered = [], []
        for function in list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction)):
            name = api.name(function)
            if function != entry:
                require(not api.CountBasicBlocks(function) and api.GetFirstUse(function), 'Unexpected helper body/unused declaration')
                signature = api.signature(function);variadic = bool(api.IsFunctionVarArg(api.GlobalGetValueType(function)))
                if name in annotations:
                    require(signature == ('i1', ['i1']) and variadic == (name in FLAG_HELPERS), 'Annotation signature differs')
                    block = api.AppendBasicBlockInContext(context, function, b'identity');api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.GetParam(function, 0));api.SetLinkage(function, 8);lowered.append(name)
                elif name == '__remill_undefined_8':
                    require(signature == ('i8', []) and not variadic, 'Undefined helper signature differs')
                    block = api.AppendBasicBlockInContext(context, function, b'reviewed_AF_only');api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.ConstInt(api.GetReturnType(api.GlobalGetValueType(function)), 0, 0));api.SetLinkage(function, 8)
                elif name in BRIDGES:
                    require(signature == BRIDGES[name] and not variadic, 'Guest32 bridge signature differs');bridges.append(name)
                else:
                    require(name == 'llvm.ctpop.i8' and signature == ('i8', ['i8']) and not variadic, 'Unknown external helper')
            api.SetFunctionCallConv(function, 0);api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for attr in (b'target-cpu', b'target-features'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attr, len(attr))
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    require(not api.IsAIntToPtrInst(instruction) and not api.IsAPtrToIntInst(instruction), 'Pointer/integer conversion')
                    if api.IsACallInst(instruction):
                        api.SetInstructionCallConv(instruction, 0);api.RemoveCallSiteEnumAttribute(instruction, FUNCTION_INDEX, nounwind)
        api.SetLinkage(entry, 8)
        wrapper_name = 'mw34_' + kind + '_entry'
        wrapper = api.AddFunction(module, wrapper_name.encode(), api.GlobalGetValueType(entry))
        block = api.AppendBasicBlockInContext(context, wrapper, b'entry');api.PositionBuilderAtEnd(builder, block)
        args = (c.c_void_p * 3)(*(api.GetParam(wrapper, i) for i in range(3)))
        call = api.BuildCall2(builder, api.GlobalGetValueType(entry), entry, args, 3, b'memory');api.SetInstructionCallConv(call, 0);api.BuildRet(builder, call)
        api.SetTarget(module, b'x86_64-pc-windows-msvc');api.SetDataLayout(module, HOST_LAYOUT.encode())
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        api.check(api.PrintModuleToFile(module, str(host.resolve()).encode(), c.byref(error)), error)
        intervals = sorted({(row['offset'], row['bytes']) for row in writes})
        require(all(a + w <= b for (a, w), (b, _) in zip(intervals, intervals[1:])), 'Overlapping/unreviewed State write intervals')
        result = {'schema_version': 1, 'profile': 'm3-connected-buffer-' + kind, 'kind': kind,
                  'entry_va': PROFILES[kind]['entry'], 'end_va': PROFILES[kind]['end'],
                  'source_length': PROFILES[kind]['bytes'], 'image_sha256': IMAGE_SHA, 'code_sha256': PROFILES[kind]['sha256'],
                  'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host), 'extraction_sha256': digest(extraction),
                  'guest_ir_identity_reviewed': True, 'llvm_version': api.version, 'dll_sha256': digest(dll),
                  'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT, 'guest_pointer_bits': 32, 'host_pointer_bits': 64,
                  'state_bytes': 3504, 'all_struct_layouts_equal': True, 'struct_layouts': layouts,
                  'state_gep_offsets': offsets, 'state_writes': writes,
                  'state_write_ranges': [{'offset': offset, 'bytes': width, 'field': FIELDS[offset],
                                          'store_count': sum(row['offset'] == offset for row in writes)} for offset, width in intervals],
                  'call_counts': counts, 'bridge_calls': {name: counts[name] for name in sorted(bridges)},
                  'bridges': sorted(bridges), 'flag_annotation_identities': sorted(lowered),
                  'undefined_flag_policy': policy, 'host_entry': wrapper_name,
                  'indirect_host_calls': 0, 'pointer_integer_conversions': 0, 'semantic_repairs': [],
                  'host_abi': 'Windows x64 C: State*, i32 guestPC, checked persistent Context*; same Context* return',
                  'global_page': image['global_page'], 'upstream_identity_source_sha256': digest(upstream)}
        record.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'kind': kind, 'host_ir_sha256': result['host_ir_sha256'], 'state_write_ranges': result['state_write_ranges']}))
        return result
    finally:
        if builder: api.DisposeBuilder(builder)
        for data in (gd, hd):
            if data: api.DisposeTargetData(data)
        if module.value: api.DisposeModule(module)
        api.ContextDispose(context)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--kind', choices=PROFILES, required=True)
    for name in ('llvm-dll', 'guest', 'host', 'record', 'extraction'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args();adapt(args.llvm_dll, args.guest, args.host, args.record, args.extraction, args.kind)
