#!/usr/bin/env python3
"""Compare one admitted MW3 x86 leaf with its Remill-generated native workers.

This executes an isolated 22-byte function, never the game's PE entry point.
The Python specification is only an oracle for measuring the original/lifted
workers. It is not the implementation being claimed as recompilation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

from compare_fixture import (HEADER, REQUEST, STATE, MEMORY_BASE, MEMORY_SIZE,
                             RESULT_SIZE, SENTINEL, WorkerStartError, digest,
                             difference, parse_results, run_worker, source_digest)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/analysis"))
from extract_mw3_leaf import CONTRACT, REVIEWED, extract, private_directory

ENTRY = 0x409ED0
U32 = 0xFFFFFFFF
ARITHMETIC_MASK = 0x8D5
FLAG_MASK = ARITHMETIC_MASK | 0x400
LIVE_SNAPSHOT = ROOT / "reports/mw3-in-game/20261007-060648-615224-95ac7622/verified-snapshot"
FLAG_BITS = {"CF": 1, "PF": 4, "AF": 16, "ZF": 64, "SF": 128, "OF": 2048}
STACK_OFFSETS = (16, 17, 18, 19, 31, 32, 511, 512, 1023, *range(2048, 2064),
                 *range(4065, 4081))
COMPARATOR_CHECKS = (*("register_" + name for name in
                       ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi")),
                     *("flag_" + name for name in (*FLAG_BITS, "DF")),
                     "return_eip", "worker_status", "memory_first", "memory_middle",
                     "memory_last")
ADMISSION_CHECKS = ("modified_game_image", "modified_slice_in_image",
                    "changed_contract_game_sha", "changed_contract_slice_sha",
                    "changed_contract_entry_va")
REQUEST_CHECKS = ("truncated_header", "truncated_request", "trailing_input",
                  "bad_header", "bad_entry", "unsafe_flags", "unmapped_stack",
                  "changed_slice")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def u32(value: int, label: str) -> int:
    require(type(value) is int and 0 <= value <= U32, f"Invalid {label}")
    return value


def oracle(n: int, base: int, entry_flags: int) -> tuple[int, int, int]:
    """Reviewed LEA/SHL/SUB result; only the final SUB defines these six flags."""
    u32(n, "n")
    u32(base, "base")
    u32(entry_flags, "entry_flags")
    minuend = (48 * n) & U32
    result = (minuend - n) & U32
    flags = entry_flags & 0x400
    flags |= int(minuend < n)
    flags |= int((result & 255).bit_count() % 2 == 0) << 2
    flags |= int(bool((minuend ^ n ^ result) & 16)) << 4
    flags |= int(result == 0) << 6
    flags |= int(bool(result & 0x80000000)) << 7
    flags |= int(bool((minuend ^ n) & (minuend ^ result) & 0x80000000)) << 11
    return (base + 188 * n + 312) & U32, result, flags


def directed_n() -> tuple[int, ...]:
    # Include all possible low-byte SUB results, ordinary integer edges, every
    # 48*n wrap, and every sign crossing of the wrapped minuend. +/-2 neighbors
    # straddle boundaries even when a division is not exact.
    values = set(range(256))
    values.update((0x7FFFFFFE, 0x7FFFFFFF, 0x80000000, 0x80000001,
                   0xFFFFFFFE, 0xFFFFFFFF))
    for bit in range(32):
        values.update(((1 << bit) + delta) & U32 for delta in range(-2, 3))
    for period in range(1, 48):
        boundary = (period * (1 << 32)) // 48
        values.update((boundary + delta) & U32 for delta in range(-2, 3))
    for period in range(48):
        boundary = (period * (1 << 32) + (1 << 31)) // 48
        values.update((boundary + delta) & U32 for delta in range(-2, 3))
    return tuple(sorted(values))


def corpus(seed: int, random_count: int,
           live_input: tuple[int, int] | None = None) -> list[tuple[int, ...]]:
    require(type(random_count) is int and 0 <= random_count <= 80000,
            "Random case count out of bounds")
    rng = random.Random(seed)
    pairs = []
    for n in directed_n():
        # Exact neighbors of the final address wrap, alongside fixed base
        # boundaries. The base is an opaque u32 here; this leaf never dereferences it.
        wrap = -(188 * n + 312) & U32
        bases = sorted({0, 1, 0x7FFFFFFF, 0x80000000, U32,
                        (wrap - 1) & U32, wrap, (wrap + 1) & U32})
        pairs.extend((n, base) for base in bases)
    pairs.extend((rng.getrandbits(32), rng.getrandbits(32))
                 for _ in range(random_count))
    if live_input is not None:
        n, base = live_input
        pairs.append((u32(n, "live n"), u32(base, "live base")))
    cases = []
    bits = (*FLAG_BITS.values(), 0x400)
    for index, (n, base) in enumerate(pairs):
        registers = [rng.getrandbits(32) for _ in range(8)]
        registers[1] = base
        registers[4] = MEMORY_BASE + STACK_OFFSETS[index % len(STACK_OFFSETS)]
        # Every combination of the six arithmetic flags and DF is exercised;
        # the function must replace arithmetic flags and preserve DF.
        flags = 0x202 | sum(bit for i, bit in enumerate(bits) if index >> i & 1)
        cases.append((*registers, flags, ENTRY, n, rng.getrandbits(32),
                      rng.getrandbits(32)))
    require(0 < len(cases) <= 100000, "Total case count out of protocol bounds")
    return cases


def expected(case: tuple[int, ...]) -> bytes:
    require(len(case) == 13, "Invalid request field count")
    for index, value in enumerate(case):
        u32(value, f"request[{index}]")
    registers = list(case[:8])
    flags, eip, n, unused, memory_seed = case[8:]
    require(eip == ENTRY and flags & 0x202 == 0x202 and flags & ~(FLAG_MASK | 0x202) == 0,
            "Invalid entry address or unsafe flags")
    offset = registers[4] - MEMORY_BASE
    require(16 <= offset <= MEMORY_SIZE - 16, "Invalid mapped stack")
    registers[0], registers[2], flags = oracle(n, registers[1], flags)
    memory = bytearray((i * 37 + memory_seed) & 255 for i in range(MEMORY_SIZE))
    struct.pack_into("<3I", memory, offset, SENTINEL, n, unused)
    registers[4] += 8  # RET 4 consumes the return address and one argument.
    return STATE.pack(*registers, flags, SENTINEL, 0) + memory


def encode_corpus(cases: list[tuple[int, ...]]) -> bytes:
    require(0 < len(cases) <= 100000, "Invalid corpus count")
    return HEADER.pack(b"MW34REQ1", 1, len(cases), REQUEST.size, 32) + b"".join(
        REQUEST.pack(*case) for case in cases)


def decode_corpus(data: bytes) -> list[tuple[int, ...]]:
    require(len(data) >= HEADER.size, "Truncated corpus header")
    magic, version, count, size, bits = HEADER.unpack_from(data)
    require(magic == b"MW34REQ1" and version == 1 and 0 < count <= 100000 and
            size == REQUEST.size and bits == 32, "Invalid corpus header")
    require(len(data) == HEADER.size + count * REQUEST.size,
            "Truncated or trailing corpus bytes")
    cases = [REQUEST.unpack_from(data, HEADER.size + index * REQUEST.size)
             for index in range(count)]
    for case in cases:
        expected(case)
    return cases


def validate_records(records: list[bytes], cases: list[tuple[int, ...]], role: str) -> None:
    require(len(records) == len(cases), f"{role}: result count differs")
    for index, (actual, case) in enumerate(zip(records, cases, strict=True)):
        require(len(actual) == RESULT_SIZE, f"{role}: truncated result record")
        delta = difference(actual, expected(case))
        if delta:
            raise ValueError(json.dumps({"role": role, "case": index,
                                         "input": case, "difference": delta}))


def comparator_controls(record: bytes) -> list[dict]:
    controls = []
    changes = [("register_" + name, index * 4, 1) for index, name in enumerate(
        ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"))]
    changes += [("flag_" + name, 32 + (bit.bit_length() - 1) // 8,
                 1 << ((bit.bit_length() - 1) % 8))
                for name, bit in {**FLAG_BITS, "DF": 0x400}.items()]
    changes += [("return_eip", 36, 1), ("worker_status", 40, 1),
                ("memory_first", STATE.size, 1),
                ("memory_middle", STATE.size + MEMORY_SIZE // 2, 1),
                ("memory_last", RESULT_SIZE - 1, 1)]
    for name, offset, mask in changes:
        corrupted = bytearray(record)
        corrupted[offset] ^= mask
        delta = difference(bytes(corrupted), record)
        require(delta is not None, f"Comparator missed {name}")
        controls.append({"name": name, "outcome": "rejected", "difference": delta})
    return controls


def coverage(cases: list[tuple[int, ...]], directed_count: int) -> dict:
    outputs = [oracle(case[10], case[1], case[8]) for case in cases]
    flags = {name: {"set": sum(bool(out[2] & bit) for out in outputs),
                    "clear": sum(not out[2] & bit for out in outputs)}
             for name, bit in {**FLAG_BITS, "DF": 0x400}.items()}
    require(all(item["set"] > 0 and item["clear"] > 0 for item in flags.values()),
            "Missing an output flag outcome")
    entry_patterns = sorted({case[8] & FLAG_MASK for case in cases})
    require(len(entry_patterns) == 128, "Missing entry flags/DF combinations")
    return {"flag_outcomes": flags, "entry_flags_patterns": entry_patterns,
            "directed_n_values": len(directed_n()),
            "stack_offsets": sorted({case[4] - MEMORY_BASE for case in cases}),
            "unaligned_stack_cases": sum(case[4] % 4 != 0 for case in cases),
            "wrapped_48n_cases": sum(48 * case[10] > U32 for case in cases),
            "address_wrap_cases": sum(case[1] + 188 * case[10] + 312 > U32 for case in cases),
            "directed_address_zero_cases": sum(out[0] == 0 for out in outputs[:directed_count]),
            "directed_address_max_cases": sum(out[0] == U32 for out in outputs[:directed_count]),
            "compared_memory_bytes_per_case": MEMORY_SIZE,
            "callee_stack_cleanup_bytes": 4, "return_stack_delta_bytes": 8,
            "compared_gpr_count": 8, "return_eip": hex(SENTINEL)}


def live_input(snapshot: Path) -> tuple[tuple[int, int], dict]:
    """Admit recorded inputs while making the missing entry state explicit."""
    trace_file, verified_file = snapshot / "game.jsonl", snapshot / "verification.json"
    trace_bytes = trace_file.read_bytes()
    verified_bytes = verified_file.read_bytes()
    verified = json.loads(verified_bytes)
    require(verified.get("status") == "verified_game_calls" and
            verified.get("game_sha256") == REVIEWED["image_sha256"] and
            verified.get("game_trace_sha256") == digest(trace_bytes),
            "Live-input evidence identity differs")
    spec = importlib.util.spec_from_file_location("mw34_g2_trace_verifier",
                                                 ROOT / "tools/in-game-hook/verify_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pid, calls = module.check_log(module.load_records(trace_file), live=True)
    require(verified.get("pid") == pid and verified.get("verified_game_calls") == len(calls),
            "Live-input verification count/process differs")
    # A real allocation address may differ between sessions/machines. The
    # complete strict trace check above has already admitted every call; replay
    # the first verified input pair instead of requiring one historical address.
    record = calls[0]
    replay = (record["n"], record["base"])
    return replay, {"snapshot": str(snapshot.resolve()), "trace_sha256": digest(trace_bytes),
                    "verification_sha256": digest(verified_bytes), "call": record["call"],
                    "pid": pid, "caller_va": hex(record["caller_va"]),
                    "n": replay[0], "base": replay[1],
                    "recorded_fields_replayed": ["stack_argument_n", "entry_ecx_base"],
                    "other_entry_state": "authored harness state; not captured by the game logger",
                    "scope": "one real input pair, not a complete recorded CPU/memory replay"}


def source_hashes() -> dict[str, str]:
    files = set()
    extensions = {".py", ".hpp", ".cpp", ".asm", ".s", ".txt", ".ps1", ".json", ".patch"}
    for folder in ("tools/lifting", "tools/analysis", "runtime"):
        files.update(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and path.suffix in extensions)
    files.update((ROOT / "games/mw3/config/supported-binaries.json", CONTRACT,
                  ROOT / "tools/in-game-hook/verify_trace.py",
                  ROOT / "tests/test_mw3_comparison.py"))
    if (ROOT / "tests/test_host_adapter.py").exists():
        files.add(ROOT / "tests/test_host_adapter.py")
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(files)}


def admission_controls(game: Path, contract: Path, output: Path) -> list[dict]:
    """Reject changed image/contract before any original or native code execution."""
    controls = []
    with tempfile.TemporaryDirectory(prefix="admission-controls-", dir=output) as temporary:
        folder = Path(temporary)
        original = game.read_bytes()
        metadata = json.loads(contract.read_bytes())
        changed_image = bytearray(original)
        changed_image[-1] ^= 1
        changed_slice = bytearray(original)
        changed_slice[REVIEWED["file_offset"]] ^= 1
        mutations = [("modified_game_image", bytes(changed_image), metadata),
                     ("modified_slice_in_image", bytes(changed_slice), metadata),
                     ("changed_contract_game_sha", original,
                      {**metadata, "image_sha256": "0" * 64}),
                     ("changed_contract_slice_sha", original,
                      {**metadata, "slice_sha256": "0" * 64}),
                     ("changed_contract_entry_va", original,
                      {**metadata, "entry_va": ENTRY + 1})]
        for name, binary_bytes, changed in mutations:
            binary, details, destination = folder / "image.exe", folder / "contract.json", folder / name
            binary.write_bytes(binary_bytes)
            details.write_text(json.dumps(changed), encoding="utf-8")
            try:
                extract(binary, details, destination)
            except ValueError as error:
                require(not destination.exists(), f"Admission emitted artifacts for {name}")
                controls.append({"name": name, "outcome": "rejected", "reason": str(error)})
            else:
                raise ValueError(f"Admission accepted {name}")
    return controls


def worker_controls(workers: list[tuple[str, Path]], fixture: Path,
                    case: tuple[int, ...], output: Path) -> list[dict]:
    controls = []
    valid = encode_corpus([case])
    changed_entry, changed_flags, changed_stack = list(case), list(case), list(case)
    changed_entry[9] += 1
    changed_flags[8] |= 0x100
    changed_stack[4] = 0
    mutations = {"truncated_header": b"MW34", "truncated_request": valid[:-1],
                 "trailing_input": valid + b"X",
                 "bad_header": HEADER.pack(b"MW34REQ1", 2, 1, REQUEST.size, 32) + REQUEST.pack(*case),
                 "bad_entry": valid[:HEADER.size] + REQUEST.pack(*changed_entry),
                 "unsafe_flags": valid[:HEADER.size] + REQUEST.pack(*changed_flags),
                 "unmapped_stack": valid[:HEADER.size] + REQUEST.pack(*changed_stack)}
    code = fixture.read_bytes()
    with tempfile.TemporaryDirectory(prefix="worker-controls-", dir=output) as temporary:
        folder = Path(temporary)
        input_file, result_file, code_file = folder / "input.bin", folder / "result.bin", folder / "slice.bin"
        for role, worker in workers:
            code_file.write_bytes(code)
            for name, data in mutations.items():
                input_file.write_bytes(data)
                result = subprocess.run([str(worker.resolve()), str(input_file), str(result_file),
                                         str(code_file)], capture_output=True, text=True, timeout=10)
                require(result.returncode == 1 and bool(result.stderr.strip()),
                        f"{role}/{name}: missing explicit worker rejection")
                controls.append({"role": role, "name": name, "outcome": "rejected",
                                 "reason": result.stderr.strip()})
            input_file.write_bytes(valid)
            code_file.write_bytes(code[:-1] + bytes([code[-1] ^ 1]))
            result = subprocess.run([str(worker.resolve()), str(input_file), str(result_file), str(code_file)],
                                    capture_output=True, text=True, timeout=10)
            require(result.returncode == 1 and "identity" in result.stderr,
                    f"{role}: changed slice not explicitly rejected")
            controls.append({"role": role, "name": "changed_slice", "outcome": "rejected",
                             "reason": result.stderr.strip()})
    return controls


def validate_build(build: dict, reference: Path, lifted: list[Path]) -> None:
    require(build.get("schema_version") == 1 and build.get("llvm_version") == "21.1.8" and
            build.get("remill_commit") == "0e324aee8c67a63ec759ef379dcfafa0b3cb1448",
            "Build is missing pinned LLVM/Remill provenance")
    require(build.get("source_digest") == source_digest(ROOT),
            "Lifted build sources changed after compilation/provenance recording")
    require(build.get("slice_sha256", build.get("fixture_sha256")) == REVIEWED["slice_sha256"],
            "Build slice identity differs")
    require(build.get("reference_sha256") == digest(reference.read_bytes()),
            "Reference worker differs from build provenance")
    require(len(lifted) == 2, "G2 requires both O0 and O2 native workers")
    for level, worker in zip(("O0", "O2"), lifted, strict=True):
        require(build.get(f"native_{level}_sha256") == digest(worker.read_bytes()),
                f"{level} worker differs from build provenance")


def validate_layout_record(layout: dict, build: dict) -> None:
    """Require the adapter's bounded AF/OF overwrite proof and ABI evidence."""
    require(isinstance(layout, dict) and layout.get("version") == 1 and
            layout.get("profile") == "mw3-helper" and layout.get("entry_va") == ENTRY,
            "Wrong reviewed adapter profile/entry")
    require(layout.get("llvm_version") == [21, 1, 8] and
            layout.get("dll_sha256") == build.get("llvm_dll_sha256"),
            "Adapter LLVM identity differs from compilation provenance")
    require(layout.get("guest_pointer_bits") == 32 and layout.get("host_pointer_bits") == 64 and
            layout.get("guest_address_intrinsics_bits") == 32 and layout.get("state_bytes") == 3504 and
            layout.get("all_struct_layouts_equal") is True and
            layout.get("indirect_calls") == 0 and layout.get("pointer_integer_conversions") == 0,
            "Missing checked State/address/host ABI boundary")
    layouts = layout.get("struct_layouts", {})
    require(isinstance(layouts, dict) and
            layouts.get("struct.State", {}).get("size") == 3504 and
            layouts.get("struct.State", {}).get("offsets") == [0] and
            layouts.get("struct.X86State", {}).get("offsets", [])[2:3] == [2064] and
            layouts.get("struct.ArithFlags", {}).get("offsets") == list(range(16)),
            "Reviewed arithmetic flag storage differs")
    artifacts = build.get("artifacts", {})
    require(isinstance(artifacts, dict) and
            layout.get("guest_ir_sha256") == artifacts.get("sub_00409ed0-guest.ll") and
            layout.get("host_ir_sha256") == artifacts.get("sub_00409ed0-host.ll") and
            all(type(layout.get(name)) is str and len(layout[name]) == 64
                for name in ("dll_sha256", "guest_ir_sha256", "host_ir_sha256")),
            "Adapter IR identities differ from compilation artifacts")
    annotations = layout.get("flag_annotation_identities", [])
    expected_annotations = {"__remill_flag_computation_" + name
                            for name in ("carry", "overflow", "sign", "zero")}
    require(layout.get("bridges") == ["__remill_function_return", "__remill_read_memory_32"] and
            isinstance(annotations, list) and expected_annotations <= set(annotations) and
            set(annotations) <= expected_annotations | {"__remill_compare_sle", "__remill_compare_uge"},
            "Reviewed helper bridges/flag annotations missing")
    policy = layout.get("undefined_flag_policy")
    require(isinstance(policy, dict) and
            policy.get("policy") == "straight-line-ssa-overwritten-af-of-v1" and
            type(policy.get("undefined_calls")) is int and policy["undefined_calls"] == 2 and
            type(policy.get("replacement_value")) is int and policy["replacement_value"] == 0 and
            policy.get("flag_offsets") == [2069, 2077] and
            type(policy.get("observable_undefined_values")) is int and
            policy["observable_undefined_values"] == 0,
            "Missing reviewed overwritten undefined-flag policy")
    blocks = policy.get("blocks")
    require(isinstance(blocks, list) and blocks and
            all(type(block) is str and bool(block) for block in blocks) and
            len(set(blocks)) == len(blocks), "Missing straight-line proof block chain")
    stores, overwrites = policy.get("stores"), policy.get("overwrites")
    require(isinstance(stores, list) and isinstance(overwrites, list) and
            len(stores) == len(overwrites) == 2 and
            all(isinstance(entry, dict) for entry in stores + overwrites),
            "Missing two undefined-flag stores/overwrites")
    require({entry.get("offset") for entry in stores} == {2069, 2077} and
            {entry.get("offset") for entry in overwrites} == {2069, 2077},
            "Undefined stores escape the two reviewed flag slots")
    origins = set()
    for store in stores:
        overwrite = next(entry for entry in overwrites if entry["offset"] == store["offset"])
        active = store.get("origins")
        require(isinstance(active, list) and len(active) == 1 and type(active[0]) is str and
                active[0].startswith("%") and len(active[0]) > 1,
                "Missing exact undefined SSA origin")
        require(overwrite.get("origins") == active and
                type(store.get("store_instruction")) is int and store["store_instruction"] >= 0 and
                overwrite.get("store_instruction") == store["store_instruction"] and
                type(overwrite.get("overwrite_instruction")) is int and
                overwrite["overwrite_instruction"] > store["store_instruction"] and
                store.get("block") in blocks and overwrite.get("block") in blocks and
                blocks.index(overwrite["block"]) >= blocks.index(store["block"]),
                "Undefined flag is not overwritten after its matched store")
        origins.update(active)
    require(len(origins) == 2, "Undefined flags do not have two distinct SSA origins")


