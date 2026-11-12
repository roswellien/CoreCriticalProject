"""Authored emission descriptors: binding, limits and corruption rejection."""

import copy
import struct
import unittest

import owned_emission as emission


class OwnedEmissionTests(unittest.TestCase):
    def setUp(self):
        self.bindings = [dict(owner="torso", material="Glass", width=16, height=8,
                              hash=12345, bounds=((-1, 1), (-1, 1), (-1, 1)))]
        self.records = [dict(id="eyes", batch=0, strength=.35, regions=[(0, .2, .3, .7)],
                             anchors=[dict(id="left", position=(-.3, 0, .2), color=(1, .01, .01),
                                           radius=1.2, intensity=.1),
                                      dict(id="right", position=(.3, 0, .2), color=(1, .01, .01),
                                           radius=1.2, intensity=.1)])]
        self.data = emission.pack(77, self.bindings, self.records)

    def test_roundtrip_and_zero_control(self):
        result = emission.read(self.data, 77, self.bindings)
        self.assertEqual(result[0]["id"], "eyes")
        self.assertEqual([a["id"] for a in result[0]["anchors"]], ["left", "right"])
        self.assertAlmostEqual(result[0]["strength"], .35, places=6)
        self.records[0]["strength"] = 0
        for anchor in self.records[0]["anchors"]:
            anchor["intensity"] = 0
        self.assertEqual(emission.read(emission.pack(77, self.bindings, self.records),
                                       77, self.bindings)[0]["strength"], 0)

    def test_mesh_color_owner_and_batch_identity(self):
        weighted = copy.deepcopy(self.bindings)
        weighted[0]["rigid"] = False
        with self.assertRaisesRegex(ValueError, "rigid batch"):
            emission.read(self.data, 77, weighted)
        with self.assertRaises(ValueError):
            emission.read(self.data, 78, self.bindings)
        for key, value in (("owner", "foreign"), ("material", "Foreign"),
                           ("width", 32), ("height", 16), ("hash", 12346)):
            wrong = copy.deepcopy(self.bindings)
            wrong[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                emission.read(self.data, 77, wrong)
        wrong = bytearray(self.data)
        struct.pack_into("<I", wrong, 52, 1)
        with self.assertRaises(ValueError):
            emission.read(bytes(wrong), 77, self.bindings)

    def test_truncation_trailing_magic_and_names(self):
        for length in (0, 19, 20, 147, 163, len(self.data) - 1):
            with self.subTest(length=length), self.assertRaises(ValueError):
                emission.read(self.data[:length], 77, self.bindings)
        for data in (self.data + b"x", b"BADMAGIC" + self.data[8:], b"x" * (emission.MAX_BYTES + 1)):
            with self.assertRaises(ValueError):
                emission.read(data, 77, self.bindings)
        wrong = bytearray(self.data)
        wrong[25] = 65  # Nonzero padding after the record ID's terminator.
        with self.assertRaises(ValueError):
            emission.read(bytes(wrong), 77, self.bindings)

    def test_limits_invalid_rectangles_anchors_and_duplicates(self):
        changes = [dict(strength=float("nan")), dict(strength=-1), dict(strength=3),
                   dict(regions=[]), dict(regions=[(0, 0, 1, 1)] * 33),
                   dict(regions=[(.5, 0, .2, 1)]), dict(regions=[(0, -1, 1, 1)]),
                   dict(anchors=self.records[0]["anchors"] * 5),
                   dict(anchors=[self.records[0]["anchors"][0]] * 2)]
        for values in changes:
            records = copy.deepcopy(self.records)
            records[0].update(values)
            with self.subTest(values=values), self.assertRaises((ValueError, OverflowError)):
                emission.pack(77, self.bindings, records)
        for key, value in (("position", (6, 0, 0)), ("radius", 5), ("intensity", -1),
                           ("color", (1, float("inf"), 0))):
            records = copy.deepcopy(self.records)
            records[0]["anchors"][0][key] = value
            with self.subTest(key=key), self.assertRaises((ValueError, OverflowError)):
                emission.pack(77, self.bindings, records)
        with self.assertRaises(ValueError):
            emission.pack(77, self.bindings, self.records * 2)


if __name__ == "__main__":
    unittest.main()
