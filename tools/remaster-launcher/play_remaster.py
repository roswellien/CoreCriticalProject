"""Validate a local launch profile, prepare its assets, then start its backend.

``plan`` reads registrations and returns launch data without writing or starting
the game. ``main`` owns preparation and process launch. Native and D7VK are
explicit choices: an unsupported native configuration never switches backends.
All generated assets and receipts belong under ignored local storage.
"""

from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "local/remaster/launcher.json"
REGISTRY = ROOT / "local/remaster/models.json"


def read_json(path):
    """Read a UTF-8 manifest, accepting the BOM written by Windows tooling."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Cannot read completed manifest {path}: {exc}") from exc


def graphics_limitations(graphics, profile):
    """Check declared host capabilities, including its bounded output dimensions."""
    caps = profile["graphics_capabilities"]
    choices = profile.get("supported_graphics_values", {})
    ranges = profile.get("supported_graphics_ranges", {})
    bounds = {"width": (640, 7680), "height": (480, 4320)}
    for key, limits in ranges.items():
        if (key not in bounds or not isinstance(limits, list) or len(limits) != 2
                or any(type(n) is not int for n in limits)
                or not bounds[key][0] <= limits[0] <= limits[1] <= bounds[key][1]):
            raise RuntimeError("Invalid native graphics range: " + key)
    errors = []
    for key, value in graphics.items():
        if caps.get(key) == value or value in choices.get(key, []):
            continue
        if key in ranges and type(value) is int and ranges[key][0] <= value <= ranges[key][1]:
            continue
        allowed = (f"{ranges[key][0]}..{ranges[key][1]}" if key in ranges else
                   ", ".join(map(str, choices.get(key, [caps[key]] if key in caps else []))) or "not advertised")
        errors.append(f"Unsupported native graphics setting {key}={value}; supported: {allowed}.")
    return errors


def _prepared_profile_bindings(profile_environment, prepared_bindings):
    """Keep the profile's authored catalog unless preparation supplies a fresh one."""
    bindings = dict(prepared_bindings)
    profile_catalog = profile_environment.get("MW34_SURFACE_NORMALS")
    if profile_catalog and "MW34_SURFACE_NORMALS" not in bindings:
        bindings["MW34_SURFACE_NORMALS"] = profile_catalog
    return bindings


def _chassis_preparation_environment(profile_environment, prepared_environment):
    """Combine profile catalogs with fresh resources, preferring fresh bindings."""
    environment = dict(profile_environment)
    catalog = environment.get("MW34_SURFACE_NORMALS")
    if catalog and not Path(catalog).is_absolute():
        environment["MW34_SURFACE_NORMALS"] = str((ROOT / catalog).resolve())
    environment.update(prepared_environment)
    return environment


