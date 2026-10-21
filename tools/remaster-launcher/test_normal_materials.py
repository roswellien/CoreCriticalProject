"""Asset-free material packing and cache invalidation checks."""

from pathlib import Path
import hashlib
import json
import struct
import tempfile
import unittest
from unittest.mock import patch

from normal_materials import (
    NO_NORMAL,
    normal_environment,
    pack_normals,
    pack_surface_normals,
    pack_surface_bindings,
    read_surface_bindings,
)


class NormalMaterialsTests(unittest.TestCase):
    def test_colour_alignment_preserves_unselected_entries(self):
        from align_surface_colour_bank import align, redirect_bank_map
        from prepare_surface_normals import bank_entries
        from normal_materials import pixel_hash

        with tempfile.TemporaryDirectory(prefix="mw34-colour-pair-") as temporary:
            root = Path(temporary)
            source = root / "source.zbd"
            reference = root / "reference.zbd"
            output = root / "paired.zbd"

            def bank(values):
                data = bytearray(struct.pack("<6I", 0, 1, 0, len(values), 0, 0))
                position = 24 + 40 * len(values)
                for name, value in values:
                    data.extend(struct.pack("<32sII", name.encode(), position, 0xFFFFFFFF))
                    position += 18
                for name, value in values:
                    data.extend(struct.pack("<IHHIHHH", 0x25, 1, 1, 0, 0, 0, value))
                return bytes(data)

            source.write_bytes(bank([("Armor", 0x1234), ("Panel", 0xABCD)]))
            reference.write_bytes(bank([("Armor", 0xE6DA)]))
            before = source.read_bytes()
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            report = align(
                source,
                digest(source),
                reference,
                digest(reference),
                {"Armor": (1, 1, 1, pixel_hash(struct.pack("<H", 0xE6DA)))},
                output,
            )
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(report["unchanged_entries"], 1)
            table = bank_entries(output)
            data = output.read_bytes()
            self.assertEqual(struct.unpack_from("<H", data, table["Armor"][0] + 16)[0], 0xE6DA)
            self.assertEqual(struct.unpack_from("<H", data, table["Panel"][0] + 16)[0], 0xABCD)
            key = b"zbd/rmechtex16.zbd"
            path = b"unchanged-source"
            mapping = b"MWBANK1\0" + struct.pack("<III", 1, len(key), len(path)) + key + path
            changed = redirect_bank_map(mapping, output)
            self.assertTrue(changed.endswith(str(output.resolve()).encode()))
            with self.assertRaises(ValueError):
                redirect_bank_map(mapping + b"x", output)

    def test_surface_catalog_shares_images_across_256_bindings(self):
        normal = (1, 1, bytes([128, 128, 255, 255]))
        entries = [((1, 1, 1, index), normal) for index in range(256)]
        packed = pack_surface_bindings(entries)
        self.assertEqual(read_surface_bindings(packed), entries)
        self.assertEqual(struct.unpack_from("<II", packed, 12 + 256 * 52 + 8), (256, 1))
        with self.assertRaises(ValueError):
            pack_surface_bindings(entries + [((1, 1, 1, 256), normal)])
        for corrupt in [packed[:-1], packed + b"junk", packed[:-1] + bytes([packed[-1] ^ 1])]:
            with self.assertRaises(ValueError):
                read_surface_bindings(corrupt)
        boundary = [((1, 1, 1, i), (1, 1, bytes([i, 128, 255, 255]))) for i in range(64)]
        boundary.append(((1, 1, 1, 64), None))
        self.assertEqual(read_surface_bindings(pack_surface_bindings(boundary)), boundary)
        with self.assertRaises(ValueError):
            pack_surface_bindings(boundary + [((1, 1, 1, 65), (1, 1, bytes([64, 128, 255, 255])))])

    def test_stock_catalog_checks_bank_pixels_and_orientation(self):
        from PIL import Image
        from prepare_surface_normals import prepare

        with tempfile.TemporaryDirectory(prefix="mw34-stock-normal-test-") as temporary:
            root = Path(temporary)
            bank = root / "bank.bin"
            colour = root / "colour.png"
            normal = root / "normal.png"
            # Rounded bank conversion differs from bit truncation for this color.
            Image.new("RGB", (2, 2), (230, 218, 216)).save(colour)
            normal_image = Image.new("RGBA", (2, 2))
            normal_image.putdata([(160, g, 240, 255) for g in [100, 110, 120, 130]])
            normal_image.save(normal)
            data = struct.pack("<6I", 0, 1, 0, 1, 0, 0) + struct.pack(
                "<32sII", b"Armor", 64, 0xFFFFFFFF
            )
            data += struct.pack("<IHHIHH", 0x25, 2, 2, 0, 0, 0) + struct.pack("<4H", *[0xE6DA] * 4)
            bank.write_bytes(data)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    dict(materials=[dict(name="Armor", basecolor=str(colour), normal=str(normal))])
                )
            )
            pin = lambda p: dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            config = root / "catalog.json"
            config.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        registrations=[
                            dict(
                                bank=pin(bank),
                                manifest=pin(manifest),
                                normal_row_order="stored",
                                normal_y="invert",
                            )
                        ],
                    )
                )
            )
            output = root / "surface.bin"
            report = prepare(config, output)
            self.assertEqual(report["bindings"], 1)
            entries = read_surface_bindings(output.read_bytes())
            self.assertEqual(
                entries[0][1][2], b"".join(bytes([160, g, 240, 255]) for g in [155, 145, 135, 125])
            )
            Image.new("RGB", (2, 2), (10, 20, 30)).save(colour)
            with self.assertRaisesRegex(ValueError, "every bank pixel"):
                prepare(config, root / "wrong.bin")
            self.assertFalse((root / "wrong.bin").exists())

    def test_conflicting_surface_images_are_not_silently_merged(self):
        from PIL import Image
        from prepare_surface_normals import prepare

        with tempfile.TemporaryDirectory(prefix="mw34-normal-conflict-") as temporary:
            root = Path(temporary)
            bank = root / "bank.bin"
            colour = root / "colour.png"
            manifest = root / "manifest.json"
            Image.new("RGB", (1, 1), (255, 255, 255)).save(colour)
            normal_paths = []
            for index, r in enumerate([128, 192]):
                path = root / f"normal{index}.png"
                Image.new("RGBA", (1, 1), (r, 128, 255, 255)).save(path)
                normal_paths.append(path)
            header = struct.pack("<6I", 0, 1, 0, 2, 0, 0)
            record = struct.pack("<IHHIHHH", 0x25, 1, 1, 0, 0, 0, 0xFFFF)
            bank.write_bytes(
                header
                + struct.pack("<32sII", b"Armor", 104, 0xFFFFFFFF)
                + struct.pack("<32sII", b"Panel", 122, 0xFFFFFFFF)
                + record
                + record
            )
            manifest.write_text(
                json.dumps(
                    dict(
                        materials=[
                            dict(name=name, basecolor=str(colour), normal=str(path))
                            for name, path in zip(["Armor", "Panel"], normal_paths)
                        ]
                    )
                )
            )
            pin = lambda p: dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            config = root / "catalog.json"
            config.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        registrations=[
                            dict(
                                bank=pin(bank),
                                manifest=pin(manifest),
                                normal_row_order="stored",
                                normal_y="preserve",
                            )
                        ],
                    )
                )
            )
            with self.assertRaisesRegex(ValueError, "Conflicting normal maps"):
                prepare(config, root / "result.bin")
            self.assertFalse((root / "result.bin").exists())

    def test_launcher_requires_matching_normal_capability(self):
        import play_remaster

        with tempfile.TemporaryDirectory(prefix="mw34-normal-profile-test-") as temporary:
            root = Path(temporary)
            audit = root / "local/work-ahead/texture-launcher-audit-v2"
            audit.mkdir(parents=True)
            (audit / "configured-banks.json").write_text("[{}]")
            executable = root / "authored-fixture.exe"
            executable.write_bytes(b"Not executed; authored launcher identity fixture")
            identity = hashlib.sha256(executable.read_bytes()).hexdigest()
            (root / "normal.png").write_bytes(b"Existence-only launcher fixture")
            graphics = dict(width=64, height=64, aa=1, af=1)
            native = dict(
                executable=executable.name,
                executable_sha256=identity,
                model_ids=["fixture"],
                graphics_capabilities=graphics,
                cumulative_texture_banks=True,
                verify_source_snapshot=True,
                source_snapshot="snapshot.json",
            )
            config = root / "profile.json"
            registry = root / "models.json"
            snapshot = root / "snapshot.json"
            registry.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        models=[
                            dict(
                                id="fixture",
                                name="Fixture",
                                backend="native",
                                status="runtime-ready",
                                required_files=[],
                                normal_textures={"Armor": "normal.png"},
                            )
                        ],
                    )
                )
            )

            def save(formats, snapshot_formats):
                native["normal_map_formats"] = formats
                config.write_text(
                    json.dumps(dict(backend="native", graphics=graphics, native=native))
                )
                snapshot.write_text(
                    json.dumps(
                        dict(
                            executable_sha256=identity,
                            model_ids=["fixture"],
                            normal_map_formats=snapshot_formats,
                        )
                    )
                )

            with patch.object(play_remaster, "ROOT", root):
                save([], [])
                with self.assertRaisesRegex(RuntimeError, "BWNRM2"):
                    play_remaster.plan(config_path=config, registry_path=registry)
                save([2], [])
                with self.assertRaisesRegex(RuntimeError, "normal-map support"):
                    play_remaster.plan(config_path=config, registry_path=registry)
                save([2], [2])
                planned = play_remaster.plan(config_path=config, registry_path=registry)
                self.assertTrue(planned["supported"])
                self.assertEqual(planned["command"][-1], str(config))
                (root / "authored.txt").write_bytes(b"MW34SNA1\nauthored-00.bin\n")
                native["runtime_environment"] = {"MW34_SURFACE_NORMALS": "authored.txt"}
                save([2], [2])
                with self.assertRaisesRegex(RuntimeError, "Paged authored normals"):
                    play_remaster.plan(config_path=config, registry_path=registry)
                native["authored_normal_catalog_versions"] = [1]
                save([2], [2])
                with self.assertRaisesRegex(RuntimeError, "authored-normal catalog support"):
                    play_remaster.plan(config_path=config, registry_path=registry)
                matching = json.loads(snapshot.read_text())
                matching["authored_normal_catalog_versions"] = [1]
                snapshot.write_text(json.dumps(matching))
                self.assertTrue(
                    play_remaster.plan(config_path=config, registry_path=registry)["supported"]
                )
                (root / "normal.png").unlink()
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    play_remaster.plan(config_path=config, registry_path=registry)

    def test_material_order_and_explicit_exclusion(self):
        pixel = (1, 1, bytes([128, 128, 255, 255]))
        packed = pack_normals(["Armor", "Glass", "Armor"], {"Glass": None, "Armor": pixel})
        self.assertEqual(struct.unpack_from("<III", packed, 16), (0, NO_NORMAL, 0))
        self.assertEqual(packed[-4:], pixel[2])
        with self.assertRaises(ValueError):
            pack_normals(["Missing"], {"Armor": pixel})
        self.assertEqual(
            normal_environment("MW34_STRIDER_LOD1_TEXTURES"), "MW34_STRIDER_LOD1_NORMALS"
        )

    def test_full_texture_identity_and_duplicate_rejection(self):
        first = bytes(8) + b"\0\0"
        second = bytes(8) + b"\1\0"
        entries = [(5, 1, 1, first, None), (5, 1, 1, second, None)]
        packed = pack_surface_normals(entries)
        self.assertNotEqual(packed[24:32], packed[76:84])
        with self.assertRaises(ValueError):
            pack_surface_normals([entries[0], entries[0]])
        with self.assertRaises(ValueError):
            pack_surface_normals([(5, 1, 1, b"bad", None)])

    def test_native_preparation_cache_and_source_invalidation(self):
        from PIL import Image
        from native_assets import prepare

        with tempfile.TemporaryDirectory(prefix="mw34-normal-material-test-") as temporary:
            root = Path(temporary)
            audit = root / "local/work-ahead/texture-launcher-audit-v2"
            audit.mkdir(parents=True)
            bank = root / "authored-bank.bin"
            bank.write_bytes(b"Authored test fixture")
            target = root / "local/work-ahead/training-terrain-game-test/install/zbd/test.zbd"
            rows = [
                dict(
                    target=str(target),
                    source=str(bank),
                    expected_sha256=hashlib.sha256(bank.read_bytes()).hexdigest(),
                )
            ]
            (audit / "configured-banks.json").write_text(json.dumps(rows))
            colour = root / "colour.png"
            normal = root / "normal.png"
            metadata = root / "batches.json"
            Image.new("RGB", (2, 2), (100, 100, 100)).save(colour)
            Image.new("RGBA", (2, 2), (128, 128, 255, 255)).save(normal)
            metadata.write_text(json.dumps(dict(batches=[dict(material="Armor")])))
            model = dict(
                id="fixture",
                textures={"Armor": str(colour)},
                normal_textures={"Armor": str(normal)},
                texture_environment="MW34_FIXTURE_TEXTURES",
                batch_metadata=str(metadata),
            )
            environment = prepare(root, [model])
            path = Path(environment["MW34_FIXTURE_NORMALS"])
            original = path.read_bytes()
            modified = path.stat().st_mtime_ns
            prepare(root, [model])
            self.assertEqual(path.stat().st_mtime_ns, modified)
            path.write_bytes(b"corrupted cached sidecar")
            prepare(root, [model])
            self.assertEqual(path.read_bytes(), original)
            Image.new("RGBA", (2, 2), (255, 128, 128, 255)).save(normal)
            prepare(root, [model])
            self.assertNotEqual(path.read_bytes(), original)
            # Repacking only the normal sidecar must not change albedo output.
            albedo = Path(environment["MW34_FIXTURE_TEXTURES"]).read_bytes()
            prepare(root, [model])
            self.assertEqual(Path(environment["MW34_FIXTURE_TEXTURES"]).read_bytes(), albedo)


if __name__ == "__main__":
    unittest.main()
