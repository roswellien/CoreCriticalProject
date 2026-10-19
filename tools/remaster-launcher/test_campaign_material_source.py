import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np

from campaign_material_source import converted_color, read_variant
from normal_materials import pixel_hash


class CampaignSourceTests(unittest.TestCase):
    def test_alpha_thresholds_and_channel_positions(self):
        colors = np.array([0xf800, 0x07e0, 0x001f, 0xffff], dtype='uint32')
        alpha = np.array([0, 127, 128, 255], dtype='uint8')
        self.assertEqual(struct.unpack('<4H', converted_color(colors, alpha, 2)),
                         (0x7c00, 0x03e0, 0x801f, 0xffff))
        self.assertEqual(struct.unpack('<4H', converted_color(colors, alpha, 3)),
                         (0x0f00, 0x70f0, 0x800f, 0xffff))

    def test_separate_alpha_is_verified_and_retained(self):
        raw = struct.pack('<2H', 0xf800, 0x07e0)
        coverage = bytes([0, 255])
        converted = struct.pack('<2H', 0x7c00, 0x83e0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'upgraded.zbd'
            path.write_bytes(struct.pack('<IHHIHH', 43, 2, 1, 0, 0, 0) + raw + coverage)
            variant = dict(bank=str(path), offset=0, key=[2, 1, 2, pixel_hash(converted)],
                           source_rgb565_sha256=hashlib.sha256(raw).hexdigest(),
                           source_alpha_sha256=hashlib.sha256(coverage).hexdigest(),
                           converted_colour_sha256=hashlib.sha256(converted).hexdigest())
            image, alpha = read_variant(variant, pixel_hash)
            self.assertEqual(np.asarray(image).tolist(), [[[255, 0, 0], [0, 255, 0]]])
            self.assertEqual(np.asarray(alpha).tolist(), [[0, 255]])
            path.write_bytes(path.read_bytes()[:-1] + b'\x80')
            with self.assertRaisesRegex(ValueError, 'coverage changed'):
                read_variant(variant, pixel_hash)


if __name__ == '__main__':
    unittest.main()
