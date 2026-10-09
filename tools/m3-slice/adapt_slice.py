"""Exact-identity MW3 whole-function guest32 to Windows x64 ABI adapter.

Instruction/defined-flag computations remain Remill's. The one final SAR AF
value is architecturally undefined, not dead: only that reviewed store is
given an arbitrary zero, and AF is excluded from architectural exit checks.
"""
import argparse
import ctypes as c
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, FLAG_HELPERS, digest, checked_state_offsets
from extract_image import IMAGE_SHA, CODE_SHA, ENTRY, END

REVIEWED_IR = '60cf4c91d2ed5ff9857768196f06ac0aff40178f6e27f8a80f5cafdda936d62c'
LLVM_DLL_SHA = '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
BRIDGES = {
    '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
    '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
    '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
}
CALL_COUNTS = {**dict.fromkeys(FLAG_HELPERS, 1), '__remill_read_memory_32': 3,
               '__remill_write_memory_32': 5, '__remill_function_return': 1,
               'llvm.ctpop.i8': 2, '__remill_undefined_8': 1}
FIELDS = {2065: ('CF', 1), 2067: ('PF', 1), 2069: ('AF', 1), 2071: ('ZF', 1),
          2073: ('SF', 1), 2077: ('OF', 1), 2216: ('EAX', 4), 2264: ('EDX', 4),
          2312: ('ESP', 4), 2472: ('EIP', 4)}
SSA = r'%[A-Za-z0-9_.$]+'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def rendered(api, value):
    pointer = api.PrintValueToString(value)
    try:
        return c.string_at(pointer).decode()
    finally:
        api.DisposeMessage(pointer)


def prove_final_af(source, offsets):
    """Narrow authored-testable proof; production additionally requires IR SHA.

    No value-use besides the one AF store, no subsequent AF read, no aliases,
    no conditional continuation, and no subsequent call except the checked
    guest32 memory bridges and final return bridge. Return observes only the
    architectural fields including the CC5 defined mask, explicitly not AF.
    """
    body_match = re.search(r'^define ptr @sub_558290\(ptr noalias %state, i32 %program_counter, ptr noalias %memory\) \{\n(.*?)^}', source, re.M | re.S)
    require(body_match is not None and len(re.findall(r'^define ', source, re.M)) == 1,
            'Final AF requires exactly the reviewed entry/signature')
    body = body_match[1]
    require(not re.search(r'\b(?:undef|poison|volatile|atomic|phi|select|inttoptr|ptrtoint)\b', body),
            'Unsupported value/control/alias operation in final AF proof')
    blocks, current = {'entry': []}, 'entry'
    for raw in body.splitlines():
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        label = re.fullmatch(r'([A-Za-z0-9_.$]+):', line)
        if label:
            current = label[1]
            require(current not in blocks, 'Duplicate block in final AF proof')
            blocks[current] = []
        else:
            blocks[current].append(line)
    chain, current = [], 'entry'
    while current not in chain:
        require(current in blocks and blocks[current], 'Missing/empty final AF block')
        chain.append(current)
        terminator = blocks[current][-1]
        successor = re.fullmatch(r'br label %([A-Za-z0-9_.$]+)', terminator)
        if successor:
            current = successor[1]
        else:
            require(re.fullmatch(r'ret ptr ' + SSA, terminator), 'Conditional/unsupported AF control flow')
            break
    else:
        raise ValueError('Cyclic final AF control flow')
    require(set(chain) == set(blocks), 'Unreachable/unreviewed AF blocks')
    calls = list(re.finditer(r'^\s*(' + SSA + r') = call zeroext i8 @__remill_undefined_8\(\)(?: #\d+)?\s*$', body, re.M))
    require(len(calls) == 1, 'Expected exactly one reviewed final SAR undefined AF call')
    root = calls[0][1]
    uses = [line.strip() for line in body.splitlines() if re.search(re.escape(root) + r'(?![A-Za-z0-9_.$])', line)]
    require(len(uses) == 2, 'Undefined AF value leaks outside its single store')
    store = next((line for line in uses if not line.startswith(root + ' =')), '')
    match = re.fullmatch(r'store i8 ' + re.escape(root) + r', ptr (' + SSA + r'), align 1', store)
    require(match is not None and offsets.get(match[1]) == 2069, 'Undefined AF destination differs from reviewed AF byte')
    af_aliases = {name for name, offset in offsets.items() if offset == 2069}
    tail = body[calls[0].end():]
    require(tail.count(store) == 1, 'Final undefined AF store missing')
    for line in tail.splitlines():
        line = line.split(';', 1)[0].strip()
        if line == store:
            continue
        require(not any(re.search(re.escape(alias) + r'(?![A-Za-z0-9_.$])', line) for alias in af_aliases),
                'Final undefined AF is read/aliased after its store')
        if re.search(r'\bbr\b', line):
            require(re.fullmatch(r'br label ' + SSA, line), 'Final AF has a conditional continuation')
        if 'call ' in line:
            helper = re.search(r'@([^ (]+)', line)
            require(helper is not None and helper[1] in BRIDGES,
                    'Unreviewed observer/call after undefined AF store')
    return {'policy': 'single-final-SAR-AF-arbitrary-zero', 'instruction': 'SAR EAX,1',
            'undefined_calls': 1, 'call_ssa': root, 'store': store, 'state_offset': 2069,
            'width': 1, 'defined_exit_flags_mask': 0xcc5, 'excluded_exit_flag': 'AF',
            'architectural_AF_compatibility_claim': False, 'value_has_only_AF_store_use': True,
            'subsequent_AF_reads': 0, 'not_a_dead_store_proof': True,
            'checked_unconditional_block_chain': chain,
            'return_bridge_contract': 'checked guest32 return; AF excluded from architectural observation'}


