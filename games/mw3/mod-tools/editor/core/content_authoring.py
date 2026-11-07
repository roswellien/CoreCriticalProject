"""Modular MW3-RE authoring adapter; the native tool owns all content semantics.

Sources, exports, profiles and playtest logs stay in a separate workspace. This
module never patches the selected installation or starts the original executable.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

from editor.config import PROJECT_ROOT, game_directory, load_settings, settings_path

_native_playtests: dict[str, subprocess.Popen] = {}


class ContentToolError(ValueError):
    def __init__(self, result: dict):
        self.result = result
        super().__init__(
            "\n".join(
                f"{item.get('code', 'content')}: {item.get('message', '')} "
                f"{item.get('package', '')} {item.get('content', '')} {item.get('field', '')}"
                for item in result.get("diagnostics", [])
            )
            or "The native content tool rejected this request."
        )


def configure_content(tool: str, runtime: str, workspace: str) -> dict:
    """Save explicit user-selected tools separately from package-owned data."""
    tool_path, runtime_path, workspace_path = (
        Path(value).resolve() for value in (tool, runtime, workspace)
    )
    if not tool_path.is_file() or not runtime_path.is_file():
        raise ValueError("Choose existing mw3content and MW3-RE runtime executables.")
    install = game_directory().resolve()
    if workspace_path == install or workspace_path.is_relative_to(install):
        raise ValueError("The authoring workspace must be outside the original installation.")
    if install.is_relative_to(workspace_path):
        raise ValueError("The authoring workspace must not contain the original installation.")
    data = load_settings()
    data.update(
        schema_version=1,
        content_tool=str(tool_path),
        native_runtime=str(runtime_path),
        content_workspace=str(workspace_path),
    )
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".content.tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)
    return data


class ContentAuthoring:
    def __init__(self):
        settings = load_settings()
        self.tool = Path(settings.get("content_tool", ""))
        self.runtime = Path(settings.get("native_runtime", ""))
        self.workspace = Path(
            settings.get("content_workspace", PROJECT_ROOT / "local/mod-tools/content")
        ).resolve()
        install = game_directory().resolve()
        if (
            self.workspace == install
            or self.workspace.is_relative_to(install)
            or install.is_relative_to(self.workspace)
        ):
            raise ValueError(
                "The content workspace must be separate from the original installation."
            )

    def path(self, relative: str) -> Path:
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ":" in relative
        ):
            raise ValueError("Use a path inside the content workspace.")
        parts = relative.replace("\\", "/").split("/")
        if ".." in parts:
            raise ValueError("Parent paths are not allowed in the content workspace.")
        path = (self.workspace / relative).resolve()
        if path == self.workspace or not path.is_relative_to(self.workspace):
            raise ValueError("The path leaves the content workspace.")
        return path

    def cli(self, *arguments: str) -> dict:
        if not self.tool.is_file():
            raise ValueError("Configure the installed mw3content executable first.")
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            process = subprocess.run(
                [str(self.tool), *map(str, arguments)],
                stdout=output,
                stderr=errors,
                timeout=120,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if output.tell() > 4 * 1024 * 1024 or errors.tell() > 64 * 1024:
                raise ValueError("Native content tool output exceeded its limit.")
            output.seek(0)
            try:
                result = json.load(output)
            except (ValueError, UnicodeError) as error:
                raise ValueError("The native content tool returned invalid JSON.") from error
        if not isinstance(result, dict) or result.get("ok") is not True or process.returncode:
            raise ContentToolError(result if isinstance(result, dict) else {})
        return result

    def save(self, project_id: str, source: dict) -> dict:
        if not isinstance(project_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_-]{0,63}", project_id
        ):
            raise ValueError(
                "Use a lowercase project ID with letters, digits, underscores and hyphens."
            )
        if not isinstance(source, dict):
            raise TypeError("A source manifest must be a JSON object.")
        path = self.path(f"sources/{project_id}/pack.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".pack-{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(source, indent=2), encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return {"project_id": project_id, "source": str(path), "workspace": str(self.workspace)}

    def compile(self, project_id: str) -> dict:
        source = self.path(f"sources/{project_id}")
        destination = self.path(f"compiled/{project_id}/build-{uuid.uuid4().hex}")
        result = self.cli(
            "compile", str(source), str(destination), "--store", str(self.path("store"))
        )
        receipt = self.path(f"compiled/{project_id}/latest.json")
        temporary = receipt.with_name(f".latest-{uuid.uuid4().hex}.json")
        try:
            temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
            temporary.replace(receipt)
        finally:
            temporary.unlink(missing_ok=True)
        return result

    def latest_build(self, project_id: str) -> dict:
        receipt = self.path(f"compiled/{project_id}/latest.json")
        if not receipt.is_file():
            raise ValueError("Compile this project successfully before exporting or installing it.")
        result = json.loads(receipt.read_text(encoding="utf-8"))
        output = Path(result["output"]).resolve()
        parent = self.path(f"compiled/{project_id}")
        if (
            output == parent
            or not output.is_relative_to(parent)
            or not (output / "pack.json").is_file()
        ):
            raise ValueError(
                "The latest build receipt does not identify this project's compiled package."
            )
        return result

    def install(self, project_id: str) -> dict:
        build = self.latest_build(project_id)
        return self.cli("install", build["output"], "--store", str(self.path("store")))

    def package(self, project_id: str) -> dict:
        build = self.latest_build(project_id)
        source = Path(build["output"])
        destination = self.path(
            f"exports/{project_id}-{build['version']}-{uuid.uuid4().hex}.mw3pack"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        return self.cli(
            "package", str(source), str(destination), "--store", str(self.path("store"))
        )

    def playtest(self, profile: str, mission: str = "", network: dict | None = None) -> dict:
        profile_path = self.path(profile)
        if not self.runtime.is_file():
            raise ValueError("Configure the native MW3-RE runtime before playtesting.")
        store = self.path("store")
        resolved = self.cli("resolve", str(profile_path), "--store", str(store))
        if network is None:
            network = {"mode": "single"}
        if not isinstance(network, dict):
            raise TypeError("Network playtest settings must be an object.")
        mode = network.get("mode", "single")
        if mode not in ("single", "host", "join"):
            raise ValueError("Choose single player, host or join for the native playtest.")
        definitions = resolved.get("content", {}).get("definitions", [])
        selected = next(
            (
                item
                for item in definitions
                if item.get("kind") == "mission" and item.get("id") == mission
            ),
            None,
        )
        arena = selected is not None and selected.get("data", {}).get("multiplayer", False)
        if mode != "single" and not arena:
            raise ValueError("Host and join playtests require a selected multiplayer mission ID.")
        if arena and mode == "single":
            raise ValueError("This mission is an arena; choose host or join.")
        network_arguments = []
        if mode != "single":
            players = network.get("players", 2)
            port = network.get("port", 27888)
            if type(players) is not int or not 2 <= players <= 8:
                raise ValueError("Arena playtests require two to eight players.")
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError("Choose a network port from 1 to 65535.")
            name = network.get("name", "Studio " + mode)
            if (
                not isinstance(name, str)
                or not name
                or len(name) > 64
                or any(ord(c) < 32 for c in name)
            ):
                raise ValueError("Use a player name of one to 64 printable characters.")
            network_arguments = ["--net-wait", str(players), "--net-name", name]
            if mode == "host":
                network_arguments += ["--host", "--net-port", str(port)]
            else:
                address = network.get("address", "127.0.0.1:27888")
                if not isinstance(address, str) or not re.fullmatch(
                    r"[A-Za-z0-9._:\[\]-]{1,255}", address
                ):
                    raise ValueError("Enter a host address, optionally followed by its port.")
                network_arguments += ["--join", address]
        write = self.path("playtest/" + mode)
        running = _native_playtests.get(str(write))
        if running is not None and running.poll() is None:
            raise ValueError("A native Studio playtest is already running for this role.")
        write.mkdir(parents=True, exist_ok=True)
        arguments = [
            str(self.runtime),
            "--install",
            str(game_directory()),
            "--write-dir",
            str(write),
            "--content-profile",
            str(profile_path),
            "--content-store",
            str(store),
            "--windowed",
        ]
        if mission:
            arguments += ["--content-mission", mission]
        arguments += network_arguments
        with (write / "native.log").open("ab") as log:
            process = subprocess.Popen(
                arguments,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        _native_playtests[str(write)] = process
        return {"pid": process.pid, "log": str(write / "native.log"), "profile": str(profile_path)}

    def save_profile(self, relative: str, profile: dict) -> dict:
        path = self.path(relative)
        if not isinstance(profile, dict):
            raise TypeError("Profile must be a JSON object.")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}-{uuid.uuid4().hex}.staging.json")
        try:
            temporary.write_text(json.dumps(profile, indent=2), encoding="utf-8")
            result = self.cli("resolve", str(temporary), "--store", str(self.path("store")))
            locked = result["content"]["lock"]["packages"]
            requests = {item["id"]: item for item in profile["packages"]}
            pinned = json.loads(json.dumps(profile))
            pinned["packages"] = []
            for entry in locked:
                pin = dict(entry)
                if "path" in requests.get(pin["id"], {}):
                    pin["path"] = requests[pin["id"]]["path"]
                pinned["packages"].append(pin)
            temporary.write_text(json.dumps(pinned, indent=2), encoding="utf-8")
            result = self.cli("resolve", str(temporary), "--store", str(self.path("store")))
            temporary.replace(path)
            result["profile"] = pinned
            return result
        finally:
            temporary.unlink(missing_ok=True)


def templates() -> dict:
    """Authored starter definitions only; game content is supplied locally."""
    return {
        "package": {
            "schema_version": 3,
            "game_id": "mw3",
            "id": "my-mod",
            "version": "1.0.0",
            "files": {},
            "dependencies": [],
            "required_capabilities": {},
            "definitions": [],
            "patches": [],
        },
        "hud": {
            "kind": "hud",
            "id": "my-mod:wide-hud",
            "behavior": "native-widgets-v1",
            "data": {
                "reference_width": 640,
                "reference_height": 480,
                "widgets": {
                    "TIMER": {
                        "position": {"x": 580, "y": 15, "anchor_x": "right", "anchor_y": "top"}
                    }
                },
            },
        },
        "hud_artwork_binding": {
            "format": "mw3h-v1",
            "sprites": {"0123456789abcdef": "artwork/reticle.rgba"},
        },
        "equipment": {
            "kind": "equipment",
            "id": "my-mod:guardian",
            "behavior": "mw3:equipment/ecm@1",
            "data": {
                "name": "my_guardian",
                "label": "Guardian ECM",
                "tech": 2,
                "weight": [1.0, 1.5],
                "slots": [1, 2],
            },
        },
        "weapon": {
            "kind": "weapon",
            "id": "my-mod:ac5",
            "behavior": "mw3:weapon@1",
            "data": {
                "name": "my_ac5",
                "label": "Custom AC5",
                "base": "stock:ac5",
                "tech": 2,
                "uses_ammo": True,
                "missile": False,
                "lrm": False,
                "reader": {},
            },
        },
        "chassis": {
            "kind": "chassis",
            "id": "my-mod:bushwacker",
            "behavior": "mw3:biped@1",
            "data": {
                "name": "my_bushwacker",
                "label": "Custom Bushwacker",
                "base": "stock:bushwacker",
                "tech": 2,
                "mass": 55.0,
                "weight_class": 1,
                "model_name": "bushwacker",
                "reader": {},
            },
        },
        "world": {
            "kind": "world",
            "id": "my-mod:world",
            "behavior": "authored",
            "data": {
                "bounds": [-128, 128, 256, 256],
                "spawn": [0, 0, 0],
                "heightfield": {
                    "origin": [-128, 0, 128],
                    "spacing": 128,
                    "heights": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                },
            },
        },
        "world_asset": {
            "kind": "world_asset",
            "id": "my-mod:prop",
            "behavior": "static_mesh",
            "data": {
                "meshes": [
                    {
                        "vertices": [[0, 0, 0], [1, 0, 0], [0, 0, -1]],
                        "triangles": [[0, 1, 2]],
                        "color": [0.5, 0.5, 0.5],
                        "collision": True,
                        "ground": True,
                    }
                ]
            },
        },
        "mission": {
            "kind": "mission",
            "id": "my-mod:first-mission",
            "behavior": "native",
            "data": {
                "world": "my-mod:world",
                "number": 1,
                "readers": {
                    "objectives.zrd": [
                        "m1",
                        [
                            "desc",
                            "Reach extraction",
                            "primary",
                            [
                                "reach_area",
                                ["point", [0, 0, -40], "radius", 10.0, "desc", "Reach extraction"],
                            ],
                        ],
                    ]
                },
            },
        },
        "campaign": {
            "kind": "campaign",
            "id": "my-mod:campaign",
            "behavior": "graph",
            "data": {
                "name": "My campaign",
                "start": "landing",
                "variables": {"intel": False},
                "salvage": True,
                "nodes": [
                    {
                        "id": "landing",
                        "mission": "my-mod:first-mission",
                        "on_success": [{"op": "set", "variable": "intel", "value": True}],
                        "on_failure": [],
                        "routes": [
                            {"when": {"outcome": "success"}, "next": None},
                            {"when": True, "next": "landing"},
                        ],
                    }
                ],
            },
        },
        "profile": {
            "schema_version": 1,
            "id": "my-playtest",
            "packages": [],
            "conflicts": [],
            "selections": {},
        },
    }
