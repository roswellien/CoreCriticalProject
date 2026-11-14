"""Own a fresh Windows/x64 native build and stage a local observational payload.

Recipe v1 requires explicit existing tools, dependencies, clean tracked source
and fresh owned destinations. It runs authored tool-qualification probes and
builds only the native mw3 target. The payload is not installed or executed.
Observed pre/post identities do not authenticate the build or admit its consumers.
"""
from __future__ import annotations

import argparse
import ctypes
from contextlib import contextmanager
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import tempfile
import time

MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_CLOSURE_BYTES = 4 * 1024**3
MAX_MEMBERS = 20000
ENVIRONMENT_POLICY = "mw3-re-explicit-windows-native-bootstrap-v2"
_TOOL_NAMES = {"git": "git.exe", "cmake": "cmake.exe", "ninja": "ninja.exe",
               "clang_cl": "clang-cl.exe", "glslang": "glslangValidator.exe",
               "dxc": "dxc.exe", "dumpbin": "dumpbin.exe"}
_DIRECTORIES = ("source", "vs", "sdl3", "sdl3_ttf", "archive_prefix", "crt_root",
                "vulkan_headers", "ttf_notices")
_WINDOWS_KEYS = ("SystemRoot", "WINDIR", "SystemDrive", "COMSPEC", "ProgramFiles",
                 "ProgramFiles(x86)", "ProgramW6432", "ProgramData", "OS",
                 "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS")
_VS_KEYS = ("INCLUDE", "LIB", "LIBPATH", "VSINSTALLDIR", "VCINSTALLDIR", "VCToolsInstallDir",
            "VCToolsVersion", "VCIDEInstallDir", "VisualStudioVersion", "WindowsSdkDir",
            "WindowsSDKVersion", "WindowsSDKLibVersion", "WindowsSdkBinPath",
            "WindowsSdkVerBinPath", "UniversalCRTSdkDir", "UCRTVersion", "ExtensionSdkDir",
            "NETFXSDKDir", "VSCMD_ARG_HOST_ARCH", "VSCMD_ARG_TGT_ARCH", "VSCMD_VER")
_SEARCH_POLICY = {"CMAKE_FIND_USE_PACKAGE_REGISTRY": "FALSE",
                  "CMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY": "FALSE",
                  "CMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH": "FALSE",
                  "CMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH": "FALSE"}
_NATIVE_BOOTSTRAP_FILES = (
    'Common7/Tools/VsDevCmd.bat',
    'Common7/Tools/vsdevcmd/core/vsdevcmd_start.bat',
    'Common7/Tools/vsdevcmd/core/parse_cmd.bat',
    'Common7/Tools/vsdevcmd/core/dotnet.bat',
    'Common7/Tools/vsdevcmd/core/msbuild.bat',
    'Common7/Tools/vsdevcmd/core/winsdk.bat',
    'Common7/Tools/vsdevcmd/core/vsdevcmd_end.bat',
    'Common7/Tools/vsdevcmd/ext/vcvars.bat',
)
_NATIVE_BOOTSTRAP_PROFILES = (
    dict(name='vs17-native-x64-01',
         source_hashes=(
             'c004278e64444bf3524360f960511b5ce7b1d0306910f08a4ebcf1c42ff9bd6d',
             'da311beae7797632908b5a2e292ac00811e1373ab3108921ab1fe3ef2ec84466',
             '01aa909650dfcb166c0fd6352ccf550177b8e90cde140214f18d105061f9196b',
             'e9fcdd8a29629e2594a3d2ac34e03ca944aaf92f1e93aed003173a5466f262e2',
             '0a1cca60b353b2881ac1ed587c1323a7535e1bedda749c94247b9ef110efdf08',
             '66bbdb774bf79d538828efafb2099e2485a79c610beac775052d43f8c6bd752b',
             '4f85ee6d2b1b4dff009ea9681ffaf7a698a96e8dd4e4ca3c779b8884de1c7206',
             '136beb56e4c59f6f704ec5ccbc6e86ffc92d526f1f2996c79e48739f909696c6',
         ),
         metadata={
             'VC/Auxiliary/Build/Microsoft.VCToolsVersion.default.txt':
                 '030613df718548a88970e4c1844a8605d17aba9aa36bfea0b4359d8f28fd62bf',
             'VC/Auxiliary/Build/Microsoft.VCToolsVersion.v143.default.txt':
                 '030613df718548a88970e4c1844a8605d17aba9aa36bfea0b4359d8f28fd62bf',
             'VC/Auxiliary/Build/Microsoft.VCRedistVersion.default.txt':
                 'a57d05f36a0e13206231f97899d320819d02725273bc30d4c3197d529af63d91',
         },
         preferred_toolset='VC/Auxiliary/Build/Microsoft.VCToolsVersion.v143.default.txt',
         toolset='14.44.35207', redist='14.44.35112', crt='Microsoft.VC143.CRT'),
    dict(name='vs18-native-x64-01',
         source_hashes=(
             'a7815e85d636828e5cf70fe4235b11fcb41750896a4d2d60756b43bacaf4f0b2',
             '96a54921f33a23ca4be2db17f125baf09800a1885733e8e6efb1f6e43ccc43ba',
             '79d8abad15711f28985159dea103301392f49c3621320133257da1beeac0aa4f',
             'e9fcdd8a29629e2594a3d2ac34e03ca944aaf92f1e93aed003173a5466f262e2',
             '0a1cca60b353b2881ac1ed587c1323a7535e1bedda749c94247b9ef110efdf08',
             '66bbdb774bf79d538828efafb2099e2485a79c610beac775052d43f8c6bd752b',
             'a1f6367dacf1305200838c46ab51a8090cf122b6c5a15c93aee20a741f4ac295',
             '525c2879279791fb005b162b6dc42f9a78c59d07982864357bdcc284e65cfa24',
         ),
         metadata={
             'VC/Auxiliary/Build/Microsoft.VCToolsVersion.default.txt':
                 '2ca998516f8f18b39c28ce022abb90ef5ad711b468494671dd84b74618b569d9',
             'VC/Auxiliary/Build/Microsoft.VCToolsVersion.v145.default.txt':
                 '2ca998516f8f18b39c28ce022abb90ef5ad711b468494671dd84b74618b569d9',
             'VC/Auxiliary/Build/Microsoft.VCRedistVersion.default.txt':
                 '2ca998516f8f18b39c28ce022abb90ef5ad711b468494671dd84b74618b569d9',
         },
         preferred_toolset='VC/Auxiliary/Build/Microsoft.VCToolsVersion.v145.default.txt',
         toolset='14.51.36231', redist='14.51.36231', crt='Microsoft.VC145.CRT'),
)
_GENERATED = {"profile.json", "THIRD-PARTY.txt", "metadata/build-observation.json"}
_CRT = re.compile(r"(?:vcruntime|msvcp|concrt|vccorlib)", re.IGNORECASE)
_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


class _CommandFailed(ValueError):
    def __init__(self, output):
        super().__init__("Dependency inspection failed")
        self.output = bytes(output)


def _relative(value):
    if not isinstance(value, str) or not value or len(value) > 240 or "\\" in value:
        raise ValueError("Invalid staged member path")
    for part in value.split("/"):
        if (not part or part in (".", "..") or part.endswith((".", " "))
                or any(ord(character) < 32 or character in '<>:"|?*' for character in part)
                or re.fullmatch(r"CON(?:IN\$|OUT\$)?|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³]",
                                part.split(".")[0], re.IGNORECASE)):
            raise ValueError("Unsafe staged member path")
    return value


def _unlinked(path):
    path = Path(os.path.abspath(path))
    volume_root = re.match(r"\\\\\?\\Volume\{[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\}(?=\\|$)",
                           str(path), re.IGNORECASE)
    for ancestor in (path, *path.parents):
        is_volume_root = volume_root and str(ancestor).rstrip("\\").casefold() == volume_root[0].casefold()
        try:
            # A GUID volume without its trailing slash names the device, not its root directory.
            attributes = (os.stat(volume_root[0] + "\\", follow_symlinks=False)
                          if is_volume_root else ancestor.lstat())
        except FileNotFoundError:
            attributes = None
        if attributes is not None and (stat.S_ISLNK(attributes.st_mode)
                or getattr(attributes, "st_file_attributes", 0) & 0x400):
            raise ValueError("Staging input/output contains a link")
        # Python 3.11 lists the invalid namespace-only \\?\ parent above a GUID volume.
        # Check the real volume root itself, then stop before that non-filesystem parent.
        if is_volume_root:
            break
    return path