def plan(backend=None, original_models=False, *, config_path=None, registry_path=None, verification=None):
    """Resolve registered models, capabilities and command arguments without launching.

    Paths in registrations are relative to ROOT unless already absolute. A
    returned ``supported=False`` describes a capability mismatch; malformed or
    missing required inputs raise instead. ``original_models`` disables optional
    replacement meshes, not the original game simulation or registered banks.
    """
    selected_config = (Path(config_path) if config_path is not None else CONFIG).resolve()
    config = read_json(selected_config)
    backend = backend or config["backend"]
    profile_environment = config.get("native", {}).get("runtime_environment", {})
    from presentation_policy import choice, apply as apply_presentation
    if choice(config.get('native', {})) is not None:
        # Normal sessions never inherit optional developer registries/presets.
        config['native'].setdefault('prepared_pack_roots', [])
        config['native'].setdefault('prepared_environment_pack_roots', [])
        config['native'].pop('sun_preset', None)
    installed_packs = "prepared_pack_roots" in config.get("native", {})
    prepared_profile = None
    from chassis_appearances import mode as validate_appearance_mode
    validate_appearance_mode(config.get('native', {}).get('mech_appearance'))
    chassis_records = []
    if installed_packs:
        if backend != "native" or registry_path is not None:
            raise RuntimeError("Prepared mech packs require the native backend and cannot mix legacy registries")
        from prepared_mech_packs import compose
        roots = [] if original_models else config["native"]["prepared_pack_roots"]
        if not isinstance(roots, list) or len(roots) > 128 or any(not isinstance(p, str) for p in roots):
            raise RuntimeError("Invalid installed pack roots")
        ready, bindings = compose(roots, config["native"], verification, chassis_records)
        config["native"]["runtime_environment"] = _prepared_profile_bindings(
            profile_environment, bindings
        )
        prepared_profile = config
        offline = []
    else:
        selected_registry = (
            Path(registry_path) if registry_path is not None
            else ROOT / config.get("native", {}).get("model_registry", str(REGISTRY))
        ).resolve()
        registry = read_json(selected_registry)
        if registry["schema_version"] != 1:
            raise RuntimeError("Unsupported model registry version")
        statuses = {"runtime-ready"}
        if backend == "native" and config["native"].get("include_runtime_candidates", False):
            statuses.add("runtime-candidate")
        ready = [m for m in registry["models"] if m["status"] in statuses and m["backend"] == backend]
        offline = [m["name"] for m in registry["models"] if m not in ready]
        if original_models:
            ready = []
            offline = []
    bank_manifest = ROOT / "local/work-ahead/texture-launcher-audit-v2/configured-banks.json"
    environment_packs = None
    if "prepared_environment_pack_roots" in config.get("native", {}):
        if backend != "native":
            raise RuntimeError("Prepared environment packs require the native backend")
        from prepared_environment_packs import select, profile_bindings, detail_metadata
        environment_packs = select(config['native']['prepared_environment_pack_roots'], config['native'], verification)
        from mission_lighting import apply_training
        apply_training(environment_packs, config['native'])
        config['native']['runtime_environment'] = profile_bindings(environment_packs,config['native'])
        # Installed pack versions own their independently verified detail pins.
        # A development catalog hash must not reject another valid pack revision.
        installed_detail = detail_metadata(environment_packs)
        if installed_detail:
            config['native'].setdefault('surface_detail',{}).setdefault('packs',{}).update(installed_detail)
        env = config['native']['runtime_environment']
        if 'MW34_EFFECT_LIGHT_CATALOG' in env:
            from prepared_environment_packs import sha
            config['native']['effect_lighting']['catalog'] = env['MW34_EFFECT_LIGHT_CATALOG']
            config['native']['effect_lighting']['sha256'] = sha(env['MW34_EFFECT_LIGHT_CATALOG'])
        prepared_profile = config
        banks = [key for p in environment_packs.values() for key in p['registry']['banks']]
    else:
        banks = read_json(bank_manifest) if bank_manifest.is_file() else []
    if not banks and not installed_packs and environment_packs is None:
        raise RuntimeError("Texture pack manifest is empty or missing")
    apply_presentation(config.get('native', {}), environment_packs or {})
    graphics = dict(config["graphics"])
    # Settings UI persists the named off choice; the native sampler contract
    # uses one raster sample for disabled AA.

    if graphics.get("aa") == "off":
        graphics["aa"] = 1
    if backend == "d7vk":
        command = [
            sys.executable,
            str(ROOT / "mw3_launcher.py"),
            "--no-gui",
            "--resolution",
            "1920x1440 (1440p 4:3 Equivalent)",
            "--aa",
            "8x MSAA",
            "--af",
            "16x",
            "--textures",
            "ai",
        ]
        supported = True
        limitations = [
            "D7VK runs the original executable and original models; native model replacements are not compatible with this backend."
        ]
    elif backend == "native":
        profile = config["native"]
        caps = profile["graphics_capabilities"]
        detail_env = profile.get("runtime_environment", {})
        detail_roles = []
        if detail_env.get("MW34_WATER_DETAIL") == "1":
            detail_roles += ["water", "surf"]
        if detail_env.get("MW34_CLOUD_DETAIL") == "1":
            detail_roles += ["cloud"]
        if detail_roles and 1 not in profile.get("surface_detail_versions", []):
            raise RuntimeError("Sky/water detail requires a validated compatible native host")
        for role in detail_roles:
            detail_path = ROOT / detail_env.get("MW34_" + role.upper() + "_NORMALS", "")
            pin = profile.get("surface_detail", {}).get("packs", {}).get(role, {})
            if not detail_path.is_file() or not 0 < detail_path.stat().st_size <= 16 * 1024 * 1024:
                raise RuntimeError("Missing or excessive surface detail pack: " + role)
            with detail_path.open("rb") as stream:
                detail_hash = hashlib.file_digest(stream, "sha256").hexdigest()
            if detail_hash != pin.get("sha256"):
                raise RuntimeError("Surface detail pack changed: " + role)
        world_normals = profile.get("runtime_environment", {}).get("MW34_WORLD_NORMALS")
        if world_normals:
            if 1 not in profile.get("world_normal_page_versions", []):
                raise RuntimeError("World normal pages require a validated compatible native host")
            if not (ROOT / world_normals).is_file():
                raise RuntimeError("Configured world-normal manifest is missing")
        authored_normals = profile.get("runtime_environment", {}).get("MW34_SURFACE_NORMALS")
        if authored_normals:
            authored_path = ROOT / authored_normals
            if not authored_path.is_file():
                raise RuntimeError("Configured authored-normal catalog is missing")
            with authored_path.open("rb") as stream:
                authored_magic = stream.read(8)
            if authored_magic == b"MW34SNA1" and 1 not in profile.get(
                "authored_normal_catalog_versions", []
            ):
                raise RuntimeError(
                    "Paged authored normals require a validated compatible native host"
                )
            if authored_magic not in (b"BWSNR2\0\0", b"MW34SNA1"):
                raise RuntimeError("Unsupported authored-normal catalog")
        if any("normal_textures" in m for m in ready) and 2 not in profile.get(
            "normal_map_formats", []
        ):
            raise RuntimeError("Registered material normals require a validated BWNRM2 native host")
        executable = ROOT / profile["executable"]
        if profile.get("runtime_environment", {}).get("MW34_EFFECT_LIGHTS") == "1":
            if 1 not in profile.get("effect_lighting_versions", []):
                raise RuntimeError("Effect lighting requires a validated compatible native host")
            catalog = ROOT / profile.get("runtime_environment", {}).get(
                "MW34_EFFECT_LIGHT_CATALOG", ""
            )
            pin = profile.get("effect_lighting", {})
            if not catalog.is_file():
                raise RuntimeError("Configured effect-light catalog is missing: " + str(catalog))
            registered_catalog = pin.get("catalog")
            if not registered_catalog or (ROOT / registered_catalog).resolve() != catalog.resolve():
                raise RuntimeError(
                    "Effect-light profile mismatch: selected " + str(catalog)
                    + "; registered " + str(registered_catalog)
                    + ". Repair the profile using the selected catalog's generation receipt."
                )
            data = catalog.read_bytes()
            if len(data) < 12 or data[:8] != b"MWFX1\0\0\0":
                raise RuntimeError("Invalid effect-light catalog")
            count = int.from_bytes(data[8:12], "little")
            if not 0 < count <= 8192 or len(data) != 12 + 48 * count:
                raise RuntimeError("Invalid effect-light catalog size")
            if hashlib.sha256(data).hexdigest() != pin.get("sha256"):
                raise RuntimeError(
                    "Effect-light catalog changed; publish its matching preview metadata"
                )
        if not executable.is_file():
            raise RuntimeError("Registered native executable is missing")
        if profile.get("executable_sha256"):
            with executable.open("rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            if digest.lower() != profile["executable_sha256"].lower():
                raise RuntimeError(
                    "Native executable changed; publish its completed validation/profile before launching"
                )
        if profile.get("translated_module"):
            module = ROOT / profile["translated_module"]
            if not module.is_file() or hashlib.sha256(module.read_bytes()).hexdigest() != profile.get("translated_module_sha256"):
                raise RuntimeError("Generated native game module is missing or changed. Repair this runtime version.")
        if profile.get("verify_source_snapshot"):
            snapshot = read_json(ROOT / profile["source_snapshot"])
            if snapshot.get("controller_input_version") != profile.get("controller_input_version"):
                raise RuntimeError("Native source snapshot and launcher disagree on controller input support")
            if (
                snapshot.get("executable_sha256", "").lower()
                != profile.get("executable_sha256", "").lower()
            ):
                raise RuntimeError(
                    "Native source snapshot does not match the selected executable; publish its matching build metadata"
                )
            if sorted(snapshot.get("model_ids", [])) != sorted(profile.get("model_ids", [])):
                raise RuntimeError(
                    "Native source snapshot and launcher disagree on supported models"
                )
            if snapshot.get("skin_ids", {}) != profile.get("skin_ids", {}):
                raise RuntimeError(
                    "Native source snapshot and launcher disagree on supported model skins"
                )
            if snapshot.get("normal_map_formats", []) != profile.get("normal_map_formats", []):
                raise RuntimeError(
                    "Native source snapshot and launcher disagree on normal-map support"
                )
            if snapshot.get("world_normal_page_versions", []) != profile.get(
                "world_normal_page_versions", []
            ):
                raise RuntimeError(
                    "Native source snapshot and launcher disagree on world-normal page support"
                )
            if snapshot.get("authored_normal_catalog_versions", []) != profile.get(
                "authored_normal_catalog_versions", []
            ):
                raise RuntimeError(
                    "Native source snapshot and launcher disagree on authored-normal catalog support"
                )
            if snapshot.get("surface_detail_versions", []) != profile.get(
                "surface_detail_versions", []
            ):
                raise RuntimeError(
                    "Native source snapshot and launcher disagree on sky/water detail support"
                )
        unknown = [m["name"] for m in ready if m.get("id") not in profile.get("model_ids", [])]
        if unknown:
            raise RuntimeError(
                "Published models need a compatible native host: " + ", ".join(unknown)
            )
        unsupported_skins = [
            m["name"] + "/" + skin["id"]
            for m in ready
            for skin in m.get("skins", [])
            if skin["id"] not in profile.get("skin_ids", {}).get(m["id"], [])
        ]
        if unsupported_skins:
            raise RuntimeError(
                "Published skins need a compatible native host: " + ", ".join(unsupported_skins)
            )
        mesh_versions = profile.get("mesh_payload_versions", [1, 2])
        incompatible = [
            m["name"] for m in ready if m.get("required_native_mesh_format", 1) not in mesh_versions
        ]
        if incompatible:
            raise RuntimeError(
                "Published models need a newer native mesh format: " + ", ".join(incompatible)
            )
        limitations = graphics_limitations(graphics, profile)
        supported = not limitations
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(__file__).with_name("play_native.ps1")),
            "-Profile",
            str(selected_config),
            "-RuntimeRoot", str(ROOT),
        ]
        if profile.get("cumulative_texture_banks") is not True:
            supported = False
            limitations.append(
                "Native cumulative texture-bank redirection has not been connected to this profile."
            )
    else:
        raise RuntimeError("Unknown renderer backend " + str(backend))
    for model in ready:
        for asset in model["required_files"] + [
            path for path in model.get("normal_textures", {}).values() if path is not None
        ]:
            if not (ROOT / asset).is_file():
                raise RuntimeError(f"Published model {model['name']} is incomplete: {asset}")
    music = None
    if backend == "native" and config["native"].get("local_cd_audio", False):
        from local_music import configuration

        music = configuration(ROOT, config['native'].get('music_inputs'))
        if config["native"].get("installation_layout") == 1 and music is None:
            raise RuntimeError("Local music is enabled but its installed input configuration is missing")
    asset_output = (
        config.get("native", {}).get("prepared_asset_directory") if backend == "native" else None
    )
    return dict(
        backend=backend,
        graphics=graphics,
        supported=supported,
        texture_banks=len(banks),
        models=ready,
        offline_models=offline,
        limitations=limitations,
        command=command,
        music=music,
        asset_output=asset_output,
        prepared_profile=prepared_profile,
        environment_packs=environment_packs,
        chassis_records=chassis_records,
        appearance_coverage=[dict(chassis=row['registration']['id'], **row['appearance'])
                             for row in chassis_records if 'appearance' in row],
    )


