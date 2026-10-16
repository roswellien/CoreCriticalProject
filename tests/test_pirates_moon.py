"""PM target isolation controls using only project-authored PE data."""
import hashlib
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from test_binary_tools import fixture, record_for

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/pirates-moon"))
import target
import generate
import translate as pm_translate


class TargetIsolation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = fixture()
        self.image = target.PEImage(self.data)
        self.record = record_for(self.data)
        (self.root / "fixture.exe").write_bytes(self.data)
        self.pin = dict(filename="fixture.exe", sha256=self.record["sha256"], size_bytes=len(self.data),
                        image_base=self.image.image_base, entry_point_rva=self.image.entry_point_rva)
        self.profile = dict(schema_version=1, target=target.GAME, entry=0x401000,
                            initializer_tables=[], modules=dict(game=self.pin))
        self.manifest = dict(schema_version=1, game=target.GAME, binaries=[self.record])
        self.write_config()

    def write_config(self):
        (self.root / "target.json").write_text(json.dumps(self.profile))
        (self.root / "supported-binaries.json").write_text(json.dumps(self.manifest))

    def load(self):
        with patch.object(target, "CONFIG", self.root):
            return target.load_target(self.root)

    def test_exact_profile_and_code_ranges(self):
        value = self.load()
        self.assertEqual(value["inputs"]["game"]["data"], self.data)
        self.assertEqual(target.closure_images(value)["game"][3:], (0x401000, 0x401200))

    def test_changed_dependency_bytes_rejected(self):
        changed = bytearray(self.data)
        changed[0x201] ^= 1
        (self.root / "fixture.exe").write_bytes(changed)
        with self.assertRaisesRegex(ValueError, "wrong exact game"):
            self.load()

    def test_wrong_game_manifest_rejected(self):
        self.manifest["game"] = "mw3"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "schema or game"):
            self.load()

    def test_default_manifest_reader_still_rejects_pm(self):
        with self.assertRaises(ValueError):
            target.load_manifest(self.root / "supported-binaries.json")

    def asset_manifest(self, files):
        (self.root / "native-assets.json").write_text(json.dumps(dict(
            schema_version=1, target=target.GAME, install_options=4, files=files)))

    def test_hardware_install_flag_requires_actual_matching_assets(self):
        self.asset_manifest([self.pin])
        with patch.object(target, "CONFIG", self.root):
            self.assertEqual(target.verify_native_assets(self.root), 4)
            (self.root / "fixture.exe").write_bytes(self.data[:-1] + b"X")
            with self.assertRaisesRegex(ValueError, "asset identity mismatch"):
                target.verify_native_assets(self.root)

    def test_empty_hardware_inventory_cannot_declare_installed(self):
        self.asset_manifest([])
        with patch.object(target, "CONFIG", self.root), self.assertRaisesRegex(ValueError, "empty hardware"):
            target.verify_native_assets(self.root)

    def test_hardware_asset_cannot_escape_installation(self):
        outside = self.root / "outside.asset"
        outside.write_bytes(self.data)
        installation = self.root / "installation"
        installation.mkdir()
        self.asset_manifest([dict(self.pin, filename="../outside.asset")])
        with patch.object(target, "CONFIG", self.root), self.assertRaisesRegex(ValueError, "escapes installation"):
            target.verify_native_assets(installation)

    def test_bounded_scan_uses_shortest_call_depth_and_handles_cycles(self):
        graph = {0: [0x30, 0x10], 0x10: [0x20], 0x20: [0x40],
                 0x30: [0x40], 0x40: [0x50], 0x50: [0]}
        graph = {0x401000 + k: [0x401000 + c for c in v] for k, v in graph.items()}
        scanner = SimpleNamespace(IMAGES={}, PES={}, PE=lambda *args: SimpleNamespace(imports=lambda: {}),
                                  image=lambda a: "game" if a in graph else None,
                                  function=lambda a, bound: dict(entry=a, end=a+1, image="game",
                                                               calls=graph[a], tails=[], imms=[]))
        with patch.dict(sys.modules, {"mfc_closure": scanner}):
            for depth, expected in ((2, set(graph)-{0x401050}), (3, set(graph))):
                output = self.root / f"depth-{depth}.json"
                pm_translate.create_closure(self.load(), output, [0x401000], False, depth)
                closure = json.loads(output.read_text())
                self.assertEqual({f["entry"] for f in closure["functions"]}, expected)
                self.assertEqual(closure["selection"]["max_depth"], depth)

    def test_pe_metadata_conflict_rejected(self):
        self.pin["image_base"] += 4096
        self.write_config()
        with self.assertRaisesRegex(ValueError, "PE identity"):
            self.load()

    def test_module_path_escape_rejected(self):
        self.pin["filename"] = "../fixture.exe"
        self.write_config()
        with self.assertRaises((FileNotFoundError, ValueError)):
            self.load()

    def test_closure_cannot_cross_target_or_executable_ranges(self):
        value = self.load()
        valid = dict(target=target.GAME, images={"game": self.pin["sha256"]},
                     functions=[dict(image="game", entry=0x401000, end=0x401009)])
        target.require_closure(value, valid)
        for change in (dict(target="mw3"), dict(images={"game": "0" * 64}),
                       dict(functions=[dict(image="game", entry=0x402000, end=0x402009)])):
            with self.assertRaises(ValueError):
                target.require_closure(value, valid | change)

    def test_dispatch_rejects_foreign_report_before_artifact_reads(self):
        directory = self.root / "lifts-r1"
        directory.mkdir()
        data = json.dumps(dict(target="mw3", images={})).encode()
        (directory / "report.json").write_bytes(data)
        with self.assertRaisesRegex(ValueError, "different target"):
            generate.verified_rows(self.load(), [(directory, hashlib.sha256(data).hexdigest())])

    def test_dispatch_binds_native_object_and_source_to_closed_report(self):
        directory = self.root / "lifts-r1"
        directory.mkdir()
        closure = dict(target=target.GAME, images={"game": self.pin["sha256"]},
                       functions=[dict(image="game", entry=0x401000, end=0x401009)])
        closure_bytes = json.dumps(closure).encode()
        (directory / "closure.json").write_bytes(closure_bytes)
        artifact = directory / "m_401000-O2.obj"
        artifact.write_bytes(b"authored placeholder for identity checking only")
        row = dict(entry=0x401000, start=0x401000, end=0x401009,
                   source_sha256=hashlib.sha256(self.data[0x200:0x209]).hexdigest(),
                   objects={"O2": {"sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}})
        report = dict(target=target.GAME, images=closure["images"],
                      closure_sha256=hashlib.sha256(closure_bytes).hexdigest(),
                      components={"m_401000": row})
        def save():
            data = json.dumps(report).encode()
            (directory / "report.json").write_bytes(data)
            return hashlib.sha256(data).hexdigest()
        digest = save()
        self.assertEqual(len(generate.verified_rows(self.load(), [(directory, digest)])), 1)
        artifact.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "native object"):
            generate.verified_rows(self.load(), [(directory, digest)])
        row["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source differs"):
            generate.verified_rows(self.load(), [(directory, save())])


if __name__ == "__main__":
    unittest.main()