def admit_slice_record(path):
    record = json.loads(path.read_text(encoding='utf-8-sig'))
    require(record.get('image_sha256') == IMAGE_SHA and record.get('code_sha256') == CODE_SHA and
            record.get('entry_va') == ENTRY and record.get('end_va') == END and
            record.get('code_bytes') == 43 and record.get('code_file_offset') == 0x157690,
            'Private full-function image/extraction binding differs')
    for key, expected in (('image_path', IMAGE_SHA), ('code_path', CODE_SHA)):
        require(digest(Path(record[key])) == expected, 'Private image/code changed before adapter: ' + key)
    global_page = record['global_page']
    require(global_page['base'] == 0x72c000 and global_page['size'] == 4096 and
            Path(global_page['initial_path']).read_bytes() == bytes(4096) and
            digest(Path(global_page['initial_path'])) == global_page['initial_sha256'],
            'Guest global zero-fill mapping differs')
    for name, expected in record['source_tools'].items():
        require(digest(Path(name)) == expected, 'Extraction source/tool binding changed: ' + name)
    return record


def state_fields(layouts):
    """Named observations, each derived from the complete LLVM struct proof."""
    x = layouts['struct.X86State']['offsets']
    fields = {}
    def field(name, offset, width, **details):
        fields[name] = {'offset': offset, 'bytes': width, **details}
    gpr = layouts['struct.GPR']['offsets']
    for name, index in {'EAX': 1, 'ECX': 5, 'EDX': 7, 'EBX': 3, 'ESP': 13,
                        'EBP': 15, 'ESI': 9, 'EDI': 11, 'EIP': 33}.items():
        field(name, x[6] + gpr[index] + layouts['struct.Reg']['offsets'][0], 4)
    flags = layouts['struct.ArithFlags']['offsets']
    for name, index in {'CF': 1, 'PF': 3, 'AF': 5, 'ZF': 7, 'SF': 9, 'DF': 11, 'OF': 13}.items():
        field(name, x[2] + flags[index], 1)
    field('vector_storage', x[1], 32 * layouts['union.VectorReg']['size'], count=32, stride=64)
    field('logical_x87_storage', x[7], layouts['struct.X87Stack']['size'], count=8, stride=16)
    for i in range(8):
        field(f'logical_ST{i}_raw80', x[7] + i * layouts['struct.anon.3']['size'] +
              layouts['struct.anon.3']['offsets'][1], layouts['struct.float80_t']['size'])
    field('MMX_storage', x[8], layouts['struct.MMX']['size'], count=8, stride=16)
    for i in range(8):
        field(f'MMX{i}', x[8] + i * layouts['struct.anon.4']['size'] +
              layouts['struct.anon.4']['offsets'][1], 8)
    sw = layouts['struct.FPUStatusFlags']['offsets']
    for name, index in {'C0': 1, 'C1': 3, 'C2': 5, 'C3': 7, 'PE': 9, 'UE': 11,
                        'OE': 13, 'ZE': 15, 'DE': 17, 'IE': 19, 'SF': 21}.items():
        field('x87_' + name, x[9] + sw[index], 1)
    fpu = x[11] + layouts['union.FPU']['offsets'][0] + layouts['struct.anon.11']['offsets'][0]
    fx = layouts['struct.FpuFXSAVE']['offsets']
    for name, index, width in [('CW', 0, 2), ('SW', 1, 2), ('physical_FTW', 2, 1), ('FOP', 4, 2),
                              ('FIP', 5, 4), ('FCS', 6, 2), ('FDP', 8, 4), ('FDS', 9, 2),
                              ('MXCSR', 11, 4), ('MXCSR_MASK', 12, 4)]:
        field('x87_' + name, fpu + fx[index], width)
    fields['x87_TOP'] = {**fields['x87_SW'], 'bit_offset': 11, 'bit_width': 3}
    field('legacy_fxsave_guest_storage', fpu, layouts['union.FPU']['size'])
    return fields


