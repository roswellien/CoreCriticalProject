import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from build_chassis_pack import build
from prepared_chassis_packs import CAPABILITY, CATALOG_KEY, REGISTRY, definition, prepare, select, _banks
from legacy_chassis_skins import CAPABILITY as SKIN_CAPABILITY
from reader_archive import _directory
from zrd_document import decode, encode


def archive(members):
    payload, records = bytearray(), bytearray()
    for name, data in members.items():
        records += struct.pack('<II', len(payload), len(data)) + name.encode().ljust(64, b'\0') + bytes(range(76))
        payload += data
    return bytes(payload + records + struct.pack('<II', 1, len(members)))


class ChassisPackTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.host = dict(content_capabilities={CAPABILITY: [1]}, runtime_environment={})
        self.document = dict(schema_version=1, template='madcat', fields=dict(max_mass=75, clan=False))
        for name, data in [('mesh.bin', b'BWMESH4\0payload'), ('tex.bin', b'BWTEX1\0\0payload')]:
            (self.root / name).write_bytes(data)
        (self.root / 'definition.json').write_text(json.dumps(self.document))
        self.project = dict(pack_id='community.test', name='Test chassis', version='1.0.0', chassis=[dict(
            id='mech', name='Test Mech', metadata_template='orion', controller='madcat',
            definition='definition.json', meshes=dict(close='mesh.bin', distance='mesh.bin'),
            textures=dict(close='tex.bin', distance='tex.bin'))])
        (self.root / 'project.json').write_text(json.dumps(self.project))
        self.packfile = build(self.root / 'project.json', self.root / 'built')
        self.pack = self.root / 'built/pack'
        self.manifest = json.loads((self.pack / 'pack.json').read_text())

    def test_headlight_project_build_select_and_capability(self):
        lamp = dict(id='torso', space='guest_node', attachment='torso', position=[1,2,3],
                    direction=[0,0,-2], color=[1,1,1], intensity=2, range=50,
                    inner_angle=15, outer_angle=30)
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                project = self.legacy_project()[0] if legacy else self.root / 'project.json'
                data = json.loads(project.read_text())
                data['chassis'][0]['headlights'] = [lamp]
                project.write_text(json.dumps(data))
                output = self.root / ('lamp-legacy' if legacy else 'lamp-prepared')
                build(project, output)
                manifest = json.loads((output/'pack/pack.json').read_text())
                self.assertEqual(manifest['native_payload']['required_capabilities']['mech-headlights'], 1)
                host = dict(content_capabilities={CAPABILITY:[1,2,3]})
                if legacy:
                    host['content_capabilities'][SKIN_CAPABILITY] = [1]
                with self.assertRaisesRegex(ValueError, 'mech-headlights'):
                    select([(output/'pack',manifest)],host)
                host['content_capabilities']['mech-headlights'] = [1]
                records = select([(output/'pack',manifest)],host)
                actual = records[0]['registration']['headlights'][0]
                self.assertEqual(actual, dict(lamp, direction=[0,0,-1]))

    def selected(self):
        return select([(self.pack, self.manifest)], self.host)

    def registry(self, mutate):
        path = self.pack / REGISTRY
        data = json.loads(path.read_text()); mutate(data['chassis'][0])
        raw = json.dumps(data).encode(); path.write_bytes(raw)
        self.manifest['files'][REGISTRY] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def original(self, mass=75):
        return encode([['version', [2], 'max_mass', [float(mass)], 'clan', ['false'],
                        'skins', ['a', ['Default'], 'b', ['Other']]]])

    def test_unsigned_pack_has_stable_namespaced_identity(self):
        selected = self.selected()
        self.assertTrue(self.packfile.is_file())
        self.assertEqual(selected[0]['registration']['id'], 'community.test:mech')
        self.assertTrue(selected[0]['registration']['resource'].startswith('c'))
        self.assertEqual(self.selected(), selected)
        self.assertNotIn('signature', self.manifest)

    def legacy_project(self):
        """Small authored resources; no original game bytes in these fixtures."""
        from chassis_icons import MAGIC, image
        node = bytearray(352)
        node[:36] = b'mech_example.flt'.ljust(36, b'\0')
        struct.pack_into('<I', node, 36, 0x200)
        struct.pack_into('<I', node, 52, 5)
        struct.pack_into('<I', node, 60, 1)
        mesh = bytearray(92)
        struct.pack_into('<5I', mesh, 16, 1, 3, 0, 0, 0)
        polygon = struct.pack('<9I', 3, 0, 0, 0, 0, 0, 0, 0, 0)
        geometry = bytes(node + mesh) + bytes(36) + polygon + struct.pack('<3I', 0, 1, 2) + bytes(36)
        definition = [['max_mass', [100.0], 'weight_class', ['assault'], 'clan', ['false'],
                       'effect', ['exampleConcrete']]]
        files = {
            'node.bin': geometry,
            'material.bin': struct.pack('<I', 1) + bytes(40),
            'legacy-definition.zrd': encode(definition),
            'animation.zrd': encode([['ANIMATION', ['exampleConcrete']]]),
            'motion.bin': (struct.pack('<IfIIffI', 4, 1.0, 1, 1, -1.0, 1.0, 3)
                           + b'hip' + struct.pack('<I14f', 12, *([0.0] * 14))),
            'image.bin': image(bytes([255]) * 2050, (0, 255, 0)),
            'icon.bin': MAGIC + struct.pack('<II', 41, 50) + bytes([255]) * 2050,
        }
        for name, data in files.items():
            (self.root / name).write_bytes(data)
        descriptor = dict(schema_version=1, resource='example',
                          definition='legacy-definition.zrd', materials='material.bin',
                          silhouette='icon.bin', models=dict.fromkeys(('close', 'distance', 'cockpit'), 'node.bin'),
                          motions={'example_walk': 'motion.bin'},
                          animations={'example_prints.zrd': 'animation.zrd'},
                          textures={'example_skin': 'image.bin'})
        (self.root / 'legacy.json').write_text(json.dumps(descriptor))
        project = dict(pack_id='community.legacy', name='Legacy', version='1.0.0', chassis=[dict(
            id='mech', name='Example', metadata_template='annihilator', legacy='legacy.json')])
        path = self.root / 'legacy-project.json'
        path.write_text(json.dumps(project))
        return path, descriptor, definition

    def test_legacy_pack_requires_capability_and_preserves_stock_resources(self):
        from legacy_chassis_resources import image_members, members
        from prepared_mech_packs import compose
        project, descriptor, definition = self.legacy_project()
        build(project, self.root / 'legacy-built')
        pack = self.root / 'legacy-built/pack'
        manifest = json.loads((pack / 'pack.json').read_text())
        with self.assertRaisesRegex(ValueError, 'Update the game runtime'):
            select([(pack, manifest)], self.host)
        records = []
        models, environment = compose([str(pack)], dict(content_capabilities={CAPABILITY: [1, 2, 3]}),
                                      chassis_records=records)
        self.assertEqual(models, [])
        self.assertNotIn('visuals', records[0]['registration'])
        directory = self.root / 'legacy-game/zbd'
        directory.mkdir(parents=True)
        common = encode([['ANIMATION_DEFINITIONS', ['ANIMATION_LIST', ['ANIMATION_DEFINITION_FILE', ['stock.zrd']]]]])
        stock = {'reader.zbd': archive({'dfn_annihilator.zrd': encode(definition), 'commonAnim.zrd': common}),
                 'mechlib.zbd': archive({'materials': (self.root / 'material.bin').read_bytes(), 'stock.flt': b'unchanged'}),
                 'motion.zbd': archive({'stock_walk': b'unchanged motion'})}
        pixels = (self.root / 'image.bin').read_bytes()
        image_bank = struct.pack('<6I', 0, 1, 0, 1, 0, 0) + struct.pack('<32sII', b'stock', 64, 0xffffffff) + pixels
        stock.update({'rmechtex.zbd': image_bank, 'rimage.zbd': image_bank})
        for name, data in stock.items():
            (directory / name).write_bytes(data)
        bindings = prepare(records, directory.parent / 'Mech3.exe', self.root / 'legacy-out', environment)
        banks = _banks(bindings['MW34_REMASTER_BANKS'])
        generated = records[0]['registration']['resource']
        for name, data in stock.items():
            self.assertEqual((directory / name).read_bytes(), data)
            after = Path(banks['zbd/' + name]).read_bytes()
            if name in ('rimage.zbd', 'rmechtex.zbd'):
                self.assertEqual(image_members(after)['stock'], image_members(data)['stock'])
            else:
                for key, content in members(data).items():
                    if key not in ('materials', 'commonanim.zrd'):
                        self.assertEqual(members(after)[key], content)
        reader = members(Path(banks['zbd/reader.zbd']).read_bytes())
        motions = members(Path(banks['zbd/motion.zbd']).read_bytes())
        self.assertEqual(motions[generated + '_walk'], (self.root / 'motion.bin').read_bytes())
        library = members(Path(banks['zbd/mechlib.zbd']).read_bytes())
        model = library['mech_' + generated + '.flt']
        self.assertEqual(struct.unpack_from('<I', model, 352 + 92 + 36 + 28)[0], 1)
        self.assertIn('commonanim.zrd', reader)
        self.assertIn(generated + 'Concrete', str(decode(reader['dfn_' + generated + '.zrd'])))
        self.assertIn(('icon_' + generated + '_green'), image_members(Path(banks['zbd/rimage.zbd']).read_bytes()))

    def test_legacy_parser_rejects_malformed_payloads_and_undeclared_files(self):
        from legacy_chassis_resources import load, model, rewrite_archive
        _, descriptor, _ = self.legacy_project()
        originals = {path: (self.root / path).read_bytes()
                     for path in ('node.bin', 'material.bin', 'motion.bin', 'image.bin', 'icon.bin')}
        for path in originals:
            with self.subTest(payload=path):
                (self.root / path).write_bytes(originals[path][:-1])
                with self.assertRaises((ValueError, struct.error)):
                    load(descriptor, lambda name: (self.root / name).read_bytes())
                (self.root / path).write_bytes(originals[path])
        node = bytearray(originals['node.bin'][:352])
        struct.pack_into('<I', node, 36, 0x200)
        struct.pack_into('<I', node, 60, 1)
        mesh = bytearray(92)
        struct.pack_into('<I', mesh, 20, 100)
        with self.assertRaisesRegex(ValueError, 'mesh vectors'):
            model(bytes(node + mesh), 1)
        bad_normals = bytearray(originals['node.bin'])
        polygon_offset = 352 + 92 + 36
        struct.pack_into('<I', bad_normals, polygon_offset, 0x203)
        indices_end = polygon_offset + 36 + 12
        bad_normals[indices_end:indices_end] = struct.pack('<3I', *([0xffffffff] * 3))
        with self.assertRaisesRegex(ValueError, 'normal index'):
            model(bytes(bad_normals), 1)
        with self.assertRaisesRegex(ValueError, 'Colliding'):
            rewrite_archive(archive({'Stock': b'x'}), {'stock': b'y'})
        from prepare_legacy_chassis import source_members
        bank = bytearray(archive({'Stock': b'x'}))
        struct.pack_into('<I', bank, len(bank) - 12, 2)
        source = self.root / 'source.zbd'
        source.write_bytes(bank)
        self.assertEqual(source_members(source, 'mw'), {'stock': b'x'})
        source.write_bytes(bank[:-8] + struct.pack('<III', 2, 1, 0))
        self.assertEqual(source_members(source, 'pm'), {'stock': b'x'})
        for collision in ('example', 'example_walk', 'EXAMPLE_WALK'):
            duplicate = copy.deepcopy(descriptor)
            duplicate['textures'][collision] = 'image.bin'
            with self.assertRaisesRegex(ValueError, 'Colliding'):
                load(duplicate, lambda name: (self.root / name).read_bytes())
        descriptor['models']['close'] = '../escape.bin'
        (self.root / 'legacy.json').write_text(json.dumps(descriptor))
        with self.assertRaises(ValueError):
            build(self.root / 'legacy-project.json', self.root / 'unsafe-legacy')

    def test_silhouette_pack_requires_new_host_and_composes_named_images(self):
        from chassis_icons import MAGIC, image
        pixels = bytes([255]) * 2050
        (self.root / 'icon.bin').write_bytes(MAGIC + struct.pack('<II', 41, 50) + pixels)
        self.project['chassis'][0].update(silhouette='icon.bin', base_skin_name='Olive Drab')
        (self.root / 'icons-project.json').write_text(json.dumps(self.project))
        build(self.root / 'icons-project.json', self.root / 'icons')
        root = self.root / 'icons/pack'; manifest = json.loads((root / 'pack.json').read_text())
        with self.assertRaisesRegex(ValueError, 'Update the game runtime'):
            select([(root, manifest)], self.host)
        host = dict(content_capabilities={CAPABILITY: [1, 2]})
        selected = select([(root, manifest)], host)
        self.assertEqual(selected[0]['registration']['base_skin_name'], 'Olive Drab')
        game = self.game()
        original = (struct.pack('<6I', 0, 1, 0, 1, 0, 0) +
                    struct.pack('<32sII', b'icon_madcat_green', 64, 0xffffffff) + image(pixels, (0, 255, 0)))
        (game.parent / 'zbd/rimage.zbd').write_bytes(original)
        output = prepare(selected, game, self.root / 'icons-prepared', {})
        banks = _banks(output['MW34_REMASTER_BANKS'])
        generated = Path(banks['zbd/rimage.zbd']).read_bytes()
        self.assertIn(('icon_' + selected[0]['registration']['resource'] + '_green').encode(), generated)
        self.assertEqual(generated[224:224 + len(original) - 64], original[64:])

    def test_old_host_and_corruption_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Update the game runtime'):
            select([(self.pack, self.manifest)], dict(content_capabilities={}))
        target = self.pack / self.manifest['files'].keys().__iter__().__next__()
        target.write_bytes(b'x' * target.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.selected()

    def test_undeclared_path_duplicate_id_and_code_rejected(self):
        self.registry(lambda row: row['meshes'].update(close='../escape.bin'))
        with self.assertRaisesRegex(ValueError, 'Undeclared'):
            self.selected()
        self.registry(lambda row: row['meshes'].update(close=self.project['chassis'][0]['meshes']['close']))
        self.registry(lambda row: row.update(command='run.exe'))
        with self.assertRaisesRegex(ValueError, 'fields'):
            self.selected()

    def test_definition_preserves_types_and_omits_unprovided_stock_skins(self):
        result = decode(definition(self.document, self.original()))[0]
        self.assertIs(type(result[result.index('max_mass') + 1][0]), float)
        self.assertEqual(result[result.index('clan') + 1], ['false'])
        self.assertEqual(result[result.index('skins') + 1], ['a', ['Default']])
        for fields in (dict(command='run.exe'), dict(version=9), dict(skins=[])):
            with self.assertRaises(ValueError):
                definition({**self.document, 'fields': fields}, self.original())

    def game(self):
        directory = self.root / 'game/zbd'; directory.mkdir(parents=True)
        reader = archive({'dfn_madcat.zrd': self.original(), 'dfn_orion.zrd': self.original()})
        models = {}
        for suffix in ('', '_1', '_hud'):
            name = 'mech_madcat' + suffix + '.flt'
            data = bytearray(512); data[:32] = name.encode().ljust(32, b'\0')
            data[352:384] = b'madcat'.ljust(32, b'\0'); models[name] = bytes(data)
        (directory / 'reader.zbd').write_bytes(reader)
        (directory / 'mechlib.zbd').write_bytes(archive(models))
        return directory.parent / 'Mech3.exe'

    def test_private_resource_composition_preserves_every_original_member(self):
        game = self.game(); original = game.parent / 'zbd'
        bindings = prepare(self.selected(), game, self.root / 'prepared', {})
        self.assertEqual(Path(bindings[CATALOG_KEY]).read_bytes()[:8], b'MWCHAS2\0')
        banks = _banks(bindings['MW34_REMASTER_BANKS'])
        for name in ('reader.zbd', 'mechlib.zbd'):
            before, after = (original / name).read_bytes(), Path(banks['zbd/' + name]).read_bytes()
            _, old = _directory(before); _, new = _directory(after)
            self.assertEqual(new[:len(old)], old)
            for _, offset, size, _ in old:
                self.assertEqual(after[offset:offset + size], before[offset:offset + size])
        self.assertEqual(len(_directory(Path(banks['zbd/mechlib.zbd']).read_bytes())[1]), 6)

    def test_mass_mismatch_fails_and_disabling_has_no_resources(self):
        game = self.game(); records = self.selected()
        records[0]['definition']['fields']['max_mass'] = 80
        with self.assertRaisesRegex(ValueError, 'mass'):
            prepare(records, game, self.root / 'prepared', {})
        self.assertEqual(prepare([], game, self.root / 'disabled', {}), {})
        self.assertFalse((self.root / 'disabled').exists())

    def test_second_independent_pack_is_order_independent(self):
        project = copy.deepcopy(self.project)
        project.update(pack_id='another.example', name='Another')
        (self.root / 'second.json').write_text(json.dumps(project))
        build(self.root / 'second.json', self.root / 'other')
        other = self.root / 'other/pack'
        metadata = [(self.pack, self.manifest), (other, json.loads((other / 'pack.json').read_text()))]
        a, b = select(metadata, self.host), select(metadata[::-1], self.host)
        self.assertEqual(a, b)
        self.assertNotEqual(a[0]['registration']['resource'], a[1]['registration']['resource'])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            select(metadata + metadata[:1], self.host)

    def test_namespaced_chassis_skin_is_discovered_through_normal_composition(self):
        from prepared_mech_packs import compose
        from prepared_skin_packs import write_catalog, CATALOG_KEY as SKIN_KEY
        skin = self.root / 'community-paint'; (skin / 'skins').mkdir(parents=True)
        mesh_pin = hashlib.sha256((self.root / 'mesh.bin').read_bytes()).hexdigest()
        raw = json.dumps(dict(schema_version=2, payload_profile='prepared-skins-v1', skins=[dict(
            id='community.paint:new-look', name='New Look', chassis='community.test:mech',
            mesh_sha256=dict(close=mesh_pin, distance=mesh_pin),
            textures=dict(close='paint.bin', distance='paint.bin'))])).encode()
        pixels = b'BWTEX1\0\0paint'
        files = {}
        for name, data in [('skins/skins.json', raw), ('paint.bin', pixels)]:
            (skin / name).write_bytes(data)
            files[name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            if name.endswith('.bin'): files[name]['format'] = 'BWTEX1'
        manifest = dict(schema_version=2, game_id='mw3', id='community.paint', provides=dict(textures=True), files=files,
                        native_payload=dict(profile='prepared-skins-v1', registry='skins/skins.json', path_base='pack-root',
                                            required_formats=['BWTEX1'], required_capabilities={'additional-mech-skins': 1}))
        (skin / 'pack.json').write_text(json.dumps(manifest))
        host = copy.deepcopy(self.host); host['content_capabilities']['additional-mech-skins'] = [1]
        added = []; models, environment = compose([str(skin), str(self.pack)], host, chassis_records=added)
        self.assertEqual(models, [])
        self.assertEqual(added[0]['additional_skins'][0]['chassis'], 'community.test:mech')
        bindings = write_catalog(models + added, self.root / 'skins-out')
        self.assertIn(b'community.paint:new-look', Path(bindings[SKIN_KEY]).read_bytes())
        with self.assertRaisesRegex(ValueError, 'compatible'):
            compose([str(skin)], host, chassis_records=[])

    def test_generated_catalog_and_banks_reach_child_launch_profile(self):
        import types
        from unittest.mock import patch
        import play_remaster
        from native_assets import write_atomic
        game = self.game()
        game.write_bytes(b'fixture only')
        planned = dict(backend='native', graphics=dict(width=1280,height=720,aa=1,af=1), supported=True,
                       texture_banks=0, models=[], offline_models=[], limitations=[],
                       command=['powershell.exe','-Profile','old.json'], music=None,
                       asset_output=str(self.root/'output'), prepared_profile=dict(native=dict(runtime_environment={})),
                       chassis_records=self.selected())
        assets = types.SimpleNamespace(prepare=lambda *a,**kw: {}, write_atomic=write_atomic)
        with (patch('sys.argv',['play_remaster','--game-exe',str(game)]),
              patch.object(play_remaster,'plan',return_value=planned),
              patch.object(play_remaster,'read_json',return_value={'native':{'executable':'fixture.exe'}}),
              patch.dict('sys.modules',{'native_assets':assets}),
              patch.object(play_remaster.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)),
              patch.object(play_remaster.subprocess,'call',return_value=0) as child):
            self.assertEqual(play_remaster.main(),0)
        command = child.call_args.args[0]
        environment = json.loads(Path(command[command.index('-Profile')+1]).read_text())['native']['runtime_environment']
        self.assertTrue(Path(environment[CATALOG_KEY]).is_file())
        self.assertEqual(len(_banks(environment['MW34_REMASTER_BANKS'])),2)

    def test_additional_chassis_surface_materials_build_select_prepare_and_invalidation(self):
        import surface_materials
        mesh_out = bytearray(b'BWMESH4\0' + struct.pack('<IIII', 1, 1, 1, 0))
        mesh_out.extend(struct.pack('<5d', 1.0, 2.0, 3.0, 0.25, 0.5))
        mesh_out.extend(b'root'.ljust(32, b'\0') + b''.ljust(32, b'\0') + struct.pack('<i', -1))
        mesh_out.extend(struct.pack('<16f', 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1) * 2)
        mesh_out.extend(b'torso'.ljust(32, b'\0'))
        mesh_out.extend(struct.pack('<16f', 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1) * 2)
        mesh_out.extend(b'torso'.ljust(32, b'\0') + b'torso'.ljust(32, b'\0'))
        mesh_out.extend(struct.pack('<III', 0, 3, 0xFFFFFFFF))
        for idx in range(3):
            mesh_out.extend(struct.pack('<8f', float(idx), 0.0, 0.0, 0.0, 0.0, 1.0, 0.25 * idx, 0.5 * idx))
        tex_out = bytearray(b'BWTEX1\0\0' + struct.pack('<III', 1, 1, 0))
        tex_out.extend(b'armor_hull'.ljust(32, b'\0') + struct.pack('<IIQ', 1, 1, 0) + b'\x00\x7c')
        mesh_hash = surface_materials.mesh_uv_identity(bytes(mesh_out))
        sfm_close = surface_materials.pack_surface_materials(
            asset_id='community.surface:mech:close',
            mesh_uv_hash=mesh_hash,
            batch_materials=['armor_hull'],
            records=[{'asset_id': 'community.surface:mech:close', 'material_name': 'armor_hull'}],
        )
        sfm_dist = surface_materials.pack_surface_materials(
            asset_id='community.surface:mech:distance',
            mesh_uv_hash=mesh_hash,
            batch_materials=['armor_hull'],
            records=[{'asset_id': 'community.surface:mech:distance', 'material_name': 'armor_hull'}],
        )
        (self.root / 'sfm-mesh.bin').write_bytes(bytes(mesh_out))
        (self.root / 'sfm-tex.bin').write_bytes(bytes(tex_out))
        (self.root / 'sfm-close.bin').write_bytes(sfm_close)
        (self.root / 'sfm-dist.bin').write_bytes(sfm_dist)
        project = dict(
            pack_id='community.surface',
            name='Surface chassis',
            version='1.0.0',
            chassis=[dict(
                id='mech',
                name='Surface Mech',
                metadata_template='orion',
                controller='madcat',
                definition='definition.json',
                meshes=dict(close='sfm-mesh.bin', distance='sfm-mesh.bin'),
                textures=dict(close='sfm-tex.bin', distance='sfm-tex.bin'),
                surface_materials=dict(close='sfm-close.bin', distance='sfm-dist.bin'),
            )],
        )
        project_path = self.root / 'surface-project.json'
        project_path.write_text(json.dumps(project))
        build(project_path, self.root / 'surface-built')
        pack = self.root / 'surface-built/pack'
        manifest = json.loads((pack / 'pack.json').read_text())
        self.assertEqual(manifest['native_payload']['required_capabilities']['surface-materials'], 1)
        self.assertIn('BWSFM1', manifest['native_payload']['required_formats'])

        with self.assertRaisesRegex(ValueError, 'surface-materials'):
            select([(pack, manifest)], self.host)

        host = dict(content_capabilities={CAPABILITY: [1], 'surface-materials': [1]}, runtime_environment={})
        records = select([(pack, manifest)], host)
        self.assertIn('surface_materials', records[0])
        game = self.game()
        bindings = prepare(records, game, self.root / 'surface-prepared', {})
        resource_upper = records[0]['registration']['resource'].upper()
        self.assertTrue(Path(bindings[f'MW34_CHASSIS_{resource_upper}_SURFACE_MATERIALS']).is_file())
        self.assertTrue(Path(bindings[f'MW34_CHASSIS_{resource_upper}_LOD1_SURFACE_MATERIALS']).is_file())


if __name__ == '__main__':
    unittest.main()