def _regular(path):
    path = _unlinked(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Staging requires a regular file")
    return path


def _directory(path):
    path = _unlinked(path)
    if not path.is_dir():
        raise ValueError("Staging requires an existing directory")
    return path


def _physical_location(path):
    """Resolve an existing ancestor by handle before appending any uncreated descendants."""
    from ctypes import wintypes as wt
    path = _unlinked(path)
    ancestor = path
    suffix = []
    while not ancestor.exists():
        if ancestor == ancestor.parent:
            raise ValueError("No existing physical ancestor for overlap preflight")
        suffix.append(ancestor.name)
        ancestor = ancestor.parent
    _unlinked(ancestor)
    class FileInformation(ctypes.Structure):
        _fields_ = [("attributes", wt.DWORD), ("creation", wt.FILETIME),
                    ("access", wt.FILETIME), ("write", wt.FILETIME),
                    ("volume", wt.DWORD), ("size_high", wt.DWORD), ("size_low", wt.DWORD),
                    ("links", wt.DWORD), ("index_high", wt.DWORD), ("index_low", wt.DWORD)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = (wt.LPCWSTR, wt.DWORD, wt.DWORD, wt.LPVOID, wt.DWORD, wt.DWORD, wt.HANDLE)
    kernel.CreateFileW.restype = wt.HANDLE
    kernel.GetFinalPathNameByHandleW.argtypes = (wt.HANDLE, wt.LPWSTR, wt.DWORD, wt.DWORD)
    kernel.GetFinalPathNameByHandleW.restype = wt.DWORD
    kernel.GetFileInformationByHandle.argtypes = (wt.HANDLE, ctypes.POINTER(FileInformation))
    kernel.CloseHandle.argtypes = (wt.HANDLE,)
    # Same handle-based final-name primitive as PackStorage.CanonicalFilePath.
    # Metadata access only; BACKUP_SEMANTICS admits directories, OPEN_REPARSE_POINT does not follow a replaced leaf.
    handle = kernel.CreateFileW(str(ancestor), 0x80, 7, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "Cannot open physical overlap ancestor")
    try:
        information = FileInformation()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(information)):
            raise OSError(ctypes.get_last_error(), "Cannot identify physical overlap ancestor")
        if information.attributes & 0x400:
            raise ValueError("Physical overlap ancestor contains a link")
        if suffix and not information.attributes & 0x10:
            raise ValueError("Uncreated destination has a non-directory ancestor")
        buffer = ctypes.create_unicode_buffer(32768)
        # FILE_NAME_NORMALIZED | VOLUME_NAME_GUID puts DOS and volume aliases in one namespace.
        count = kernel.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 1)
        if not 0 < count < len(buffer) or not buffer.value.lower().startswith("\\\\?\\volume{"):
            raise OSError(ctypes.get_last_error(), "Cannot normalize physical overlap ancestor")
        canonical = Path(buffer.value).joinpath(*reversed(suffix))
        file_index = (information.index_high << 32) | information.index_low
        identity = None if suffix else (information.volume, file_index)
        return canonical, identity
    finally:
        kernel.CloseHandle(handle)


def _paths_overlap(first, second):
    first_path, first_identity = _physical_location(first)
    second_path, second_identity = _physical_location(second)
    same_object = first_identity is not None and first_identity == second_identity
    return same_object or first_path.is_relative_to(second_path) or second_path.is_relative_to(first_path)


def _identity(path):
    observed = _regular(path).stat()
    return observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns


