"""Independent transport corpus for the additive M4 capture pipeline.

No original/native/game execution. The only spawned test programs are tiny,
independently authored Python stage fixtures in this review's fresh directory.
"""
import hashlib
import importlib.util
import json
import ntpath
import os
import struct
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
CHECKS = []
PINS = {}
ATTEMPT = None


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    path = Path(path).resolve()
    result = sha(path.read_bytes())
    name = ntpath.normcase(ntpath.normpath(str(path)))
    assert name not in PINS or PINS[name] == result, name
    PINS[name] = result
    return result


def need(value, name):
    assert value, name
    CHECKS.append({"name": name, "passed": True})


def load(name, filename):
    path = ROOT / "tools/m4-pipeline" / filename
    pin(path)
    if ATTEMPT is not None:
        (ATTEMPT / (filename + ".candidate")).write_bytes(path.read_bytes())
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def archive(index, payload, magic=b"MW34CAP1", raw_index=None,
            index_length=None, index_digest=None):
    body = canonical(index) if raw_index is None else raw_index
    return magic + struct.pack("<Q", len(body) if index_length is None else index_length) + (
        bytes.fromhex(sha(body)) if index_digest is None else index_digest) + body + payload


def decode(data):
    need(data[:8] == b"MW34CAP1", "Independent header magic")
    length, = struct.unpack_from("<Q", data, 8)
    raw = data[48:48+length]
    need(len(raw) == length and sha(raw) == data[16:48].hex(),
         "Independent index extent and digest")
    index = json.loads(raw)
    need(raw == canonical(index), "Independently canonical index encoding")
    payload = data[48+length:]
    return index, payload


def expect_refusal(function, name):
    try:
        function()
    except Exception as error:
        CHECKS.append({"name": name, "passed": True,
                       "refusal": type(error).__name__, "reason": str(error)[:180]})
    else:
        raise AssertionError("Required refusal: " + name)


