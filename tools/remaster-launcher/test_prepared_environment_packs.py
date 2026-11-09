"""Asset-free checks of operation selection, relocation and disabled bindings."""
import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import weakref
from normal_materials import pack_surface_bindings,pixel_hash,read_surface_bindings
from normal_materials import DecodedSurfaceBudgetExceeded
import prepared_environment_packs
from prepared_environment_packs import select,prepare,profile_bindings,detail_metadata,encode_normal_pages,PROFILE,REGISTRY,REGIONS,sha

class EnvironmentPackTests(unittest.TestCase):
    def test_cache_admission_removal_and_duplicate_owner(self):
        from startup_cache import VerificationCache, environment_resources
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);one=self.fixture(root/'one');host=self.host();cache_root=root/'cache'
            cold=VerificationCache(cache_root)
            selected=select([str(one)],host,cold)
            environment_resources(selected,host,cache_root);cold.save()
            warm=VerificationCache(cache_root)
            select([str(one)],host,warm)
            self.assertGreater(warm.reused,0)
            two=self.fixture(root/'two')
            with self.assertRaisesRegex(ValueError,'region ownership'):
                select([str(one),str(two)],host,warm)
            (one/'environment/bank.bin').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                select([str(one)],host,warm)
            stock=environment_resources({},host,cache_root)
            self.assertNotIn('MW34_REMASTER_BANKS',stock)
            self.assertNotIn('MW34_WORLD_NORMALS',stock)
            self.assertNotIn('MW34_SURFACE_NORMALS',stock)

    def test_duplicate_region_ownership_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            one=self.fixture(Path(folder)/'one')
            two=self.fixture(Path(folder)/'two')
            with self.assertRaisesRegex(ValueError, 'region ownership'):
                select([str(one),str(two)],self.host())
            with self.assertRaisesRegex(ValueError, 'region ownership'):
                select([str(two),str(one)],self.host())

    def test_detail_pins_follow_selected_pack_revision(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.fixture(Path(t)/'current')
            chosen=select([str(root)],self.host())
            pins=detail_metadata(chosen)
            self.assertEqual(set(pins),{'water','surf','cloud'})
            for role,pin in pins.items():
                self.assertEqual(pin['sha256'],sha(Path(pin['path'])))
                self.assertEqual(pin['bytes'],Path(pin['path']).stat().st_size)
            self.assertEqual(detail_metadata({}),{})
    def fixture(
        self,
        root,
        operation='training',
        normal=b'\x80\x80\xff\xff',
        world_format='BWSNR2',
        world_normal=None,
        surface_hash=123,
    ):
        root.mkdir(); files={}
        def put(name,data,fmt=None):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            files[name]=dict(bytes=len(data),sha256=sha(p))
            if fmt:files[name]['format']=fmt
            return name
        bank=put('environment/bank.bin',struct.pack('<6I',0,1,0,1,0,0),'ZBD-texture-v1')
        reg=dict(schema_version=2,payload_profile=PROFILE,operation=operation,banks={f'zbd/{r}/{n}.zbd':bank for r in REGIONS[operation] for n in ['rtexture','rtexture2','rtexture3','texture','texture1','texture2']},detail={})
        data=pack_surface_bindings([((1,1,1,123),(1,1,normal))])
        world_data=pack_surface_bindings(
            [((1,1,1,surface_hash),(1,1,world_normal or normal))],
            compressed=world_format=='BWSNR3',
        )
        for role,magic in [('authored','MW34SNA1'),('world','MW34SNP1')]:
            page_data=world_data if role=='world' else data
            page_format=world_format if role=='world' else 'BWSNR2'
            reg[role]=[put('environment/'+role+'.bin',page_data,page_format)]
            reg[role+'_manifest']=put('environment/'+role+'.txt',(magic+'\n'+role+'.bin\n').encode(),magic)
        for role in ['water','surf','cloud']:reg['detail'][role]=put('environment/'+role+'-detail.bin',data,'BWSNR2')
        reg['effects']=put('environment/effects.bin',b'MWFX1\0\0\0'+struct.pack('<I',0),'MWFX1')
        if operation=='shared-mechs':
            reg['banks']={f'zbd/{n}.zbd':bank for n in ['rmechtex','rmechtex16']}
            reg={k:v for k,v in reg.items() if k in {'schema_version','payload_profile','operation','banks','authored','authored_manifest'}}
            used={bank,*reg['authored'],reg['authored_manifest']}
            files={k:v for k,v in files.items() if k in used}
        put(REGISTRY,json.dumps(reg).encode())
        manifest=dict(schema_version=2,id='test.'+root.name.replace(' ','-').lower(),native_payload=dict(profile=PROFILE,registry=REGISTRY,path_base='pack-root',reference_host_sha256='a'*64,required_formats=['BWSNR2']+(['BWSNR3'] if world_format=='BWSNR3' else [])),files=files)
        (root/'pack.json').write_text(json.dumps(manifest))
        return root
    def host(self):
        return dict(content_capabilities={'environment-resources':[1]},executable_sha256='a'*64,runtime_environment={'MW34_WORLD_NORMALS':'stale','MW34_REMASTER_BANKS':'stale','MW34_EFFECT_LIGHTS':'0','MW34_BUSHWACKER_TEST':'selected-mech','MW34_FIXTURE_LIGHT_RETAIN_DISTANCE':'160'})
    def test_relocation_selection_and_disable(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);one=self.fixture(root/'one');two=self.fixture(root/'two','operation4');moved=root/'relocated with spaces';one.rename(moved)
            chosen=select([str(moved),str(two)],self.host());self.assertEqual(set(chosen),{'training','operation4'})
            bindings=prepare(chosen,self.host(),root/'launch');self.assertEqual(bindings['MW34_BUSHWACKER_TEST'],'selected-mech')
            self.assertEqual(bindings['MW34_EFFECT_LIGHTS'],'1')
            self.assertTrue(Path(bindings['MW34_EFFECT_LIGHT_CATALOG']).is_file())
            self.assertEqual(bindings['MW34_FIXTURE_LIGHT_RETAIN_DISTANCE'],'160')
            raw=Path(bindings['MW34_REMASTER_BANKS']).read_bytes();self.assertEqual(struct.unpack('<I',raw[8:12])[0],18)
            pages=Path(bindings['MW34_SURFACE_NORMALS']);page=pages.parent/pages.read_text().splitlines()[1]
            self.assertEqual(len(read_surface_bindings(page.read_bytes())),1)
            empty=prepare({},self.host(),root/'disabled');self.assertNotIn('MW34_WORLD_NORMALS',empty);self.assertNotIn('MW34_REMASTER_BANKS',empty)
            self.assertEqual(empty['MW34_EFFECT_LIGHTS'],'0')
    def test_compressed_world_catalog_selection_and_repacking(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);pack=self.fixture(root/'compressed','operation2',world_format='BWSNR3')
            chosen=select([str(pack)],self.host())
            self.assertIn('operation2',chosen)
            output=root/'launch';env=prepare(chosen,self.host(),output)
            world_manifest=Path(env['MW34_WORLD_NORMALS'])
            world_name=world_manifest.read_text().splitlines()[1]
            page=(world_manifest.parent/world_name).read_bytes()
            self.assertEqual(page[:8],b'BWSNR3\0\0')
            self.assertEqual(len(read_surface_bindings(page)),1)
            entries=[((1,1,1,123),(1,1,b'\x80\x80\xff\xff'))]
            pages=list(encode_normal_pages(entries,world=True))
            self.assertEqual(pages[0][:8],b'BWSNR3\0\0')
    def test_decoded_source_page_budget_is_checked_before_decode(self):
        page=pack_surface_bindings([((1,1,1,123),(1,1,b'\x80\x80\xff\xff'))],compressed=True)
        with patch('normal_codec.decode',side_effect=AssertionError('Oversized image decoded')):
            with self.assertRaises(DecodedSurfaceBudgetExceeded):
                read_surface_bindings(page,max_decoded_bytes=3)
            with self.assertRaises(DecodedSurfaceBudgetExceeded):
                read_surface_bindings(page,max_working_bytes=11)
    def test_world_merge_flushes_before_decoding_remaining_budget(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            first=self.fixture(root/'first','operation1',world_format='BWSNR3',surface_hash=123)
            second=self.fixture(root/'second','operation2',world_format='BWSNR3',surface_hash=124)
            chosen=select([str(first),str(second)],self.host())
            output=root/'launch';output.mkdir()
            pixel_hash.cache_clear()
            source_pixel_reference=[None]
            read_count=[0]
            read_page=prepared_environment_packs.read_surface_bindings
            def track_source_pixels(data,**kwargs):
                read_count[0]+=1
                if read_count[0]==3:
                    self.assertIsNone(source_pixel_reference[0]())
                entries=read_page(data,**kwargs)
                if source_pixel_reference[0] is None:
                    key,value=entries[0]
                    pixels=memoryview(value[2])
                    source_pixel_reference[0]=weakref.ref(pixels)
                    return [(key,(value[0],value[1],pixels))]
                return entries
            with patch.object(prepared_environment_packs,'MERGED_NORMAL_DECODED_BYTES',15):
                with patch.object(
                    prepared_environment_packs,
                    'read_surface_bindings',
                    side_effect=track_source_pixels,
                ):
                    names,_,_=prepared_environment_packs.write_merged_normal_catalog(
                        chosen,'world',output
                    )
            self.assertEqual(len(names),2)
            self.assertIsNone(source_pixel_reference[0]())
            self.assertEqual(pixel_hash.cache_info().currsize,0)
            self.assertEqual(
                [len(read_surface_bindings((output/name).read_bytes())) for name in names],
                [1,1],
            )
    def test_world_merge_reuses_decoded_images_across_source_pages(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);page_names=[];paths={}
            for index in range(20):
                name=f'page-{index}.bin'
                path=root/name
                path.write_bytes(pack_surface_bindings(
                    [((1,1,1,index+1),(1,1,b'\x80\x80\xff\xff'))],
                    compressed=True,
                ))
                page_names.append(name);paths[name]=str(path)
            selected={'training':dict(registry={'world':page_names},paths=paths)}
            output=root/'launch';output.mkdir()
            captured=[];pack_page=pack_surface_bindings
            def capture_entries(entries,**kwargs):
                captured.extend(entries)
                return pack_page(entries,**kwargs)
            with patch.object(prepared_environment_packs,'MERGED_NORMAL_DECODED_BYTES',64):
                with patch.object(
                    prepared_environment_packs,'pack_surface_bindings',
                    side_effect=capture_entries,
                ):
                    prepared_environment_packs.write_merged_normal_catalog(
                        selected,'world',output
                    )
            canonical_image=captured[0][1]
            self.assertEqual(len(captured),20)
            self.assertTrue(all(value is canonical_image for _,value in captured))
    def test_shared_surface_conflict_uses_fixed_campaign_priority(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            op3=self.fixture(root/'op3','operation3',world_normal=b'\x81\x80\xff\xff')
            op2=self.fixture(root/'op2','operation2',world_normal=b'\x82\x80\xff\xff')
            chosen=select([str(op3),str(op2)],self.host())
            output=root/'launch';env=prepare(chosen,self.host(),output)
            manifest=Path(env['MW34_WORLD_NORMALS']);name=manifest.read_text().splitlines()[1]
            page=read_surface_bindings((manifest.parent/name).read_bytes())
            self.assertEqual(page[0][1][2],b'\x82\x80\xff\xff')
    def test_reject_bad_host_corruption_and_conflicts(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);one=self.fixture(root/'one');two=self.fixture(root/'two','operation1',b'\x90\x80\xff\xff')
            with self.assertRaises(ValueError):select([str(one)],dict(executable_sha256='b'*64))
            with self.assertRaises(ValueError):prepare(select([str(one),str(two)],self.host()),self.host(),root/'conflict')
            (one/'environment/bank.bin').write_bytes(b'bad')
            with self.assertRaises(ValueError):select([str(one)],self.host())
    def test_lighting_pack_admission_on_reviewed_cinematic_host(self):
        with tempfile.TemporaryDirectory() as t:
            pack=self.fixture(Path(t)/'lighting-base')
            manifest=json.loads((pack/'pack.json').read_text())
            manifest['native_payload']['reference_host_sha256']='0d3d920f6b560ddcd92fbeeb4034d59430ddd46a19b75269255fc8ec83fe12ef'
            (pack/'pack.json').write_text(json.dumps(manifest))
            host=self.host();host.pop('content_capabilities')
            for digest in ['9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83',
                           'c1afedadd8ed9e13a956db917a1a5335a6581fac01374b367969d4e985852115']:
                host['executable_sha256']=digest
                self.assertIn('training',select([str(pack)],host))
            host['executable_sha256']='b'*64
            with self.assertRaises(ValueError):select([str(pack)],host)

    def test_shared_mechs_own_only_global_banks_and_compose_with_operations(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);shared=self.fixture(root/'shared','shared-mechs');world=self.fixture(root/'world','operation2')
            moved=root/'moved shared pack';shared.rename(moved)
            chosen=select([str(moved)],self.host());env=prepare(chosen,self.host(),root/'alone')
            self.assertEqual(env['MW34_EFFECT_LIGHTS'],'0')
            self.assertNotIn('MW34_WORLD_NORMALS',env)
            self.assertIn('MW34_SURFACE_NORMALS',env)
            raw=Path(env['MW34_REMASTER_BANKS']).read_bytes();self.assertEqual(struct.unpack('<I',raw[8:12])[0],2)
            chosen=select([str(moved),str(world)],self.host());env=prepare(chosen,self.host(),root/'combined')
            self.assertEqual(env['MW34_EFFECT_LIGHTS'],'1')
            raw=Path(env['MW34_REMASTER_BANKS']).read_bytes();self.assertEqual(struct.unpack('<I',raw[8:12])[0],8)
            self.assertIn('MW34_WORLD_NORMALS',env)
            disabled=prepare({},self.host(),root/'disabled-shared');self.assertNotIn('MW34_REMASTER_BANKS',disabled)

    def test_optional_environment_surface_materials_bind_and_require_capability(self):
        from surface_materials import ROLE_HEIGHT, pack_surface_materials, read_surface_materials_file
        from startup_cache import VerificationCache
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            pack = self.fixture(root / 'surf-op', 'training')
            surf_bytes = pack_surface_materials(
                asset_id='training',
                mesh_uv_hash=0,
                batch_materials=['ground_sand'],
                records=[dict(
                    asset_id='training',
                    material_name='ground_sand',
                    height_image='sand_h',
                    height_reference=0.5,
                    height_amplitude=0.08,
                    max_displacement=0.08,
                )],
                images={'sand_h': (ROLE_HEIGHT, 2, 2, b'\x40\x00\x00\xff' * 4)},
            )
            surf_rel = 'environment/ground-surface.bin'
            surf_path = pack / surf_rel
            surf_path.write_bytes(surf_bytes)
            reg = json.loads((pack / REGISTRY).read_text())
            reg['ground_surface_materials'] = surf_rel
            (pack / REGISTRY).write_text(json.dumps(reg))
            manifest = json.loads((pack / 'pack.json').read_text())
            manifest['files'][surf_rel] = dict(bytes=len(surf_bytes), sha256=sha(surf_path), format='BWSFM1')
            manifest['files'][REGISTRY] = dict(bytes=(pack / REGISTRY).stat().st_size, sha256=sha(pack / REGISTRY))
            manifest['native_payload']['required_formats'].append('BWSFM1')
            (pack / 'pack.json').write_text(json.dumps(manifest))

            # Missing required_capabilities['surface-materials'] == 1 must fail.
            host_with_cap = self.host()
            host_with_cap['content_capabilities']['surface-materials'] = [1]
            with self.assertRaises(ValueError):
                select([str(pack)], host_with_cap)

            manifest['native_payload']['required_capabilities'] = {'surface-materials': 1}
            (pack / 'pack.json').write_text(json.dumps(manifest))

            # Host without surface-materials capability must reject the pack.
            with self.assertRaises(ValueError):
                select([str(pack)], self.host())

            cache_dir = root / 'cache'
            cache1 = VerificationCache(cache_dir)
            chosen = select([str(pack)], host_with_cap, verification=cache1)
            cache1.save()
            env = prepare(chosen, host_with_cap, root / 'launch-surf')
            merged = read_surface_materials_file(Path(env['MW34_GROUND_SURFACE_MATERIALS']))
            self.assertEqual(merged['records'][0]['material_name'], 'ground_sand')
            self.assertEqual(merged['images'][0]['pixels'], b'\x40\x00\x00\xff' * 4)

            # Corrupting the BWSFM1 file on disk invalidates VerificationCache and fails select().
            bad_bytes = bytearray(surf_bytes)
            bad_bytes[-1] ^= 0xFF
            surf_path.write_bytes(bytes(bad_bytes))
            cache2 = VerificationCache(cache_dir)
            with self.assertRaises(ValueError):
                select([str(pack)], host_with_cap, verification=cache2)

    def test_surface_material_catalog_merges_regions_and_shared_mechs(self):
        from surface_materials import (
            NO_SURFACE_MATERIAL, ROLE_HEIGHT, pack_surface_materials, read_surface_materials_file,
        )
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            host = self.host()
            host['content_capabilities']['surface-materials'] = [1]
            packs = []
            for region, materials, first_binding in (
                ('operation1', [('overlap', 10), ('operation_only', 11)], 'overlap'),
                ('training', [('overlap', 20), ('training_only', 21)], 'training_only'),
                ('shared-mechs', [('shared_only', 30)], 'shared_only'),
            ):
                pack = self.fixture(root / region, region)
                registry = json.loads((pack / REGISTRY).read_text())
                registry['surface_materials'] = 'environment/surface.bin'
                if region != 'shared-mechs':
                    registry['ground_surface_materials'] = 'environment/surface.bin'
                (pack / REGISTRY).write_text(json.dumps(registry))
                images = {f'h_{name}': (ROLE_HEIGHT, 1, 1, bytes([value, 0, 0, 255]))
                          for name, value in materials}
                data = pack_surface_materials(
                    asset_id=region, mesh_uv_hash=0,
                    batch_materials=[first_binding, 'neutral', *[name for name, _ in materials]],
                    records=[dict(asset_id=region, material_name=name, height_image=f'h_{name}',
                                  height_amplitude=0.1) for name, _ in materials],
                    images=images,
                )
                surf_path = pack / registry['surface_materials']
                surf_path.write_bytes(data)
                manifest = json.loads((pack / 'pack.json').read_text())
                manifest['files'][registry['surface_materials']] = dict(
                    bytes=len(data), sha256=sha(surf_path), format='BWSFM1')
                manifest['files'][REGISTRY] = dict(
                    bytes=(pack / REGISTRY).stat().st_size, sha256=sha(pack / REGISTRY))
                manifest['native_payload']['required_formats'].append('BWSFM1')
                manifest['native_payload']['required_capabilities'] = {'surface-materials': 1}
                (pack / 'pack.json').write_text(json.dumps(manifest))
                packs.append(str(pack))

            shared = select([packs[-1]], host)
            shared_preview = profile_bindings(shared, host)
            self.assertEqual(
                Path(shared_preview['MW34_SURFACE_MATERIALS']),
                Path(packs[-1]) / 'environment/surface.bin',
            )
            shared_environment = prepare(shared, host, root / 'shared-only')
            shared_catalog = read_surface_materials_file(
                Path(shared_environment['MW34_SURFACE_MATERIALS']))
            self.assertEqual([record['material_name'] for record in shared_catalog['records']],
                             ['shared_only'])
            self.assertNotIn('MW34_GROUND_SURFACE_MATERIALS', shared_environment)

            chosen = select(list(reversed(packs)), host)
            preview = profile_bindings(chosen, host)
            self.assertNotIn('MW34_SURFACE_MATERIALS', preview)
            self.assertNotIn('MW34_GROUND_SURFACE_MATERIALS', preview)
            limited_output = root / 'too-small'
            limited_output.mkdir()
            with patch.object(prepared_environment_packs, 'MAX_SIDECAR_BYTES', 3):
                with self.assertRaisesRegex(ValueError, 'image byte budget'):
                    prepared_environment_packs.write_merged_surface_materials(
                        chosen, 'surface_materials', limited_output)
            self.assertEqual(list(limited_output.iterdir()), [])
            env = prepare(chosen, host, root / 'merged')
            for key, expected_names in (
                ('MW34_SURFACE_MATERIALS', {'overlap', 'operation_only', 'training_only', 'shared_only'}),
                ('MW34_GROUND_SURFACE_MATERIALS', {'overlap', 'operation_only', 'training_only'}),
            ):
                catalog = read_surface_materials_file(Path(env[key]))
                records = {record['material_name']: record for record in catalog['records']}
                self.assertEqual(set(records), expected_names)
                self.assertEqual(catalog['images'][records['overlap']['height_image']]['pixels'][0], 10)
                self.assertEqual(records['training_only']['asset_id'], 'training')
                self.assertEqual(catalog['records'][catalog['bindings'][0]]['material_name'], 'overlap')
                self.assertEqual(catalog['bindings'][1], NO_SURFACE_MATERIAL)

            from startup_cache import environment_resources
            cached = environment_resources(chosen, host, root / 'cache')
            with patch('prepared_environment_packs.prepare',
                       side_effect=AssertionError('Warm preparation repeated')):
                warm = environment_resources(chosen, host, root / 'cache')
            for key, expected_names in (
                ('MW34_SURFACE_MATERIALS', {'overlap', 'operation_only', 'training_only', 'shared_only'}),
                ('MW34_GROUND_SURFACE_MATERIALS', {'overlap', 'operation_only', 'training_only'}),
            ):
                self.assertEqual(warm[key], cached[key])
                self.assertNotEqual(warm[key], str(Path(packs[0]) / 'environment/surface.bin'))
                catalog = read_surface_materials_file(Path(warm[key]))
                self.assertEqual({record['material_name'] for record in catalog['records']},
                                 expected_names)

if __name__=='__main__':unittest.main()
