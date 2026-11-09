"""Exercise installed preparation without game bytes, replacement packs or Pillow."""
import tempfile
import unittest
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import native_assets
import prepared_environment_packs
import refresh_content_runtime
import stage_native_runtime
import test_prepared_environment_packs as environment_fixtures


class InstalledPreparationTests(unittest.TestCase):
    def test_staged_coordinator_prepares_without_the_development_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / 'authored-inputs'
            fixture.mkdir()
            host_file = fixture / 'host.bin'
            host_file.write_bytes(b'authored host fixture; never executed')
            snapshot = fixture / 'snapshot.json'
            snapshot.write_text('{}', encoding='utf-8')
            entry = fixture / 'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(b'authored entry fixture; never executed')
            (fixture / 'decoder.bin').write_bytes(b'authored decoder fixture; never executed')
            music = fixture / 'local/remaster/music.json'
            music.parent.mkdir(parents=True)
            music.write_text(json.dumps({'decoder': 'decoder.bin'}), encoding='utf-8')
            profile = fixture / 'profile.json'
            native = dict(executable=str(host_file),
                          executable_sha256=hashlib.sha256(host_file.read_bytes()).hexdigest(),
                          source_snapshot=str(snapshot), original_support_versions=[1],
                          content_capabilities={'environment-resources': [1]},
                          runtime_environment={'MW34_SEED': 'host', 'MW34_STARTUP': 'loader'})
            profile.write_text(json.dumps(dict(native=native, graphics={})), encoding='utf-8')
            python_home = fixture / 'empty-python-home'
            python_home.mkdir()
            staged = root / 'initial-runtime'
            with patch.object(stage_native_runtime, 'ROOT', fixture):
                stage_native_runtime.stage(profile, staged, python_home)
            refreshed = root / 'updated-runtime'
            refresh_content_runtime.stage(staged, refreshed, 'fixture-update')
            pack = environment_fixtures.EnvironmentPackTests().fixture(root / 'pack', world_format='BWSNR3')
            # -I excludes PYTHONPATH and the current checkout. Only the packaged
            # coordinator can supply producers/imports, including the codec.
            script = '''
import json, sys
from pathlib import Path
coordinator = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(coordinator))
from startup_cache import environment_resources
from prepared_environment_packs import select
host = dict(content_capabilities={'environment-resources': [1]},
            executable_sha256='a' * 64, runtime_environment={})
for index, chosen in enumerate(({}, select([sys.argv[2]], host))):
    cache = Path(sys.argv[3]) / str(index)
    first = environment_resources(chosen, host, cache)
    assert environment_resources(chosen, host, cache) == first
    if chosen:
        assert Path(first['MW34_REMASTER_BANKS']).is_file()
for name, module in tuple(sys.modules.items()):
    if name in ('startup_cache', 'normal_materials', 'normal_codec'):
        assert Path(module.__file__).resolve().parent == coordinator
'''
            for runtime in (staged, refreshed):
                with self.subTest(runtime=runtime.name):
                    result = subprocess.run(
                        [sys.executable, '-I', '-B', '-c', script,
                         str(runtime / 'coordinator'), str(pack), str(root / runtime.name / 'cache')],
                        cwd=root, capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