def bundle_tests(module, out):
    source = out / "synthetic-source"
    source.mkdir()
    expected = {"phase/state.bin": bytes(range(256))*3,
                "phase/fx.bin": bytes(range(255, -1, -1))*2,
                "phase/empty.bin": b"", "cafe\u0301-marker.txt": b"unused"}
    # Only the normalized NFC path is part of the successful source.
    expected.pop("cafe\u0301-marker.txt")
    expected["caf\u00e9-marker.txt"] = b"NFC UTF-8 path and binary \x00\xff"
    for name, value in expected.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        pin(path)
    first, second = out / "first.capture", out / "second.capture"
    receipt = module.pack_capture(source, first)
    module.pack_capture(source, second)
    data = first.read_bytes()
    need(data == second.read_bytes(), "Deterministic independent synthetic roundtrip")
    index, payload = decode(data)
    need(index["format"] == "mw34.capture.v1" and index["total_bytes"] == len(payload),
         "Independent format and complete payload extent")
    entries = index["files"]
    names = [v["path"] for v in entries]
    need(names == sorted(expected), "Complete sorted logical synthetic file names")
    offset = 0
    for record in entries:
        value = expected[record["path"]]
        need(record["offset"] == offset and record["size"] == len(value)
             and record["sha256"] == sha(value)
             and payload[offset:offset+len(value)] == value,
             "Independent exact synthetic record: " + record["path"])
        offset += len(value)
    with module.CaptureBundle(first, sha(data)) as reader:
        need(reader.names() == tuple(sorted(expected)), "Reader names exact complete corpus")
        for name, value in expected.items():
            need(reader.exists(name) and reader.read_bytes(name) == value,
                 "Reader exact bytes: " + name)
        need(not reader.exists("missing.bin"), "Missing canonical logical path absent")
        expect_refusal(lambda: reader.read_bytes("missing.bin"), "Missing member cannot return bytes")
        expect_refusal(lambda: reader.read_bytes("../phase/state.bin"), "Reader traversal query rejected")
        expect_refusal(lambda: first.open("r+b"), "Live reader excludes file write sharing")
        expect_refusal(lambda: os.replace(second, first), "Live reader excludes replacement sharing")
    expect_refusal(lambda: module.CaptureBundle(first, "0"*64), "Wrong pinned whole-file hash")
    frozen = first.read_bytes()
    expect_refusal(lambda: module.pack_capture(source, first), "Existing bundle target never overwritten")
    need(first.read_bytes() == frozen, "Existing final bytes retained on refused publication")
    expect_refusal(lambda: module.pack_capture(source, source / "inside.capture"),
                   "Output cannot join its own capture input tree")

    # Refresh each attack's whole-file pin, otherwise the outer SHA would hide a
    # broken inner parser. Every inner index SHA is genuine unless under test.
    attacks = []
    clone = lambda: json.loads(json.dumps(index))
    def altered(name, edit, changed_payload=None):
        value = clone(); edit(value)
        attacks.append((name, archive(value, payload if changed_payload is None else changed_payload)))
    attacks.extend([
        ("wrong magic", archive(index, payload, magic=b"MW34BAD1")),
        ("truncated fixed header", data[:47]),
        ("declared enormous index", archive(index, payload, index_length=(1<<64)-1)),
        ("declared index above64MiB", archive(index, payload, index_length=64*1024*1024+1)),
        ("wrong embedded index digest", archive(index, payload, index_digest=b"\0"*32)),
        ("truncated index", data[:48+len(canonical(index))-1]),
        ("truncated payload", data[:-1]),
        ("trailing payload byte", data+b"!"),
        ("noncanonical JSON spaces", archive(index, payload, raw_index=json.dumps(index).encode())),
        ("invalid UTF-8 index", archive(index, payload, raw_index=b"\xff")),
        ("duplicate JSON format member", archive(index, payload,
             raw_index=b'{"format":"mw34.capture.v1",'+canonical(index)[1:])),
    ])
    altered("wrong format", lambda v: v.update(format="mw34.capture.v2"))
    altered("unknown index field", lambda v: v.update(extra=1))
    altered("missing total", lambda v: v.pop("total_bytes"))
    altered("wrong total", lambda v: v.update(total_bytes=len(payload)+1))
    altered("boolean total", lambda v: v.update(total_bytes=True))
    altered("negative total", lambda v: v.update(total_bytes=-1))
    altered("oversized total", lambda v: v.update(total_bytes=2*1024**3+1))
    altered("files not list", lambda v: v.update(files={}))
    altered("unsorted entries", lambda v: v["files"].reverse())
    altered("unknown record field", lambda v: v["files"][0].update(extra=1))
    altered("missing record hash", lambda v: v["files"][0].pop("sha256"))
    altered("wrong record digest", lambda v: v["files"][-1].update(sha256="0"*64))
    altered("uppercase record digest", lambda v: v["files"][-1].update(sha256="A"*64))
    altered("short record digest", lambda v: v["files"][-1].update(sha256="a"*63))
    altered("nonhex record digest", lambda v: v["files"][-1].update(sha256="g"*64))
    altered("payload tampering", lambda v: None, bytes([payload[0]^1])+payload[1:])
    altered("negative record offset", lambda v: v["files"][0].update(offset=-1))
    altered("boolean record offset", lambda v: v["files"][0].update(offset=False))
    altered("record gap", lambda v: v["files"][-1].update(offset=v["files"][-1]["offset"]+1))
    altered("record overlap", lambda v: v["files"][-1].update(offset=0))
    altered("negative size", lambda v: v["files"][-1].update(size=-1))
    altered("boolean size", lambda v: v["files"][-1].update(size=True))
    altered("floating size", lambda v: v["files"][-1].update(size=1.0))
    altered("size above256MiB", lambda v: v["files"][-1].update(size=256*1024**2+1))
    altered("huge64bit size", lambda v: v["files"][-1].update(size=(1<<64)-1))
    altered("duplicate logical member", lambda v: v["files"].append(v["files"][-1].copy()))
    altered("casefold duplicate logical member", lambda v: v["files"].append(
        dict(v["files"][-1], path=v["files"][-1]["path"].upper())))
    paths = ("", ".", "..", "../x", "a/../x", "a/./x", "a//x", "a/", "/x",
             "C:/x", "C:x", "//host/share/x", "a\\x", "a:stream", "a/CON",
             "a/nul.txt", "a/PRN", "a/AUX", "a/COM1.txt", "a/LPT9",
             "a/COM\u00b9.txt", "a/LPT\u00b2", "a/file.", "a/file ", "a./x", "a /x",
             "a/\x00x", "a/\nx", "a/\x7fx", "a/\x85x", "cafe\u0301.txt")
    for path in paths:
        altered("invalid logical path " + repr(path), lambda v, p=path: v["files"][0].update(path=p))
    # Empty unique records are legitimate individually; the count still has a bound.
    count_index = {"format": "mw34.capture.v1", "total_bytes": 0,
                   "files": [{"path": f"p/{i:06}.bin", "offset": 0, "size": 0,
                              "sha256": sha(b"")} for i in range(200001)]}
    attacks.append(("count above200k", archive(count_index, b"")))
    for number, (name, attack) in enumerate(attacks):
        path = out / f"attack-{number:03}.capture"
        path.write_bytes(attack)
        expect_refusal(lambda p=path, a=attack: module.CaptureBundle(p, sha(a)), name)
        pin(path)
    race = out / "raced.capture"
    original_publish = module.publish_new_file
    def injected_publish(src, dest, *args, **kwargs):
        Path(dest).write_bytes(b"independent winning publisher")
        return original_publish(src, dest, *args, **kwargs)
    module.publish_new_file = injected_publish
    try:
        expect_refusal(lambda: module.pack_capture(source, race), "Concurrent final publisher wins without overwrite")
    finally:
        module.publish_new_file = original_publish
    need(race.read_bytes() == b"independent winning publisher", "Concurrent winner exact bytes retained")
    need(not list(out.glob("*.tmp")), "Failed atomic publication leaves no complete sibling temporary")
    original_scan = module._scan
    changed_source = source / "phase/state.bin"
    saved_source = changed_source.read_bytes()
    scans = 0
    def changing_scan(path):
        nonlocal scans
        values = original_scan(path)
        scans += 1
        if scans == 2:
            changed_source.write_bytes(bytes(v ^ 1 for v in saved_source))
        return values
    module._scan = changing_scan
    changed_target = out / "changed-source.capture"
    try:
        expect_refusal(lambda: module.pack_capture(source, changed_target),
                       "Same-size source mutation before publication is rehashed and refused")
    finally:
        module._scan = original_scan
        changed_source.write_bytes(saved_source)
    need(scans == 2 and not changed_target.exists() and not list(out.glob("*.tmp")),
         "Source-change refusal never publishes final or partial temporary")
    interrupted_target = out / "interrupted.capture"
    def interrupted_publish(*args, **kwargs):
        raise OSError("Independent publication interruption")
    module.publish_new_file = interrupted_publish
    try:
        expect_refusal(lambda: module.pack_capture(source, interrupted_target),
                       "Interrupted final publication cannot publish successful capture")
    finally:
        module.publish_new_file = original_publish
    need(not interrupted_target.exists() and not list(out.glob("*.tmp")),
         "Interrupted publication cleans owned temporary and publishes no final")
    pin(first); pin(second); pin(race)
    return {"synthetic_files": len(expected), "malformed_archives": len(attacks),
            "producer_receipt": receipt}


