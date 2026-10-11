"""Strict raw80 host candidate for the exact physical compound FCOS root."""
from pathlib import Path
import ctypes as c
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-fp-native'))
from adapt_first import FPTypes, HOST_LAYOUT, FUNCTION_INDEX


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = ROOT / 'reports/m4-cosine-native' / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or expected == value, path
        pins[str(path)] = value
        return path

    receipt = pin(ROOT / 'reports/m4-cosine-native/guest-lift-r1/report.json',
                  '3c39f79575c1aab5176520c0a9c86ed79659db5f3454a32b94154edb4f4bdf2b')
    lift = json.loads(receipt.read_bytes())
    assert lift['passed'] and lift['FCOS_count'] == 3
    for path, digest in lift['files'].items():
        pin(path, digest)
    guest = pin(lift['guest_IR'], lift['guest_IR_sha256'])
    source = guest.read_text()
    transformed = source
    rules = [
        (r'^(  %\d+) = fptrunc x86_fp80 (%\d+) to float$',
         r'\1 = call float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80 \2, metadata !"round.dynamic", metadata !"fpexcept.strict")',
         'declare float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80, metadata, metadata)'),
        (r'^(  %\d+) = fpext double (%\d+) to x86_fp80$',
         r'\1 = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double \2, metadata !"fpexcept.strict")',
         'declare x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double, metadata)')]
    for pattern, replacement, declaration in rules:
        transformed, count = re.subn(pattern, replacement, transformed, flags=re.M)
        assert count == 3
        transformed += '\n' + declaration + '\n'
    occurrences = []

    def lower(match):
        result, value = match.groups()
        index = len(occurrences)
        occurrences.append(dict(index=index, result=result, input=value))
        return (f'  %mw.cos.{index}.input = alloca x86_fp80, align 16\n'
                f'  %mw.cos.{index}.output = alloca x86_fp80, align 16\n'
                f'  store x86_fp80 {value}, ptr %mw.cos.{index}.input, align 16\n'
                f'  call void @mw34_actual_fcos_status_raw80(ptr %state, ptr %mw.cos.{index}.input, ptr %mw.cos.{index}.output)\n'
                f'  {result} = load x86_fp80, ptr %mw.cos.{index}.output, align 16')

    transformed, count = re.subn(r'^  (%\d+) = call x86_fp80 @cosl\(x86_fp80 noundef (%\d+)\) #\d+$',
                                 lower, transformed, flags=re.M)
    assert count == 3
    transformed, count = re.subn(r'^declare dso_local x86_fp80 @cosl\([^\n]+\n', '', transformed, flags=re.M)
    assert count == 1
    transformed += '\ndeclare void @mw34_actual_fcos_status_raw80(ptr, ptr, ptr)\n'
    repairs = []
    for result in ('261', '490', '719'):
        before = f'  %{result} = call i32 @__remill_fpu_exception_test(i32 noundef 127) #5'
        assert transformed.count(before) == 1
        transformed = transformed.replace(before,
            f'  %{result} = call i32 @mw34_fp_store_exception_test(ptr %state, i32 127)')
    transformed += '\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
    for index, (value, pointer) in enumerate((('115', '116'), ('258', '259'),
                                             ('419', '420'), ('487', '488'),
                                             ('648', '649'), ('716', '717'))):
        before = f'  store i8 %{value}, ptr %{pointer}, align 1'
        assert transformed.count(before) == 1
        assert f'  %{pointer} = getelementptr inbounds nuw i8, ptr %state, i32 2753' in source
        transformed = transformed.replace(before,
            f'  %mw.de.{index}.prior = load i8, ptr %{pointer}, align 1\n'
            f'  %mw.de.{index}.sticky = or i8 %{value}, %mw.de.{index}.prior\n'
            f'  store i8 %mw.de.{index}.sticky, ptr %{pointer}, align 1')
        repairs.append(dict(index=index, DE_offset=2753, value=value, pointer=pointer))
    assert transformed.count('ptr noalias %memory) {') == 1
    transformed = transformed.replace('ptr noalias %memory) {', 'ptr noalias %memory) strictfp {')
    strict = out / '4b64f0.strict-input.ll'
    strict.write_text(transformed)
    dll = pin(ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll',
              '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb')
    bridges = {
        '__remill_read_memory_f64': ('double', ['ptr', 'i32']),
        '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
        '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
        '__remill_write_memory_f32': ('ptr', ['ptr', 'i32', 'float']),
        '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
        '__remill_fpu_exception_clear': ('void', ['i32']),
        '__remill_fpu_exception_test': ('i32', ['i32']),
        'mw34_fp_store_exception_test': ('i32', ['ptr', 'i32']),
        'mw34_actual_fcos_status_raw80': ('void', ['ptr', 'ptr', 'ptr'])}
    expected = dict(zip(bridges, (3, 1, 7, 3, 1, 6, 3, 3, 3)))
    api = FPTypes(dll)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    gd = hd = builder = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(strict).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        gd = api.CreateTargetData(api.GetDataLayoutStr(module))
        hd = api.CreateTargetData(HOST_LAYOUT.encode())
        assert api.PointerSize(gd) == 4 and api.PointerSize(hd) == 8
        layouts = {}
        for name in re.findall(r'^%([^ =]+) = type', source, re.M):
            typ = api.GetTypeByName2(context, name.encode())

            def layout(data):
                return dict(size=api.ABISizeOfType(data, typ), alignment=api.ABIAlignmentOfType(data, typ),
                            offsets=[api.OffsetOfElement(data, typ, i) for i in range(api.CountStructElementTypes(typ))])
            before, after = layout(gd), layout(hd)
            assert before == after, name
            layouts[name] = before
        assert layouts['struct.State']['size'] == 3504
        entry = api.GetNamedFunction(module, b'sub_4b64f0')
        assert api.signature(entry) == ('ptr', ['ptr', 'i32', 'ptr'])
        builder = api.CreateBuilderInContext(context)
        counts = {name: 0 for name in bridges}
        annotations = []
        nounwind = api.GetEnumAttributeKindForName(b'nounwind', 8)
        for function in list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction)):
            name = api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function) and not name.startswith('llvm.'):
                if name in ('__remill_flag_computation_zero', '__remill_flag_computation_sign'):
                    assert api.signature(function) == ('i1', ['i1'])
                    block = api.AppendBasicBlockInContext(context, function, b'identity')
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.GetParam(function, 0))
                    annotations.append(name)
                elif name == '__remill_undefined_8':
                    assert api.signature(function) == ('i8', [])
                    # XOR AF is architecturally undefined. This literal zero
                    # representative remains excluded from semantic equality.
                    assert source.count('call zeroext i8 @__remill_undefined_8()') == 1
                    assert 'store i8 %182, ptr %181, align 1' in source
                    assert source.count('ptr %181') == 2
                    block = api.AppendBasicBlockInContext(context, function, b'undefined_AF_representative')
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.ConstInt(api.GetReturnType(api.GlobalGetValueType(function)), 0, 0))
                else:
                    assert name in bridges and api.signature(function) == bridges[name], name
                    assert not api.IsFunctionVarArg(api.GlobalGetValueType(function))
                    api.SetFunctionCallConv(function, 0)
            for attribute in (b'target-cpu', b'target-features', b'no-trapping-math'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attribute, len(attribute))
            api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for inst in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    assert not api.IsAIntToPtrInst(inst) and not api.IsAPtrToIntInst(inst)
                    if api.IsACallInst(inst):
                        called = api.GetCalledValue(inst)
                        if api.IsAFunction(called) and api.name(called) in bridges:
                            counts[api.name(called)] += 1
                            api.SetInstructionCallConv(inst, 0)
                        api.RemoveCallSiteEnumAttribute(inst, FUNCTION_INDEX, nounwind)
        assert counts == expected, (counts, expected)
        assert len(annotations) == 2
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        wrapper = api.AddFunction(module, b'mw34_fp_entry_4b64f0', api.GlobalGetValueType(entry))
        block = api.AppendBasicBlockInContext(context, wrapper, b'entry')
        api.PositionBuilderAtEnd(builder, block)
        params = (c.c_void_p * 3)(*(api.GetParam(wrapper, i) for i in range(3)))
        result = api.BuildCall2(builder, api.GlobalGetValueType(entry), entry, params, 3, b'memory')
        api.BuildRet(builder, result)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        host = out / '4b64f0.ll'
        api.check(api.PrintModuleToFile(module, str(host).encode(), c.byref(error)), error)
    finally:
        if builder:
            api.DisposeBuilder(builder)
        for data in (gd, hd):
            if data:
                api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(context)
    for path in (__file__, ROOT / 'tools/m4-fp-native/adapt_first.py', ROOT / 'tools/lifting/host_adapter.py'):
        pin(path)
    for path in out.iterdir():
        pin(path)
    report = dict(passed=True, scope='Strict static compound FCOS host candidate; execution is a separate gate',
                  root=0x4b64f0, host_IR=str(host), host_IR_sha256=sha(host),
                  full_state_bytes=3504, all_layouts_equal=True, layouts=layouts,
                  bridge_counts=counts, cosine_occurrences=occurrences, sticky_DE_repairs=repairs,
                  strict_dynamic_rounding=True, normal_raw80_pointer_ABI=True,
                  AF_representative=0, AF_semantic_equality_claimed=False,
                  native_executed=False, initializer_credit=0, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), bridge_counts=counts)))


if __name__ == '__main__':
    main(sys.argv[1])
