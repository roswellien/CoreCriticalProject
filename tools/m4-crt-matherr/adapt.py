"""ABI lowering of the complete four-instruction callback-registration leaf.

The source instruction/flag/memory computations remain the exact Remill lift.
Only the two scalar flag annotations acquire their upstream identity bodies.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import re
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, checked_state_offsets


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(out):
    base = ROOT / 'reports/m4-crt-matherr'
    need(out.is_relative_to(base) and not out.exists(), 'Fresh private matherr ABI output')
    source = base / 'preparation-r1/guest.ll'
    record = json.loads((base / 'preparation-r1/report.json').read_text())
    need(record['passed'] and record['guest_IR_sha256'] == sha(source), 'Exact prepared source lift')
    text = source.read_text()
    need(re.findall(r'^define ptr @([^ (]+)', text, re.M) == ['sub_7800b38f']
         and not re.search(r'\b(?:undef|poison|volatile|atomic|float|double|x86_fp80|inttoptr|ptrtoint)\b', text)
         and '__remill_missing_block' not in text, 'Complete bounded integer body')
    dll = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll'
    need(sha(dll) == '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb', 'Exact LLVM API identity')
    helpers = {'__remill_flag_computation_zero', '__remill_flag_computation_sign'}
    bridges = {'__remill_read_memory_32': ('i32', ['ptr', 'i32']),
               '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
               '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr'])}
    upstream = ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp'
    for name in helpers:
        need(re.search(r'bool ' + name + r'\(bool result, \.\.\.\)\s*\{\s*return result;\s*}', upstream.read_text()),
             'Upstream annotation identity source')
    out.mkdir()
    (out / 'adapt-source.py').write_bytes(Path(__file__).read_bytes())
    api = LLVM(dll)
    context = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    gd = hd = builder = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(source).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        gd = api.CreateTargetData(api.GetDataLayoutStr(module))
        hd = api.CreateTargetData(HOST_LAYOUT.encode())
        layouts = {}
        for name in re.findall(r'^%([^ =]+) = type', text, re.M):
            ty = api.GetTypeByName2(context, name.encode())
            need(ty and not api.IsOpaqueStruct(ty), 'Complete State type')
            def layout(d):
                return {'size': api.ABISizeOfType(d, ty), 'alignment': api.ABIAlignmentOfType(d, ty),
                        'offsets': [api.OffsetOfElement(d, ty, i) for i in range(api.CountStructElementTypes(ty))]}
            before, after = layout(gd), layout(hd)
            need(before == after, 'Complete guest/host ABI type equality ' + name)
            layouts[name] = before
        need(len(layouts) == 34 and layouts['struct.State']['size'] == 3504
             and layouts['struct.State']['alignment'] == 8, 'Complete exact State ABI')
        entry = api.GetNamedFunction(module, b'sub_7800b38f')
        offsets = checked_state_offsets(api, entry, gd)
        builder = api.CreateBuilderInContext(context)
        api.dll.LLVMSetLinkage.restype = None
        api.dll.LLVMSetLinkage.argtypes = [c.c_void_p, c.c_uint]
        counts = {}
        actual_helpers, actual_bridges = set(), set()
        for function in list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction)):
            name = api.name(function)
            if name in helpers:
                need(not api.CountBasicBlocks(function) and api.signature(function) == ('i1', ['i1'])
                     and api.IsFunctionVarArg(api.GlobalGetValueType(function)), 'Exact annotation signature')
                block = api.AppendBasicBlockInContext(context, function, b'identity')
                api.PositionBuilderAtEnd(builder, block)
                api.BuildRet(builder, api.GetParam(function, 0))
                api.dll.LLVMSetLinkage(function, 8)
                actual_helpers.add(name)
            elif name in bridges:
                need(not api.CountBasicBlocks(function) and api.signature(function) == bridges[name]
                     and not api.IsFunctionVarArg(api.GlobalGetValueType(function)), 'Exact bridge signature')
                actual_bridges.add(name)
            else:
                need(name == 'sub_7800b38f' and api.signature(function) == ('ptr', ['ptr', 'i32', 'ptr']),
                     'Only actual complete leaf definition')
            api.SetFunctionCallConv(function, 0)
            for attr in (b'nounwind', b'willreturn'):
                api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, api.GetEnumAttributeKindForName(attr, len(attr)))
            for attr in (b'target-cpu', b'target-features'):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attr, len(attr))
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    need(not api.IsAIntToPtrInst(instruction) and not api.IsAPtrToIntInst(instruction), 'No guest pointer conversion')
                    if api.IsACallInst(instruction):
                        callee = api.GetCalledValue(instruction)
                        need(api.IsAFunction(callee), 'Only direct typed native calls')
                        called = api.name(callee)
                        counts[called] = counts.get(called, 0) + 1
                        api.SetInstructionCallConv(instruction, 0)
                        for attr in (b'nounwind', b'willreturn'):
                            api.RemoveCallSiteEnumAttribute(instruction, FUNCTION_INDEX,
                                api.GetEnumAttributeKindForName(attr, len(attr)))
        need(actual_helpers == helpers and actual_bridges == set(bridges), 'Complete exact helper sets')
        need(counts == {'__remill_read_memory_32': 3, '__remill_write_memory_32': 2,
                        '__remill_flag_computation_zero': 1, '__remill_flag_computation_sign': 1,
                        '__remill_function_return': 1}, 'Exact complete call counts')
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        api.check(api.PrintModuleToFile(module, str(out / 'host.ll').encode(), c.byref(error)), error)
        report = {'passed': True, 'scope': 'Exact ABI-lowered whole leaf; compiled original/native and runtime integration review pending',
                  'source_path': str(source), 'source_sha256': sha(source), 'host_sha256': sha(out / 'host.ll'),
                  'layouts': layouts, 'State_offsets': offsets, 'calls': counts,
                  'complete_instruction_PCs': [0x7800b38f, 0x7800b393, 0x7800b39a, 0x7800b39f],
                  'defined_flags_mask': 0x8c5, 'undefined_AF_excluded': True,
                  'callback_invoked': False, 'whole_M4_complete': False}
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        files = [Path(__file__), source, base / 'preparation-r1/report.json', dll, upstream,
                 ROOT / 'tools/lifting/host_adapter.py', *(p for p in out.iterdir() if p.is_file())]
        (out / 'pins.json').write_text(json.dumps({'files': {str(p): sha(p) for p in files}}, indent=2) + '\n')
        print(json.dumps({'passed': True, 'types': 34, 'State_bytes': 3504, 'report_sha256': sha(out / 'report.json')}))
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
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
    p = argparse.ArgumentParser()
    p.add_argument('output', type=Path)
    main(p.parse_args().output.resolve())
