"""Synthetic, project-authored PE fixtures. No original game content is used."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/analysis"))
import pe  # noqa: E402


def load_tool(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


disassemble = load_tool("mw34_disassemble", ROOT / "tools/analysis/disassemble.py")


def fixture() -> bytes:
    """Author a tiny PE32 image with imports, exports and HIGHLOW relocation."""
    data = bytearray(0xC00)

    def put(offset: int, fmt: str, *values: int) -> None:
        struct.pack_into(fmt, data, offset, *values)

    data[0:2] = b"MZ"
    put(0x3C, "<I", 0x80)
    data[0x80:0x84] = b"PE\0\0"
    put(0x84, "<HHIIIHH", 0x14C, 3, 0, 0, 0, 224, 0x102)
    optional = 0x98
    put(optional, "<H", 0x10B)
    put(optional + 16, "<I", 0x1000)
    put(optional + 28, "<I", 0x400000)
    put(optional + 32, "<II", 0x1000, 0x200)
    put(optional + 56, "<II", 0x4000, 0x200)
    put(optional + 68, "<HH", 3, 0x40)
    put(optional + 92, "<I", 16)
    put(optional + 96, "<II", 0x2000, 0x100)
    put(optional + 104, "<II", 0x2100, 40)
    put(optional + 96 + 5 * 8, "<II", 0x3000, 12)
    section_table = optional + 224
    for index, (name, va, raw, size, flags) in enumerate([
        (b".text", 0x1000, 0x200, 0x200, 0x60000020),
        (b".rdata", 0x2000, 0x400, 0x600, 0x40000040),
        (b".reloc", 0x3000, 0xA00, 0x200, 0x42000040),
    ]):
        offset = section_table + index * 40
        data[offset:offset + len(name)] = name
        put(offset + 8, "<IIII", size, va, size, raw)
        put(offset + 36, "<I", flags)
    # Authored x86 leaf: return arg0 + arg1. Not extracted from any game.
    data[0x200:0x209] = bytes.fromhex("8b44240403442408c3")
    put(0x400, "<IIHHIIIIIII", 0, 0, 0, 0, 0x2050, 1, 2, 1, 0x2060, 0x2070, 0x2080)
    data[0x450:0x45C] = b"fixture.dll\0"
    put(0x460, "<II", 0x1000, 0x20A0)
    put(0x470, "<I", 0x2090)
    put(0x480, "<H", 0)
    data[0x490:0x49C] = b"fixture_add\0"
    data[0x4A0:0x4B6] = b"KERNEL32.GetTickCount\0"
    put(0x500, "<IIIII", 0x21A0, 0, 0, 0x2180, 0x21C0)
    data[0x580:0x58D] = b"KERNEL32.dll\0"
    put(0x5A0, "<III", 0x21E0, 0x80000007, 0)
    put(0x5C0, "<III", 0x21E0, 0x80000007, 0)
    put(0x5E0, "<H", 4)
    data[0x5E2:0x5EF] = b"GetTickCount\0"
    put(0xA00, "<IIHH", 0x1000, 12, 0x3004, 0)
    return bytes(data)


def changed(data: bytes, offset: int, fmt: str, *values: int) -> bytes:
    output = bytearray(data)
    struct.pack_into(fmt, output, offset, *values)
    return bytes(output)


def record_for(data: bytes) -> dict:
    image = pe.PEImage(data)
    return {
        "id": "synthetic-fixture", "title": "Project-authored test fixture", "filename": "fixture.exe",
        "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
        "pe": {key: getattr(image, key) for key in ("machine", "optional_magic", "image_base", "entry_point_rva")},
        "provenance": "Authored entirely in tests/test_binary_tools.py; not a game support claim.",
    }


class PEParsingTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def test_metadata_imports_exports_and_relocations(self):
        report = pe.PEImage(self.data).metadata()
        self.assertEqual(report["image_base"], 0x400000)
        self.assertEqual(report["entry_point_va"], 0x401000)
        self.assertEqual(report["entry_point_sections"], [".text"])
        self.assertEqual([section["name"] for section in report["executable_sections"]], [".text"])
        self.assertEqual(report["imports"][0]["library"], "KERNEL32.dll")
        self.assertEqual(report["imports"][0]["symbols"][0]["name"], "GetTickCount")
        self.assertEqual(report["imports"][0]["symbols"][1]["ordinal"], 7)
        self.assertEqual(report["exports"][0]["names"], ["fixture_add"])
        self.assertEqual(report["exports"][1]["forwarder"], "KERNEL32.GetTickCount")
        self.assertEqual(report["relocations"]["type_counts"], {"0": 1, "3": 1})
        self.assertEqual(report["dependencies"]["categories"]["timing"][0]["name"], "GetTickCount")
        self.assertEqual(report["function_seeds"][0]["label"], "sub_00401000")
        serialized = json.dumps(report)
        self.assertNotIn(self.data[0x200:0x209].hex(), serialized)

    def test_original_first_thunk_falls_back_to_iat(self):
        data = changed(self.data, 0x500, "<I", 0)
        self.assertEqual(len(pe.PEImage(data).imports()[0]["symbols"]), 2)

    def test_header_rva_and_zero_filled_tail(self):
        image = pe.PEImage(self.data)
        self.assertEqual(image.rva_range(0x80, 4)[0], 0x80)
        with self.assertRaises(pe.PEError):
            image.rva_range(0x1FF, 2)
        data = changed(self.data, 0x178 + 40 + 8, "<I", 0x800)
        with self.assertRaises(pe.PEError):
            pe.PEImage(data).rva_range(0x2700, 4)

    def test_rejects_truncated_headers_and_sections(self):
        for length in (0, 1, 63, 127, 131, 150, 200, 375, 500, len(self.data) - 1):
            with self.subTest(length=length), self.assertRaises(pe.PEError):
                pe.PEImage(self.data[:length]).metadata()

    def test_rejects_invalid_pe_identity_or_extents(self):
        cases = [
            (0x3C, "<I", 0xFFFFFFF0), (0x84, "<H", 0x8664), (0x98, "<H", 0x20B),
            (0x86, "<H", 97), (0x94, "<H", 95), (0x98 + 92, "<I", 17),
            (0x98 + 60, "<I", 0x100), (0x98 + 28, "<I", 0xFFFFF000),
            (0x98 + 16, "<I", 0x4000), (0x178 + 40 + 20, "<I", 0x200),
            (0x178 + 40 + 12, "<I", 0x1000), (0x178 + 16, "<I", 0xFFFFFF00),
            (0x98 + 104, "<I", 0),
        ]
        for offset, fmt, value in cases:
            with self.subTest(offset=offset, value=value), self.assertRaises(pe.PEError):
                pe.PEImage(changed(self.data, offset, fmt, value)).metadata()

    def test_rejects_malformed_imports_and_exports(self):
        cases = [
            (0x98 + 108, "<I", 20),  # no terminating import descriptor
            (0x500 + 12, "<I", 0),  # missing library
            (0x500 + 16, "<I", 0),  # missing IAT
            (0x5A0, "<I", 0x7FFFF000),  # unmapped import-by-name pointer
            (0x5A0, "<I", 0x80010007),  # reserved ordinal bits
            (0x480, "<H", 2),  # export ordinal outside EAT
            (0x400 + 20, "<I", 0x10001),  # excessive export address count
            (0x460, "<I", 0x4000),  # export outside image
        ]
        for offset, fmt, value in cases:
            with self.subTest(offset=offset, value=value), self.assertRaises(pe.PEError):
                pe.PEImage(changed(self.data, offset, fmt, value)).metadata()

    def test_rejects_unterminated_metadata_and_thunks(self):
        data = bytearray(self.data)
        data[0x900:0xA00] = b"A" * 0x100
        with self.assertRaises(pe.PEError):
            pe.PEImage(bytes(data)).rva_string(0x2500)
        data = bytearray(changed(self.data, 0x500, "<I", 0x2580))
        for offset in range(0x980, 0xA00, 4):
            struct.pack_into("<I", data, offset, 0x80000001)
        with self.assertRaises(pe.PEError):
            pe.PEImage(bytes(data)).imports()

    def test_absent_directories_and_security_file_offset(self):
        data = bytearray(self.data)
        data[0x98 + 96:0x98 + 224] = bytes(128)
        struct.pack_into("<II", data, 0x98 + 96 + 4 * 8, 0xBE0, 32)
        report = pe.PEImage(bytes(data)).metadata()
        self.assertEqual(report["imports"], [])
        self.assertEqual(report["exports"], [])
        self.assertFalse(report["relocations"]["present"])
        self.assertEqual(report["data_directories"][4]["address_kind"], "file_offset")

    def test_highadj_consumes_addend_instead_of_decoding_it(self):
        data = changed(self.data, 0xA00, "<IIHH", 0x3000, 12, 0x4004, 0x3FFF)
        report = pe.PEImage(data).relocations()
        self.assertEqual(report["type_counts"], {"4": 1})
        self.assertEqual(report["entry_count"], 1)
        self.assertEqual(report["slot_count"], 2)

    def test_missing_highadj_addend_fails(self):
        data = changed(self.data, 0xA00, "<IIHH", 0x3000, 12, 0, 0x4004)
        with self.assertRaisesRegex(pe.PEError, "paired addend"):
            pe.PEImage(data).relocations()

    def test_empty_relocation_blocks_are_bounded(self):
        data = changed(self.data, 0xA00, "<IIIIII", 0x1000, 8, 0x1000, 8, 0x1000, 8)
        data = changed(data, 0x98 + 96 + 5 * 8 + 4, "<I", 24)
        with patch.object(pe, "MAX_TABLE_ENTRIES", 2), self.assertRaisesRegex(pe.PEError, "block count"):
            pe.PEImage(data).relocations()

    def test_bad_relocation_blocks_fail(self):
        for size in (0, 7, 9, 14, 0xFFFFFFFF):
            with self.subTest(size=size), self.assertRaises(pe.PEError):
                pe.PEImage(changed(self.data, 0xA04, "<I", size)).relocations()
        with self.assertRaises(pe.PEError):
            pe.PEImage(changed(self.data, 0xA00, "<I", 0x1001)).relocations()

    def test_deterministic_mutations_never_leak_low_level_parser_errors(self):
        generator = random.Random(34)
        for _ in range(250):
            data = bytearray(self.data)
            offset = generator.randrange(len(data))
            data[offset] ^= generator.randrange(1, 256)
            try:
                pe.PEImage(bytes(data)).metadata()
            except pe.PEError:
                pass


class ManifestAndCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.data = fixture()
        self.binary = self.folder / "renamed-user-file.exe"
        self.binary.write_bytes(self.data)
        self.manifest_path = self.folder / "manifest.json"
        self.manifest = {"schema_version": 1, "game": "mw3", "binaries": [record_for(self.data)]}
        self.write_manifest()

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def run_cli(self, relative: str, *arguments: str):
        return subprocess.run([sys.executable, str(ROOT / relative), str(self.binary), "--manifest", str(self.manifest_path), *arguments], text=True, capture_output=True, timeout=20, check=False)

    def test_exact_identity_accepts_renamed_file(self):
        record = pe.validate_identity(self.data, pe.load_manifest(self.manifest_path))
        self.assertEqual(record["id"], "synthetic-fixture")
        result = self.run_cli("tools/binary-validator/validate.py", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "verified_identity")

    def test_changed_byte_unknown_hash_fails_closed(self):
        data = changed(self.data, 0x20, "<B", 1)
        with self.assertRaises(pe.UnsupportedBinaryError):
            pe.validate_identity(data, self.manifest)
        self.binary.write_bytes(data)
        result = self.run_cli("tools/binary-validator/validate.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unsupported binary", result.stderr)

    def test_empty_manifest_unknown_analysis_and_strict_mode(self):
        self.manifest["binaries"] = []
        self.write_manifest()
        self.assertEqual(self.run_cli("tools/binary-validator/validate.py").returncode, 2)
        analysis = self.run_cli("tools/analysis/analyze.py")
        self.assertEqual(analysis.returncode, 0, analysis.stderr)
        self.assertEqual(json.loads(analysis.stdout)["support"]["status"], "unknown_binary")
        self.assertEqual(self.run_cli("tools/analysis/analyze.py", "--require-supported").returncode, 2)

    def test_mismatched_manifest_metadata_rejected(self):
        self.manifest["binaries"][0]["size_bytes"] += 1
        with self.assertRaises(pe.UnsupportedBinaryError):
            pe.validate_identity(self.data, self.manifest)
        self.manifest["binaries"][0]["size_bytes"] -= 1
        self.manifest["binaries"][0]["pe"]["image_base"] += 0x1000
        with self.assertRaises(pe.UnsupportedBinaryError):
            pe.validate_identity(self.data, self.manifest)

    def test_malformed_hash_identity_cannot_bypass_parser(self):
        data = changed(self.data, 0xA04, "<I", 0)
        self.manifest["binaries"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaises(pe.PEError):
            pe.validate_identity(data, self.manifest)

    def test_invalid_manifest_fields(self):
        cases = [
            lambda value: value.update(schema_version=True),
            lambda value: value.update(game="mw4"),
            lambda value: value.update(binaries={}),
            lambda value: value["binaries"][0].update(sha256="0" * 63),
            lambda value: value["binaries"][0].update(sha256="A" * 64),
            lambda value: value["binaries"][0].update(size_bytes=True),
            lambda value: value["binaries"][0].update(filename="../fixture.exe"),
            lambda value: value["binaries"][0].update(filename="C:\\fixture.exe"),
            lambda value: value["binaries"][0].update(notes="not a list"),
            lambda value: value["binaries"][0].update(unknown=True),
            lambda value: value["binaries"][0]["pe"].update(machine=0x8664),
            lambda value: value["binaries"].append(value["binaries"][0].copy()),
        ]
        for change in cases:
            with self.subTest(change=change):
                self.manifest = {"schema_version": 1, "game": "mw3", "binaries": [record_for(self.data)]}
                change(self.manifest)
                self.write_manifest()
                with self.assertRaises(pe.ManifestError):
                    pe.load_manifest(self.manifest_path)

    def test_duplicate_json_keys_and_malformed_json_fail(self):
        for text in ('{"schema_version":1,"schema_version":1,"game":"mw3","binaries":[]}', "not json"):
            self.manifest_path.write_text(text, encoding="utf-8")
            with self.assertRaises(pe.ManifestError):
                pe.load_manifest(self.manifest_path)

    def test_output_cannot_overwrite_source_or_manifest(self):
        for output in (self.binary, self.manifest_path):
            before = output.read_bytes()
            result = self.run_cli("tools/analysis/analyze.py", "--output", str(output))
            self.assertEqual(result.returncode, 3)
            self.assertEqual(output.read_bytes(), before)

    def test_analysis_file_output_and_missing_file_errors(self):
        output = self.folder / "nested/report.json"
        result = self.run_cli("tools/analysis/analyze.py", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["sha256"], hashlib.sha256(self.data).hexdigest())
        self.binary.unlink()
        self.assertEqual(self.run_cli("tools/binary-validator/validate.py").returncode, 4)
        self.assertEqual(self.run_cli("tools/analysis/analyze.py").returncode, 4)

    def test_invalid_manifest_never_silently_becomes_unknown_binary(self):
        self.manifest_path.write_text("{}", encoding="utf-8")
        self.assertEqual(self.run_cli("tools/analysis/analyze.py").returncode, 3)

    def test_read_file_size_limit(self):
        with patch.object(pe, "MAX_FILE_BYTES", 8), self.assertRaises(pe.PEError):
            pe.read_binary(self.binary)

    def test_disassembler_missing_dependency(self):
        output = self.folder / "disassembly.txt"
        with patch.object(disassemble.shutil, "which", return_value=None):
            with patch("sys.stderr"):
                result = disassemble.main([str(self.binary), "--output", str(output)])
        self.assertEqual(result, 3)
        self.assertFalse(output.exists())

    def test_disassembler_passes_only_executable_sections_without_shell(self):
        output = self.folder / "disassembly.txt"

        def fake_run(command, **kwargs):
            self.assertIn("--section=.text", command)
            self.assertNotIn("--section=.rdata", command)
            self.assertNotIn("shell", kwargs)
            self.assertIn("--no-show-raw-insn", command)
            self.assertNotIn("--", command)
            self.assertEqual(command[-1], str(self.binary.resolve()))
            kwargs["stdout"].write(b"test disassembly\n")
            return subprocess.CompletedProcess(command, 0, stderr=b"")

        with patch.object(disassemble.shutil, "which", return_value="llvm-objdump"), patch.object(disassemble.subprocess, "run", side_effect=fake_run), patch("sys.stdout"):
            result = disassemble.main([str(self.binary), "--output", str(output)])
        self.assertEqual(result, 0)
        self.assertIn("test disassembly", output.read_text(encoding="utf-8"))

    def test_failed_disassembly_preserves_previous_output(self):
        output = self.folder / "disassembly.txt"
        output.write_text("prior output", encoding="utf-8")
        with patch.object(disassemble.shutil, "which", return_value="llvm-objdump"), patch.object(disassemble.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, stderr=b"failure")), patch("sys.stderr"):
            result = disassemble.main([str(self.binary), "--output", str(output)])
        self.assertEqual(result, 3)
        self.assertEqual(output.read_text(encoding="utf-8"), "prior output")
        self.assertEqual(list(self.folder.glob("disassembly-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
