"""Check a JSON value against the small part of JSON Schema the pack contracts use.

The contracts in docs/packs/schemas are ordinary JSON Schema files, so any standard
validator can read them. This repository's checks run with the standard library only
(see tools/check.py), so this module reads the keywords the contracts need and refuses
a schema that uses any other. That refusal is deliberate: a keyword this module skipped
would make a pack look valid here and invalid everywhere else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Keywords that describe the schema and never reject a value.
ANNOTATION_KEYWORDS = {"$schema", "$id", "$defs", "title", "description"}
CHECKED_KEYWORDS = {
    "$ref",
    "type",
    "const",
    "enum",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "pattern",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "minItems",
    "maxItems",
    "uniqueItems",
}


class UnsupportedSchemaError(Exception):
    """The schema uses something this module cannot check."""


@dataclass(frozen=True)
class Violation:
    """One way a value breaks its schema.

    path is where in the value, as a JSON Pointer ("" is the root). keyword is the
    schema keyword that rejected it, so a caller can tell an unknown field
    ("additionalProperties") from any other mistake.
    """

    path: str
    keyword: str
    message: str


def find_violations(value: Any, schema: dict[str, Any]) -> list[Violation]:
    """Every violation of schema in value, in the order the value is walked."""
    violations: list[Violation] = []
    _check(value, schema, schema, "", violations)
    return violations


def _resolve_reference(reference: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    prefix = "#/$defs/"
    if not reference.startswith(prefix):
        raise UnsupportedSchemaError(f"only {prefix}<name> references are supported: {reference}")
    name = reference[len(prefix) :]
    definitions = root_schema.get("$defs", {})
    if name not in definitions:
        raise UnsupportedSchemaError(f"no such definition: {reference}")
    return definitions[name]


def _is_type(value: Any, type_name: str) -> bool:
    # bool is a subclass of int in Python, but true is not a number in JSON Schema.
    is_boolean = isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return is_boolean
    if type_name == "integer":
        return isinstance(value, int) and not is_boolean
    if type_name == "number":
        return isinstance(value, (int, float)) and not is_boolean
    raise UnsupportedSchemaError(f"unsupported type: {type_name}")


def _same_json_value(left: Any, right: Any) -> bool:
    # 1 == True in Python; in JSON they are different values.
    return type(left) is type(right) and left == right


def _check(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    violations: list[Violation],
) -> None:
    unknown_keywords = set(schema) - ANNOTATION_KEYWORDS - CHECKED_KEYWORDS
    if unknown_keywords:
        raise UnsupportedSchemaError(f"unsupported keywords: {sorted(unknown_keywords)}")

    def report(keyword: str, message: str) -> None:
        violations.append(Violation(path, keyword, message))

    if "$ref" in schema:
        referenced = _resolve_reference(schema["$ref"], root_schema)
        _check(value, referenced, root_schema, path, violations)

    if "type" in schema and not _is_type(value, schema["type"]):
        report("type", f"expected {schema['type']}")
        # The remaining keywords assume the type; checking them would only add noise.
        return

    if "const" in schema and not _same_json_value(value, schema["const"]):
        report("const", f"expected {schema['const']!r}")
    if "enum" in schema:
        allowed = schema["enum"]
        if not any(_same_json_value(value, option) for option in allowed):
            report("enum", f"expected one of {allowed!r}")

    if isinstance(value, str):
        _check_string(value, schema, report)
    elif isinstance(value, bool):
        pass
    elif isinstance(value, (int, float)):
        if "minimum" in schema and value < schema["minimum"]:
            report("minimum", f"less than {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            report("maximum", f"more than {schema['maximum']}")
    elif isinstance(value, list):
        _check_array(value, schema, root_schema, path, violations, report)
    elif isinstance(value, dict):
        _check_object(value, schema, root_schema, path, violations, report)


def _check_string(value: str, schema: dict[str, Any], report: Any) -> None:
    if "minLength" in schema and len(value) < schema["minLength"]:
        report("minLength", f"shorter than {schema['minLength']} characters")
    if "maxLength" in schema and len(value) > schema["maxLength"]:
        report("maxLength", f"longer than {schema['maxLength']} characters")
    if "pattern" in schema and re.search(schema["pattern"], value) is None:
        report("pattern", f"does not match {schema['pattern']}")


def _check_array(
    value: list[Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    violations: list[Violation],
    report: Any,
) -> None:
    if "minItems" in schema and len(value) < schema["minItems"]:
        report("minItems", f"fewer than {schema['minItems']} items")
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        report("maxItems", f"more than {schema['maxItems']} items")
    if schema.get("uniqueItems"):
        for index, item in enumerate(value):
            repeated = any(_same_json_value(item, earlier) for earlier in value[:index])
            if repeated:
                report("uniqueItems", f"item {index} repeats an earlier item")
    if "items" in schema:
        for index, item in enumerate(value):
            _check(item, schema["items"], root_schema, f"{path}/{index}", violations)


def _check_object(
    value: dict[str, Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    violations: list[Violation],
    report: Any,
) -> None:
    for name in schema.get("required", []):
        if name not in value:
            report("required", f"missing {name}")
    known_properties = schema.get("properties", {})
    additional = schema.get("additionalProperties", True)
    for name, member in value.items():
        member_path = f"{path}/{name}"
        if name in known_properties:
            _check(member, known_properties[name], root_schema, member_path, violations)
        elif additional is False:
            violations.append(Violation(member_path, "additionalProperties", "unknown field"))
        elif isinstance(additional, dict):
            _check(member, additional, root_schema, member_path, violations)
