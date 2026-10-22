"""Exercise installed preparation without game bytes, replacement packs or Pillow."""
import tempfile
import unittest
from pathlib import Path

import native_assets
import prepared_environment_packs


class InstalledPreparationTests(unittest.TestCase):
    def test_no_optional_assets_leaves_native_original_archive_reader_enabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bindings = native_assets.prepare(root, [], output=root / "cache",
                                             allow_original_banks=True, use_development_banks=False)
            self.assertNotIn("MW34_REMASTER_BANKS", bindings)

    def test_empty_environment_selection_never_binds_invalid_zero_entry_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "environment"
            bindings = prepared_environment_packs.prepare({}, {"runtime_environment": {}}, output)
            self.assertNotIn("MW34_REMASTER_BANKS", bindings)
            self.assertFalse((output / "texture-banks.bin").exists())


if __name__ == "__main__":
    unittest.main()
