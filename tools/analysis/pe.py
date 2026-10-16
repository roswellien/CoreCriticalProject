"""Bounded, read-only PE32/i386 metadata inspection. No code is executed."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from collections import Counter
from pathlib import Path

MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_SECTIONS = 96
MAX_TABLE_ENTRIES = 65536
MAX_STRING_BYTES = 4096
DIRECTORY_NAMES = (
    "exports", "imports", "resources", "exceptions", "security", "base_relocations",
    "debug", "architecture", "global_pointer", "tls", "load_config", "bound_imports",
    "iat", "delay_imports", "clr", "reserved",
)


class PEError(ValueError):
    """The input is malformed or outside the supported PE32/i386 subset."""


class ManifestError(ValueError):
    """A supported-binary manifest is invalid."""


class UnsupportedBinaryError(ValueError):
    """The input is not an exact, verified supported identity."""


def read_binary(path: Path) -> bytes:
    with path.open("rb") as stream:
        # Limit the read itself, including files that grow after stat().
        if path.stat().st_size > MAX_FILE_BYTES:
            raise PEError(f"input exceeds the {MAX_FILE_BYTES}-byte analysis limit")
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise PEError("input grew beyond the analysis limit")
    return data


class PEImage:
    def __init__(self, data: bytes):
        self.data = data
        if len(data) > MAX_FILE_BYTES:
            raise PEError("input exceeds the analysis limit")
        if self.read(0, 2) != b"MZ":
            raise PEError("missing DOS MZ signature")
        pe_offset = self.u32(0x3C)
        if pe_offset < 0x40 or self.read(pe_offset, 4) != b"PE\0\0":
            raise PEError("invalid PE signature or header offset")
        coff = pe_offset + 4
        self.machine, section_count, self.timestamp, _, _, optional_size, self.characteristics = self.unpack("<HHIIIHH", coff)
        if self.machine != 0x14C:
            raise PEError(f"unsupported machine 0x{self.machine:04x}; expected i386")
        if not 1 <= section_count <= MAX_SECTIONS:
            raise PEError("invalid or excessive section count")
        optional = coff + 20
        self.read(optional, optional_size)
        if optional_size < 96:
            raise PEError("truncated PE32 optional header")
        self.optional_magic = self.u16(optional)
        if self.optional_magic != 0x10B:
            raise PEError("expected PE32 optional header (PE32+ is unsupported)")
        self.entry_point_rva = self.u32(optional + 16)
        self.image_base = self.u32(optional + 28)
        self.section_alignment = self.u32(optional + 32)
        self.file_alignment = self.u32(optional + 36)
        self.size_of_image = self.u32(optional + 56)
        self.size_of_headers = self.u32(optional + 60)
        self.subsystem = self.u16(optional + 68)
        self.dll_characteristics = self.u16(optional + 70)
        if not self.size_of_image or self.image_base + self.size_of_image > 0x100000000:
            raise PEError("image extent exceeds the 32-bit address space")
        if not 0 < self.size_of_headers <= min(len(data), self.size_of_image):
            raise PEError("invalid SizeOfHeaders")
        if self.entry_point_rva >= self.size_of_image:
            raise PEError("entry point lies outside the image")
        if not self.section_alignment or not self.file_alignment:
            raise PEError("zero file or section alignment")
        directory_count = self.u32(optional + 92)
        if directory_count > 16 or 96 + directory_count * 8 > optional_size:
            raise PEError("invalid or truncated data directory table")
        self.directories: list[tuple[int, int]] = []
        for index in range(directory_count):
            rva, size = self.unpack("<II", optional + 96 + index * 8)
            if (rva == 0) != (size == 0) and index != 8:
                raise PEError(f"incomplete {DIRECTORY_NAMES[index]} directory")
            self.directories.append((rva, size))
        self.directories.extend([(0, 0)] * (16 - directory_count))
        section_table = optional + optional_size
        if section_table + section_count * 40 > self.size_of_headers:
            raise PEError("section table exceeds SizeOfHeaders")
        self.sections: list[dict] = []
        raw_ranges = [(0, self.size_of_headers)]
        virtual_ranges = [(0, self.size_of_headers)]
        for index in range(section_count):
            record = section_table + index * 40
            name = self.read(record, 8).split(b"\0", 1)[0].decode("ascii", errors="backslashreplace")
            virtual_size, virtual_address, raw_size, raw_offset = self.unpack("<IIII", record + 8)
            flags = self.u32(record + 36)
            extent = max(virtual_size, raw_size)
            if virtual_address + extent > self.size_of_image:
                raise PEError(f"section {name!r} exceeds SizeOfImage")
            if raw_size:
                self.read(raw_offset, raw_size)
                self.check_overlap(raw_ranges, raw_offset, raw_size, "raw sections")
            if extent:
                self.check_overlap(virtual_ranges, virtual_address, extent, "virtual sections")
            self.sections.append({
                "name": name, "virtual_address": virtual_address, "virtual_size": virtual_size,
                "raw_offset": raw_offset, "raw_size": raw_size, "characteristics": flags,
                "executable": bool(flags & 0x20000000), "readable": bool(flags & 0x40000000),
                "writable": bool(flags & 0x80000000),
            })

    @staticmethod
    def check_overlap(ranges: list[tuple[int, int]], start: int, size: int, label: str) -> None:
        end = start + size
        if any(start < previous_end and previous_start < end for previous_start, previous_end in ranges):
            raise PEError(f"overlapping {label}")
        ranges.append((start, end))

    def read(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise PEError(f"truncated file range at 0x{offset:x}, size {size}")
        return self.data[offset:offset + size]

    def unpack(self, fmt: str, offset: int) -> tuple:
        return struct.unpack(fmt, self.read(offset, struct.calcsize(fmt)))

    def u16(self, offset: int) -> int:
        return self.unpack("<H", offset)[0]

    def u32(self, offset: int) -> int:
        return self.unpack("<I", offset)[0]

    def rva_range(self, rva: int, size: int) -> tuple[int, int]:
        """Return file offset and contiguous backing end; reject zero-filled tails."""
        if rva < 0 or size < 0 or rva + size > self.size_of_image:
            raise PEError("RVA range exceeds the image")
        if rva < self.size_of_headers and rva + size <= self.size_of_headers:
            return rva, self.size_of_headers
        for section in self.sections:
            delta = rva - section["virtual_address"]
            if 0 <= delta < section["raw_size"] and delta + size <= section["raw_size"]:
                return section["raw_offset"] + delta, section["raw_offset"] + section["raw_size"]
        raise PEError(f"RVA 0x{rva:x} (size {size}) has no contiguous file backing")

    def rva_u32(self, rva: int) -> int:
        return self.u32(self.rva_range(rva, 4)[0])

    def rva_string(self, rva: int) -> str:
        offset, backing_end = self.rva_range(rva, 1)
        end = self.data.find(b"\0", offset, min(backing_end, offset + MAX_STRING_BYTES))
        if end < 0:
            raise PEError(f"unterminated or excessive metadata string at RVA 0x{rva:x}")
        try:
            return self.data[offset:end].decode("ascii")
        except UnicodeDecodeError as error:
            raise PEError(f"non-ASCII metadata name at RVA 0x{rva:x}") from error

    def directory(self, index: int) -> tuple[int, int]:
        rva, size = self.directories[index]
        if rva:
            self.rva_range(rva, size)
        return rva, size

    def imports(self) -> list[dict]:
        rva, size = self.directory(1)
        if not rva:
            return []
        imports = []
        total_symbols = 0
        for index in range(min(size // 20, MAX_TABLE_ENTRIES)):
            offset = self.rva_range(rva + index * 20, 20)[0]
            lookup, timestamp, chain, name_rva, iat = self.unpack("<IIIII", offset)
            if not any((lookup, timestamp, chain, name_rva, iat)):
                return imports
            if not name_rva or not iat:
                raise PEError("import descriptor lacks library name or IAT")
            library = self.rva_string(name_rva)
            if not library:
                raise PEError("empty imported library name")
            thunk = lookup or iat
            symbols = []
            for symbol_index in range(MAX_TABLE_ENTRIES):
                value = self.rva_u32(thunk + symbol_index * 4)
                if not value:
                    break
                total_symbols += 1
                if total_symbols > MAX_TABLE_ENTRIES:
                    raise PEError("excessive import symbol count")
                # Ensure the reported IAT slot is actually mapped in the image.
                self.rva_range(iat + symbol_index * 4, 4)
                symbol = {"iat_rva": iat + symbol_index * 4}
                if value & 0x80000000:
                    if value & 0x7FFF0000:
                        raise PEError("invalid reserved bits in ordinal import")
                    symbol["ordinal"] = value & 0xFFFF
                else:
                    hint = self.u16(self.rva_range(value, 2)[0])
                    symbol.update({"name": self.rva_string(value + 2), "hint": hint})
                    if not symbol["name"]:
                        raise PEError("empty imported symbol name")
                symbols.append(symbol)
            else:
                raise PEError("unterminated import thunk table")
            imports.append({"library": library, "symbols": symbols})
        raise PEError("unterminated or excessive import descriptor table")

    def exports(self) -> list[dict]:
        rva, size = self.directory(0)
        if not rva:
            return []
        if size < 40:
            raise PEError("truncated export directory")
        offset = self.rva_range(rva, 40)[0]
        _, _, _, _, _, ordinal_base, function_count, name_count, functions, names, ordinals = self.unpack("<IIHHIIIIIII", offset)
        if function_count > MAX_TABLE_ENTRIES or name_count > MAX_TABLE_ENTRIES:
            raise PEError("excessive export table count")
        if name_count and not function_count:
            raise PEError("export names exist without an address table")
        function_offset = self.rva_range(functions, function_count * 4)[0] if function_count else 0
        names_offset = self.rva_range(names, name_count * 4)[0] if name_count else 0
        ordinals_offset = self.rva_range(ordinals, name_count * 2)[0] if name_count else 0
        names_by_index: dict[int, list[str]] = {}
        for index in range(name_count):
            ordinal_index = self.u16(ordinals_offset + index * 2)
            if ordinal_index >= function_count:
                raise PEError("export name ordinal exceeds the address table")
            names_by_index.setdefault(ordinal_index, []).append(self.rva_string(self.u32(names_offset + index * 4)))
        exports = []
        for index in range(function_count):
            target = self.u32(function_offset + index * 4)
            if not target:
                if index in names_by_index:
                    raise PEError("named export points to an absent function")
                continue
            if target >= self.size_of_image:
                raise PEError("export target exceeds the image")
            entry = {"ordinal": ordinal_base + index, "rva": target, "names": names_by_index.get(index, [])}
            if rva <= target < rva + size:
                entry["forwarder"] = self.rva_string(target)
            exports.append(entry)
        return exports

    def relocations(self) -> dict:
        rva, size = self.directory(5)
        cursor = 0
        blocks = 0
        slots = 0
        counts: Counter[int] = Counter()
        while cursor < size:
            if blocks >= MAX_TABLE_ENTRIES:
                raise PEError("excessive relocation block count")
            if size - cursor < 8:
                raise PEError("truncated base relocation block header")
            offset = self.rva_range(rva + cursor, 8)[0]
            page, block_size = self.unpack("<II", offset)
            if block_size < 8 or block_size % 2 or block_size > size - cursor:
                raise PEError("invalid base relocation block size")
            if page % 4096 or page >= self.size_of_image:
                raise PEError("invalid base relocation page RVA")
            count = (block_size - 8) // 2
            slots += count
            if slots > MAX_TABLE_ENTRIES:
                raise PEError("excessive relocation entry count")
            offset = self.rva_range(rva + cursor + 8, count * 2)[0] if count else offset + 8
            index = 0
            while index < count:
                entry = self.u16(offset + index * 2)
                kind, displacement = entry >> 12, entry & 0xFFF
                if kind and page + displacement + (4 if kind == 3 else 2) > self.size_of_image:
                    raise PEError("relocation target exceeds the image")
                counts[kind] += 1
                index += 1
                if kind == 4:
                    if index >= count:
                        raise PEError("HIGHADJ relocation lacks its paired addend slot")
                    index += 1
            cursor += block_size
            blocks += 1
        return {
            "present": bool(rva), "stripped_flag": bool(self.characteristics & 1),
            "dynamic_base_flag": bool(self.dll_characteristics & 0x40), "block_count": blocks,
            "entry_count": sum(counts.values()), "slot_count": slots,
            "type_counts": {str(key): value for key, value in sorted(counts.items())},
            "type_names": {"0": "ABSOLUTE (padding)", "1": "HIGH", "2": "LOW", "3": "HIGHLOW", "4": "HIGHADJ"},
            "interpretation": "Presence and flags only; safe rebasing has not been established.",
        }

    def metadata(self) -> dict:
        imports = self.imports()
        exports = self.exports()
        entry_sections = [section["name"] for section in self.sections if section["virtual_address"] <= self.entry_point_rva < section["virtual_address"] + max(section["raw_size"], section["virtual_size"])]
        return {
            "machine": self.machine, "optional_magic": self.optional_magic, "format": "PE32", "architecture": "i386",
            "timestamp": self.timestamp, "image_base": self.image_base, "size_of_image": self.size_of_image,
            "size_of_headers": self.size_of_headers, "section_alignment": self.section_alignment,
            "file_alignment": self.file_alignment, "subsystem": self.subsystem,
            "characteristics": self.characteristics, "dll_characteristics": self.dll_characteristics,
            "entry_point_rva": self.entry_point_rva, "entry_point_va": self.image_base + self.entry_point_rva,
            "entry_point_sections": entry_sections, "sections": self.sections,
            "executable_sections": [section for section in self.sections if section["executable"]],
            "data_directories": [{"name": DIRECTORY_NAMES[index], "address": address, "size": size, "address_kind": "file_offset" if index == 4 else "rva"} for index, (address, size) in enumerate(self.directories)],
            "imports": imports, "exports": exports, "relocations": self.relocations(),
            "dependencies": dependency_report(imports),
            "function_seeds": [{"va": self.image_base + self.entry_point_rva, "rva": self.entry_point_rva, "label": f"sub_{self.image_base + self.entry_point_rva:08X}", "evidence": "PE entry point; boundary and calling convention unverified"}] if self.entry_point_rva else [],
            "analysis_limits": [
                "No instruction decoding, execution, function-boundary recovery, or string extraction is performed.",
                "x87, SSE/MMX, SEH, RTTI, vtables, globals, jump tables, indirect calls, callbacks and subsystem boundaries remain unanalysed.",
                "Delay imports, TLS callbacks, bound imports and dynamic API resolution are not decoded.",
                "Executable section flags and entry points are evidence, not proof that every byte is code.",
            ],
        }


def dependency_report(imports: list[dict]) -> dict:
    categories: dict[str, list[dict]] = {}
    library_categories = {
        "ddraw.dll": "directdraw", "d3dim.dll": "direct3d", "d3drm.dll": "direct3d",
        "d3d8.dll": "direct3d", "d3d9.dll": "direct3d", "dinput.dll": "directinput",
        "dinput8.dll": "directinput", "dsound.dll": "directsound", "winmm.dll": "multimedia",
        "wsock32.dll": "networking", "ws2_32.dll": "networking", "wininet.dll": "networking",
        "shell32.dll": "shell", "user32.dll": "windowing", "gdi32.dll": "gdi",
        "advapi32.dll": "advanced_win32", "kernel32.dll": "base_win32", "ntdll.dll": "nt_native",
    }
    prefixes = {
        "threading": ("createthread", "exitthread", "getcurrentthread", "tls", "interlocked", "setthread", "resumethread", "suspendthread", "_beginthread", "_endthread"),
        "synchronization": ("waitfor", "createevent", "setevent", "resetevent", "createmutex", "releasemutex", "createsemaphore", "releasesemaphore", "entercriticalsection", "leavecriticalsection", "initializecriticalsection", "deletecriticalsection"),
        "timing": ("queryperformance", "gettickcount", "timegettime", "timebeginperiod", "timeendperiod", "timesetevent", "sleep", "getsystemtime", "getlocaltime"),
        "memory": ("heap", "virtualalloc", "virtualfree", "virtualprotect", "virtualquery", "globalalloc", "globalfree", "localalloc", "localfree", "malloc", "calloc", "realloc", "free"),
        "file_io": ("createfile", "readfile", "writefile", "setfile", "getfile", "findfirstfile", "findnextfile", "findclose", "deletefile", "movefile", "copyfile", "fopen", "fread", "fwrite", "fclose", "_open", "_read", "_write"),
        "registry": ("regopen", "regquery", "regset", "regcreate", "regclose", "regdelete", "regenum"),
        "dynamic_loading": ("loadlibrary", "freelibrary", "getprocaddress", "getmodulehandle"),
        "exceptions": ("setunhandledexceptionfilter", "unhandledexceptionfilter", "raiseexception", "__cxxframehandler", "_except_handler"),
    }
    for library in imports:
        dll = library["library"].lower()
        base_category = library_categories.get(dll)
        if re.fullmatch(r"(?:msvcrt|msvcr\d+|ucrtbase)\.dll", dll):
            base_category = "crt"
        for symbol in library["symbols"]:
            evidence = {"library": library["library"], **({"name": symbol["name"]} if "name" in symbol else {"ordinal": symbol["ordinal"]})}
            matches = {base_category} if base_category else set()
            # Symbol-prefix classification is a candidate label, never a recovered subsystem.
            if "name" in symbol:
                name = symbol["name"].lower()
                matches.update(category for category, starts in prefixes.items() if name.startswith(starts))
            for category in sorted(matches):
                categories.setdefault(category, []).append(evidence)
    return {
        "evidence": "Static import table only. Categories are API-family candidates; imports do not prove calls are reachable. COM methods and dynamically loaded APIs can be absent.",
        "library_count": len(imports), "symbol_count": sum(len(library["symbols"]) for library in imports),
        "categories": dict(sorted(categories.items())),
    }


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def load_manifest(path: Path, *, expected_game: str = "mw3") -> dict:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ManifestError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ManifestError(f"cannot decode manifest: {error}") from error
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "game", "binaries"}:
        raise ManifestError("manifest requires exactly schema_version, game and binaries")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1 or manifest["game"] != expected_game:
        raise ManifestError("unsupported manifest schema or game")
    if not isinstance(manifest["binaries"], list):
        raise ManifestError("binaries must be a list")
    ids, hashes = set(), set()
    required = {"id", "title", "filename", "sha256", "size_bytes", "pe"}
    for record in manifest["binaries"]:
        if not isinstance(record, dict) or not required <= set(record) or set(record) - required - {"provenance", "notes"}:
            raise ManifestError("invalid binary record fields")
        if any(not isinstance(record[key], str) or not record[key].strip() for key in ("id", "title", "filename", "sha256")):
            raise ManifestError("binary identity strings must be non-empty")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", record["id"]):
            raise ManifestError("binary id must be lowercase letters, digits and hyphens")
        if "/" in record["filename"] or "\\" in record["filename"] or record["filename"] in (".", ".."):
            raise ManifestError("filename must be a basename")
        if not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
            raise ManifestError("sha256 must be a complete lowercase SHA-256 digest")
        if record["id"] in ids or record["sha256"] in hashes:
            raise ManifestError("duplicate binary id or hash")
        ids.add(record["id"])
        hashes.add(record["sha256"])
        if not _integer(record["size_bytes"], 1, MAX_FILE_BYTES):
            raise ManifestError("invalid size_bytes")
        pe = record["pe"]
        if not isinstance(pe, dict) or set(pe) != {"machine", "optional_magic", "image_base", "entry_point_rva"}:
            raise ManifestError("invalid PE identity fields")
        if any(not _integer(pe[key], 0, 0xFFFFFFFF) for key in pe) or pe["machine"] != 0x14C or pe["optional_magic"] != 0x10B:
            raise ManifestError("PE identity must describe PE32/i386 with unsigned 32-bit values")
        if "provenance" in record and (not isinstance(record["provenance"], str) or not record["provenance"].strip()):
            raise ManifestError("provenance must be a non-empty string")
        if "notes" in record and (not isinstance(record["notes"], list) or any(not isinstance(note, str) for note in record["notes"])):
            raise ManifestError("notes must be a string list")
    return manifest


def validate_identity(data: bytes, manifest: dict, image: PEImage | None = None) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    for record in manifest["binaries"]:
        if digest == record["sha256"]:
            if len(data) != record["size_bytes"]:
                raise UnsupportedBinaryError("hash record disagrees with file size")
            image = image or PEImage(data)
            if any(getattr(image, key) != expected for key, expected in record["pe"].items()):
                raise UnsupportedBinaryError("hash record disagrees with PE identity metadata")
            # Fully validate the implemented metadata subset before accepting a profile.
            image.metadata()
            return record
    raise UnsupportedBinaryError(f"unsupported binary SHA-256 {digest}; no exact verified manifest identity")
