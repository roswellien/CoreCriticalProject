import struct
import unittest

from chassis_icons import append_icons, image, mask, MAGIC, WIDTH, HEIGHT


class ChassisIconsTests(unittest.TestCase):
    def fixture(self):
        pixels = bytes([255]) * (WIDTH * HEIGHT)
        payload = image(pixels, (0, 255, 0))
        bank = (struct.pack('<6I', 0, 1, 0, 1, 0, 0) +
                struct.pack('<32sII', b'icon_madcat_green', 64, 0xffffffff) + payload)
        return bank, MAGIC + struct.pack('<II', WIDTH, HEIGHT) + pixels

    def test_preserves_original_and_uses_original_resource_lookup(self):
        before, authored = self.fixture()
        after = append_icons(before, {'c123456789abc': authored})
        self.assertEqual(struct.unpack_from('<I', after, 12)[0], 5)
        old_name, offset, marker = struct.unpack_from('<32sII', after, 24)
        self.assertEqual(old_name.rstrip(b'\0'), b'icon_madcat_green')
        self.assertEqual(marker, 0xffffffff)
        self.assertEqual(after[offset:offset + len(before) - 64], before[64:])
        names = [struct.unpack_from('<32s', after, 24 + i * 40)[0].rstrip(b'\0') for i in range(5)]
        self.assertEqual(names[1:], [f'icon_c123456789abc_{s}'.encode() for s in ('green', 'grey', 'red', 'yellow')])

    def test_rejects_bad_masks_and_malformed_original(self):
        before, authored = self.fixture()
        for data in (authored[:-1], authored + b'x', authored[:16] + bytes(WIDTH * HEIGHT),
                     authored[:8] + struct.pack('<II', HEIGHT, WIDTH) + authored[16:]):
            with self.assertRaises(ValueError): mask(data)
        for data in (before[:24], before[:24] + bytes(40) + before[64:]):
            with self.assertRaises(ValueError): append_icons(data, {'c123456789abc': authored})
        with self.assertRaises(ValueError): append_icons(before, {'madcat': authored})


if __name__ == '__main__': unittest.main()
