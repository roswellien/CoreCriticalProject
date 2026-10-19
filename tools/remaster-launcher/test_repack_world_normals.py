import unittest

import normal_materials as catalog
from repack_world_normals import PAGE_BYTES, pages_for


class RepackTests(unittest.TestCase):
    def test_global_sharing_and_disabled_binding(self):
        a = (2, 2, bytes([128, 128, 255, 255]) * 4)
        b = (1, 4, a[2])  # Equal bytes with different layout must stay distinct.
        entries = [((2, 2, 1, i), [a, b, None][i % 3]) for i in range(600)]
        pages = list(pages_for(entries))
        restored = {}
        for page in pages:
            data = catalog.pack_surface_bindings(page)
            self.assertLessEqual(len(data), PAGE_BYTES)
            restored.update(catalog.read_surface_bindings(data))
        self.assertEqual(restored, dict(entries))
        # Each image/disabled group fits one page despite interleaved sources.
        self.assertEqual(len(pages), 3)

    def test_image_count_and_byte_limits(self):
        entries = [((1, 1, 1, i), (1, 1, bytes([i, 128, 255, 255]))) for i in range(65)]
        self.assertEqual([len(p) for p in pages_for(entries)], [64, 1])
        large = [(1024, 1024, bytes([i, 128, 255, 255]) * 1024**2) for i in range(4)]
        entries = [((1, 1, 1, i), normal) for i, normal in enumerate(large)]
        self.assertEqual([len(p) for p in pages_for(entries)], [3, 1])

    def test_duplicate_key_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            list(pages_for([((1, 1, 1, 1), None)] * 2))


if __name__ == '__main__':
    unittest.main()
