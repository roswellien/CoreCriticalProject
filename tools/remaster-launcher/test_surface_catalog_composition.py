"""Regression checks for duplicate authored surface keys blocking native Training."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from normal_materials import (
    DecodedSurfaceBudgetExceeded,
    pack_surface_bindings,
    read_surface_bindings,
)
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

    def test_decoded_memory_budget_is_aggregated_before_retaining_each_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pixels = bytes([128, 128, 255, 255]) * 16
            other_pixels = bytes([127, 128, 255, 255]) * 16
            files = [root / "first.bin", root / "second.bin"]
            files[0].write_bytes(
                pack_surface_bindings(
                    [((4, 4, 1, 42), (4, 4, pixels))], compressed=True, cache_hashes=False
                )
            )
            files[1].write_bytes(
                pack_surface_bindings(
                    [((4, 4, 1, 43), (4, 4, other_pixels))],
                    compressed=True,
                    cache_hashes=False,
                )
            )
            with (
                patch("surface_catalog_composition.MAX_WORKING_BYTES", 255),
                self.assertRaises(DecodedSurfaceBudgetExceeded),
            ):
                compose(files, root / "out")

    def test_repacking_includes_both_catalog_headers_in_native_page_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.bin"
            page = pack_surface_bindings(
                [((1, 1, 1, 42), (1, 1, bytes([128, 128, 255, 255])))]
            )
            source.write_bytes(page)
            with (
                patch("surface_catalog_composition.MAX_NATIVE_PAGE_BYTES", len(page) - 1),
                self.assertRaisesRegex(ValueError, "native page budget"),
            ):
                compose([source], root / "out")


if __name__ == "__main__":
    unittest.main()