def frozen_roundtrips(module, out):
    schema = ROOT / "reports/m4-pipeline-review/capture-schema-r2/report.json"
    pin(schema)
    evidence = json.loads(schema.read_text())
    rows = []
    for number, row in enumerate(evidence["representative_rows"]):
        source = Path(row["row"])
        target = out / f"frozen-{number}.capture"
        receipt = module.pack_capture(source, target)
        with module.CaptureBundle(target, sha(target.read_bytes())) as reader:
            need(reader.names() == tuple(sorted(row["files"])),
                 "Exact complete frozen row inventory " + str(number))
            for name, item in row["files"].items():
                original = source / name
                value = original.read_bytes()
                need(len(value) == item["bytes"] and sha(value) == item["sha256"],
                     "Frozen source evidence retained " + str(number) + "/" + name)
                need(reader.read_bytes(name) == value,
                     "Exact frozen byte roundtrip " + str(number) + "/" + name)
                pin(original)
        pin(target)
        rows.append({"row": str(source), "control": row["control"],
                     "logical_files": row["file_count"], "receipt": receipt})
    return rows


def manifest_tests(module, out):
    directory = out / "manifests"
    directory.mkdir()
    dependency = directory / "dependency.bin"
    other = directory / "other.bin"
    dependency.write_bytes(b"A"*16)
    other.write_bytes(b"B"*16)
    normalized = lambda p: ntpath.normcase(ntpath.normpath(str(p)))
    a, b = directory / "a.json", directory / "b.json"
    a.write_text(json.dumps({"files": {str(dependency): sha(dependency.read_bytes())}}))
    alias = str(dependency).replace("\\", "/").upper()
    b.write_text(json.dumps({"files": {alias: sha(dependency.read_bytes()),
                                      str(other): sha(other.read_bytes())}}))
    merged = module.merge_manifests([a, b])
    expected = {normalized(dependency): sha(dependency.read_bytes()),
                normalized(other): sha(other.read_bytes())}
    need(merged == dict(sorted(expected.items())), "Normalized union retains all exact bindings once")
    stats = module.verify_manifest(merged)
    need(stats["passed"] and stats["unique_physical_dependencies"] == 2
         and not stats["metadata_only_cache_used"], "Complete unique physical rehash remains required")
    info = dependency.stat()
    dependency.write_bytes(b"C"*16)
    os.utime(dependency, ns=(info.st_atime_ns, info.st_mtime_ns))
    expect_refusal(lambda: module.verify_manifest(merged),
                   "Same size/mtime physical mutation cannot use a metadata-only cache")
    dependency.write_bytes(b"A"*16)
    need(module.verify_manifest(merged)["passed"], "Restored exact bytes regain physical closure")
    attacks = [
        ("normalized conflicting hash", {"files": {alias: "0"*64}}),
        ("empty files manifest", {"files": {}}),
        ("files list", {"files": []}),
        ("unknown manifest field", {"files": {}, "extra": 1}),
        ("missing files field", {}),
    ]
    for value in ("0"*63, "A"*64, "g"*64, True, None, 0):
        attacks.append(("invalid digest " + repr(value), {"files": {str(dependency): value}}))
    for name in ("relative.bin", "C:relative.bin", "\\relative.bin", "//host/share/x",
                 "C:/a:stream", "C:/a\0b"):
        attacks.append(("invalid absolute dependency " + repr(name), {"files": {name: "0"*64}}))
    for number, (name, value) in enumerate(attacks):
        path = directory / f"attack-{number}.json"
        path.write_text(json.dumps(value))
        # Conflicts are checked against the real binding; every other attack
        # must fail by itself, including the nonempty-union requirement.
        parents = [a, path] if number == 0 else [path]
        expect_refusal(lambda p=parents: module.merge_manifests(p), name)
        pin(path)
    duplicate = directory / "duplicate.json"
    key = json.dumps(str(dependency))
    duplicate.write_text('{"files":{'+key+':"'+sha(dependency.read_bytes())+'",'+key+':"'+'0'*64+'"}}')
    expect_refusal(lambda: module.merge_manifests([duplicate]), "Duplicate JSON dependency key refused")
    pin(a); pin(b); pin(duplicate); pin(dependency); pin(other)
    return {"unique_bindings": len(merged), "malformed_manifests": len(attacks)+1}


