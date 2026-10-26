"""Check GUI launch options cross the asset-preparation boundary without a game."""

import os
import sys
import types
import unittest
import tempfile
import json
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


if __name__ == "__main__":
    unittest.main()
