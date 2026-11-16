"""MW3-RE argv planning; lexical validation is not package/execution admission.

Schemas 2 and 3 are pure. Schema 4 (the labelled Native preview) also reads the pack manifests
it is given, read-only, to turn installed model and map packs into game arguments.
"""

from pathlib import Path, PureWindowsPath
import json
import re


_FIELDS = frozenset({
    "schema_version", "engine", "runtime_root", "executable", "game_dir", "write_dir", "renderer",
    "width", "height", "aa", "af", "window_mode", "render_thread", "lighting", "assets",
})
_AA = {"off": "off", "1": "off", "fxaa": "fxaa", "2": "ssaa2", "4": "ssaa4"}
_MAX_JSON_BYTES = 2 * 1024 * 1024
_MAX_JSON_DEPTH = 64
# Pack manifests and model registries are small JSON files; payloads themselves are never read.
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_MAX_PREVIEW_PACKS = 64
_MAX_REGISTRY_MODELS = 256
_PREVIEW_FIELDS = frozenset({"draw_distance", "hud", "hud_text", "geometry", "model_packs", "environment_packs"})
# 800 is the original game's scenery range; the preview runtime also accepts 1200 and 1600.
_PREVIEW_DRAW_DISTANCES = (800, 1200, 1600)
_PREVIEW_HUDS = ("original", "core-critical")
_PREVIEW_GEOMETRY = ("legacy", "partial")
_RUNTIME_MODEL_STATUSES = ("runtime-ready", "runtime-candidate")
# The native runtime stores pack file offsets in signed 32-bit values, so a file of 2 GiB or more
# (today the shared-mech texture bank) cannot be loaded; such a pack is left out and reported.
_NATIVE_FILE_LIMIT = 2 ** 31


def plan_json(raw):
    """Plan bounded raw JSON, rejecting duplicate properties before dict conversion."""
    if type(raw) not in (str, bytes) or len(raw) > _MAX_JSON_BYTES:
        raise ValueError("Invalid native request JSON size or type")
    if type(raw) is bytes:
        raw = raw.decode("utf-8", errors="strict")
    if len(raw.encode("utf-8")) > _MAX_JSON_BYTES:
        raise ValueError("Native request JSON is too large")
    # Bound nesting before the recursive JSON decoder, ignoring delimiters inside strings.
    depth = 0
    in_string = False
    escaped = False
    for character in raw:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                raise ValueError("Native request JSON is too deep")
        elif character in "]}":
            depth -= 1

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate native request property")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("Non-finite native request JSON number")

    return plan_launch(json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant))


def _windows_path(value, *, directory=True):
    """Check raw components before PureWindowsPath can collapse aliases."""
    if type(value) is not str or not value or re.match(r"[A-Za-z]:[\\/]", value) is None:
        raise ValueError("Invalid Windows path")
    names = value[2:].replace("\\", "/").split("/")
    names.pop(0)
    if directory and names and names[-1] == "":
        names.pop()
    if not names and not directory:
        raise ValueError("Invalid Windows path")
    device = re.compile(r"CON(?:IN\$|OUT\$)?|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³]", re.IGNORECASE)
    for name in names:
        if (not name or name in (".", "..") or name.endswith((".", " "))
                or any(ord(character) < 32 or character in '<>:"|?*' for character in name)
                or device.fullmatch(name.split(".", 1)[0]) is not None):
            raise ValueError("Invalid Windows path component")
    return PureWindowsPath(value)


def _check_depth(text, limit=_MAX_JSON_DEPTH):
    """Bound nesting before the recursive JSON decoder, ignoring delimiters inside strings."""
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > limit:
                raise ValueError("Pack JSON is too deep")
        elif character in "]}":
            depth -= 1


