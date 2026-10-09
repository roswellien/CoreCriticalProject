"""Round-trip and corruption checks for authored movie download packages."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/asset-inventory'))
import package_movie_download as package


class MoviePackageTests(unittest.TestCase):
    def make_package(self, root, basename=None):
        source = root / 'authored.bin'
        source.write_bytes(bytes(range(35)))
        output = root / 'package'
        argv = ['package', str(source), str(output)] + (['--basename', basename] if basename else [])
        with patch.object(sys, 'argv', argv), \
             patch.object(package, 'PART_BYTES', 16), contextlib.redirect_stdout(io.StringIO()):
            package.main()
        return source, output

    def test_generated_joiner_round_trip_and_no_overwrite(self):
        local = ROOT / 'local/work-ahead'
        local.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as directory:
            source, output = self.make_package(Path(directory))
            joined = subprocess.run([sys.executable, str(output / 'reassemble.py')], capture_output=True)
            self.assertEqual(joined.returncode, 0, joined.stderr)
            self.assertEqual((output / 'opening-2160p-30fps.mp4').read_bytes(), source.read_bytes())
            repeated = subprocess.run([sys.executable, str(output / 'reassemble.py')], capture_output=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual((output / 'opening-2160p-30fps.mp4').read_bytes(), source.read_bytes())

    def test_corrupted_download_rejected_before_creating_movie(self):
        local = ROOT / 'local/work-ahead'
        local.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as directory:
            _, output = self.make_package(Path(directory))
            (output / 'opening-2160p-30fps.mp4.part002').write_bytes(b'corrupted')
            joined = subprocess.run([sys.executable, str(output / 'reassemble.py')], capture_output=True)
            self.assertNotEqual(joined.returncode, 0)
            self.assertFalse((output / 'opening-2160p-30fps.mp4').exists())

    def test_other_movie_names_round_trip(self):
        local = ROOT / 'local/work-ahead'
        local.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as directory:
            source, output = self.make_package(Path(directory), 'C2M1-2160p-30fps')
            joined = subprocess.run([sys.executable, str(output / 'reassemble.py')], capture_output=True)
            self.assertEqual(joined.returncode, 0, joined.stderr)
            self.assertEqual((output / 'C2M1-2160p-30fps.mp4').read_bytes(), source.read_bytes())


if __name__ == '__main__':
    unittest.main()
