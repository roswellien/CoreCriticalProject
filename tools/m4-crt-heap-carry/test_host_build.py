"""Asset-free checks for host/DLL seam metadata and provenance coverage."""
import json
from pathlib import Path
import unittest

from build_host import parse_symbols, source_pins


class HostBuildTests(unittest.TestCase):
    def test_named_native_seam(self):
        text = """Export {
  Ordinal: 1
  Name: sub_401000
  RVA: 0x1000
}
Import {
  Name: entry_commandline.exe
  Symbol: mw34_bridge (1)
}
"""
        self.assertEqual(parse_symbols(text), (["sub_401000"], ["mw34_bridge"]))
        for invalid in (
            text.replace("entry_commandline.exe", "unexpected.dll"),
            text.replace("sub_401000", "unsafe/name"),
            text + text,
            text.replace("Symbol: mw34_bridge (1)", "Symbol: (ordinal 1)"),
            text.replace("Symbol: mw34_bridge (1)", "Symbol: mw34_bridge (1)\n  Symbol: (ordinal 2)"),
            "",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    parse_symbols(invalid)

    def test_every_host_file_has_a_decision_and_exact_pin(self):
        root = Path(__file__).parent
        recorded = json.loads((root / "host-source-manifest.json").read_text())["files"]
        self.assertEqual(source_pins(), {name: row["sha256"] for name, row in recorded.items()})
        self.assertTrue(all(row["decision"] == "commit" for row in recorded.values()))
        for name in ("audio/local_cd_audio.hpp", "graphics/menu_version.hpp",
                     "memory/guest_memory.hpp", "mfc_entries.inc", "mfc_routers.inc"):
            self.assertIn(name, recorded)


if __name__ == "__main__":
    unittest.main()
