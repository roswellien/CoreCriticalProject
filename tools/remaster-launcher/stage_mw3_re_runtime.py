"""Local-only MW3-RE staging internals; no installation, execution or public build CLI.

The owned native configure/build recipe is deliberately not implemented here yet.
Tests supply real authored Release PE inputs to this inventory/copy boundary.
An observed hash/commit is not authenticated provenance or consumer admission.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import time

MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_CLOSURE_BYTES = 4 * 1024**3
MAX_MEMBERS = 20000
_GENERATED = {"profile.json", "THIRD-PARTY.txt", "metadata/build-observation.json"}
_CRT = re.compile(r"(?:vcruntime|msvcp|concrt|vccorlib)", re.IGNORECASE)
_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


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
    for ancestor in (path, *path.parents):
        try:
            attributes = ancestor.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(attributes.st_mode) or getattr(attributes, "st_file_attributes", 0) & 0x400:
            raise ValueError("Staging input/output contains a link")
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
                             bufsize=0, creationflags=subprocess.CREATE_NO_WINDOW)
    data = bytearray()
    try:
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
            raise ValueError("Dependency inspection failed")
    finally:
        try:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
        finally:
            child.stdout.close()
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


def _metadata(members, components, source_commit, builder, tool_hash):
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
    witness = _json(dict(kind="local-build-staging-observation-v1",
        assurance="observational-only-not-authenticated", source_commit=source_commit,
        builder=builder, build_id=build_id, artifacts=artifacts, components=components,
        inspection=dict(tool="dumpbin.exe", sha256=tool_hash),
        external_prerequisites=["Windows x64", "Vulkan loader and driver"]))
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
                   source_commit, builder, environment):
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
    generated, provisional_id = _metadata(placeholder, components, source_commit, builder, tool_hash)
    _budget(members, generated)
    _descriptor(_pins(placeholder, generated), source_commit, builder, provisional_id)
    pinned = []
    for member in members:
        digest = file_hash(member.source)
        if _identity(member.source) != member.identity:
            raise ValueError("Source changed during inventory")
        pinned.append(replace(member, sha256=digest))
    generated, build_id = _metadata(pinned, components, source_commit, builder, tool_hash)
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
        if output.is_relative_to(source) or source.is_relative_to(output):
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


if __name__ == "__main__":
    raise SystemExit("Owned native configure/build recipe is not implemented; no payload was staged.")
