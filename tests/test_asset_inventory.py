"""Asset discovery checks using authored inputs only."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import wave

spec = importlib.util.spec_from_file_location(
    "asset_inventory", Path(__file__).resolve().parents[1] / "tools/asset-inventory/inventory.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def test_signatures_exclusions_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with wave.open(str(root / "audio.zbd"), "wb") as stream:
                stream.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                stream.writeframes(b"\0\0" * 80)
            (root / "copy.zbd").write_bytes((root / "audio.zbd").read_bytes())
            (root / "unknown.zbd").write_bytes(b"authored unknown format")
            (root / "media").mkdir()
            (root / "media/disc.iso").write_bytes(b"excluded")
            report = module.inventory(root, {"media"})
            self.assertEqual(report["file_count"], 3)
            self.assertEqual(report["signature_counts"], {"riff-wave": 2, "unknown": 1})
            self.assertEqual(report["duplicate_groups"], [["audio.zbd", "copy.zbd"]])
            self.assertEqual(report["files"][0]["metadata"]["duration_seconds"], 0.01)

    def test_truncated_wave_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.wav"
            path.write_bytes(b"RIFF\x04\x00\x00\x00WAVE")
            record = module.inspect_file(path)
            self.assertEqual(record["signature_class"], "riff-wave")
            self.assertIn("decode_error", record["metadata"])


if __name__ == "__main__":
    unittest.main()
