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


def volume_guid_alias(path):
    """Resolve the actual test drive's alternate spelling without creating a mount or link."""
    import ctypes
    from ctypes import wintypes
    path = Path(path).absolute()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetVolumeNameForVolumeMountPointW.argtypes = (wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD)
    kernel.GetVolumeNameForVolumeMountPointW.restype = wintypes.BOOL
    volume = ctypes.create_unicode_buffer(32768)
    if not kernel.GetVolumeNameForVolumeMountPointW(path.anchor, volume, len(volume)):
        raise OSError(ctypes.get_last_error(), "Cannot resolve the required volume-GUID test alias")
    return Path(volume.value) / path.relative_to(path.anchor)


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

        def test_volume_alias_staging_overlap_precedes_any_mutation(self):
            from dataclasses import replace
            inventory = self.inventory()
            before = {path.relative_to(self.root).as_posix(): producer.file_hash(path)
                      for path in self.root.rglob("*") if path.is_file()}
            original_paths = {path.relative_to(self.root).as_posix() for path in self.root.rglob("*")}
            alias = volume_guid_alias(self.release)
            self.assertTrue(alias.is_dir())
            cases = ((inventory, alias / "missing-parent/payload"),
                     (replace(inventory, input_roots=(alias, Path(inputs.crt_root))),
                      self.release / "another-missing-parent/payload"))
            for candidate, output in cases:
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, "overlaps"):
                    producer.stage_inventory(candidate, output)
                self.assertFalse(output.exists())
                self.assertEqual(original_paths, {path.relative_to(self.root).as_posix() for path in self.root.rglob("*")})
                self.assertEqual(before, {path.relative_to(self.root).as_posix(): producer.file_hash(path)
                                         for path in self.root.rglob("*") if path.is_file()})
            hardlink = self.root / "same-file-hardlink.dll"
            os.link(self.library, hardlink)
            self.assertTrue(producer._paths_overlap(self.library, hardlink))
            producer.stage_inventory(inventory, self.output)
            self.assertTrue((self.output / "runtime.json").is_file())

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


