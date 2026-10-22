"""Authored-only malformed-input checks for the native preparation boundary."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from export_recipe import components
from translate import resolve, source_span


class PreparationChecks(unittest.TestCase):
    def image(self):
        blob = bytearray(1024)
        struct.pack_into('<H', blob, 0, 0x5a4d)
        struct.pack_into('<I', blob, 0x3c, 0x80)
        blob[0x80:0x84] = b'PE\0\0'
        struct.pack_into('<HH', blob, 0x84, 0x14c, 1)
        struct.pack_into('<H', blob, 0x94, 224)
        struct.pack_into('<H', blob, 0x98, 0x10b)
        struct.pack_into('<I', blob, 0x98+28, 0x400000)
        section = 0x98+224
        struct.pack_into('<IIII', blob, section+8, 512, 0x1000, 512, 512)
        struct.pack_into('<I', blob, section+36, 0x60000020)
        blob[512:516] = b'TEST'
        return blob

    def test_only_raw_executable_section_is_read(self):
        blob = self.image()
        before = bytes(blob)
        self.assertEqual(source_span(blob, 0x401000, 0x401004), b'TEST')
        self.assertEqual(bytes(blob), before)
        for start, end in [(0x400fff, 0x401004), (0x401000, 0x401201), (0x401000, 0x401000)]:
            with self.assertRaises(ValueError):
                source_span(blob, start, end)

    def test_truncated_headers_nonexecutable_and_ambiguous_sections_reject(self):
        for count in (0, 32, 128, 300, 700):
            with self.assertRaises((ValueError, struct.error)):
                source_span(self.image()[:count], 0x401000, 0x401004)
        blob = self.image()
        section = 0x98+224
        struct.pack_into('<I', blob, section+36, 0x40000040)
        with self.assertRaises(ValueError):
            source_span(blob, 0x401000, 0x401004)
        blob = self.image()
        struct.pack_into('<H', blob, 0x86, 2)
        blob[section+40:section+80] = blob[section:section+40]
        with self.assertRaises(ValueError):
            source_span(blob, 0x401000, 0x401004)

    def test_storage_paths_reject_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(resolve(root, 'source/file.bin'), root / 'source/file.bin')
            for value in ('../escape', '/absolute', 'C:/drive', 'source\\file', 'a//b', './file'):
                with self.assertRaises(ValueError):
                    resolve(root, value)

    def test_report_reader_does_not_depend_on_large_layout_ledgers(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            expected = {'first': {'entry': 1}, 'last': {'entry': 2, 'layout': 'x' * 100000}}
            path.write_text(json.dumps({'provider': 'authored', 'components': expected, 'failed': {}}))
            self.assertEqual(dict(components(path)), expected)
            path.write_text('{"components":{"same":{},"same":{}}}')
            with self.assertRaises(ValueError):
                list(components(path))
            path.write_text('{"components":{"incomplete":')
            with self.assertRaises(ValueError):
                list(components(path))
            for invalid in ('{"components":{"a":{},}}', '{"components":{},}', '{"components":{}} true'):
                path.write_text(invalid)
                with self.assertRaises(ValueError):
                    list(components(path))

    def test_startup_extraction_has_no_historical_runtime_dependencies(self):
        from startup_adapters import extract
        source = extract(Path(__file__).resolve().parents[2])
        for text in ('ROOT', 'reports/', 'pack.bin', 'adaptation.json', 'layout.json'):
            self.assertNotIn(text, source)
        self.assertIn('original = (folder / \'guest.ll\').read_text()', source)
        self.assertIn('original = set(expected_pcs)', source)


if __name__ == '__main__':
    unittest.main()
