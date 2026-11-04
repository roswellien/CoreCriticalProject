import unittest
import tempfile
import zipfile
from pathlib import Path

from editor.config import (
    is_game_installed,
    game_directory,
    tool_directory,
    detect_game_directory,
)
from package_studio import package_studio


class TestPackager(unittest.TestCase):
    def test_config_paths(self):
        # Tool directory should exist and have unzbd.exe
        tdir = tool_directory()
        self.assertTrue((tdir / "unzbd.exe").is_file(), f"unzbd.exe missing in {tdir}")
        self.assertTrue((tdir / "rezbd.exe").is_file(), f"rezbd.exe missing in {tdir}")

        # Game directory check
        gdir = game_directory()
        self.assertTrue(gdir.is_dir())
        self.assertTrue(is_game_installed())

    def test_package_studio_lightweight(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            zip_path = package_studio(mode="lightweight", version="9.9.9", output_dir=out_dir)
            self.assertTrue(zip_path.is_file())
            self.assertGreater(zip_path.stat().st_size, 1000000)

            # Check contents of the zip
            with zipfile.ZipFile(zip_path, "r") as z:
                names = z.namelist()
                self.assertTrue(any("Launch-Mod-Studio.cmd" in n for n in names))
                self.assertTrue(any("run_studio.py" in n for n in names))
                self.assertTrue(any("bin/unzbd.exe" in n for n in names))
                self.assertTrue(any("bin/rezbd.exe" in n for n in names))
                self.assertTrue(any("editor/web/index.html" in n for n in names))
                self.assertTrue(any("README.txt" in n for n in names))


if __name__ == "__main__":
    unittest.main()