def stage_tests(module, out):
    directory = out / "stages"
    directory.mkdir()
    script = directory / "stage child with spaces.py"
    script.write_text('''import json,os,sys,time
from pathlib import Path
mode,artifact,watched,extra=sys.argv[1:]
sys.stdout.buffer.write(b"actual stdout\\x00\\xff\\n")
sys.stdout.buffer.flush()
sys.stderr.buffer.write(b"actual stderr\\x80\\n")
sys.stderr.buffer.flush()
if mode=="timeout":
 Path(artifact).write_bytes(b"partial output before timeout")
 time.sleep(2)
if mode=="input_changed": Path(watched).write_bytes(b"changed owned input")
if mode!="missing_output": Path(artifact).write_bytes(json.dumps({"argv":sys.argv,"cwd":os.getcwd(),"extra":extra}).encode())
if mode=="nonzero_exit": sys.exit(7)
''')
    rows = []
    special = 'literal ; & | ` $(no_shell) " %PATH%'
    for mode in ("success", "nonzero_exit", "timeout", "missing_output", "input_changed"):
        watched = directory / (mode+"-input.bin")
        watched.write_bytes(b"initial owned input")
        target = directory / mode
        artifact = target / "artifact.bin"
        command = [str(Path(sys.executable).absolute()), str(script), mode,
                   str(artifact), str(watched), special]
        start, wall = time.perf_counter_ns(), time.time_ns()
        receipt = module.run_stage(command, target, timeout_seconds=0.15 if mode=="timeout" else 10,
                                   required_outputs=[artifact], cwd=ROOT, inputs=[script, watched])
        end, wall_end = time.perf_counter_ns(), time.time_ns()
        expected_status = mode
        need(receipt["status"] == expected_status and receipt["passed"] == (mode=="success"),
             "Actual isolated child status " + mode)
        need(start <= receipt["start_monotonic_ns"] <= receipt["end_monotonic_ns"] <= end
             and receipt["elapsed_seconds"] == (receipt["end_monotonic_ns"]-receipt["start_monotonic_ns"])/1e9
             and wall <= receipt["started_unix_ns"] <= wall_end,
             "Measured stage clocks bracketed by independent parent " + mode)
        need(receipt["argv"] == command and receipt["cwd"] == str(ROOT)
             and not receipt["command_shell_used"] and not receipt["environment_dumped"]
             and not receipt["timeout_descendant_tree_termination_claimed"],
             "Direct full argument vector/cwd and honest scope " + mode)
        need((target/"stdout.bin").read_bytes().startswith(b"actual stdout\0\xff\n")
             and (target/"stderr.bin").read_bytes().endswith(b"actual stderr\x80\n"),
             "Exact actual binary stdout/stderr preserved " + mode)
        if mode in ("success", "nonzero_exit", "input_changed"):
            value = json.loads(artifact.read_bytes())
            need(value["extra"] == special and value["cwd"].casefold() == str(ROOT).casefold(),
                 "Child received literal shell metacharacters as data " + mode)
        if mode=="nonzero_exit":
            need(receipt["exit_code"] == 7, "Actual nonzero child exit is retained")
        if mode=="input_changed":
            need(not receipt["inputs_stable"] and receipt["input_sha256"] != receipt["final_input_sha256"],
                 "Changed explicit input cannot publish successful stage")
        if mode=="timeout":
            need(artifact.read_bytes() == b"partial output before timeout"
                 and str(artifact) in receipt["artifact_sha256"] and not receipt["passed"],
                 "Timed-out partial artifact is hashed and retained without success")
        need(module.verify_stage(target, sha((target/"stage.json").read_bytes()))["status"] == mode,
             "Pinned stage receipt physically verifies " + mode)
        rows.append({"directory": str(target), "status": mode, "seconds": receipt["elapsed_seconds"]})
        for path in target.iterdir():
            if path.is_file(): pin(path)
        pin(watched)
    # Preexisting required artifact is refused before the child can execute.
    stale = directory / "stale.bin"
    stale.write_bytes(b"retained previous artifact")
    marker = directory / "should-never-appear.bin"
    target = directory / "preexisting-required"
    expect_refusal(lambda: module.run_stage([sys.executable, str(script), "success", str(marker), str(stale), special],
                                           target, required_outputs=[stale]),
                   "Stale required output refused before launch")
    need(stale.read_bytes() == b"retained previous artifact" and not marker.exists() and not target.exists(),
         "Stale output refusal publishes nothing and preserves prior bytes")
    expect_refusal(lambda: module.run_stage([sys.executable, "-c", "pass"], directory/"success"),
                   "Existing private stage directory never overwritten")
    fresh = directory / "fresh-alias-output.bin"
    expect_refusal(lambda: module.run_stage([sys.executable, "-c", "pass"], directory/"output-aliases",
                                           required_outputs=[fresh, str(fresh).upper().replace("\\", "/")]),
                   "Windows aliases of one required output are refused before launch")
    for timeout in (True, 0, -1, float("inf"), float("nan"), 601):
        expect_refusal(lambda t=timeout: module.run_stage([sys.executable, "-c", "pass"], directory/"invalid-timeout", t),
                       "Invalid bounded timeout " + repr(timeout))
    success = directory / "success"
    receipt_path = success / "stage.json"
    receipt_bytes = receipt_path.read_bytes()
    expected_sha = sha(receipt_bytes)
    expect_refusal(lambda: module.verify_stage(success, "0"*64), "External stage receipt pin is required")
    for name in ("stdout.bin", "stderr.bin", "artifact.bin"):
        path = success / name
        before = path.read_bytes(); path.write_bytes(before+b"tamper")
        expect_refusal(lambda: module.verify_stage(success, expected_sha), "Stage physical " + name + " corruption")
        path.write_bytes(before)
    # Inner consistency controls refresh the external receipt SHA deliberately.
    original = json.loads(receipt_bytes)
    mutations = [
        ("unknown successful status", lambda v: v.update(status="invented_status", passed=False)),
        ("nonbool passed", lambda v: v.update(passed=1)),
        ("negative monotonic interval", lambda v: v.update(end_monotonic_ns=v["start_monotonic_ns"]-1)),
        ("wrong measured duration", lambda v: v.update(elapsed_seconds=v["elapsed_seconds"]+1)),
        ("unbound declared command", lambda v: v.update(argv=[str(directory/"unbound.exe"), *v["argv"][1:]])),
        ("invented stage source digest", lambda v: v.update(stage_source_sha256="0"*64)),
        ("invented Python digest", lambda v: v.update(python_sha256="0"*64)),
        ("contradictory success launch error", lambda v: v.update(launch_error="invented launch failure")),
        ("inconsistent required artifact set", lambda v: v.update(required_outputs=[])),
    ]
    for name, mutate in mutations:
        value = json.loads(json.dumps(original)); mutate(value)
        receipt_path.write_text(json.dumps(value, indent=2)+"\n")
        try:
            expect_refusal(lambda: module.verify_stage(success, sha(receipt_path.read_bytes())), name)
        finally:
            receipt_path.write_bytes(receipt_bytes)
    need(module.verify_stage(success, expected_sha)["recorded_stage_passed"],
         "Restored immutable genuine success receipt remains valid")
    pin(script); pin(stale)
    return {"actual_direct_child_stages": rows, "malformed_receipts": len(mutations),
            "only_independent_python_fixtures_spawned": True}


