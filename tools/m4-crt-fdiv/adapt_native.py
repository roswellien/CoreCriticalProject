"""Bounded writer: exact integer CFG, accepted CW lowering, typed FNCLEX.

The complete original fallback stays in the preserved guest module. Its native
entry is an explicit fault in this increment, never a successful substitute.
"""
import ctypes as c
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, checked_state_offsets
sys.path.insert(0, str(ROOT / 'tools/m4-crt-control'))
from adapt import blocks, SSA

NEW = (0x78004254, 0x7800426B, 0x780042A3, 0x780042CF)
CONTROL = (0x780042E1, 0x780042F7, 0x7800432C, 0x7800439F)


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def definition(text, name):
    match = re.search(r'^define ptr @' + name + r'[^\n]*\{\n(.*?)^}', text, re.M | re.S)
    require(match is not None, 'Complete definition ' + name)
    return match


def named(text):
    text = re.sub(r'%(\d+)\b', r'%v\1', text)
    text = re.sub(r'^(\d+):', r'v\1:', text, flags=re.M)
    return re.sub(r'\s+#\d+\b', '', text)


def cfg_model(body, entry):
    """Carry RETURN_PC across dynamic CALL bookkeeping blocks; no CPU oracle."""
    bs = blocks(body)
    pending = [('entry', entry, None)]
    seen, pcs = {}, {}
    while pending:
        key, pc, return_pc = pending.pop()
        if key in seen:
            require(seen[key] == pc, 'Conflicting instruction PC at CFG merge')
            continue
        seen[key] = pc
        local = {'%NEXT_PC': pc, '%RETURN_PC': return_pc, '%program_counter': entry}
        for line in bs[key]:
            match = re.fullmatch(r'(' + SSA + r') = load i32, ptr (%NEXT_PC|%RETURN_PC), align 4', line)
            if match:
                local[match[1]] = local.get(match[2])
                continue
            match = re.fullmatch(r'(' + SSA + r') = (add|sub) i32 (' + SSA + r'), (-?\d+)', line)
            if match and isinstance(local.get(match[3]), int):
                local[match[1]] = (local[match[3]] + (1 if match[2] == 'add' else -1) * int(match[4])) & 0xFFFFFFFF
                continue
            match = re.fullmatch(r'(' + SSA + r') = select i1 ' + SSA + r', i32 (' + SSA + r'), i32 (' + SSA + r')', line)
            if match and match[2] in local and match[3] in local:
                local[match[1]] = (local[match[2]], local[match[3]])
                continue
            match = re.fullmatch(r'store i32 (' + SSA + r'), ptr (%NEXT_PC|%RETURN_PC|%PC), align (?:4|8)', line)
            if match:
                value = local.get(match[1])
                local[match[2]] = value
                if match[2] == '%PC' and isinstance(value, int) and key not in pcs:
                    pcs[key] = value
        term = bs[key][-1]
        if term.startswith('ret ptr '):
            continue
        edges = re.findall(r'label %([A-Za-z0-9_.$]+)', term)
        require(term.startswith('br ') and len(edges) in (1, 2), 'Bounded CFG terminator')
        n = local.get('%NEXT_PC')
        if len(edges) == 2:
            require(isinstance(n, int) or isinstance(n, tuple) and len(n) == 2, 'Exact instruction/internal branch PC')
            targets = n if isinstance(n, tuple) else (n, n)
            pending.extend((edge, target, local.get('%RETURN_PC')) for edge, target in zip(edges, targets))
        else:
            # Only a CALL's own return-bookkeeping successor may have an
            # unresolved target NEXT_PC; it must restore the known RETURN_PC.
            require(isinstance(n, int) or (n is None and '@__remill_function_call' in '\n'.join(bs[key])),
                    'Unresolved instruction fallthrough')
            pending.append((edges[0], n, local.get('%RETURN_PC')))
    require(set(seen) == set(bs), 'Every original CFG block reached by static proof')
    return dict(instruction_PCs=sorted(set(pcs.values())), block_PCs=pcs,
                bookkeeping_blocks=sorted(set(bs) - set(pcs)), all_blocks_reachable=True)