def native_recipe_tests(inputs):
    """Real selected-tool/environment controls; these remain authored builds, never MW3 positives."""
    import stage_mw3_re_runtime as producer

    class NativeRecipeTests(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.temporary = tempfile.TemporaryDirectory(prefix="mw34-native-recipe-")
            cls.addClassCleanup(cls.temporary.cleanup)
            cls.root = Path(cls.temporary.name)
            cls.paths = {name: Path(getattr(inputs, name)) for name in ("git", "cmake", "ninja", "clang_cl", "dumpbin", "crt_root")}
            cls.paths["source"] = Path(__file__).resolve().parents[2]
            cls.environment, cls.derived, cls.system = producer.build_environment(
                Path(inputs.vs), cls.paths, cls.root, source=cls.paths["source"])
            cls.tools = producer._tool_observations(
                {key: value for key, value in cls.paths.items() if key in producer._TOOL_NAMES},
                cls.environment, cls.root)
            print("Selected recipe tools: " + json.dumps(cls.tools, sort_keys=True))
            cls.fixture, cls.flags = producer.build_qualification_fixture(
                cls.paths, cls.derived, cls.environment, cls.root / "clean")

        def test_selected_environment_strips_parent_controls(self):
            keys = ("CC", "CXX", "CFLAGS", "CXXFLAGS", "CL", "_CL_", "LINK", "_LINK_",
                    "CMAKE_TOOLCHAIN_FILE", "CMAKE_PREFIX_PATH", "VCPKG_ROOT",
                    "PKG_CONFIG_PATH", "GIT_EXEC_PATH", "AUTHORED_PACKAGE_ROOT", "HOME",
                    "USERPROFILE", "AUTHORED_CREDENTIAL_SENTINEL")
            parent = dict(os.environ)
            parent.update({key: "AUTHORED_PARENT_CONTROL" for key in keys})
            parent["NoDefaultCurrentDirectoryInExePath"] = "0"
            environment, _, _ = producer.build_environment(Path(inputs.vs), self.paths, self.root,
                                                           source=self.paths["source"], parent=parent)
            script = "import json,os,sys; print(json.dumps({k:os.environ.get(k) for k in sys.argv[1:]}))"
            received = json.loads(producer._run([sys.executable, "-I", "-c", script, *keys,
                                                "NoDefaultCurrentDirectoryInExePath"],
                                               environment, self.root))
            self.assertEqual({key: received[key] for key in keys}, dict.fromkeys(keys))
            self.assertEqual(received["NoDefaultCurrentDirectoryInExePath"], "1")
            self.assertEqual(Path(environment["PATH"].split(";")[0]), self.paths["git"].parent)
            _, flags = producer.build_qualification_fixture(self.paths, self.derived, environment,
                                                            self.root / "sanitized-parent-controls")
            self.assertEqual(flags, self.flags)

        def test_bootstrap_fetches_only_allowlisted_parent_values(self):
            from collections.abc import Mapping
            permitted = {name.swapcase(): os.environ[name] for name in producer._WINDOWS_KEYS if name in os.environ}
            class HostileParent(Mapping):
                def __iter__(self):
                    return iter([*permitted, "AUTHORED_VALUE_MUST_NOT_BE_READ", "NoDefaultCurrentDirectoryInExePath"])
                def __len__(self):
                    return len(permitted) + 2
                def __getitem__(self, name):
                    if name not in permitted:
                        raise AssertionError("Non-allowlisted parent value was accessed.")
                    return permitted[name]
            environment, _ = producer._bootstrap_base(self.root, HostileParent())
            self.assertEqual(environment["NoDefaultCurrentDirectoryInExePath"], "1")
            self.assertNotIn("AUTHORED_VALUE_MUST_NOT_BE_READ", environment)

        def test_real_cmake_git_guard_and_shadow_control(self):
            commit = producer._run([self.paths["git"], "-C", self.paths["source"], "rev-parse", "HEAD"],
                                   self.environment, self.root).decode().strip()
            guarded = producer.qualify_git_lookup(self.paths["source"], commit, self.paths,
                self.environment, self.fixture, self.root / "git-guarded")
            unsafe = producer.qualify_git_lookup(self.paths["source"], commit, self.paths,
                self.environment, self.fixture, self.root / "git-unsafe", unsafe_control=True)
            self.assertTrue(guarded["guarded"])
            self.assertFalse(unsafe["guarded"])
            self.assertEqual((self.root / "git-unsafe/result.txt").read_text().strip(), "MW34_AUTHORED_SHADOW_GIT")

        def test_actual_compiler_and_linker_parent_controls(self):
            controls = {"CXXFLAGS": "-DMW34_POISON_CXXFLAGS", "CFLAGS": "-DMW34_POISON_CFLAGS",
                        "CL": "/DMW34_POISON_CL", "_CL_": "/DMW34_POISON_UNDERSCORE_CL",
                        "LINK": "/INCLUDE:MW34_POISON_LINK"}
            for name, value in controls.items():
                with self.subTest(control=name):
                    injected = dict(os.environ, **{name: value})
                    sanitized, _, _ = producer.build_environment(Path(inputs.vs), self.paths, self.root,
                                                                  source=self.paths["source"], parent=injected)
                    self.assertNotIn(name, sanitized)
                    unsafe = dict(sanitized, **{name: value})
                    directory = self.root / ("unsafe-" + name)
                    with self.assertRaisesRegex(ValueError, "Selected external tool failed"):
                        producer.build_qualification_fixture(self.paths, self.derived, unsafe, directory)
                    diagnostics = "\n".join(path.read_text(errors="strict") for path in
                                           (directory / "configure.log", directory / "build.log") if path.exists())
                    if name == "_CL_":
                        # Clang21 appends _CL_ after CMake's "--"; retain that exact adverse oracle.
                        self.assertIn("clang-cl: error: no such file or directory: '/DMW34_POISON_UNDERSCORE_CL'",
                                      diagnostics)
                        direct = directory / "direct-compiler.log"
                        with self.assertRaisesRegex(ValueError, "Selected external tool failed"):
                            producer._run([self.paths["clang_cl"], "/nologo", "/c",
                                           "/Fo" + str(directory / "guard.obj"),
                                           self.root / "clean/source/guard.c"],
                                          unsafe, directory, log=direct)
                        self.assertIn("MW34_POISON_COMPILER_CONTROL", direct.read_text())
                        continue
                    expected = "MW34_POISON_LINK" if name == "LINK" else "MW34_POISON_COMPILER_CONTROL"
                    self.assertIn(expected, diagnostics)

        def test_toolchain_and_prefix_specific_oracles(self):
            toolchain = self.root / "poison-toolchain.cmake"
            marker = self.root / "toolchain-evaluated"
            toolchain.write_text("file(WRITE " + producer._cmake_literal(marker) +
                                 ' "evaluated")\nmessage(FATAL_ERROR "MW34_POISON_TOOLCHAIN")\n', encoding="utf-8")
            parent = dict(os.environ, CMAKE_TOOLCHAIN_FILE=str(toolchain))
            sanitized, _, _ = producer.build_environment(Path(inputs.vs), self.paths, self.root, parent=parent)
            self.assertNotIn("CMAKE_TOOLCHAIN_FILE", sanitized)
            with self.assertRaisesRegex(ValueError, "Selected external tool failed"):
                producer.build_qualification_fixture(self.paths, self.derived,
                    dict(sanitized, CMAKE_TOOLCHAIN_FILE=str(toolchain)), self.root / "unsafe-toolchain")
            self.assertTrue(marker.is_file())
            self.assertIn("MW34_POISON_TOOLCHAIN", (self.root / "unsafe-toolchain/configure.log").read_text())
            prefix = self.root / "poison-prefix"
            prefix.mkdir()
            prefix_marker = self.root / "prefix-evaluated"
            (prefix / "MW34MarkerConfig.cmake").write_text(
                "file(WRITE " + producer._cmake_literal(prefix_marker) + ' "found")\nset(MW34Marker_FOUND TRUE)\n', encoding="utf-8")
            configure_source = self.root / "clean/source"
            for restored, search_enabled in ((False, False), (True, False), (True, True)):
                directory = self.root / ("prefix-" + str(restored) + "-" + str(search_enabled))
                directory.mkdir()
                command, _ = producer.configure_arguments(self.paths, self.derived, configure_source, directory / "build")
                if search_enabled:
                    command.append("-DCMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH=TRUE")
                environment = dict(sanitized)
                if restored:
                    environment["CMAKE_PREFIX_PATH"] = str(prefix)
                producer._run(command, environment, directory, timeout=180, log=directory / "configure.log")
                self.assertEqual(prefix_marker.exists(), restored and search_enabled)

        def test_configured_dependency_roots_and_escape(self):
            result = producer._validate_edges(self.paths, self.environment, self.system, self.fixture,
                                               target="mw34_native_stage_fixture")
            self.assertTrue(result["selected_root_checks"])
            reply = self.fixture / ".cmake/api/v1/reply"
            target = next(reply.glob("target-mw34_normal_hash-*.json"))
            original = target.read_bytes()
            modified = json.loads(original)
            outside = self.root / "outside-include"
            outside.mkdir()
            modified["compileGroups"][0].setdefault("includes", []).append(dict(path=str(outside)))
            target.write_text(json.dumps(modified), encoding="utf-8")
            try:
                with self.assertRaisesRegex(ValueError, "dependency escapes"):
                    producer._validate_edges(self.paths, self.environment, self.system, self.fixture,
                                              target="mw34_native_stage_fixture")
            finally:
                target.write_bytes(original)

        def test_bad_cache_controls_stop_before_native_build(self):
            cache = producer._cache(self.fixture / "CMakeCache.txt")
            _, expected = producer.configure_arguments(self.paths, self.derived, self.root / "clean/source", self.fixture)
            native = dict(MW3_PACKAGE="ON", MW3_CORE_CRITICAL_VULKAN="ON",
                          CMAKE_DISABLE_FIND_PACKAGE_SDL3_sound="TRUE")
            cache.update(native)
            expected.update(native)
            cases = (("CMAKE_CXX_COMPILER", str(self.root / "other.exe"), "selected path mismatch"),
                     ("CMAKE_BUILD_TYPE", "Debug", "recipe option mismatch"),
                     ("MW3_PACKAGE", "OFF", "recipe option mismatch"),
                     ("MW3_CORE_CRITICAL_VULKAN", "OFF", "recipe option mismatch"),
                     ("CMAKE_DISABLE_FIND_PACKAGE_SDL3_sound", "FALSE", "recipe option mismatch"),
                     ("CMAKE_TOOLCHAIN_FILE", "poison", "Unexpected configured toolchain"),
                     ("CMAKE_CXX_FLAGS_RELEASE", "/DMW34_POISON", "non-clean recipe flags"))
            for name, value, error in cases:
                with self.subTest(field=name), self.assertRaisesRegex(ValueError, error):
                    producer._validate_configured(self.paths, self.derived, dict(cache, **{name: value}),
                                                   expected, self.flags, self.fixture, {})

        def test_actual_pe_architecture_and_kind_are_required(self):
            original = Path(inputs.native_stage_fixture_exe).read_bytes()
            offset = int.from_bytes(original[60:64], "little")
            for name, position, value in (("wrong-machine", offset + 4, b"\x4c\x01"),
                                           ("dll-as-exe", offset + 22,
                                            (int.from_bytes(original[offset + 22:offset + 24], "little") | 0x2000).to_bytes(2, "little"))):
                path = self.root / (name + ".exe")
                changed = bytearray(original)
                changed[position:position + 2] = value
                path.write_bytes(changed)
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Expected an x64"):
                    producer._pe(path, library=False)

        def test_recipe_destinations_and_cpu_are_rejected_before_mutation(self):
            from argparse import Namespace
            arguments = dict(self.paths, vs=Path(inputs.vs), commit="a" * 40, jobs=1,
                             build=self.root / "never-built", output=self.root / "never-staged")
            for name in ("sdl3", "sdl3_ttf", "archive_prefix", "vulkan_headers", "ttf_notices"):
                directory = self.root / ("path-" + name)
                directory.mkdir()
                arguments[name] = directory
            for name in ("glslang", "dxc"):
                arguments[name] = self.root / producer._TOOL_NAMES[name]
                arguments[name].write_bytes(b"authored invalid tool; never executed")
            for name in ("archive_lib", "zlib_lib", "lzma_lib"):
                arguments[name] = self.root / (name + ".lib")
                arguments[name].write_bytes(b"authored invalid library; never linked")
            existing = self.root / "existing-destination"
            existing.mkdir()
            for changes, reason in ((dict(jobs=0), "CPU budget"), (dict(jobs=9), "CPU budget"),
                                    (dict(build=existing), "already exists"),
                                    (dict(output=arguments["source"] / "owned-stage-must-not-exist"), "overlaps"),
                                    (dict(output=arguments["build"] / "nested"), "overlap")):
                candidate = {key: str(value) if isinstance(value, Path) else value
                             for key, value in dict(arguments, **changes).items()}
                with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, reason):
                    producer._recipe_paths(Namespace(**candidate))
            source_alias = volume_guid_alias(arguments["source"])
            root_alias = volume_guid_alias(self.root)
            for changes in (dict(build=source_alias / "owned-stage-must-not-exist"),
                            dict(output=source_alias / "owned-stage-must-not-exist"),
                            dict(source=source_alias, output=arguments["source"] / "owned-stage-must-not-exist"),
                            dict(output=root_alias / arguments["build"].name)):
                candidate = {key: str(value) if isinstance(value, Path) else value
                             for key, value in dict(arguments, **changes).items()}
                with self.subTest(alias_changes=changes), self.assertRaisesRegex(ValueError, "overlap"):
                    producer._recipe_paths(Namespace(**candidate))
                self.assertFalse(Path(candidate["build"]).exists())
                self.assertFalse(Path(candidate["output"]).exists())
            ordinary = {key: str(value) if isinstance(value, Path) else value for key, value in arguments.items()}
            normalized = producer._recipe_paths(Namespace(**ordinary))
            self.assertEqual(normalized["build"], arguments["build"])
            self.assertEqual(normalized["output"], arguments["output"])
            self.assertFalse(arguments["build"].exists())
            self.assertFalse(arguments["output"].exists())

        def test_real_git_observation_rejects_stale_and_dirty_source(self):
            repository = self.root / "authored-repository"
            repository.mkdir()
            def git(*arguments):
                return producer._run([self.paths["git"], "-C", repository,
                    "-c", "core.hooksPath=NUL", "-c", "commit.gpgsign=false", *arguments],
                    self.environment, self.root).decode().strip()
            git("init")
            for name in ("CMakeLists.txt", "AGENTS.md", "runtime/mw3-re/CMakeLists.txt",
                         "tests/native_stage_fixture.cpp", "tools/remaster-launcher/normal_hash.cpp"):
                path = repository / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("authored Git observation control\n", encoding="utf-8")
            git("add", ".")
            git("-c", "user.name=Authored Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Create authored Git fixture")
            commit = git("rev-parse", "HEAD")
            producer._source_identity(repository, self.paths["git"], self.environment, commit)
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                producer._source_identity(repository, self.paths["git"], self.environment, "a" * 40)
            (repository / "AGENTS.md").write_text("changed authored input\n")
            with self.assertRaisesRegex(ValueError, "Dirty tracked"):
                producer._source_identity(repository, self.paths["git"], self.environment, commit)

        def test_producer_ownership_conflict_is_visible(self):
            with producer._producer_ownership():
                with self.assertRaisesRegex(ValueError, "Another owned native producer"):
                    with producer._producer_ownership():
                        self.fail("A duplicate producer acquired ownership.")

        def test_timeout_stops_owned_grandchild(self):
            child_pid = self.root / "owned-child.pid"
            grandchild_pid = self.root / "owned-grandchild.pid"
            script = ("import os,sys,time,subprocess;from pathlib import Path;"
                      "Path(sys.argv[1]).write_text(str(os.getpid()));"
                      "subprocess.Popen([sys.executable,'-I','-c',"
                      "'import os,sys,time;from pathlib import Path;Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(20)',sys.argv[2]]);time.sleep(20)")
            with self.assertRaisesRegex(ValueError, "inspection timed out"):
                producer._capture_inspection([sys.executable, "-I", "-c", script, str(child_pid), str(grandchild_pid)],
                                             self.environment, self.root, timeout=1)
            import ctypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32)
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
            kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
            for path in (child_pid, grandchild_pid):
                self.assertTrue(path.is_file())
                handle = kernel.OpenProcess(0x00100000, False, int(path.read_text()))
                if handle:
                    try:
                        self.assertEqual(kernel.WaitForSingleObject(handle, 1000), 0)
                    finally:
                        kernel.CloseHandle(handle)
                else:
                    self.assertEqual(ctypes.get_last_error(), 87)

    return NativeRecipeTests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("native-stage-fixture-exe", "native-stage-fixture-dll", "dumpbin", "crt-root", "stage-plan-tool"):
        parser.add_argument("--" + name)
    for name in ("vs", "git", "cmake", "ninja", "clang-cl"):
        parser.add_argument("--" + name)
    inputs, remaining = parser.parse_known_args()
    recipe_names = ("vs", "git", "cmake", "ninja", "clang_cl")
    supplied = {name: value for name, value in vars(inputs).items() if name not in recipe_names}
    if any(supplied.values()):
        if os.name != "nt" or not all(supplied.values()):
            parser.error("Explicit native staging requires Windows and all five fixture/tool inputs.")
        for name, value in supplied.items():
            path = Path(value)
            if not path.is_absolute() or not (path.is_dir() if name == "crt_root" else path.is_file()):
                parser.error("Missing or non-absolute fixture/tool input: " + name)
        NativeStageTests = native_stage_tests(inputs)
        selected = ["NativeStageTests"]
        recipe = {name: getattr(inputs, name) for name in recipe_names}
        if any(recipe.values()):
            if not all(recipe.values()):
                parser.error("Recipe qualification requires all five explicit selected tool inputs.")
            for name, value in recipe.items():
                path = Path(value)
                if not path.is_absolute() or not (path.is_dir() if name == "vs" else path.is_file()):
                    parser.error("Missing explicit recipe tool input: " + name)
            NativeRecipeTests = native_recipe_tests(inputs)
            selected.append("NativeRecipeTests")
        unittest.main(argv=[sys.argv[0], *remaining], defaultTest=selected)
    else:
        if any(getattr(inputs, name) for name in recipe_names):
            parser.error("Recipe tools also require the five explicit PE fixture inputs.")
        unittest.main(argv=[sys.argv[0], *remaining])