def reparse_tests(bundle, stages, out):
    import paths
    import stat
    from types import SimpleNamespace
    # The managed environment refused an actual owned junction. Exercise the
    # identical lstat reparse attribute and ancestor walk without claiming that
    # a real junction was created or that concurrent reparses are supported.
    location = out / "controlled-reparse"
    location.mkdir()
    source = location / "source"
    source.mkdir()
    (source/"one.bin").write_bytes(b"independent source")
    original_lstat = Path.lstat
    selected = source
    def injected_lstat(path, *args, **kwargs):
        result = original_lstat(path, *args, **kwargs)
        if path == selected:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return result
    Path.lstat = injected_lstat
    try:
        expect_refusal(lambda: paths.reject_reparse(source), "Reparse FILE_ATTRIBUTE_REPARSE_POINT predicate")
        expect_refusal(lambda: bundle.pack_capture(source, location/"new.capture"),
                       "Input root reparse is rejected before capture scan")
        expect_refusal(lambda: bundle.pack_capture(out/"synthetic-source", source/"new.capture"),
                       "Output parent reparse is rejected before publication")
        expect_refusal(lambda: stages.run_stage([sys.executable, "-c", "pass"], source/"stage"),
                       "Stage output reparse ancestor rejected before launch")
        expect_refusal(lambda: stages.run_stage([sys.executable, "-c", "pass"], location/"stage", cwd=source),
                       "Stage cwd reparse rejected before launch")
        selected = source / "one.bin"
        expect_refusal(lambda: bundle.pack_capture(source, location/"leaf.capture"),
                       "Input leaf reparse is rejected before reading bytes")
        selected = out / "first.capture"
        expect_refusal(lambda: bundle.CaptureBundle(selected, sha(selected.read_bytes())),
                       "Reader input reparse rejected before mmap")
    finally:
        Path.lstat = original_lstat
    need(not (location/"new.capture").exists() and not (source/"new.capture").exists()
         and not (location/"stage").exists() and not (source/"stage").exists(),
         "Controlled reparse denials publish no output or launch directories")
    return {"controlled_attribute_denials": 7, "actual_junction_fixture_created": False,
            "actual_junction_setup": "Denied with Access denied by managed environment",
            "concurrent_reparse_changes_supported": False}


