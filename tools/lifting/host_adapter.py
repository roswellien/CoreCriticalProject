"""Bounded fixture ABI adapter using the official LLVM C API.

Remill supplies every instruction and flag computation. This adapter preserves
State storage, lowers reviewed flag/condition identities, and exposes a host C ABI.
"""

import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import re


HOST_LAYOUT = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:64-f80:128-n8:16:32:64-S128"
FLAG_HELPERS = {"__remill_flag_computation_" + name for name in
                ("carry", "zero", "sign", "overflow")}
ANNOTATIONS = FLAG_HELPERS | {'__remill_compare_uge'}
BRIDGES = {"__remill_read_memory_32", "__remill_write_memory_32", "__remill_function_return"}
FUNCTION_INDEX = 0xFFFFFFFF
PROFILES = {'fixture': 0x10000000, 'shift': 0x10000000, 'mw3-helper': 0x409ed0}
UNDEFINED_FLAG = '__remill_undefined_8'
DEAD_FLAG_OFFSETS = {2069, 2077}
SSA = r'%[A-Za-z0-9_.$]+'
VALUE = rf'(?:{SSA}|-?\d+|true|false)'


def prove_dead_flags(text, profile, typed_offsets=None):
    """Fail-closed proof for the two opt-in straight-line Remill profiles.

    This is deliberately a small parser, not an LLVM optimization pass. LLVM
    verifies the module separately. Every accepted instruction is parsed in
    full, each block has one successor, and every undefined SSA use is checked.
    State aliases must be direct constant GEPs; typed offsets are supplied by
    the LLVM data-layout API rather than guessed from textual type names.
    """
    if profile not in ('shift', 'mw3-helper'):
        raise ValueError('Dead undefined flags require an explicit reviewed profile')
    typed_offsets = typed_offsets or {}
    entry_name = f'sub_{PROFILES[profile]:x}'
    definitions = list(re.finditer(r'^define [^\n]+\{\n(.*?)^}', text, re.M | re.S))
    if len(definitions) != 1:
        raise ValueError('Dead-flag proof requires exactly one defined entry')
    header = definitions[0].group(0).splitlines()[0]
    expected = (f'define ptr @{entry_name}(ptr noalias %state, i32 %program_counter, '
                'ptr noalias %memory) {')
    if header != expected:
        raise ValueError('Dead-flag proof entry or signature differs')
    body = definitions[0].group(1)
    helper_lines = [line.split(';', 1)[0].strip() for line in text.splitlines()
                    if '@' + UNDEFINED_FLAG in line.split(';', 1)[0]]
    declarations = [line for line in helper_lines if re.fullmatch(
        r'declare(?: dso_local)? zeroext i8 @__remill_undefined_8\(\)(?: #\d+)?', line)]
    if len(declarations) != 1 or len(helper_lines) != 3:
        raise ValueError('Undefined helper declaration or complete use set differs')
    if re.search(r'\b(?:undef|poison|volatile|atomic)\b', body) or '"' in body:
        raise ValueError('Unreviewed literal, volatile, or atomic operation')
    blocks, current = {'entry': []}, 'entry'
    for source in body.splitlines():
        line = source.split(';', 1)[0].strip()
        if not line:
            continue
        label = re.fullmatch(r'([A-Za-z0-9_.$]+):', line)
        if label:
            current = label[1]
            if current in blocks:
                raise ValueError('Duplicate basic block')
            blocks[current] = []
        else:
            blocks[current].append(line)
    chain, cursor = [], 'entry'
    while cursor not in chain:
        if cursor not in blocks or not blocks[cursor]:
            raise ValueError('Missing successor or empty block')
        chain.append(cursor)
        terminator = blocks[cursor][-1]
        successor = re.fullmatch(r'br label %([A-Za-z0-9_.$]+)', terminator)
        if successor:
            cursor = successor[1]
            continue
        if re.fullmatch(rf'ret ptr {SSA}', terminator):
            break
        raise ValueError('Dead-flag proof requires unconditional successors and one return')
    else:
        raise ValueError('Dead-flag proof rejects CFG cycles')
    if set(chain) != set(blocks):
        raise ValueError('Dead-flag proof rejects unreachable or alternate blocks')

    pointers = {'%state': ('state', 0), '%memory': ('memory', 0)}
    locals_, local_types = {}, {}
    taints = {'%state': set(), '%memory': set(), '%program_counter': set()}
    roots, terminals, dirty, overwrites = [], [], {}, []
    scalar_calls = FLAG_HELPERS | {'__remill_compare_sle', 'llvm.ctpop.i8'}
    instructions = [(block, position, line) for block in chain
                    for position, line in enumerate(blocks[block])]

    def operands(values):
        result = set()
        for value in values:
            if value.startswith('%'):
                if value not in taints:
                    raise ValueError('Unknown or forward SSA operand')
                result |= taints[value]
        return result

    def pointer(value):
        if value not in pointers:
            raise ValueError('Unknown pointer alias in dead-flag proof')
        return pointers[value]

    for index, (block, position, line) in enumerate(instructions):
        assignment = re.fullmatch(rf'({SSA}) = (.+)', line)
        result, operation = (assignment[1], assignment[2]) if assignment else (None, line)
        if result and result in taints:
            raise ValueError('Duplicate SSA definition')
        if result:
            taints[result] = set()
        if re.fullmatch(r'br label %[A-Za-z0-9_.$]+', operation):
            if result or position != len(blocks[block]) - 1:
                raise ValueError('Unexpected interior branch')
            continue
        match = re.fullmatch(rf'ret ptr ({SSA})', operation)
        if match:
            if result or dirty or operands([match[1]]) or position != len(blocks[block]) - 1:
                raise ValueError('Undefined flag reaches return without an overwrite')
            continue
        match = re.fullmatch(r'alloca (i8|i32|ptr), align (1|4|8)', operation)
        if match and result:
            pointers[result] = ('local', result)
            locals_[result] = None
            local_types[result] = match[1]
            continue
        match = re.fullmatch(rf'getelementptr(?: inbounds)?(?: nuw)? i8, ptr %state, i32 (-?\d+)', operation)
        if match and result:
            offset = int(match[1])
            if not 0 <= offset < 3504:
                raise ValueError('State byte GEP is outside reviewed storage')
            pointers[result] = ('state', offset)
            continue
        match = re.fullmatch(r'getelementptr inbounds %struct\.State, ptr %state(?:, i32 \d+)+', operation)
        if match and result:
            if result not in typed_offsets or not 0 <= typed_offsets[result] < 3504:
                raise ValueError('Typed State GEP lacks a checked LLVM offset')
            pointers[result] = ('state', typed_offsets[result])
            continue
        match = re.fullmatch(rf'load (i\d+|ptr), ptr ({SSA}), align (1|4|8)', operation)
        if match and result:
            value_type, address = match[1], match[2]
            root, offset = pointer(address)
            if root == 'state':
                if value_type == 'ptr':
                    raise ValueError('State pointer reload is unsupported')
                width = (int(value_type[1:]) + 7) // 8
                if offset + width > 3504:
                    raise ValueError('State load extent is outside reviewed storage')
                if any(offset <= slot < offset + width for slot in dirty):
                    raise ValueError('Undefined flag read before overwrite')
            elif root != 'local':
                raise ValueError('Unreviewed direct pointer load')
            elif value_type != local_types[offset] or \
                    (locals_[offset] and locals_[offset][0] == 'state'):
                raise ValueError('State spill/reload or mismatched local load')
            if value_type == 'ptr':
                stored = locals_.get(offset)
                if not stored or stored[0] != 'memory':
                    raise ValueError('State spill/reload or unknown pointer alias')
                pointers[result] = stored
            continue
        match = re.fullmatch(rf'store (i\d+|ptr) ({VALUE}), ptr ({SSA}), align (1|4|8)', operation)
        if match and not result:
            value_type, value, address = match[1], match[2], match[3]
            origins = operands([value]); root, offset = pointer(address)
            if root == 'local' and value_type != local_types[offset]:
                raise ValueError('Mismatched local store type')
            if value_type == 'ptr':
                if origins or root != 'local':
                    raise ValueError('Unreviewed pointer escape')
                stored = pointer(value)
                if stored[0] == 'state' and value != '%state':
                    raise ValueError('State alias spill is unsupported')
                locals_[offset] = stored
                continue
            width = (int(value_type[1:]) + 7) // 8
            if root == 'state' and offset + width > 3504:
                raise ValueError('State store extent is outside reviewed storage')
            if origins:
                if root != 'state' or offset not in DEAD_FLAG_OFFSETS or width != 1 or value_type != 'i8':
                    raise ValueError('Undefined value reaches an observable store')
                if offset in dirty:
                    raise ValueError('Multiple undefined stores to the same flag')
                dirty[offset] = {'origins': sorted(origins), 'store_instruction': index}
                terminals.append({'offset': offset, 'origins': sorted(origins),
                                  'store_instruction': index, 'block': block})
            elif root == 'state':
                overlap = [slot for slot in dirty if offset <= slot < offset + width]
                if overlap and (width != 1 or value_type != 'i8' or overlap != [offset]):
                    raise ValueError('Partial or broad overwrite of undefined flag')
                if offset in dirty:
                    overwrites.append({'offset': offset, **dirty.pop(offset),
                                       'overwrite_instruction': index, 'block': block})
            elif root != 'local':
                raise ValueError('Unreviewed direct pointer store')
            continue
        match = re.fullmatch(rf'(?:tail )?call (.+?) @([A-Za-z0-9_.$]+)\((.*?)\)(?: #\d+)?', operation)
        if match and result:
            prefix, name, args = match[1], match[2], match[3]
            values = re.findall(SSA, args)
            if operands(values):
                raise ValueError('Undefined SSA value escapes through a call')
            if name == UNDEFINED_FLAG:
                if prefix != 'zeroext i8' or args:
                    raise ValueError('Undefined helper signature or call differs')
                roots.append(result); taints[result] = {result}
            elif name in scalar_calls:
                if 'ptr' in args or '%' in prefix:
                    raise ValueError('Flag identity has pointer or unreviewed type')
            elif name in BRIDGES:
                pointer_values = re.findall(rf'ptr(?: noundef)? ({SSA})', args)
                if name == '__remill_function_return':
                    if dirty or not pointer_values or pointer_values[0] != '%state':
                        raise ValueError('State call observes undefined flags')
                    pointer_values = pointer_values[1:]
                    pointers[result] = ('memory', 0)
                elif name == '__remill_write_memory_32':
                    pointers[result] = ('memory', 0)
                if not pointer_values or any(pointer(value)[0] != 'memory' for value in pointer_values):
                    raise ValueError('Memory bridge receives a State alias')
            else:
                raise ValueError('Unreviewed call during dead-flag proof')
            continue
        match = re.fullmatch(rf'(?:add|sub|mul|shl|lshr|ashr|and|or|xor)(?: nuw)?(?: nsw)? i\d+ ({VALUE}), ({VALUE})', operation)
        comparison = re.fullmatch(rf'icmp (?:eq|ne|ult|ule|ugt|uge|slt|sle|sgt|sge) i\d+ ({VALUE}), ({VALUE})', operation)
        cast = re.fullmatch(rf'(?:zext|sext|trunc)(?: nuw)?(?: nsw)? i\d+ ({VALUE}) to i\d+', operation)
        if result and (match or comparison or cast):
            active = match or comparison or cast
            origins = operands(active.groups())
            # Only the exact reviewed booleanization chain may carry havoc.
            if origins and not (re.fullmatch(rf'icmp ne i8 {SSA}, 0', operation) or
                                re.fullmatch(rf'zext i1 {SSA} to i8', operation)):
                raise ValueError('Unreviewed pure use of undefined SSA value')
            taints[result] = origins
            continue
        raise ValueError('Unreviewed instruction in dead-flag proof: ' + operation)
    if dirty or len(roots) != 2 or len(terminals) != 2 or len(overwrites) != 2:
        raise ValueError('Dead-flag proof requires exactly two overwritten undefined values')
    if {item['offset'] for item in terminals} != DEAD_FLAG_OFFSETS or \
            {origin for item in terminals for origin in item['origins']} != set(roots):
        raise ValueError('Undefined helper does not feed the two reviewed dead flags')
    # Any SSA derived from a root must have at least one checked use; otherwise
    # extra dead/unsupported chains could conceal an unreviewed use pattern.
    for name, origins in taints.items():
        if origins and not any(re.search(rf'(?<![\w.$]){re.escape(name)}(?![\w.$])', line.split(' = ', 1)[-1])
                               for _, _, line in instructions):
            raise ValueError('Unconsumed undefined SSA chain')
    return {'policy': 'straight-line-ssa-overwritten-af-of-v1', 'undefined_calls': len(roots),
            'replacement_value': 0, 'flag_offsets': sorted(DEAD_FLAG_OFFSETS),
            'blocks': chain, 'stores': terminals, 'overwrites': overwrites,
            'observable_undefined_values': 0}


