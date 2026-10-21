"""Protect atlas panels from lighting/height leakage across unrelated surfaces."""

import unittest
import numpy as np
from PIL import Image
from prepare_campaign_terrain_relief import atlas_relief


class AtlasTests(unittest.TestCase):
    recipe = dict(panels=[[0, 0, 0.5, 1], [0.5, 0, 1, 1]], depth_ratio=0.02, slope_limit=0.3)

    def normals(self, pixels):
        normal, _, _ = atlas_relief(Image.fromarray(pixels), self.recipe)
        return np.frombuffer(normal[2], dtype="uint8").reshape(64, 64, 4)

    def test_unrelated_flat_colors_do_not_create_ridge(self):
        image = np.full((64, 64, 3), 30, dtype="uint8")
        image[:, 32:] = 220
        self.assertTrue(np.all(self.normals(image) == [128, 128, 255, 255]))

    def test_neighbor_content_cannot_change_other_panel(self):
        rng = np.random.default_rng(7)
        image = rng.integers(0, 256, (64, 64, 3), dtype="uint8")
        before = self.normals(image).copy()
        image[:, :32] = 255 - image[:, :32]
        after = self.normals(image)
        self.assertTrue(np.array_equal(before[:, 32:], after[:, 32:]))
        self.assertFalse(np.array_equal(before[:, 2:30], after[:, 2:30]))

    def test_excluded_strip_stays_flat(self):
        image = Image.fromarray(
            np.random.default_rng(8).integers(0, 256, (64, 64, 3), dtype="uint8")
        )
        recipe = dict(self.recipe, panels=[[0.25, 0, 1, 1]])
        normal, _, _ = atlas_relief(image, recipe)
        pixels = np.frombuffer(normal[2], dtype="uint8").reshape(64, 64, 4)
        self.assertTrue(np.all(pixels[:, :18] == [128, 128, 255, 255]))

    def test_overlap_is_rejected(self):
        recipe = dict(self.recipe, panels=[[0, 0, 0.75, 1], [0.5, 0, 1, 1]])
        with self.assertRaises(ValueError):
            atlas_relief(Image.new("RGB", (64, 64)), recipe)


if __name__ == "__main__":
    unittest.main()
