"""Validate the original eight-slot skin grammar and preserve implicit lookups.

MW3 derives alternate textures by appending a suffix to both members of each
primary alias (sub_474500, VA 47463E–474702). Namespacing must preserve that
relationship. This module supplies data to the original parser, not skin logic.
"""

import re

CAPABILITY = "legacy-mech-skins"
MESSAGES = ("MSG_SKIN_PRIMARY", *("MSG_SKIN_VARIANT" + letter for letter in "BCDEFGH"))


def metadata(rows):
    """Check ordered, stable skin identities without reading binary resources."""
    if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
        raise ValueError("Legacy skins require 1–8 ordered records")
    ids, suffixes = set(), set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"id", "message", "suffix"}:
            raise ValueError("Invalid legacy skin metadata fields")
        ident, suffix = row["id"], row["suffix"]
        if (
            not isinstance(ident, str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", ident)
            or ident in ids
            or row["message"] != MESSAGES[index]
            or not isinstance(suffix, str)
            or (suffix != "" if index == 0 else not re.fullmatch(r"_[a-z0-9]{1,8}", suffix))
            or suffix in suffixes
        ):
            raise ValueError("Invalid, duplicate or out-of-order legacy skin metadata")
        ids.add(ident)
        suffixes.add(suffix)
    return rows


def texture_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,31}", value):
        raise ValueError("Invalid legacy skin texture name")
    return value


def _entries(values, damage=False):
    if not isinstance(values, list) or not 1 <= len(values) <= 512:
        raise ValueError("Invalid legacy skin texture list")
    names = set()
    for value in values:
        if damage and type(value) is int and value == 0:
            continue
        if isinstance(value, list):
            if len(value) != 2:
                raise ValueError("Legacy skin aliases require exactly two names")
            names.update(texture_name(name) for name in value)
        else:
            names.add(texture_name(value))
    return names


def definition_skins(definition):
    """Return metadata and texture families from the supported donor grammar."""
    body = definition[0]
    if body.count("skins") != 1:
        raise ValueError("Missing or repeated legacy skins field")
    position = body.index("skins") + 1
    if position >= len(body):
        raise ValueError("Missing legacy skins value")
    block = body[position]
    if not isinstance(block, list) or not block or len(block) % 2:
        raise ValueError("Invalid legacy skins block")
    keys = block[::2]
    has_damage = keys[-1] == "damage"
    messages = keys[:-1] if has_damage else keys
    if messages != list(MESSAGES[: len(messages)]) or not 1 <= len(messages) <= 8:
        raise ValueError("Unsupported legacy skin order or grammar")
    primary = _entries(block[1])
    rows = [{"id": "primary", "message": MESSAGES[0], "suffix": ""}]
    for index, message in enumerate(messages[1:], 1):
        value = block[index * 2 + 1]
        if not isinstance(value, list) or len(value) != 1:
            raise ValueError("Legacy alternate skin requires one suffix")
        rows.append(
            {
                "id": message.removeprefix("MSG_SKIN_").lower(),
                "message": message,
                "suffix": value[0],
            }
        )
    metadata(rows)
    required = set(primary)
    for row in rows[1:]:
        required.update(texture_name(name + row["suffix"]) for name in primary)
    if has_damage:
        damage = block[-1]
        if not isinstance(damage, list) or len(damage) != len(block[1]):
            raise ValueError("Legacy damage and primary skin lengths disagree")
        required.update(_entries(damage, damage=True))
    return rows, primary, required


def validate(definition, textures, rows=None):
    """Validate embedded lookups before any composed resource can be published."""
    body = definition[0]
    if rows is None and "skins" not in body:
        return
    actual, _, required = definition_skins(definition)
    if rows is None:
        if len(actual) > 1:
            raise ValueError("Alternate legacy skins require descriptor schema 2; upgrade the pack")
    else:
        metadata(rows)
        if [(row["message"], row["suffix"]) for row in rows] != [
            (row["message"], row["suffix"]) for row in actual
        ]:
            raise ValueError("Legacy skin metadata and definition disagree")
    missing = required - textures.keys()
    if missing:
        raise ValueError("Missing legacy skin texture: " + min(missing))


def texture_names(data, target):
    """Namespace declared families together and reject ambiguous ownership."""
    textures = data["textures"]
    if "skins" not in data:
        return {name: target + "_t" + str(index) for index, name in enumerate(sorted(textures))}
    _, primary, _ = definition_skins(data["definition"])
    names = {}
    for index, base in enumerate(sorted(primary)):
        for row in data["skins"]:
            original = base + row["suffix"]
            generated = texture_name(target + "_t" + str(index) + row["suffix"])
            if original in names:
                raise ValueError("Ambiguous legacy skin texture family: " + original)
            names[original] = generated
    for index, name in enumerate(sorted(textures.keys() - names.keys()), len(primary)):
        names[name] = texture_name(target + "_t" + str(index))
    if len({name.casefold() for name in names.values()}) != len(names):
        raise ValueError("Colliding generated legacy skin texture names")
    return names
