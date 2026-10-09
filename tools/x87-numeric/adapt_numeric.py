"""Exact authored arithmetic profile; preserve FP effects under optimization.

This accepts only the pinned lifter's reviewed IR for the ten-byte fixture.
It is deliberately not a general arithmetic or game-function adapter.
"""
import argparse
import ctypes as c
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, digest

GUEST_SHA256 = '2cc05e95814d0d7c533a26e9a6bc1c3eb398a34e58085330fcfb9429eec304c9'
BRIDGES = {
    '__remill_read_memory_f64': ('double', ['ptr', 'i32']),
    '__remill_write_memory_f64': ('ptr', ['ptr', 'i32', 'double']),
    '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
    '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
    '__remill_fpu_exception_clear': ('void', ['i32']),
    '__remill_fpu_exception_test': ('i32', ['i32']),
    '__remill_undefined_8': ('i8', []),
}
COUNTS = dict(zip(BRIDGES, (3, 1, 1, 1, 3, 3, 3)))


class NumericLLVM(LLVM):
    def type_name(self, typ):
        kind = self.GetTypeKind(typ)
        if kind in (0, 1, 2, 3, 4, 14):
            return {0: 'void', 1: 'half', 2: 'float', 3: 'double',
                    4: 'x86_fp80', 14: 'metadata'}[kind]
        if kind == 8:
            return 'i' + str(self.GetIntTypeWidth(typ))
        if kind == 12:
            return 'ptr'
        raise ValueError('Unreviewed boundary type')

    def signature(self, function):
        return (self.type_name(self.GetReturnType(self.GlobalGetValueType(function))),
                [self.type_name(self.TypeOf(self.GetParam(function, i)))
                 for i in range(self.CountParams(function))])


def constrain(source):
    # Exact source identity makes these replacements fail closed to new IR.
    declarations = []
    for op in ('fadd', 'fsub'):
        pattern = rf'^(  %\d+) = {op} x86_fp80 (%\d+), (%\d+)$'
        source, count = re.subn(pattern, rf'\1 = call x86_fp80 @llvm.experimental.constrained.{op}.f80(x86_fp80 \2, x86_fp80 \3, metadata !"round.dynamic", metadata !"fpexcept.strict")', source, flags=re.M)
        if count != 1:
            raise ValueError('Arithmetic instruction count changed')
        declarations.append(f'declare x86_fp80 @llvm.experimental.constrained.{op}.f80(x86_fp80, x86_fp80, metadata, metadata)')
    source, count = re.subn(r'^(  %\d+) = fptrunc x86_fp80 (%\d+) to double$', r'\1 = call double @llvm.experimental.constrained.fptrunc.f64.f80(x86_fp80 \2, metadata !"round.dynamic", metadata !"fpexcept.strict")', source, flags=re.M)
    if count != 1:
        raise ValueError('Store conversion count changed')
    declarations.append('declare double @llvm.experimental.constrained.fptrunc.f64.f80(x86_fp80, metadata, metadata)')
    source, count = re.subn(r'^(  %\d+) = fpext double (%\d+) to x86_fp80$', r'\1 = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double \2, metadata !"fpexcept.strict")', source, flags=re.M)
    if count != 3:
        raise ValueError('Load extension count changed')
    declarations.append('declare x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double, metadata)')
    source = source.replace('ptr noalias %memory) {', 'ptr noalias %memory) strictfp {', 1)
    # These comparisons only classify admitted finite, normal values/zeros.
    # They neither round nor raise exceptions on this bounded domain.
    return source + '\n' + '\n'.join(declarations) + '\n'


