"""Corruption controls for the game-call evidence verifier (no game bytes)."""

import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools/in-game-hook/verify_trace.py"
SPEC = importlib.util.spec_from_file_location("verify_trace", MODULE)
trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trace)


def call(event, count, n=1, base=1000):
    eax, edx, flags = trace.oracle(n, base)
    return {"event": event, "call": count, "pid": 42, "tid": 43,
            "caller_va": trace.CALLER, "n": n, "base": base,
            "eax": eax, "edx": edx, "flags": flags,
            "original_eax": eax, "original_edx": edx, "original_flags": flags,
            "registers_match": True, "stack_delta": 8, "memory_unchanged": True}


def records():
    return [{"event": "identity", "profile": "mw3-us-1-2-retail",
             "image_sha256": trace.IMAGE_SHA, "entry_va": trace.ENTRY,
             "replacement": "authored-x86-integer-helper-v1"},
            {"event": "selftest", "cases": 10400, "mismatches": 0,
             "memory_bytes_per_case": 4096, "seed": 13364},
            {"event": "comparison_controls", "cases": 7, "rejected": 7},
            *[call("hook_selftest_call", i) for i in range(1, 65)],
            {"event": "hook_thunk_selftest", "cases": 64, "mismatches": 0,
             "caller_memory_bytes_per_case": 1024, "fp_vector_preserved": True},
            {"event": "installed", "pid": 42, "entry_va": trace.ENTRY,
             "hook_va": 0x10000000, "patched_bytes": 7, "on_disk_game_unchanged": True},
            call("game_call", 1)]


class TraceTests(unittest.TestCase):
    def test_independent_known_arithmetic(self):
        self.assertEqual(trace.oracle(0, 0), (312, 0, 0x44))
        self.assertEqual(trace.oracle(1, 1000), (1500, 47, 0x10))
        self.assertEqual(trace.oracle(0xFFFFFFFF, 0xFFFFFFFF), (123, 0xFFFFFFD1, 0x95))

    def test_valid_trace(self):
        pid, calls = trace.check_log(records(), live=True)
        self.assertEqual((pid, len(calls)), (42, 1))

    def test_selftests_and_installation_do_not_count(self):
        with self.assertRaisesRegex(trace.EvidenceError, "no actual game_call"):
            trace.check_log(records()[:-1], live=True)

    def test_corrupt_live_call(self):
        # Change one field of otherwise valid evidence; every mutation must fail.
        controls = {"event": "hook_selftest_call", "call": 2, "pid": 99,
                    "tid": 0, "caller_va": trace.CALLER + 1, "eax": 1501,
                    "edx": 48, "flags": 0, "original_eax": 0,
                    "original_edx": 0, "original_flags": 0x410,
                    "registers_match": False, "stack_delta": 4,
                    "memory_unchanged": False, "n": True, "base": -1}
        for field, value in controls.items():
            with self.subTest(field=field):
                corrupt = records()
                corrupt[-1][field] = value
                with self.assertRaises(trace.EvidenceError):
                    trace.check_log(corrupt, live=True)

    def test_fatal_and_unknown_events_rejected(self):
        for event in ("fatal", "unknown"):
            with self.subTest(event=event), self.assertRaises(trace.EvidenceError):
                trace.check_log(records() + [{"event": event}], live=True)

    def test_initialization_corruption(self):
        valid = records()
        mutations = [(0, "image_sha256", "wrong"), (1, "mismatches", 1),
                     (2, "rejected", 6), (3, "call", 2),
                     (67, "fp_vector_preserved", False), (68, "pid", 99),
                     (68, "patched_bytes", 5)]
        for index, field, value in mutations:
            with self.subTest(index=index, field=field):
                corrupt = copy.deepcopy(valid)
                corrupt[index][field] = value
                with self.assertRaises(trace.EvidenceError):
                    trace.check_log(corrupt, live=True)


if __name__ == "__main__":
    unittest.main()
