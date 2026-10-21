"""Installer atomicity controls using authored host stand-ins, no game media."""
from pathlib import Path
import tempfile
import unittest
import apply_live_camera_isolation as adapter


class CameraInstallTests(unittest.TestCase):
    def test_unknown_photo_revision_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            host = Path(folder)
            photo = host / 'photo_replay_stage.inc'
            mfc = host / 'mfc_stage.hpp'
            photo.write_bytes(b'newer independent photo work')
            mfc.write_text('independent renderer work')
            with self.assertRaisesRegex(ValueError, 'Unknown photo'):
                adapter.apply(host)
            self.assertEqual(photo.read_bytes(), b'newer independent photo work')
            self.assertEqual(mfc.read_text(), 'independent renderer work')

    def test_missing_dispatch_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            host = Path(folder)
            photo = host / 'photo_replay_stage.inc'
            original = (adapter.SOURCE / photo.name).read_bytes()
            photo.write_bytes(original)
            (host / 'mfc_stage.hpp').write_text('unknown dispatch')
            with self.assertRaisesRegex(ValueError, 'Unknown distance'):
                adapter.apply(host)
            self.assertEqual(photo.read_bytes(), original)
            self.assertEqual((host / 'mfc_stage.hpp').read_text(), 'unknown dispatch')


if __name__ == '__main__':
    unittest.main()
