"""Asset-free resource contract and unsigned community-pack checks."""
import json
import unittest

from content_capabilities import advertised, require
import test_prepared_mech_packs as mech_fixtures
import test_prepared_environment_packs as environment_fixtures


class ContentCapabilityTests(unittest.TestCase):
    def test_legacy_skins_need_the_independent_coordinator_capability(self):
        payload = {'profile': 'additional-chassis-v1', 'required_capabilities': {
            'additional-mech-chassis': 3, 'legacy-mech-skins': 1}}
        host = {'content_capabilities': {'additional-mech-chassis': [1, 2, 3]}}
        with self.assertRaisesRegex(ValueError, 'legacy-mech-skins'):
            require(host, payload, 'community.legacy')
        host['content_capabilities']['legacy-mech-skins'] = [1]
        require(host, payload, 'community.legacy')

    def test_no_publisher_or_executable_identity_requirement(self):
        host = {'executable_sha256': 'b' * 64, 'content_capabilities': {'ui-artwork': [1]}}
        for payload in ({'profile': 'prepared-ui-v1'},
                        {'profile': 'prepared-ui-v1', 'reference_host_sha256': 'unrelated provenance'}):
            require(host, payload, 'community.hud')

    def test_missing_versions_and_pack_self_authorization(self):
        payload = {'profile': 'prepared-ui-v1', 'required_capabilities': {'ui-artwork': 2},
                   'content_capabilities': {'ui-artwork': [1, 2]}}
        for declaration in ({}, {'ui-artwork': [1]}, {'ui-artwork': [2]}):
            with self.subTest(declaration=declaration), self.assertRaises(ValueError):
                require({'content_capabilities': declaration}, payload, 'community.hud')
        require({'content_capabilities': {'ui-artwork': [1, 2]}}, payload, 'community.hud')

    def test_malformed_and_unknown_contracts_fail_closed(self):
        for table in (None, [], {'ui-artwork': []}, {'ui-artwork': [True]},
                      {'ui-artwork': [1.0]}, {'ui-artwork': [-1]}, {'ui-artwork': [1, 1]}):
            with self.subTest(table=table), self.assertRaises(ValueError):
                advertised({'content_capabilities': table})
        for extra in (None, [], {'unknown': 1}, {'ui-artwork': True}, {'ui-artwork': 0}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                require({'content_capabilities': {'ui-artwork': [1]}},
                        {'profile': 'prepared-ui-v1', 'required_capabilities': extra}, 'bad')

    def test_appearances_are_an_independent_required_feature(self):
        payload = {'profile': 'additional-chassis-v1',
                   'required_capabilities': {'additional-mech-chassis': 3, 'mech-appearances': 1}}
        host = {'content_capabilities': {'additional-mech-chassis': [1, 2, 3]}}
        with self.assertRaises(ValueError):
            require(host, payload, 'community.mech')
        host['content_capabilities']['mech-appearances'] = [1]
        require(host, payload, 'community.mech')

    def test_explicit_table_overrides_legacy_including_empty(self):
        legacy = {'executable_sha256': 'dee5e15e02ae18539a3f5b7a89f1e1abac55a2afd964717c28fb900351f85f0a'}
        require(legacy, {'profile': 'prepared-ui-v1'}, 'old.hud')
        self.assertEqual(advertised(legacy | {'content_capabilities': {}}), {})
        with self.assertRaises(ValueError):
            require(legacy | {'content_capabilities': {}}, {'profile': 'prepared-ui-v1'}, 'old.hud')

    def test_community_models_without_reference_keep_format_and_binding_checks(self):
        fixture = mech_fixtures.PreparedPackTests(); fixture.setUp()
        try:
            root = fixture.build()
            path = root / 'pack.json'; manifest = json.loads(path.read_text())
            manifest['native_payload'].pop('reference_host_sha256')
            path.write_text(json.dumps(manifest))
            import prepared_mech_packs as packs
            host = fixture.host | {'executable_sha256': 'b' * 64}
            self.assertTrue(packs.compose([str(root)], host)[0])
            with self.assertRaises(ValueError):
                packs.compose([str(root)], host | {'mesh_payload_versions': [1]})
        finally:
            fixture.doCleanups()

    def test_community_environments_without_reference(self):
        import tempfile
        from pathlib import Path
        from prepared_environment_packs import select
        fixture = environment_fixtures.EnvironmentPackTests()
        with tempfile.TemporaryDirectory() as temp:
            root = fixture.fixture(Path(temp) / 'community')
            path = root / 'pack.json'; manifest = json.loads(path.read_text())
            manifest['native_payload'].pop('reference_host_sha256')
            path.write_text(json.dumps(manifest))
            self.assertIn('training', select([str(root)], fixture.host() | {'executable_sha256': 'b' * 64}))


if __name__ == '__main__':
    unittest.main()