def _read_pack_json(path):
    """Read one small pack manifest/registry, rejecting duplicates and non-finite numbers."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Pack file is missing: {path}")
    if path.stat().st_size > _MAX_MANIFEST_BYTES:
        raise ValueError(f"Pack file is too large: {path}")
    text = path.read_text(encoding="utf-8-sig")
    _check_depth(text)

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate property in pack file: {path}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Non-finite number in pack file: {path}")

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def _pack_member(root, relative):
    """Resolve a registry path inside its pack root and return it as an absolute path string.

    Registry values are relative to the pack root. The game's working directory is the runtime
    folder, so it must receive absolute paths.
    """
    if type(relative) is not str or not relative:
        raise ValueError(f"Invalid pack member path in {root}")
    parts = relative.replace("\\", "/").split("/")
    if re.match(r"[A-Za-z]:", relative) or relative.startswith(("/", "\\")) or ".." in parts or "" in parts:
        raise ValueError(f"Pack member path leaves its pack: {relative}")
    member = Path(root, *parts)
    if not member.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError(f"Pack member path leaves its pack: {relative}")
    if not member.is_file():
        raise ValueError(f"Pack member is missing: {member}")
    return str(member)


def _pack_payload(root, profile):
    """Return the pack's native_payload after checking it is the expected prepared profile."""
    manifest = _read_pack_json(Path(root, "pack.json"))
    payload = manifest.get("native_payload") if type(manifest) is dict else None
    if type(payload) is not dict or payload.get("profile") != profile:
        raise ValueError(f"Pack is not a {profile} pack: {root}")
    return manifest, payload


def _model_pack_arguments(root, taken=None):
    """Turn a prepared-native-v1 mech pack into --cc-model/--cc-model-normals arguments.

    `taken` maps each chassis already supplied by an earlier enabled pack to that pack's root. Such a
    chassis is left out of this pack, the same "first chassis wins" rule as prepared_mech_packs.py,
    because the native runtime refuses a second model or normal map for one chassis and level.
    Returns the arguments and the chassis this pack lost to earlier packs.

    The registry lists models; each keeps its file paths in an "environment" table using the
    names MW34_<ID>_MESH, MW34_<ID>_TEXTURES and MW34_<ID>_NORMALS, with LOD1_ after <ID> for
    the distance model. A level of detail is emitted only when both its mesh and textures exist.
    Alternative liveries (*_SKIN_*) are not part of this preview.
    """
    _, payload = _pack_payload(root, "prepared-native-v1")
    if payload.get("path_base") != "pack-root":
        raise ValueError(f"Mech pack paths must be relative to the pack root: {root}")
    registry = _read_pack_json(_pack_member(root, payload.get("registry")))
    models = registry.get("models") if type(registry) is dict else None
    if type(models) is not list or len(models) > _MAX_REGISTRY_MODELS:
        raise ValueError(f"Invalid mech pack registry: {root}")
    arguments = []
    overridden = []
    taken = {} if taken is None else taken
    for model in models:
        if type(model) is not dict:
            raise ValueError(f"Invalid mech pack registry entry: {root}")
        if model.get("backend") != "native" or model.get("status") not in _RUNTIME_MODEL_STATUSES:
            continue
        chassis = model.get("id")
        files = model.get("environment")
        if type(chassis) is not str or re.fullmatch(r"[a-z0-9]+", chassis) is None or type(files) is not dict:
            raise ValueError(f"Invalid mech pack registry entry: {root}")
        if chassis in taken:
            overridden.append({"chassis": chassis, "kept_from": taken[chassis]})
            continue
        supplied = False
        for level, infix in ((0, ""), (1, "LOD1_")):
            prefix = f"MW34_{chassis.upper()}_{infix}"
            # Same rule as prepared_mech_packs.py: the Bushwacker close mesh keeps its historical
            # MW34_BUSHWACKER_TEST name.
            mesh_name = "TEST" if chassis == "bushwacker" and level == 0 else "MESH"
            mesh, textures = files.get(prefix + mesh_name), files.get(prefix + "TEXTURES")
            if mesh is None or textures is None:
                continue
            arguments += ["--cc-model", chassis, str(level), _pack_member(root, mesh),
                          _pack_member(root, textures)]
            normals = files.get(prefix + "NORMALS")
            if normals is not None:
                arguments += ["--cc-model-normals", chassis, str(level), _pack_member(root, normals)]
            supplied = True
        if supplied:
            taken[chassis] = root
    return arguments, overridden


