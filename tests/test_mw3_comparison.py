"""Independent corpus/oracle and evidence-corruption tests; no MW3 execution."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

LIFTING = Path(__file__).resolve().parents[1] / "tools/lifting"
sys.path.insert(0, str(LIFTING))
import compare_mw3_leaf as leaf
import verify_mw3_leaf as verify


def request(n=1, base=1000, flags=0x202, stack_offset=2049):
    return (0x11111111, base, 0x33333333, 0x44444444,
            leaf.MEMORY_BASE + stack_offset, 0x66666666, 0x77777777,
            0x88888888, flags, leaf.ENTRY, n, 0xAABBCCDD, 0x12345678)


def valid_controls():
    return {"admission_negative_controls": [
        {"name": name, "outcome": "rejected", "reason": "admitted identity differs"}
        for name in leaf.ADMISSION_CHECKS],
        "comparator_negative_controls": leaf.comparator_controls(leaf.expected(request())),
        "worker_negative_controls": [
            {"role": role, "name": name, "outcome": "rejected", "reason": "protocol rejected"}
            for role in ("reference", "O0", "O2") for name in leaf.REQUEST_CHECKS]}


def layout_evidence():
    build = {"llvm_dll_sha256": "a" * 64, "artifacts": {
        "sub_00409ed0-guest.ll": "b" * 64, "sub_00409ed0-host.ll": "c" * 64}}
    layout = {"version": 1, "profile": "mw3-helper", "entry_va": leaf.ENTRY,
              "llvm_version": [21, 1, 8], "dll_sha256": "a" * 64,
              "guest_ir_sha256": "b" * 64, "host_ir_sha256": "c" * 64,
              "guest_pointer_bits": 32, "host_pointer_bits": 64,
              "guest_address_intrinsics_bits": 32, "state_bytes": 3504,
              "all_struct_layouts_equal": True, "indirect_calls": 0,
              "pointer_integer_conversions": 0,
              "struct_layouts": {"struct.State": {"size": 3504, "offsets": [0]},
                                 "struct.X86State": {"offsets": [0, 16, 2064]},
                                 "struct.ArithFlags": {"offsets": list(range(16))}},
              "bridges": ["__remill_function_return", "__remill_read_memory_32"],
              "flag_annotation_identities": ["__remill_flag_computation_" + name
                                             for name in ("carry", "overflow", "sign", "zero")],
              "undefined_flag_policy": {
                  "policy": "straight-line-ssa-overwritten-af-of-v1", "undefined_calls": 2,
                  "replacement_value": 0, "flag_offsets": [2069, 2077],
                  "observable_undefined_values": 0, "blocks": ["entry", "finish"],
                  "stores": [{"offset": 2069, "origins": ["%u0"], "store_instruction": 4, "block": "entry"},
                             {"offset": 2077, "origins": ["%u1"], "store_instruction": 5, "block": "entry"}],
                  "overwrites": [{"offset": 2069, "origins": ["%u0"], "store_instruction": 4,
                                  "overwrite_instruction": 8, "block": "finish"},
                                 {"offset": 2077, "origins": ["%u1"], "store_instruction": 5,
                                  "overwrite_instruction": 9, "block": "finish"}]}}
    return layout, build


def authored_snapshot(folder, pairs):
    """Synthetic valid logger protocol records; never evidence of real play."""
    def call(event, count, n=1, base=1000):
        eax, edx, flags = leaf.oracle(n, base, 0x202)
        return {"event": event, "call": count, "pid": 42, "tid": 43,
                "caller_va": 0x405173, "n": n, "base": base,
                "eax": eax, "edx": edx, "flags": flags,
                "original_eax": eax, "original_edx": edx, "original_flags": flags,
                "registers_match": True, "stack_delta": 8, "memory_unchanged": True}
    records = [{"event": "identity", "profile": "mw3-us-1-2-retail",
                "image_sha256": leaf.REVIEWED["image_sha256"], "entry_va": leaf.ENTRY,
                "replacement": "authored-x86-integer-helper-v1"},
               {"event": "selftest", "cases": 10400, "mismatches": 0,
                "memory_bytes_per_case": 4096, "seed": 13364},
               {"event": "comparison_controls", "cases": 7, "rejected": 7},
               *[call("hook_selftest_call", count) for count in range(1, 65)],
               {"event": "hook_thunk_selftest", "cases": 64, "mismatches": 0,
                "caller_memory_bytes_per_case": 1024, "fp_vector_preserved": True},
               {"event": "installed", "pid": 42, "entry_va": leaf.ENTRY,
                "hook_va": 0x10000000, "patched_bytes": 7, "on_disk_game_unchanged": True},
               *[call("game_call", count, n, base)
                 for count, (n, base) in enumerate(pairs, 1)]]
    trace_bytes = ("\n".join(json.dumps(record) for record in records) + "\n").encode()
    verification = {"status": "verified_game_calls", "game_sha256": leaf.REVIEWED["image_sha256"],
                    "game_trace_sha256": leaf.digest(trace_bytes), "pid": 42,
                    "verified_game_calls": len(pairs), "mismatches": 0}
    (folder / "game.jsonl").write_bytes(trace_bytes)
    (folder / "verification.json").write_text(json.dumps(verification), encoding="utf-8")
    return records, verification


class RecordedInputTests(unittest.TestCase):
    def setUp(self):
        reports = leaf.ROOT / "reports"
        reports.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="mw34-live-replay-", dir=reports)
        self.folder = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_first_verified_pair_can_have_a_different_allocation_address(self):
        first = (0, 123456789)
        authored_snapshot(self.folder, [first, (0, 330401912)])
        replay, evidence = leaf.live_input(self.folder)
        self.assertEqual(replay, first)
        self.assertEqual((evidence["call"], evidence["n"], evidence["base"]), (1, *first))
        self.assertEqual(evidence["recorded_fields_replayed"], ["stack_argument_n", "entry_ecx_base"])
        self.assertNotIn("Training", evidence["scope"])
        cases = leaf.corpus(0x3434, 0, replay)
        self.assertEqual((cases[-1][10], cases[-1][1]), first)

    def test_verification_identity_pid_and_count_changes_are_rejected(self):
        for field, value in (("status", "not_verified"), ("game_sha256", "0" * 64),
                             ("game_trace_sha256", "0" * 64), ("pid", 44),
                             ("verified_game_calls", 2)):
            _, verified = authored_snapshot(self.folder, [(0, 123456789)])
            verified[field] = value
            (self.folder / "verification.json").write_text(json.dumps(verified), encoding="utf-8")
            with self.subTest(field=field), self.assertRaises(ValueError):
                leaf.live_input(self.folder)

    def test_matching_trace_hash_does_not_admit_bad_original_identity_or_call(self):
        for row, field, value in ((0, "image_sha256", "0" * 64),
                                  (0, "entry_va", leaf.ENTRY + 1),
                                  (-1, "event", "hook_selftest_call"),
                                  (-1, "caller_va", 0x405174),
                                  (-1, "registers_match", False),
                                  (-1, "eax", 0)):
            records, verified = authored_snapshot(self.folder, [(0, 123456789)])
            records[row][field] = value
            data = ("\n".join(json.dumps(record) for record in records) + "\n").encode()
            (self.folder / "game.jsonl").write_bytes(data)
            verified["game_trace_sha256"] = leaf.digest(data)
            (self.folder / "verification.json").write_text(json.dumps(verified), encoding="utf-8")
            with self.subTest(field=field), self.assertRaises(ValueError):
                leaf.live_input(self.folder)

    def test_installation_and_selftests_cannot_supply_replay_input(self):
        authored_snapshot(self.folder, [])
        with self.assertRaisesRegex(ValueError, "no actual game_call"):
            leaf.live_input(self.folder)


class OracleTests(unittest.TestCase):
    def test_known_sub_results_and_flags(self):
        # Hand-computed zero, ordinary, unsigned borrow, and signed SUB overflow.
        self.assertEqual(leaf.oracle(0, 0, 0x202), (312, 0, 0x44))
        self.assertEqual(leaf.oracle(1, 1000, 0x202), (1500, 47, 0x10))
        self.assertEqual(leaf.oracle(0xFFFFFFFF, 0xFFFFFFFF, 0x202),
                         (123, 0xFFFFFFD1, 0x95))
        self.assertEqual(leaf.oracle(0x80000000, 0, 0x202),
                         (312, 0x80000000, 0x885))
        self.assertEqual(leaf.oracle(0x08000000, 0, 0x202),
                         (0xE0000138, 0x78000000, 0x804))

    def test_incoming_arithmetic_flags_overwritten_df_preserved(self):
        for incoming in range(128):
            bits = (*leaf.FLAG_BITS.values(), 0x400)
            flags = 0x202 | sum(bit for i, bit in enumerate(bits) if incoming >> i & 1)
            self.assertEqual(leaf.oracle(1, 1000, flags)[2], 0x10 | (flags & 0x400))

    def test_all_gpr_stack_return_and_entire_memory(self):
        case = request()
        actual = leaf.expected(case)
        state = leaf.STATE.unpack_from(actual)
        self.assertEqual(state, (1500, 1000, 47, 0x44444444,
                                 case[4] + 8, 0x66666666, 0x77777777,
                                 0x88888888, 0x10, leaf.SENTINEL, 0))
        memory = bytearray((i * 37 + 0x12345678) & 255 for i in range(4096))
        struct.pack_into("<3I", memory, 2049, leaf.SENTINEL, 1, 0xAABBCCDD)
        self.assertEqual(actual[leaf.STATE.size:], memory)
        self.assertEqual(len(actual), leaf.RESULT_SIZE)

    def test_permitted_stack_edges_and_unaligned_addresses(self):
        for offset in leaf.STACK_OFFSETS:
            self.assertEqual(leaf.STATE.unpack_from(leaf.expected(request(stack_offset=offset)))[4],
                             leaf.MEMORY_BASE + offset + 8)
        for offset in (0, 15, 4081, 4095):
            with self.assertRaisesRegex(ValueError, "mapped stack"):
                leaf.expected(request(stack_offset=offset))

    def test_oracle_and_state_reject_non_u32_or_unsafe_values(self):
        for bad in (-1, 0x100000000, True, None):
            for field in ("n", "base", "entry_flags"):
                with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                    values = {"n": 1, "base": 0, "entry_flags": 0x202}
                    values[field] = bad
                    leaf.oracle(**values)
        for index, value in ((8, 0x302), (8, 0), (9, leaf.ENTRY + 1)):
            case = list(request())
            case[index] = value
            with self.assertRaises(ValueError):
                leaf.expected(tuple(case))


class CorpusTests(unittest.TestCase):
    def test_seeded_corpus_directed_coverage_and_training_pair(self):
        cases = leaf.corpus(0x3434, 10000, (0, 330401912))
        self.assertEqual(cases, leaf.corpus(0x3434, 10000, (0, 330401912)))
        directed = len(cases) - 10001
        data = leaf.coverage(cases, directed)
        self.assertEqual(len(data["entry_flags_patterns"]), 128)
        self.assertEqual(data["compared_memory_bytes_per_case"], 4096)
        self.assertGreater(data["directed_address_zero_cases"], 0)
        self.assertGreater(data["directed_address_max_cases"], 0)
        self.assertGreater(data["unaligned_stack_cases"], 0)
        self.assertEqual((cases[-1][10], cases[-1][1]), (0, 330401912))
        # The logger does not provide the remaining GPR/entry flag/memory fields.
        self.assertEqual(cases[-1][9], leaf.ENTRY)
        self.assertNotEqual(cases[-1][0], 330402224)  # Synthetic entry EAX, not logged exit EAX.
        self.assertTrue({16, 17, 4080}.issubset(data["stack_offsets"]))

    def test_directed_48n_wrap_and_sign_neighbors(self):
        values = set(leaf.directed_n())
        self.assertTrue(set(range(256)).issubset(values))
        for period in range(1, 48):
            boundary = period * (1 << 32) // 48
            self.assertTrue({boundary - 1, boundary, boundary + 1}.issubset(values))
        for period in range(48):
            boundary = (period * (1 << 32) + (1 << 31)) // 48
            self.assertTrue({boundary - 1, boundary, boundary + 1}.issubset(values))

    def test_protocol_round_trip_and_malformed_records(self):
        cases = [request(), request(n=0, base=330401912, stack_offset=4080)]
        encoded = leaf.encode_corpus(cases)
        self.assertEqual(leaf.decode_corpus(encoded), cases)
        malformed = [b"MW34", encoded[:-1], encoded + b"x"]
        for index, value in ((1, 2), (2, 0), (3, leaf.REQUEST.size + 1), (4, 64)):
            header = list(leaf.HEADER.unpack_from(encoded))
            header[index] = value
            malformed.append(leaf.HEADER.pack(*header) + encoded[leaf.HEADER.size:])
        for value in malformed:
            with self.assertRaises(ValueError):
                leaf.decode_corpus(value)

    def test_result_headers_and_exact_extent_required(self):
        state = leaf.expected(request())
        for pointer_bits in (32, 64):
            data = leaf.HEADER.pack(b"MW34RES1", 1, 1, leaf.RESULT_SIZE, pointer_bits) + state
            self.assertEqual(leaf.parse_results(data, 1, pointer_bits), [state])
            for changed in (data[:-1], data + b"X", data[:8] + b"\x02\0\0\0" + data[12:]):
                with self.assertRaises(ValueError):
                    leaf.parse_results(changed, 1, pointer_bits)
            with self.assertRaises(ValueError):
                leaf.parse_results(data, 1, 64 if pointer_bits == 32 else 32)


class ComparatorEvidenceTests(unittest.TestCase):
    def test_adapter_layout_binds_profile_storage_ir_and_dll(self):
        layout, build = layout_evidence()
        leaf.validate_layout_record(layout, build)
        for key, changed in (("profile", "fixture"), ("entry_va", leaf.ENTRY + 1),
                             ("llvm_version", [21, 1, 7]), ("dll_sha256", "d" * 64),
                             ("guest_ir_sha256", "d" * 64), ("host_ir_sha256", "d" * 64),
                             ("guest_pointer_bits", 64), ("host_pointer_bits", 32),
                             ("guest_address_intrinsics_bits", 64), ("state_bytes", 3505),
                             ("all_struct_layouts_equal", False), ("indirect_calls", 1),
                             ("pointer_integer_conversions", 1), ("bridges", []),
                             ("flag_annotation_identities", []), ("undefined_flag_policy", None)):
            bad = copy.deepcopy(layout)
            bad[key] = changed
            with self.subTest(key=key), self.assertRaises(ValueError):
                leaf.validate_layout_record(bad, build)
        bad = copy.deepcopy(layout)
        bad["struct_layouts"]["struct.X86State"]["offsets"][2] += 1
        with self.assertRaises(ValueError):
            leaf.validate_layout_record(bad, build)

    def test_undefined_flag_policy_requires_exact_slots_and_zero_observers(self):
        layout, build = layout_evidence()
        for key, changed in (("policy", "allow-undefined"), ("undefined_calls", 1),
                             ("replacement_value", 1), ("replacement_value", False),
                             ("flag_offsets", [2065, 2077]), ("observable_undefined_values", 1),
                             ("blocks", []), ("stores", []), ("overwrites", [])):
            bad = copy.deepcopy(layout)
            bad["undefined_flag_policy"][key] = changed
            with self.subTest(key=key), self.assertRaises(ValueError):
                leaf.validate_layout_record(bad, build)

    def test_overwrite_evidence_rejects_reordered_unmatched_or_aliased_stores(self):
        layout, build = layout_evidence()
        for collection, key, changed in (("stores", "offset", 2065),
                                         ("stores", "origins", []),
                                         ("overwrites", "origins", ["%other"]),
                                         ("overwrites", "store_instruction", 3),
                                         ("overwrites", "overwrite_instruction", 4),
                                         ("overwrites", "block", "unknown")):
            bad = copy.deepcopy(layout)
            bad["undefined_flag_policy"][collection][0][key] = changed
            with self.subTest(key=key), self.assertRaises(ValueError):
                leaf.validate_layout_record(bad, build)

    def test_every_state_field_and_mapped_edges_corruption_detected(self):
        controls = leaf.comparator_controls(leaf.expected(request()))
        self.assertEqual([item["name"] for item in controls], list(leaf.COMPARATOR_CHECKS))
        self.assertEqual(len(controls), 20)
        self.assertTrue(all(item["outcome"] == "rejected" for item in controls))

    def test_oracle_comparator_rejects_mutated_outputs_and_counts(self):
        case = request()
        original = leaf.expected(case)
        leaf.validate_records([original], [case], "test")
        for offset in (*range(0, leaf.STATE.size, 4), leaf.STATE.size, leaf.RESULT_SIZE - 1):
            changed = bytearray(original)
            changed[offset] ^= 1
            with self.assertRaises(ValueError):
                leaf.validate_records([bytes(changed)], [case], "test")
        for records in ([], [original, original], [original[:-1]]):
            with self.assertRaises(ValueError):
                leaf.validate_records(records, [case], "test")

    def test_control_verifier_requires_all_unique_rejections(self):
        self.assertEqual(verify.validate_controls(valid_controls()), 49)
        for group in valid_controls():
            changed = valid_controls()
            changed[group].pop()
            with self.assertRaises(ValueError):
                verify.validate_controls(changed)
            changed = valid_controls()
            changed[group][0]["outcome"] = "passed"
            with self.assertRaises(ValueError):
                verify.validate_controls(changed)
        changed = valid_controls()
        changed["worker_negative_controls"][-1] = changed["worker_negative_controls"][0]
        with self.assertRaises(ValueError):
            verify.validate_controls(changed)

    def test_provenance_binds_both_native_workers_and_reviewed_slice(self):
        reports = leaf.ROOT / "reports"
        reports.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="mw34-provenance-", dir=reports) as temporary:
            paths = [Path(temporary) / name for name in ("reference", "O0", "O2")]
            for i, path in enumerate(paths):
                path.write_bytes(f"authored identity test artifact {i}".encode())
            build = {"schema_version": 1, "llvm_version": "21.1.8",
                     "remill_commit": "0e324aee8c67a63ec759ef379dcfafa0b3cb1448",
                     "source_digest": leaf.source_digest(leaf.ROOT),
                     "slice_sha256": leaf.REVIEWED["slice_sha256"],
                     "reference_sha256": leaf.digest(paths[0].read_bytes()),
                     "native_O0_sha256": leaf.digest(paths[1].read_bytes()),
                     "native_O2_sha256": leaf.digest(paths[2].read_bytes())}
            leaf.validate_build(build, paths[0], paths[1:])
            for key in build:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    changed = copy.deepcopy(build)
                    changed[key] = "changed"
                    leaf.validate_build(changed, paths[0], paths[1:])
            with self.assertRaises(ValueError):
                leaf.validate_build(build, paths[0], [paths[1], paths[1]])


if __name__ == "__main__":
    unittest.main()