def adapt(dll, guest, host, record):
    if digest(guest) != GUEST_SHA256:
        raise ValueError('IR differs from the exact reviewed arithmetic profile')
    source = guest.read_text()
    transformed = constrain(source)
    api = NumericLLVM(dll)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    builder = guest_data = host_data = None
    try:
        path = host.with_suffix('.strict-input.ll')
        path.write_text(transformed)
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(path.resolve()).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        guest_layout = api.GetDataLayoutStr(module).decode()
        guest_data = api.CreateTargetData(guest_layout.encode())
        host_data = api.CreateTargetData(HOST_LAYOUT.encode())
        if (api.PointerSize(guest_data), api.PointerSize(host_data)) != (4, 8):
            raise ValueError('Incorrect pointer width')
        layouts = {}
        for name in re.findall(r'^%([^ =]+) = type', source, re.M):
            typ = api.GetTypeByName2(context, name.encode())
            def layout(data):
                return {'size': api.ABISizeOfType(data, typ), 'alignment': api.ABIAlignmentOfType(data, typ),
                        'offsets': [api.OffsetOfElement(data, typ, i) for i in range(api.CountStructElementTypes(typ))]}
            before, after = layout(guest_data), layout(host_data)
            if before != after:
                raise ValueError('State layout changes: ' + name)
            layouts[name] = before
        if layouts['struct.State']['size'] != 3504:
            raise ValueError('State size differs')
        entry = api.GetNamedFunction(module, b'sub_10000000')
        if api.signature(entry) != ('ptr', ['ptr', 'i32', 'ptr']):
            raise ValueError('Entry ABI differs')
        nounwind = api.GetEnumAttributeKindForName(b'nounwind', 8)
        counts = {name: 0 for name in BRIDGES}
        for function in api.iterate(api.GetFirstFunction(module), api.GetNextFunction):
            name = api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function) and not name.startswith('llvm.'):
                if name not in BRIDGES or api.signature(function) != BRIDGES[name] or api.IsFunctionVarArg(api.GlobalGetValueType(function)):
                    raise ValueError('Unreviewed bridge: ' + name)
                api.SetFunctionCallConv(function, 0)
            for attribute in (b'target-cpu', b'target-features', b'no-trapping-math'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attribute, len(attribute))
            api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for inst in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    if api.IsAIntToPtrInst(inst) or api.IsAPtrToIntInst(inst):
                        raise ValueError('Pointer/integer conversion')
                    if api.IsACallInst(inst):
                        called = api.GetCalledValue(inst)
                        if not api.IsAFunction(called):
                            # Only the exact source's six empty compiler barriers.
                            continue
                        name = api.name(called)
                        if name in BRIDGES:
                            counts[name] += 1
                            api.SetInstructionCallConv(inst, 0)
                        api.RemoveCallSiteEnumAttribute(inst, FUNCTION_INDEX, nounwind)
        if counts != COUNTS:
            raise ValueError('Bridge call counts differ')
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        builder = api.CreateBuilderInContext(context)
        wrapper = api.AddFunction(module, b'mw34_lifted_entry', api.GlobalGetValueType(entry))
        block = api.AppendBasicBlockInContext(context, wrapper, b'entry')
        api.PositionBuilderAtEnd(builder, block)
        args = (c.c_void_p * 3)(*(api.GetParam(wrapper, i) for i in range(3)))
        call = api.BuildCall2(builder, api.GlobalGetValueType(entry), entry, args, 3, b'memory')
        api.BuildRet(builder, call)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        api.check(api.PrintModuleToFile(module, str(host.resolve()).encode(), c.byref(error)), error)
        record.write_text(json.dumps({'schema_version': 1, 'profile': 'x87_numeric_add_sub',
            'entry_va': 0x10000000, 'authored_bytes': 'dd01dc4108dc21dd1ac3',
            'llvm_version': api.version, 'dll_sha256': digest(dll),
            'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
            'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT,
            'guest_pointer_bits': 32, 'host_pointer_bits': 64, 'state_bytes': 3504,
            'all_struct_layouts_equal': True, 'struct_layouts': layouts, 'bridge_calls': counts,
            'constrained_operations': {'fadd': 1, 'fsub': 1, 'fptrunc': 1, 'fpext': 3},
            'rounding': 'dynamic', 'exceptions': 'strict',
            'undefined_helpers': {'__remill_undefined_8': {'calls': 3, 'only_store_offsets': [2737, 2741, 2743], 'observed': False}},
            'scope': 'exact authored IR only; normal directed corpus; host x87 arithmetic'}, indent=2) + '\n')
    finally:
        if builder: api.DisposeBuilder(builder)
        for data in (guest_data, host_data):
            if data: api.DisposeTargetData(data)
        if module.value: api.DisposeModule(module)
        api.ContextDispose(context)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('llvm-dll', 'guest', 'host', 'record'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    adapt(args.llvm_dll, args.guest, args.host, args.record)
