import unittest
import numpy as np
from PIL import Image
from feature_relief import feature_relief


class FeatureTests(unittest.TestCase):
    def recipe(self, **kwargs):
        return dict(features=[], micro_gain=0.0, depth_ratio=0.01, slope_limit=0.4, **kwargs)

    def pixels(self, image, recipe):
        normal, _, _ = feature_relief(image, recipe)
        return np.frombuffer(normal[2], dtype="uint8").reshape(image.height, image.width, 4)

    def test_painted_stripe_is_not_a_structural_ridge(self):
        image = np.full((64, 64, 3), 220, dtype="uint8")
        image[20:35] = [160, 10, 10]
        recipe = self.recipe(paint_boundaries=[dict(shape="rect", points=[[0, 0.25], [1, 0.65]])])
        recipe["micro_gain"] = 0.2
        self.assertTrue(np.all(self.pixels(Image.fromarray(image), recipe) == [128, 128, 255, 255]))

    def test_glass_is_flat_with_grain_and_adjacent_structure(self):
        image = Image.fromarray(
            np.random.default_rng(5).integers(0, 256, (64, 64, 3), dtype="uint8")
        )
        r = self.recipe(flat_regions=[dict(shape="rect", points=[[0.2, 0.2], [0.8, 0.8]])])
        r["micro_gain"] = 0.2
        r["features"] = [
            dict(shape="line", points=[[0.1, 0.2], [0.9, 0.2]], height=0.1, width=0.06)
        ]
        self.assertTrue(np.all(self.pixels(image, r)[14:50, 14:50] == [128, 128, 255, 255]))

    def test_structure_survives_uniform_albedo(self):
        r = self.recipe()
        r["features"] = [dict(shape="rect", points=[[0.3, 0.3], [0.7, 0.7]], height=0.08)]
        pixels = self.pixels(Image.new("RGB", (64, 64), (128, 128, 128)), r)
        self.assertTrue(np.any(pixels[:, :, :2] != 128))
        self.assertTrue(np.all(pixels[:2] == [128, 128, 255, 255]))

    def test_invalid_uvs_fail(self):
        r = self.recipe()
        r["features"] = [dict(shape="line", points=[[-0.1, 0.3], [0.7, 0.7]], height=0.08)]
        with self.assertRaises(ValueError):
            self.pixels(Image.new("RGB", (64, 64)), r)

    def test_grain_mask_preserves_authored_geometry(self):
        random = Image.fromarray(
            np.random.default_rng(7).integers(0, 256, (64, 64, 3), dtype="uint8")
        )
        recipe = self.recipe()
        recipe["micro_gain"] = 0.2
        recipe["features"] = [dict(shape="rect", points=[[0.3, 0.3], [0.7, 0.7]], height=0.08)]
        masked, _, _ = feature_relief(random, recipe, grain_mask=np.zeros((64, 64), dtype=bool))
        plain, _, _ = feature_relief(Image.new("RGB", (64, 64), (128, 128, 128)), recipe)
        self.assertEqual(masked, plain)
        self.assertTrue(any(v != 128 for v in masked[2][::4]))
        with self.assertRaises(ValueError):
            feature_relief(random, recipe, grain_mask=np.zeros((32, 32), dtype=bool))


if __name__ == "__main__":
    unittest.main()
