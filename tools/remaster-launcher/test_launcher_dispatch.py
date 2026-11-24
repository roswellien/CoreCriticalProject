"""Check GUI launch options cross the asset-preparation boundary without a game."""

import os
import sys
import types
import unittest
import tempfile
import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import play_remaster


class LauncherDispatchTests(unittest.TestCase):
    def test_environment_preparation_cannot_replace_installed_enemy_skin_bindings(self):
        # Observed session: the model plan had B-H bindings, while the final
        # environment/profile retained only the historical Bushwacker-D pair.
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            model_bindings = {
                f'MW34_{chassis}{lod}_SKIN_{skin}_TEXTURES': str(output / f'{chassis}{lod}-{skin}.bin')
                for chassis in ('BUSHWACKER', 'THOR') for lod in ('', '_LOD1') for skin in 'BCDEFGH'
            }
            model_bindings['MW34_THOR_MESH'] = str(output / 'thor.bin')
            native = dict(runtime_environment=dict(model_bindings))
            planned = dict(backend='native', graphics=dict(width=1280,height=720,aa=1,af=1),
                           supported=True, texture_banks=1,
                           models=[dict(id='thor',name='Thor',status='runtime-ready')],
                           offline_models=[],limitations=[],command=['powershell.exe','-Profile','old.json'],
                           music=None,asset_output=str(output),prepared_profile=dict(native=native),environment_packs={})
            stale = {'MW34_BUSHWACKER_SKIN_D_TEXTURES': 'stale-developer-skin.bin',
                     'MW34_ORION_MESH': 'disabled-old-model.bin',
                     'MW34_REMASTER_BANKS': 'prepared-banks.bin'}
            with (patch.object(sys,'argv',['play_remaster','--prepare-only','--asset-output',str(output)]),
                  patch.object(play_remaster,'plan',return_value=planned),
                  patch.object(play_remaster,'read_json',return_value={'native':{'executable':'authored.exe'}}),
                  patch.dict(sys.modules,{'native_assets':types.SimpleNamespace(prepare=lambda *a,**kw:dict(model_bindings))}),
                  patch('startup_cache.environment_resources',return_value=stale)):
                self.assertEqual(play_remaster.main(),0)
            profiles=list((output/'launches').glob('*/profile.json'))
            self.assertEqual(len(profiles),1)
            actual=json.loads(profiles[0].read_text())['native']['runtime_environment']
            for key,value in model_bindings.items(): self.assertEqual(actual.get(key),value,key)
            self.assertEqual(actual['MW34_REMASTER_BANKS'],'prepared-banks.bin')
            self.assertNotIn('MW34_ORION_MESH',actual)

    def run_launch(self, *extra, dynamic_lighting=None):
        graphics = dict(width=3440, height=1440, aa="fxaa", af=16, window_mode="fullscreen")
        planned = dict(
            backend="native",
            graphics=graphics,
            supported=True,
            texture_banks=39,
            models=[dict(id="bushwacker", name="Bushwacker", status="runtime-ready")],
            offline_models=[],
            limitations=[],
            command=["powershell.exe", "-Profile", "session.json"],
            music=None,
            asset_output=None,
        )
        assets = types.SimpleNamespace(
            prepare=lambda *a, **kw: {"MW34_BUSHWACKER_TEST": "prepared-mesh.bin"}
        )
        executable = Path(__file__).resolve()
        native_profile = {"executable": "native.exe", "sun_preset": {"default": "sunset", "source": "authored-presets.json", "map": "BIG LAKE"}}
        if dynamic_lighting is not None:
            native_profile["presentation"] = {"dynamic_lighting": dynamic_lighting}
        with (
            patch.object(
                sys,
                "argv",
                ["play_remaster", "--game-exe", str(executable), "--instant-replay", "1", *extra],
            ),
            patch.object(play_remaster, "plan", return_value=planned) as plan,
            patch.object(
                play_remaster,
                "read_json",
                return_value={"native": native_profile},
            ),
            patch.dict(sys.modules, {"native_assets": assets}),
            patch.dict(os.environ, {"MW34_STALE_MODEL": "wrong", "MW34_WIDTH": "1920"}),
            patch.object(
                play_remaster.subprocess,
                "run",
                return_value=types.SimpleNamespace(
                    returncode=0, stdout='{"map":"Big Lake","preset":"sunset"}', stderr=""
                ),
            ),
            patch.object(play_remaster.subprocess, "call", return_value=0) as call,
        ):
            self.assertEqual(play_remaster.main(), 0)
        return plan, call, executable

    def test_prepared_models_resolution_and_explicit_options_reach_native_launcher(self):
        _, call, executable = self.run_launch()
        command = call.call_args.args[0]
        environment = call.call_args.kwargs["env"]
        self.assertEqual(environment["MW34_REMASTER_WIDTH"], "3440")
        self.assertEqual(environment["MW34_REMASTER_HEIGHT"], "1440")
        self.assertEqual(environment["MW34_BUSHWACKER_TEST"], "prepared-mesh.bin")
        self.assertNotIn("MW34_STALE_MODEL", environment)
        self.assertNotIn("MW34_WIDTH", environment)
        self.assertEqual(command[command.index("-InstantReplay") + 1], "1")
        self.assertEqual(command[command.index("-GameExe") + 1], str(executable))

    def test_original_model_choice_is_passed_to_registry_planning(self):
        plan, _, _ = self.run_launch("--original-models")
        self.assertTrue(plan.call_args.args[1])

    def test_profile_registry_is_not_overridden_by_an_implicit_cli_default(self):
        plan, _, _ = self.run_launch()
        self.assertIsNone(plan.call_args.kwargs["registry_path"])

    def test_explicit_registry_is_forwarded(self):
        plan, _, _ = self.run_launch("--registry", "comparison-registry.json")
        self.assertEqual(plan.call_args.kwargs["registry_path"], Path("comparison-registry.json"))

    def test_profile_lighting_default_keeps_automatic_campaign_selection(self):
        _, call, _ = self.run_launch()
        self.assertNotIn("-LightingPreset", call.call_args.args[0])

    def test_explicit_lighting_preset_requests_manual_selection(self):
        _, call, _ = self.run_launch("--lighting-preset", "sunset")
        command = call.call_args.args[0]
        self.assertEqual(command[command.index("-LightingPreset") + 1], "sunset")

    def test_dynamic_lighting_off_ignores_pack_sun_preset(self):
        with patch.object(play_remaster.subprocess, "run") as resolve:
            _, call, _ = self.run_launch(dynamic_lighting=False)
        self.assertNotIn("-LightingPreset", call.call_args.args[0])
        resolve.assert_not_called()


class LegacyRoutingTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows coordinator guard")
    def test_powershell_preflight_rejects_decoded_duplicates(self):
        harness = r'''
param($Coordinator, $Cases)
$ErrorActionPreference = 'Stop'
$tokens = $null; $parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($Coordinator, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Coordinator syntax error' }
foreach ($function in $ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]}, $true)) {
    Invoke-Expression $function.Extent.Text
}
$results = foreach ($case in (Get-Content -LiteralPath $Cases -Raw | ConvertFrom-Json)) {
    $raw = [string]::new([char[]]$case.units)
    if ($null -ne $case.repeat) { $raw = $raw + [string]::new([char]$case.fill, [int]$case.repeat) + [string]$case.suffix }
    $inputUnits = if ($null -ne $case.repeat) { @() } else { @($raw.ToCharArray() | ForEach-Object { [int]$_ }) }
    $inputBytes = [Text.Encoding]::UTF8.GetByteCount($raw)
    $baselineAccepted = $true
    if ($case.compat) { try { $null = ConvertFrom-Json -InputObject $raw } catch { $baselineAccepted = $false } }
    $beforeLocation = (Get-Location).Path
    $beforeEnvironment = [Environment]::GetEnvironmentVariable('MW34_TDD_SENTINEL', 'Process')
    $leaked = $false
    $snapshotMatches = $true
    $fileUnchanged = $true
    $fileClosed = $true
    $filePath = $null
    if ($case.phase -eq 'file') {
        $encoding = if ($case.utf16) { [Text.Encoding]::Unicode } else { [Text.Encoding]::UTF8 }
        [byte[]]$fileBytes = $encoding.GetBytes($raw)
        if ($case.bom) { $fileBytes = $encoding.GetPreamble() + $fileBytes }
        $filePath = Join-Path (Split-Path $Cases -Parent) ($case.id + '.json')
        [IO.File]::WriteAllBytes($filePath, $fileBytes)
    }
    try {
        if ($case.phase -eq 'preflight') { $null = Assert-UniqueLegacyJson $raw }
        elseif ($case.phase -eq 'file') { $snapshotMatches = (Read-LegacyProfileSnapshot $filePath) -ceq $raw }
        else { $null = ConvertFrom-LegacyLaunchProfile $raw }
        $message = ''
    }
    catch {
        $message = $_.Exception.Message
        $outward = ($_ | Out-String) + $_.Exception.ToString() + [string]$_.ErrorDetails + [string]$_.TargetObject
        $leaked = $outward.Contains('D3_AUTHORED_')
    }
    if ($null -ne $filePath) {
        $fileUnchanged = [Convert]::ToBase64String([IO.File]::ReadAllBytes($filePath)) -ceq [Convert]::ToBase64String($fileBytes)
        try { $exclusive = [IO.File]::Open($filePath, 'Open', 'ReadWrite', 'None'); $exclusive.Dispose() }
        catch { $fileClosed = $false }
    }
    @{id=$case.id;message=$message;leaked=$leaked;input_units=@($inputUnits);input_bytes=$inputBytes;snapshot_matches=$snapshotMatches;file_unchanged=$fileUnchanged;file_closed=$fileClosed;baseline_accepted=$baselineAccepted;major=$PSVersionTable.PSVersion.Major;cwd_unchanged=((Get-Location).Path -eq $beforeLocation);
      environment_unchanged=([Environment]::GetEnvironmentVariable('MW34_TDD_SENTINEL', 'Process') -eq $beforeEnvironment)}
}
ConvertTo-Json -InputObject @($results) -Compress
'''
        cases = []
        for index, raw in enumerate([
            '{"schema_version":1,"native":{},"values":[1,1],"data":[{"item":1},{"item":1}]}',
            '{"__type":"fixture","data":{"__type":"","quoted\\\"name":1}}',
            '{"__type":17,"data":{"__type":null}}',
            r'{"note":1,"\\u006eote":2}',
        ]):
            cases.append({"id": "valid-" + str(index), "raw": raw, "reason": ""})
        for index, raw in enumerate([
            '{"note":1,"note":2}', r'{"note":1,"\u006eote":2}',
            '{"data":[{"item":1,"item":2}]}', '{"":1,"":2}',
            '{"__type":"a","__type":"b"}', r'{"__type":"a","\u005f_type":"b"}',
            '{"data":{"__type":"","__type":"b"}}',
            '{"native":{"runtime_environment":{}},"native":{}}',
        ]):
            cases.append({"id": "duplicate-" + str(index), "raw": raw, "reason": "Duplicate JSON"})
        cases.append({"id": "empty-name-preflight", "raw": '{"":1}', "phase": "preflight", "reason": ""})
        for index, raw in enumerate([
            r'{"\ud800":1,"\ufffd":2}', r'{"\ud800":1,"\ud801":2}',
            r'{"\udc00":1,"\ufffd":2}', r'{"\udc00":1,"\udc01":2}',
            r'{"\ud800":1,"\udc00":2}', r'{"a\ud800b":1,"a\ufffdb":2}',
            r'{"\ud800\ud801\udc00":1,"\ufffd\ud801\udc00":2}',
            r'{"\ud800\udc00\ud800":1,"\ud800\udc00\ufffd":2}',
            '{"note":1,\'note\':2}', '{note:1,"note":2}',
        ]):
            cases.append({"id": "identity-duplicate-" + str(index), "raw": raw, "reason": "Duplicate JSON"})
        for index, raw in enumerate([
            r'{"\ud800":1}', r'{"\udc00":1}',
            r'{"\ud800\udc00":1,"\ufffd":2}',
            r'{"\ud800\udc00":1,"\ud800\udc01":2}',
        ]):
            cases.append({"id": "identity-valid-" + str(index), "raw": raw, "reason": ""})
        for index, raw in enumerate([
            '{"' + chr(0xD800) + '":1,"\\ufffd":2}',
            '{"' + chr(0xDC00) + '":1,"\\ufffd":2}',
            '{"' + chr(0xD800) + '":1,"\\ud800":2}',
            '{"' + chr(0xD800) + '\\udc00":1,"\\ud800\\udc00":2}',
            '{"\\ud800' + chr(0xDC00) + '":1,"\\ud800\\udc00":2}',
        ]):
            cases.append({"id": "identity-runtime-" + str(index), "raw": raw,
                          "reason": "Duplicate JSON", "reason7": ""})
        for index, raw in enumerate([
            '{"note":D3_AUTHORED_DIAGNOSTIC_SENTINEL}',
            '{D3_AUTHORED_KEY_SENTINEL!:1}',
        ]):
            cases.append({"id": "converter-diagnostic-" + str(index), "raw": raw,
                          "reason": "Invalid legacy profile JSON"})
        for index, raw in enumerate([
            '{"schema_version":1,"native":{},}', '{"a":1,/* authored */"b":2}',
            '{"a":1,// authored\n"b":2}', "{'a':1}", '{a:1}', '{a\\u0062:1}',
            '{"a":NaN}', '{"a":Infinity}', '{"a":undefined}', '{"a":0x10}',
            '{"a":new Date(1)}', '{"a":new Date(2020,1,2),"b":1}',
            '{"a":new Foo({"k":1}),"b":1}', '{17:1}', '{a.b:1}', '{a-b:1}', '{$a:1}',
            '{/*a*/b:1}', '{"a\nb":1}', '{"a":1} true', '{"__type":{}}', '{"":1}',
            '{a(b:1}', '{a)b:1}', '{a[b:1}', '{a{b:1}', '{a b:1}', '{a"b:1}',
            '{a/*b*/:1}', '{a/b:1}', '{a/*b*/ :1}', '{"a:1}',
            '{"a":new Foo(1),"b":1}', r'{"\x61":1}', r'{"\v":1}',
            '{"it\\\'s":1}',
        ]):
            cases.append({"id": "syntax-" + str(index), "raw": raw, "reason": "", "compat": True})
        for index, raw in enumerate([
            '{"a":1,/* } \\" ignored */"a":2}',
            '{"a":new Foo({"k":1,"k":2}),"b":1}',
            '{"a":new Date(2020,1,2),"b":1,"b":2}',
        ]):
            cases.append({"id": "syntax-duplicate-" + str(index), "raw": raw, "reason": "Duplicate JSON"})
        for depth in (64, 65):
            cases.append({"id": "depth-" + str(depth), "raw": '[' * depth + '0' + ']' * depth,
                          "phase": "preflight", "reason": "depth" if depth == 65 else ""})
        limit = 2 * 1024 * 1024
        prefix, suffix = '{"note":"', '"}'
        overhead = len((prefix + suffix).encode("utf-8"))
        for extra in (0, 1):
            cases.append({"id": "bytes-" + str(extra), "raw": prefix, "repeat": limit - overhead + extra,
                          "fill": ord('x'), "suffix": suffix, "phase": "preflight",
                          "expected_bytes": limit + extra, "reason": "large" if extra else ""})
            cases.append({"id": "file-bytes-" + str(extra), "raw": prefix, "repeat": limit - overhead + extra,
                          "fill": ord('x'), "suffix": suffix, "phase": "file", "reason": "large" if extra else ""})
        for utf16 in (False, True):
            cases.append({"id": "file-bom-" + str(utf16), "raw": '{"note":"é"}',
                          "phase": "file", "bom": True, "utf16": utf16, "reason": ""})
        for extra in (0, 1):
            multibyte_suffix = 'x' + suffix + (' ' if extra else '')
            count = (limit - len((prefix + 'x' + suffix).encode("utf-8"))) // len('é'.encode("utf-8"))
            cases.append({"id": "multibyte-" + str(extra), "raw": prefix, "repeat": count,
                          "fill": ord('é'), "suffix": multibyte_suffix, "phase": "preflight",
                          "expected_bytes": limit + extra, "reason": "large" if extra else ""})
        cases.append({"id": "wide-object", "raw": json.dumps({"key" + str(i): i for i in range(80)}),
                      "phase": "preflight", "reason": ""})
        for case in cases:
            encoded = case.pop("raw").encode("utf-16-le", errors="surrogatepass")
            case["units"] = [int.from_bytes(encoded[i:i + 2], "little") for i in range(0, len(encoded), 2)]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = root / "preflight.ps1"
            runner.write_text(harness, encoding="utf-8")
            case_file = root / "cases.json"
            case_file.write_text(json.dumps(cases), encoding="utf-8")
            coordinator = Path(play_remaster.__file__).with_name("play_native.ps1")
            for executable in [shutil.which("powershell.exe"), shutil.which("pwsh")]:
                if executable is None:
                    self.fail("Both supported PowerShell runtimes are prerequisites")
                completed = subprocess.run(
                    [executable, "-NoProfile", "-File", str(runner), str(coordinator), str(case_file)],
                    capture_output=True, text=True, timeout=120, check=True,
                )
                results = json.loads(completed.stdout)
                self.assertEqual(len(results), len(cases))
                for case, result in zip(cases, results):
                    with self.subTest(runtime=executable, case=case["id"]):
                        self.assertEqual(result["id"], case["id"])
                        self.assertEqual(result["input_units"], [] if "repeat" in case else case["units"], "Fixture transport changed raw UTF-16")
                        if "expected_bytes" in case:
                            self.assertEqual(result["input_bytes"], case["expected_bytes"])
                        reason = case.get("reason7", case["reason"]) if result["major"] >= 7 else case["reason"]
                        if case.get("compat"):
                            self.assertEqual(result["message"] == "", result["baseline_accepted"], "Legacy conversion acceptance changed")
                        elif reason:
                            self.assertIn(reason, result["message"])
                        else:
                            self.assertEqual(result["message"], "")
                        self.assertTrue(result["cwd_unchanged"])
                        self.assertTrue(result["environment_unchanged"])
                        self.assertFalse(result["leaked"], "Outward error exposed authored profile content")
                        self.assertTrue(result["snapshot_matches"])
                        self.assertTrue(result["file_unchanged"])
                        self.assertTrue(result["file_closed"], "Profile reader left a file handle open")

    @unittest.skipUnless(os.name == "nt", "Windows coordinator guard")
    def test_powershell_main_rejects_routing_before_cwd_and_environment_changes(self):
        harness = r'''
param($Coordinator, $ProfilePath, $TaskRoot)
$ErrorActionPreference = 'Stop'
$beforeLocation = (Get-Location).Path
$beforeEnvironment = [Environment]::GetEnvironmentVariable('MW34_TDD_SENTINEL', 'Process')
try { & $Coordinator -Profile $ProfilePath -RuntimeRoot $TaskRoot | Out-Null; $message = 'ACCEPTED' }
catch { $message = $_.Exception.Message }
@{message=$message; cwd_unchanged=((Get-Location).Path -eq $beforeLocation);
  environment_unchanged=([Environment]::GetEnvironmentVariable('MW34_TDD_SENTINEL', 'Process') -eq $beforeEnvironment)} | ConvertTo-Json -Compress
'''
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = self.profile_fixture(root)
            profile["native"]["executable"] = str(root / "must-not-exist.exe")
            profile["native"]["runtime_environment"] = {"MW34_TDD_SENTINEL": "changed"}
            path = root / "profile.json"
            runner = root / "guard.ps1"
            runner.write_text(harness, encoding="utf-8")
            coordinator = Path(play_remaster.__file__).with_name("play_native.ps1")
            controls = []
            for key, value in [("engine", "mw3-re"), ("Engine", None), ("schema_version", 2),
                               ("schema_version", True), ("Schema_Version", 1)]:
                tagged = dict(profile, **{key: value})
                if key == "Schema_Version":
                    del tagged["schema_version"]
                controls.append((json.dumps(tagged), "routing"))
            nested = dict(profile, native=dict(profile["native"], Engine="mw3-re"))
            controls.append((json.dumps(nested), "routing"))
            controls.append((json.dumps(profile)[:-1] + ',"note":1,"note":2}', "Duplicate JSON"))
            for executable in [shutil.which("powershell.exe"), shutil.which("pwsh")]:
                self.assertIsNotNone(executable, "Both supported PowerShell runtimes are prerequisites")
                if executable is None:
                    self.fail("Supported PowerShell runtime is missing")
                for raw, reason in controls:
                    path.write_text(raw, encoding="utf-8")
                    names_before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
                    completed = subprocess.run(
                        [executable, "-NoProfile", "-File", str(runner), str(coordinator), path.name, str(root)],
                        capture_output=True, text=True, timeout=30, check=True,
                    )
                    result = json.loads(completed.stdout)
                    with self.subTest(runtime=executable, reason=reason, raw=raw):
                        self.assertIn(reason, result["message"])
                        self.assertTrue(result["cwd_unchanged"])
                        self.assertTrue(result["environment_unchanged"])
                        self.assertEqual(path.read_text(encoding="utf-8"), raw)
                        self.assertEqual(sorted(str(p.relative_to(root)) for p in root.rglob("*")), names_before)

    @staticmethod
    def profile_fixture(root):
        host = root / "authored-host.exe"
        host.write_bytes(b"authored non-executed host fixture")
        return {
            "schema_version": 1,
            "backend": "native",
            "graphics": {"width": 1280, "height": 720, "aa": 1, "af": 1},
            "native": {
                "executable": str(host), "prepared_pack_roots": [],
                "runtime_environment": {}, "cumulative_texture_banks": True,
                "graphics_capabilities": {"width": 1280, "height": 720, "aa": 1, "af": 1},
                "content_capabilities": {},
            },
        }

    def test_real_legacy_plan_rejects_engine_tags_before_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = self.profile_fixture(root)
            path = root / "profile.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            control = play_remaster.plan(config_path=path)
            self.assertTrue(control["supported"])
            self.assertIn("play_native.ps1", control["command"][5])
            for key, value in [("engine", "mw3-re"), ("Engine", None), ("schema_version", 2),
                               ("schema_version", True), ("Schema_Version", 1)]:
                tagged = dict(profile, **{key: value})
                raw = json.dumps(tagged)
                path.write_text(raw, encoding="utf-8")
                before = dict(os.environ)
                with self.subTest(key=key, value=value), self.assertRaisesRegex(RuntimeError, "routing"):
                    play_remaster.plan(config_path=path)
                self.assertEqual(path.read_text(encoding="utf-8"), raw)
                self.assertEqual(dict(os.environ), before)

    def test_real_plan_rejects_raw_duplicate_keys_before_lossy_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = self.profile_fixture(root)
            path = root / "profile.json"
            control = json.dumps(profile)
            path.write_text(control, encoding="utf-8")
            self.assertTrue(play_remaster.plan(config_path=path)["supported"])
            for extra in [
                '"note":1,"note":2',
                '"note":1,"\\u006eote":2',
                '"data":[{"item":1,"item":2}]',
                '"data":{"__type":"a","__type":"b"}',
                '"data":{"":1,"":2}',
            ]:
                raw = control[:-1] + "," + extra + "}"
                path.write_text(raw, encoding="utf-8")
                with self.subTest(extra=extra), self.assertRaisesRegex(RuntimeError, "Duplicate JSON"):
                    play_remaster.plan(config_path=path)
                self.assertEqual(path.read_text(encoding="utf-8"), raw)


if __name__ == "__main__":
    unittest.main()
