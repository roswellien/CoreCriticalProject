"""Verify package closure and original separation using authored file fixtures."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from build_precompiled_update import package, pin


class PrecompiledUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mw34-precompiled-package-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / 'runtime'; self.runtime.mkdir()
        host = self.runtime / 'host.exe'; host.write_bytes(b'authored host; never executed')
        (self.runtime / 'runtime.json').write_text(json.dumps(dict(
            precompiled_runtime_version=1, files={'host.exe': pin(host)})))
        self.game = self.root / 'game'; self.game.mkdir()
        (self.game / 'MECH3.EXE').write_bytes(b'authored original; never executed')
        self.preparer = self.root / 'copy.exe'; self.preparer.write_bytes(b'authored copy tool fixture')

    def build(self, output=None):
        return package(self.runtime, self.preparer, self.game, output or self.root / 'update',
                       '1.2.3', 1, self.root / 'private.pem', 'fixture')

    def test_complete_precompiled_archive_uses_existing_protocol(self):
        with patch('build_precompiled_update.subprocess.run') as sign:
            receipt = self.build()
        self.assertFalse(receipt['generation_required'])
        self.assertEqual(receipt['original_images_included'], 0)
        manifest = json.loads((self.root / 'update/manifest.json').read_text())
        self.assertEqual(manifest['preparation_contract'], 'mw3-local-runtime-v1')
        self.assertEqual(manifest['original_inputs']['MECH3.EXE'], pin(self.game / 'MECH3.EXE'))
        with zipfile.ZipFile(self.root / 'update/1.2.3.zip') as archive:
            self.assertEqual(set(archive.namelist()), set(manifest['files']))
            self.assertEqual(archive.read('Runtime/host.exe'), (self.runtime / 'host.exe').read_bytes())
        sign.assert_called_once()
        self.assertTrue(str(sign.call_args.args[0][-1]).endswith('1.2.3.mw3update'))

    def test_descriptive_build_id_cannot_replace_release_version(self):
        with self.assertRaisesRegex(ValueError, 'public release version'):
            package(self.runtime, self.preparer, self.game, self.root / 'bad-update',
                    'mw3-feature-20261024-r1', 1, self.root / 'private.pem', 'fixture')
        self.assertFalse((self.root / 'bad-update').exists())

    def test_modified_missing_and_extra_runtime_members_rejected(self):
        host = self.runtime / 'host.exe'
        host.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.build()
        host.unlink()
        with self.assertRaises(ValueError): self.build()
        host.write_bytes(b'authored host; never executed')
        (self.runtime / 'unregistered').write_bytes(b'extra')
        with self.assertRaises(ValueError): self.build()

    def test_input_overlap_rejected_before_writing(self):
        with self.assertRaises(ValueError): self.build(self.runtime / 'update')
        self.assertFalse((self.runtime / 'update').exists())


if __name__ == '__main__':
    unittest.main()