class LLVM:
    def __init__(self, path):
        self.dll = c.CDLL(str(Path(path).resolve()))
        p, u, s, b = c.c_void_p, c.c_uint, c.c_size_t, c.c_char_p
        signatures = {
            "GetVersion": (None, [c.POINTER(u)] * 3),
            "ContextCreate": (p, []), "ContextDispose": (None, [p]),
            "CreateMemoryBufferWithContentsOfFile": (u, [b, c.POINTER(p), c.POINTER(p)]),
            "ParseIRInContext": (u, [p, p, c.POINTER(p), c.POINTER(p)]),
            "DisposeMessage": (None, [p]), "DisposeModule": (None, [p]),
            "GetDataLayoutStr": (b, [p]), "CreateTargetData": (p, [b]),
            "DisposeTargetData": (None, [p]), "PointerSize": (u, [p]),
            "ABISizeOfType": (c.c_ulonglong, [p, p]),
            "ABIAlignmentOfType": (u, [p, p]),
            "OffsetOfElement": (c.c_ulonglong, [p, p, u]),
            "GetTypeByName2": (p, [p, b]), "IsOpaqueStruct": (u, [p]),
            "CountStructElementTypes": (u, [p]),
            "GetNamedFunction": (p, [p, b]), "GlobalGetValueType": (p, [p]),
            "CountParams": (u, [p]), "GetParam": (p, [p, u]),
            "IsFunctionVarArg": (u, [p]),
            "TypeOf": (p, [p]), "GetTypeKind": (u, [p]),
            "GetIntTypeWidth": (u, [p]), "GetReturnType": (p, [p]),
            "GetFirstFunction": (p, [p]), "GetNextFunction": (p, [p]),
            "GetValueName2": (p, [p, c.POINTER(s)]), "GetFirstUse": (p, [p]),
            "GetNextUse": (p, [p]), "GetUser": (p, [p]),
            "CountBasicBlocks": (u, [p]), "GetFirstBasicBlock": (p, [p]),
            "GetNextBasicBlock": (p, [p]), "GetFirstInstruction": (p, [p]),
            "GetNextInstruction": (p, [p]), "IsAIntToPtrInst": (p, [p]),
            "GetInstructionParent": (p, [p]), "GetBasicBlockParent": (p, [p]),
            "IsAGetElementPtrInst": (p, [p]), "GetGEPSourceElementType": (p, [p]),
            "GetNumOperands": (u, [p]), "GetOperand": (p, [p, u]),
            "IsAConstantInt": (p, [p]), "ConstIntGetSExtValue": (c.c_longlong, [p]),
            "StructGetTypeAtIndex": (p, [p, u]), "GetElementType": (p, [p]),
            "PrintValueToString": (p, [p]),
            "IsAPtrToIntInst": (p, [p]), "IsACallInst": (p, [p]),
            "GetCalledValue": (p, [p]), "IsAFunction": (p, [p]),
            "GetFunctionCallConv": (u, [p]), "SetFunctionCallConv": (None, [p, u]),
            "SetInstructionCallConv": (None, [p, u]),
            "RemoveStringAttributeAtIndex": (None, [p, u, b, u]),
            "GetEnumAttributeKindForName": (u, [b, s]),
            "RemoveEnumAttributeAtIndex": (None, [p, u, u]),
            "RemoveCallSiteEnumAttribute": (None, [p, u, u]),
            "SetTarget": (None, [p, b]), "SetDataLayout": (None, [p, b]),
            "AddFunction": (p, [p, b, p]),
            "AppendBasicBlockInContext": (p, [p, p, b]),
            "CreateBuilderInContext": (p, [p]), "DisposeBuilder": (None, [p]),
            "PositionBuilderAtEnd": (None, [p, p]),
            "BuildCall2": (p, [p, p, p, c.POINTER(p), u, b]),
            "BuildRet": (p, [p, p]), "VerifyModule": (u, [p, u, c.POINTER(p)]),
            "ConstInt": (p, [p, c.c_ulonglong, u]),
            "PrintModuleToFile": (u, [p, b, c.POINTER(p)]),
        }
        for name, (result, args) in signatures.items():
            function = getattr(self.dll, "LLVM" + name)
            function.restype, function.argtypes = result, args
            setattr(self, name, function)
        version = [u(), u(), u()]
        self.GetVersion(*(c.byref(value) for value in version))
        self.version = tuple(value.value for value in version)
        if self.version != (21, 1, 8):
            raise ValueError(f"Expected pinned LLVM 21.1.8, got {self.version}")

    def check(self, result, error):
        message = c.string_at(error).decode(errors="replace") if error.value else ""
        if error.value:
            self.DisposeMessage(error)
            error.value = None
        if result:
            raise ValueError(message or "LLVM operation failed")

    def name(self, value):
        length = c.c_size_t()
        pointer = self.GetValueName2(value, c.byref(length))
        return c.string_at(pointer, length.value).decode()

    @staticmethod
    def iterate(first, advance):
        while first:
            yield first
            first = advance(first)

    def kind(self, value):
        value_type = self.TypeOf(value)
        kind = self.GetTypeKind(value_type)
        if kind == 8:  # LLVMIntegerTypeKind
            return "i" + str(self.GetIntTypeWidth(value_type))
        if kind == 12:  # LLVMPointerTypeKind
            return "ptr"
        raise ValueError("Unreviewed boundary type")

    def signature(self, function):
        result_type = self.GetReturnType(self.GlobalGetValueType(function))
        result_kind = self.GetTypeKind(result_type)
        if result_kind == 12:
            result = "ptr"
        elif result_kind == 8:
            result = "i" + str(self.GetIntTypeWidth(result_type))
        else:
            raise ValueError("Unreviewed result type")
        return result, [self.kind(self.GetParam(function, index))
                        for index in range(self.CountParams(function))]


