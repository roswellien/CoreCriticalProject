"""Asset-free lossless transport and malformed-stream regression checks."""
import random
import unittest

from normal_codec import encode, decode
from normal_materials import pack_surface_bindings, read_surface_bindings


class NormalCodecTests(unittest.TestCase):
    def test_exact_channels_and_run_boundaries(self):
        generator = random.Random(2781)
        for count in (1, 2, 31, 127, 128, 129, 512):
            for pixels in (bytes([128, 128, 255, 255]) * count,
                           generator.randbytes(count * 4),
                           bytes(range(256)) * count):
                self.assertEqual(decode(encode(pixels), len(pixels)), pixels)

    def test_flat_map_compresses_without_resampling(self):
        pixels = bytes([128, 128, 255, 255]) * (1024 * 1024)
        encoded = encode(pixels)
        self.assertLessEqual(len(encoded), len(pixels) // 32 + 16)
        self.assertEqual(decode(encoded, len(pixels)), pixels)

    def test_invalid_tokens_and_lengths_fail(self):
        for data, size in ((b"", 4), (b"\x80", 4), (b"\x03\x00", 4),
                           (b"\xff\x00", 4), (b"\x80\x00", 4),
                           (b"\x83\x00\x80\x00", 4), (b"\x83\x00", 3),
                           (b"\xc0\x01", 4), (b"\xc3\x00", 4)):
            with self.assertRaises(ValueError):
                decode(data, size)

    def test_surface_roundtrip_preserves_keys_exclusions_and_pixels(self):
        entries = [((16, 8, 1, 17), (16, 8, bytes([128, 127, 254, 255]) * 128)),
                   ((2, 2, 2, 91), None)]
        data = pack_surface_bindings(entries, compressed=True)
        self.assertTrue(data.startswith(b"BWSNR3\0\0"))
        self.assertEqual(read_surface_bindings(data), entries)
        for invalid in (data[:-1], data + b"x"):
            with self.assertRaises(ValueError):
                read_surface_bindings(invalid)


if __name__ == "__main__":
    unittest.main()
