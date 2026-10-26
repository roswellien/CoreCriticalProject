"""Stage a LOCAL, non-distributable installed-runtime trial from completed inputs.

This first integration trial deliberately uses original archives/models and no
CD music. It does not edit the selected development profile or user settings.
Generated host/CRT artifacts and derived visual assets remain local. It is not
a release packager or permission to redistribute the resulting directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from prepared_mech_packs import ALL_MODEL_KEYS
from content_capabilities import advertised

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Stage:
    def __init__(self, directory):
        self.root = Path(directory).resolve()
        if self.root.exists():
            raise ValueError("Use a new runtime staging directory")
        self.root.mkdir(parents=True)
        self.copied = {}

    def copy(self, source, relative):
        source = Path(source).resolve(strict=True)
        destination = self.root / relative
        before = source.stat()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if sha(source) != sha(destination) or (before.st_size, before.st_mtime_ns) != (source.stat().st_size, source.stat().st_mtime_ns):
            raise ValueError("Source changed during staging: " + str(source))
        return "@runtime/" + destination.relative_to(self.root).as_posix()

    def asset(self, source):
        source = Path(source)
        if not source.is_absolute():
            source = ROOT / source
        source = source.resolve(strict=True)
        if source in self.copied:
            return self.copied[source]
        relative = Path("assets") / f"resource-{len(self.copied):03}"
        if source.is_dir():
            self.copied[source] = "@runtime/" + relative.as_posix()
            for file in source.rglob("*"):
                if file.is_symlink():
                    raise ValueError("Linked runtime resources are not supported")
                if file.is_file():
                    self.copy(file, relative / file.relative_to(source))
            return self.copied[source]
        destination = relative / source.name
        marker = "@runtime/" + destination.as_posix()
        self.copied[source] = marker
        header = source.read_bytes()[:10] if source.stat().st_size < 2 * 1024**2 else b""
        if header.startswith((b"MW34SNA1", b"MW34SNP1")):
            # Native paged catalogs resolve filenames beside the catalog itself.
            lines = source.read_text(encoding="utf-8-sig").splitlines()
            pages = []
            for index, page in enumerate(lines[1:]):
                if not page.strip():
                    continue
                path = Path(page)
                if not path.is_absolute():
                    path = source.parent / path
                name = f"page-{index:03}.bin"
                self.copy(path, destination.parent / name)
                pages.append(name)
            target = self.root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(lines[0] + "\n" + "\n".join(pages) + "\n", encoding="utf-8")
        else:
            self.copy(source, destination)
        return marker


def stage(profile_path, output, python_home):
    raw = Path(profile_path).read_bytes()
    profile = json.loads(raw.decode("utf-8-sig"))
    native = profile["native"]
    environment = native["runtime_environment"]
    if environment.get("MW34_SEED") != "host" or environment.get("MW34_STARTUP") != "loader":
        raise ValueError("Host-initialized loader startup is required")
    target = Stage(output)
    native["executable"] = target.copy(native["executable"], "bin/entry_commandline.exe")
    if sha(target.root / "bin/entry_commandline.exe") != native["executable_sha256"]:
        raise ValueError("Selected native host differs from the completed profile")
    native["source_snapshot"] = target.copy(native["source_snapshot"], "metadata/source-snapshot.json")
    native["installation_layout"] = 1
    native["content_capabilities"] = advertised(native)
    native["launch_inputs"] = {
        "entry_object": target.copy(ROOT / "reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj", "startup/entry.obj"),
        "crt_pack": ("@game/native-inputs/crt.bin" if 1 in native.get('original_support_versions', []) else
                     target.copy(ROOT / "reports/m4-crt-fdiv/native-derived-r1/pack.bin", "startup/crt.bin")),
        "crt_provider": "@game/native-inputs/MSVCRT.DLL",
    }
    for key in ALL_MODEL_KEYS:
        environment.pop(key, None)
    from prepared_environment_packs import profile_bindings
    environment = profile_bindings({}, native)
    native["runtime_environment"] = environment
    environment.pop("MW34_GAME_EXE", None)  # Always supplied from the selected original installation.
    environment.pop("MW34_MUSIC_PACK", None)
    environment.pop("MW34_REMASTER_BANKS", None)  # Explicit original-archive trial; never copy 26 GiB of development banks.
    # HUD/menu artwork is installed separately through verified UI packs.
    environment['MW34_HIRES_HUD'] = '0'
    environment.pop('MW34_HIRES_MENU', None)
    environment.pop('MW34_MENU_HD_BG', None)
    environment.pop('MW34_CINEMATIC_PATHS', None)
    if 1 in native.get('original_support_versions', []):
        # User originals are installed/imported by setup, never copied into Runtime.
        environment['MW34_REQUIRE_USER_PROVIDERS'] = '1'
        environment['MW34_MFC42_IMAGE'] = '@game/native-inputs/MFC42.DLL'
        environment['MW34_MSVCP50_IMAGE'] = '@game/native-inputs/MSVCP50.DLL'
        environment['MW34_IV50_IMAGE'] = '@game/native-inputs/Ir50_32.base11000000.dll'
    for key, value in list(environment.items()):
        if isinstance(value, str) and not value.startswith('@game/') and ("/" in value or "\\" in value):
            environment[key] = target.asset(value)
    if native.get("sun_preset"):
        native["sun_preset"]["source"] = target.asset(native["sun_preset"]["source"])
    if native.get('stock_effect_lighting'):
        native['stock_effect_lighting']['catalog'] = target.copy(
            ROOT / native['stock_effect_lighting']['catalog'], 'resources/stock-effect-lights.bin')
    if native.get('stock_soundtrack'):
        native['stock_soundtrack']['root'] = target.asset(native['stock_soundtrack']['root'])
    native["effect_lighting"] = {}
    native["surface_detail"] = {"packs": {}}
    native["prepared_pack_roots"] = []
    music_config = json.loads((ROOT / 'local/remaster/music.json').read_text(encoding='utf-8-sig'))
    native['music_decoder'] = target.copy(ROOT / music_config['decoder'], 'bin/decode_music.exe')
    native["local_cd_audio"] = False  # Explicit diagnostic choice, not a player setting migration.
    # Only fields consumed at runtime: research history contains machine-specific
    # paths and is preserved in the original profile, not copied into this trial.
    keep = {"executable", "executable_sha256", "source_snapshot", "verify_source_snapshot", "installation_layout", "content_capabilities",
            "launch_inputs", "runtime_environment", "sun_preset", "effect_lighting", "surface_detail", "prepared_pack_roots", "mission_environment_versions", "cinematic_path_versions", "cinematic_codec_sha256", "original_support_versions",
            "local_cd_audio", "graphics_capabilities", "supported_graphics_values", "supported_graphics_ranges", "cumulative_texture_banks",
            "model_ids", "skin_ids", "normal_map_formats", "world_normal_page_versions", "authored_normal_catalog_versions",
            "surface_detail_versions", "mesh_payload_versions", "effect_lighting_versions", "music_decoder",
            "include_runtime_candidates", "authored_normal_catalog_budget_bytes", "world_normal_catalog_budget_bytes", "controller_input_version",
            "stock_presentation_versions", "stock_effect_lighting", "stock_soundtrack", "dynamic_lighting_defaults", "presentation"}
    profile = {"schema_version": 1, "backend": "native", "graphics": profile["graphics"],
               "native": {k: v for k, v in native.items() if k in keep}}
    for role in profile["native"].get("surface_detail", {}).get("packs", {}).values():
        for key in list(role):
            if key not in ("path", "sha256", "bindings", "bytes"):
                del role[key]
    profile["native"]["surface_detail"] = {"packs": profile["native"].get("surface_detail", {}).get("packs", {})}
    (target.root / "profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    for name in ("play_remaster.py", "play_native.ps1", "resolve_sun_preset.ps1", "prepared_mech_packs.py",
                 "prepared_environment_packs.py", "prepared_skin_packs.py", "prepared_chassis_packs.py", "chassis_catalog.py", "chassis_icons.py", "reader_archive.py", "zrd_document.py", "content_capabilities.py", "legacy_content_capabilities.json", "mission_lighting.py", "normal_materials.py", "native_assets.py", "local_music.py", "presentation_policy.py"):
        target.copy(Path(__file__).with_name(name), Path("coordinator") / name)
    python_home = Path(python_home)
    for file in python_home.iterdir():
        if file.is_file() and (file.suffix.lower() in (".exe", ".dll", ".zip", "._pth") or file.name.lower().startswith("license")):
            target.copy(file, Path("python") / file.name)
    for folder in ("Lib", "DLLs"):
        for file in (python_home / folder).rglob("*"):
            excluded = {"site-packages", "__pycache__", "test", "tests", "idlelib", "tkinter", "ensurepip", "turtledemo"}
            if file.is_file() and not (set(file.relative_to(python_home).parts) & excluded):
                target.copy(file, Path("python") / file.relative_to(python_home))
    files = {}
    for file in target.root.rglob("*"):
        if file.is_file():
            files[file.relative_to(target.root).as_posix()] = {"bytes": file.stat().st_size, "sha256": sha(file)}
    manifest = {"schema_version": 1, "profile": "profile.json", "coordinator": "coordinator/play_remaster.py",
                "python": "python/python.exe", "purpose": "private-local-original-archives-no-music-trial",
                "files": files}
    (target.root / "runtime.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if Path(profile_path).read_bytes() != raw:
        raise ValueError("Published profile changed during staging; keep this trial separate and retry from a completed profile")
    return len(files), sum(f["bytes"] for f in files.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python-home", type=Path, required=True)
    args = parser.parse_args()
    print(stage(args.profile, args.output, args.python_home))
