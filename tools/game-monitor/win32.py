"""Windows diagnostics backend. Reads health signals; does not operate the UI."""

import ctypes as c
from ctypes import wintypes as w
import os
import time

if os.name != "nt":
    raise RuntimeError("Live game monitoring requires Windows")

k = c.WinDLL("kernel32", use_last_error=True)
p = c.WinDLL("psapi", use_last_error=True)
u = c.WinDLL("user32", use_last_error=True)
PTR = c.c_void_p
UPTR = c.c_size_t


def api(dll, name, args, result=w.BOOL):
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


close_handle = api(k, "CloseHandle", [w.HANDLE])
open_process = api(k, "OpenProcess", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
wait_process = api(k, "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
exit_code = api(k, "GetExitCodeProcess", [w.HANDLE, c.POINTER(w.DWORD)])
query_path = api(k, "QueryFullProcessImageNameW", [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)])
process_times = api(k, "GetProcessTimes", [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4)
read_memory = api(k, "ReadProcessMemory", [w.HANDLE, PTR, PTR, UPTR, c.POINTER(UPTR)])
detach = api(k, "DebugActiveProcessStop", [w.DWORD])
attach_debug = api(k, "DebugActiveProcess", [w.DWORD])
kill_on_exit = api(k, "DebugSetProcessKillOnExit", [w.BOOL])
window_pid = api(u, "GetWindowThreadProcessId", [w.HWND, c.POINTER(w.DWORD)], w.DWORD)
is_hung = api(u, "IsHungAppWindow", [w.HWND])
ENUMPROC = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
enum_windows = api(u, "EnumWindows", [ENUMPROC, w.LPARAM])
final_path = api(k, "GetFinalPathNameByHandleW", [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD], w.DWORD)


class Memory(c.Structure):
    _fields_ = [("cb", w.DWORD), ("faults", w.DWORD)] + [(name, UPTR) for name in
        ("peak_working", "working", "quota_peak_paged", "quota_paged", "quota_peak_nonpaged",
         "quota_nonpaged", "pagefile", "peak_pagefile", "private")]


memory_info = api(p, "GetProcessMemoryInfo", [w.HANDLE, c.POINTER(Memory), w.DWORD])
enum_processes = api(p, "EnumProcesses", [c.POINTER(w.DWORD), w.DWORD, c.POINTER(w.DWORD)])


def pids_for_image(path):
    target = os.path.normcase(os.path.abspath(path))
    size = 4096
    while True:
        ids, count = (w.DWORD * size)(), w.DWORD()
        if not enum_processes(ids, c.sizeof(ids), c.byref(count)):
            raise error("EnumProcesses")
        if count.value < c.sizeof(ids):
            break
        size *= 2
        if size > 65536:
            raise RuntimeError("Process inventory exceeds bounded capacity")
    matches = []
    for pid in ids[:count.value // c.sizeof(w.DWORD)]:
        handle = open_process(0x1000, False, pid)
        if not handle:
            continue
        try:
            buffer, length = c.create_unicode_buffer(32768), w.DWORD(32768)
            if query_path(handle, 0, buffer, c.byref(length)) and os.path.normcase(os.path.abspath(buffer.value)) == target:
                matches.append(pid)
        finally:
            close_handle(handle)
    return matches


def error(operation):
    return OSError(c.get_last_error(), operation + ": " + c.FormatError(c.get_last_error()))


def ticks(value):
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


class Process:
    def __init__(self, pid):
        self.pid = pid
        self.handle = open_process(0x100000 | 0x400 | 0x10, False, pid)
        if not self.handle:
            raise error("OpenProcess")
        self.previous = None
        buffer, size = c.create_unicode_buffer(32768), w.DWORD(32768)
        if not query_path(self.handle, 0, buffer, c.byref(size)):
            self.close()
            raise error("QueryFullProcessImageName")
        self.path = buffer.value

    def alive(self):
        result = wait_process(self.handle, 0)
        if result == 0xFFFFFFFF:
            raise error("WaitForSingleObject")
        return result == 0x102

    def exit_code(self):
        code = w.DWORD()
        if not exit_code(self.handle, c.byref(code)):
            raise error("GetExitCodeProcess")
        return code.value

    def sample(self):
        times = [w.FILETIME() for _ in range(4)]
        if not process_times(self.handle, *(c.byref(value) for value in times)):
            raise error("GetProcessTimes")
        cpu = (ticks(times[2]) + ticks(times[3])) / 10_000_000
        now = time.monotonic()
        percent = None
        if self.previous:
            percent = round(100 * (cpu - self.previous[1]) / max(now - self.previous[0], .001), 2)
        self.previous = now, cpu
        memory = Memory()
        memory.cb = c.sizeof(memory)
        if not memory_info(self.handle, c.byref(memory), c.sizeof(memory)):
            raise error("GetProcessMemoryInfo")
        windows = []

        @ENUMPROC
        def callback(hwnd, _):
            pid = w.DWORD()
            window_pid(hwnd, c.byref(pid))
            if pid.value == self.pid:
                windows.append({"hwnd": int(hwnd), "os_not_responding": bool(is_hung(hwnd))})
            return True

        if not enum_windows(callback, 0):
            raise error("EnumWindows health query")
        return {"pid": self.pid, "creation_filetime": ticks(times[0]),
                "cpu_seconds": round(cpu, 4), "cpu_one_core_percent": percent,
                "working_set_bytes": memory.working, "private_bytes": memory.private,
                "windows": windows}

    def read(self, address, size):
        size = min(size, 65536)
        buffer, count = c.create_string_buffer(size), UPTR()
        if not read_memory(self.handle, address, buffer, size, c.byref(count)):
            raise error("ReadProcessMemory(debug string)")
        return buffer.raw[:count.value]

    def close(self):
        if self.handle:
            close_handle(self.handle)
            self.handle = None


class ExceptionRecord(c.Structure):
    _fields_ = [("code", w.DWORD), ("flags", w.DWORD), ("record", PTR), ("address", PTR),
                ("count", w.DWORD), ("information", UPTR * 15)]


class ExceptionInfo(c.Structure):
    _fields_ = [("record", ExceptionRecord), ("first_chance", w.DWORD)]


class CreateProcess(c.Structure):
    _fields_ = [("file", w.HANDLE), ("process", w.HANDLE), ("thread", w.HANDLE), ("base", PTR),
               ("debug_offset", w.DWORD), ("debug_size", w.DWORD), ("tls", PTR),
               ("start", PTR), ("name", PTR), ("unicode", w.WORD)]


class LoadDll(c.Structure):
    _fields_ = [("file", w.HANDLE), ("base", PTR), ("offset", w.DWORD),
               ("size", w.DWORD), ("name", PTR), ("unicode", w.WORD)]


class DebugString(c.Structure):
    _fields_ = [("data", PTR), ("unicode", w.WORD), ("length", w.WORD)]


class DebugUnion(c.Union):
    _fields_ = [("exception", ExceptionInfo), ("created", CreateProcess), ("dll", LoadDll),
               ("string", DebugString), ("exit", w.DWORD), ("unload", PTR)]


class DebugEvent(c.Structure):
    _fields_ = [("code", w.DWORD), ("pid", w.DWORD), ("tid", w.DWORD), ("info", DebugUnion)]


wait_debug = api(k, "WaitForDebugEventEx", [c.POINTER(DebugEvent), w.DWORD])
continue_debug = api(k, "ContinueDebugEvent", [w.DWORD, w.DWORD, w.DWORD])


def file_name(handle):
    if not handle:
        return None
    buffer = c.create_unicode_buffer(32768)
    count = final_path(handle, buffer, len(buffer), 0)
    return os.path.basename(buffer.value) if 0 < count < len(buffer) else None


class Debugger:
    def __init__(self, pid, attach=False):
        self.pid = pid
        self.initial_breakpoint = False
        self.wow64_breakpoint_seen = False
        self.exited = False
        if attach and not attach_debug(pid):
            raise error("DebugActiveProcess")
        if not kill_on_exit(False):
            failure = error("DebugSetProcessKillOnExit")
            if attach:
                detach(pid)
            raise failure

    def poll(self, process, emit):
        # Drain a bounded batch. Every event is continued even if logging fails.
        for _ in range(128):
            event = DebugEvent()
            if not wait_debug(c.byref(event), 0):
                if c.get_last_error() in (121, 258):
                    break
                raise error("WaitForDebugEventEx")
            status = 0x10002  # DBG_CONTINUE for notifications.
            try:
                if event.code == 1:
                    exc = event.info.exception
                    code = exc.record.code
                    initial = code == 0x80000003 and bool(exc.first_chance) and not self.initial_breakpoint
                    wow64_initial = code == 0x4000001f and bool(exc.first_chance) and not self.wow64_breakpoint_seen
                    if wow64_initial:
                        self.wow64_breakpoint_seen = True
                    if initial:
                        self.initial_breakpoint = True
                    else:
                        # Never swallow application exceptions, even first-chance ones.
                        status = 0x80010001  # DBG_EXCEPTION_NOT_HANDLED
                    level = "info" if initial or wow64_initial else ("warning" if exc.first_chance else "critical")
                    event_name = "loader_breakpoint" if initial else ("wow64_breakpoint" if wow64_initial else "exception")
                    emit("debugger", event_name, level,
                         pid=event.pid, tid=event.tid, code=f"0x{code:08X}",
                         address=hex(exc.record.address or 0), first_chance=bool(exc.first_chance),
                         parameters=list(exc.record.information)[:min(exc.record.count, 15)])
                elif event.code in (3, 6):
                    info = event.info.created if event.code == 3 else event.info.dll
                    try:
                        emit("debugger", "process_created" if event.code == 3 else "module_loaded",
                             pid=event.pid, tid=event.tid, base=hex(info.base or 0), module=file_name(info.file))
                    finally:
                        if info.file:
                            close_handle(info.file)
                elif event.code == 5:
                    self.exited = True
                    emit("debugger", "process_exit", "info" if event.info.exit == 0 else "error",
                         pid=event.pid, exit_code=event.info.exit, exit_hex=f"0x{event.info.exit:08X}")
                elif event.code == 8:
                    info = event.info.string
                    try:
                        # OUTPUT_DEBUG_STRING_INFO reports bytes for both formats.
                        raw = process.read(info.data, info.length)
                        text = raw.decode("utf-16-le" if info.unicode else "mbcs", errors="replace").split("\0", 1)[0]
                        from core import severity
                        emit("debugger", "debug_message", severity(text), pid=event.pid, tid=event.tid, text=text[:8192])
                    except OSError as failure:
                        emit("collector", "debug_string_unavailable", "warning", error=str(failure))
                elif event.code == 9:
                    emit("debugger", "rip_error", "error", pid=event.pid)
            finally:
                if not continue_debug(event.pid, event.tid, status):
                    raise error("ContinueDebugEvent")
            if self.exited:
                break

    def close(self):
        if not self.exited and not detach(self.pid):
            raise error("DebugActiveProcessStop")
