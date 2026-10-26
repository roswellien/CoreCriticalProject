"""Stock/no-pack cleanup and graphics choice across real resource-cache reuse."""
from pathlib import Path
import copy
import hashlib
import struct
import tempfile
import unittest

from presentation_policy import apply, environment
from prepared_environment_packs import select
from startup_cache import environment_resources
from test_prepared_environment_packs import EnvironmentPackTests


class PresentationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / 'stock.bin'
        self.catalog.write_bytes(b'MWFX1\0\0\0' + struct.pack('<I', 1) +
            struct.pack('<IIIIQ6f', 1,1,1,1,123,8,2,.1,1,.5,.1))

    def host(self, enabled):
        host = EnvironmentPackTests().host()
        host.update(stock_presentation_versions=[1],
                    stock_effect_lighting=dict(catalog=str(self.catalog),
                        bytes=self.catalog.stat().st_size,
                        sha256=hashlib.sha256(self.catalog.read_bytes()).hexdigest()),
                    presentation=dict(schema_version=1,dynamic_lighting=enabled),
                    sun_preset={'source': 'stale-training.json'},
                    runtime_environment={'MW34_SUN':'1','MW34_SKY_TINT':'0,0,1',
                        'MW34_NIGHT_WORLD_GAIN':'.2','MW34_CAMPAIGN_LIGHTING':'1',
                        'MW34_MISSILE_EXHAUST':'1','MW34_WEATHER':'1',
                        'MW34_FIXTURE_SHADOWS':'1','MW34_SEH_LOG':'1'})
        return host

    def test_stock_clears_all_enhancements_and_old_training(self):
        host = self.host(False)
        host['runtime_environment'].update(MW34_EFFECT_LIGHT_CATALOG='stale.bin',
                                         MW34_MISSION_ENVIRONMENTS='stale.bin')
        apply(host,{})
        self.assertNotIn('sun_preset',host)
        env=host['runtime_environment']
        for flag in ['SUN','NORMAL_MAPS','EFFECT_LIGHTS','FIXTURE_LIGHTS','FIXTURE_SHADOWS',
                     'SUN_SHADOWS','WEATHER','CAMPAIGN_LIGHTING','MISSILE_EXHAUST',
                     'WATER_DETAIL','SURF_DETAIL','CLOUD_DETAIL']:
            self.assertEqual(env['MW34_'+flag],'0',flag)
        for resource in ['MW34_EFFECT_LIGHT_CATALOG','MW34_MISSION_ENVIRONMENTS','MW34_SKY_TINT']:
            self.assertNotIn(resource,env)
        self.assertEqual(env['MW34_NIGHT_WORLD_GAIN'],'1')
        self.assertEqual(env['MW34_SEH_LOG'],'1')

    def test_lighting_without_packs_uses_identity_receiver_and_stock_catalog(self):
        host=self.host(True);apply(host,{})
        env=host['runtime_environment']
        self.assertEqual(env['MW34_EFFECT_LIGHTS'],'1')
        self.assertEqual(env['MW34_EFFECT_LIGHT_CATALOG'],str(self.catalog.resolve()))
        self.assertEqual(env['MW34_SUN_STRENGTH'],'0')
        self.assertEqual(env['MW34_SUN_AMBIENT'],'1')
        self.assertEqual(env['MW34_CAMPAIGN_LIGHTING'],'1')
        self.assertEqual(env['MW34_WEATHER'],'1')
        self.assertNotIn('sun_preset',host)

    def test_pack_and_warm_cache_cannot_enable_disabled_lighting(self):
        fixture=EnvironmentPackTests();pack=fixture.fixture(self.root/'pack')
        off=self.host(False);selected=select([str(pack)],off)
        original=copy.deepcopy(off)
        first=environment_resources(selected,off,self.root/'cache')
        self.assertEqual(first['MW34_EFFECT_LIGHTS'],'0')
        self.assertNotIn('MW34_EFFECT_LIGHT_CATALOG',first)
        on=self.host(True)
        second=environment_resources(selected,on,self.root/'cache')
        self.assertEqual(second['MW34_EFFECT_LIGHTS'],'1')
        self.assertEqual(first['MW34_REMASTER_BANKS'],second['MW34_REMASTER_BANKS'])
        third=environment_resources(selected,off,self.root/'cache')
        self.assertEqual(third['MW34_EFFECT_LIGHTS'],'0')
        self.assertNotIn('MW34_EFFECT_LIGHT_CATALOG',third)
        self.assertEqual(off,original,'Resource preparation mutated launcher intent')
        disabled=environment_resources({},off,self.root/'cache')
        self.assertNotIn('MW34_REMASTER_BANKS',disabled)
        self.assertNotIn('MW34_SURFACE_NORMALS',disabled)
        self.assertEqual(disabled['MW34_SUN'],'0')

    def test_authored_normals_do_not_enable_normal_color_diagnostics(self):
        host = self.host(True)
        enabled = environment(host, {}, {'MW34_WORLD_NORMALS': 'world.txt',
                                        'MW34_SUN_NORMALS': '1'})
        self.assertEqual(enabled['MW34_NORMAL_MAPS'], '1')
        self.assertEqual(enabled['MW34_SUN_NORMALS'], '0')
        host['presentation']['dynamic_lighting'] = False
        disabled = environment(host, {}, enabled)
        self.assertEqual(disabled['MW34_NORMAL_MAPS'], '0')
        self.assertNotIn('MW34_SUN_NORMALS', disabled)

    def test_mission_catalog_requires_selected_pack_and_lighting_choice(self):
        selected={'operation1':{'registry':{'effects':'effect.bin'},
            'paths':{'effect.bin':str(self.catalog)},'lighting':{'missions':{'c1m1':{}}}}}
        bindings={'MW34_MISSION_ENVIRONMENTS':'selected.bin'}
        off=environment(self.host(False),selected,bindings)
        self.assertNotIn('MW34_MISSION_ENVIRONMENTS',off)
        on=environment(self.host(True),selected,bindings)
        self.assertEqual(on['MW34_CAMPAIGN_LIGHTING'],'1')
        self.assertEqual(on['MW34_MISSION_ENVIRONMENTS'],'selected.bin')
        no_pack=environment(self.host(True),{},bindings)
        self.assertNotIn('MW34_MISSION_ENVIRONMENTS',no_pack)

    def test_unknown_policy_and_missing_catalog_fail(self):
        host=self.host(False);host['presentation']['dynamic_lighting']='false'
        with self.assertRaises(ValueError):apply(host,{})
        host=self.host(True);host['stock_presentation_versions']=[]
        with self.assertRaises(ValueError):apply(host,{})
        host=self.host(True);self.catalog.write_bytes(b'bad')
        with self.assertRaises(ValueError):apply(host,{})
        # Off never requires optional lighting resources.
        apply(self.host(False),{})

    def test_shadows_are_a_separate_saved_choice(self):
        host=self.host(True);host['presentation']['shadows']=False;apply(host,{})
        self.assertEqual(host['runtime_environment']['MW34_FIXTURE_SHADOWS'],'0')
        host=self.host(True);host['presentation']['shadows']=True;apply(host,{})
        self.assertEqual(host['runtime_environment']['MW34_FIXTURE_SHADOWS'],'1')
        host['presentation']['dynamic_lighting']=False;apply(host,{})
        self.assertEqual(host['runtime_environment']['MW34_FIXTURE_SHADOWS'],'0')
        self.assertTrue(host['presentation']['shadows'],'Turning lighting off erased shadow preference')


if __name__=='__main__':unittest.main()
