"""Bounded new call-integration adapter; the earlier gates are untouched."""
import ctypes as c
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, digest, ANNOTATIONS

BLOCKS = {
    'entry': (0x10000000, 10),
    'after_direct': (0x1000000a, 17),
    'after_import': (0x1000001b, 13),
    'after_indirect': (0x10000028, 15),
    'direct': (0x10000200, 25),
    'timer': (0x10000300, 26),
    'choice_add': (0x10000400, 33),
    'choice_sub': (0x10000500, 33),
}
BRIDGES = {
    '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
    '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
    '__remill_function_call': ('ptr', ['ptr', 'i32', 'ptr']),
    '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
    '__remill_missing_block': ('ptr', ['ptr', 'i32', 'ptr']),
    'sub_10000200': ('ptr', ['ptr', 'i32', 'ptr']),
}
REVIEWED_IR = {
    'entry': '9322d1f91965aed985ebdaeeef43fc46c24ef56f5a1c642f1240c0afa9347f85',
    'after_direct': '087a71cbb9a6072e7bcfe91d6fa1046457cad4630646f0f3771beac15d178c0f',
    'after_import': '2d730bfcc3f707ff2d974a79cfed9e17548b37cffd75f3d0b2c50817d6526a01',
    'after_indirect': '87f62aac3cd04ee9b1a5e6e1a972934a6c0ac0730248805b97f2cebb3bdcbffc',
    'direct': '48f6ff6cb5f9cac2a638c8b286d55e2ea2ef82f7cc85a86959bc7e0ab87c8d00',
    'timer': 'a5abea300468db14457b1061ba3600ce33781c3a6fd75128ca3fcabb67f15c52',
    'choice_add': '44c1058759ee5ce98b93e195ed6d15e9192340661a8976915a0ed138cb893f12',
    'choice_sub': '88d9e2a84db43aa8d2e88ab2fa2794887489a55e78c75680d50713f429a79a54',
}

def adapt(dll, guest, host, record, name):
    if name not in BLOCKS:
        raise ValueError('Unknown admitted block')
    if digest(guest) != REVIEWED_IR[name]:
        raise ValueError('Guest IR differs from the independently reviewed authored block identity')
    address, length = BLOCKS[name]
    source = guest.read_text()
    entry_name = f'sub_{address:x}'
    if re.findall(r'^define .*?@([^ (]+)', source, re.M) != [entry_name]:
        raise ValueError('Expected exactly the admitted block entry')
    if re.search(r'\b(?:undef|poison|atomic|volatile|inttoptr|ptrtoint|x86_fp80|float|double)\b', source):
        raise ValueError('Unsupported operation in the bounded integer call probe')
    api = LLVM(dll)
    for method, result, args in (
        ('SetValueName2', None, [c.c_void_p, c.c_char_p, c.c_size_t]),
        ('SetLinkage', None, [c.c_void_p, c.c_uint]),
    ):
        fn = getattr(api.dll, 'LLVM' + method)
        fn.restype, fn.argtypes = result, args
        setattr(api, method, fn)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    gd = hd = builder = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        guest_layout = api.GetDataLayoutStr(module).decode()
        gd, hd = api.CreateTargetData(guest_layout.encode()), api.CreateTargetData(HOST_LAYOUT.encode())
        if (api.PointerSize(gd), api.PointerSize(hd)) != (4, 8):
            raise ValueError('Unexpected pointer widths')
        layouts = {}
        for typename in re.findall(r'^%([^ =]+) = type', source, re.M):
            ty = api.GetTypeByName2(context, typename.encode())
            if not ty or api.IsOpaqueStruct(ty):
                raise ValueError('Opaque or absent State type')
            def layout(data):
                return {'size': api.ABISizeOfType(data, ty), 'alignment': api.ABIAlignmentOfType(data, ty),
                        'offsets': [api.OffsetOfElement(data, ty, i) for i in range(api.CountStructElementTypes(ty))]}
            before, after = layout(gd), layout(hd)
            if before != after:
                raise ValueError('Guest State layout changes: ' + typename)
            layouts[typename] = before
        if layouts.get('struct.State', {}).get('size') != 3504:
            raise ValueError('Unexpected State storage')
        entry = api.GetNamedFunction(module, entry_name.encode())
        if api.signature(entry) != ('ptr', ['ptr', 'i32', 'ptr']):
            raise ValueError('Unreviewed entry signature')
        builder = api.CreateBuilderInContext(context)
        nounwind = api.GetEnumAttributeKindForName(b'nounwind', 8)
        bridges, lowered, call_counts = [], [], {}
        for function in list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction)):
            fn_name = api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function):
                signature = api.signature(function)
                if fn_name in ANNOTATIONS:
                    if signature != ('i1', ['i1']):
                        raise ValueError('Unreviewed annotation signature')
                    block = api.AppendBasicBlockInContext(context, function, b'identity')
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.GetParam(function, 0))
                    api.SetLinkage(function, 8)  # internal; no cross-module identity collision.
                    lowered.append(fn_name)
                elif fn_name in BRIDGES:
                    if signature != BRIDGES[fn_name]:
                        raise ValueError('Unreviewed guest32 bridge signature')
                    bridges.append(fn_name)
                elif fn_name == 'llvm.ctpop.i8' and signature == ('i8', ['i8']):
                    pass
                else:
                    raise ValueError('Unsupported external: ' + fn_name)
            api.SetFunctionCallConv(function, 0)
            api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for attr in (b'target-cpu', b'target-features'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attr, len(attr))
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for insn in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    if api.IsAIntToPtrInst(insn) or api.IsAPtrToIntInst(insn):
                        raise ValueError('Pointer/integer conversion')
                    if api.IsACallInst(insn):
                        if not api.IsAFunction(api.GetCalledValue(insn)):
                            raise ValueError('Indirect host IR call')
                        called_name=api.name(api.GetCalledValue(insn))
                        call_counts[called_name]=call_counts.get(called_name,0)+1
                        api.SetInstructionCallConv(insn, 0)
                        api.RemoveCallSiteEnumAttribute(insn, FUNCTION_INDEX, nounwind)
        native_name = f'mw34_block_{address:x}'.encode()
        api.SetValueName2(entry, native_name, len(native_name))
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        api.check(api.PrintModuleToFile(module, str(host.resolve()).encode(), c.byref(error)), error)
        report = {'schema_version': 1, 'profile': 'm2-call-integration', 'block': name, 'guest_entry': address,
                  'source_length': length, 'llvm_version': api.version, 'guest_ir_sha256': digest(guest),
                  'host_ir_sha256': digest(host), 'dll_sha256': digest(dll), 'guest_layout': guest_layout,
                  'host_layout': HOST_LAYOUT, 'state_bytes': 3504, 'guest_pointer_bits': 32,
                  'host_pointer_bits': 64, 'all_struct_layouts_equal': True, 'struct_layouts': layouts,
                  'bridges': sorted(bridges), 'flag_annotation_identities': sorted(lowered),
                  'guest_ir_identity_reviewed': True, 'call_counts': call_counts,
                  'indirect_host_calls': 0, 'pointer_integer_conversions': 0,
                  'routing': 'admitted guest32 registry; direct and indirect calls share admission'}
        record.write_text(json.dumps(report, indent=2) + '\n')
        return report
    finally:
        if builder: api.DisposeBuilder(builder)
        for data in (gd, hd):
            if data: api.DisposeTargetData(data)
        if module.value: api.DisposeModule(module)
        api.ContextDispose(context)
