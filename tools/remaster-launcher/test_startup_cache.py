"""Cache reuse must preserve admission, content checks and complete resources."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from startup_cache import VerificationCache, environment_resources, cache_writer
from prepared_environment_packs import select, prepare
import test_prepared_environment_packs as environment_fixtures


class StartupCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixtures = environment_fixtures.EnvironmentPackTests()

    def test_verified_file_reuse_change_and_replacement(self):
        path = self.root / 'file.bin'
        path.write_bytes(b'good')
        digest = hashlib.sha256(b'good').hexdigest()
        first = VerificationCache(self.root)
        self.assertEqual(first.digest(path, digest), digest)
        first.save()
        second = VerificationCache(self.root)
        with patch('startup_cache.hashlib.file_digest', side_effect=AssertionError('Unchanged file was reread')):
            self.assertEqual(second.digest(path, digest), digest)
        self.assertEqual(second.reused, 1)
        previous = path.stat()
        replacement = self.root / 'replacement'
        replacement.write_bytes(b'evil')
        os.utime(replacement, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        os.replace(replacement, path)
        self.assertNotEqual(second.digest(path, digest), digest)

    def test_invalid_receipt_forces_full_check(self):
        (self.root / 'verified-pack-files-v1.json').write_text('broken')
        path = self.root / 'file'; path.write_bytes(b'ok')
        cache = VerificationCache(self.root)
        cache.digest(path, hashlib.sha256(b'ok').hexdigest())
        self.assertEqual(cache.hashed, 1)

    def test_warm_resources_reused_and_corrupt_output_rebuilt(self):
        pack = self.fixtures.fixture(self.root / 'pack')
        host = self.fixtures.host()
        chosen = select([str(pack)], host)
        first = environment_resources(chosen, host, self.root / 'cache')
        with patch('prepared_environment_packs.prepare', side_effect=AssertionError('Warm preparation repeated')):
            self.assertEqual(environment_resources(chosen, host, self.root / 'cache'), first)
        output = Path(first['MW34_REMASTER_BANKS'])
        output.write_bytes(b'bad')
        with patch('prepared_environment_packs.prepare', wraps=prepare) as rebuild:
            self.assertEqual(environment_resources(chosen, host, self.root / 'cache'), first)
            rebuild.assert_called_once()
        self.assertEqual(output.read_bytes()[:8], b'MWBANK1\0')

    def test_pack_admission_and_corruption_still_rejected_when_warm(self):
        pack = self.fixtures.fixture(self.root / 'pack')
        host = self.fixtures.host()
        cache = VerificationCache(self.root / 'cache')
        select([str(pack)], host, cache); cache.save()
        with self.assertRaises(ValueError):
            select([str(pack)], dict(executable_sha256='b'*64), VerificationCache(self.root / 'cache'))
        (pack / 'environment/bank.bin').write_bytes(b'X'*24)
        with self.assertRaises(ValueError):
            select([str(pack)], host, VerificationCache(self.root / 'cache'))

    def test_new_session_reuses_resources_with_fresh_launch_bindings(self):
        pack = self.fixtures.fixture(self.root / 'pack')
        host = self.fixtures.host()
        first_host = dict(host, runtime_environment={
            'MW34_FRAME_TIMES': 'session-a/times.txt', 'MW34_PERF_OVERLAY': '0',
            'MW34_INSTANT_REPLAY': '0'})
        chosen = select([str(pack)], first_host)
        first = environment_resources(chosen, first_host, self.root / 'cache')
        second_host = dict(host, launch_session_directory='session-b', graphics={'width': 1920},
                           runtime_environment={
            'MW34_FRAME_TIMES': 'session-b/times.txt', 'MW34_PERF_OVERLAY': '1',
            'MW34_INSTANT_REPLAY': '0'})
        with patch('prepared_environment_packs.prepare', side_effect=AssertionError('New session rebuilt images')):
            second = environment_resources(chosen, second_host, self.root / 'cache')
        self.assertEqual(first['MW34_REMASTER_BANKS'], second['MW34_REMASTER_BANKS'])
        self.assertEqual(second['MW34_FRAME_TIMES'], 'session-b/times.txt')
        self.assertEqual(second['MW34_PERF_OVERLAY'], '1')
        self.assertEqual(second['MW34_INSTANT_REPLAY'], '0')

    def test_selection_host_and_producer_changes_invalidate_resources(self):
        pack = self.fixtures.fixture(self.root / 'pack')
        host = self.fixtures.host(); chosen = select([str(pack)], host)
        first = environment_resources(chosen, host, self.root / 'cache')
        other = dict(host, authored_normal_catalog_budget_bytes=1000000)
        second = environment_resources(chosen, other, self.root / 'cache')
        self.assertNotEqual(first['MW34_REMASTER_BANKS'], second['MW34_REMASTER_BANKS'])
        actual = Path.read_bytes
        def changed(path):
            data = actual(path)
            return data + b'\n# changed producer' if path.name == 'mission_lighting.py' else data
        with patch.object(Path, 'read_bytes', changed):
            third = environment_resources(chosen, host, self.root / 'cache')
        self.assertNotEqual(first['MW34_REMASTER_BANKS'], third['MW34_REMASTER_BANKS'])
        disabled = environment_resources({}, host, self.root / 'cache')
        self.assertNotIn('MW34_REMASTER_BANKS', disabled)
        with patch('prepared_environment_packs.prepare', side_effect=AssertionError('Empty selection rebuilt')):
            self.assertEqual(environment_resources({}, host, self.root / 'cache'), disabled)

    def test_incomplete_attempt_and_concurrent_writer(self):
        with cache_writer(self.root / 'cache'):
            with self.assertRaises(RuntimeError):
                with cache_writer(self.root / 'cache'):
                    pass
        pack = self.fixtures.fixture(self.root / 'pack')
        host = self.fixtures.host(); chosen = select([str(pack)], host)
        with patch('prepared_environment_packs.prepare', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                environment_resources(chosen, host, self.root / 'cache')
        result = environment_resources(chosen, host, self.root / 'cache')
        self.assertTrue(Path(result['MW34_REMASTER_BANKS']).is_file())


if __name__ == '__main__':
    unittest.main()
