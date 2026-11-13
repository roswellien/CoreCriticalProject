"""Exercise installed preparation without game bytes, replacement packs or Pillow."""
import tempfile
import unittest
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import native_assets
import prepared_environment_packs
import refresh_content_runtime
import stage_native_runtime
import test_prepared_environment_packs as environment_fixtures


class InstalledPreparationTests(unittest.TestCase):
    def test_staged_coordinator_prepares_without_the_development_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / 'authored-inputs'
            fixture.mkdir()
            host_file = fixture / 'host.bin'
            host_file.write_bytes(b'authored host fixture; never executed')
            snapshot = fixture / 'snapshot.json'
            snapshot.write_text('{}', encoding='utf-8')
            entry = fixture / 'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(b'authored entry fixture; never executed')
            (fixture / 'decoder.bin').write_bytes(b'authored decoder fixture; never executed')
            music = fixture / 'local/remaster/music.json'
            music.parent.mkdir(parents=True)
            music.write_text(json.dumps({'decoder': 'decoder.bin'}), encoding='utf-8')
            profile = fixture / 'profile.json'
            native = dict(executable=str(host_file),
                          executable_sha256=hashlib.sha256(host_file.read_bytes()).hexdigest(),
                          source_snapshot=str(snapshot), original_support_versions=[1],
                          content_capabilities={'environment-resources': [1]},
                          runtime_environment={'MW34_SEED': 'host', 'MW34_STARTUP': 'loader'})
            profile.write_text(json.dumps(dict(native=native, graphics={})), encoding='utf-8')
            python_home = fixture / 'empty-python-home'
            python_home.mkdir()
            staged = root / 'initial-runtime'
            with patch.object(stage_native_runtime, 'ROOT', fixture):
                stage_native_runtime.stage(profile, staged, python_home)
            refreshed = root / 'updated-runtime'
            refresh_content_runtime.stage(staged, refreshed, 'fixture-update')
            pack = environment_fixtures.EnvironmentPackTests().fixture(root / 'pack', world_format='BWSNR3')
            # -I excludes PYTHONPATH and the current checkout. Only the packaged
            # coordinator can supply producers/imports, including the codec.
            script = '''
import json, sys
from pathlib import Path
coordinator = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(coordinator))
from startup_cache import environment_resources
from prepared_environment_packs import select
from owned_emission import pack, read
bindings = [dict(owner='torso', material='Glass', width=1, height=1, hash=77,
                 bounds=((-1,1),(-1,1),(-1,1)))]
records = [dict(id='eyes', batch=0, strength=.35, regions=[(0,0,1,1)], anchors=[])]
assert read(pack(12, bindings, records), 12, bindings)[0]['id'] == 'eyes'
host = dict(content_capabilities={'environment-resources': [1]},
            executable_sha256='a' * 64, runtime_environment={})
for index, chosen in enumerate(({}, select([sys.argv[2]], host))):
    cache = Path(sys.argv[3]) / str(index)
    first = environment_resources(chosen, host, cache)
    assert environment_resources(chosen, host, cache) == first
    if chosen:
        assert Path(first['MW34_REMASTER_BANKS']).is_file()
for name, module in tuple(sys.modules.items()):
    if name in ('startup_cache', 'normal_materials', 'normal_codec', 'owned_emission'):
        assert Path(module.__file__).resolve().parent == coordinator
'''
            for runtime in (staged, refreshed):
                with self.subTest(runtime=runtime.name):
                    result = subprocess.run(
                        [sys.executable, '-I', '-B', '-c', script,
                         str(runtime / 'coordinator'), str(pack), str(root / runtime.name / 'cache')],
                        cwd=root, capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_optional_assets_leaves_native_original_archive_reader_enabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bindings = native_assets.prepare(root, [], output=root / "cache",
                                             allow_original_banks=True, use_development_banks=False)
            self.assertNotIn("MW34_REMASTER_BANKS", bindings)

    def test_empty_environment_selection_never_binds_invalid_zero_entry_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "environment"
            bindings = prepared_environment_packs.prepare({}, {"runtime_environment": {}}, output)
            self.assertNotIn("MW34_REMASTER_BANKS", bindings)
            self.assertFalse((output / "texture-banks.bin").exists())


def native_stage_tests(inputs):
    """Explicit Windows-only authored PE qualification; never substitutes for a native build."""
    import stage_mw3_re_runtime as producer

    class NativeStageTests(unittest.TestCase):
        def setUp(self):
            self.temporary = tempfile.TemporaryDirectory(prefix="mw34-native-stage-")
            self.addCleanup(self.temporary.cleanup)
            self.root = Path(self.temporary.name)
            self.release = self.root / "Release"
            self.release.mkdir()
            self.executable = self.release / "mw34_native_stage_fixture.exe"
            self.library = self.release / "mw34_normal_hash.dll"
            shutil.copyfile(inputs.native_stage_fixture_exe, self.executable)
            shutil.copyfile(inputs.native_stage_fixture_dll, self.library)
            self.notice = self.root / "LICENSE.txt"
            self.notice.write_text("Authored fixture notice; not a native-game distribution.\n",
                                   encoding="utf-8")
            self.output = self.root / "payload"
            self.environment = {
                key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP")
                if key in os.environ
            }
            self.environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
            self.environment["NoDefaultCurrentDirectoryInExePath"] = "1"
            self.components = [dict(name="authored-stage-fixture", version="1",
                                    source="project-authored-test", notices=["LICENSE.txt"])]

        def inventory(self, **changes):
            arguments = dict(executable=self.executable, release_roots=[self.release],
                             crt_root=Path(inputs.crt_root), dumpbin=Path(inputs.dumpbin),
                             notices={"LICENSE.txt": self.notice}, components=self.components,
                             source_commit="a" * 40, builder="authored-stage-fixture",
                             environment=self.environment)
            arguments.update(changes)
            return producer.make_inventory(**arguments)

        def assertIncomplete(self):
            self.assertFalse((self.output / "runtime.json").exists())
            self.assertTrue((self.output / ".incomplete").is_file())

        def test_real_pe_closure_and_production_planning(self):
            before = {path: producer.file_hash(path) for path in (self.executable, self.library, self.notice)}
            inventory = self.inventory()
            producer.stage_inventory(inventory, self.output)
            descriptor = json.loads((self.output / "runtime.json").read_text(encoding="utf-8"))
            self.assertEqual(descriptor["roles"], dict(executable="bin/mw3.exe", profile="profile.json"))
            self.assertEqual(descriptor["capabilities"], {})
            self.assertIn("bin/mw34_normal_hash.dll", descriptor["dependencies"])
            self.assertTrue(any(name.lower().startswith("bin/vcruntime") for name in descriptor["files"]))
            physical = {path.relative_to(self.output).as_posix() for path in self.output.rglob("*") if path.is_file()}
            self.assertEqual(physical, set(descriptor["files"]) | {"runtime.json"})
            self.assertEqual(set(descriptor["files"]), set(descriptor["roles"].values()) | set(descriptor["dependencies"]))
            for name, pin in descriptor["files"].items():
                member = self.output / name
                self.assertEqual(member.stat().st_size, pin["bytes"])
                self.assertEqual(producer.file_hash(member), pin["sha256"])
            witness = json.loads((self.output / "metadata/build-observation.json").read_text(encoding="utf-8"))
            self.assertEqual(witness["kind"], "local-build-staging-observation-v1")
            self.assertEqual(witness["assurance"], "observational-only-not-authenticated")
            self.assertEqual(witness["builder"], "authored-stage-fixture")
            self.assertNotIn("runtime.json", witness["artifacts"])
            self.assertNotIn("metadata/build-observation.json", witness["artifacts"])
            self.assertEqual(witness["external_prerequisites"], ["Windows x64", "Vulkan loader and driver"])
            game, data = self.root / "original game", self.root / "user data"
            command = [inputs.stage_plan_tool, "--mw3-re-stage-plan", str(self.output),
                       str(game), str(data), "fixture-a"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            planned = json.loads(result.stdout)
            expected_write = str(data / "mw3-re/profiles/fixture-a")
            self.assertEqual(planned, dict(ok=True, working_directory=str(self.output / "bin"),
                argv=[str(self.output / "bin/mw3.exe"), "--install", str(game), "--write-dir", expected_write,
                      "--cc-vulkan-wsi", "--window", "1280x720", "--windowed", "--cc-aa", "fxaa",
                      "--cc-af", "16", "--cc-render-thread", "1", "--cc-lighting", "off"]))
            profile_path = self.output / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["options"]["aa"] = "8"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            descriptor["files"]["profile.json"] = dict(bytes=profile_path.stat().st_size,
                                                       sha256=producer.file_hash(profile_path))
            (self.output / "runtime.json").write_text(json.dumps(descriptor), encoding="utf-8")
            blocked = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(blocked.returncode, 0, blocked.stdout + blocked.stderr)
            blocked_plan = json.loads(blocked.stdout)
            self.assertFalse(blocked_plan["ok"])
            self.assertNotIn("argv", blocked_plan)
            self.assertTrue(blocked_plan["reasons"])
            self.assertEqual(json.loads(profile_path.read_text())["options"]["aa"], "8")
            self.assertFalse(game.exists())
            self.assertFalse(data.exists())
            self.assertEqual(before, {path: producer.file_hash(path) for path in before})

        def test_missing_application_dll(self):
            self.library.unlink()
            with self.assertRaisesRegex(ValueError, "Missing application dependency"):
                self.inventory()
            self.assertFalse(self.output.exists())

        def test_missing_app_local_crt(self):
            empty = self.root / "empty-crt"
            empty.mkdir()
            with self.assertRaisesRegex(ValueError, "Missing app-local CRT"):
                self.inventory(crt_root=empty)

        def test_ambiguous_application_dll(self):
            other = self.root / "other-release"
            other.mkdir()
            shutil.copyfile(self.library, other / self.library.name)
            with self.assertRaisesRegex(ValueError, "Ambiguous application dependency"):
                self.inventory(release_roots=[self.release, other])

        def test_selected_dll_precedes_real_system32_collision(self):
            # A compiled authored DLL receives an OS basename only in this non-executing fixture.
            collision = self.release / "KERNEL32.dll"
            self.assertTrue((producer._system32() / collision.name).is_file())
            shutil.copyfile(self.library, collision)
            with patch.object(producer, "_inspect", wraps=producer._inspect) as inspected:
                inventory = self.inventory()
            members = {member.relative: member for member in inventory.members}
            self.assertIn("bin/KERNEL32.dll", members)
            self.assertIn(collision, [call.args[0] for call in inspected.call_args_list])
            self.assertEqual(members["bin/KERNEL32.dll"].sha256, producer.file_hash(collision))
            self.assertIn("bin/vcruntime140.dll", {name.lower() for name in members})
            producer.stage_inventory(inventory, self.output)
            self.assertEqual(producer.file_hash(self.output / "bin/KERNEL32.dll"), producer.file_hash(collision))
            other = self.root / "other-release"
            other.mkdir()
            shutil.copyfile(collision, other / collision.name)
            with self.assertRaisesRegex(ValueError, "Ambiguous application dependency"):
                self.inventory(release_roots=[self.release, other])

        def test_inspection_output_is_capped_while_child_runs(self):
            pid_path = self.root / "inspection-child.pid"
            completed = self.root / "inspection-output-completed"
            script = (
                "import os,sys,time; from pathlib import Path; "
                "Path(sys.argv[1]).write_text(str(os.getpid())); "
                "[(os.write(1,b'x'*8192),os.write(2,b'y'*8192)) for _ in range(1024)]; "
                "Path(sys.argv[2]).write_text('captured all 16MiB'); time.sleep(.1)"
            )
            before = time.monotonic()
            with self.assertRaisesRegex(ValueError, "Excessive dependency inspection output"):
                producer._capture_inspection([sys.executable, "-I", "-c", script, str(pid_path), str(completed)],
                                             self.environment, self.root)
            self.assertLess(time.monotonic() - before, 5)
            self.assertTrue(pid_path.is_file())
            self.assertFalse(completed.exists(), "Output was only capped after the child completed.")
            process_id = int(pid_path.read_text())
            # OpenProcess with SYNCHRONIZE: a returned handle must already be signaled.
            import ctypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.restype = ctypes.c_void_p
            handle = kernel.OpenProcess(0x00100000, False, process_id)
            if handle:
                try:
                    kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
                    self.assertEqual(kernel.WaitForSingleObject(handle, 0), 0)
                finally:
                    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
                    kernel.CloseHandle(handle)
            else:
                self.assertEqual(ctypes.get_last_error(), 87, "Cannot establish inspection-child exit.")

        def test_inspection_timeout_reaps_child(self):
            before = time.monotonic()
            with self.assertRaisesRegex(ValueError, "inspection timed out"):
                producer._capture_inspection([sys.executable, "-I", "-c", "import time; time.sleep(10)"],
                                             self.environment, self.root, timeout=.1)
            self.assertLess(time.monotonic() - before, 3)

        def test_api_and_ext_sets_are_recognized_inspection_names(self):
            text = ("Dump of file authored.exe\nFile Type: EXECUTABLE IMAGE\n"
                    "Image has the following dependencies:\n"
                    "api-ms-win-crt-runtime-l1-1-0.dll\next-ms-win-authored-l1-1-0.dll\nSummary\n")
            self.assertEqual(producer._parse_dependents(text),
                             ["api-ms-win-crt-runtime-l1-1-0.dll", "ext-ms-win-authored-l1-1-0.dll"])

        def test_required_notice_and_unsafe_member_names(self):
            self.notice.unlink()
            with self.assertRaises((ValueError, OSError)):
                self.inventory()
            self.notice.write_text("authored notice", encoding="utf-8")
            for name in ("../escape", "bin/CON.txt", "bin/file.", "bin//file", "bin\\file",
                         "runtime.json", "PROFILE.json", "profile.json"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    self.inventory(notices={"LICENSE.txt": self.notice, name: self.notice},
                                   components=[dict(self.components[0], notices=["LICENSE.txt", name])])
            valid = "licenses/fixture/LICENSE.txt"
            self.inventory(notices={"LICENSE.txt": self.notice, valid: self.notice},
                           components=[dict(self.components[0], notices=["LICENSE.txt", valid])])
            for first, second in (("licenses/same.txt", "licenses/SAME.txt"),
                                  ("licenses/file", "licenses/file/child")):
                with self.subTest(paths=(first, second)), self.assertRaisesRegex(ValueError, "alias"):
                    self.inventory(notices={"LICENSE.txt": self.notice, first: self.notice, second: self.notice},
                                   components=[dict(self.components[0], notices=["LICENSE.txt", first, second])])

        def test_existing_and_overlapping_destinations(self):
            inventory = self.inventory()
            self.output.mkdir()
            with self.assertRaisesRegex(ValueError, "already exists"):
                producer.stage_inventory(inventory, self.output)
            for output in (self.release / "payload", self.root):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    producer.stage_inventory(inventory, output)

        def test_inventory_budget_precedes_source_hashing(self):
            with patch.object(producer, "MAX_CLOSURE_BYTES", 1), \
                 patch.object(producer, "file_hash", side_effect=AssertionError("premature hash")):
                with self.assertRaisesRegex(ValueError, "budget"):
                    self.inventory()
            self.assertFalse(self.output.exists())

        def test_changed_source_after_inventory(self):
            inventory = self.inventory()
            self.library.write_bytes(self.library.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "Source changed"):
                producer.stage_inventory(inventory, self.output)
            self.assertIncomplete()

        def test_destination_hash_is_independent(self):
            inventory = self.inventory()
            original = producer._copy_member
            def corrupt(member, destination):
                original(member, destination)
                destination.write_bytes(b"x" * member.bytes)
            with patch.object(producer, "_copy_member", side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, "Destination"):
                    producer.stage_inventory(inventory, self.output)
            self.assertIncomplete()

        def test_extra_physical_member_blocks_completion(self):
            inventory = self.inventory()
            original = producer._copy_member
            def extra(member, destination):
                original(member, destination)
                (self.output / "unexpected.txt").write_text("authored extra", encoding="utf-8")
            with patch.object(producer, "_copy_member", side_effect=extra):
                with self.assertRaisesRegex(ValueError, "physical inventory"):
                    producer.stage_inventory(inventory, self.output)
            self.assertIncomplete()

        def test_linked_input_ancestor(self):
            linked = self.root / "linked"
            result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(linked), str(self.release)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.addCleanup(lambda: linked.rmdir())
            with self.assertRaisesRegex(ValueError, "link"):
                self.inventory(executable=linked / self.executable.name)

        def test_inspection_failure_and_false_empty_success(self):
            bad_outputs = ("", "unrecognized localized output", "Dump of file x\nFile Type: EXECUTABLE IMAGE\n",
                           "Dump of file x\nFile Type: EXECUTABLE IMAGE\n  Image has the following dependencies:\n    ../evil.dll\n  Summary\n")
            for text in bad_outputs:
                with self.subTest(output=text), self.assertRaises(ValueError):
                    producer._parse_dependents(text)
            with self.assertRaisesRegex(ValueError, "inspection failed"):
                producer._capture_inspection([sys.executable, "-I", "-c", "import sys; sys.exit(7)"],
                                             self.environment, self.root)

    return NativeStageTests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("native-stage-fixture-exe", "native-stage-fixture-dll", "dumpbin", "crt-root", "stage-plan-tool"):
        parser.add_argument("--" + name)
    inputs, remaining = parser.parse_known_args()
    supplied = vars(inputs)
    if any(supplied.values()):
        if os.name != "nt" or not all(supplied.values()):
            parser.error("Explicit native staging requires Windows and all five fixture/tool inputs.")
        for name, value in supplied.items():
            path = Path(value)
            if not path.is_absolute() or not (path.is_dir() if name == "crt_root" else path.is_file()):
                parser.error("Missing or non-absolute fixture/tool input: " + name)
        NativeStageTests = native_stage_tests(inputs)
        unittest.main(argv=[sys.argv[0], *remaining], defaultTest="NativeStageTests")
    else:
        unittest.main(argv=[sys.argv[0], *remaining])
