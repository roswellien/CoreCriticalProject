"""Asset-free checks for host/DLL seam metadata and provenance coverage."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_host import parse_symbols, source_pins, verify_dependency_headers


class HostBuildTests(unittest.TestCase):
    def test_dependency_headers_accept_only_line_ending_differences(self):
        original = b"// Authored fixture\n#define VALUE 1\n"
        digest = hashlib.sha256(original).hexdigest()
        cases = (
            ("LF", original, True),
            ("CRLF", original.replace(b"\n", b"\r\n"), True),
            ("mixed endings", original.replace(b"\n", b"\r\n", 1), True),
            ("changed value", original.replace(b"1", b"2"), False),
            ("extra whitespace", original.replace(b"VALUE", b" VALUE"), False),
            ("bare CR", original.replace(b"\n", b"\r"), False),
            ("BOM", b"\xef\xbb\xbf" + original, False),
            ("missing newline", original[:-1], False),
            ("missing file", None, False),
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "headers with spaces"
            directory.mkdir()
            header = directory / "fixture.h"
            for name in ("remill", "vulkan"):
                dependencies = {name: {"hash_algorithm": "sha256-crlf-to-lf",
                                       "files": {"fixture.h": digest}}}
                for label, content, accepted in cases:
                    with self.subTest(dependency=name, case=label):
                        if content is None:
                            header.unlink()
                        else:
                            header.write_bytes(content)
                        if accepted:
                            raw_pins = verify_dependency_headers(dependencies, {name: directory})
                            self.assertEqual(raw_pins[name]["fixture.h"],
                                             hashlib.sha256(content).hexdigest())
                            self.assertEqual(header.read_bytes(), content)
                        else:
                            with self.assertRaisesRegex(ValueError, f"Pinned {name} header mismatch"):
                                verify_dependency_headers(dependencies, {name: directory})

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