def adapt(dll, guest, host, record, slice_record):
    private_root = (ROOT / 'reports/m3-slice').resolve()
    require(all(path.resolve().is_relative_to(private_root) for path in (guest, host, record, slice_record)),
            'Private game IR/layout must remain in ignored M3 reports')
    require(digest(dll) == LLVM_DLL_SHA, 'Unreviewed LLVM DLL identity')
    require(digest(guest) == REVIEWED_IR, 'Guest IR differs from exact reviewed whole-function identity')
    image = admit_slice_record(slice_record)
    upstream = ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp'
    primary = upstream.read_text()
    require(re.search(r'uint8_t __remill_undefined_8\(void\)\s*\{\s*return 0;\s*}', primary),
            'Reviewed upstream undefined-value contract changed')
    for name in FLAG_HELPERS:
        require(re.search(r'bool ' + name + r'\(bool result, \.\.\.\)\s*\{\s*return result;\s*}', primary),
                'Reviewed upstream flag identity changed')
    source = guest.read_text()
    require(re.findall(r'^define .*?@([^ (]+)', source, re.M) == ['sub_558290'], 'Entry identity differs')
    require(not re.search(r'\b(?:undef|poison|atomic|volatile|inttoptr|ptrtoint|x86_fp80|float|double)\b', source),
            'Unsupported operation in integer whole-function slice')
    api = LLVM(dll)
    for name, result, args in (('SetLinkage', None, [c.c_void_p, c.c_uint]),
                               ('IsAStoreInst', c.c_void_p, [c.c_void_p])):
        function = getattr(api.dll, 'LLVM' + name)
        function.restype, function.argtypes = result, args
        setattr(api, name, function)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    gd = hd = builder = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        guest_layout = api.GetDataLayoutStr(module).decode()
        gd, hd = api.CreateTargetData(guest_layout.encode()), api.CreateTargetData(HOST_LAYOUT.encode())
        require((api.PointerSize(gd), api.PointerSize(hd)) == (4, 8), 'Unexpected pointer widths')
        layouts = {}
        for name in re.findall(r'^%([^ =]+) = type', source, re.M):
            ty = api.GetTypeByName2(context, name.encode())
            require(ty and not api.IsOpaqueStruct(ty), 'Missing/opaque State storage')
            def layout(data):
                return {'size': api.ABISizeOfType(data, ty), 'alignment': api.ABIAlignmentOfType(data, ty),
                        'offsets': [api.OffsetOfElement(data, ty, i) for i in range(api.CountStructElementTypes(ty))]}
            before, after = layout(gd), layout(hd)
            require(before == after, 'Guest/host structure layout differs: ' + name)
            layouts[name] = before
        require(layouts.get('struct.State', {}).get('size') == 3504, 'Unexpected State storage')
        entry = api.GetNamedFunction(module, b'sub_558290')
        require(entry and api.signature(entry) == ('ptr', ['ptr', 'i32', 'ptr']) and
                not api.IsFunctionVarArg(api.GlobalGetValueType(entry)), 'Entry signature differs')
        offsets = checked_state_offsets(api, entry, gd)
        require({name: offsets.get(name) for name in ('%EAX', '%EDX', '%ESP', '%PC')} ==
                {'%EAX': 2216, '%EDX': 2264, '%ESP': 2312, '%PC': 2472}, 'Reviewed GPR layout differs')
        af = prove_final_af(source, offsets)
        writes = []
        call_counts = {}
        for block_index, block in enumerate(api.iterate(api.GetFirstBasicBlock(entry), api.GetNextBasicBlock)):
            for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                if api.IsAStoreInst(instruction):
                    line = rendered(api, instruction).strip()
                    pointer = re.search(r', ptr (' + SSA + r'), align ', line)
                    require(pointer is not None, 'Unreviewed store destination')
                    name = pointer[1]
                    if name in offsets:
                        offset = offsets[name]
                        width = api.ABISizeOfType(gd, api.TypeOf(api.GetOperand(instruction, 0)))
                        require(offset in FIELDS and width == FIELDS[offset][1], 'Unreviewed State store range')
                        writes.append({'offset': offset, 'width': width, 'field': FIELDS[offset][0],
                                       'destination_ssa': name, 'block_index': block_index, 'instruction': line})
                    else:
                        require(name in {'%MONITOR', '%STATE', '%MEMORY', '%NEXT_PC'}, 'Unknown indirect/aliased store')
                if api.IsACallInst(instruction):
                    callee = api.GetCalledValue(instruction)
                    require(api.IsAFunction(callee), 'Indirect host IR call')
                    name = api.name(callee)
                    call_counts[name] = call_counts.get(name, 0) + 1
        require(call_counts == CALL_COUNTS, 'Exact reviewed helper/bridge call counts differ')
        require({item['offset'] for item in writes} == set(FIELDS), 'Incomplete expected State store observation')
        undefined = api.GetNamedFunction(module, b'__remill_undefined_8')
        uses = list(api.iterate(api.GetFirstUse(undefined), api.GetNextUse))
        require(len(uses) == 1, 'Undefined helper use set differs')
        call = api.GetUser(uses[0])
        require(api.IsACallInst(call) and api.GetCalledValue(call) == undefined, 'Undefined helper escapes call')
        value_uses = list(api.iterate(api.GetFirstUse(call), api.GetNextUse))
        require(len(value_uses) == 1 and api.IsAStoreInst(api.GetUser(value_uses[0])) and
                api.GetOperand(api.GetUser(value_uses[0]), 0) == call, 'Undefined flag LLVM use closure leaks')
        builder = api.CreateBuilderInContext(context)
        nounwind = api.GetEnumAttributeKindForName(b'nounwind', 8)
        lowered, bridges = [], []
        for function in list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction)):
            name = api.name(function)
            if name != 'sub_558290':
                require(not api.CountBasicBlocks(function) and api.GetFirstUse(function), 'Unexpected helper definition/unused declaration')
                signature = api.signature(function)
                variadic = bool(api.IsFunctionVarArg(api.GlobalGetValueType(function)))
                if name in FLAG_HELPERS:
                    require(signature == ('i1', ['i1']) and variadic, 'Flag annotation signature differs')
                    block = api.AppendBasicBlockInContext(context, function, b'identity')
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.GetParam(function, 0))
                    api.SetLinkage(function, 8)
                    lowered.append(name)
                elif name == '__remill_undefined_8':
                    require(signature == ('i8', []) and not variadic, 'Undefined flag signature differs')
                    block = api.AppendBasicBlockInContext(context, function, b'reviewed_final_SAR_AF')
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.ConstInt(api.GetReturnType(api.GlobalGetValueType(function)), 0, 0))
                    api.SetLinkage(function, 8)
                elif name in BRIDGES:
                    require(signature == BRIDGES[name] and not variadic, 'Guest32 bridge signature differs')
                    bridges.append(name)
                else:
                    require(name == 'llvm.ctpop.i8' and signature == ('i8', ['i8']) and not variadic, 'Unknown external helper: ' + name)
            api.SetFunctionCallConv(function, 0)
            api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for attr in (b'target-cpu', b'target-features'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attr, len(attr))
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    require(not api.IsAIntToPtrInst(instruction) and not api.IsAPtrToIntInst(instruction), 'Pointer/integer conversion')
                    if api.IsACallInst(instruction):
                        api.SetInstructionCallConv(instruction, 0)
                        api.RemoveCallSiteEnumAttribute(instruction, FUNCTION_INDEX, nounwind)
        api.SetLinkage(entry, 8)
        wrapper = api.AddFunction(module, b'mw34_lifted_entry', api.GlobalGetValueType(entry))
        block = api.AppendBasicBlockInContext(context, wrapper, b'entry')
        api.PositionBuilderAtEnd(builder, block)
        args = (c.c_void_p * 3)(*(api.GetParam(wrapper, i) for i in range(3)))
        call = api.BuildCall2(builder, api.GlobalGetValueType(entry), entry, args, 3, b'memory')
        api.SetInstructionCallConv(call, 0)
        api.BuildRet(builder, call)
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        host.parent.mkdir(parents=True, exist_ok=True)
        api.check(api.PrintModuleToFile(module, str(host.resolve()).encode(), c.byref(error)), error)
        ranges = [{'offset': offset, 'bytes': width, 'width': width, 'field': field,
                   'store_count': sum(item['offset'] == offset for item in writes)}
                  for offset, (field, width) in sorted(FIELDS.items())]
        report = {'schema_version': 1, 'profile': 'm3-whole-function-558290', 'entry_va': ENTRY,
                  'end_va': END, 'source_length': 43, 'image_sha256': IMAGE_SHA, 'code_sha256': CODE_SHA,
                  'slice_record_sha256': digest(slice_record), 'guest_ir_identity_reviewed': True,
                  'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
                  'llvm_version': api.version, 'dll_sha256': digest(dll),
                  'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT, 'state_bytes': 3504,
                  'guest_pointer_bits': 32, 'host_pointer_bits': 64, 'all_struct_layouts_equal': True,
                  'struct_layouts': layouts, 'state_gep_offsets': offsets, 'state_fields': state_fields(layouts),
                  'state_write_ranges': ranges, 'state_writes': writes,
                  'all_other_State_bytes_preserved': True, 'state_write_proof': 'LLVM store operands/types and constant GEP offsets under equal full layouts',
                  'bridges': sorted(bridges), 'call_counts': call_counts,
                  'bridge_calls': {name: call_counts[name] for name in sorted(BRIDGES)},
                  'flag_annotation_identities': sorted(lowered), 'undefined_flag_policy': af,
                  'host_abi': 'Windows x64 C: ptr State*, i32 guestPC, ptr checked guest-memory Context*; returns same Context*',
                  'host_entry': 'mw34_lifted_entry', 'indirect_host_calls': 0,
                  'pointer_integer_conversions': 0, 'semantic_repairs': [],
                  'global_page': image['global_page'], 'stack_page': image['stack_page'],
                  'upstream_identity_contract': {'path': str(ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp'),
                   'sha256': digest(ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp'),
                   'undefined8_line': 470, 'flag_identity_lines': [498, 502, 506, 510]}}
        record.write_text(json.dumps(report, indent=2) + '\n')
        return report
    finally:
        if builder:
            api.DisposeBuilder(builder)
        for data in (gd, hd):
            if data:
                api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(context)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('llvm-dll', 'guest', 'host', 'record', 'slice-record'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = adapt(args.llvm_dll, args.guest, args.host, args.record, args.slice_record)
    print(json.dumps({'profile': result['profile'], 'guest_ir_sha256': result['guest_ir_sha256'],
                      'host_ir_sha256': result['host_ir_sha256'], 'state_write_ranges': result['state_write_ranges']}))
