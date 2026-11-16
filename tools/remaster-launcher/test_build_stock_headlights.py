"""Check deterministic MWHDLT1 conversion and the committed placement inventory."""
import copy
import json
from pathlib import Path
import struct
import unittest

import build_stock_headlights as converter


ROOT = Path(__file__).resolve().parents[2]
PLACEMENTS = ROOT / "games/mw3/headlights/original-mounts.json"
BINDING = ROOT / "runtime/mw3-re/src/frontend/core_critical/renderer/headlight_original_binding.hpp"


def read_string(data: bytes, offset: int) -> tuple[str, int]:
    length = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    return data[offset:offset + length].decode("ascii"), offset + length


def read_catalog(data: bytes) -> list[dict]:
    if data[:8] != b"MWHDLT1\0":
        raise AssertionError("wrong catalog magic")
    count = struct.unpack_from("<I", data, 8)[0]
    offset = 12
    profiles = []
    for _ in range(count):
        stock_id, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        model_hash, offset = read_string(data, offset)
        first_mesh, offset = read_string(data, offset)
        second_mesh, offset = read_string(data, offset)
        identity = data[offset:offset + 32]
        offset += 32
        lamp_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        lamps = []
        for _ in range(lamp_count):
            lamp_id, offset = read_string(data, offset)
            space, offset = read_string(data, offset)
            attachment, offset = read_string(data, offset)
            values = struct.unpack_from("<13f", data, offset)
            offset += 13 * 4
            lamps.append(dict(id=lamp_id, space=space, attachment=attachment, values=values))
        profiles.append(dict(stock_id=stock_id, kind=kind, model_hash=model_hash,
                             meshes=(first_mesh, second_mesh), identity=identity, lamps=lamps))
    if offset != len(data):
        raise AssertionError("catalog has trailing bytes")
    return profiles


class BuildStockHeadlightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.placements = json.loads(PLACEMENTS.read_text(encoding="utf-8"))
        cls.binding_source = BINDING.read_text(encoding="utf-8")

    def test_real_catalog_round_trip_has_all_original_profiles_and_lamps(self):
        data = converter.compile_catalog(self.placements, self.binding_source)
        self.assertEqual(data, converter.compile_catalog(self.placements, self.binding_source))
        profiles = read_catalog(data)
        bindings = converter.read_bindings(self.binding_source)
        self.assertEqual(len(profiles), 18)
        self.assertEqual(sum(len(profile["lamps"]) for profile in profiles), 93)
        self.assertEqual([profile["stock_id"] for profile in profiles], sorted(bindings.values()))
        for chassis, profile in zip(sorted(bindings, key=bindings.get), profiles):
            source = self.placements[chassis]["original"]
            self.assertEqual(profile["stock_id"], bindings[chassis])
            self.assertEqual(profile["kind"], 0)
            self.assertEqual(profile["model_hash"], source["model_sha256"])
            self.assertEqual(profile["identity"], bytes.fromhex(source["model_sha256"]))
            self.assertEqual(profile["meshes"], ("", ""))
            self.assertEqual([lamp["id"] for lamp in profile["lamps"]],
                             [lamp["id"] for lamp in source["lamps"]])

    def test_rejects_chassis_hash_lamp_and_field_contract_violations(self):
        cases = []
        unknown_chassis = copy.deepcopy(self.placements)
        unknown_chassis["not-a-stock-mech"] = unknown_chassis.pop("annihilator")
        cases.append(unknown_chassis)
        bad_hash = copy.deepcopy(self.placements)
        bad_hash["annihilator"]["original"]["model_sha256"] = "G" * 64
        cases.append(bad_hash)
        too_many = copy.deepcopy(self.placements)
        too_many["annihilator"]["original"]["lamps"] *= 2
        cases.append(too_many)
        invalid_direction = copy.deepcopy(self.placements)
        invalid_direction["annihilator"]["original"]["lamps"][0]["direction"] = [0, 0, 0]
        cases.append(invalid_direction)
        invalid_angle = copy.deepcopy(self.placements)
        lamp = invalid_angle["annihilator"]["original"]["lamps"][0]
        lamp["inner_angle"] = lamp["outer_angle"]
        cases.append(invalid_angle)
        invalid_space = copy.deepcopy(self.placements)
        invalid_space["annihilator"]["original"]["lamps"][0]["space"] = "donor_bone"
        cases.append(invalid_space)
        invalid_id = copy.deepcopy(self.placements)
        invalid_id["annihilator"]["original"]["lamps"][0]["id"] = "bad id"
        cases.append(invalid_id)
        for index, candidate in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                converter.compile_catalog(candidate, self.binding_source)

    def test_rejects_duplicate_json_properties_and_non_finite_values(self):
        with self.assertRaisesRegex(ValueError, "Duplicate JSON property"):
            json.loads('{"a": 1, "a": 2}', object_pairs_hook=converter._unique_object)
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            json.loads('{"a": NaN}', parse_constant=converter._reject_constant)


if __name__ == "__main__":
    unittest.main()