def main(folder):
    folder = Path(folder).resolve()
    require(folder.parent == ROOT / 'reports/m4-crt-fdiv' and not (folder / 'candidate.ll').exists(), 'Fresh adaptation outputs')
    original = (folder / 'guest.ll').read_text()
    control_path = ROOT / 'reports/m4-crt-control/research-r1/host.ll'
    require(sha(control_path) == '49e25a2cd2f9279970fac099141a08742ab678eb9b041be6b1368effc55ea5a9', 'Exact accepted control candidate')
    control = control_path.read_text()
    old_types = dict(re.findall(r'^(%[^ =]+) = type (.*)$', original, re.M))
    control_types = dict(re.findall(r'^(%[^ =]+) = type (.*)$', control, re.M))
    require(old_types == control_types and len(old_types) == 34, 'All literal State types match accepted control module')
    proofs = {}
    bodies = []
    for entry in NEW:
        name = f'sub_{entry:x}'
        match = definition(original, name)
        body = named(match.group())
        proof = cfg_model(match[1], entry)
        proofs[name] = proof
        if entry == 0x78004254:
            # Replace only the complete single FNCLEX instruction block.
            start = body.index('  call void @__remill_fpu_exception_clear(')
            end = body.index('  store ptr %v69, ptr %MEMORY, align 4', start)
            old = body[start:end]
            require(old.count('@__remill_undefined_8') == 4 and 'i32 2745' in old and 'i32 2755' in old,
                    'Exact baseline FNCLEX separate flags/helper lowering')
            body = body[:start] + '  %fdiv_clex = call ptr @mw34_fdiv_fnclex(ptr %state, i32 %v67, ptr %v69)\n' + body[end:]
            body = body.replace('  store ptr %v69, ptr %MEMORY, align 4', '  store ptr %fdiv_clex, ptr %MEMORY, align 4')
            (folder / 'baseline-fnclex.ll').write_text(old)
        if entry == 0x780042A3:
            label = next(key for key, pc in proof['block_PCs'].items() if pc == 0x7802C070)
            pieces = re.split(r'(?m)^(v\d+):[^\n]*\n', body)
            native_blocks = {'entry': pieces[0]}
            for index in range(1, len(pieces), 2):
                block, lines = pieces[index:index + 2]
                if block == 'v' + label:
                    native_blocks[block] = (
                '  %fallback_pc = getelementptr i8, ptr %state, i32 2472\n'
                '  store i32 2013446256, ptr %fallback_pc, align 8\n'
                '  %fallback_fault = call ptr @mw34_fdiv_unsupported(ptr %state, i32 2013446256, ptr %memory)\n'
                '  ret ptr %fallback_fault\n\n')
                else:
                    native_blocks[block] = re.sub(r'(?m)^}\s*$', '', lines)
            reached, todo = set(), ['entry']
            while todo:
                block = todo.pop()
                if block in reached:
                    continue
                require(block in native_blocks, 'Exact native CFG successor')
                reached.add(block)
                todo.extend(re.findall(r'label %(v\d+)', native_blocks[block]))
            rebuilt = pieces[0] + ''.join(block + ':\n' + lines for block, lines in native_blocks.items()
                                         if block != 'entry' and block in reached)
            require(all(proof['block_PCs'].get(block[1:], 0) < 0x7802C070 or block == 'v' + label
                        for block in reached if block != 'entry'), 'No reached unsupported arithmetic block')
            proof['native_reached_blocks'] = sorted(reached)
            proof['native_removed_unsupported_blocks'] = sorted(set(native_blocks) - reached)
            body = rebuilt.rstrip() + '\n}'
            require('x86_fp80' not in body and 'double' not in body, 'No unsupported fallback numeric lowering retained')
        body = body.replace('{\n', '{\n  %fdiv_entry = call ptr @mw34_fdiv_enter(ptr %state, i32 %program_counter, ptr %memory)\n', 1)
        bodies.append(body)
    # Keep the accepted control lowering bodies intact; new checked-entry bridge
    # receives every actual entry. Native symbol retargeting is reversible.
    candidate = control + '\n' + '\n\n'.join(bodies) + '\n'
    candidate += '\ndeclare ptr @__remill_function_call(ptr, i32, ptr)\n'
    candidate += '\ndeclare ptr @mw34_fdiv_fnclex(ptr, i32, ptr)\n'
    candidate += '\ndeclare ptr @mw34_fdiv_unsupported(ptr, i32, ptr)\n'
    # Existing control entry helper becomes the one shared checked entry route.
    candidate = candidate.replace('mw34_cf_enter', 'mw34_fdiv_enter')
    for old in ('__remill_read_memory_32', '__remill_write_memory_32', '__remill_function_return',
                '__remill_function_call', 'mw34_cf_wait', 'mw34_cf_store_cw', 'mw34_cf_load_cw'):
        candidate = candidate.replace('@' + old + '(', '@mw34_fdiv_' + old + '(')
    for entry in NEW + CONTROL:
        candidate = candidate.replace('@sub_' + f'{entry:x}' + '(', '@mw34_fdiv_sub_' + f'{entry:x}' + '(')
    require('__remill_fpu_exception_clear' not in candidate and '__remill_fpu_set_rounding' not in candidate,
            'No host FP exception/rounding side effects retained')
    require(not re.search(r'\b(?:undef|poison|atomic|volatile|float|double|x86_fp80|inttoptr|ptrtoint)\b', candidate),
            'Bounded integer/typed-transfer native IR only')
    (folder / 'candidate.ll').write_text(candidate)
    api = LLVM(ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll')
    ctx = api.ContextCreate()
    module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    gd = hd = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(folder / 'candidate.ll').encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(ctx, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        gd = api.CreateTargetData(api.GetDataLayoutStr(module))
        hd = api.CreateTargetData(HOST_LAYOUT.encode())
        layouts, offsets, calls = {}, {}, {}
        for name in old_types:
            ty = api.GetTypeByName2(ctx, name[1:].encode())
            require(ty and not api.IsOpaqueStruct(ty), 'Complete State type')
            def layout(data):
                return dict(size=api.ABISizeOfType(data, ty), align=api.ABIAlignmentOfType(data, ty),
                            offsets=[api.OffsetOfElement(data, ty, i) for i in range(api.CountStructElementTypes(ty))])
            a, b = layout(gd), layout(hd)
            require(a == b, 'State layout unchanged')
            layouts[name] = a
        require(layouts['%struct.State']['size'] == 3504, 'Complete State3504 identity')
        for entry in NEW + CONTROL:
            name = f'mw34_fdiv_sub_{entry:x}'
            fn = api.GetNamedFunction(module, name.encode())
            require(api.signature(fn) == ('ptr', ['ptr', 'i32', 'ptr']), 'Static entry ABI')
            offsets[name] = checked_state_offsets(api, fn, gd)
        for fn in api.iterate(api.GetFirstFunction(module), api.GetNextFunction):
            api.SetFunctionCallConv(fn, 0)
            for attr in (b'nounwind', b'willreturn'):
                api.RemoveEnumAttributeAtIndex(fn, FUNCTION_INDEX, api.GetEnumAttributeKindForName(attr, len(attr)))
            for attr in (b'target-cpu', b'target-features'):
                api.RemoveStringAttributeAtIndex(fn, FUNCTION_INDEX, attr, len(attr))
            for block in api.iterate(api.GetFirstBasicBlock(fn), api.GetNextBasicBlock):
                for ins in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    require(not api.IsAIntToPtrInst(ins) and not api.IsAPtrToIntInst(ins), 'No host pointer conversion')
                    if api.IsACallInst(ins):
                        called = api.GetCalledValue(ins)
                        require(api.IsAFunction(called), 'Only statically bound host calls')
                        target = api.name(called)
                        calls[target] = calls.get(target, 0) + 1
                        api.SetInstructionCallConv(ins, 0)
                        for attr in (b'nounwind', b'willreturn'):
                            api.RemoveCallSiteEnumAttribute(ins, FUNCTION_INDEX, api.GetEnumAttributeKindForName(attr, len(attr)))
        api.SetTarget(module, b'x86_64-pc-windows-msvc')
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        api.check(api.PrintModuleToFile(module, str(folder / 'host.ll').encode(), c.byref(error)), error)
        report = dict(passed=True, scope='Native-only successful actual dynamic query path; exact fallback entry rejects before arithmetic',
                      guest_sha256=sha(folder / 'guest.ll'), candidate_sha256=sha(folder / 'candidate.ll'),
                      host_sha256=sha(folder / 'host.ll'), accepted_control_host_sha256=sha(control_path),
                      source_sha256=sha(__file__), new_integer_CFGs=proofs, layouts=layouts, State_offsets=offsets,
                      calls=calls, unsupported_native_entry=0x7802C070, FNCLEX_defined_clear_mask=0x80FF,
                      FNCLEX_CC='native undefined representative preserves incoming C0-C3; no original measured CC policy',
                      original_executed=False, native_executed=False, whole_M4_complete=False)
        (folder / 'adaptation.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=True, native_original_bodies=8, denied_fallback=True, adaptation_sha256=sha(folder / 'adaptation.json'))))
    finally:
        for data in (gd, hd):
            if data:
                api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(ctx)


if __name__ == '__main__':
    main(sys.argv[1])
