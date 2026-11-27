"""Asset-free checks of operation selection, relocation and disabled bindings."""
import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import weakref
from normal_materials import pack_surface_bindings,pixel_hash,read_surface_bindings
from normal_materials import DecodedSurfaceBudgetExceeded
import prepared_environment_packs
from prepared_environment_packs import select,prepare,detail_metadata,encode_normal_pages,PROFILE,REGISTRY,REGIONS,sha

class EnvironmentPackTests(unittest.TestCase):
    def target_fixture(self, root):
        import surface_materials

        manifest = json.loads((root / "pack.json").read_text())
        registry = json.loads((root / REGISTRY).read_text())
        # Independent authored raw polygon stream: one triangle, canonical
        # corner xyz/normal/UV words, before any renderer sees the fixture.
        vertices = (
            -1.0,
            -1.0,
            2.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            1.0,
            -1.0,
            2.0,
            0.0,
            0.0,
            1.0,
            1.0,
            0.0,
            0.0,
            1.0,
            2.0,
            0.0,
            0.0,
            1.0,
            0.5,
            1.0,
        )
        source = struct.pack("<II24f", 1, 3, *vertices)
        uv_hash = pixel_hash(source)
        sidecar = "environment/ground-height.bin"
        pixels = b"\x20\x20\x20\xff\xe0\xe0\xe0\xff" * 2
        data = surface_materials.pack_surface_materials(
            asset_id="training:fixture",
            mesh_uv_hash=uv_hash,
            batch_materials=["ground"],
            records=[
                dict(
                    asset_id="training:fixture",
                    material_name="ground",
                    height_image="ramp",
                    height_reference=0.5,
                    height_amplitude=0.05,
                )
            ],
            images={"ramp": (surface_materials.ROLE_HEIGHT, 2, 2, pixels)},
        )
        (root / sidecar).write_bytes(data)
        manifest["files"][sidecar] = dict(
            bytes=len(data), sha256=sha(root / sidecar), format="BWSFM1"
        )
        document = dict(
            schema_version=1,
            targets=[
                dict(
                    surface_materials=sidecar,
                    asset_id="training:fixture",
                    source=dict(
                        kind="gamez-zbd-v27",
                        member="zbd/t1/gamez.zbd",
                        sha256=hashlib.sha256(source).hexdigest(),
                        bytes=len(source),
                        model_slot=7,
                    ),
                    mesh_uv_hash=f"{uv_hash:016x}",
                    polygon_materials=["ground"],
                    surface_keys=[
                        dict(width=1, height=1, format=1, hash=f"{pixel_hash(bytes(2)):016x}")
                    ],
                )
            ],
        )
        registry["material_targets"] = "environment/material_targets.json"
        manifest["native_payload"]["required_formats"].extend(
            ["BWSFM1", prepared_environment_packs.MATERIAL_TARGET_FORMAT]
        )
        manifest["native_payload"]["required_capabilities"] = {"surface-materials": 1}
        self.save_target_fixture(root, manifest, registry, document)
        return manifest, registry, document

    def save_target_fixture(self, root, manifest, registry, document):
        for name, value, format_ in (
            (REGISTRY, registry, None),
            (
                "environment/material_targets.json",
                document,
                prepared_environment_packs.MATERIAL_TARGET_FORMAT,
            ),
        ):
            data = json.dumps(value).encode()
            (root / name).write_bytes(data)
            manifest["files"][name] = dict(bytes=len(data), sha256=sha(root / name))
            if format_:
                manifest["files"][name]["format"] = format_
        (root / "pack.json").write_text(json.dumps(manifest))

    def test_material_targets_keep_independent_source_and_image_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(Path(folder) / "targets")
            _, _, document = self.target_fixture(root)
            host = self.host()
            host["content_capabilities"]["surface-materials"] = [1]
            chosen = select([str(root)], host)
            target = chosen["training"]["material_targets"][0]
            for key, value in document["targets"][0].items():
                self.assertEqual(target[key], value)
            self.assertEqual(target["sidecar_sha256"], sha(Path(target["path"])))
            # Selection does not enable rendering or add a launch flag.
            self.assertNotIn("MW34_POM", prepare(chosen, host, Path(folder) / "launch"))

    def test_material_targets_reject_wrong_source_material_and_member(self):
        import copy

        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(Path(folder) / "targets")
            manifest, registry, document = self.target_fixture(root)
            host = self.host()
            host["content_capabilities"]["surface-materials"] = [1]
            mutations = [
                lambda x: x["targets"].append(copy.deepcopy(x["targets"][0])),
                lambda x: x["targets"][0]["source"].update(member="zbd/c1/gamez.zbd"),
                lambda x: x["targets"][0]["source"].update(kind="first-seen"),
                lambda x: x["targets"][0]["source"].update(model_slot=True),
                lambda x: x["targets"][0]["source"].update(unknown=1),
                lambda x: x["targets"][0].update(mesh_uv_hash="0000000000000000"),
                lambda x: x["targets"][0].update(mesh_uv_hash="0000000000000001"),
                lambda x: x["targets"][0].update(asset_id="wrong:asset"),
                lambda x: x["targets"][0].update(polygon_materials=["wrong"]),
                lambda x: x["targets"][0].update(surface_materials="../outside.bin"),
                lambda x: x["targets"][0].update(surface_keys=[None]),
                lambda x: x["targets"][0]["surface_keys"][0].update(width=0),
                lambda x: x["targets"][0]["surface_keys"][0].update(hash="1"),
                lambda x: x["targets"][0].update(unrecognized=True),
                lambda x: x.update(schema_version=True),
            ]
            for mutation in mutations:
                with self.subTest(mutation=mutations.index(mutation)):
                    changed = copy.deepcopy(document)
                    mutation(changed)
                    self.save_target_fixture(root, manifest, registry, changed)
                    with self.assertRaises(ValueError):
                        select([str(root)], host)
            self.save_target_fixture(root, manifest, registry, document)
            extra = root / "environment/unused.bin"
            extra.write_bytes(b"unused")
            manifest["files"]["environment/unused.bin"] = dict(bytes=6, sha256=sha(extra))
            (root / "pack.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "unused"):
                select([str(root)], host)

    def test_material_target_metadata_limits_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(Path(folder) / "targets")
            manifest, registry, document = self.target_fixture(root)
            host = self.host()
            host["content_capabilities"]["surface-materials"] = [1]
            path = root / registry["material_targets"]
            for data in (
                b'{"schema_version":1,"schema_version":1,"targets":[]}',
                b" " * (prepared_environment_packs.MATERIAL_TARGET_BYTES + 1),
            ):
                path.write_bytes(data)
                manifest["files"][registry["material_targets"]].update(
                    bytes=len(data), sha256=sha(path)
                )
                (root / "pack.json").write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    select([str(root)], host)
            document["targets"] *= 4097
            self.save_target_fixture(root, manifest, registry, document)
            with self.assertRaises(ValueError):
                select([str(root)], host)

    def test_material_target_budget_is_charged_before_unique_sidecar_read(self):
        import copy
        import surface_materials

        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(Path(folder) / "targets")
            manifest, registry, document = self.target_fixture(root)
            first = document["targets"][0]["surface_materials"]
            second = "environment/second-height.bin"
            (root / second).write_bytes((root / first).read_bytes())
            manifest["files"][second] = dict(manifest["files"][first])
            document["targets"].append(copy.deepcopy(document["targets"][0]))
            document["targets"][1]["source"]["model_slot"] = 8
            files = manifest["files"]
            paths = {name: str(root / name) for name in files}
            original_reader = surface_materials.read_surface_materials_file
            budget = dict(
                owners=set(), bytes=surface_materials.MAX_SIDECAR_BYTES - files[first]["bytes"]
            )
            self.save_target_fixture(root, manifest, registry, document)
            path = root / registry["material_targets"]
            # Sharing one immutable owner does not consume the budget twice.
            prepared_environment_packs.read_material_targets(path, "training", files, paths, budget)
            self.assertEqual(budget["bytes"], surface_materials.MAX_SIDECAR_BYTES)
            document["targets"][1]["surface_materials"] = second
            self.save_target_fixture(root, manifest, registry, document)
            budget = dict(
                owners=set(), bytes=surface_materials.MAX_SIDECAR_BYTES - files[first]["bytes"]
            )
            with patch.object(
                surface_materials, "read_surface_materials_file", wraps=original_reader
            ) as reader:
                with self.assertRaisesRegex(ValueError, "decoded budget"):
                    prepared_environment_packs.read_material_targets(
                        path, "training", files, paths, budget
                    )
                self.assertEqual(reader.call_count, 1)

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
    def test_streamed_c1_pack_admits_exact_r8_and_requires_capability(self):
        with tempfile.TemporaryDirectory() as t:
            root = self.fixture(Path(t) / "c1", "operation1")
            manifest_path = root / "pack.json"
            manifest = json.loads(manifest_path.read_text())
            registry = json.loads((root / REGISTRY).read_text())
            index = "environment/height-index.json"
            image = "environment/height.r8"
            stream_format = prepared_environment_packs.STREAM_INDEX_FORMAT
            image_format = prepared_environment_packs.STREAM_IMAGE_FORMAT
            def write(member, value, fmt=None):
                (root / member).write_bytes(value)
                pin = dict(bytes=len(value), sha256=sha(root / member))
                if fmt:
                    pin["format"] = fmt
                manifest["files"][member] = pin

            registry["streamed_height_materials"] = index
            write(REGISTRY, json.dumps(registry).encode())
            write(image, bytes([127]), image_format)
            manifest["native_payload"]["required_formats"].extend([stream_format, image_format])
            manifest["native_payload"]["required_capabilities"] = {"surface-materials": 1}
            document = {
                "schema_version": 1,
                "images": [{"member": image, "width": 1, "height": 1}],
                "subsets": [{"world": 0, "x": 0, "z": 0, "images": [0]}],
                "targets": [{
                    "asset_id": "c1:ground",
                    "source": {"kind": "gamez-zbd-v27", "member": "zbd/c1/gamez.zbd",
                               "sha256": "a" * 64, "bytes": 1, "model_slot": 7},
                    "mesh_uv_hash": "0000000000000001",
                    "polygon_materials": ["txwall01"],
                    "surface_keys": [{"width": 1, "height": 1, "format": 1, "hash": "0000000000000001"}],
                    "height_bindings": [{"image": 0, "amplitude": 0.8}],
                }],
            }
            def save_index():
                write(index, json.dumps(document).encode(), stream_format)
                manifest_path.write_text(json.dumps(manifest))

            save_index()
            host = self.host()
            host["content_capabilities"]["surface-materials"] = [1]
            with self.assertRaisesRegex(ValueError, "c1-height-stream"):
                select([str(root)], host)
            host["content_capabilities"][prepared_environment_packs.STREAM_CAPABILITY] = [1]
            selected = select([str(root)], host)
            self.assertEqual(selected["operation1"]["paths"][image], str(root / image))
            (root / image).write_bytes(bytes([128]))
            with self.assertRaisesRegex(ValueError, "integrity failure"):
                select([str(root)], host)
            (root / image).write_bytes(bytes([127]))
            document["targets"][0]["height_bindings"][0]["amplitude"] = 0.75
            save_index()
            with self.assertRaisesRegex(ValueError, "streamed polygon height identity"):
                select([str(root)], host)

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

if __name__=='__main__':unittest.main()
