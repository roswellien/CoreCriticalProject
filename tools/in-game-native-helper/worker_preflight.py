"""Exercise the real linked helper object through a pipe server, without game launch.

The independently authored formula below is a BEFORE-only result observer.
Execution is exclusively the frozen mw34_lifted_entry in the x64 worker.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import time
import uuid

ROOT, FRAME, BROKER, BASE, SIZE = 0x409ED0, 0x20001800, 0x10000100, 0x20001000, 4096
ARITHMETIC = 0x8D5
U32 = 0xFFFFFFFF

class Cpu(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [(name, C.c_uint32) for name in ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi', 'flags', 'eip')]

class Request(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('magic', C.c_char * 8)] + [(name, C.c_uint32) for name in ('version', 'bytes', 'sequence', 'kind', 'pid', 'tid')] + [
        ('cpu', Cpu), ('fx', C.c_ubyte * 512), ('env', C.c_ubyte * 28)] + [(name, C.c_uint32) for name in ('n', 'caller', 'memory_seed')]

class Event(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [(name, C.c_uint32) for name in ('address', 'value', 'width', 'write')]

class Response(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('magic', C.c_char * 8)] + [(name, C.c_uint32) for name in ('version', 'bytes', 'sequence', 'status', 'worker_pid')] + [
        ('cpu', Cpu), ('fx', C.c_ubyte * 512), ('env', C.c_ubyte * 28), ('memory', C.c_ubyte * 4096), ('events', Event * 2),
        ('reads', C.c_uint32), ('returns', C.c_uint32), ('complete', C.c_uint32), ('error', C.c_char * 192)]

assert C.sizeof(Request) == 624 and C.sizeof(Response) == 4940
k = C.WinDLL('kernel32', use_last_error=True)
class Overlapped(C.Structure):
    _fields_ = [('Internal', C.c_size_t), ('InternalHigh', C.c_size_t), ('Offset', W.DWORD), ('OffsetHigh', W.DWORD), ('hEvent', W.HANDLE)]

def prototype(name, result, *args):
    function = getattr(k, name); function.restype = result; function.argtypes = args; return function

create_pipe = prototype('CreateNamedPipeW', W.HANDLE, W.LPCWSTR, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, C.c_void_p)
connect_pipe = prototype('ConnectNamedPipe', W.BOOL, W.HANDLE, C.POINTER(Overlapped))
read_file = prototype('ReadFile', W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.POINTER(Overlapped))
write_file = prototype('WriteFile', W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.POINTER(Overlapped))
create_event = prototype('CreateEventW', W.HANDLE, C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR)
wait = prototype('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
completion = prototype('GetOverlappedResult', W.BOOL, W.HANDLE, C.POINTER(Overlapped), C.POINTER(W.DWORD), W.BOOL)
cancel = prototype('CancelIoEx', W.BOOL, W.HANDLE, C.POINTER(Overlapped))
close = prototype('CloseHandle', W.BOOL, W.HANDLE)
get_tid = prototype('GetCurrentThreadId', W.DWORD)

def ensure(condition, why):
    if not condition: raise AssertionError(why)

def finish(pipe, operation, event, done):
    if wait(event, 30000) != 0:
        cancel(pipe, C.byref(operation)); wait(event, 5000)
        raise TimeoutError('Helper preflight pipe operation timed out')
    if not completion(pipe, C.byref(operation), C.byref(done), False): raise C.WinError(C.get_last_error())

def transfer(pipe, data, writing):
    buffer = C.create_string_buffer(data); count = len(data) if writing else data; cursor = 0
    while cursor < count:
        event = create_event(None, True, False, None); ensure(event, 'Transfer event creation')
        operation = Overlapped(); operation.hEvent = event; done = W.DWORD()
        try:
            function = write_file if writing else read_file
            if not function(pipe, C.byref(buffer, cursor), count - cursor, C.byref(done), C.byref(operation)):
                ensure(C.get_last_error() == 997, 'Pipe transfer start failed'); finish(pipe, operation, event, done)
            ensure(0 < done.value <= count - cursor, 'Truncated helper pipe transfer'); cursor += done.value
        finally: close(event)
    return buffer.raw[:count]

def request(sequence, n, rng):
    r = Request(); r.magic = b'MWHLPR01'; r.version = 1; r.bytes = C.sizeof(r)
    r.sequence = sequence; r.kind = 1; r.pid = os.getpid(); r.tid = get_tid()
    r.cpu = Cpu(*(rng.getrandbits(32) for _ in range(10))); r.cpu.eip = ROOT
    r.cpu.esp = rng.randrange(0x10000, 0x7FFEFFF0); r.caller = 0x12345678
    # Opaque bytes are deliberately unconstrained and never loaded into host FP.
    r.fx[:] = rng.randbytes(512); r.env[:] = rng.randbytes(28)
    r.n = n; r.memory_seed = rng.getrandbits(32); return r

def initial_memory(r):
    memory = bytearray((r.memory_seed + i * 37) & 255 for i in range(SIZE))
    struct.pack_into('<II', memory, FRAME - BASE, BROKER, r.n); return memory

def expected_cpu(r):
    # Independent review observer: final SUB alone defines arithmetic flags;
    # both surrounding LEAs preserve them. This code does not execute the leaf.
    cpu = Cpu.from_buffer_copy(bytes(r.cpu)); minuend = r.n * 48 & U32; difference = minuend - r.n & U32
    flags = int(minuend < r.n)
    flags |= int((difference & 255).bit_count() % 2 == 0) << 2
    flags |= int(bool((minuend ^ r.n ^ difference) & 16)) << 4
    flags |= int(difference == 0) << 6; flags |= (difference >> 31) << 7
    flags |= int(bool((minuend ^ r.n) & (minuend ^ difference) & 0x80000000)) << 11
    cpu.eax = cpu.ecx + r.n * 188 + 312 & U32; cpu.edx = difference
    cpu.esp += 8; cpu.eip = r.caller; cpu.flags = (r.cpu.flags & ~ARITHMETIC) | flags
    return cpu

def verify(r, a, worker_pid):
    ensure(a.magic == b'MWHLPA01' and a.version == 1 and a.bytes == C.sizeof(a) and a.sequence == r.sequence and a.worker_pid == worker_pid, 'Helper response identity/framing')
    ensure(a.status == 0 and a.complete == 1 and a.reads == 2 and a.returns == 1 and not a.error, 'Actual compiled read/RET closure')
    ensure(bytes(a.cpu) == bytes(expected_cpu(r)), 'Compiled CPU/fullflags differ from independent BEFORE-only observer')
    ensure(bytes(a.fx) == bytes(r.fx) and bytes(a.env) == bytes(r.env), 'Opaque wholeFX512/ENV28 preservation')
    ensure(bytes(a.memory) == initial_memory(r), 'Whole readonly4096 owned page changed')
    expected = ((FRAME + 4, r.n, 4, 0), (FRAME, BROKER, 4, 0))
    actual = tuple(tuple(getattr(event, name) for name in ('address', 'value', 'width', 'write')) for event in a.events)
    ensure(actual == expected, 'Actual two checked read events differ')

def directed_n():
    values = set(range(256)); values.update((0x7FFFFFFF, 0x80000000, 0xFFFFFFFF))
    for bit in range(32):
        for delta in (-1, 0, 1): values.add(((1 << bit) + delta) & U32)
    for period in range(1, 48):
        for delta in (-1, 0, 1): values.add(((period << 32) // 48 + delta) & U32)
    for period in range(48):
        for delta in (-1, 0, 1): values.add((((period << 32) + (1 << 31)) // 48 + delta) & U32)
    return sorted(values)

def corruption_checks(r, good, worker_pid):
    offsets = [Cpu.__dict__[name].offset + Response.cpu.offset for name, _ in Cpu._fields_]
    offsets += [Response.cpu.offset + Cpu.flags.offset + bit // 8 for bit in range(32)]
    offsets += [Response.fx.offset + i for i in (0, 255, 511)] + [Response.env.offset + i for i in (0, 13, 27)]
    offsets += [Response.memory.offset + i for i in (0, 2047, 4095, FRAME - BASE, FRAME - BASE + 4)]
    offsets += [Response.events.offset + i for i in range(0, 32, 4)]
    offsets += [getattr(Response, name).offset for name in ('status', 'worker_pid', 'reads', 'returns', 'complete')]
    # Duplicate flag offsets are intentional: each full flag bit is changed.
    flags_start = len(Cpu._fields_)
    for index, offset in enumerate(offsets):
        raw = bytearray(bytes(good)); raw[offset] ^= 1 << ((index - flags_start) % 8) if flags_start <= index < flags_start + 32 else 1
        try: verify(r, Response.from_buffer_copy(raw), worker_pid)
        except AssertionError: continue
        raise AssertionError(f'Comparator silently accepted output corruption at{offset}')
    return len(offsets)

def startup_denials(args, output):
    controls = []
    for label, source, argument in (('changed-object', Path(args.object), 1), ('changed-game-leaf', Path(args.game), 0)):
        changed = bytearray(source.read_bytes()); changed[37584 if argument == 0 else -1] ^= 1
        path = output / (label + '.bin'); path.write_bytes(changed)
        inputs = [args.game, args.object]; inputs[argument] = str(path)
        result = subprocess.run([args.worker, *inputs, r'\\.\pipe\mw34-helper-invalid'], capture_output=True, timeout=8,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        ensure(result.returncode != 0 and result.stderr, f'Startup admitted{label}')
        controls.append(dict(label=label, exit_code=result.returncode, error=result.stderr.decode(errors='replace').strip(),
                             input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return controls

def run(args):
    output = Path(args.output); output.mkdir(parents=True, exist_ok=False)
    workspace = Path(__file__).resolve().parents[2]
    sources = [Path(__file__), Path(__file__).parent / 'worker.cpp', Path(__file__).parent / 'worker/CMakeLists.txt',
               Path(__file__).parent / 'protocol.hpp', workspace / 'tools/lifting/lifted_worker.cpp', Path(args.object)]
    report = dict(passed=False, game_launched=False, kind=1, live_function_credit=False,
                  execution='Actual frozen compiled helper object; independent formula used only as BEFORE-only observer',
                  worker=str(Path(args.worker).resolve()), worker_sha256=hashlib.sha256(Path(args.worker).read_bytes()).hexdigest(),
                  source_files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    name = rf'\\.\pipe\mw34-helper-preflight-{uuid.uuid4().hex}'
    pipe = create_pipe(name, 3 | 0x40000000, 8, 1, 16384, 16384, 60000, None)
    ensure(pipe != C.c_void_p(-1).value, 'Helper pipe server creation')
    event = create_event(None, True, False, None); operation = Overlapped(); operation.hEvent = event
    process = None; records = []; sequence = 1; positive = rejected = 0; rng = random.Random(0x409ED0)
    stdout = open(output / 'worker.stdout', 'wb'); stderr = open(output / 'worker.stderr', 'wb')
    try:
        connected = connect_pipe(pipe, C.byref(operation)); code = C.get_last_error()
        ensure(connected or code in (997, 535), 'Helper server connect start')
        process = subprocess.Popen([args.worker, args.game, args.object, name], stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        if not connected and code != 535: finish(pipe, operation, event, W.DWORD())
        def exchange(r):
            transfer(pipe, bytes(r), True); raw = transfer(pipe, C.sizeof(Response), False); a = Response.from_buffer_copy(raw)
            ensure(a.magic == b'MWHLPA01' and a.version == 1 and a.bytes == C.sizeof(a) and a.sequence == r.sequence
                   and a.worker_pid == process.pid, 'Response framing/pipe client process identity')
            records.append((bytes(r), raw)); return a
        r = request(sequence, 0, rng); r.kind = 0; a = exchange(r); sequence += 1
        ensure(a.status == 0 and not a.reads and not a.returns and not a.complete, 'Handshake grants no function credits')
        bits = (1, 4, 16, 64, 128, 2048, 1024)
        for flag_index in range(128):
            r = request(sequence, (0, 1, 0x7FFFFFFF, 0x80000000, U32)[flag_index % 5], rng); sequence += 1
            r.cpu.flags = 0x202 | sum(bit for i, bit in enumerate(bits) if flag_index >> i & 1)
            a = exchange(r); verify(r, a, process.pid); positive += 1
        directed = directed_n()
        for n in directed:
            wrap = -(n * 188 + 312) & U32
            for base in ((wrap - 1) & U32, wrap, (wrap + 1) & U32):
                r = request(sequence, n, rng); sequence += 1; r.cpu.ecx = base
                a = exchange(r); verify(r, a, process.pid); positive += 1
        for _ in range(512):
            r = request(sequence, rng.getrandbits(32), rng); sequence += 1
            a = exchange(r); verify(r, a, process.pid); positive += 1
        report['corrupted_output_denials'] = corruption_checks(r, a, process.pid)
        negatives = (
            ('wrong-root', lambda r: setattr(r.cpu, 'eip', ROOT + 1)),
            ('actual-ESP-wrap', lambda r: setattr(r.cpu, 'esp', 0xFFFFFFF8)),
            ('actual-ESP-low', lambda r: setattr(r.cpu, 'esp', 0)),
            ('missing-caller', lambda r: setattr(r, 'caller', 0)),
            ('unpinned-live-caller', lambda r: setattr(r, 'kind', 2)),
        )
        for label, mutate in negatives:
            r = request(sequence, rng.getrandbits(32), rng); sequence += 1; mutate(r); a = exchange(r)
            ensure(a.status == 2 and not a.reads and not a.returns and not a.complete and bytes(a.cpu) == bytes(r.cpu)
                   and bytes(a.fx) == bytes(r.fx) and bytes(a.env) == bytes(r.env), f'Unsupported input admitted or altered: {label}')
            rejected += 1
        for label, mutate in (
            ('framing', lambda r: setattr(r, 'magic', b'WRONG001')),
            ('version', lambda r: setattr(r, 'version', 2)),
            ('size', lambda r: setattr(r, 'bytes', C.sizeof(r) - 1)),
            ('process-owner', lambda r: setattr(r, 'pid', r.pid ^ 1)),
            ('thread-owner', lambda r: setattr(r, 'tid', 0)),
            ('unsupported-kind', lambda r: setattr(r, 'kind', 3)),
            ('repeated-handshake', lambda r: setattr(r, 'kind', 0)),
            ('replayed-sequence', lambda r: setattr(r, 'sequence', sequence - 1)),
        ):
            r = request(sequence, 0, rng); mutate(r); a = exchange(r)
            ensure(a.status == 2 and not a.reads and not a.returns and not a.complete, f'Protocol denial failed: {label}'); rejected += 1
        r = request(sequence, 0x12345678, rng); sequence += 1; a = exchange(r); verify(r, a, process.pid); positive += 1
        report['startup_denials'] = startup_denials(args, output)
        if args.idle_check_seconds:
            ensure(60 < args.idle_check_seconds <= 300, 'Idle persistence check must exceed the old60sec deadline and remain bounded')
            time.sleep(args.idle_check_seconds); ensure(process.poll() is None, 'Worker exited while pipe server was idle')
            r = request(sequence, 0xFFFFFFFF, rng); sequence += 1; a = exchange(r); verify(r, a, process.pid); positive += 1
            report['idle_seconds_then_successful_request'] = args.idle_check_seconds
        report.update(passed=True, positive_invocations=positive, rejected_requests=rejected, request_count=len(records),
                      compiled_reads=positive * 2, compiled_returns=positive, zero_guest_writes=True, full_flag_input_combinations=128,
                      directed_n_values=len(directed), randomized_cases=512, fp_bytes_compared=positive * 512, env_bytes_compared=positive * 28,
                      whole_owned_memory_bytes_compared=positive * SIZE)
    except Exception as exception:
        report['failure'] = str(exception); raise
    finally:
        close(pipe); close(event)
        if process is not None:
            try: report['worker_exit'] = process.wait(timeout=8)
            except subprocess.TimeoutExpired: process.kill(); report['worker_exit'] = process.wait(timeout=8)
        stdout.close(); stderr.close()
        with open(output / 'wire.bin', 'wb') as stream:
            for r, a in records: stream.write(r); stream.write(a)
        report['wire_sha256'] = hashlib.sha256((output / 'wire.bin').read_bytes()).hexdigest()
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    ensure(report.get('worker_exit') == 0, 'Persistent helper worker did not cleanly exit on server EOF')
    print(json.dumps(report))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for option in ('worker', 'game', 'object', 'output'): parser.add_argument('--' + option, required=True)
    parser.add_argument('--idle-check-seconds', type=float, default=0)
    run(parser.parse_args())
