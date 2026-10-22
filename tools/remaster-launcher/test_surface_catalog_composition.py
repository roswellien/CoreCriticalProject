"""Regression checks for duplicate authored surface keys blocking native Training."""
from pathlib import Path
import tempfile
import unittest

from normal_materials import pack_surface_bindings, read_surface_bindings
from surface_catalog_composition import compose


class SurfaceCatalogCompositionTests(unittest.TestCase):
    def test_identical_duplicates_collapse_and_source_images_are_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = (1, 1, bytes([128, 128, 255, 255]))
            key = (1, 1, 1, 42)
            files = [root / "first.bin", root / "second.bin"]
            for file in files:
                file.write_bytes(pack_surface_bindings([(key, image)]))
            before = [file.read_bytes() for file in files]
            result = compose(files, root / "out")
            self.assertEqual((result["bindings"], result["duplicates"], result["resolved_conflicts"]), (1, 1, 0))
            page = Path(result["manifest"]).read_text().splitlines()[1]
            self.assertEqual(read_surface_bindings(Path(page).read_bytes()), [(key, image)])
            self.assertEqual([file.read_bytes() for file in files], before)

    def test_conflicting_pixels_require_exact_explicit_choice(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key = (1, 1, 1, 42)
            old = (1, 1, bytes([128, 128, 255, 255]))
            new = (1, 1, bytes([150, 128, 250, 255]))
            files = [root / "old.bin", root / "identical-old.bin", root / "new.bin"]
            for file, image in zip(files, [old, old, new]):
                file.write_bytes(pack_surface_bindings([(key, image)]))
            with self.assertRaises(ValueError): compose(files, root / "rejected")
            self.assertFalse((root / "rejected").exists())
            with self.assertRaises(ValueError): compose(files, root / "rejected", overrides={key: root / "unknown.bin"})
            result = compose(files, root / "out", overrides={key: files[-1]})
            self.assertEqual(result["resolved_conflicts"], 1)
            page = Path(result["manifest"]).read_text().splitlines()[1]
            self.assertEqual(read_surface_bindings(Path(page).read_bytes()), [(key, new)])


if __name__ == "__main__":
    unittest.main()
