"""Convert owner-authored mech placements to the runtime MWHDLT1 format."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLACEMENTS = ROOT / "games/mw3/headlights/original-mounts.json"
DEFAULT_BINDING = (
    ROOT / "runtime/mw3-re/src/frontend/core_critical/renderer" / "headlight_original_binding.hpp"
)
MAGIC = b"MWHDLT1\0"
PROFILE_LIMIT = 18
ELEMENTAL_STOCK_ID = 7
LAMP_LIMIT = 8


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON number: " + value)


def read_bindings(source: str) -> dict[str, int]:
    """Read the launcher stock order from the runtime's authoritative binding table."""
    matches = re.findall(r'"(mech_[a-z0-9_]+\.flt)"', source)
    expected_count = 19
    if len(matches) != expected_count or len(set(matches)) != expected_count:
        raise ValueError("Could not identify the 19 unique stock members")
    mapping = {}
    for stock_id, member in enumerate(matches):
        if stock_id == ELEMENTAL_STOCK_ID:
            continue
        chassis = member.removeprefix("mech_").removesuffix(".flt")
        mapping[chassis] = stock_id
    # The Elemental is skipped above; also refuse a table that names it as a mech under another id.
    elemental_listed_twice = "elemental" in mapping
    if len(mapping) != PROFILE_LIMIT or elemental_listed_twice:
        raise ValueError("Runtime binding table does not describe 18 non-Elemental stock mechs")
    return mapping


def _text(value, field: str, maximum: int, pattern: str | None = None) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(field + " must be a non-empty string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError(field + " must be ASCII") from None
    if len(encoded) > maximum or (pattern is not None and re.fullmatch(pattern, value) is None):
        raise ValueError(field + " exceeds the runtime string contract")
    return encoded


def _string(value: str, field: str, maximum: int, pattern: str | None = None) -> bytes:
    encoded = _text(value, field, maximum, pattern)
    return struct.pack("<I", len(encoded)) + encoded


def _number(value, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(field + " must be a number")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(field + " is outside the runtime numeric range")
    try:
        packed = struct.pack("<f", number)
    except (OverflowError, struct.error):
        raise ValueError(field + " cannot be represented as float32") from None
    converted = struct.unpack("<f", packed)[0]
    if not math.isfinite(converted) or not minimum <= converted <= maximum:
        raise ValueError(field + " is outside the runtime float32 range")
    return converted


def _vector(value, field: str, minimum: float, maximum: float) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(field + " must contain exactly three numbers")
    return tuple(_number(component, field, minimum, maximum) for component in value)


def _lamp(lamp: object, profile_name: str) -> bytes:
    required = {"id", "space", "attachment", "position", "direction", "color",
                "intensity", "range", "inner_angle", "outer_angle"}
    if not isinstance(lamp, dict) or set(lamp) != required:
        raise ValueError(profile_name + " lamp fields do not match the source schema")
    result = bytearray()
    light_id = lamp["id"]
    result.extend(_string(light_id, "lamp id", 31, r"[a-z0-9_-]+"))
    if lamp["space"] != "guest_node":
        raise ValueError(profile_name + " original lamp must use guest_node space")
    result.extend(_string(lamp["space"], "lamp space", 10))
    result.extend(_string(lamp["attachment"], "lamp attachment", 31, r"[A-Za-z0-9._-]+"))

    position = _vector(lamp["position"], "lamp position", -100, 100)
    direction = _vector(lamp["direction"], "lamp direction", -1, 1)
    direction_length = math.hypot(*direction)
    if abs(direction_length - 1.0) > 0.00001:
        raise ValueError(profile_name + " lamp direction is not unit length")
    direction = tuple(component / direction_length for component in direction)
    color = _vector(lamp["color"], "lamp color", 0, 1)
    scalars = (
        _number(lamp["intensity"], "lamp intensity", 0, 8),
        _number(lamp["range"], "lamp range", 1, 256),
        _number(lamp["inner_angle"], "lamp inner angle", 0, 89),
        _number(lamp["outer_angle"], "lamp outer angle", 0, 89),
    )
    if scalars[2] >= scalars[3]:
        raise ValueError(profile_name + " lamp inner angle must be less than outer angle")
    for vector in (position, direction, color):
        result.extend(struct.pack("<3f", *vector))
    result.extend(struct.pack("<4f", *scalars))
    return bytes(result)


def compile_catalog(placements: object, binding_source: str) -> bytes:
    if not isinstance(placements, dict) or len(placements) != PROFILE_LIMIT:
        raise ValueError("Expected exactly 18 original mech placement profiles")
    stock_ids = read_bindings(binding_source)
    if set(placements) != set(stock_ids):
        missing = sorted(set(stock_ids) - set(placements))
        unknown = sorted(set(placements) - set(stock_ids))
        raise ValueError(f"Placement chassis mismatch; missing={missing}, unknown={unknown}")

    profiles = []
    for chassis, stock_id in sorted(stock_ids.items(), key=lambda item: item[1]):
        wrapper = placements[chassis]
        if not isinstance(wrapper, dict) or set(wrapper) != {"original"}:
            raise ValueError(chassis + " must contain exactly one original profile")
        profile = wrapper["original"]
        if not isinstance(profile, dict) or set(profile) != {"model_sha256", "lamps"}:
            raise ValueError(chassis + " original profile fields do not match the source schema")
        model_hash = profile["model_sha256"]
        if not isinstance(model_hash, str) or re.fullmatch(r"[0-9a-f]{64}", model_hash) is None:
            raise ValueError(chassis + " model_sha256 must be 64 lowercase hexadecimal characters")
        lamps = profile["lamps"]
        if not isinstance(lamps, list) or not 1 <= len(lamps) <= LAMP_LIMIT:
            raise ValueError(chassis + " must have between one and eight lamps")
        lamp_ids = [lamp.get("id") if isinstance(lamp, dict) else None for lamp in lamps]
        valid_ids = all(isinstance(value, str) for value in lamp_ids)
        if not valid_ids or len(set(lamp_ids)) != len(lamp_ids):
            raise ValueError(chassis + " lamp ids must be unique strings")

        # The runtime requires a nonzero 32-byte identity. Raw SHA-256 digest bytes
        # bind that identity to the same original model hash used for profile matching.
        identity = bytes.fromhex(model_hash)
        if len(identity) != 32 or not any(identity):
            raise ValueError(chassis + " model identity must be a nonzero 32-byte digest")
        row = bytearray(struct.pack("<II", stock_id, 0))
        row.extend(_string(model_hash, "model hash", 64))
        row.extend(struct.pack("<I", 0))
        row.extend(struct.pack("<I", 0))
        row.extend(identity)
        row.extend(struct.pack("<I", len(lamps)))
        for lamp in lamps:
            row.extend(_lamp(lamp, chassis))
        profiles.append(bytes(row))
    return MAGIC + struct.pack("<I", len(profiles)) + b"".join(profiles)


def build_catalog(placements_path: Path = DEFAULT_PLACEMENTS,
                  binding_path: Path = DEFAULT_BINDING) -> bytes:
    try:
        placements = json.loads(placements_path.read_text(encoding="utf-8"),
                                object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        binding_source = binding_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        message = "Cannot read stock headlight inputs: " + str(error)
        raise ValueError(message) from None
    return compile_catalog(placements, binding_source)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--placements", type=Path, default=DEFAULT_PLACEMENTS)
    parser.add_argument("--binding", type=Path, default=DEFAULT_BINDING)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(build_catalog(arguments.placements, arguments.binding))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