def main(directory):
    global ATTEMPT
    out = Path(directory).resolve()
    assert out.parent == ROOT / "reports/m4-pipeline-review"
    out.mkdir(parents=True, exist_ok=False)
    ATTEMPT = out
    try:
        for filename in ("paths.py", "capture_bundle.py", "manifests.py", "stages.py"):
            candidate = ROOT / "tools/m4-pipeline" / filename
            pin(candidate)
            (out / (filename + ".candidate")).write_bytes(candidate.read_bytes())
        bundle = load("independent_capture_candidate", "capture_bundle.py")
        result = bundle_tests(bundle, out)
        roundtrips = frozen_roundtrips(bundle, out)
        manifests = load("independent_manifest_candidate", "manifests.py")
        manifest_result = manifest_tests(manifests, out)
        stages = load("independent_stage_candidate", "stages.py")
        stage_result = stage_tests(stages, out)
        reparse_result = reparse_tests(bundle, stages, out)
        pin(ROOT / "tools/m4-pipeline/paths.py")
        pin(__file__); pin(sys.executable)
        for name, expected in PINS.items():
            need(sha(Path(name).read_bytes()) == expected, "Final physical review binding: " + name)
        report = {"passed": True, "checks": CHECKS, "bundle": result,
                  "frozen_roundtrips": roundtrips, "manifests": manifest_result,
                  "stages": stage_result,
                  "reparse": reparse_result,
                  "native_candidate_rerun": False, "original_executed": False,
                  "game_launched": False, "semantic_observer_rules_changed": False,
                  "files": PINS}
        (out / "report.json").write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps({"passed": True, "checks": len(CHECKS),
                          "malformed_archives": result["malformed_archives"]}))
    except Exception:
        (out / "failure.txt").write_text(traceback.format_exc())
        (out / "review-attempt.py").write_bytes(Path(__file__).read_bytes())
        raise


if __name__ == "__main__":
    main(sys.argv[1])