def _environment_pack_skip_reason(root):
    """Return why a prepared-environment-v1 map pack must be left out, or None to load it."""
    manifest, _ = _pack_payload(root, "prepared-environment-v1")
    files = manifest.get("files")
    if type(files) is not dict:
        raise ValueError(f"Map pack has no file table: {root}")
    for name, entry in files.items():
        size = entry.get("bytes") if type(entry) is dict else None
        if type(size) is not int or size < 0:
            raise ValueError(f"Map pack file table is invalid: {root}")
        if size >= _NATIVE_FILE_LIMIT:
            return f"{name} is {size} bytes; the native runtime loads files under 2 GiB"
    return None


def _preview_choices(preview):
    """Validate the schema-4 preview object and return its choices with defaults."""
    if type(preview) is not dict or not set(preview).issubset(_PREVIEW_FIELDS):
        raise ValueError("Invalid native preview fields")
    choices = {"draw_distance": 800, "hud": None, "hud_text": None, "geometry": None,
               "model_packs": [], "environment_packs": []}
    choices.update(preview)
    distance = choices["draw_distance"]
    if type(distance) is not int or distance not in _PREVIEW_DRAW_DISTANCES:
        raise ValueError("Native preview scenery distance must be 800, 1200 or 1600")
    if choices["hud"] is not None and choices["hud"] not in _PREVIEW_HUDS:
        raise ValueError("Unknown native preview HUD")
    if choices["hud_text"] is not None:
        if type(choices["hud_text"]) is not bool:
            raise ValueError("Native preview HUD text selection must be Boolean")
        if choices["hud"] != "core-critical":
            raise ValueError("Native preview HUD text needs the core-critical HUD")
    if choices["geometry"] is not None and choices["geometry"] not in _PREVIEW_GEOMETRY:
        raise ValueError("Unknown native preview geometry mode")
    for field in ("model_packs", "environment_packs"):
        packs = choices[field]
        if type(packs) is not list or len(packs) > _MAX_PREVIEW_PACKS:
            raise ValueError(f"Invalid native preview {field}")
    return choices


def _window_arguments(window_mode, width, height):
    """Return argv tokens for window presentation.

    The native runtime defaults to borderless desktop fullscreen; --window or --windowed makes
    it a window. Both fullscreen and borderless therefore emit no window tokens.
    """
    if window_mode == "windowed":
        return ["--window", f"{width}x{height}", "--windowed"]
    return []


