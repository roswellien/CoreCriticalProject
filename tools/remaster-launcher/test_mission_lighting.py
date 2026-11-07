"""Pack lighting selection, validation, relocation and native wire inputs."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

from mission_lighting import FIELDS, MISSIONS, encode, validate, apply_training
from prepared_environment_packs import select, prepare, sha, REGISTRY
import test_prepared_environment_packs as fixtures

AUTHORED = json.loads(Path(__file__).with_name('mission-lighting.json').read_text())['missions']


def attach(root, operation, ambient=None):
    data = dict(schema_version=1, missions={key: copy.deepcopy(AUTHORED[key]) for key in MISSIONS[operation]}, maps={})
    if ambient is not None: data['missions']['c1m1']['ambient_strength'] = ambient
    if operation == 'training':
        data['maps'] = {'BIG LAKE': dict(default='community', presets={'community': dict(
            azimuth=123, elevation=25, strength=.8, ambient=.2, sun_color=[1, .9, .7], ambient_color=[.8, .9, 1])})}
    path=root/'environment/lighting.json';path.write_text(json.dumps(data))
    manifest=json.loads((root/'pack.json').read_text()); registry=json.loads((root/REGISTRY).read_text())
    registry['lighting']='environment/lighting.json';(root/REGISTRY).write_text(json.dumps(registry))
    for name, fmt in ((REGISTRY,None),('environment/lighting.json','MW34-lighting-v1')):
        manifest['files'][name]=dict(bytes=(root/name).stat().st_size,sha256=sha(root/name))
        if fmt:manifest['files'][name]['format']=fmt
    manifest['native_payload']['required_formats'].append('MW34-lighting-v1')
    (root/'pack.json').write_text(json.dumps(manifest))
    return data


class MissionLightingTests(unittest.TestCase):
    def test_current_authored_values_and_wire(self):
        for operation in ('operation1','operation2','operation3','operation4'):
            validate(dict(schema_version=1,missions={key:AUTHORED[key] for key in MISSIONS[operation]},maps={}),operation)
        self.assertEqual(AUTHORED['c2m4']['ambient_strength'], .4)
        self.assertTrue(AUTHORED['c2m4']['is_interior'])
        self.assertTrue(AUTHORED['c1m3']['has_lightning'])
        raw=encode(AUTHORED)
        self.assertEqual(raw[:12], b'MW34ENV1'+struct.pack('<I',24))
        self.assertEqual([AUTHORED[f't1m{mission}']['elevation'] for mission in range(1, 5)], [6, 18, 58, 8])
        self.assertGreater(AUTHORED['t1m3']['rain_intensity'], .5)
        self.assertEqual([AUTHORED[f't1m{mission}']['rain_intensity'] for mission in (1, 2, 4)], [0, 0, 0])

    def test_conflict_relocation_disable_and_capability(self):
        fixture=fixtures.EnvironmentPackTests()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); first=fixture.fixture(root/'first','operation1');second=fixture.fixture(root/'second','operation1')
            attach(first,'operation1',.31);attach(second,'operation1',.61)
            moved=root/'relocated pack';first.rename(moved)
            host=fixture.host();host['mission_environment_versions']=[1]
            with self.assertRaisesRegex(ValueError, 'Conflicting environment region ownership'):
                select([str(moved),str(second)],host)
            chosen=select([str(moved)],host)
            self.assertEqual(chosen['operation1']['lighting']['missions']['c1m1']['ambient_strength'],.31)
            bindings=prepare(chosen,host,root/'output')
            self.assertEqual(Path(bindings['MW34_MISSION_ENVIRONMENTS']).read_bytes(),encode(chosen['operation1']['lighting']['missions']))
            host['runtime_environment']['MW34_MISSION_ENVIRONMENTS']='stale'
            self.assertNotIn('MW34_MISSION_ENVIRONMENTS',prepare({},host,root/'disabled'))
            with self.assertRaisesRegex(ValueError,'update the native runtime'):select([str(moved)],fixture.host())
            (moved/'environment/lighting.json').write_text('{}')
            with self.assertRaises(ValueError):select([str(moved)],host)

    def test_invalid_missions_and_numbers_fail(self):
        good=dict(schema_version=1,missions={key:copy.deepcopy(AUTHORED[key]) for key in MISSIONS['operation1']},maps={})
        for change in (lambda d:d['missions'].pop('c1m2'),
                       lambda d:d['missions']['c1m1'].update(ambient_strength=float('nan')),
                       lambda d:d['missions']['c1m1'].update(shadows=1),
                       lambda d:d['missions']['c1m1'].update(command='run.exe'),
                       lambda d:d['missions']['c1m1'].update(sun_color=[1,2]),
                       lambda d:d['missions']['c1m1'].update(horizon_low=.8,horizon_high=.2)):
            bad=copy.deepcopy(good);change(bad)
            with self.assertRaises(ValueError):validate(bad,'operation1')

    def test_repackaged_archive_installs_and_selects(self):
        from repackage_environment_lighting import build
        fixture=fixtures.EnvironmentPackTests()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);pack=fixture.fixture(root/'old-pack','operation1')
            executable=root/'host.exe';executable.write_bytes(b'authored host identity fixture')
            host=fixture.host();host.update(executable=str(executable),executable_sha256=sha(executable),mission_environment_versions=[1])
            manifest=json.loads((pack/'pack.json').read_text());manifest['native_payload']['reference_host_sha256']=host['executable_sha256'];(pack/'pack.json').write_text(json.dumps(manifest))
            catalog=root/'sun.json';catalog.write_text('{"maps":{}}');host['sun_preset']=dict(source=str(catalog))
            profile=root/'profile.json';profile.write_text(json.dumps(dict(native=host)))
            result=build([pack],profile,root/'output')
            installed=root/'installed'
            with zipfile.ZipFile(result[0]['path']) as archive:archive.extractall(installed)
            chosen=select([str(installed)],host)
            self.assertEqual(chosen['operation1']['lighting']['missions']['c1m1'],AUTHORED['c1m1'])
            self.assertTrue(json.loads((root/'output/packs.json').read_text())['verified'])

    @unittest.skipUnless(sys.platform=='win32','Uses the actual installed PowerShell resolver')
    def test_training_catalog_reaches_shared_resolver(self):
        fixture=fixtures.EnvironmentPackTests()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);pack=fixture.fixture(root/'training');attach(pack,'training')
            host=fixture.host();host['mission_environment_versions']=[1]
            native={'sun_preset':dict(source='missing-developer-file',map='BIG LAKE',default='night')}
            apply_training(select([str(pack)],host),native)
            self.assertEqual(native['sun_preset']['default'],'community')
            profile=root/'profile.json';profile.write_text(json.dumps(dict(native=native)))
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name('resolve_sun_preset.ps1')),
                '-Profile',str(profile),'-CatalogPath',native['sun_preset']['source'],'-MapName','BIG LAKE','-Preset','community'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['environment']['MW34_SUN_AZIMUTH'],'123')


if __name__=='__main__':unittest.main()
