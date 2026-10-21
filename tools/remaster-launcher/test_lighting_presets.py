"""Exercise the actual shared preset resolver without launching the game."""

from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.name == "nt", "Native launcher uses Windows PowerShell")
class LightingPresetTests(unittest.TestCase):
    def resolve(self, profile, preset):
        return subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "tools/remaster-launcher/resolve_sun_preset.ps1"),
                "-Profile",
                str(profile),
                "-Preset",
                preset,
            ],
            capture_output=True,
            text=True,
        )

    def test_shared_big_lake_presets_and_unknown_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary) / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "native": {
                            "sun_preset": {
                                "source": "tools/remaster-launcher/sun-presets.json",
                                "map": "BIG LAKE",
                                "default": "sunset",
                            }
                        }
                    }
                )
            )
            for name, azimuth, elevation, color in [
                ("sunset", "225", "9", "1,0.56,0.28"),
                ("sunrise", "45", "11", "1,0.73,0.5"),
                ("midday", "225", "35", "1,0.96,0.86"),
            ]:
                result = self.resolve(profile, name)
                self.assertEqual(result.returncode, 0, result.stderr)
                environment = json.loads(result.stdout)["environment"]
                self.assertEqual(environment["MW34_SUN_AZIMUTH"], azimuth)
                self.assertEqual(environment["MW34_SUN_ELEVATION"], elevation)
                self.assertEqual(environment["MW34_SUN_COLOR"], color)
                self.assertEqual(environment["MW34_SKY_AUTO"], "1")
            result = self.resolve(profile, "unknown")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unknown lighting preset", result.stderr)
            result = self.resolve(profile, "night")
            self.assertEqual(result.returncode, 0, result.stderr)
            environment = json.loads(result.stdout)["environment"]
            self.assertEqual(environment["MW34_SKY_AUTO"], "0")
            self.assertEqual(environment["MW34_NIGHT_WORLD_GAIN"], "0.24")
            self.assertEqual(environment["MW34_SKY_GLOW"], "0")
            self.assertEqual(environment["MW34_HAZE_COLOR"], "0.035,0.05,0.085")

    def test_invalid_color_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            catalog = folder / "presets.json"
            preset = {
                "azimuth": 225,
                "elevation": 9,
                "strength": 1.6,
                "ambient": 0.32,
                "sun_color": [1, -1, 0],
                "ambient_color": [1, 1, 1],
            }
            catalog.write_text(json.dumps({"maps": {"TEST": {"presets": {"bad": preset}}}}))
            profile = folder / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "native": {
                            "sun_preset": {"source": str(catalog), "map": "TEST", "default": "bad"}
                        }
                    }
                )
            )
            result = self.resolve(profile, "bad")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Invalid lighting color", result.stderr)

    def test_invalid_night_fields_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            catalog = folder / "presets.json"
            profile = folder / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "native": {
                            "sun_preset": {"source": str(catalog), "map": "TEST", "default": "bad"}
                        }
                    }
                )
            )
            base = {
                "azimuth": 225,
                "elevation": 35,
                "strength": 0.18,
                "ambient": 0.09,
                "sun_color": [0.5, 0.62, 0.9],
                "ambient_color": [0.52, 0.65, 0.9],
            }
            for field, value in [
                ("night_world_gain", 1.01),
                ("sky_auto", "false"),
                ("haze_color", [0, 0, 1.01]),
            ]:
                with self.subTest(field=field):
                    catalog.write_text(
                        json.dumps(
                            {"maps": {"TEST": {"presets": {"bad": dict(base, **{field: value})}}}}
                        )
                    )
                    result = self.resolve(profile, "bad")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(field, result.stderr)


if __name__ == "__main__":
    unittest.main()