def file_hash(path):
    with _regular(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@dataclass(frozen=True)
class Member:
    relative: str
    source: Path
    bytes: int
    identity: tuple
    sha256: str = ""


@dataclass(frozen=True)
class Inventory:
    members: tuple[Member, ...]
    generated: tuple[tuple[str, bytes], ...]
    input_roots: tuple[Path, ...]
    source_commit: str
    builder: str
    build_id: str


def _budget(members, generated=()):
    sizes = [member.bytes for member in members] + [len(data) for _, data in generated]
    if (len(sizes) > MAX_MEMBERS or any(size <= 0 or size > MAX_CLOSURE_BYTES for size in sizes)
            or sum(sizes) > MAX_CLOSURE_BYTES):
        raise ValueError("Staging inventory exceeds its member or byte budget")


def _pe(path, *, library):
    """Check the narrow Windows/x64 image requirement, not a general PE validator."""
    with _regular(path).open("rb") as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            raise ValueError("Expected an x64 PE image")
        offset = struct.unpack_from("<I", dos, 60)[0]
        if not 64 <= offset <= 1024 * 1024:
            raise ValueError("Invalid PE header offset")
        stream.seek(offset)
        header = stream.read(26)
    if len(header) != 26 or header[:4] != b"PE\0\0":
        raise ValueError("Invalid PE header")
    machine = struct.unpack_from("<H", header, 4)[0]
    flags = struct.unpack_from("<H", header, 22)[0]
    magic = struct.unpack_from("<H", header, 24)[0]
    if machine != 0x8664 or magic != 0x20b or not flags & 2 or bool(flags & 0x2000) != library:
        raise ValueError("Expected an x64 executable or application DLL")


def _parse_dependents(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if (len(lines) < 5 or not lines[0].startswith("Dump of file ")
            or lines[1] not in ("File Type: EXECUTABLE IMAGE", "File Type: DLL") or "Summary" not in lines):
        raise ValueError("Unrecognized dependency inspection output")
    imports = []
    headings = set()
    for line in lines[2:lines.index("Summary")]:
        if line in ("Image has the following dependencies:",
                    "Image has the following delay load dependencies:"):
            if line in headings:
                raise ValueError("Repeated dependency inspection section")
            headings.add(line)
            continue
        if not headings or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,235}\.dll", line, re.IGNORECASE):
            raise ValueError("Malformed dependency inspection entry")
        _relative(line)
        if line.casefold() in {name.casefold() for name in imports}:
            raise ValueError("Repeated dependency inspection entry")
        imports.append(line)
    if not headings or not imports:
        raise ValueError("Missing dependency inspection section")
    return imports


def _resume_owned_child(child, kernel):
    from ctypes import wintypes as wt
    class ThreadEntry(ctypes.Structure):
        _fields_ = [(name, wt.DWORD) for name in
                    ("size", "usage", "thread", "owner", "base_priority", "delta_priority", "flags")]
    kernel.CreateToolhelp32Snapshot.argtypes = (wt.DWORD, wt.DWORD)
    kernel.CreateToolhelp32Snapshot.restype = wt.HANDLE
    kernel.Thread32First.argtypes = kernel.Thread32Next.argtypes = (wt.HANDLE, ctypes.POINTER(ThreadEntry))
    kernel.OpenThread.argtypes = (wt.DWORD, wt.BOOL, wt.DWORD)
    kernel.OpenThread.restype = wt.HANDLE
    kernel.ResumeThread.argtypes = (wt.HANDLE,)
    kernel.ResumeThread.restype = wt.DWORD
    snapshot = kernel.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
    if snapshot == ctypes.c_void_p(-1).value:
        raise OSError("Cannot inspect the owned suspended child thread")
    try:
        entry = ThreadEntry()
        entry.size = ctypes.sizeof(entry)
        found = []
        more = kernel.Thread32First(snapshot, ctypes.byref(entry))
        while more:
            if entry.owner == child.pid:
                found.append(entry.thread)
            more = kernel.Thread32Next(snapshot, ctypes.byref(entry))
        if len(found) != 1:
            raise ValueError("Unexpected owned suspended child thread state")
        thread = kernel.OpenThread(2, False, found[0])  # THREAD_SUSPEND_RESUME
        if not thread:
            raise OSError("Cannot open the owned suspended child thread")
        try:
            if kernel.ResumeThread(thread) != 1:
                raise OSError("Cannot resume the owned child")
        finally:
            kernel.CloseHandle(thread)
    finally:
        kernel.CloseHandle(snapshot)


def _assign_child_job(child, kernel):
    from ctypes import wintypes as wt
    class BasicLimits(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                    ("flags", wt.DWORD), ("minimum_working_set", ctypes.c_size_t),
                    ("maximum_working_set", ctypes.c_size_t), ("active_processes", wt.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wt.DWORD), ("scheduling", wt.DWORD)]
    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("basic", BasicLimits), ("io", ctypes.c_uint64 * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]
    kernel.CloseHandle.argtypes = (wt.HANDLE,)
    kernel.CreateJobObjectW.argtypes = (wt.LPVOID, wt.LPCWSTR)
    kernel.CreateJobObjectW.restype = wt.HANDLE
    kernel.SetInformationJobObject.argtypes = (wt.HANDLE, ctypes.c_int, wt.LPVOID, wt.DWORD)
    kernel.AssignProcessToJobObject.argtypes = (wt.HANDLE, wt.HANDLE)
    kernel.OpenProcess.argtypes = (wt.DWORD, wt.BOOL, wt.DWORD)
    kernel.OpenProcess.restype = wt.HANDLE
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise OSError("Cannot create an owned child job")
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise OSError("Cannot configure the owned child job")
        process = kernel.OpenProcess(0x0101, False, child.pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise OSError("Cannot open the owned child")
        try:
            if not kernel.AssignProcessToJobObject(job, process):
                raise OSError("Cannot assign the owned child job")
        finally:
            kernel.CloseHandle(process)
        _resume_owned_child(child, kernel)
        return job
    except BaseException:
        kernel.CloseHandle(job)
        raise


def _finish_child_job(child, job, kernel):
    from ctypes import wintypes as wt
    class Accounting(ctypes.Structure):
        _fields_ = [(name, ctypes.c_int64) for name in
                    ("user_time", "kernel_time", "period_user_time", "period_kernel_time")]
        _fields_ += [(name, wt.DWORD) for name in
                     ("page_faults", "total_processes", "active_processes", "terminated_processes")]
    kernel.QueryInformationJobObject.argtypes = (wt.HANDLE, ctypes.c_int, wt.LPVOID, wt.DWORD, wt.LPDWORD)
    kernel.TerminateJobObject.argtypes = (wt.HANDLE, wt.UINT)
    accounting = Accounting()
    def query():
        if not kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
            raise OSError("Cannot establish the owned child job exit state")
        return accounting.active_processes
    deadline = time.monotonic() + 5
    if query() and not kernel.TerminateJobObject(job, 1):
        raise OSError("Cannot terminate the remaining owned child job")
    # Closing a kill-on-close Job initiates asynchronous termination. Keep it queryable
    # until every owned descendant has left; waiting only for the direct child is insufficient.
    while query():
        if time.monotonic() >= deadline:
            raise OSError("Owned child job did not reach zero active processes")
        time.sleep(.005)
    child.wait(timeout=max(.001, deadline - time.monotonic()))
    return dict(active_processes=accounting.active_processes,
                total_processes=accounting.total_processes,
                terminated_processes=accounting.terminated_processes)


def _capture_inspection(command, environment, directory, timeout=30):
    if os.name != "nt":
        raise ValueError("Dependency inspection requires Windows")
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    peek = kernel.PeekNamedPipe
    peek.argtypes = (wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                     wintypes.LPDWORD, wintypes.LPDWORD, wintypes.LPDWORD)
    peek.restype = wintypes.BOOL
    deadline = time.monotonic() + timeout
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, env=environment, cwd=directory,
                             bufsize=0, creationflags=subprocess.CREATE_NO_WINDOW | 4)  # CREATE_SUSPENDED
    data = bytearray()
    job = None
    try:
        # Assign before resuming: compiler/build grandchildren inherit only this owned job.
        job = _assign_child_job(child, kernel)
        handle = msvcrt.get_osfhandle(child.stdout.fileno())
        available = wintypes.DWORD()
        while True:
            if time.monotonic() >= deadline:
                raise ValueError("Dependency inspection timed out")
            # Peek avoids a blocking read: this single consumer reads only bytes already in the pipe.
            # stderr shares the same bounded pipe, so neither a second buffer nor a reader thread is needed.
            if not peek(handle, None, 0, None, ctypes.byref(available), None):
                error = ctypes.get_last_error()
                if error in (109, 232):  # Broken pipe / no data: all writers closed.
                    break
                raise OSError(error, "Cannot read dependency inspection pipe")
            if available.value:
                count = min(65536, available.value, MAX_METADATA_BYTES + 1 - len(data))
                block = child.stdout.read(count)
                if not block:
                    break
                data.extend(block)
                if len(data) > MAX_METADATA_BYTES:
                    raise ValueError("Excessive dependency inspection output")
            elif child.poll() is not None:
                break
            else:
                time.sleep(.01)
        try:
            returncode = child.wait(timeout=max(.001, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise ValueError("Dependency inspection timed out") from None
        if returncode != 0:
            raise _CommandFailed(data)
    finally:
        try:
            if job is not None:
                _finish_child_job(child, job, kernel)
            else:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=5)
        finally:
            child.stdout.close()
            if child.poll() is not None:
                # CPython's Windows Handle remains referenced by exception tracebacks.
                child._handle.Close()
            if job is not None:
                kernel.CloseHandle(job)
    return data


def _inspect(path, dumpbin, environment):
    data = _capture_inspection([str(dumpbin), "/nologo", "/dependents", str(path)],
                               environment, dumpbin.parent)
    try:
        return _parse_dependents(data.decode("utf-8", errors="strict"))
    except UnicodeDecodeError:
        raise ValueError("Unsupported dependency inspection output encoding") from None


def _system32():
    if os.name != "nt":
        raise ValueError("Native staging requires Windows")
    buffer = ctypes.create_unicode_buffer(32768)
    count = ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
    if not 0 < count < len(buffer):
        raise ValueError("Cannot locate the Windows system directory")
    return _directory(buffer.value)


def _dll(name, roots):
    matches = [entry for root in roots for entry in root.iterdir() if entry.name.casefold() == name.casefold()]
    if len(matches) > 1:
        raise ValueError("Ambiguous application dependency")
    return _regular(matches[0]) if matches else None


def _json(value):
    encoded = (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_METADATA_BYTES:
        raise ValueError("Staging metadata exceeds its budget")
    return encoded


def _metadata(members, components, source_commit, builder, tool_hash, observation=None):
    profile = _json(dict(schema_version=1, engine="mw3-re", purpose="planning-defaults", options=dict(
        renderer="vulkan-wsi", width=1280, height=720, aa="fxaa", af=16,
        window_mode="windowed", render_thread=True, lighting="off")))
    index = "\n".join(
        f'{item["name"]} {item["version"]}; source {item["source"]}; notices {", ".join(item["notices"])}'
        for item in components).encode("utf-8") + b"\n"
    if len(index) > MAX_METADATA_BYTES:
        raise ValueError("Staging notice index exceeds its budget")
    artifacts = {member.relative: dict(bytes=member.bytes, sha256=member.sha256) for member in members}
    for relative, data in (("profile.json", profile), ("THIRD-PARTY.txt", index)):
        artifacts[relative] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    build_id = "observed-" + hashlib.sha256(_json(artifacts)).hexdigest()
    witness_data = dict(kind="local-build-staging-observation-v1",
        assurance="observational-only-not-authenticated", source_commit=source_commit,
        builder=builder, build_id=build_id, artifacts=artifacts, components=components,
        inspection=dict(tool="dumpbin.exe", sha256=tool_hash),
        external_prerequisites=["Windows x64", "Vulkan loader and driver"])
    if observation is not None:
        build_id = "mw3-re-" + artifacts["bin/mw3.exe"]["sha256"]
        witness_data.update(schema_version=1, kind="mw3-re-local-observation",
                            assurance="observational-prepost-only", build_id=build_id,
                            observation=observation)
    witness = _json(witness_data)
    return (("profile.json", profile), ("THIRD-PARTY.txt", index),
            ("metadata/build-observation.json", witness)), build_id


def _pins(members, generated):
    pins = {member.relative: dict(bytes=member.bytes, sha256=member.sha256) for member in members}
    for relative, data in generated:
        pins[relative] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return pins


def _descriptor(pins, source_commit, builder, build_id):
    roles = dict(executable="bin/mw3.exe", profile="profile.json")
    return _json(dict(schema_version=2, engine="mw3-re", roles=roles,
        dependencies=sorted(set(pins) - set(roles.values())), files=pins, capabilities={},
        provenance=dict(source_commit=source_commit, build_id=build_id, builder=builder)))


def make_inventory(*, executable, release_roots, crt_root, dumpbin, notices, components,
                   source_commit, builder, environment, observation=None):
    """Plan a bounded closure from explicit selected inputs; do not create or copy payloads."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit) or not _ID.fullmatch(builder) or builder.endswith("."):
        raise ValueError("Invalid observational source or builder identity")
    executable = _regular(executable)
    roots = tuple(_directory(root) for root in release_roots)
    crt_root = _directory(crt_root)
    dumpbin = _regular(dumpbin)
    if not roots or len(roots) > 16 or len(set(roots)) != len(roots) or dumpbin.name.lower() != "dumpbin.exe":
        raise ValueError("Invalid selected dependency or inspection roots")
    if not isinstance(environment, dict) or environment.get("NoDefaultCurrentDirectoryInExePath") != "1":
        raise ValueError("Inspection requires an explicit guarded child environment")
    if not isinstance(notices, dict) or not notices or "LICENSE.txt" not in notices:
        raise ValueError("Missing required project notice")
    if not isinstance(components, list) or not 1 <= len(components) <= 64:
        raise ValueError("Invalid component notice inventory")
    covered = set()
    for item in components:
        if not isinstance(item, dict) or set(item) != {"name", "version", "source", "notices"}:
            raise ValueError("Invalid component identity")
        for field in ("name", "version", "source"):
            value = item[field]
            if not isinstance(value, str) or not 1 <= len(value) <= 256 or any(ord(c) < 32 for c in value):
                raise ValueError("Invalid component identity")
        if not isinstance(item["notices"], list) or not 1 <= len(item["notices"]) <= 64:
            raise ValueError("Missing component notices")
        for name in item["notices"]:
            if _relative(name) not in notices:
                raise ValueError("Missing component notice")
            covered.add(name)
    if covered != set(notices):
        raise ValueError("Notice inventory does not match its component index")
    reserved = {name.casefold() for name in _GENERATED | {"runtime.json", ".incomplete", ".runtime.json.pending"}}
    members = []
    def add(source, relative):
        _relative(relative)
        if relative.casefold() in reserved:
            raise ValueError("Staging member alias or reserved path")
        for member in members:
            names = relative.casefold(), member.relative.casefold()
            if names[0].startswith(names[1] + "/") or names[1].startswith(names[0] + "/"):
                raise ValueError("Staging member file/directory alias")
        reserved.add(relative.casefold())
        source = _regular(source)
        observed = _identity(source)
        members.append(Member(relative, source, observed[2], observed))
        _budget(members)
    add(executable, "bin/mw3.exe")
    for relative, source in notices.items():
        if relative != "LICENSE.txt" and not relative.startswith("licenses/"):
            raise ValueError("Invalid staged notice location")
        add(source, relative)
    system32 = _system32()
    pending = [executable]
    visited = set()
    tool_identity = _identity(dumpbin)
    tool_hash = file_hash(dumpbin)
    while pending:
        image = pending.pop()
        if image in visited:
            continue
        visited.add(image)
        _pe(image, library=image != executable)
        for name in _inspect(image, dumpbin, environment):
            lowered = name.lower()
            if re.fullmatch(r"(?:api|ext)-ms-win-[a-z0-9-]+\.dll", lowered):
                continue
            if re.match(r"(?:vcruntime|msvcp|concrt|vccorlib).*d\.dll$", lowered) or lowered in ("sdl3d.dll", "sdl3_ttfd.dll"):
                raise ValueError("Debug runtime dependencies are not Release payloads")
            crt = _CRT.match(name) is not None
            dependency = _dll(name, (crt_root,) if crt else roots)
            if dependency is None:
                if crt:
                    raise ValueError("Missing app-local CRT dependency")
                if _dll(name, (system32,)) is not None:
                    continue
                raise ValueError("Missing application dependency")
            relative = "bin/" + dependency.name
            if relative.casefold() not in {member.relative.casefold() for member in members}:
                add(dependency, relative)
                pending.append(dependency)
    if _identity(dumpbin) != tool_identity or file_hash(dumpbin) != tool_hash:
        raise ValueError("Selected inspection tool changed")
    placeholder = [replace(member, sha256="0" * 64) for member in members]
    generated, provisional_id = _metadata(placeholder, components, source_commit, builder, tool_hash, observation)
    _budget(members, generated)
    _descriptor(_pins(placeholder, generated), source_commit, builder, provisional_id)
    pinned = []
    for member in members:
        digest = file_hash(member.source)
        if _identity(member.source) != member.identity:
            raise ValueError("Source changed during inventory")
        pinned.append(replace(member, sha256=digest))
    generated, build_id = _metadata(pinned, components, source_commit, builder, tool_hash, observation)
    _budget(pinned, generated)
    return Inventory(tuple(pinned), generated, (*roots, crt_root), source_commit, builder, build_id)


def _copy_member(member, destination):
    if _identity(member.source) != member.identity or file_hash(member.source) != member.sha256:
        raise ValueError("Source changed before copying")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _unlinked(destination)
    with member.source.open("rb") as source, destination.open("xb") as target:
        count = 0
        while count <= member.bytes:
            data = source.read(min(65536, member.bytes + 1 - count))
            if not data:
                break
            count += len(data)
            if count > member.bytes:
                raise ValueError("Source changed while copying")
            target.write(data)
    if count != member.bytes or _identity(member.source) != member.identity or file_hash(member.source) != member.sha256:
        raise ValueError("Source changed while copying")


def _physical(root):
    result = set()
    for directory, folders, files in os.walk(root, followlinks=False):
        _directory(directory)
        for name in folders:
            _directory(Path(directory) / name)
        for name in files:
            path = _regular(Path(directory) / name)
            result.add(path.relative_to(root).as_posix())
    return result


def stage_inventory(inventory, output):
    """Copy only an admitted inventory into a new owned directory, then publish its descriptor."""
    output = _unlinked(output)
    if output.exists():
        raise ValueError("Staging output already exists")
    for source in (*inventory.input_roots, *(member.source for member in inventory.members)):
        if _paths_overlap(output, source):
            raise ValueError("Staging output overlaps an input")
    _budget(inventory.members, inventory.generated)
    output.mkdir(parents=True, exist_ok=False)
    incomplete = output / ".incomplete"
    incomplete.write_text("Incomplete local staging attempt. Not an installed or admitted runtime.\n", encoding="utf-8")
    try:
        pins = {}
        for member in inventory.members:
            destination = output / member.relative
            _copy_member(member, destination)
            if destination.stat().st_size != member.bytes or file_hash(destination) != member.sha256:
                raise ValueError("Destination does not match the independently observed source pin")
            pins[member.relative] = dict(bytes=member.bytes, sha256=member.sha256)
        for relative, data in inventory.generated:
            destination = _unlinked(output / relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(data)
            pins[relative] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        descriptor = _descriptor(pins, inventory.source_commit, inventory.builder, inventory.build_id)
        if _physical(output) != set(pins) | {".incomplete"}:
            raise ValueError("Final physical inventory differs from the planned closure")
        # Recheck the exact bytes and sources immediately before the completion marker.
        for relative, pin in pins.items():
            path = output / relative
            if path.stat().st_size != pin["bytes"] or file_hash(path) != pin["sha256"]:
                raise ValueError("Destination changed before completion")
        for member in inventory.members:
            if _identity(member.source) != member.identity or file_hash(member.source) != member.sha256:
                raise ValueError("Source changed before completion")
        pending = output / ".runtime.json.pending"
        with pending.open("xb") as stream:
            stream.write(descriptor)
        if _physical(output) != set(pins) | {".incomplete", pending.name}:
            raise ValueError("Final physical inventory changed before completion")
        incomplete.unlink()
        pending.replace(output / "runtime.json")
    except BaseException:
        if not (output / "runtime.json").exists() and not incomplete.exists():
            incomplete.write_text("Incomplete local staging attempt.\n", encoding="utf-8")
        raise


def _run(command, environment, directory, *, timeout=30, log=None):
    try:
        data = _capture_inspection([str(argument) for argument in command], environment, directory, timeout)
    except _CommandFailed as error:
        if log is not None:
            Path(log).write_bytes(error.output)
        raise ValueError("Selected external tool failed; see the private bounded diagnostic.") from None
    if log is not None:
        Path(log).write_bytes(data)
    return bytes(data)


def _small_text(path):
    with _regular(path).open("rb") as stream:
        data = stream.read(MAX_METADATA_BYTES + 1)
    if len(data) > MAX_METADATA_BYTES:
        raise ValueError("Input metadata exceeds its budget")
    try:
        return data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("Unsupported input metadata encoding") from None


def _path_argument(value):
    if (not isinstance(value, str) or not Path(value).is_absolute()
            or any(character in value for character in '\0\r\n;"')):
        raise ValueError("CLI paths must be explicit absolute single paths")
    return _unlinked(value)


def _bootstrap_base(scratch, parent=None):
    """Allow only named Windows basics; never copy a caller environment wholesale."""
    parent = os.environ if parent is None else parent
    observed_names = {name.upper(): name for name in parent}
    result = {name: parent[observed_names[name.upper()]] for name in _WINDOWS_KEYS if name.upper() in observed_names}
    if not all(result.get(name) for name in ("SystemRoot", "WINDIR", "COMSPEC", "ProgramFiles(x86)")):
        raise ValueError("Missing required Windows bootstrap paths")
    windows = _directory(result["SystemRoot"])
    if (windows != _system32().parent or _directory(result["WINDIR"]) != windows
            or _regular(result["COMSPEC"]) != windows / "System32/cmd.exe"):
        raise ValueError("Unexpected Windows bootstrap paths")
    system = tuple(_directory(path) for path in
                   (windows / "System32", windows, windows / "System32/Wbem",
                    windows / "System32/WindowsPowerShell/v1.0"))
    scratch = _directory(scratch)
    result.update(TEMP=str(scratch), TMP=str(scratch), PATH=";".join(map(str, system)))
    result["NoDefaultCurrentDirectoryInExePath"] = "1"
    result["VSCMD_SKIP_SENDTELEMETRY"] = "1"
    return result, system


def _native_bootstrap_inputs(vs):
    """Admit only the reviewed native core/VC source and exact selected metadata."""
    vs = _directory(vs)
    if any(character in str(vs) for character in '\0\r\n"&|<>^%!'):
        raise ValueError("Unsafe native bootstrap path")
    remaining = MAX_METADATA_BYTES
    members = {}
    digests = {}
    contents = {}

    def acquire(relative):
        nonlocal remaining
        path = _regular(vs / relative)
        before = _identity(path)
        if not 0 < before[2] <= remaining:
            raise ValueError("Native bootstrap inputs exceed their byte budget")
        with path.open("rb") as stream:
            data = stream.read(before[2] + 1)
        if len(data) != before[2] or _identity(path) != before:
            raise ValueError("Native bootstrap input changed during acquisition")
        remaining -= len(data)
        members[relative] = path
        digests[relative] = hashlib.sha256(data).hexdigest()
        contents[relative] = data

    for relative in _NATIVE_BOOTSTRAP_FILES:
        acquire(relative)
    vector = tuple(digests[relative] for relative in _NATIVE_BOOTSTRAP_FILES)
    profile = next((item for item in _NATIVE_BOOTSTRAP_PROFILES
                    if item["source_hashes"] == vector), None)
    if profile is None:
        raise ValueError("Unsupported native bootstrap source profile")
    for relative, expected in profile["metadata"].items():
        acquire(relative)
        if digests[relative] != expected:
            raise ValueError("Unsupported native bootstrap metadata")
        try:
            value = contents[relative].decode("ascii").strip()
        except UnicodeDecodeError:
            raise ValueError("Unsupported native bootstrap metadata") from None
        version = profile["redist"] if "RedistVersion" in relative else profile["toolset"]
        if not re.fullmatch(r"14\.[1-9][0-9]*\.[0-9]+", value) or value != version:
            raise ValueError("Unsupported native bootstrap metadata")
    return profile["name"], members


def _native_bootstrap_selection(vs):
    name, _ = _native_bootstrap_inputs(vs)
    return next(profile for profile in _NATIVE_BOOTSTRAP_PROFILES if profile["name"] == name)


def _validate_native_crt(vs, crt, profile):
    expected = vs / "VC/Redist/MSVC" / profile["redist"] / "x64" / profile["crt"]
    if crt != expected:
        raise ValueError("Selected CRT differs from the admitted redist version")


def _native_bootstrap(vs, environment, scratch, *, expected_profile=None):
    """Run one admitted native-only initialization, collecting its environment privately."""
    profile, members = _native_bootstrap_inputs(vs)
    if expected_profile is not None and profile != expected_profile:
        raise ValueError("Native bootstrap profile changed before wrapper creation")
    identities = {name: _identity(path) for name, path in members.items()}
    scratch = _directory(scratch)
    if any(character in str(scratch) for character in '\0\r\n"&|<>^%!'):
        raise ValueError("Unsafe native bootstrap scratch path")
    if (environment.get("VSCMD_SKIP_SENDTELEMETRY") != "1"
            or environment.get("NoDefaultCurrentDirectoryInExePath") != "1"):
        raise ValueError("Missing fixed native bootstrap controls")
    directory = Path(tempfile.mkdtemp(prefix="mw34-vs-native-", dir=scratch))
    wrapper = directory / "native.cmd"
    phase = directory / "phase.txt"
    core = members["Common7/Tools/VsDevCmd.bat"]
    vc = members["Common7/Tools/vsdevcmd/ext/vcvars.bat"]
    script = ("@echo off\r\nsetlocal DisableDelayedExpansion\r\n"
              f'> "{phase}" echo core\r\n'
              f'call "{core}" -no_ext -no_logo -arch=x64 -host_arch=x64 -startdir=none >nul\r\n'
              'if errorlevel 1 exit /b 1\r\n'
              'if /i not "%VSCMD_ARG_HOST_ARCH%"=="x64" exit /b 1\r\n'
              'if /i not "%VSCMD_ARG_TGT_ARCH%"=="x64" exit /b 1\r\n'
              'if /i not "%VSCMD_ARG_APP_PLAT%"=="Desktop" exit /b 1\r\n'
              'if not "%VSCMD_ARG_NO_EXT%"=="1" exit /b 1\r\n'
              'if defined __VSCMD_INTERNAL_INIT_STATE exit /b 1\r\n'
              f'> "{phase}" echo vc\r\ncall "{vc}" >nul\r\n'
              'if errorlevel 1 exit /b 1\r\n'
              'if not defined __VSCMD_VCVARS_INCLUDE exit /b 1\r\n'
              'if not defined INCLUDE exit /b 1\r\n'
              'set "INCLUDE=%__VSCMD_VCVARS_INCLUDE%%INCLUDE%"\r\n'
              'set "EXTERNAL_INCLUDE=%__VSCMD_VCVARS_INCLUDE%%EXTERNAL_INCLUDE%"\r\n'
              'set "__VSCMD_VCVARS_INCLUDE="\r\n'
              f'> "{phase}" echo collect\r\nset\r\nexit /b 0\r\n')
    try:
        encoded = script.encode("mbcs", errors="strict")
    except UnicodeError:
        directory.rmdir()
        raise ValueError("Unsupported native bootstrap path encoding") from None
    if len(encoded) > 64 * 1024:
        directory.rmdir()
        raise ValueError("Native bootstrap wrapper exceeds its byte budget")

    def phase_name():
        try:
            with _regular(phase).open("rb") as stream:
                value = stream.read(65)
            return (value.strip().decode("ascii")
                    if len(value) <= 64 and value.strip() in (b"core", b"vc", b"collect") else "unknown")
        except (OSError, ValueError):
            return "unknown"

    exited = True
    try:
        with wrapper.open("xb") as stream:
            stream.write(encoded)
        command = subprocess.list2cmdline([environment["COMSPEC"]]) + f' /d /s /c ""{wrapper}""'
        exited = False
        try:
            raw = bytes(_capture_inspection(command, environment, directory, timeout=30))
            exited = True
        except ValueError as error:
            # A ValueError reaches here only after the capture's verified Job cleanup.
            exited = True
            kind = "timed out" if str(error) == "Dependency inspection timed out" else "failed"
            raise ValueError("Selected VS native bootstrap " + kind + " at phase " + phase_name()) from None
        except (OSError, subprocess.SubprocessError):
            # Preserve owned scratch if exit/cleanup could not be established.
            raise ValueError("Selected VS native bootstrap failed at phase " + phase_name()) from None
        if phase_name() != "collect":
            raise ValueError("Selected VS native bootstrap failed at phase " + phase_name())
        after_profile, after_members = _native_bootstrap_inputs(vs)
        if (profile != after_profile or members != after_members
                or identities != {name: _identity(path) for name, path in after_members.items()}):
            raise ValueError("Native bootstrap inputs changed across initialization")
        return raw
    finally:
        if exited:
            _unlinked(directory)
            wrapper.unlink(missing_ok=True)
            phase.unlink(missing_ok=True)
            directory.rmdir()


def build_environment(vs, tools, scratch, *, source=None, parent=None, bootstrap_profile=None):
    """Construct the sole native child environment from admitted native-only VS x64 inputs."""
    vs = _directory(vs)
    profile = _native_bootstrap_selection(vs)
    if bootstrap_profile is not None and profile["name"] != bootstrap_profile:
        raise ValueError("Native bootstrap profile changed before initialization")
    base, system = _bootstrap_base(scratch, parent)
    # Never log, pin or return the complete collected environment.
    raw = _native_bootstrap(vs, base, _directory(scratch), expected_profile=profile["name"])
    try:
        collected = dict(line.split("=", 1) for line in raw.decode("mbcs").splitlines()
                         if "=" in line and not line.startswith("="))
    except UnicodeDecodeError:
        raise ValueError("Unsupported VS bootstrap output") from None
    folded = {key.upper(): value for key, value in collected.items()}
    selected = {key: folded[key.upper()] for key in _VS_KEYS if key.upper() in folded}
    required = ("INCLUDE", "LIB", "LIBPATH", "VSINSTALLDIR", "VCINSTALLDIR", "VCToolsInstallDir",
                "WindowsSdkDir", "WindowsSdkVerBinPath")
    if (any(not selected.get(key) for key in required)
            or selected.get("VSCMD_ARG_HOST_ARCH") != "x64" or selected.get("VSCMD_ARG_TGT_ARCH") != "x64"):
        raise ValueError("Incomplete or non-x64 selected VS bootstrap")
    if _directory(selected["VSINSTALLDIR"]) != vs:
        raise ValueError("VS bootstrap selected another installation")
    vc = _directory(selected["VCToolsInstallDir"])
    if (selected.get("VCToolsVersion") != profile["toolset"]
            or vc != vs / "VC/Tools/MSVC" / profile["toolset"]):
        raise ValueError("VS bootstrap selected a different admitted toolset version")
    if not vc.is_relative_to(vs / "VC/Tools/MSVC") or _directory(selected["VCINSTALLDIR"]) != vs / "VC":
        raise ValueError("Unexpected selected VS compiler origin")
    kits = _directory(Path(base["ProgramFiles(x86)"]) / "Windows Kits")
    sdk = _directory(selected["WindowsSdkDir"])
    sdk_bin = _directory(Path(selected["WindowsSdkVerBinPath"]) / "x64")
    if not sdk.is_relative_to(kits) or not sdk_bin.is_relative_to(sdk):
        raise ValueError("Unexpected selected Windows SDK origin")
    for key in ("INCLUDE", "LIB", "LIBPATH"):
        for value in selected[key].split(";"):
            path = _directory(value)
            if not any(path.is_relative_to(root) for root in (vs, kits, system[1])):
                raise ValueError("VS search paths leave the selected tool/SDK roots")
    derived = {"linker": _regular(vc / "bin/Hostx64/x64/link.exe"),
               "ar": _regular(vc / "bin/Hostx64/x64/lib.exe"),
               "rc": _regular(sdk_bin / "rc.exe"), "mt": _regular(sdk_bin / "mt.exe")}
    if _regular(tools["dumpbin"]) != vc / "bin/Hostx64/x64/dumpbin.exe":
        raise ValueError("Inspection tool does not match the selected VS x64 toolset")
    parents = [Path(tools[name]).parent for name in _TOOL_NAMES if name in tools]
    parents += [derived["linker"].parent, sdk_bin, *system]
    search = []
    for directory in parents:
        directory = _directory(directory)
        if source is not None and directory == Path(source):
            raise ValueError("Source directory cannot be a tool search path")
        if directory not in search:
            search.append(directory)
    environment = dict(base, **selected)
    environment["PATH"] = ";".join(map(str, search))
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="NUL", GIT_OPTIONAL_LOCKS="0")
    environment["NoDefaultCurrentDirectoryInExePath"] = "1"
    return environment, derived, (vs, kits, system[1])


def _source_identity(source, git, environment, expected_commit, *, require_clean=True):
    def query(*arguments):
        return _run([git, "-C", source, *arguments], environment, source).decode("utf-8").strip()
    if Path(query("rev-parse", "--show-toplevel")) != source:
        raise ValueError("Source is not the selected consolidated repository root")
    for member in ("CMakeLists.txt", "AGENTS.md", "runtime/mw3-re/CMakeLists.txt",
                   "tests/native_stage_fixture.cpp", "tools/remaster-launcher/normal_hash.cpp"):
        _regular(source / member)
    commit = query("rev-parse", "HEAD")
    tree = query("rev-parse", "HEAD^{tree}")
    native_tree = query("rev-parse", "HEAD:runtime/mw3-re")
    if (not re.fullmatch(r"[0-9a-f]{40}", expected_commit) or commit != expected_commit
            or not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (tree, native_tree))):
        raise ValueError("Observed source commit/tree identity mismatch")
    if require_clean and query("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Dirty tracked source is not an owned native recipe input")
    return dict(commit=commit, tree=tree, native_tree=native_tree,
                describe=query("describe", "--tags", "--match", "v[0-9]*", "--always", "--dirty"),
                build_count=query("rev-list", "--count", "HEAD"))


def _tool_observations(tools, environment, directory):
    probes = {"git": (["--version"], r"git version [^\r\n]+"),
              "cmake": (["--version"], r"cmake version [^\r\n]+"),
              "ninja": (["--version"], r"[0-9]+(?:\.[0-9]+)+"),
              "clang_cl": (["--version"], r"clang version [^\r\n]+"),
              "glslang": (["--version"], r"Glslang Version: [^\r\n]+"),
              "dxc": (["--version"], r"[^\r\n]*(?:dxc|libdxcompiler)[^\r\n]*"),
              "dumpbin": (["/headers"], r"Microsoft \(R\) COFF/PE Dumper Version [^\r\n]+")}
    result = {}
    for name, (arguments, expression) in probes.items():
        if name not in tools:
            continue
        path = _regular(tools[name])
        if path.name.lower() != _TOOL_NAMES[name].lower():
            raise ValueError("Unexpected selected tool basename")
        _pe(path, library=False)
        before = _identity(path)
        digest = file_hash(path)
        try:
            actual = [*arguments, path] if name == "dumpbin" else arguments
            text = _run([path, *actual], environment, directory).decode("utf-8")
        except ValueError:
            raise ValueError("Selected " + name + " version/identity probe failed") from None
        version = re.search(expression, text)
        if version is None or _identity(path) != before or file_hash(path) != digest:
            raise ValueError("Unusable or changed selected tool identity")
        result[name] = dict(bytes=before[2], sha256=digest, version=version.group(0))
    exec_path = Path(_run([tools["git"], "--exec-path"], environment, directory).decode("utf-8").strip())
    if not _directory(exec_path).is_relative_to(Path(tools["git"]).parent.parent):
        raise ValueError("Selected Git execution prefix leaves its installation")
    return result


def _cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in (*_DIRECTORIES, *_TOOL_NAMES, "build", "output", "archive_lib", "zlib_lib", "lzma_lib"):
        parser.add_argument("--" + name.replace("_", "-"), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--jobs", required=True, type=int)
    return parser.parse_args(argv)


def _load_json(path, limit=MAX_METADATA_BYTES):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate build metadata property")
            result[key] = value
        return result
    with _regular(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Excessive build metadata")
    try:
        result = json.loads(data, object_pairs_hook=unique)
        pending = [(result, 0)]
        while pending:
            value, depth = pending.pop()
            if depth > 64:
                raise ValueError("Excessive build metadata depth")
            if isinstance(value, dict):
                pending.extend((item, depth + 1) for item in value.values())
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value)
        return result
    except (json.JSONDecodeError, UnicodeError, RecursionError):
        raise ValueError("Invalid build metadata") from None


def _notice_inputs(paths, source_commit):
    native = paths["source"] / "runtime/mw3-re"
    notices = {}
    components = []
    inputs = {}
    qualification_checks = []
    def component(name, version, source, files):
        for value in (name, version, source):
            if not isinstance(value, str) or not 1 <= len(value) <= 256 or any(ord(c) < 32 for c in value):
                raise ValueError("Invalid selected component identity")
        for relative, path in files.items():
            _relative(relative)
            if relative in notices:
                raise ValueError("Repeated selected notice destination")
            notices[relative] = _regular(path)
            inputs["notice/" + relative] = path
        components.append(dict(name=name, version=version, source=source, notices=list(files)))
    component("mw3-re", "observed-source", source_commit, {"LICENSE.txt": native / "LICENSE"})
    distributions = {}
    for key, name in (("sdl3", "SDL3"), ("sdl3_ttf", "SDL3_ttf")):
        cmake = paths[key]
        distribution = cmake.parent
        match = re.search(r'set\(PACKAGE_VERSION "([0-9.]+)"\)', _small_text(cmake / (name + "ConfigVersion.cmake")))
        if not match:
            raise ValueError("Missing selected SDL distribution version")
        library = _regular(distribution / "lib/x64" / (name + ".dll"))
        _pe(library, library=True)
        inputs[key + "/dll"] = library
        inputs[key + "/import-library"] = _regular(library.with_suffix(".lib"))
        for directory in (cmake, distribution / "include"):
            for path in _directory(directory).rglob("*"):
                _unlinked(path)
                if path.is_file():
                    inputs[key + "/" + path.relative_to(distribution).as_posix()] = _regular(path)
                    if len(inputs) > MAX_MEMBERS:
                        raise ValueError("Excessive selected dependency inventory")
        component(name.lower(), match[1], "pending-observed-sdk-identity",
                  {"licenses/" + name.lower().replace("_", "-") + "/LICENSE.txt": distribution / "LICENSE.txt"})
        distributions[key] = (match[1], library.parent, library)
    qualification_path = paths["ttf_notices"] / "component-source-map.json"
    qualification = _load_json(qualification_path)
    inputs["ttf-notices/component-source-map.json"] = qualification_path
    if (not isinstance(qualification, dict) or qualification.get("release_version") != "SDL3_ttf " + distributions["sdl3_ttf"][0]
            or not str(qualification.get("status", "")).startswith("release-associated-notice-set-qualified")):
        raise ValueError("Unqualified SDL3_ttf release/component notice association")
    qualification_checks.append((distributions["sdl3_ttf"][2], qualification.get("x64_dll_sha256")))
    expected = {"freetype": "freetype/FTL.TXT", "harfbuzz": "harfbuzz/COPYING",
                "plutosvg": "plutosvg/LICENSE", "plutovg": "plutovg/LICENSE"}
    entries = qualification.get("components")
    if (not isinstance(entries, list) or len(entries) != 4
            or {item.get("name") for item in entries if isinstance(item, dict)} != set(expected)):
        raise ValueError("Incomplete SDL3_ttf component notice inventory")
    for item in entries:
        if any(not isinstance(item.get(field), str) for field in
               ("name", "version", "source_repo", "source_commit", "notice_relative_path", "notice_sha256")):
            raise ValueError("Malformed SDL3_ttf component source/notice map")
        name = item["name"]
        relative = expected[name]
        notice = _regular(paths["ttf_notices"] / relative)
        if (item.get("notice_relative_path") != relative
                or not re.fullmatch(r"[0-9a-f]{40}", str(item.get("source_commit", "")))):
            raise ValueError("SDL3_ttf component notice identity mismatch")
        qualification_checks.append((notice, item.get("notice_sha256")))
        component(name, item["version"], item["source_repo"] + "@" + item["source_commit"],
                  {"licenses/" + relative: notice})
    static = (("pl_mpeg", "c871f2be022ece7ef4f64230b4fb8e1fb9eb6023", "README.md"),
              ("enet", "1.3.18", "LICENSE"), ("miniupnpc", "2.2.8", "LICENSE"),
              ("miniz", "3.0.2", "LICENSE"))
    enet_header = _small_text(native / "third_party/enet/include/enet/enet.h")
    if (not all(re.search(r"ENET_VERSION_" + key + r"\s+" + value + r"\b", enet_header)
                for key, value in (("MAJOR", "1"), ("MINOR", "3"), ("PATCH", "18")))
            or _small_text(native / "third_party/miniupnpc/VERSION").strip() != "2.2.8"
            or "tag 3.0.2" not in _small_text(native / "third_party/miniz/README.md")
            or static[0][1] not in _small_text(native / "third_party/pl_mpeg/README.md")):
        raise ValueError("Unexpected vendored static component version")
    for name, version, basename in static:
        component(name, version, "CoreCriticalProject:" + source_commit,
                  {"licenses/" + name + "/" + basename: native / "third_party" / name / basename})
    prefix = paths["archive_prefix"]
    headers = {"archive.h": r"ARCHIVE_VERSION_NUMBER\s+3007009",
               "zlib.h": r'ZLIB_VERSION\s+"1\.3\.1"',
               "lzma/version.h": r"LZMA_VERSION_PATCH\s+1"}
    for relative, pattern in headers.items():
        if not re.search(pattern, _small_text(prefix / "include" / relative)):
            raise ValueError("Static archive prefix version mismatch")
    lzma_header = _small_text(prefix / "include/lzma/version.h")
    if not all(re.search(r"LZMA_VERSION_" + key + r"\s+" + value + r"\b", lzma_header)
               for key, value in (("MAJOR", "5"), ("MINOR", "8"), ("PATCH", "1"))):
        raise ValueError("Static xz prefix version mismatch")
    for name, version, sources in (
            ("libarchive", "3.7.9", ("COPYING",)), ("zlib", "1.3.1", ("LICENSE",)),
            ("xz", "5.8.1", ("COPYING", "COPYING.0BSD"))):
        component(name, version, "selected-static-prefix:" + name + "-" + version,
                  {"licenses/" + name + "/" + basename:
                   prefix / "share/licenses" / (name + "-" + version) / basename for basename in sources})
    for key in ("archive_lib", "zlib_lib", "lzma_lib"):
        library = _regular(paths[key])
        if not library.is_relative_to(prefix / "lib") or library.suffix.lower() != ".lib":
            raise ValueError("Selected static archive library leaves its pinned prefix")
        with library.open("rb") as stream:
            if stream.read(8) != b"!<arch>\n":
                raise ValueError("Selected archive input is not a static COFF archive")
        inputs[key] = library
    for key, directory in (("archive-include", prefix / "include"), ("vulkan", paths["vulkan_headers"])):
        for path in _directory(directory).rglob("*"):
            _unlinked(path)
            if path.is_file():
                inputs[key + "/" + path.relative_to(directory).as_posix()] = _regular(path)
                if len(inputs) > MAX_MEMBERS:
                    raise ValueError("Excessive selected dependency inventory")
    for name in ("dxcompiler.dll", "dxil.dll"):
        inputs["dxc/" + name] = _regular(paths["dxc"].parent / name)
    _input_sizes(inputs)
    for path, expected_hash in qualification_checks:
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash) or file_hash(path) != expected_hash:
            raise ValueError("Selected qualified notice/DLL hash mismatch")
    for name in ("sdl3", "sdl3_ttf"):
        next(item for item in components if item["name"] == name)["source"] = "sha256:" + file_hash(distributions[name][2])
    for name, key in (("libarchive", "archive_lib"), ("zlib", "zlib_lib"), ("xz", "lzma_lib")):
        next(item for item in components if item["name"] == name)["source"] = "selected-static-input-sha256:" + file_hash(paths[key])
    _json(components)
    return notices, components, inputs, distributions


def _input_sizes(inputs):
    sizes = {name: _identity(path) for name, path in inputs.items()}
    if (len(sizes) > MAX_MEMBERS or any(not 0 < identity[2] <= MAX_CLOSURE_BYTES for identity in sizes.values())
            or sum(identity[2] for identity in sizes.values()) > MAX_CLOSURE_BYTES):
        raise ValueError("Selected dependency observations exceed their budget")
    return sizes


def _observe_inputs(inputs):
    sizes = _input_sizes(inputs)
    observed = {}
    for name, path in inputs.items():
        observed[name] = dict(bytes=sizes[name][2], sha256=file_hash(path))
        if _identity(path) != sizes[name]:
            raise ValueError("Selected input changed during observation")
    _json(observed)
    return observed


def _recipe_paths(args):
    paths = {key: _path_argument(value) for key, value in vars(args).items() if key not in ("commit", "jobs")}
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise ValueError("Recipe requires a full lowercase observed integration commit")
    if not 1 <= args.jobs <= min(8, os.cpu_count() or 1):
        raise ValueError("Recipe jobs exceed the permitted CPU budget")
    for name in _DIRECTORIES:
        _directory(paths[name])
    for name in (*_TOOL_NAMES, "archive_lib", "zlib_lib", "lzma_lib"):
        _regular(paths[name])
    for name in _TOOL_NAMES:
        if paths[name].name.lower() != _TOOL_NAMES[name].lower():
            raise ValueError("Wrong selected recipe tool basename")
    if not paths["crt_root"].is_relative_to(paths["vs"] / "VC/Redist/MSVC"):
        raise ValueError("Release CRT leaves the selected VS installation")
    if not re.fullmatch(r"Microsoft\.VC[0-9]+\.CRT", paths["crt_root"].name) or paths["crt_root"].parent.name != "x64":
        raise ValueError("Selected CRT is not an x64 Release CRT")
    profile = _native_bootstrap_selection(paths["vs"])
    _validate_native_crt(paths["vs"], paths["crt_root"], profile)
    build, output = paths["build"], paths["output"]
    if _paths_overlap(build, output):
        raise ValueError("Recipe build/output destinations overlap")
    for destination in (build, output):
        if destination.exists():
            raise ValueError("Recipe build/output destination already exists")
        _directory(destination.parent)
        for name, protected in paths.items():
            if name not in ("build", "output") and (
                    _paths_overlap(destination, protected)):
                raise ValueError("Recipe destination overlaps a selected input")
    return paths


def _cmake_literal(value):
    text = str(value).replace("\\", "/")
    marker = "="
    while "]" + marker + "]" in text:
        marker += "="
    return "[" + marker + "[" + text + "]" + marker + "]"


def configure_arguments(paths, derived, source, build):
    cache = dict(_SEARCH_POLICY, CMAKE_BUILD_TYPE="Release", CMAKE_MAKE_PROGRAM=paths["ninja"],
                 CMAKE_C_COMPILER=paths["clang_cl"], CMAKE_CXX_COMPILER=paths["clang_cl"],
                 CMAKE_LINKER=derived["linker"], CMAKE_AR=derived["ar"],
                 CMAKE_RC_COMPILER=derived["rc"], CMAKE_MT=derived["mt"],
                 CMAKE_MSVC_RUNTIME_LIBRARY="MultiThreadedDLL", CMAKE_EXPORT_COMPILE_COMMANDS="ON")
    command = [paths["cmake"], "-S", source, "-B", build, "-G", "Ninja"]
    command.extend("-D" + name + "=" + str(value).replace("\\", "/") for name, value in cache.items())
    return command, cache


def _cache(path):
    result = {}
    for line in _small_text(path).splitlines():
        if not line or line.startswith(("#", "//")):
            continue
        match = re.fullmatch(r"([^:=]+):([^=]+)=(.*)", line)
        if not match or match[1] in result:
            raise ValueError("Malformed or repeated CMake cache entry")
        result[match[1]] = match[3]
    return result


def _flags(cache):
    result = {}
    for name in ("CMAKE_C_FLAGS", "CMAKE_CXX_FLAGS", "CMAKE_EXE_LINKER_FLAGS",
                 "CMAKE_SHARED_LINKER_FLAGS", "CMAKE_MODULE_LINKER_FLAGS"):
        for suffix in ("", "_RELEASE"):
            key = name + suffix
            if key not in cache or re.search(r"[A-Za-z]:[\\/]", cache[key]):
                raise ValueError("Missing or nonlogical clean default flags")
            result[key] = cache[key]
    return result


def _query_codemodel(build):
    query = build / ".cmake/api/v1/query"
    query.mkdir(parents=True)
    (query / "codemodel-v2").write_text("", encoding="utf-8")


def _library_arguments(fragment):
    from ctypes import wintypes as wt
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.CommandLineToArgvW.argtypes = (wt.LPCWSTR, ctypes.POINTER(ctypes.c_int))
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wt.LPWSTR)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = (wt.HLOCAL,)
    count = ctypes.c_int()
    arguments = shell.CommandLineToArgvW("link.exe " + fragment, ctypes.byref(count))
    if not arguments:
        raise ValueError("Cannot decode selected CMake link arguments")
    try:
        return [arguments[index] for index in range(1, count.value)]
    finally:
        kernel.LocalFree(arguments)


def _validate_edges(paths, environment, allowed_system, build, *, target="mw3"):
    """Inspect the actual configured target closure, not a caller-supplied library roster."""
    reply = _directory(build / ".cmake/api/v1/reply")
    indices = list(reply.glob("index-*.json"))
    if len(indices) != 1:
        raise ValueError("Missing or ambiguous fresh configured target reply")
    index = _load_json(indices[0])
    model = _load_json(reply / _relative(index["reply"]["codemodel-v2"]["jsonFile"]))
    configured_source = _directory(model["paths"]["source"])
    expected_source = paths["source"] / "runtime/mw3-re" if target == "mw3" else build.parent / "source"
    if configured_source != expected_source:
        raise ValueError("Configured target graph has an unexpected source root")
    configurations = model["configurations"]
    if len(configurations) != 1 or configurations[0]["name"] != "Release":
        raise ValueError("Configured target graph is not the selected Release configuration")
    references = {entry["id"]: entry for entry in configurations[0]["targets"]}
    descriptions = {identity: _load_json(reply / _relative(reference["jsonFile"]))
                    for identity, reference in references.items()}
    generated_libraries = set()
    for description in descriptions.values():
        for artifact in description.get("artifacts", []):
            path = _unlinked(build / artifact["path"])
            if path.suffix.lower() == ".lib":
                if not path.is_relative_to(build):
                    raise ValueError("Configured library output leaves the owned build")
                generated_libraries.add(path)
    selected = [entry for entry in references.values() if entry["name"] == target]
    if len(selected) != 1:
        raise ValueError("Configured native target is absent or ambiguous")
    allowed = (paths["source"], build, paths["clang_cl"].parent.parent, *allowed_system)
    if target != "mw3":
        allowed += (configured_source,)
    allowed += tuple(paths[name].parent for name in ("sdl3", "sdl3_ttf") if name in paths)
    allowed += tuple(paths[name] for name in ("archive_prefix", "vulkan_headers") if name in paths)
    library_search = (build, *( _directory(value) for value in environment["LIB"].split(";")))
    def path_allowed(path, *, directory=False):
        if directory and _unlinked(path).is_relative_to(build):
            if Path(path).exists() and not Path(path).is_dir():
                raise ValueError("Configured generated include is not a directory")
            return _unlinked(path)
        path = _directory(path) if directory else _regular(path)
        if not any(path.is_relative_to(root) for root in allowed):
            raise ValueError("Configured dependency escapes the selected source/tool/input roots")
        return path
    pending = [selected[0]["id"]]
    visited = set()
    while pending:
        identity = pending.pop()
        if identity in visited:
            continue
        if len(visited) >= MAX_MEMBERS or identity not in references:
            raise ValueError("Invalid configured native target closure")
        visited.add(identity)
        description = descriptions[identity]
        pending.extend(item["id"] for item in description.get("dependencies", []))
        for group in description.get("compileGroups", []):
            for include in group.get("includes", []):
                path_allowed(include["path"], directory=True)
        for source in description.get("sources", []):
            path = Path(source["path"])
            if not path.is_absolute():
                path = configured_source / path
            # Generated outputs may not exist before build; their ancestors must stay in the owned build.
            if source.get("isGenerated"):
                if not _unlinked(path).is_relative_to(build):
                    raise ValueError("Configured generated source leaves the owned build")
            else:
                path_allowed(path)
        for fragment in description.get("link", {}).get("commandFragments", []):
            for token in _library_arguments(fragment["fragment"]):
                if token.upper().startswith(("/LIBPATH:", "-LIBPATH:")):
                    path_allowed(token.split(":", 1)[1], directory=True)
            if fragment["role"] != "libraries":
                continue
            for token in _library_arguments(fragment["fragment"]):
                library = Path(token)
                if library.suffix.lower() != ".lib":
                    raise ValueError("Unknown configured library argument")
                if library.is_absolute():
                    if _unlinked(library) not in generated_libraries:
                        path_allowed(library)
                else:
                    matches = [root / library for root in library_search
                               if (root / library).is_file() or _unlinked(root / library) in generated_libraries]
                    if not matches:
                        raise ValueError("Configured system/CRT library cannot resolve in selected LIB roots")
                    if _unlinked(matches[0]) not in generated_libraries:
                        path_allowed(matches[0])
    return dict(target=target, configured_targets=len(visited), selected_root_checks=True)


def build_qualification_fixture(paths, derived, environment, directory):
    """Build authored probe code with the same clean selected toolchain controls."""
    directory.mkdir()
    source = directory / "source"
    build = directory / "build"
    source.mkdir()
    guard = ("#if defined(MW34_POISON_CXXFLAGS) || defined(MW34_POISON_CFLAGS) || "
             "defined(MW34_POISON_CL) || defined(MW34_POISON_UNDERSCORE_CL)\n"
             "#error MW34_POISON_COMPILER_CONTROL\n#endif\n")
    (source / "guard.cpp").write_text(guard + "#include <windows.h>\n#include <vector>\n#include " +
        '"' + (paths["source"] / "tests/native_stage_fixture.cpp").as_posix() + '"\n', encoding="utf-8")
    (source / "guard.c").write_text(guard + "#include <windows.h>\n#include <stdio.h>\n"
        "void mw34_environment_guard(void) { (void)sizeof(DWORD); }\n", encoding="utf-8")
    project = ('cmake_minimum_required(VERSION 3.24)\nproject(mw34_recipe_probe LANGUAGES C CXX)\n'
        'find_package(MW34Marker CONFIG QUIET)\n'
        'add_library(mw34_normal_hash SHARED ' + _cmake_literal(paths["source"] / "tools/remaster-launcher/normal_hash.cpp") + ')\n'
        'target_include_directories(mw34_normal_hash PRIVATE ' + _cmake_literal(paths["source"] / "runtime/graphics") + ')\n'
        'target_compile_features(mw34_normal_hash PRIVATE cxx_std_20)\n'
        'add_executable(mw34_native_stage_fixture guard.cpp guard.c)\n'
        'target_link_libraries(mw34_native_stage_fixture PRIVATE mw34_normal_hash)\n')
    (source / "CMakeLists.txt").write_text(project, encoding="utf-8")
    _query_codemodel(build)
    command, _ = configure_arguments(paths, derived, source, build)
    _run(command, environment, directory, timeout=180, log=directory / "configure.log")
    _run([paths["cmake"], "--build", build, "--target", "mw34_native_stage_fixture", "--parallel", "1"],
         environment, directory, timeout=180, log=directory / "build.log")
    _pe(build / "mw34_native_stage_fixture.exe", library=False)
    return build, _flags(_cache(build / "CMakeCache.txt"))


def qualify_git_lookup(source, commit, paths, environment, fixture, directory, *, unsafe_control=False):
    directory.mkdir()
    shadow = directory / "shadow"
    shadow.mkdir()
    for source_path, name in ((fixture / "mw34_native_stage_fixture.exe", "git.exe"),
                              (fixture / "mw34_normal_hash.dll", "mw34_normal_hash.dll"),
                              (paths["crt_root"] / "vcruntime140.dll", "vcruntime140.dll")):
        original = _regular(source_path)
        shutil.copyfile(original, shadow / name)
        if file_hash(original) != file_hash(shadow / name):
            raise ValueError("Authored Git lookup control changed while copying")
    script = directory / "lookup.cmake"
    result_path = directory / "result.txt"
    script.write_text("execute_process(COMMAND git -C " + _cmake_literal(source) +
        " rev-parse HEAD WORKING_DIRECTORY " + _cmake_literal(shadow) +
        " RESULT_VARIABLE status OUTPUT_VARIABLE identity ERROR_VARIABLE diagnostic)\n"
        'if(NOT status STREQUAL "0")\nmessage(FATAL_ERROR "Bare Git identity query failed")\nendif()\n'
        "file(WRITE " + _cmake_literal(result_path) + ' "' + "$" + '{identity}")\n', encoding="utf-8")
    guarded = dict(environment)
    if unsafe_control:
        guarded.pop("NoDefaultCurrentDirectoryInExePath", None)
    _run([paths["cmake"], "-P", script], guarded, shadow, log=directory / "lookup.log")
    actual = _small_text(result_path).strip()
    expected = "MW34_AUTHORED_SHADOW_GIT" if unsafe_control else commit
    if actual != expected:
        raise ValueError("Unsupported selected CMake/Git current-directory lookup behavior")
    return dict(guarded=not unsafe_control, expected_identity_observed=True)


def _validate_configured(paths, derived, cache, expected, baseline_flags, build, source_identity):
    for name, value in expected.items():
        actual = cache.get(name)
        if isinstance(value, Path):
            if actual is None or _unlinked(actual) != value:
                raise ValueError("Configured selected path mismatch: " + name)
        elif actual != value:
            raise ValueError("Configured recipe option mismatch: " + name)
    forbidden = ("CMAKE_TOOLCHAIN_FILE", "CMAKE_PROJECT_INCLUDE", "CMAKE_PROJECT_INCLUDE_BEFORE",
                 "CMAKE_PROJECT_TOP_LEVEL_INCLUDES", "CMAKE_C_COMPILER_LAUNCHER",
                 "CMAKE_CXX_COMPILER_LAUNCHER", "CMAKE_C_LINKER_LAUNCHER", "CMAKE_CXX_LINKER_LAUNCHER")
    if any(cache.get(name) for name in forbidden) or _flags(cache) != baseline_flags:
        raise ValueError("Unexpected configured toolchain/launcher or non-clean recipe flags")
    if cache.get("MW3_CC_TARGET_X64") != "1":
        raise ValueError("Native configure did not establish the x64 target")
    commands = _load_json(build / "compile_commands.json", 16 * MAX_METADATA_BYTES)
    if not isinstance(commands, list) or not 1 <= len(commands) <= MAX_MEMBERS:
        raise ValueError("Invalid native compile command inventory")
    main = [entry["command"] for entry in commands
            if Path(entry["file"]).as_posix().endswith("/src/frontend/sdl/mw3_main.cpp")]
    renderer = [entry for entry in commands if Path(entry["file"]).as_posix().endswith("/src/frontend/core_critical/frame_renderer.cpp")]
    if (len(main) != 1 or not renderer or "CC_MW3_RE_ADAPTER=1" not in main[0]
            or "MW3_HAVE_LIBARCHIVE=1" not in main[0] or "LIBARCHIVE_STATIC" not in main[0]
            or any(token in main[0] for token in ("MW3_GAME_DIR", "MW3_ASSETS_DIR", "MW3_HAVE_SDL_SOUND"))):
        raise ValueError("Native compile definitions do not match the package/Vulkan/archive recipe")
    resource = _small_text(build / "mw3.rc")
    if (source_identity["describe"] in ("", "unknown") or not source_identity["build_count"].isdigit()
            or f'VALUE "ProductVersion", "{source_identity["describe"]}"' not in resource
            or f'FILEVERSION 0,1,0,{source_identity["build_count"]}' not in resource):
        raise ValueError("Native generated version/count does not match genuine selected Git")


@contextmanager
def _producer_ownership():
    from ctypes import wintypes as wt
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = (wt.LPVOID, wt.BOOL, wt.LPCWSTR)
    kernel.CreateMutexW.restype = wt.HANDLE
    kernel.CloseHandle.argtypes = kernel.ReleaseMutex.argtypes = (wt.HANDLE,)
    handle = kernel.CreateMutexW(None, True, "Local\\CoreCriticalProject-B1-native-producer")
    if not handle:
        raise OSError("Cannot acquire native producer ownership")
    if ctypes.get_last_error() == 183:
        kernel.CloseHandle(handle)
        raise ValueError("Another owned native producer is active")
    try:
        yield
    finally:
        kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


def produce(args):
    if os.name != "nt":
        raise ValueError("Owned native recipe requires Windows")
    paths = _recipe_paths(args)
    tools = {name: paths[name] for name in _TOOL_NAMES}
    bootstrap_profile, bootstrap_inputs = _native_bootstrap_inputs(paths["vs"])
    profile = next(item for item in _NATIVE_BOOTSTRAP_PROFILES if item["name"] == bootstrap_profile)
    _validate_native_crt(paths["vs"], paths["crt_root"], profile)
    environment, derived, allowed_system = build_environment(paths["vs"], tools, paths["build"].parent,
                                                            source=paths["source"], bootstrap_profile=bootstrap_profile)
    tools_before = _tool_observations(tools, environment, paths["build"].parent)
    source_before = _source_identity(paths["source"], paths["git"], environment, args.commit)
    notices, components, inputs, distributions = _notice_inputs(paths, args.commit)
    if not 1 <= len(source_before["describe"]) <= 256:
        raise ValueError("Observed native version exceeds the bounded component index")
    components[0]["version"] = source_before["describe"]
    inputs.update({"selected-tool/" + name: path for name, path in derived.items()})
    inputs.update({"selected-bootstrap/" + name: path for name, path in bootstrap_inputs.items()})
    inputs_before = _observe_inputs(inputs)
    with _producer_ownership():
        build = paths["build"]
        build.mkdir()
        marker = build / ".incomplete"
        marker.write_text("Owned local native invocation in progress; not an admitted runtime.\n", encoding="utf-8")
        fixture, baseline_flags = build_qualification_fixture(paths, derived, environment, build / "qualification")
        lookup = qualify_git_lookup(paths["source"], args.commit, paths, environment, fixture, build / "git-lookup")
        command, expected = configure_arguments(paths, derived, paths["source"] / "runtime/mw3-re", build)
        selected = dict(MW3_PACKAGE="ON", MW3_CORE_CRITICAL_VULKAN="ON",
                        CMAKE_DISABLE_FIND_PACKAGE_SDL3_sound="TRUE", SDL3_DIR=paths["sdl3"],
                        SDL3_ttf_DIR=paths["sdl3_ttf"], MW3_VULKAN_HEADERS=paths["vulkan_headers"],
                        GLSLANG=paths["glslang"], DXC=paths["dxc"],
                        LIBARCHIVE_INCLUDE=paths["archive_prefix"] / "include",
                        LIBARCHIVE_LIB=paths["archive_lib"], MW3_Z_LIB=paths["zlib_lib"],
                        MW3_LZMA_LIB=paths["lzma_lib"])
        expected.update(selected)
        command.extend("-D" + name + "=" + str(value).replace("\\", "/") for name, value in selected.items())
        _query_codemodel(build)
        _run(command, environment, build, timeout=180, log=build / "configure.log")
        cache = _cache(build / "CMakeCache.txt")
        _validate_configured(paths, derived, cache, expected, baseline_flags, build, source_before)
        edges = _validate_edges(paths, environment, allowed_system, build)
        _run([paths["cmake"], "--build", build, "--target", "mw3", "--parallel", args.jobs],
             environment, build, timeout=3600, log=build / "build.log")
        executable = _regular(build / "mw3.exe")
        _pe(executable, library=False)
        source_after = _source_identity(paths["source"], paths["git"], environment, args.commit)
        tools_after = _tool_observations(tools, environment, build)
        inputs_after = _observe_inputs(inputs)
        if _native_bootstrap_inputs(paths["vs"])[0] != bootstrap_profile:
            raise ValueError("Native bootstrap profile changed across native build")
        if source_after != source_before or tools_after != tools_before or inputs_after != inputs_before:
            raise ValueError("Selected source/tool/dependency observations changed across native build")
        observation = dict(source=source_before, environment_policy=ENVIRONMENT_POLICY,
                           bootstrap_profile=bootstrap_profile,
                           toolchain_versions={name: environment[name] for name in
                                               ("VCToolsVersion", "WindowsSDKVersion", "UCRTVersion") if name in environment},
                           recipe=dict(platform="windows-x64", configuration="Release", package=True,
                                       core_critical_vulkan=True, sdl3_sound=False, crt="MultiThreadedDLL",
                                       launcher_artwork=[], flags=baseline_flags),
                           tools_pre=tools_before, tools_post=tools_after,
                           inputs_pre=inputs_before, inputs_post=inputs_after, git_lookup=lookup,
                           configured_dependencies=edges)
        inventory = make_inventory(executable=executable,
            release_roots=[distributions["sdl3"][1], distributions["sdl3_ttf"][1]],
            crt_root=paths["crt_root"], dumpbin=paths["dumpbin"], notices=notices,
            components=components, source_commit=args.commit, builder="mw3-re-recipe-v1",
            environment=environment, observation=observation)
        for member in inventory.members:
            basename = Path(member.relative).name.lower()
            if member.relative.startswith("bin/") and basename not in ("mw3.exe", "sdl3.dll", "sdl3_ttf.dll") and not _CRT.match(basename):
                raise ValueError("Unexpected application DLL escapes the bounded native recipe")
        stage_inventory(inventory, paths["output"])
        marker.unlink()
        return dict(output=str(paths["output"]), build_id=inventory.build_id,
                    assurance="observational-prepost-only", runtime_sha256=file_hash(paths["output"] / "runtime.json"))


if __name__ == "__main__":
    try:
        print(json.dumps(produce(_cli()), sort_keys=True))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error)) from None