def validate_generated_layout(build: dict, directory: Path) -> dict:
    artifacts = build.get("artifacts", {})
    for name in ("layout.json", "sub_00409ed0-guest.ll", "sub_00409ed0-host.ll"):
        require(digest((directory / name).read_bytes()) == artifacts.get(name),
                f"Generated adapter artifact differs: {name}")
    layout = json.loads((directory / "layout.json").read_bytes())
    validate_layout_record(layout, build)
    return layout


def compare(args) -> dict:
    # Extraction's pinned contract, entire PE identity, mapping and slice hash
    # must all pass before a worker can execute any game-derived instruction.
    admitted = extract(args.game, args.contract, args.output_dir / "admitted")
    fixture = args.output_dir / "admitted/sub_00409ed0.bin"
    replay, recorded_input = live_input(args.live_snapshot)
    build_bytes = args.metadata.read_bytes()
    build = json.loads(build_bytes)
    validate_build(build, args.reference, args.lifted)
    layout = validate_generated_layout(build, args.metadata.parent)
    cases = corpus(args.seed, args.random_cases, replay)
    directed_count = len(cases) - args.random_cases - 1
    encoded = encode_corpus(cases)
    corpus_file = args.output_dir / "corpus.bin"
    corpus_file.write_bytes(encoded)
    report = {"schema_version": 1, "gate": "G2", "outcome": "failed",
              "function": "sub_00409ED0", "scope": "isolated original x86 leaf vs Remill-generated native x64 O0/O2",
              "not_proven": "native x64 whole-game launch or extended gameplay stability",
              "admission": admitted, "slice_sha256": digest(fixture.read_bytes()),
              "metadata_path": str(args.metadata.resolve()), "metadata_sha256": digest(build_bytes),
              "build_provenance": build, "seed": args.seed, "directed_cases": directed_count,
              "adapter_profile": layout["profile"],
              "undefined_flag_policy": layout["undefined_flag_policy"],
              "random_cases": args.random_cases, "recorded_input_cases": 1,
              "total_cases": len(cases), "corpus_sha256": digest(encoded),
              "recorded_input": {**recorded_input, "corpus_case_index": len(cases) - 1},
              "coverage": coverage(cases, directed_count), "source_hashes": source_hashes(),
              "source_digest": source_digest(ROOT),
              "python_version": sys.version.split()[0], "lifted_runs": []}
    report["admission_negative_controls"] = admission_controls(args.game, args.contract, args.output_dir)
    original_file = args.output_dir / "reference.bin"
    report["reference_run"] = run_worker(args.reference, corpus_file, original_file, fixture, args.timeout)
    original = parse_results(original_file.read_bytes(), len(cases), 32)
    validate_records(original, cases, "original_x86_independent_specification")
    report["reference_self_test"] = "passed independent result/all-GPR/flags/stack/memory specification"
    report["comparator_negative_controls"] = comparator_controls(original[0])
    for index, (level, worker) in enumerate(zip(("O0", "O2"), args.lifted, strict=True)):
        result_file = args.output_dir / f"lifted-{index}.bin"
        run = run_worker(worker, corpus_file, result_file, fixture, args.timeout)
        native = parse_results(result_file.read_bytes(), len(cases), 64)
        validate_records(native, cases, "native_" + level)
        require(native == original, f"{level}: native/original differential mismatch")
        run.update({"optimization": level, "differential_result": "zero mismatches"})
        report["lifted_runs"].append(run)
    workers = [("reference", args.reference), ("O0", args.lifted[0]), ("O2", args.lifted[1])]
    report["worker_negative_controls"] = worker_controls(workers, fixture, cases[0], args.output_dir)
    report["outcome"] = "mw3_leaf_lift_passed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / "MW3/Mech3.exe")
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--lifted", type=Path, action="append", required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--live-snapshot", type=Path, default=LIVE_SNAPSHOT)
    parser.add_argument("--random-cases", type=int, default=10000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x3434)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if not 0 <= args.random_cases <= 80000 or not 1 <= args.timeout <= 60:
        parser.error("Case count or timeout out of bounds")
    report = {"schema_version": 1, "gate": "G2", "outcome": "failed"}
    destination = None
    try:
        args.output_dir = private_directory(args.output_dir)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        destination = args.output_dir / "report.json"
        report = compare(args)
        print(f"G2 leaf comparison passed: {report['total_cases']} cases, native O0/O2, zero mismatches")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        if isinstance(error, WorkerStartError):
            report["worker_start_failure"] = {"command": error.command, "winerror": error.winerror}
            if error.winerror == 4551:
                report["outcome"] = "execution_blocked"
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if destination is not None:
            destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
