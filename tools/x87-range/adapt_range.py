"""Exact authored masked denormal and range profiles; strict FP retargeting."""
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


SPEC = {}
for name, sha, code, op in (
    ('mul64', '2191a98a7e3c2bf4d547a22591c342b79185e9540ebeb0df5ebd056308906a1a', 'dd01dc4908dd1ac3', 'fmul'),
    ('div64', 'b45250c94d0f2b1028670d676e9e28c07a8ebe3f88874da2108b5c7e2012ddf2', 'dd01dc7108dd1ac3', 'fdiv'),
):
    SPEC[name] = {'sha256': sha, 'bytes': code, 'bridges': dict(BRIDGES),
                  'counts': dict(zip(BRIDGES, (2, 1, 1, 1, 2, 2))),
                  'operations': {op: 1, 'fptrunc': 1, 'fpext': 3, 'fcmp_f64': 3, 'fcmp_f80': 6}}



def constrain(source, profile):
    declarations = []
    dynamic = 'metadata !"round.dynamic", metadata !"fpexcept.strict"'
    strict = 'metadata !"fpexcept.strict"'
    # Remill evaluates the m64->80 argument before CheckedFloatBinOp clears
    # host exceptions. A signaling NaN is quieted then, losing its physical IE.
    # Relocate that exact promotion into the existing clear/test region. The
    # original operand bits and arithmetic remain unchanged; no oracle runs here.
    promotion = '  %93 = fpext double %84 to x86_fp80\n'
    operation = 'fmul' if profile.startswith('mul') else 'fdiv'
    arithmetic = f'  %95 = {operation} x86_fp80 %83, %93\n'
    if source.count(promotion) != 1 or source.count(arithmetic) != 1:
        raise ValueError('Reviewed arithmetic promotion repair sites differ')
    region = ('  call void @__remill_fpu_exception_clear(i32 noundef 127) #4\n'
              '  call void asm sideeffect "", "~{memory},~{dirflag},~{fpsr},~{flags}"() #6\n' + arithmetic)
    if source.count(region) != 1:
        raise ValueError('Reviewed exception region differs')
    source = source.replace(promotion, '', 1).replace(arithmetic, promotion + arithmetic, 1)
    # Named SSA avoids moving a numbered definition behind a later slot.
    source = re.sub(r'%93\b', '%memory_operand_promoted', source)
    # Record the final FSTP significand increment from actual generated values.
    # Canonical finite x87 encodings are monotonic in magnitude after removing
    # sign bit79. Re-extending the actual binary64 store is exact and uses no
    # scalar80 C ABI. Nonfinite inputs clear C1 in these admitted masked cases.
    store_site = '  %194 = call noundef ptr @__remill_write_memory_f64('
    if source.count(store_site) != 1:
        raise ValueError('Reviewed final FSTP C1 repair site differs')
    c1_patch = ('  %store_c1_promoted = fpext double %158 to x86_fp80\n'
                '  %store_c1_input_bits = bitcast x86_fp80 %148 to i80\n'
                '  %store_c1_output_bits = bitcast x86_fp80 %store_c1_promoted to i80\n'
                '  %store_c1_input_abs = and i80 %store_c1_input_bits, 604462909807314587353087\n'
                '  %store_c1_output_abs = and i80 %store_c1_output_bits, 604462909807314587353087\n'
                '  %store_c1_exponent = lshr i80 %store_c1_input_abs, 64\n'
                '  %store_c1_is_finite = icmp ne i80 %store_c1_exponent, 32767\n'
                '  %store_c1_incremented = icmp ugt i80 %store_c1_output_abs, %store_c1_input_abs\n'
                '  %store_c1_set = and i1 %store_c1_is_finite, %store_c1_incremented\n'
                '  %store_c1_value = zext i1 %store_c1_set to i8\n'
                '  %store_c1_slot = getelementptr inbounds i8, ptr %state, i32 2739\n'
                '  store i8 %store_c1_value, ptr %store_c1_slot, align 1\n')
    source = source.replace(store_site, c1_patch + store_site, 1)
    # DE is sticky across guest instructions. The original arithmetic/store
    # classifications replaced the previous shadow flag before capturing host
    # exceptions, erasing an earlier FLD's denormal-operand observation.
    for label, value, slot in (('arithmetic', '%92', '%94'),
                               ('store', '%156', '%157')):
        site = f'  store i8 {value}, ptr {slot}, align 1\n'
        if source.count(site) != 1:
            raise ValueError('Reviewed sticky denormal site differs: ' + label)
        patch = (f'  %de_{label}_previous = load i8, ptr {slot}, align 1\n'
                 f'  %de_{label}_accumulated = or i8 %de_{label}_previous, {value}\n'
                 f'  store i8 %de_{label}_accumulated, ptr {slot}, align 1\n')
        source = source.replace(site, patch, 1)
    for op, expected in SPEC[profile]['operations'].items():
        if op in ('fmul', 'fdiv'):
            name = f'llvm.experimental.constrained.{op}.f80'
            pattern = rf'^(  %\d+) = {op} x86_fp80 (%\d+), (%(?:\d+|memory_operand_promoted|store_c1_promoted))$'
            replacement = rf'\1 = call x86_fp80 @{name}(x86_fp80 \2, x86_fp80 \3, {dynamic})'
            signature = f'declare x86_fp80 @{name}(x86_fp80, x86_fp80, metadata, metadata)'
        elif op == 'fptrunc':
            name = 'llvm.experimental.constrained.fptrunc.f64.f80'
            pattern = r'^(  %\d+) = fptrunc x86_fp80 (%\d+) to double$'
            replacement = rf'\1 = call double @{name}(x86_fp80 \2, {dynamic})'
            signature = f'declare double @{name}(x86_fp80, metadata, metadata)'
        elif op == 'fpext':
            name = 'llvm.experimental.constrained.fpext.f80.f64'
            pattern = r'^(  %(?:\d+|memory_operand_promoted|store_c1_promoted)) = fpext double (%\d+) to x86_fp80$'
            replacement = rf'\1 = call x86_fp80 @{name}(double \2, {strict})'
            signature = f'declare x86_fp80 @{name}(double, metadata)'
        elif op in ('fcmp_f64', 'fcmp_f80'):
            ty, suffix = ('double', 'f64') if op == 'fcmp_f64' else ('x86_fp80', 'f80')
            name = f'llvm.experimental.constrained.fcmp.{suffix}'
            pattern = rf'^(  %\d+) = fcmp (ueq|oeq|olt) {ty} (%\d+), ([^\n]+)$'
            replacement = rf'\1 = call i1 @{name}({ty} \3, {ty} \4, metadata !"\2", {strict})'
            signature = f'declare i1 @{name}({ty}, {ty}, metadata, metadata)'
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
        raise ValueError('Unreviewed arithmetic profile')
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
                            # Only the exact source's four empty compiler barriers.
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
        record.write_text(json.dumps({'schema_version': 1, 'profile': 'x87_range_' + profile,
            'entry_va': 0x10000000, 'authored_bytes': SPEC[profile]['bytes'],
            'llvm_version': api.version, 'dll_sha256': digest(dll),
            'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
            'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT,
            'guest_pointer_bits': 32, 'host_pointer_bits': 64, 'state_bytes': 3504,
            'all_struct_layouts_equal': True, 'struct_layouts': layouts, 'bridge_calls': counts,
            'constrained_operations': SPEC[profile]['operations'],
            'bridge_lowerings': {}, 'status_lowerings': {'memory_operand_promotion': {
                'moves': 1, 'source_type': 'f64', 'destination_type': 'f80',
                'after_exception_clear': True, 'before_arithmetic': True,
                'captured_by_existing_test': True}, 'final_store_c1': {
                'stores': 1, 'state_byte_offset': 2739, 'rule': 'stored_magnitude_greater_than_input',
                'input_type': 'f80', 'stored_type': 'f64', 'assignment': 'unconditional',
                'nonfinite_cleared': True, 'comparison': 'unsigned_abs_f80_encoding'},
                'sticky_denormal': {'sites': 2, 'state_byte_offset': 2753,
                'operation': 'or_previous_shadow_and_new_classification',
                'arithmetic': True, 'final_store': True}},
            'rounding': 'dynamic', 'exceptions': 'strict', 'undefined_helpers': {},
            'scope': 'exact authored IR only; bounded denormal and store-range corpora; host x87 arithmetic'}, indent=2) + '\n')
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
