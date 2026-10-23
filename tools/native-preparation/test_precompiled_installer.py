"""Authored inputs exercise the native copy tool without executing a game."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('MW34_PRECOMPILED_INSTALLER_TEST'), 'Select the built native copy tool')
class PrecompiledInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mw34-precompiled-copy-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tool = self.root / 'tool' / 'InstallPrecompiledRuntime.exe'
        self.tool.parent.mkdir()
        shutil.copy2(os.environ['MW34_PRECOMPILED_INSTALLER_TEST'], self.tool)
        self.runtime = self.tool.parent / 'Runtime'
        (self.runtime / 'bin').mkdir(parents=True)
        (self.runtime / 'runtime.json').write_text('authored manifest fixture')
        (self.runtime / 'bin' / 'host.exe').write_bytes(b'authored host fixture; never executed')
        self.game = self.root / 'game'; self.game.mkdir()
        (self.game / 'MECH3.EXE').write_bytes(b'authored original fixture; never executed')
        self.previous = self.root / 'previous'; self.previous.mkdir()
        (self.previous / 'sentinel').write_text('preserve previous version')

    def run_copy(self, output, extra=()):
        return subprocess.run([str(self.tool), '--game', str(self.game), '--output', str(output),
                               '--version', 'fixture-v1', '--previous', str(self.previous), *extra],
                              capture_output=True)

    def test_copy_retry_and_inputs_preserved(self):
        output = self.root / 'output'
        self.assertEqual(self.run_copy(output).returncode, 0)
        (output / 'bin' / 'host.exe').write_bytes(b'interrupted attempt')
        self.assertEqual(self.run_copy(output).returncode, 0)
        self.assertEqual((output / 'bin' / 'host.exe').read_bytes(),
                         (self.runtime / 'bin' / 'host.exe').read_bytes())
        self.assertEqual((self.previous / 'sentinel').read_text(), 'preserve previous version')
        self.assertEqual((self.game / 'MECH3.EXE').read_bytes(), b'authored original fixture; never executed')

    def test_overlap_and_unknown_arguments_fail(self):
        for output in (self.runtime / 'nested', self.game / 'nested', self.previous / 'nested', self.root):
            self.assertNotEqual(self.run_copy(output).returncode, 0)
        self.assertNotEqual(self.run_copy(self.root / 'output', ('--unexpected', 'bad')).returncode, 0)
        self.assertFalse((self.root / 'output').exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows junction fixture')
    def test_linked_output_rejected(self):
        import _winapi
        target = self.root / 'target'; target.mkdir()
        link = self.root / 'linked-output'
        _winapi.CreateJunction(str(target), str(link))
        self.assertNotEqual(self.run_copy(link).returncode, 0)
        self.assertEqual(list(target.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
