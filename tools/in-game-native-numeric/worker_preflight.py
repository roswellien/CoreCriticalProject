"""Pipe-server tests of the real x64 worker; no x86 game/process launch.

The authored input domain is marked kind1. Positive responses must come from
the linked compiled Session, including its real events/routes and RET closure.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time
import uuid

ROOT, FRAME, BROKER, LEAF = 0x4C19F0, 0x20001800, 0x410A80, 0x780C10F0
CONTROLS = (0x7F, 0x47F, 0x87F, 0xC7F, 0x27F, 0x67F, 0xA7F, 0xE7F, 0x37F, 0x77F, 0xB7F, 0xF7F)
STICKY = (0, 2, 32, 34, 512, 514, 544, 546)
CAPTURED_BEFORE = Path(__file__).resolve().parents[2] / 'reports/mw3-live-native-numeric/20261008-055302-435459-f2b7abb0/game-captures/call-2.before.bin'
CAPTURED_BEFORE_SHA = '10001979c7a6aced3bc2b1c3421b15ef01df00294779cf3262b821ed31c5f19f'

class Cpu(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [(name, C.c_uint32) for name in ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi', 'flags', 'eip')]

class Request(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('magic', C.c_char * 8)] + [(name, C.c_uint32) for name in ('version', 'bytes', 'sequence', 'kind', 'pid', 'tid')] + [
        ('cpu', Cpu), ('fx', C.c_ubyte * 512), ('env', C.c_ubyte * 28), ('globals', C.c_ubyte * 44)] + [
        (name, C.c_uint32) for name in ('cs', 'ds', 'ss', 'fs_base', 'provider_base', 'provider_bits', 'iat_target', 'caller')]

class Event(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [(name, C.c_uint32) for name in ('pc', 'address', 'value', 'width', 'write')]

class Response(C.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('magic', C.c_char * 8)] + [(name, C.c_uint32) for name in ('version', 'bytes', 'sequence', 'status', 'worker_pid')] + [
        ('cpu', Cpu), ('fx', C.c_ubyte * 512), ('env', C.c_ubyte * 28), ('globals', C.c_ubyte * 44), ('events', Event * 22),
        ('routes', C.c_uint32 * 15), ('steps', C.c_uint32), ('complete', C.c_uint32), ('error', C.c_char * 192)]

assert C.sizeof(Request) == 688 and C.sizeof(Response) == 1352
k = C.WinDLL('kernel32', use_last_error=True)
ULONG_PTR = C.c_size_t
class Overlapped(C.Structure):
    _fields_ = [('Internal', ULONG_PTR), ('InternalHigh', ULONG_PTR), ('Offset', W.DWORD), ('OffsetHigh', W.DWORD), ('hEvent', W.HANDLE)]

def prototype(name, result, *args):
    function = getattr(k, name); function.restype = result; function.argtypes = args
    return function

create_pipe = prototype('CreateNamedPipeW', W.HANDLE, W.LPCWSTR, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, C.c_void_p)
connect_pipe = prototype('ConnectNamedPipe', W.BOOL, W.HANDLE, C.POINTER(Overlapped))
read_file = prototype('ReadFile', W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.POINTER(Overlapped))
write_file = prototype('WriteFile', W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.POINTER(Overlapped))
create_event = prototype('CreateEventW', W.HANDLE, C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR)
wait = prototype('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
overlapped_result = prototype('GetOverlappedResult', W.BOOL, W.HANDLE, C.POINTER(Overlapped), C.POINTER(W.DWORD), W.BOOL)
cancel = prototype('CancelIoEx', W.BOOL, W.HANDLE, C.POINTER(Overlapped))
close = prototype('CloseHandle', W.BOOL, W.HANDLE)
get_tid = prototype('GetCurrentThreadId', W.DWORD)

def ensure(condition, why):
    if not condition: raise AssertionError(why)

def finish(pipe, operation, event, done):
    if wait(event, 60000) != 0:
        cancel(pipe, C.byref(operation)); wait(event, 60000)
        raise TimeoutError('Numeric preflight pipe transfer timed out')
    if not overlapped_result(pipe, C.byref(operation), C.byref(done), False):
        raise C.WinError(C.get_last_error())

def transfer(pipe, data, writing):
    buffer = C.create_string_buffer(data if writing else data)
    count = len(data) if writing else data
    cursor = 0
    while cursor < count:
        event = create_event(None, True, False, None); ensure(event, 'Event creation')
        operation = Overlapped(); operation.hEvent = event; done = W.DWORD()
        try:
            function = write_file if writing else read_file
            if not function(pipe, C.byref(buffer, cursor), count - cursor, C.byref(done), C.byref(operation)):
                ensure(C.get_last_error() == 997, 'Pipe transfer start failed')
                finish(pipe, operation, event, done)
            ensure(0 < done.value <= count - cursor, 'Truncated pipe transfer')
            cursor += done.value
        finally: close(event)
    return buffer.raw[:count]

def word(array, offset, value, width=4):
    raw = value.to_bytes(width, 'little'); array[offset:offset + width] = raw

def input_request(sequence, cw=0x37F, depth=0, top=0, sticky=0, mxcsr=0x1F80):
    r = Request(); r.magic = b'MWNMXR01'; r.version = 1; r.bytes = C.sizeof(r)
    r.sequence = sequence; r.kind = 1; r.pid = os.getpid(); r.tid = get_tid()
    r.cpu = Cpu(0x13579BDF, 0x2468ACE0, 0x81726354, 0x10293847, 0x0012F800, 0x92837465,
                0x56473829, 0xAABBCCDD, 0x202 | (sequence % 2) * 0xCD5, ROOT)
    # Distinct reserved bytes test the transport's preservation, rather than a
    # memset-derived claim that numerical/reserved bytes were all live input.
    r.fx[:] = bytes((i * 17 + 0x39) & 255 for i in range(512))
    sw = top << 11 | sticky
    word(r.fx, 0, cw, 2); word(r.fx, 2, sw, 2)
    r.fx[4] = sum(1 << ((top + i) & 7) for i in range(depth))
    # Measured FX legacy metadata elision must remain acceptable.
    r.fx[6:24] = bytes(18); word(r.fx, 24, mxcsr); word(r.fx, 28, 0xFFFF)
    tag = 0xFFFF
    for logical in range(8):
        word(r.fx, 32 + 16 * logical, 0x8000000000000000 + (logical << 56), 8)
        word(r.fx, 40 + 16 * logical, 0x4000 | (0x8000 if logical % 2 else 0), 2)
        if logical < depth: tag &= ~(3 << (2 * ((top + logical) & 7)))
    for offset, value in ((0, 0xFFFF0000 | cw), (4, 0xFFFF0000 | sw), (8, 0xFFFF0000 | tag),
                          (12, 0x11223344), (16, 0x11D0000 | 0x23), (20, 0x55667788), (24, 0xFFFF002B)):
        word(r.env, offset, value)
    r.globals[:] = bytes((sequence + i * 31) & 255 for i in range(44))
    r.cs = 0x23; r.ds = r.ss = 0x2B; r.fs_base = 0x7FFDE000
    r.provider_base = 0x780C0000; r.provider_bits = 0x7F7FFFFF; r.iat_target = LEAF; r.caller = 0x00412345
    return r

def verify_positive(r, a):
    ensure(a.status == 0 and a.complete == 1 and a.steps == 22, f'Compiled positive rejected: {bytes(a.error)!r}')
    expected_cpu = Cpu.from_buffer_copy(bytes(r.cpu)); expected_cpu.esp += 4; expected_cpu.eip = r.caller
    ensure(bytes(a.cpu) == bytes(expected_cpu), 'CPU/fullflags/live ESP/caller projection')
    ensure(bytes(a.globals) == struct.pack('<11I', 0x7F7FFFFF, *([0] * 10)), 'Native eleven globals')
    wanted_fx = bytearray(r.fx); wanted_fx[2:4] = (int.from_bytes(wanted_fx[2:4], 'little') & ~512).to_bytes(2, 'little')
    wanted_fx[32 + 7 * 16:42 + 7 * 16] = struct.pack('<QH', 0xFFFFFF0000000000, 0x407E)
    ensure(bytes(a.fx) == wanted_fx, 'Defined numeric/raw80 output plus reserved/FX metadata preservation')
    wanted_env = bytearray(r.env); wanted_env[4:6] = wanted_fx[2:4]
    wanted_env[12:24] = struct.pack('<III', 0x4C1A09, 0x11D0000 | 0x23, 0x60B368)
    ensure(bytes(a.env) == wanted_env, 'Native separate whole legacy ENV')
    routes = (BROKER, ROOT, BROKER, 0, 1, 0x4C19F3, 0x4C1A00, 0x4C19F8, 0, 1, 0x4C1A03, 0x5BB4FC, 0x4C1A09, 1, 1)
    ensure(tuple(a.routes) == routes, 'Actual completed direct/body/import call records')
    raw_iat = a.events[3].value
    expected = [(ROOT, FRAME - 4, r.cpu.ebp, 4, 1), (0x4C19F3, FRAME - 8, 0x4C19F8, 4, 1),
                (0x4C1A00, FRAME - 12, FRAME - 4, 4, 1), (0x4C1A03, 0x5BB4FC, raw_iat, 4, 0),
                (0x4C1A03, FRAME - 16, 0x4C1A09, 4, 1), (LEAF, 0x78115004, 0x7F7FFFFF, 4, 0),
                (LEAF + 6, FRAME - 16, 0x4C1A09, 4, 0), (0x4C1A09, 0x60B368, 0x7F7FFFFF, 4, 1)]
    expected += [(0x4C1A0F + 10 * i, 0x60B36C + 4 * i, 0, 4, 1) for i in range(10)]
    expected += [(0x4C1A73, FRAME - 12, FRAME - 4, 4, 0), (0x4C1A74, FRAME - 8, 0x4C19F8, 4, 0),
                 (0x4C19F8, FRAME - 4, r.cpu.ebp, 4, 0), (0x4C19F9, FRAME, BROKER, 4, 0)]
    actual = [tuple(getattr(event, name) for name in ('pc', 'address', 'value', 'width', 'write')) for event in a.events]
    ensure(actual == expected and raw_iat != LEAF, 'Actual ordered compiled event values/raw-file IAT owner')

def run(args):
    output = Path(args.output); output.mkdir(parents=True, exist_ok=False)
    name = rf'\\.\pipe\mw34-numeric-preflight-{uuid.uuid4().hex}'
    pipe = create_pipe(name, 3 | 0x40000000, 8, 1, 8192, 8192, 60000, None)
    ensure(pipe != C.c_void_p(-1).value, 'Preflight pipe server creation')
    event = create_event(None, True, False, None); operation = Overlapped(); operation.hEvent = event
    process = None; records = []; sequence = 1; positive = rejected = 0
    stdout = open(output / 'worker.stdout', 'wb'); stderr = open(output / 'worker.stderr', 'wb')
    report = {'passed': False, 'original_execution': False, 'kind': 1, 'live_function_credit': False,
              'worker': str(Path(args.worker).resolve()), 'worker_sha256': hashlib.sha256(Path(args.worker).read_bytes()).hexdigest()}
    try:
        connected = connect_pipe(pipe, C.byref(operation)); code = C.get_last_error()
        ensure(connected or code in (997, 535), 'Server connect start')
        process = subprocess.Popen([args.worker, args.game, args.provider, args.object, name], stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        if not connected and code != 535: finish(pipe, operation, event, W.DWORD())
        def exchange(r):
            transfer(pipe, bytes(r), True); raw = transfer(pipe, C.sizeof(Response), False)
            a = Response.from_buffer_copy(raw)
            ensure(a.magic == b'MWNMXA01' and a.version == 1 and a.bytes == C.sizeof(a) and a.sequence == r.sequence
                   and a.worker_pid == process.pid, 'Response identity/framing')
            records.append((bytes(r), raw)); return a
        r = input_request(sequence); r.kind = 0; a = exchange(r); sequence += 1
        ensure(a.status == 0 and not a.steps and not a.complete and not any(a.routes), 'Handshake has no function credits')
        for index, cw in enumerate(CONTROLS):
            for depth in (0, 1, 7):
                for top in (0, 7):
                    for mxcsr in (0x1F80, 0x1FA0):
                        r = input_request(sequence, cw, depth, top, STICKY[(index + depth + top) % 8], mxcsr); sequence += 1
                        verify_positive(r, exchange(r)); positive += 1
        # The actual live BEFORE has no authored CPU/FP/global substitution.
        # Only transport ownership, kind and sequence are changed for offline
        # replay. The original AFTER file is intentionally not read here.
        captured_raw = CAPTURED_BEFORE.read_bytes()
        ensure(hashlib.sha256(captured_raw).hexdigest() == CAPTURED_BEFORE_SHA, 'Pinned actual live BEFORE changed')
        captured = Request.from_buffer_copy(captured_raw)
        captured.sequence = sequence; sequence += 1; captured.kind = 1; captured.pid = os.getpid(); captured.tid = get_tid()
        replay = exchange(captured); verify_positive(captured, replay); positive += 1
        ensure(bytes(replay.fx[24:28]) == bytes(captured.fx[24:28]) == struct.pack('<I', 0x1FA0), 'Actual live MXCSR PE preserved without normalization')
        report.update(captured_before=str(CAPTURED_BEFORE), captured_before_sha256=CAPTURED_BEFORE_SHA,
                      captured_before_replayed=True, captured_before_substitutions=['sequence', 'kind=1', 'pipe-server pid', 'pipe-server tid'],
                      captured_after_used_as_input=False, admitted_mxcsr=['1f80', '1fa0'])
        # Each numerical denial must happen before a single guest memory event.
        cases = (
            ('unsupported-CW', lambda r: (word(r.fx, 0, 0x137F, 2), word(r.env, 0, 0xFFFF137F))),
            ('unsupported-MXCSR-1fa1', lambda r: word(r.fx, 24, 0x1FA1)),
            ('unsupported-MXCSR-1fc0', lambda r: word(r.fx, 24, 0x1FC0)),
            ('full-stack', lambda r: None),
            ('ENV-CW-mismatch', lambda r: word(r.env, 0, 0xFFFF077F)),
            ('ENV-SW-mismatch', lambda r: word(r.env, 4, 0xFFFF0002)),
            ('ENV-fulltag-mismatch', lambda r: word(r.env, 8, 0xFFFF0000)),
            ('nonelided-FX-metadata', lambda r: word(r.fx, 8, 0x12345678)),
            ('malformed-opcode-metadata', lambda r: word(r.env, 16, 0xFFFF0023)),
            ('provider-rebase', lambda r: setattr(r, 'provider_base', 0x780D0000)),
            ('operand-change', lambda r: setattr(r, 'provider_bits', 0x3F800000)),
            ('resolved-IAT-change', lambda r: setattr(r, 'iat_target', LEAF + 1)),
            ('unmeasured-live-raw80', lambda r: word(r.fx, 32, 0x8000000000000001, 8)),
        )
        for label, mutate in cases:
            r = input_request(sequence, depth=1); sequence += 1
            if label == 'full-stack': r.fx[4] = 0xFF; word(r.env, 8, 0xFFFF0000)
            else: mutate(r)
            a = exchange(r)
            ensure(a.status == 2 and not a.steps and not a.complete and bytes(a.fx) == bytes(r.fx)
                   and bytes(a.env) == bytes(r.env) and bytes(a.globals) == bytes(r.globals), f'Negative admitted or modified: {label}')
            rejected += 1
        r = input_request(sequence - 1); a = exchange(r)
        ensure(a.status == 2 and b'Nonsequential' in a.error and not a.steps, 'Sequence replay denial'); rejected += 1
        r = input_request(sequence); r.magic = b'WRONG001'; a = exchange(r)
        ensure(a.status == 2 and not a.steps, 'Request framing denial'); rejected += 1
        r = input_request(sequence); sequence += 1; verify_positive(r, exchange(r)); positive += 1
        if args.idle_check_seconds:
            ensure(60 < args.idle_check_seconds <= 300, 'Idle persistence test must exceed the prior60second deadline and remain bounded')
            time.sleep(args.idle_check_seconds)
            ensure(process.poll() is None, 'Persistent worker exited while pipe server was idle')
            r = input_request(sequence); sequence += 1; verify_positive(r, exchange(r)); positive += 1
            report['idle_seconds_then_successful_request'] = args.idle_check_seconds
        report.update(passed=True, positive_invocations=positive, rejected_requests=rejected, compiled_events=positive * 22,
                      compiled_routes=positive * 3, request_count=len(records), host_boundary='Private Session.invoke; canonical host FX512 plus separate ENV28 boundary unchanged',
                      canonical_ancestor_scope='Prior accepted gate applies to canonical ancestor; MXCSR1fa0 extension is separately prepared and tested')
    except Exception as exception:
        report['failure'] = str(exception); raise
    finally:
        close(pipe); close(event)
        if process is not None:
            try: report['worker_exit'] = process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); report['worker_exit'] = process.wait(timeout=10)
        stdout.close(); stderr.close()
        with open(output / 'wire.bin', 'wb') as stream:
            for r, a in records: stream.write(r); stream.write(a)
        report['wire_sha256'] = hashlib.sha256((output / 'wire.bin').read_bytes()).hexdigest()
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    ensure(report.get('worker_exit') == 0, 'Worker did not cleanly exit on server EOF')
    print(json.dumps(report))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for option in ('worker', 'game', 'provider', 'object', 'output'): parser.add_argument('--' + option, required=True)
    parser.add_argument('--idle-check-seconds', type=float, default=0)
    run(parser.parse_args())
