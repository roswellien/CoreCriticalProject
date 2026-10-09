"""Format-probe boundaries checked with project-authored byte sequences."""
import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location(
    "asset_probe", Path(__file__).resolve().parents[1] / "tools/asset-inventory/probe.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def image_fixture():
    return (struct.pack("<6I", 0, 1, 0, 1, 0, 0)
            + struct.pack("<32sII", b"authored", 64, 0xFFFFFFFF)
            + struct.pack("<IHHII", 5, 2, 2, 0, 0) + b"\0" * 8)


class ProbeTests(unittest.TestCase):
    def test_image_dimensions_and_span(self):
        result = module.image_table(image_fixture())
        self.assertEqual(result["exact_16bpp_spans"], 1)
        self.assertEqual(result["dimension_counts"], {"2x2": 1})

    def test_invalid_offsets_and_counts(self):
        for pos, value in ((12, 0xFFFFFFFF), (56, 4), (56, 1000)):
            data = bytearray(image_fixture())
            struct.pack_into("<I", data, pos, value)
            with self.assertRaises(ValueError):
                module.image_table(data)

    def test_riff_sequence_and_trailer(self):
        riff = b"RIFF" + struct.pack("<I", 14) + b"WAVEdata" + struct.pack("<I", 2) + b"\0\0"
        result = module.riff_streams(riff * 2 + b"authored trailer")
        self.assertEqual(result["stream_count"], 2)
        self.assertEqual(result["covered_bytes"], 44)
        self.assertEqual(result["trailing_bytes"], 16)

    def test_riff_bad_chunk_bounds(self):
        riff = b"RIFF" + struct.pack("<I", 12) + b"WAVEdata" + struct.pack("<I", 100)
        with self.assertRaises(ValueError):
            module.riff_streams(riff)


if __name__ == "__main__":
    unittest.main()
