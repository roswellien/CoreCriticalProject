"""Exact authored spill and valid FISTP32 profiles; strict FP retargeting."""
import argparse
import ctypes as c
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, digest

BRIDGES = {
    '__remill_read_memory_f64': ('double', ['ptr', 'i32']),
    '__remill_write_memory_f64': ('ptr', ['ptr', 'i32', 'double']),
    '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
    '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
    '__remill_fpu_exception_clear': ('void', ['i32']),
    '__remill_fpu_exception_test': ('i32', ['i32']),
    '__remill_undefined_8': ('i8', []),
}


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


SPEC = {
    'spill64': {
        'sha256': '21e7331b94cf78dd30f4323f068da0e069611f657514936150a3f7409d3b2747',
        'bytes': 'dd01dc4108dd5a08dd4208dc21dd1ac3',
        'bridges': dict(BRIDGES),
        'counts': dict(zip(BRIDGES, (4, 2, 1, 1, 4, 4, 3))),
        'operations': {'fadd': 1, 'fsub': 1, 'fptrunc': 2, 'fpext': 4},
    },
    'fistp32': {
        'sha256': 'bc7e0f03047c9310470d75ce4baa048a1af07987619f986ff43cea3cc29e24a5',
        'bytes': 'dd01db1ac3',
        'bridges': {
            '__remill_read_memory_f64': ('double', ['ptr', 'i32']),
            '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
            '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
            '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
            '__remill_fpu_exception_clear': ('void', ['i32']),
            '__remill_fpu_exception_test': ('i32', ['i32']),
            '__mw34_x87_nearbyint80': ('void', ['ptr', 'ptr']),
        },
        'counts': {name: 1 for name in ('__remill_read_memory_f64', '__remill_write_memory_32',
                   '__remill_read_memory_32', '__remill_function_return', '__remill_fpu_exception_clear', '__remill_fpu_exception_test', '__mw34_x87_nearbyint80')},
        'operations': {'fptosi': 1, 'sitofp': 1, 'fpext': 1},
    },
}


def constrain(source, profile):
    declarations = []
    dynamic = 'metadata !"round.dynamic", metadata !"fpexcept.strict"'
    strict = 'metadata !"fpexcept.strict"'
    if profile == 'fistp32':
        # Windows CRT long double is binary64, while this LLVM value is80-bit.
        # Only pointers to reviewed10-byte temporary storage cross the C ABI.
        pattern = r'^(  %\d+) = call x86_fp80 @llvm.nearbyint.f80\(x86_fp80 (%\d+)\)$'
        replacement = (r'  %round_input = alloca x86_fp80, align 16\n'
                       r'  %round_output = alloca x86_fp80, align 16\n'
                       r'  store x86_fp80 \2, ptr %round_input, align 16\n'
                       r'  call void @__mw34_x87_nearbyint80(ptr %round_input, ptr %round_output)\n'
                       r'\1 = load x86_fp80, ptr %round_output, align 16')
        source, count = re.subn(pattern, replacement, source, flags=re.M)
        if count != 1:
            raise ValueError('Nearbyint bridge lowering count differs')
        declarations.append('declare void @__mw34_x87_nearbyint80(ptr, ptr)')
    for op, expected in SPEC[profile]['operations'].items():
        if op in ('fadd', 'fsub'):
            name = f'llvm.experimental.constrained.{op}.f80'
            pattern = rf'^(  %\d+) = {op} x86_fp80 (%\d+), (%\d+)$'
            replacement = rf'\1 = call x86_fp80 @{name}(x86_fp80 \2, x86_fp80 \3, {dynamic})'
            signature = f'declare x86_fp80 @{name}(x86_fp80, x86_fp80, metadata, metadata)'
        elif op == 'fptrunc':
            name = 'llvm.experimental.constrained.fptrunc.f64.f80'
            pattern = r'^(  %\d+) = fptrunc x86_fp80 (%\d+) to double$'
            replacement = rf'\1 = call double @{name}(x86_fp80 \2, {dynamic})'
            signature = f'declare double @{name}(x86_fp80, metadata, metadata)'
        elif op == 'fpext':
            name = 'llvm.experimental.constrained.fpext.f80.f64'
            pattern = r'^(  %\d+) = fpext double (%\d+) to x86_fp80$'
            replacement = rf'\1 = call x86_fp80 @{name}(double \2, {strict})'
            signature = f'declare x86_fp80 @{name}(double, metadata)'
        elif op == 'nearbyint':
            name = 'llvm.experimental.constrained.nearbyint.f80'
            pattern = r'^(  %\d+) = call x86_fp80 @llvm.nearbyint.f80\(x86_fp80 (%\d+)\)$'
            replacement = rf'\1 = call x86_fp80 @{name}(x86_fp80 \2, {dynamic})'
            signature = f'declare x86_fp80 @{name}(x86_fp80, metadata, metadata)'
        elif op == 'fptosi':
            # The preceding nearbyint performs guest RC rounding; every admitted
            # rounded input fits signed32, so this truncation is exact and defined.
            name = 'llvm.experimental.constrained.fptosi.i32.f80'
            pattern = r'^(  %\d+) = fptosi x86_fp80 (%\d+) to i32$'
            replacement = rf'\1 = call i32 @{name}(x86_fp80 \2, {strict})'
            signature = f'declare i32 @{name}(x86_fp80, metadata)'
        elif op == 'sitofp':
            name = 'llvm.experimental.constrained.sitofp.f80.i32'
            pattern = r'^(  %\d+) = sitofp i32 (%\d+) to x86_fp80$'
            replacement = rf'\1 = call x86_fp80 @{name}(i32 \2, {dynamic})'
            signature = f'declare x86_fp80 @{name}(i32, metadata, metadata)'
        else:
            raise ValueError('Unreviewed constrained operation')
        source, count = re.subn(pattern, replacement, source, flags=re.M)
        if count != expected:
            raise ValueError('Reviewed operation count changed: ' + op)
        declarations.append(signature)
    source = source.replace('ptr noalias %memory) {', 'ptr noalias %memory) strictfp {', 1)
    return source + '\n' + '\n'.join(declarations) + '\n'


