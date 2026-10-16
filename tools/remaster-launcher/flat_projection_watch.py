"""Observe guest TL scratch accesses after the existing flat-memory transform.

Only pointers emitted by ir_cleanup.flat_mem are instrumented, plus recognized
remaining remill memory calls. State accesses are never selected by address.
Observer calls retain normal memory effects and may unwind on an unknown read.
"""
from pathlib import Path
import importlib.util
import re

_path = Path(__file__).resolve().parents[1]/'m4-crt-heap-carry/ir_cleanup.py'
_spec = importlib.util.spec_from_file_location('mw34_projection_ir_cleanup', _path)
_cleanup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cleanup)

LOW = 0x72f41c
HIGH = 0x73041c
HELPER = 'mw34_projection_flat_watch_range'
SIZES = {'i8': 1, 'i16': 2, 'i32': 4, 'i64': 8, 'float': 4, 'double': 8}
BRIDGE_SIZES = {'8': 1, '16': 2, '32': 4, '64': 8, 'f32': 4, 'f64': 8, 'f80': 10}

def _state_parameter(line):
    """The lifted-body ABI's first pointer is State, regardless of SSA name."""
    match = re.match(r'^define [^@]*@([\w.$]+)\(', line)
    if not match:
        return None
    start = match.end(); depth = 0
    for end in range(start, len(line)):
        c = line[end]
        if c == '(':
            depth += 1
        elif c == ')':
            if depth == 0: break
            depth -= 1
        elif c == ',' and depth == 0:
            break
    parameter = line[start:end].strip()
    value = re.search(r'(%[\w.]+)$', parameter)
    body_abi = match.group(1).startswith('mw34_attach_') and match.group(1).endswith('_body')
    if parameter.startswith('ptr ') and value and (body_abi or value.group(1) == '%state'):
        return value.group(1)
    return None

def watched_flat_mem(text, stats):
    """Drop-in flat_mem(text,stats), with bounded observers and explicit coverage."""
    if '@'+HELPER in text or re.search(r'%mw34\.f[zg]\d+\b', text):
        raise ValueError('Projection watch requires fresh, non-flat input')
    text = _cleanup.flat_mem(text, stats)
    addresses = dict(re.findall(r'^  %mw34\.fz(\d+) = zext i32 ([^\n]+) to i64$', text, re.M))
    tokens = dict(re.findall(r'^  %mw34\.fg(\d+) = getelementptr i8, ptr (%[\w.]+), i64 %mw34\.fz\d+$', text, re.M))
    counts = dict(flat_watch_reads=0, flat_watch_writes=0, flat_watch_bridge_reads=0,
                  flat_watch_bridge_writes=0, flat_watch_f80_reads=0, flat_watch_f80_writes=0)
    selected = set()
    lines = []
    state = None
    for line in text.split('\n'):
        if line.startswith('define '): state = _state_parameter(line)
        elif line == '}': state = None
        load = re.match(r'^  %[\w.]+ = load (i8|i16|i32|i64|float|double), ptr %mw34\.fg(\d+), align 1$', line)
        store = re.match(r'^  store (i8|i16|i32|i64|float|double) [^,]+, ptr %mw34\.fg(\d+), align 1$', line)
        access = load or store
        if access:
            ty, index = access.groups()
            if index not in addresses or index not in tokens or index in selected:
                raise ValueError('Exact one-to-one flat guest pointer/access required')
            if state is None:
                raise ValueError('Watched guest access requires explicit lifted State pointer')
            selected.add(index)
            write = int(store is not None)
            watch = f'  call void @{HELPER}(ptr {state}, ptr {tokens[index]}, i32 {addresses[index]}, i32 {SIZES[ty]}, i32 {write})'
            lines.extend([line, watch] if write else [watch, line])
            counts['flat_watch_writes' if write else 'flat_watch_reads'] += 1
        else:
            lines.append(line)
    if len(selected) != stats['flat_reads']+stats['flat_writes'] or set(addresses) != selected or set(tokens) != selected:
        raise ValueError('Not every generated flat memory access was instrumented')
    # Raw80 is deliberately NOT converted to a host FP value: retain its bridge
    # and byte payload. Recognized leftover scalar calls are observed as well.
    remaining = {}
    watched = []
    state = None
    for line in lines:
        if line.startswith('define '): state = _state_parameter(line)
        elif line == '}': state = None
        bridge = re.search(r'\b(call|invoke)\b[^@\n]*@__remill_(read|write)_memory_(\w+)\((.*)\)', line)
        if not bridge:
            watched.append(line); continue
        kind, direction, width, args = bridge.groups()
        address = re.match(r'ptr (?:[\w]+ )*(%[\w.]+), i32 (?:noundef )?(%[\w.]+|-?\d+)(?:,|$)', args)
        name = direction+'_'+width
        if kind != 'call' or width not in BRIDGE_SIZES or not address or 'musttail ' in line:
            remaining[name] = remaining.get(name, 0)+1
            watched.append(line); continue
        write = int(direction == 'write')
        if state is None:
            raise ValueError('Watched remaining bridge requires explicit lifted State pointer')
        watch = f'  call void @{HELPER}(ptr {state}, ptr {address.group(1)}, i32 {address.group(2)}, i32 {BRIDGE_SIZES[width]}, i32 {write})'
        watched.extend([line, watch] if write else [watch, line])
        counts['flat_watch_bridge_writes' if write else 'flat_watch_bridge_reads'] += 1
        if width == 'f80': counts['flat_watch_f80_writes' if write else 'flat_watch_f80_reads'] += 1
    stats.update(counts)
    stats['flat_watch_unhandled'] = remaining
    stats['flat_watch_unhandled_count'] = sum(remaining.values())
    stats['flat_watch_window'] = [LOW, HIGH]
    result = '\n'.join(watched)
    if not any(counts.values()):
        return result
    # Use unsigned 64-bit arithmetic for the unwrapped end. Inlining lets LLVM
    # update all successor/PHI edges; no original numeric blocks are split here.
    result += f'''
declare void @mw34_projection_flat_access(ptr, ptr, i32, i32, i32)
define internal void @{HELPER}(ptr %state, ptr %token, i32 %address, i32 %size, i32 %write) alwaysinline uwtable {{
watch_entry:
  %start = zext i32 %address to i64
  %length = zext i32 %size to i64
  %end = add i64 %start, %length
  %below_high = icmp ult i64 %start, {HIGH}
  %above_low = icmp ugt i64 %end, {LOW}
  %nonempty = icmp ne i32 %size, 0
  %overlap = and i1 %below_high, %above_low
  %observe = and i1 %overlap, %nonempty
  br i1 %observe, label %watch_observe, label %watch_exit
watch_observe:
  call void @mw34_projection_flat_access(ptr %state, ptr %token, i32 %address, i32 %size, i32 %write)
  br label %watch_exit
watch_exit:
  ret void
}}
'''
    return result
