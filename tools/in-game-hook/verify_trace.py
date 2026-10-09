"""Verify a hash-bound, authored x86 helper run; self-tests alone never pass."""

import argparse
import hashlib
import json
from pathlib import Path

IMAGE_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
ENTRY = 0x409ED0
CALLER = 0x405173
ARITHMETIC_MASK = 0x8D5
OBSERVED_MASK = 0xCD5


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def u32(record, key):
    value = record.get(key)
    require(type(value) is int and 0 <= value <= 0xFFFFFFFF, f"Invalid {key}")
    return value


def oracle(n, base):
    t = (n * 48) & 0xFFFFFFFF
    r = (t - n) & 0xFFFFFFFF
    flags = int(t < n)
    flags |= 4 if (r & 255).bit_count() % 2 == 0 else 0
    flags |= 16 if (t ^ n ^ r) & 16 else 0
    flags |= 64 if r == 0 else 0
    flags |= 128 if r & 0x80000000 else 0
    flags |= 0x800 if (t ^ n) & (t ^ r) & 0x80000000 else 0
    return (base + n * 188 + 312) & 0xFFFFFFFF, r, flags


def check_call(record):
    eax, edx, flags = oracle(u32(record, "n"), u32(record, "base"))
    for prefix in ("", "original_"):
        require(u32(record, prefix + "eax") == eax, "EAX differs from independent oracle")
        require(u32(record, prefix + "edx") == edx, "EDX differs from independent oracle")
        observed = u32(record, prefix + "flags")
        require(not observed & ~OBSERVED_MASK, "Unexpected logged flag bits")
        require(observed & ARITHMETIC_MASK == flags, "Flags differ from independent oracle")
    require(record["flags"] == record["original_flags"], "Original/replacement DF differs")
    require(record.get("registers_match") is True, "Register comparison failed")
    require(type(record.get("stack_delta")) is int and record["stack_delta"] == 8,
            "Wrong return stack delta")
    # This field describes the isolated reference payload, not all game memory.
    require(record.get("memory_unchanged") is True, "Shadow payload comparison failed")
    require(u32(record, "pid") > 0 and u32(record, "tid") > 0, "Missing process/thread identity")


def load_records(path):
    records = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvidenceError(f"{path}:{number}: incomplete or invalid JSON") from error
        require(isinstance(record, dict), "Log record must be an object")
        records.append(record)
    return records


def check_log(records, live):
    # These events must occur once, in this order; no silent unknown/fatal events.
    stages = ["identity", "selftest", "comparison_controls"]
    stages += ["hook_selftest_call"] * 64 + ["hook_thunk_selftest"]
    if live:
        stages += ["installed"]
    require(len(records) >= len(stages), "Required initialization evidence missing")
    require([r.get("event") for r in records[:len(stages)]] == stages,
            "Initialization event sequence differs")
    identity = records[0]
    require(identity.get("profile") == "mw3-us-1-2-retail" and
            identity.get("image_sha256") == IMAGE_SHA and identity.get("entry_va") == ENTRY and
            identity.get("replacement") == "authored-x86-integer-helper-v1", "Wrong helper identity")
    require(records[1] == {"event": "selftest", "cases": 10400, "mismatches": 0,
                           "memory_bytes_per_case": 4096, "seed": 13364}, "Math self-test gate failed")
    require(records[2] == {"event": "comparison_controls", "cases": 7, "rejected": 7},
            "Comparator corruption controls failed")
    test_pid = None
    for count, record in enumerate(records[3:67], 1):
        require(type(record.get("call")) is int and record["call"] == count, "Self-test counter differs")
        check_call(record)
        if test_pid is None:
            test_pid = record["pid"]
        require(record["pid"] == test_pid, "Self-test process differs")
    require(records[67] == {"event": "hook_thunk_selftest", "cases": 64, "mismatches": 0,
                            "caller_memory_bytes_per_case": 1024, "fp_vector_preserved": True},
            "Actual entry/return thunk gate failed")
    if not live:
        require(len(records) == len(stages), "Unexpected offline self-test events")
        return None, []
    installed = records[68]
    require(u32(installed, "pid") == test_pid and installed.get("entry_va") == ENTRY and
            installed.get("patched_bytes") == 7 and installed.get("on_disk_game_unchanged") is True,
            "Hook installation evidence differs")
    require(u32(installed, "hook_va") > 0, "Missing hook address")
    game_calls = records[len(stages):]
    require(game_calls, "Pending: no actual game_call records; installation and self-tests alone do not pass")
    for count, record in enumerate(game_calls, 1):
        require(record.get("event") == "game_call", "Unexpected or fatal event after installation")
        require(type(record.get("call")) is int and record["call"] == count, "Game call counter differs")
        require(record.get("pid") == test_pid, "Game call process differs from installed process")
        require(u32(record, "caller_va") == CALLER, "Game call is not from the reviewed original caller")
        check_call(record)
    return installed["pid"], game_calls


def verify(run, game, hook, launcher, source_dir):
    run = Path(run)
    record = json.loads((run / "build.json").read_text(encoding="utf-8-sig"))
    require(record.get("schema_version") == 1, "Unsupported build record")
    for key, path in (("game_sha256", game), ("hook_sha256", hook), ("launcher_sha256", launcher)):
        require(record.get(key) == digest(path), f"Current {key} differs from recorded build")
    require(record["game_sha256"] == IMAGE_SHA, "Unadmitted game image")
    sources = record.get("source_hashes")
    require(isinstance(sources, dict) and sources, "Missing source identities")
    for name, expected in sources.items():
        require(Path(name).name == name and name not in (".", ".."), "Unsafe source name")
        require(digest(Path(source_dir) / name) == expected, f"Recorded source changed: {name}")
    check_log(load_records(run / "selftest.jsonl"), live=False)
    pid, calls = check_log(load_records(run / "game.jsonl"), live=True)
    return {"status": "verified_game_calls", "scope": "authored x86 helper in original x86 MW3",
            "pid": pid, "function_va": hex(ENTRY), "caller_va": hex(CALLER),
            "verified_game_calls": len(calls), "mismatches": 0,
            "distinct_inputs": len({(r["n"], r["base"]) for r in calls}),
            "game_sha256": record["game_sha256"], "hook_sha256": record["hook_sha256"],
            "game_trace_sha256": digest(run / "game.jsonl"),
            "memory_scope": "4096-byte isolated original-reference payload; thunk tests cover 1024 caller bytes",
            "gameplay_observation": "must be confirmed separately; traces alone do not prove playable Training",
            "native_x64_G2": "not tested by this experiment"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--game", type=Path, default=Path("MW3/Mech3.exe"))
    parser.add_argument("--hook", type=Path, default=Path("build/in-game-hook/Release/mw34_helper_hook.dll"))
    parser.add_argument("--launcher", type=Path, default=Path("build/in-game-hook/Release/mw34_hook_launcher.exe"))
    parser.add_argument("--sources", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    try:
        result = verify(args.run, args.game, args.hook, args.launcher, args.sources)
    except (EvidenceError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "not_verified", "reason": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