def adapt(dll, guest, host, record, profile):
    if profile not in SPEC:
        raise ValueError('Unreviewed expansion profile')
    bridges = SPEC[profile]['bridges']
    expected_counts = SPEC[profile]['counts']
    if digest(guest) != SPEC[profile]['sha256']:
        raise ValueError('IR differs from the exact reviewed arithmetic profile')
    source = guest.read_text()
    transformed = constrain(source, profile)
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
        counts = {name: 0 for name in bridges}
        for function in api.iterate(api.GetFirstFunction(module), api.GetNextFunction):
            name = api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function) and not name.startswith('llvm.'):
                if name not in bridges or api.signature(function) != bridges[name] or api.IsFunctionVarArg(api.GlobalGetValueType(function)):
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
                        if name in bridges:
                            counts[name] += 1
                            api.SetInstructionCallConv(inst, 0)
                        api.RemoveCallSiteEnumAttribute(inst, FUNCTION_INDEX, nounwind)
        if counts != expected_counts:
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
        record.write_text(json.dumps({'schema_version': 1, 'profile': 'x87_expand_' + profile,
            'entry_va': 0x10000000, 'authored_bytes': SPEC[profile]['bytes'],
            'llvm_version': api.version, 'dll_sha256': digest(dll),
            'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
            'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT,
            'guest_pointer_bits': 32, 'host_pointer_bits': 64, 'state_bytes': 3504,
            'all_struct_layouts_equal': True, 'struct_layouts': layouts, 'bridge_calls': counts,
            'constrained_operations': SPEC[profile]['operations'],
            'bridge_lowerings': ({'llvm.nearbyint.f80': {'bridge': '__mw34_x87_nearbyint80', 'calls': 1, 'storage_bytes': 10,
                'host_exceptions_preserved': True}} if profile == 'fistp32' else {}),
            'rounding': 'dynamic', 'exceptions': 'strict',
            'undefined_helpers': ({'__remill_undefined_8': {'calls': 3, 'only_store_offsets': [2737, 2741, 2743], 'observed': False}} if profile == 'spill64' else {}),
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
    parser.add_argument('--kind', choices=SPEC, required=True)
    args = parser.parse_args()
    adapt(args.llvm_dll, args.guest, args.host, args.record, args.kind)
