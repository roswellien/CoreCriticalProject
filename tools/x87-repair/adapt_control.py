"""Retarget authored store/load-store probes with already repaired semantics."""
import argparse
import ctypes as c
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, digest

BASE_BRIDGES = {
    '__remill_write_memory_16': ('ptr', ['ptr', 'i32', 'i16']),
    '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
    '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
}


class ControlLLVM(LLVM):
    def signature(self, function):
        if self.GetTypeKind(self.GetReturnType(self.GlobalGetValueType(function))) == 0:
            return 'void', [self.kind(self.GetParam(function, i)) for i in range(self.CountParams(function))]
        return super().signature(function)


def adapt(dll, guest, host, record, kind='store'):
    if kind not in ('store', 'load-store'):
        raise ValueError('Unknown reviewed control repair profile')
    bridges = dict(BASE_BRIDGES)
    if kind == 'load-store':
        bridges.update({'__remill_read_memory_16': ('i16', ['ptr', 'i32']),
                        '__remill_fpu_set_rounding': ('void', ['i32'])})
    source = guest.read_text()
    if re.findall(r'^define .*?@([^ (]+)', source, re.M) != ['sub_10000000']:
        raise ValueError('Requires only the authored entry at 0x10000000')
    # This experiment has no floating-point SSA operations, arithmetic or havoc.
    if re.search(r'\b(?:undef|poison|x86_fp80|float|double|atomic|volatile)\b', source):
        raise ValueError('Unsupported operation in control-word-only probe')
    api = ControlLLVM(dll)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    guest_data = host_data = builder = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(),
                  c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        guest_layout = api.GetDataLayoutStr(module).decode()
        guest_data = api.CreateTargetData(guest_layout.encode())
        host_data = api.CreateTargetData(HOST_LAYOUT.encode())
        if (api.PointerSize(guest_data), api.PointerSize(host_data)) != (4, 8):
            raise ValueError('Incorrect guest/host pointer widths')
        layouts = {}
        for name in re.findall(r'^%([^ =]+) = type', source, re.M):
            structure = api.GetTypeByName2(context, name.encode())
            if not structure or api.IsOpaqueStruct(structure):
                raise ValueError('Missing concrete State storage type')
            def layout(data):
                return {'size': api.ABISizeOfType(data, structure),
                        'alignment': api.ABIAlignmentOfType(data, structure),
                        'offsets': [api.OffsetOfElement(data, structure, i)
                                    for i in range(api.CountStructElementTypes(structure))]}
            before, after = layout(guest_data), layout(host_data)
            if before != after:
                raise ValueError('Guest State layout changes: ' + name)
            layouts[name] = before
        if layouts.get('struct.State', {}).get('size') != 3504:
            raise ValueError('Unexpected State size')
        entry = api.GetNamedFunction(module, b'sub_10000000')
        if api.signature(entry) != ('ptr', ['ptr', 'i32', 'ptr']) or \
                api.IsFunctionVarArg(api.GlobalGetValueType(entry)):
            raise ValueError('Unexpected entry signature')
        if api.GetNamedFunction(module, b'mw34_lifted_entry'):
            raise ValueError('Duplicate host entry')
        nounwind = api.GetEnumAttributeKindForName(b'nounwind', 8)
        counts = {name: 0 for name in bridges}
        for function in api.iterate(api.GetFirstFunction(module), api.GetNextFunction):
            name = api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function):
                if name not in bridges or api.signature(function) != bridges[name] or \
                        api.IsFunctionVarArg(api.GlobalGetValueType(function)):
                    raise ValueError('Unsupported bridge or signature: ' + name)
                api.SetFunctionCallConv(function, 0)
            for attribute in (b'target-cpu', b'target-features'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attribute, len(attribute))
            api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    if api.IsAIntToPtrInst(instruction) or api.IsAPtrToIntInst(instruction):
                        raise ValueError('Pointer/integer conversion rejected')
                    if api.IsACallInst(instruction):
                        called = api.GetCalledValue(instruction)
                        if not api.IsAFunction(called) or api.name(called) not in bridges:
                            raise ValueError('Indirect or unreviewed call rejected')
                        counts[api.name(called)] += 1
                        api.SetInstructionCallConv(instruction, 0)
                        api.RemoveCallSiteEnumAttribute(instruction, FUNCTION_INDEX, nounwind)
        if any(value != 1 for value in counts.values()):
            raise ValueError('Requires exactly one call to each reviewed control probe bridge')
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        builder = api.CreateBuilderInContext(context)
        wrapper = api.AddFunction(module, b'mw34_lifted_entry', api.GlobalGetValueType(entry))
        block = api.AppendBasicBlockInContext(context, wrapper, b'entry')
        api.PositionBuilderAtEnd(builder, block)
        args = (c.c_void_p * 3)(*(api.GetParam(wrapper, i) for i in range(3)))
        call = api.BuildCall2(builder, api.GlobalGetValueType(entry), entry, args, 3, b'memory')
        api.SetInstructionCallConv(call, api.GetFunctionCallConv(entry))
        api.BuildRet(builder, call)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        api.check(api.PrintModuleToFile(module, str(host.resolve()).encode(), c.byref(error)), error)
        record.write_text(json.dumps({
            'schema_version': 1, 'profile': 'repaired_cw_' + kind, 'kind': kind,
            'entry_va': 0x10000000, 'authored_bytes': 'd939c3' if kind == 'store' else 'd929d93ac3',
            'llvm_version': api.version, 'dll_sha256': digest(dll),
            'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
            'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT,
            'guest_pointer_bits': 32, 'host_pointer_bits': 64,
            'state_bytes': 3504, 'all_struct_layouts_equal': True,
            'struct_layouts': layouts, 'bridge_calls': counts,
            'semantic_repairs': [], 'undefined_helpers': [],
        }, indent=2) + '\n')
    finally:
        if builder:
            api.DisposeBuilder(builder)
        for data in (guest_data, host_data):
            if data:
                api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(context)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('llvm-dll', 'guest', 'host', 'record'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--kind', choices=('store', 'load-store'), required=True)
    args = parser.parse_args()
    adapt(args.llvm_dll, args.guest, args.host, args.record, args.kind)