def checked_state_offsets(api, entry, data):
    """Constant byte locations of direct State GEPs under the checked layout."""
    locations = {}
    state = api.GetParam(entry, 0)
    for block in api.iterate(api.GetFirstBasicBlock(entry), api.GetNextBasicBlock):
        for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
            if not api.IsAGetElementPtrInst(instruction) or api.GetOperand(instruction, 0) != state:
                continue
            current = api.GetGEPSourceElementType(instruction)
            offset = 0
            for number in range(1, api.GetNumOperands(instruction)):
                value = api.GetOperand(instruction, number)
                if not api.IsAConstantInt(value):
                    raise ValueError('Nonconstant State GEP in dead-flag proof')
                index = api.ConstIntGetSExtValue(value)
                if number == 1:
                    offset += index * api.ABISizeOfType(data, current)
                elif api.GetTypeKind(current) == 10:
                    if not 0 <= index < api.CountStructElementTypes(current):
                        raise ValueError('Invalid State structure GEP')
                    offset += api.OffsetOfElement(data, current, index)
                    current = api.StructGetTypeAtIndex(current, index)
                elif api.GetTypeKind(current) == 11:
                    current = api.GetElementType(current)
                    offset += index * api.ABISizeOfType(data, current)
                else:
                    raise ValueError('Unreviewed State GEP traversal')
            rendered = api.PrintValueToString(instruction)
            try:
                printed = c.string_at(rendered).decode()
            finally:
                api.DisposeMessage(rendered)
            name = re.match(r'\s*(%[A-Za-z0-9_.$]+) =', printed)
            if not name:
                raise ValueError('State GEP has unreviewed SSA spelling')
            locations[name[1]] = offset
    return locations