def main():
    """Handle check/prepare/run modes; return the backend exit status or 2 on failure."""
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, help="Installed runtime data root; no checkout discovery")
    parser.add_argument("--backend", choices=["native", "d7vk"])
    parser.add_argument(
        "--original-models",
        action="store_true",
        help="Use original MW3 geometry while retaining registered texture banks and graphics settings",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read current profiles/assets without launching or changing files",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Verify and prepare registered native assets without launching",
    )
    parser.add_argument(
        "--profile", type=Path, default=CONFIG, help="Completed native profile to check or launch"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        help="Completed model registry; defaults to the selected profile registry",
    )
    parser.add_argument(
        "--asset-output",
        type=Path,
        help="Separate prepared-asset directory for an integration candidate",
    )
    parser.add_argument(
        "--lighting-preset", help="Registered map lighting preset, e.g. sunrise, sunset or midday"
    )
    parser.add_argument(
        "--game-exe", type=Path, help="Validated local executable selected in the GUI"
    )
    parser.add_argument("--instant-replay", choices=["0", "1"], default="0")
    parser.add_argument(
        "--fixture-lights", choices=["0", "1"], help="Override texture-bearing environmental lights"
    )
    parser.add_argument(
        "--weather", choices=["0", "1"], help="Override supported campaign weather shading"
    )
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--input-script", type=Path, help="Explicit local UI-input script for bounded native checks")
    parser.add_argument("--dump", type=int, default=0)
    args = parser.parse_args()
    if args.runtime_root is not None:
        ROOT = args.runtime_root.resolve(strict=True)
    try:
        if args.game_exe and not args.game_exe.is_file():
            raise RuntimeError("Selected game executable is missing")
        if args.input_script and not args.input_script.is_file():
            raise RuntimeError("Selected UI-input script is missing")
        from startup_cache import VerificationCache, environment_resources
        startup_started = time.monotonic()
        def startup_progress(message):
            print(f'Startup: {message} ({time.monotonic() - startup_started:.0f}s)', flush=True)
        startup_progress('Checking content…')
        verification = VerificationCache(Path(args.asset_output) / 'startup' , startup_progress) if args.asset_output and not args.check else None
        p = plan(
            args.backend,
            args.original_models,
            config_path=args.profile,
            registry_path=args.registry,
            verification=verification,
        )
        if verification is not None:
            verification.save()
            startup_progress(f'Content checks complete: {verification.reused} unchanged, {verification.hashed} fully checked.')
        lighting_profile = p.get('prepared_profile') or read_json(args.profile)
        native_lighting = lighting_profile.get("native", {})
        lighting_config = native_lighting.get("sun_preset")
        presentation_off = native_lighting.get("presentation", {}).get("dynamic_lighting") is False
        if args.lighting_preset and p["backend"] != "native":
            raise RuntimeError("Lighting presets require the native renderer")
        if args.lighting_preset and presentation_off:
            raise RuntimeError("Lighting presets require Dynamic Lighting to be enabled")
        if p["backend"] == "native" and not presentation_off and (lighting_config or args.lighting_preset):
            # The selected pack catalog must also reach the read-only resolver;
            # the original GUI profile still contains the previous selection.
            resolved = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(Path(__file__).with_name("resolve_sun_preset.ps1")),
                    "-Profile",
                    str(args.profile.resolve()),
                    "-RuntimeRoot", str(ROOT),
                    "-Preset",
                    args.lighting_preset or lighting_config["default"],
                    "-CatalogPath", str(lighting_config['source']), "-MapName", str(lighting_config['map']),
                ],
                capture_output=True,
                text=True,
            )
            if resolved.returncode:
                raise RuntimeError(resolved.stderr.strip())
            lighting = json.loads(resolved.stdout)
            print("Lighting preset: " + lighting["map"] + " / " + lighting["preset"])
            # A profile default is automatic; only an explicit preview request disables campaign selection.

            if args.lighting_preset:
                p["command"] += ["-LightingPreset", lighting["preset"]]
        g = p["graphics"]
        aa = (
            "AA off"
            if g["aa"] == 1
            else "FXAA" if g["aa"] == "fxaa" else str(g["aa"]) + "-sample SSAA"
        )
        af = "AF off" if g["af"] == 1 else str(g["af"]) + "x AF"
        aspect = (
            "43:18 ultrawide"
            if (g["width"], g["height"]) == (3440, 1440)
            else "4:3" if g["width"] * 3 == g["height"] * 4 else "native aspect"
        )
        print(
            f"Play MW3Remaster requested profile: {g['width']}x{g['height']} ({aspect}), {aa}, {af}"
        )
        print(f"Renderer: {p['backend']}; current texture pack: {p['texture_banks']} banks")
        if p["backend"] == "native":
            print("Native build: " + read_json(args.profile)["native"]["executable"])
        if p["backend"] == "native":
            print("Scenery draw distance: " + str(g.get("draw_distance", 800)) + " units")
        if p["backend"] == "native" and g.get("fog_distance", 0):
            print("Linear fog distance: " + str(g["fog_distance"]) + " units")
        print(
            "Runtime models: "
            + (", ".join(m["name"] for m in p["models"]) or "original game models")
        )
        if p["music"]:
            print("Music: local MW3 tracks 01 and 02; original game music controls")
        candidates = [m["name"] for m in p["models"] if m["status"] == "runtime-candidate"]
        if candidates:
            print(
                "Enabled test candidates (weapon/damage/LOD checks pending): "
                + ", ".join(candidates)
            )
        if p["offline_models"]:
            print(
                "Models awaiting compatible runtime integration: " + ", ".join(p["offline_models"])
            )
        for appearance in p.get('appearance_coverage', []):
            print('Mech appearance: ' + json.dumps(appearance))
        for limitation in p["limitations"]:
            print(limitation)
        if not p["supported"]:
            raise RuntimeError(
                " ".join(p["limitations"]) + " No settings were silently disabled and no backend fallback was used."
            )
        if args.check:
            return 0
        # All launch paths share the same singleton game identity; preserve an existing session.

        if not args.prepare_only:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    "if(Get-Process -Name entry_commandline,Mech3 -ErrorAction SilentlyContinue){exit 2}",
                ],
                capture_output=True,
            )
            if result.returncode:
                raise RuntimeError(
                    "A game session is already running. Close it normally before launching Remaster."
                )
        environment = os.environ.copy()
        for key in list(environment):
            if key.startswith("MW34_"):
                environment.pop(key, None)
        if p["backend"] == "native":
            from native_assets import prepare
            startup_progress('Preparing mech resources…')
            environment.update(
                prepare(ROOT, p["models"], output=args.asset_output or p["asset_output"],
                        allow_original_banks=p.get("prepared_profile") is not None,
                        use_development_banks=p.get('environment_packs') is None)
            )
            if p.get('environment_packs') is not None:
                from prepared_environment_packs import RESOURCE_KEYS
                from prepared_mech_packs import ALL_MODEL_KEYS
                # Environment preparation may reuse a receipt containing older
                # host bindings. Only the freshly selected mech resources own
                # model/LOD/skin keys; never let that receipt replace them.
                model_bindings = {key: value for key, value in environment.items() if key in ALL_MODEL_KEYS}
                native=p['prepared_profile']['native']
                bindings=environment_resources(p['environment_packs'],native,
                    Path(args.asset_output or p['asset_output']), startup_progress)
                bindings = {key: value for key, value in bindings.items() if key not in ALL_MODEL_KEYS}
                bindings.update(model_bindings)
                native['runtime_environment']=bindings
                from presentation_policy import apply as apply_presentation
                apply_presentation(native, p['environment_packs'])
                bindings = native['runtime_environment']
                for key in RESOURCE_KEYS: environment.pop(key,None)
                environment.update(bindings)
            if p["music"]:
                startup_progress('Preparing soundtrack…')
                from local_music import prepare_music

                music_root = args.asset_output or p['asset_output']
                music_output = Path(music_root) / 'music' if music_root else None
                environment.update(prepare_music(ROOT, supplied=p['music'], output=music_output))
            for key, value in p["graphics"].items():
                environment["MW34_REMASTER_" + key.upper()] = str(value)
            p["command"] += [
                "-Frames",
                str(args.frames),
                "-Dump",
                str(args.dump),
                "-InstantReplay",
                args.instant_replay,
            ]
            if args.fixture_lights is not None:
                p["command"] += ["-FixtureLights", args.fixture_lights]
            if args.weather is not None:
                p["command"] += ["-Weather", args.weather]
            if args.game_exe:
                p["command"] += ["-GameExe", str(args.game_exe.resolve())]
            if args.input_script:
                p["command"] += ["-Script", str(args.input_script.resolve())]
        if p['backend'] == 'native':
            from prepared_skin_packs import write_catalog, CATALOG_KEY
            environment.pop(CATALOG_KEY, None)
            skin_bindings = write_catalog(p['models'] + p.get('chassis_records', []), args.asset_output or p['asset_output'])
            environment.update(skin_bindings)
            if p.get('prepared_profile') is not None:
                native = p['prepared_profile']['native']
                native.setdefault('runtime_environment', {}).pop(CATALOG_KEY, None)
                native['runtime_environment'].update(skin_bindings)
            from prepared_chassis_packs import prepare as prepare_chassis, CATALOG_KEY as CHASSIS_KEY
            environment.pop(CHASSIS_KEY, None)
            profile_environment = (
                p["prepared_profile"]["native"].get("runtime_environment", {})
                if p.get("prepared_profile") is not None
                else {}
            )
            chassis_environment = _chassis_preparation_environment(
                profile_environment, environment
            )
            chassis_bindings = prepare_chassis(p.get('chassis_records', []), args.game_exe or ROOT / 'MW3/Mech3.exe',
                                               args.asset_output or p['asset_output'] or ROOT / 'local/remaster/prepared',
                                               chassis_environment)
            environment.update(chassis_bindings)
            if p.get('prepared_profile') is not None:
                native['runtime_environment'].pop(CHASSIS_KEY, None)
                native['runtime_environment'].update(chassis_bindings)
                from presentation_policy import apply as apply_presentation
                apply_presentation(native, p.get('environment_packs') or {})
                environment.update(native['runtime_environment'])
        if p.get("prepared_profile") is not None:
            # PowerShell applies runtime_environment after preparation. Give it the
            # composed session profile so stale developer mech paths cannot return.
            import uuid
            session_dir = Path(args.asset_output or p["asset_output"] or ROOT / "local/remaster/prepared") / "launches" / uuid.uuid4().hex
            session_dir.mkdir(parents=True)
            session_profile = session_dir / "profile.json"
            session_profile.write_text(json.dumps(p["prepared_profile"], indent=2), encoding="utf-8")
            p["command"][p["command"].index("-Profile") + 1] = str(session_profile.resolve())
            print("Prepared-pack session profile: " + str(session_profile.resolve()))
        if args.prepare_only:
            return 0
        startup_progress('Starting game…')
        return subprocess.call(p["command"], cwd=ROOT, env=environment)
    except (RuntimeError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
