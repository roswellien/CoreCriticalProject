"""Exact authored live raw80 profiles; strict transport and static retargeting."""
import argparse
import ctypes as c
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, digest
from semantic_lowerings import lower, descriptor

BRIDGES = {
    '__remill_read_memory_f80': ('ptr', ['ptr', 'i32', 'ptr']),
    '__remill_write_memory_f80': ('ptr', ['ptr', 'i32', 'ptr']),
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
for name, sha, code, counts, comparisons in (
    ('push', '56b12be96118153238b85193b7719b6c1f4df5131234b4fe99a0749b7bbd640a', 'db29c3', (1,0,1,1,0,0), 3),
    ('pop', 'c7684b10c5f7bf067bc71a0b968fe99d763c24073d4a651b5de1ad624fe886cf', 'db3ac3', (0,1,1,1,1,1), 3),
    ('exchange', '1b033d0b32f687ca42f0f874685711173c8215b90e3270652f5428d060927336', 'd9c9c3', (0,0,1,1,0,0), 0),
    ('free', 'cd81f402016bda27609a9bd7a9d64d76d47a0299297b6c58bded71499f976095', 'ddc1c3', (0,0,1,1,0,0), 0),
):
    SPEC[name] = {'sha256':sha, 'bytes':code, 'bridges':dict(BRIDGES),
                  'counts':dict(zip(BRIDGES,counts)), 'operations':{'fcmp_f80':comparisons}}


def constrain(source, profile):
    expected = SPEC[profile]['operations']['fcmp_f80']
    pattern = r'^(  %\d+) = fcmp (ueq|oeq|olt) x86_fp80 (%\d+), ([^\n]+)$'
    replacement = r'\1 = call i1 @llvm.experimental.constrained.fcmp.f80(x86_fp80 \3, x86_fp80 \4, metadata !"\2", metadata !"fpexcept.strict")'
    result, count = re.subn(pattern, replacement, source, flags=re.M)
    if count != expected:
        raise ValueError('Unreviewed raw80 classification count')
    result = result.replace('ptr noalias %memory) {', 'ptr noalias %memory) strictfp {', 1)
    if expected:
        result += '\ndeclare i1 @llvm.experimental.constrained.fcmp.f80(x86_fp80, x86_fp80, metadata, metadata)\n'
    return result


def adapt(dll, guest, host, record, profile):
    if profile not in SPEC:
        raise ValueError('Unreviewed live-state profile')
    bridges = SPEC[profile]['bridges']
    expected_counts = SPEC[profile]['counts']
    if digest(guest) != SPEC[profile]['sha256']:
        raise ValueError('IR differs from the exact reviewed live-state profile')
    source = guest.read_text()
    transformed = lower(constrain(source, profile), profile)
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
        status_lowerings = descriptor(profile, host.read_text())
        record.write_text(json.dumps({'schema_version': 1, 'profile': 'x87_state_' + profile,
            'entry_va': 0x10000000, 'authored_bytes': SPEC[profile]['bytes'],
            'llvm_version': api.version, 'dll_sha256': digest(dll),
            'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
            'guest_layout': guest_layout, 'host_layout': HOST_LAYOUT,
            'guest_pointer_bits': 32, 'host_pointer_bits': 64, 'state_bytes': 3504,
            'all_struct_layouts_equal': True, 'struct_layouts': layouts, 'bridge_calls': counts,
            'constrained_operations': SPEC[profile]['operations'],
            'bridge_lowerings': {}, 'status_lowerings': status_lowerings,
            'rounding': 'dynamic', 'exceptions': 'strict', 'undefined_helpers': {},
            'scope': 'exact authored raw80 stack profiles with reviewed internal static tag/fault/sticky-DE lowerings; actual state observed'}, indent=2) + '\n')
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
