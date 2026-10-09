"""Only authored binary fixtures; no game bytes or external codecs."""

import importlib.util
from pathlib import Path
import struct
import unittest


spec = importlib.util.spec_from_file_location("video_probe", Path(__file__).resolve().parents[1] /
                                         "tools" / "asset-inventory" / "video_probe.py")
video_probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video_probe)


def chunk(kind, payload):
    return kind + struct.pack("<I", len(payload)) + payload + b"\x00" * (len(payload) % 2)


def avi_fixture():
    main = struct.pack("<14I", 40000, 0, 0, 16, 2, 0, 2, 0, 4, 2, 0, 0, 0, 0)
    video_header = struct.pack("<4s4sIHH8I4h", b"vids", b"TEST", 0, 0, 0, 0, 1, 25, 0, 2, 0, 0, 0, 0, 0, 4, 2)
    video_format = struct.pack("<IiiHHIIiiII", 40, 4, 2, 1, 24, int.from_bytes(b"TEST", "little"), 0, 0, 0, 0, 0)
    audio_header = struct.pack("<4s4sIHH8I4h", b"auds", b"\x00" * 4, 0, 0, 0, 0, 1, 8000, 0, 640, 0, 0, 2, 0, 0, 0, 0)
    audio_format = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    headers = chunk(b"avih", main)
    headers += chunk(b"LIST", b"strl" + chunk(b"strh", video_header) + chunk(b"strf", video_format))
    headers += chunk(b"LIST", b"strl" + chunk(b"strh", audio_header) + chunk(b"strf", audio_format))
    movie = chunk(b"00dc", b"abc") + chunk(b"LIST", b"rec " + chunk(b"00dc", b"defg") + chunk(b"01wb", b"\0" * 1280))
    return chunk(b"RIFF", b"AVI " + chunk(b"LIST", b"hdrl" + headers) + chunk(b"LIST", b"movi" + movie))


def both(value, width):
    return value.to_bytes(width, "little") + value.to_bytes(width, "big")


def record(name, extent, size, flags=0):
    out = bytearray(33 + len(name) + (not len(name) % 2))
    out[0] = len(out)
    out[2:10] = both(extent, 4)
    out[10:18] = both(size, 4)
    out[25] = flags
    out[28:32] = both(1, 2)
    out[32] = len(name)
    out[33:33 + len(name)] = name
    return bytes(out)


def iso_fixture():
    data = bytearray(24 * 2048)
    pvd = bytearray(2048)
    pvd[:7] = b"\x01CD001\x01"
    pvd[40:72] = b"AUTHORED".ljust(32, b" ")
    pvd[80:88] = both(24, 4)
    pvd[128:132] = both(2048, 2)
    pvd[156:190] = record(b"\0", 20, 2048, 2)
    data[16 * 2048:17 * 2048] = pvd
    data[17 * 2048:17 * 2048 + 7] = b"\xffCD001\x01"
    directory = record(b"\0", 20, 2048, 2) + record(b"\x01", 20, 2048, 2) + record(b"VIDEO", 21, 2048, 2)
    data[20 * 2048:20 * 2048 + len(directory)] = directory
    payload = avi_fixture()
    directory = record(b"\0", 21, 2048, 2) + record(b"\x01", 20, 2048, 2) + record(b"TEST.AVI;1", 22, len(payload))
    data[21 * 2048:21 * 2048 + len(directory)] = directory
    data[22 * 2048:22 * 2048 + len(payload)] = payload
    return data


class AssetVideoTests(unittest.TestCase):
    def test_header_timing_audio_and_padded_nested_chunks(self):
        data = avi_fixture()
        result = video_probe.avi_metadata(data, 0, len(data))
        self.assertEqual(result["main_header"]["total_frames"], 2)
        self.assertEqual(result["streams"][0]["units_per_second"], 25)
        self.assertAlmostEqual(result["streams"][0]["duration_seconds"], 0.08)
        self.assertEqual(result["streams"][0]["video_format"]["compression_fourcc"], "TEST")
        self.assertEqual(result["streams"][1]["audio_format"]["sample_rate"], 8000)
        self.assertEqual(result["movie_chunk_counts"], {"00dc": 2, "01wb": 1})
        self.assertEqual(result["streams"][0]["observed_data_bytes"], {"00dc": 7})

    def test_riff_outside_source_and_chunk_outside_parent(self):
        data = bytearray(avi_fixture())
        struct.pack_into("<I", data, 4, len(data) + 1)
        with self.assertRaisesRegex(ValueError, "RIFF bounds"):
            video_probe.avi_metadata(data, 0, len(data))
        data = bytearray(avi_fixture())
        struct.pack_into("<I", data, 16, len(data))
        with self.assertRaisesRegex(ValueError, "parent bounds"):
            video_probe.avi_metadata(data, 0, len(data))

    def test_primary_tree_resolves_exact_file_span(self):
        data = iso_fixture()
        result = video_probe.iso_files(data)
        self.assertEqual(result["volume_id"], "AUTHORED")
        self.assertEqual(result["directory_count"], 2)
        item = result["files"][0]
        self.assertEqual(item["path"], "VIDEO/TEST.AVI;1")
        self.assertEqual(data[item["offset"]:item["offset"] + item["bytes"]], avi_fixture())

    def test_iso_endian_and_extent_bounds_are_rejected(self):
        data = iso_fixture()
        data[16 * 2048 + 84] ^= 1
        with self.assertRaisesRegex(ValueError, "both-endian"):
            video_probe.iso_files(data)
        data = iso_fixture()
        data[16 * 2048 + 158:16 * 2048 + 166] = both(24, 4)
        with self.assertRaisesRegex(ValueError, "extent exceeds"):
            video_probe.iso_files(data)

    def test_iso_multiextent_and_cycle_are_rejected(self):
        data = iso_fixture()
        data[21 * 2048 + 68 + 25] |= 0x80
        with self.assertRaisesRegex(ValueError, "multi-extents"):
            video_probe.iso_files(data)
        data = iso_fixture()
        data[20 * 2048 + 68 + 2:20 * 2048 + 68 + 10] = both(20, 4)
        with self.assertRaisesRegex(ValueError, "cycle"):
            video_probe.iso_files(data)

    def test_repeated_primary_descriptor_requires_identical_bytes(self):
        data = iso_fixture()
        data[18 * 2048:19 * 2048] = data[17 * 2048:18 * 2048]
        data[17 * 2048:18 * 2048] = data[16 * 2048:17 * 2048]
        self.assertEqual(video_probe.iso_files(data)["descriptor_types"], [1, 1, 255])
        data[17 * 2048 + 40] ^= 1
        with self.assertRaisesRegex(ValueError, "Conflicting primary"):
            video_probe.iso_files(data)


if __name__ == "__main__":
    unittest.main()
