"""Retarget exact CRT entry IR with explicit, still-unimplemented host seams.

The native objects cannot run without checked ownership/routing/service bridges.
Every original instruction calculation and named State type stays intact.
"""
import argparse
import ctypes as c
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'reports/m4-crt-entry'
PINS = {}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(path, expected=None):
    path = Path(path).resolve(); digest = sha(path)
    need(expected is None or digest == expected, 'Exact input '+str(path))
    PINS[str(path)] = digest
    return path


def adapt(out):
    need(out.parent == BASE and not out.exists(), 'Fresh private derivative output')
    prepare = BASE/'preparation-r2'
    preparation = json.loads(pin(prepare/'report.json', '0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724').read_text())
    for path, digest in json.loads(pin(prepare/'pins.json', '51777aa9efd244d30c4303bc916eb88200931d41de36904fd601c9f2107d30d0').read_text())['files'].items():
        pin(path, digest)
    ancestor = pin(prepare/'guest.ll', preparation['guest_IR_sha256'])
    original = ancestor.read_text()
    helper_path = pin(ROOT/'tools/lifting/host_adapter.py', '97b101725526866a2a2fa4788be3a850f11da49fbf7cb563cefa1eed44c5b5ed')
    spec = importlib.util.spec_from_file_location('crt_entry_layout_api', helper_path)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    api = helper.LLVM(pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll', '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'))
    out.mkdir(parents=True)
    (out/'adapt-source.py').write_bytes(Path(__file__).read_bytes())
    (out/'original.ll').write_bytes(ancestor.read_bytes())
    text, direct_sites = re.subn(r'(\bcall ptr @)sub_([0-9a-f]+)(\()', r'\1mw34_crte_direct\3', original)
    need(direct_sites == 8, 'Exact eight original direct-call seams')
    text += '\ndeclare ptr @mw34_crte_direct(ptr, i32, ptr)\n'
    input_path = out/'routing-seams.ll'; input_path.write_text(text)
    context = api.ContextCreate(); module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    builder = guest_layout = host_layout = None
    layouts = {}; offsets = {}; lowered = []
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(input_path).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        guest_layout = api.CreateTargetData(api.GetDataLayoutStr(module)); host_layout = api.CreateTargetData(helper.HOST_LAYOUT.encode())
        for name in re.findall(r'^%([^ =]+) = type', original, re.M):
            kind = api.GetTypeByName2(context, name.encode())
            need(kind and not api.IsOpaqueStruct(kind), 'Complete named State type')
            def layout(data):
                return dict(size=api.ABISizeOfType(data,kind), align=api.ABIAlignmentOfType(data,kind), offsets=[api.OffsetOfElement(data,kind,i) for i in range(api.CountStructElementTypes(kind))])
            guest, host = layout(guest_layout), layout(host_layout)
            need(guest == host, 'Identical guest/native State type '+name)
            layouts[name] = guest
        need(layouts['struct.State']['size'] == 3504, 'Whole accepted State storage')
        for entry in preparation['entries']:
            function = api.GetNamedFunction(module, f'sub_{entry:x}'.encode())
            need(function and api.CountBasicBlocks(function), 'Complete native root definition')
            offsets[f'sub_{entry:x}'] = helper.checked_state_offsets(api, function, guest_layout)
        builder = api.CreateBuilderInContext(context)
        scalar = helper.FLAG_HELPERS | {'__remill_compare_neq','__remill_compare_eq','__remill_compare_ugt','__remill_compare_ule'}
        bridges = {'__remill_read_memory_32':('i32',['ptr','i32']), '__remill_read_memory_8':('i8',['ptr','i32']), '__remill_write_memory_32':('ptr',['ptr','i32','i32']), '__remill_function_call':('ptr',['ptr','i32','ptr']), '__remill_function_return':('ptr',['ptr','i32','ptr']), '__remill_jump':('ptr',['ptr','i32','ptr']), 'mw34_crte_direct':('ptr',['ptr','i32','ptr']), '__remill_undefined_8':('i8',[])}
        nounwind = api.GetEnumAttributeKindForName(b'nounwind',8); willreturn = api.GetEnumAttributeKindForName(b'willreturn',10)
        noinline = api.GetEnumAttributeKindForName(b'noinline',8); optnone = api.GetEnumAttributeKindForName(b'optnone',7)
        api.dll.LLVMSetLinkage.argtypes = [c.c_void_p,c.c_int]; api.dll.LLVMSetLinkage.restype = None
        for function in list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction)):
            name = api.name(function)
            if name in scalar:
                need(not api.CountBasicBlocks(function) and api.signature(function) == ('i1',['i1']), 'Exact annotation scalar identity')
                block = api.AppendBasicBlockInContext(context,function,b'identity'); api.PositionBuilderAtEnd(builder,block); api.BuildRet(builder,api.GetParam(function,0)); api.dll.LLVMSetLinkage(function,8); lowered.append(name)
            elif not api.CountBasicBlocks(function):
                need(name in bridges and api.signature(function) == bridges[name] or name == 'llvm.ctpop.i8' and api.signature(function) == ('i8',['i8']), 'Only explicit checked seam '+name)
            api.SetFunctionCallConv(function,0)
            if name != 'llvm.ctpop.i8':
                for attribute in (nounwind,willreturn,noinline,optnone):
                    api.RemoveEnumAttributeAtIndex(function,helper.FUNCTION_INDEX,attribute)
            for attribute in (b'target-cpu',b'target-features'):
                api.RemoveStringAttributeAtIndex(function,helper.FUNCTION_INDEX,attribute,len(attribute))
            for block in api.iterate(api.GetFirstBasicBlock(function),api.GetNextBasicBlock):
                for instruction in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
                    need(not api.IsAIntToPtrInst(instruction) and not api.IsAPtrToIntInst(instruction), 'No guest integer/host pointer conversion')
                    if api.IsACallInst(instruction):
                        callee = api.GetCalledValue(instruction); need(api.IsAFunction(callee), 'No untyped host call')
                        api.SetInstructionCallConv(instruction,0)
                        if api.name(callee) != 'llvm.ctpop.i8':
                            api.RemoveCallSiteEnumAttribute(instruction,helper.FUNCTION_INDEX,nounwind); api.RemoveCallSiteEnumAttribute(instruction,helper.FUNCTION_INDEX,willreturn)
        prototype = api.GetNamedFunction(module,b'sub_5ac3a0')
        enter = api.AddFunction(module,b'mw34_crte_enter',api.GlobalGetValueType(prototype))
        position = api.dll.LLVMPositionBuilderBefore; position.argtypes=[c.c_void_p,c.c_void_p]; position.restype=None
        for entry in preparation['entries']:
            function = api.GetNamedFunction(module,f'sub_{entry:x}'.encode()); position(builder,api.GetFirstInstruction(api.GetFirstBasicBlock(function)))
            args = (c.c_void_p*3)(*(api.GetParam(function,i) for i in range(3)))
            api.BuildCall2(builder,api.GlobalGetValueType(enter),enter,args,3,b'checked_root_entry')
        api.SetTarget(module,b'x86_64-pc-windows-msvc'); api.SetDataLayout(module,helper.HOST_LAYOUT.encode())
        api.check(api.VerifyModule(module,2,c.byref(error)),error)
        host = out/'candidate.ll'; api.check(api.PrintModuleToFile(module,str(host).encode(),c.byref(error)),error)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        if builder:
            api.DisposeBuilder(builder)
        for data in (guest_layout,host_layout):
            if data:
                api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(context)
    llvm = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    commands = []
    for level in ('O0','O2'):
        obj = out/f'candidate-{level}.obj'
        for program, args, log in ((pin(llvm/'clang.exe'), ['--target=x86_64-pc-windows-msvc','-'+level,'-c',str(host),'-o',str(obj)],f'compile-{level}.log'), (pin(llvm/'llvm-objdump.exe'), ['--disassemble','--syms','--unwind-info',str(obj)],f'object-{level}.txt')):
            result = subprocess.run([str(program),*args],capture_output=True)
            (out/log).write_bytes(result.stdout); (out/(log+'.stderr')).write_bytes(result.stderr)
            commands.append(dict(program=str(program),arguments=args,exit_code=result.returncode,stdout=str(out/log),stderr=str(out/(log+'.stderr'))))
            need(result.returncode == 0, 'Actual object generation/recovery')
    history = BASE/'preparation-r1'
    pin(history/'prepare-source.py'); pin(history/'failure.txt')
    report = dict(passed=True, scope='Verified x64 retarget/object generation with checked bridge requirements; no linked native execution', ancestor_sha256=sha(ancestor), host_sha256=sha(host), layouts=layouts, State_bytes=3504, all_named_type_layouts_equal=True, State_offsets=offsets, original_direct_calls_replaced=direct_sites, root_entry_checks=len(preparation['entries']), annotation_identities=sorted(lowered), instruction_arithmetic_rewrites=0, undefined_flag_policy='Unimplemented required bridge; future explicit observed representative must be reviewed', bridge_implementations='Absent; checked memory/routing/ownership/FP and guest SEH contracts required before linking execution', exceptions=dict(function_and_call_nounwind_removed=True, native_unwind_compile_outputs=True, actual_guest_SEH_implemented=False), commands=commands, original_executed=False, native_executed=False, full_startup=False, whole_M4_complete=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    pin(Path(__file__)); pin(sys.executable)
    for path in out.iterdir():
        if path.is_file():
            pin(path)
    (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,State_bytes=3504,native_object_levels=['O0','O2'],report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),native_executed=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output',type=Path)
    adapt(parser.parse_args().output.resolve())
