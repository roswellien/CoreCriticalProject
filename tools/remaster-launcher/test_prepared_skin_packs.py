import copy
import hashlib
import json
from pathlib import Path
import struct
import shutil
import unittest
import types
from unittest.mock import patch

import test_prepared_mech_packs as model_fixtures
import prepared_mech_packs as packs
import prepared_skin_packs as skins
import play_remaster


class SkinPackTests(unittest.TestCase):
    def setUp(self):
        fixture = model_fixtures.PreparedPackTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.base = fixture.build(skins=['d'])
        self.root = fixture.root
        self.host = fixture.host | dict(skin_ids={'orion': ['d']}, content_capabilities={
            'prepared-mechs': [1], 'additional-mech-skins': [1]})
        self.pack = self.root / 'skin'
        (self.pack/'skins').mkdir(parents=True)
        self.registry = dict(schema_version=2, payload_profile=skins.PROFILE, skins=[dict(
            id='test.sommerset:sommerset', name='Sommerset', chassis='orion',
            mesh_sha256={lod: hashlib.sha256((self.base/('payload/MW34_ORION'+suffix+'.bin')).read_bytes()).hexdigest()
                         for lod,suffix in [('close','_MESH'), ('distance','_LOD1_MESH')]},
            textures={'close':'texture.bin', 'distance':'texture.bin'})])
        # Valid project-authored BWTEX1: one batch, one 1x1 RGB565 material.
        self.pixels = b'BWTEX1\0\0'+struct.pack('<III',1,1,0)+b'Body'.ljust(32,b'\0')+struct.pack('<IIQH',1,1,1,0xffff)
        (self.pack/'texture.bin').write_bytes(self.pixels)
        self.save()

    def save(self):
        raw=json.dumps(self.registry).encode()
        (self.pack/skins.REGISTRY).write_bytes(raw)
        files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),**({'format':'BWTEX1'} if name.endswith('.bin') else {}))
               for name,data in [(skins.REGISTRY,raw),('texture.bin',self.pixels)]}
        self.manifest=dict(schema_version=2,id='test.sommerset',provides={'textures':True},files=files,native_payload=dict(
            profile=skins.PROFILE,registry=skins.REGISTRY,path_base='pack-root',required_formats=['BWTEX1'],
            required_capabilities={'additional-mech-skins':1}))
        (self.pack/'pack.json').write_text(json.dumps(self.manifest))

    def compose(self, roots=None, host=None):
        return packs.compose(roots or [str(self.base),str(self.pack)],host or self.host)

    def test_addition_keeps_all_original_bindings_and_order_is_independent(self):
        original, env = packs.compose([str(self.base)],self.host)
        records, added = self.compose()
        self.assertEqual(env,added)
        self.assertEqual(original[0]['environment'],records[0]['environment'])
        self.assertEqual(original[0]['skins'],records[0]['skins'])
        self.assertEqual(records[0]['additional_skins'][0]['name'],'Sommerset')
        reverse,_=self.compose([str(self.pack),str(self.base)])
        self.assertEqual(reverse,records)

    def test_disable_clears_catalog_and_additions(self):
        host=copy.deepcopy(self.host);host['runtime_environment']['MW34_ADDITIONAL_SKINS']='stale'
        records,env=self.compose([str(self.base)],host)
        self.assertNotIn(skins.CATALOG_KEY,env)
        self.assertNotIn('additional_skins',records[0])
        self.assertEqual(skins.write_catalog(records,self.root/'out'),{})

    def test_old_host_is_rejected(self):
        host=copy.deepcopy(self.host);del host['content_capabilities']['additional-mech-skins']
        with self.assertRaisesRegex(ValueError,'Update the game runtime'):self.compose(host=host)

    def test_missing_model_or_wrong_mesh_fails(self):
        with self.assertRaisesRegex(ValueError,'compatible'):self.compose([str(self.pack)])
        self.registry['skins'][0]['mesh_sha256']['distance']='0'*64;self.save()
        with self.assertRaisesRegex(ValueError,'distance mesh'):self.compose()

    def test_duplicate_identity_and_missing_lod_rejected(self):
        self.registry['skins']*=2;self.save()
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.compose()
        self.registry['skins']=self.registry['skins'][:1]
        del self.registry['skins'][0]['textures']['distance'];self.save()
        with self.assertRaisesRegex(ValueError,'both'):self.compose()

    def test_corruption_and_path_escape_rejected(self):
        (self.pack/'texture.bin').write_bytes(self.pixels[:-1]+b'x')
        with self.assertRaisesRegex(ValueError,'integrity'):self.compose()
        (self.pack/'texture.bin').write_bytes(self.pixels)
        self.registry['skins'][0]['textures']['close']='../outside.bin';self.save()
        with self.assertRaisesRegex(ValueError,'Undeclared'):self.compose()

    def test_catalog_and_no_code_or_base_replacements(self):
        records,_=self.compose()
        binding=skins.write_catalog(records,self.root/'out')
        blob=Path(binding[skins.CATALOG_KEY]).read_bytes()
        self.assertEqual(blob[:12],b'BWSKIN1\0'+struct.pack('<I',1))
        self.assertIn(b'Sommerset',blob)
        self.assertNotIn('mechs',self.manifest['provides'])

    def test_unseen_community_skin_is_discovered_without_any_code_registration(self):
        other=self.root/'community';shutil.copytree(self.pack,other)
        registry=copy.deepcopy(self.registry)
        registry['skins'][0].update(id='community.paint:night-watch',name='Night Watch')
        raw=json.dumps(registry).encode();(other/skins.REGISTRY).write_bytes(raw)
        manifest=copy.deepcopy(self.manifest);manifest['id']='community.paint'
        manifest['files'][skins.REGISTRY]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        (other/'pack.json').write_text(json.dumps(manifest))
        records,_=self.compose([str(self.pack),str(other),str(self.base)])
        self.assertEqual([s['name'] for s in records[0]['additional_skins']],['Sommerset','Night Watch'])
        blob=Path(skins.write_catalog(records,self.root/'both')[skins.CATALOG_KEY]).read_bytes()
        self.assertEqual(struct.unpack_from('<I',blob,8)[0],2)
        self.assertIn(b'community.paint:night-watch',blob)

    def test_catalog_reaches_the_actual_child_launch_profile(self):
        from native_assets import write_atomic
        models,bindings=self.compose()
        profile=dict(native=self.host|{'runtime_environment':dict(bindings)})
        planned=dict(backend='native',graphics=dict(width=1280,height=720,aa=1,af=1),supported=True,
                     texture_banks=0,models=models,offline_models=[],limitations=[],
                     command=['powershell.exe','-Profile','old.json'],music=None,
                     asset_output=str(self.root/'output'),prepared_profile=profile)
        assets=types.SimpleNamespace(prepare=lambda *a,**kw:dict(bindings),write_atomic=write_atomic)
        with (patch('sys.argv',['play_remaster']),patch.object(play_remaster,'plan',return_value=planned),
              patch.object(play_remaster,'read_json',return_value={'native':{'executable':'fixture.exe'}}),
              patch.dict('sys.modules',{'native_assets':assets}),
              patch.object(play_remaster.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)),
              patch.object(play_remaster.subprocess,'call',return_value=0) as child):
            self.assertEqual(play_remaster.main(),0)
        command=child.call_args.args[0]
        actual=json.loads(Path(command[command.index('-Profile')+1]).read_text())['native']['runtime_environment']
        self.assertIn(skins.CATALOG_KEY,actual)
        self.assertIn(b'test.sommerset:sommerset',Path(actual.pop(skins.CATALOG_KEY)).read_bytes())
        self.assertEqual(actual,bindings)


if __name__=='__main__':unittest.main()