def adapt(dll, guest, host, record, profile='fixture'):
    if profile not in PROFILES:
        raise ValueError('Unknown reviewed adapter profile')
    api = LLVM(dll)
    context, module, buffer, error = api.ContextCreate(), c.c_void_p(), c.c_void_p(), c.c_void_p()
    builder, guest_data, host_data = None, None, None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(),
                  c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        guest_layout = api.GetDataLayoutStr(module).decode()
        guest_data = api.CreateTargetData(guest_layout.encode())
        host_data = api.CreateTargetData(HOST_LAYOUT.encode())
        if api.PointerSize(guest_data) != 4 or api.PointerSize(host_data) != 8:
            raise ValueError("Unexpected guest/host pointer widths")
        layouts = {}
        for name in re.findall(r"^%([^ =]+) = type", guest.read_text(), re.MULTILINE):
            struct = api.GetTypeByName2(context, name.encode())
            if not struct or api.IsOpaqueStruct(struct):
                raise ValueError("Missing or opaque State storage type")
            def layout(data):
                return {"size": api.ABISizeOfType(data, struct),
                        "alignment": api.ABIAlignmentOfType(data, struct),
                        "offsets": [api.OffsetOfElement(data, struct, index)
                                    for index in range(api.CountStructElementTypes(struct))]}
            before, after = layout(guest_data), layout(host_data)
            if before != after:
                raise ValueError(f"Layout changes for {name}: {before} -> {after}")
            layouts[name] = before
        if layouts.get("struct.State", {}).get("size") != 3504:
            raise ValueError("Unexpected guest State layout")
        entry_name = f'sub_{PROFILES[profile]:x}'
        entry = api.GetNamedFunction(module, entry_name.encode())
        if not entry or not api.CountBasicBlocks(entry) or api.signature(entry) != ("ptr", ["ptr", "i32", "ptr"]):
            raise ValueError("Missing or incompatible reviewed entry")
        if api.GetNamedFunction(module, b"mw34_lifted_entry"):
            raise ValueError("Host entry already exists")
        dead_flags = None
        if profile != 'fixture':
            if (layouts.get('struct.State', {}).get('offsets') != [0] or
                    layouts.get('struct.X86State', {}).get('offsets', [])[2:3] != [2064] or
                    layouts.get('struct.ArithFlags', {}).get('offsets') != list(range(16))):
                raise ValueError('Reviewed arithmetic flag storage differs')
            dead_flags = prove_dead_flags(guest.read_text(), profile,
                                         checked_state_offsets(api, entry, guest_data))
            undefined = api.GetNamedFunction(module, UNDEFINED_FLAG.encode())
            if not undefined or api.signature(undefined) != ('i8', []) or \
                    api.IsFunctionVarArg(api.GlobalGetValueType(undefined)) or \
                    api.CountBasicBlocks(undefined):
                raise ValueError('Unreviewed undefined helper signature or definition')
            uses = list(api.iterate(api.GetFirstUse(undefined), api.GetNextUse))
            if len(uses) != dead_flags['undefined_calls']:
                raise ValueError('Undefined helper has uses outside the proved calls')
            for use in uses:
                user = api.GetUser(use)
                if not api.IsACallInst(user) or api.GetCalledValue(user) != undefined or \
                        api.GetBasicBlockParent(api.GetInstructionParent(user)) != entry:
                    raise ValueError('Undefined helper escapes the proved entry')
        builder = api.CreateBuilderInContext(context)
        nounwind = api.GetEnumAttributeKindForName(b"nounwind", 8)
        functions = list(api.iterate(api.GetFirstFunction(module), api.GetNextFunction))
        lowered, bridges = [], []
        annotations = ANNOTATIONS | ({'__remill_compare_sle'} if profile != 'fixture' else set())
        for function in functions:
            name = api.name(function)
            declaration = api.CountBasicBlocks(function) == 0
            if declaration and api.GetFirstUse(function) and not name.startswith("llvm."):
                if name == UNDEFINED_FLAG and dead_flags:
                    # This value is arbitrary only because every actual call
                    # passed the complete SSA/store/overwrite proof above.
                    block = api.AppendBasicBlockInContext(context, function, b"proved_unobserved")
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.ConstInt(api.GetReturnType(api.GlobalGetValueType(function)), 0, 0))
                elif name in annotations:
                    if api.signature(function) != ("i1", ["i1"]):
                        raise ValueError("Unexpected flag annotation signature")
                    if name == '__remill_compare_sle' and api.IsFunctionVarArg(api.GlobalGetValueType(function)):
                        raise ValueError('Unexpected signed comparison annotation varargs')
                    # Matches upstream tests/X86/Run.cpp: return result.
                    block = api.AppendBasicBlockInContext(context, function, b"identity")
                    api.PositionBuilderAtEnd(builder, block)
                    api.BuildRet(builder, api.GetParam(function, 0))
                    lowered.append(name)
                elif name in BRIDGES:
                    expected = {
                        '__remill_read_memory_32': ('i32', ['ptr', 'i32']),
                        '__remill_write_memory_32': ('ptr', ['ptr', 'i32', 'i32']),
                        '__remill_function_return': ('ptr', ['ptr', 'i32', 'ptr']),
                    }[name]
                    if api.signature(function) != expected:
                        raise ValueError("Guest address bridge widened or signature changed")
                    api.SetFunctionCallConv(function, 0)
                    api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
                    bridges.append(name)
                else:
                    raise ValueError("Unsupported external function: " + name)
            for attribute in (b"target-cpu", b"target-features"):
                api.RemoveStringAttributeAtIndex(function, FUNCTION_INDEX, attribute, len(attribute))
            # Do not carry guest runtime attributes into the host boundary.
            api.RemoveEnumAttributeAtIndex(function, FUNCTION_INDEX, nounwind)
            for block in api.iterate(api.GetFirstBasicBlock(function), api.GetNextBasicBlock):
                for instruction in api.iterate(api.GetFirstInstruction(block), api.GetNextInstruction):
                    if api.IsAIntToPtrInst(instruction) or api.IsAPtrToIntInst(instruction):
                        raise ValueError("Unreviewed pointer/integer conversion")
                    if api.IsACallInst(instruction):
                        called = api.GetCalledValue(instruction)
                        if not api.IsAFunction(called):
                            raise ValueError("Indirect call is unsupported")
                        api.RemoveCallSiteEnumAttribute(instruction, FUNCTION_INDEX, nounwind)
                        if api.name(called) in BRIDGES:
                            api.SetInstructionCallConv(instruction, 0)
        api.SetTarget(module, b"x86_64-pc-windows-msvc")
        api.SetDataLayout(module, HOST_LAYOUT.encode())
        wrapper = api.AddFunction(module, b"mw34_lifted_entry", api.GlobalGetValueType(entry))
        block = api.AppendBasicBlockInContext(context, wrapper, b"entry")
        api.PositionBuilderAtEnd(builder, block)
        args = (c.c_void_p * 3)(*(api.GetParam(wrapper, index) for index in range(3)))
        call = api.BuildCall2(builder, api.GlobalGetValueType(entry), entry, args, 3, b"memory")
        api.SetInstructionCallConv(call, api.GetFunctionCallConv(entry))
        api.BuildRet(builder, call)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
        host.parent.mkdir(parents=True, exist_ok=True)
        api.check(api.PrintModuleToFile(module, str(host.resolve()).encode(), c.byref(error)), error)
        report = {"version": 1, "llvm_version": api.version, "dll_sha256": digest(dll),
                  "profile": profile, "entry_va": PROFILES[profile],
                  "guest_ir_sha256": digest(guest), "host_ir_sha256": digest(host),
                  "guest_pointer_bits": 32, "host_pointer_bits": 64,
                  "guest_layout": guest_layout, "host_layout": HOST_LAYOUT,
                  "all_struct_layouts_equal": True, "struct_layouts": layouts,
                  "state_bytes": 3504, "guest_address_intrinsics_bits": 32,
                  "host_abi": "Windows x64 C wrapper", "bridges": sorted(bridges),
                  "flag_annotation_identities": sorted(lowered),
                  "indirect_calls": 0, "pointer_integer_conversions": 0,
                  "undefined_flag_policy": dead_flags}
        record.write_text(json.dumps(report, indent=2) + "\n")
        print("Verified guest State storage and emitted native x64 host bridge")
    finally:
        if builder:
            api.DisposeBuilder(builder)
        for data in (guest_data, host_data):
            if data:
                api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(context)


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-dll", type=Path, required=True)
    parser.add_argument("--guest", type=Path, required=True)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument('--profile', choices=PROFILES, default='fixture')
    arguments = parser.parse_args()
    adapt(arguments.llvm_dll, arguments.guest, arguments.host, arguments.record, profile=arguments.profile)
