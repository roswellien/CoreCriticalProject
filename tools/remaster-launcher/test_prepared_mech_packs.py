"""Exercise installed pack composition and the final coordinator profile boundary."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import prepared_mech_packs as packs
import play_remaster


class PreparedPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="MW3 installed packs ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.host = dict(content_capabilities={"prepared-mechs": [1]}, executable_sha256="a" * 64, model_ids=["orion"], skin_ids={},
                         mesh_payload_versions=[2], normal_map_formats=[2], include_runtime_candidates=True,
                         runtime_environment={"MW34_ORION_MESH": "stale.bin", "MW34_AVATAR_NORMALS": "disabled.bin", "MW34_GPU_MODELS": "1"})

    def build(self, name="first", skins=()):
        root = self.root / name
        (root / "payload").mkdir(parents=True)
        files = {}
        bindings = {}
        for key in packs.MODEL_KEYS["orion"]:
            if key in packs.SURFACE_KEYS["orion"]:
                continue
            if key in packs.SKIN_KEYS['orion'] and not any('_SKIN_'+s.upper()+'_' in key for s in skins):continue
            fmt = "BWNRM2" if key.endswith("_NORMALS") else "BWTEX1" if key.endswith("_TEXTURES") else "BWMESH2"
            relative = "payload/" + key + ".bin"
            content = fmt.encode().ljust(8, b"\0") + name.encode()
            (root / relative).write_bytes(content)
            files[relative] = dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), format=fmt)
            bindings[key] = relative
        registry = dict(schema_version=2, payload_profile="prepared-native-v1", models=[
            dict(id="orion", name="Orion", backend="native", status="runtime-candidate", environment=bindings,
                 required_formats=["BWMESH2", "BWTEX1", "BWNRM2"], skin_ids=list(skins))])
        (root / "models").mkdir()
        content = json.dumps(registry).encode()
        (root / "models/models.json").write_bytes(content)
        files["models/models.json"] = dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
        manifest = dict(schema_version=2, id="test." + name, provides=dict(mechs=["orion"]), files=files,
                        native_payload=dict(profile="prepared-native-v1", registry="models/models.json", path_base="pack-root",
                                            reference_host_sha256="a" * 64, required_formats=registry["models"][0]["required_formats"]))
        (root / "pack.json").write_text(json.dumps(manifest))
        return root

    def test_priority_disable_and_relocation(self):
        first, second = self.build(), self.build("second")
        relocated = self.root / "relocated content"
        first.rename(relocated)
        records, env = packs.compose([str(relocated), str(second)], self.host)
        self.assertEqual(len(records), 1)
        self.assertTrue(Path(env["MW34_ORION_MESH"]).is_relative_to(relocated))
        _, reverse = packs.compose([str(second), str(relocated)], self.host)
        self.assertTrue(Path(reverse["MW34_ORION_MESH"]).is_relative_to(second))
        self.assertNotIn("MW34_AVATAR_NORMALS", env)
        self.assertEqual(env["MW34_GPU_MODELS"], "1")
        records, env = packs.compose([], self.host)
        self.assertEqual(records, [])
        self.assertEqual(env, {"MW34_GPU_MODELS": "1"})

    def test_alternates_require_both_lods_and_explicit_host_support(self):
        root=self.build(skins=['b','g'])
        with self.assertRaises(ValueError):packs.compose([str(root)],self.host)
        host=self.host | dict(skin_ids={'orion':['b','g']})
        _,env=packs.compose([str(root)],host)
        self.assertIn('MW34_ORION_SKIN_B_TEXTURES',env)
        self.assertIn('MW34_ORION_LOD1_SKIN_G_TEXTURES',env)
        path=root/'models/models.json';registry=json.loads(path.read_text());del registry['models'][0]['environment']['MW34_ORION_LOD1_SKIN_B_TEXTURES']
        raw=json.dumps(registry).encode();path.write_bytes(raw)
        path=root/'pack.json';manifest=json.loads(path.read_text());manifest['files']['models/models.json']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):packs.compose([str(root)],host)

    def test_canonical_root_is_anchored_to_manifest_without_allowing_file_escape(self):
        root = self.build()
        canonical = packs.canonical_pack_root(root)
        self.assertEqual(canonical, (root / "pack.json").resolve().parent)
        self.assertEqual(packs.resolve(canonical, "pack.json"), (root / "pack.json").resolve())
        with self.assertRaises(ValueError): packs.resolve(canonical, "../outside.bin")

    def test_corruption_unsupported_host_format_and_schema(self):
        root = self.build()
        for change in ({"content_capabilities": {}}, {"mesh_payload_versions": [1]}, {"model_ids": []}, {"include_runtime_candidates": False}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                packs.compose([str(root)], self.host | change)
        manifest = json.loads((root / "pack.json").read_text())
        (root / "pack.json").write_text(json.dumps(manifest | {"schema_version": 3}))
        with self.assertRaises(ValueError): packs.compose([str(root)], self.host)
        (root / "pack.json").write_text(json.dumps(manifest))
        (root / "payload/MW34_ORION_MESH.bin").write_bytes(b"bad")
        with self.assertRaises(ValueError): packs.compose([str(root)], self.host)

    def test_allowlist_and_path_escape(self):
        for name in ("../escape", "C:/absolute", "//server/share", "a:ads", "CON.bin", "a\\b", "a./b"):
            with self.subTest(name=name), self.assertRaises(ValueError): packs.resolve(self.root, name)
        root = self.build()
        registry_path = root / "models/models.json"
        registry = json.loads(registry_path.read_text())
        registry["models"][0]["environment"]["MW34_GPU_MODELS"] = "payload/MW34_ORION_MESH.bin"
        data = json.dumps(registry).encode()
        registry_path.write_bytes(data)
        manifest = json.loads((root / "pack.json").read_text())
        manifest["files"]["models/models.json"] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        (root / "pack.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError): packs.compose([str(root)], self.host)

    def test_final_powershell_profile_contains_installed_bindings(self):
        root = self.build()
        models, bindings = packs.compose([str(root)], self.host)
        prepared_profile = dict(native=self.host | {"runtime_environment": bindings})
        command = ["powershell.exe", "-Profile", "old-profile.json"]
        planned = dict(backend="native", graphics=dict(width=1280, height=720, aa=1, af=1), supported=True,
                       texture_banks=0, models=models, offline_models=[], limitations=[], command=command,
                       music=None, asset_output=str(self.root / "output"), prepared_profile=prepared_profile)
        asset_module = types.SimpleNamespace(prepare=lambda *a, **kw: bindings)
        with (patch("sys.argv", ["play_remaster"]), patch.object(play_remaster, "plan", return_value=planned),
              patch.object(play_remaster, "read_json", return_value={"native": {"executable": "fixture.exe"}}),
              patch.dict("sys.modules", {"native_assets": asset_module}),
              patch.object(play_remaster.subprocess, "run", return_value=types.SimpleNamespace(returncode=0)),
              patch.object(play_remaster.subprocess, "call", return_value=0) as call):
            self.assertEqual(play_remaster.main(), 0)
        launched = call.call_args.args[0]
        actual_profile = json.loads(Path(launched[launched.index("-Profile") + 1]).read_text())
        self.assertEqual(actual_profile["native"]["runtime_environment"], bindings)
        self.assertNotIn("MW34_AVATAR_NORMALS", actual_profile["native"]["runtime_environment"])

    def test_plan_disabled_packs_does_not_read_developer_registry_or_banks(self):
        executable = self.root / "host.exe"
        executable.write_bytes(b"authored fixture")
        native = self.host | dict(executable=str(executable), executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                                  prepared_pack_roots=[], graphics_capabilities={}, cumulative_texture_banks=True)
        config = dict(backend="native", native=native, graphics={})
        profile_path = self.root / "profile.json"
        profile_path.write_text(json.dumps(config))
        with patch.object(play_remaster, "ROOT", self.root):
            planned = play_remaster.plan(config_path=profile_path)
        self.assertEqual(planned["models"], [])
        self.assertEqual(planned["texture_banks"], 0)
        self.assertNotIn("MW34_ORION_MESH", planned["prepared_profile"]["native"]["runtime_environment"])

    def test_optional_surface_materials_validate_compatibility_and_capability(self):
        import struct
        import surface_materials
        root = self.build("surface")
        mesh_bytes = bytearray(b"BWMESH2\0" + struct.pack("<I", 1))
        mesh_bytes.extend(b"torso".ljust(32, b"\0") + b"torso".ljust(32, b"\0"))
        mesh_bytes.extend(struct.pack("<II", 3, 0xFFFFFFFF))
        for idx in range(3):
            mesh_bytes.extend(struct.pack("<8f", float(idx), 0.0, 0.0, 0.0, 0.0, 1.0, 0.25 * idx, 0.5 * idx))
        tex_bytes = bytearray(b"BWTEX1\0\0" + struct.pack("<III", 1, 1, 0))
        tex_bytes.extend(b"armor_hull".ljust(32, b"\0") + struct.pack("<IIQ", 1, 1, 0) + b"\x00\x7c")
        mesh_hash = surface_materials.mesh_uv_identity(bytes(mesh_bytes))
        sfm_close = surface_materials.pack_surface_materials(
            asset_id="orion:close",
            mesh_uv_hash=mesh_hash,
            batch_materials=["armor_hull"],
            records=[{"asset_id": "orion:close", "material_name": "armor_hull"}],
        )
        sfm_dist = surface_materials.pack_surface_materials(
            asset_id="orion:distance",
            mesh_uv_hash=mesh_hash,
            batch_materials=["armor_hull"],
            records=[{"asset_id": "orion:distance", "material_name": "armor_hull"}],
        )
        manifest = json.loads((root / "pack.json").read_text())
        registry = json.loads((root / "models/models.json").read_text())
        for key, raw, fmt in [
            ("MW34_ORION_MESH", bytes(mesh_bytes), "BWMESH2"),
            ("MW34_ORION_LOD1_MESH", bytes(mesh_bytes), "BWMESH2"),
            ("MW34_ORION_TEXTURES", bytes(tex_bytes), "BWTEX1"),
            ("MW34_ORION_LOD1_TEXTURES", bytes(tex_bytes), "BWTEX1"),
            ("MW34_ORION_SURFACE_MATERIALS", sfm_close, "BWSFM1"),
            ("MW34_ORION_LOD1_SURFACE_MATERIALS", sfm_dist, "BWSFM1"),
        ]:
            rel = "payload/" + key + ".bin"
            (root / rel).write_bytes(raw)
            manifest["files"][rel] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), format=fmt)
            registry["models"][0]["environment"][key] = rel
        registry["models"][0]["required_formats"] = ["BWMESH2", "BWTEX1", "BWNRM2", "BWSFM1"]
        reg_bytes = json.dumps(registry).encode()
        (root / "models/models.json").write_bytes(reg_bytes)
        manifest["files"]["models/models.json"] = dict(bytes=len(reg_bytes), sha256=hashlib.sha256(reg_bytes).hexdigest())
        manifest["native_payload"]["required_formats"] = ["BWMESH2", "BWTEX1", "BWNRM2", "BWSFM1"]
        manifest["native_payload"]["required_capabilities"] = {"surface-materials": 1}
        (root / "pack.json").write_text(json.dumps(manifest))

        # Old host without surface-materials capability must reject the pack.
        with self.assertRaises(ValueError):
            packs.compose([str(root)], self.host)

        host = copy.deepcopy(self.host)
        host["content_capabilities"]["surface-materials"] = [1]
        with (
            patch.object(surface_materials, "read_surface_materials_file",
                         wraps=surface_materials.read_surface_materials_file) as sidecar_reader,
            patch.object(surface_materials, "mesh_uv_identity_file",
                         wraps=surface_materials.mesh_uv_identity_file) as mesh_reader,
            patch.object(surface_materials, "texture_batch_materials_file",
                         wraps=surface_materials.texture_batch_materials_file) as texture_reader,
        ):
            models, env = packs.compose([str(root)], host)
        self.assertEqual(sidecar_reader.call_count, 2)
        self.assertEqual(mesh_reader.call_count, 2)
        self.assertEqual(texture_reader.call_count, 2)
        self.assertEqual(len(models), 1)
        self.assertIn("MW34_ORION_SURFACE_MATERIALS", env)
        self.assertIn("MW34_ORION_LOD1_SURFACE_MATERIALS", env)

        # Appearance switch: a higher-precedence pack without surface materials
        # replaces Orion's appearance without inheriting earlier surface bindings.
        plain_root = self.build("plain-override")
        models_switch, env_switch = packs.compose([str(plain_root), str(root)], host)
        self.assertEqual(len(models_switch), 1)
        self.assertTrue(Path(env_switch["MW34_ORION_MESH"]).is_relative_to(plain_root))
        self.assertNotIn("MW34_ORION_SURFACE_MATERIALS", env_switch)
        self.assertNotIn("MW34_ORION_LOD1_SURFACE_MATERIALS", env_switch)

        # Startup cache invalidation: VerificationCache reuses unchanged BWSFM1
        # sidecars and re-hashes immediately when BWSFM1 bytes change.
        import startup_cache
        cache_dir = self.root / "cache-out"
        cache1 = startup_cache.VerificationCache(cache_dir)
        packs.compose([str(root)], host, verification=cache1)
        cache1.save()
        self.assertGreater(cache1.hashed, 0)
        cache2 = startup_cache.VerificationCache(cache_dir)
        packs.compose([str(root)], host, verification=cache2)
        self.assertEqual(cache2.hashed, 0)
        self.assertGreater(cache2.reused, 0)

        sfm_alt = surface_materials.pack_surface_materials(
            asset_id="orion:close",
            mesh_uv_hash=mesh_hash,
            batch_materials=["armor_hull"],
            records=[{"asset_id": "orion:close", "material_name": "armor_hull", "height_reference": 0.25}],
        )
        (root / "payload/MW34_ORION_SURFACE_MATERIALS.bin").write_bytes(sfm_alt)
        manifest["files"]["payload/MW34_ORION_SURFACE_MATERIALS.bin"] = dict(
            bytes=len(sfm_alt),
            sha256=hashlib.sha256(sfm_alt).hexdigest(),
            format="BWSFM1",
        )
        (root / "pack.json").write_text(json.dumps(manifest))
        cache3 = startup_cache.VerificationCache(cache_dir)
        packs.compose([str(root)], host, verification=cache3)
        self.assertEqual(cache3.hashed, 1)

        # Changing the close mesh UV layout invalidates the surface-material binding.
        altered_mesh = bytearray(mesh_bytes)
        altered_mesh[-4:] = struct.pack("<f", 0.875)
        (root / "payload/MW34_ORION_MESH.bin").write_bytes(bytes(altered_mesh))
        manifest["files"]["payload/MW34_ORION_MESH.bin"] = dict(
            bytes=len(altered_mesh),
            sha256=hashlib.sha256(bytes(altered_mesh)).hexdigest(),
            format="BWMESH2",
        )
        (root / "pack.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            packs.compose([str(root)], host)


if __name__ == "__main__":
    unittest.main()
