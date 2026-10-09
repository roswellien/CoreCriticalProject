"""Independent channel/alpha and PNG checks with authored package fixtures."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
import zlib

tool_dir = Path(__file__).resolve().parents[1] / "tools/asset-inventory"
spec = importlib.util.spec_from_file_location("probe", tool_dir / "probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
sys.modules["probe"] = probe
spec = importlib.util.spec_from_file_location("asset_decoder", tool_dir / "decode_images.py")
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)


def fixture(flags=5, colors=(0xF800, 0x07E0, 0x001F, 0x0000), alpha=b"", tail=b""):
    return (struct.pack("<6I", 0, 1, 0, 1, 0, 0)
            + struct.pack("<32sII", b"authored", 64, 0xFFFFFFFF)
            + struct.pack("<IHHIHH", flags, 2, 2, 0, 0, 0)
            + struct.pack("<4H", *colors) + alpha + tail)


class DecoderTests(unittest.TestCase):
    def decode_fixture(self, data):
        entry = probe.image_table(data)["entries"][0]
        return decoder.decode(data, entry)[1]

    def test_primary_colors_opaque_black_and_row_order(self):
        rgba = self.decode_fixture(fixture())
        self.assertEqual(rgba, bytes((255, 0, 0, 255, 0, 255, 0, 255,
                                     0, 0, 255, 255, 0, 0, 0, 255)))

    def test_keyed_black_only(self):
        rgba = self.decode_fixture(fixture(3, (0, 1, 0x20, 0x800)))
        self.assertEqual(rgba[3::4], bytes((0, 255, 255, 255)))

    def test_alpha_plane_preserves_values(self):
        rgba = self.decode_fixture(fixture(11, alpha=bytes((0, 64, 128, 255))))
        self.assertEqual(rgba[3::4], bytes((0, 64, 128, 255)))
        self.assertEqual(rgba[:3], bytes((255, 0, 0)))

    def test_channel_rounding_and_endpoints(self):
        rgba = self.decode_fixture(fixture(colors=(0xFFFF, 0x0841, 0x8420, 0)))
        self.assertEqual(rgba[:3], bytes((255, 255, 255)))
        self.assertEqual(rgba[4:7], bytes((8, 8, 8)))
        self.assertEqual(rgba[8:11], bytes((132, 134, 0)))

    def test_unknown_flags_lengths_and_palette_fail(self):
        for data in (fixture(7), fixture(11), fixture(tail=b"extra")):
            with self.assertRaises(ValueError):
                self.decode_fixture(data)
        for pos, value in ((76, 1), (78, 1), (68, 0)):
            data = bytearray(fixture())
            struct.pack_into("<H", data, pos, value)
            with self.assertRaises(ValueError):
                self.decode_fixture(data)

    def test_package_header_rejected(self):
        data = bytearray(fixture())
        struct.pack_into("<I", data, 8, 1)
        with self.assertRaises(ValueError):
            decoder.inspect_package(data)

    def test_png_crc_dimensions_and_exact_scanlines(self):
        rgba = self.decode_fixture(fixture())
        png = decoder.png_bytes(2, 2, rgba)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        pos, chunks = 8, []
        while pos < len(png):
            size = struct.unpack_from(">I", png, pos)[0]
            kind = png[pos + 4:pos + 8]
            payload = png[pos + 8:pos + 8 + size]
            crc = struct.unpack_from(">I", png, pos + 8 + size)[0]
            self.assertEqual(crc, zlib.crc32(kind + payload))
            chunks.append((kind, payload))
            pos += 12 + size
        self.assertEqual([c[0] for c in chunks], [b"IHDR", b"IDAT", b"IEND"])
        self.assertEqual(struct.unpack(">IIBBBBB", chunks[0][1]), (2, 2, 8, 6, 0, 0, 0))
        self.assertEqual(zlib.decompress(chunks[1][1]), b"\0" + rgba[:8] + b"\0" + rgba[8:])


if __name__ == "__main__":
    unittest.main()
