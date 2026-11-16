"""Pure MW3-RE argv planning; lexical validation is not package/execution admission."""

from pathlib import PureWindowsPath
import json
import re


_FIELDS = frozenset({
    "schema_version", "engine", "runtime_root", "executable", "game_dir", "write_dir", "renderer",
    "width", "height", "aa", "af", "window_mode", "render_thread", "lighting", "assets",
})
_AA = {"off": "off", "1": "off", "fxaa": "fxaa", "2": "ssaa2", "4": "ssaa4"}
_MAX_JSON_BYTES = 2 * 1024 * 1024
_MAX_JSON_DEPTH = 64


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


def plan_launch(request):
    """Return complete argv or explicit unsupported reasons; never probe or start anything."""
    if type(request) is not dict:
        raise ValueError("Missing or unknown native request fields")
    schema = request.get("schema_version")
    if type(schema) is not int or schema not in (2, 3):
        raise ValueError("Unsupported native request schema")
    allowed = _FIELDS if schema == 2 else _FIELDS | {"visuals"}
    if not _FIELDS.issubset(request) or not set(request).issubset(allowed):
        raise ValueError("Missing or unknown native request fields")
    pom = False
    if schema == 3 and "visuals" in request:
        visuals = request["visuals"]
        if type(visuals) is not dict or not set(visuals).issubset({"pom"}):
            raise ValueError("Invalid native visuals fields")
        if "pom" in visuals:
            if type(visuals["pom"]) is not bool:
                raise ValueError("Native POM selection must be Boolean")
            pom = visuals["pom"]
    if pom and request["lighting"] != "normal":
        raise ValueError("Native POM requires normal lighting")
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
    reasons = []
    if request["window_mode"] != "windowed":
        reasons.append("Fullscreen and borderless presentation are not implemented in this slice")
    if request["aa"] == "8":
        reasons.append("Saved 8-sample antialiasing has no qualified native mapping")
    if reasons:
        return {"ok": False, "reasons": reasons}
    argv = [
        request["executable"], "--install", request["game_dir"], "--write-dir", request["write_dir"],
        "--cc-vulkan-wsi", "--window", f'{request["width"]}x{request["height"]}', "--windowed",
        "--cc-aa", _AA[request["aa"]], "--cc-af", str(request["af"]),
        "--cc-render-thread", "1" if request["render_thread"] else "0", "--cc-lighting", request["lighting"],
    ]
    if pom:
        argv.extend(("--cc-pom", "1"))
    for asset in request["assets"]:
        argv.extend(("--assets", asset))
    return {"ok": True, "argv": argv, "working_directory": str(executable.parent)}