def plan_launch(request):
    """Return complete argv or explicit unsupported reasons; never probe or start anything."""
    if type(request) is not dict:
        raise ValueError("Missing or unknown native request fields")
    schema = request.get("schema_version")
    if type(schema) is not int or schema not in (2, 3, 4):
        raise ValueError("Unsupported native request schema")
    allowed = {2: _FIELDS, 3: _FIELDS | {"visuals"}, 4: _FIELDS | {"visuals", "preview"}}[schema]
    if not _FIELDS.issubset(request) or not set(request).issubset(allowed):
        raise ValueError("Missing or unknown native request fields")
    pom = False
    if schema >= 3 and "visuals" in request:
        visuals = request["visuals"]
        if type(visuals) is not dict or not set(visuals).issubset({"pom"}):
            raise ValueError("Invalid native visuals fields")
        if "pom" in visuals:
            if type(visuals["pom"]) is not bool:
                raise ValueError("Native POM selection must be Boolean")
            pom = visuals["pom"]
    if pom and request["lighting"] != "normal":
        raise ValueError("Native POM requires normal lighting")
    preview = _preview_choices(request.get("preview", {})) if schema == 4 else None
    if request["engine"] != "mw3-re" or request["renderer"] != "vulkan-wsi":
        raise ValueError("Unsupported native engine or renderer")
    for field, minimum, maximum in (("width", 640, 7680), ("height", 480, 4320)):
        if type(request[field]) is not int or not minimum <= request[field] <= maximum:
            raise ValueError("Unsupported native window dimensions")
    if type(request["af"]) is not int or request["af"] not in (1, 2, 4, 8, 16):
        raise ValueError("Unsupported native anisotropic filtering")
    if type(request["render_thread"]) is not bool:
        raise ValueError("Native render-thread selection must be Boolean")
    if type(request["aa"]) is not str or request["aa"] not in (*_AA, "8"):
        raise ValueError("Unknown native antialiasing selection")
    if request["window_mode"] not in ("windowed", "fullscreen", "borderless"):
        raise ValueError("Unknown native window mode")
    if request["lighting"] not in ("off", "flat", "normal"):
        raise ValueError("Unknown native lighting selection")
    if type(request["assets"]) is not list or len(request["assets"]) > 128:
        raise ValueError("Invalid native asset list")
    runtime = _windows_path(request["runtime_root"])
    executable = _windows_path(request["executable"], directory=False)
    game = _windows_path(request["game_dir"])
    write = _windows_path(request["write_dir"])
    for asset in request["assets"]:
        _windows_path(asset)
    if executable == runtime or not executable.is_relative_to(runtime):
        raise ValueError("Native executable leaves the runtime root")
    for protected in (runtime, game):
        if write.is_relative_to(protected) or protected.is_relative_to(write):
            raise ValueError("Native write root overlaps a read-only input root")
    if preview is not None:
        for pack in preview["model_packs"] + preview["environment_packs"]:
            root = _windows_path(pack)
            if write.is_relative_to(root) or root.is_relative_to(write):
                raise ValueError("Native write root overlaps a preview pack")
    reasons = []
    if request["aa"] == "8":
        reasons.append("Saved 8-sample antialiasing has no qualified native mapping")
    if reasons:
        return {"ok": False, "reasons": reasons}
    argv = [
        request["executable"], "--install", request["game_dir"], "--write-dir", request["write_dir"],
        "--cc-vulkan-wsi",
        *_window_arguments(request["window_mode"], request["width"], request["height"]),
        "--cc-aa", _AA[request["aa"]], "--cc-af", str(request["af"]),
        "--cc-render-thread", "1" if request["render_thread"] else "0", "--cc-lighting", request["lighting"],
    ]
    if pom:
        argv.extend(("--cc-pom", "1"))
    skipped = []
    overridden_models = []
    if preview is not None:
        # 800 is the original range, so it adds no argument and older runtimes stay compatible.
        if preview["draw_distance"] != 800:
            argv.extend(("--cc-draw-distance", str(preview["draw_distance"])))
        if preview["hud"] is not None:
            argv.extend(("--cc-hud", preview["hud"]))
        if preview["hud_text"] is not None:
            argv.extend(("--cc-hud-text", "1" if preview["hud_text"] else "0"))
        if preview["geometry"] is not None:
            argv.extend(("--cc-geometry", preview["geometry"]))
        supplied_chassis = {}
        for pack in preview["model_packs"]:
            arguments, overridden = _model_pack_arguments(pack, supplied_chassis)
            argv.extend(arguments)
            overridden_models.extend({"root": pack, **item} for item in overridden)
        for pack in preview["environment_packs"]:
            reason = _environment_pack_skip_reason(pack)
            if reason is None:
                argv.extend(("--cc-environment-pack", pack))
            else:
                skipped.append({"root": pack, "reason": reason})
    for asset in request["assets"]:
        argv.extend(("--assets", asset))
    result = {"ok": True, "argv": argv, "working_directory": str(executable.parent)}
    if preview is not None:
        result["skipped_packs"] = skipped
        result["overridden_models"] = overridden_models
    return result
