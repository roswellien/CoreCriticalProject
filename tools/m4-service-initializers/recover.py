"""Read-only, exact-image startup service recovery; never execute guest code.

Derived instruction text, bytes, provider data, and CFGs are private reports.
This is a static planning tool, not a native service implementation or oracle.
The older inventory is a comparison input, not the source of the new CFG.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/analysis"))
from pe import PEImage, read_binary

IDENTITIES = {
    "MW3/Mech3.exe": "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf",
    "local/mw3-staged/Shared_DLLs/MSVCRT.DLL": "2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7",
    "local/mw3-staged/Shared_DLLs/MSVCP50.DLL": "91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a",
    "local/mw3-staged/Shared_DLLs/MFC42.DLL": "5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8",
    "tools/analysis/pe.py": "bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638",
    "local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe":
        "a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a",
}
DECODER = ROOT / list(IDENTITIES)[-1]
ROW = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}[ ]*)+)\t(.+)$")
DEST = re.compile(r"^0x([0-9a-f]+)(?:\s|$)")
INDIRECT_IAT = re.compile(r"^dword ptr \[0x([0-9a-f]+)\]$")
ABS_MEMORY = re.compile(r"(?:(byte|word|dword|qword|tbyte) ptr )?\[0x([0-9a-f]+)\]")
FP_ROOTS = [0x4B5910, 0x4C19F0, 0x4C58C0]
EXTRA_ROOTS = [0x4C5940, 0x4C5900, 0x4C7B40, 0x4D9F90,
               0x4E78D0, 0x4125A0, 0x5B1359, 0x5B386B]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bind(path):
    path = Path(path).resolve()
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class Module:
    def __init__(self, path):
        self.path = path
        self.image = PEImage(read_binary(path))
        self.base = self.image.image_base
        self.rows = {}
        self.imports = {self.base + s["iat_rva"]: {"library": d["library"], **s}
                        for d in self.image.imports() for s in d["symbols"]}
        self.exports = self.image.exports()

    def section(self, address):
        rva = address - self.base
        return next((s for s in self.image.sections
                     if s["virtual_address"] <= rva < s["virtual_address"] +
                     max(s["raw_size"], s["virtual_size"])), None)

    def executable(self, address):
        s = self.section(address)
        return bool(s and s["executable"] and
                    address - self.base - s["virtual_address"] < s["raw_size"])

    def data(self, address, size):
        require(0 < size <= 64, "Unbounded data observation")
        rva = address - self.base
        require(0 <= rva < self.image.size_of_image, "Data outside module")
        try:
            off, _ = self.image.rva_range(rva, size)
            return {"va": address, "size": size, "file_offset": off,
                    "initial_hex": self.image.read(off, size).hex(), "backing": "file"}
        except ValueError:
            s = self.section(address)
            require(s is not None and rva + size <= s["virtual_address"] +
                    max(s["virtual_size"], s["raw_size"]), "Data crosses mapped section")
            delta = rva - s["virtual_address"]
            require(delta >= s["raw_size"], "Partially backed data needs separate contract")
            return {"va": address, "size": size, "initial_hex": bytes(size).hex(),
                    "backing": "PE virtual zero-fill; not an initialized runtime value"}

    def decode(self, out):
        text_sections = [s for s in self.image.sections if s["executable"]]
        begin = min(self.base + s["virtual_address"] for s in text_sections)
        end = max(self.base + s["virtual_address"] + s["raw_size"] for s in text_sections)
        command = [str(DECODER), "--disassemble", "--x86-asm-syntax=intel",
                   f"--start-address={begin}", f"--stop-address={end}", str(self.path)]
        result = subprocess.run(command, capture_output=True, check=True, timeout=120)
        require(len(result.stdout) < 80 * 1024 * 1024, "Decoder output limit")
        target = out / (self.path.name + ".linear-lookup.txt")
        target.write_bytes(result.stdout)
        for line in result.stdout.decode("utf-8").splitlines():
            m = ROW.match(line)
            if not m:
                continue
            address, code = int(m[1], 16), bytes.fromhex(m[2])
            require(address not in self.rows and 0 < len(code) <= 15, "Duplicate/long decoder row")
            offset, _ = self.image.rva_range(address - self.base, len(code))
            require(self.image.read(offset, len(code)) == code, "Decoder bytes differ from exact file")
            asm = re.sub(r"\s+", " ", m[3].strip())
            mnemonic, _, operands = asm.partition(" ")
            self.rows[address] = {"pc": address, "size": len(code), "bytes": code.hex(),
                                  "mnemonic": mnemonic, "operands": operands}
        return {"command": command, "output": bind(target), "rows": len(self.rows)}


def relative_target(row):
    code = bytes.fromhex(row["bytes"])
    require(len(code) == row["size"], "Instruction size inconsistency")
    if len(code) == 5 and code[0] in (0xE8, 0xE9):
        delta = int.from_bytes(code[1:], "little", signed=True)
    elif len(code) == 2 and (code[0] == 0xEB or 0x70 <= code[0] <= 0x7F or 0xE0 <= code[0] <= 0xE3):
        delta = int.from_bytes(code[1:], "little", signed=True)
    elif len(code) == 6 and code[0] == 0x0F and 0x80 <= code[1] <= 0x8F:
        delta = int.from_bytes(code[2:], "little", signed=True)
    else:
        raise ValueError("Unsupported direct branch encoding")
    actual = (row["pc"] + len(code) + delta) & 0xFFFFFFFF
    shown = DEST.match(row["operands"])
    require(shown is not None and int(shown[1], 16) == actual, "Branch displacement/text mismatch")
    return actual


def walk(module, entry, limit=12000):
    """Own edge walker: tail branches stay local; normal calls have separate entries.

    Every conditional branch retains both successors, including apparent failure
    paths. Imported/indirect calls retain a *conditional* lexical continuation.
    No caller continuation is treated as proof that the service actually returns.
    """
    todo = deque([entry])
    reached, edges, calls, imports, unresolved, returns, literals = {}, [], [], [], [], [], []
    while todo:
        pc = todo.popleft()
        if pc in reached:
            continue
        if len(reached) >= limit:
            unresolved.append({"pc": pc, "reason": "instruction bound"})
            break
        if not module.executable(pc) or pc not in module.rows:
            unresolved.append({"pc": pc, "reason": "no exact file-backed decoded executable boundary"})
            continue
        row = module.rows[pc]
        reached[pc] = row
        mnemonic, operands = row["mnemonic"], row["operands"]
        next_pc = pc + row["size"]
        if mnemonic in ("ret", "retf"):
            returns.append({"pc": pc, "operands": operands, "pop_bytes": int(operands, 0) if operands else 0})
            continue
        if mnemonic in ("int", "int3", "ud2", "iret", "iretd", "sysenter", "syscall", "<unknown>", "data16") or mnemonic.startswith("."):
            unresolved.append({"pc": pc, "reason": "system, exception or undecoded instruction", "row": row})
            continue
        control = mnemonic in ("call", "jmp") or mnemonic.startswith("j") or mnemonic.startswith("loop")
        if not control:
            for token in re.findall(r"0x([0-9a-f]+)", operands):
                value = int(token, 16)
                if module.executable(value):
                    literals.append({"pc": pc, "value": value,
                                     "classification": "executable literal; callback/handler dispatch unproved"})
            edges.append({"from": pc, "to": next_pc, "kind": "fallthrough"})
            todo.append(next_pc)
            continue
        if DEST.match(operands):
            target = relative_target(row)
            if mnemonic == "call":
                calls.append({"site": pc, "target": target, "return_pc": next_pc})
                edges.append({"from": pc, "to": next_pc, "kind": "conditional normal-call continuation"})
                todo.append(next_pc)
            elif mnemonic == "jmp":
                edges.append({"from": pc, "to": target, "kind": "tail/local jump"})
                todo.append(target)
            else:
                edges.extend(({"from": pc, "to": target, "kind": "taken " + mnemonic},
                              {"from": pc, "to": next_pc, "kind": "not taken " + mnemonic}))
                todo.extend((target, next_pc))
        else:
            slot = INDIRECT_IAT.fullmatch(operands)
            if slot and int(slot[1], 16) in module.imports:
                slot = int(slot[1], 16)
                code = bytes.fromhex(row["bytes"])
                expected_prefix = b"\xff\x15" if mnemonic == "call" else b"\xff\x25"
                require(mnemonic in ("call", "jmp") and code == expected_prefix + struct.pack("<I", slot),
                        "Import site bytes do not encode owning IAT")
                imports.append({"site": pc, "kind": mnemonic, "iat": slot,
                                "symbol": module.imports[slot],
                                "return_pc": next_pc if mnemonic == "call" else None})
            else:
                unresolved.append({"pc": pc, "reason": "unresolved indirect control", "row": row})
            if mnemonic == "call":
                edges.append({"from": pc, "to": next_pc, "kind": "conditional service/indirect continuation"})
                todo.append(next_pc)
    chosen = [reached[p] for p in sorted(reached)]
    refs = []
    for row in chosen:
        for match in ABS_MEMORY.finditer(row["operands"]):
            address = int(match[2], 16)
            width = {"byte": 1, "word": 2, "dword": 4, "qword": 8, "tbyte": 10}.get(match[1])
            ref = {"pc": row["pc"], "address": address, "width": width,
                   "operation": row["mnemonic"], "operands": row["operands"]}
            s = module.section(address)
            ref["section"] = s
            if s and width:
                ref["initial"] = module.data(address, width)
            if address in module.imports:
                ref["IAT"] = module.imports[address]
            refs.append(ref)
    return {"entry": entry, "instructions": chosen, "instruction_count": len(chosen),
            "instruction_bytes_sha256": hashlib.sha256(b"".join(bytes.fromhex(r["bytes"]) for r in chosen)).hexdigest(),
            "edges": edges, "direct_calls": calls, "import_sites": imports,
            "returns": returns, "unresolved_controls": unresolved, "executable_literals": literals,
            "absolute_memory_references": refs,
            "FP_sites": [r["pc"] for r in chosen if r["mnemonic"].startswith("f")],
            "FS_sites": [r for r in chosen if "fs:" in r["operands"]],
            "local_decode_closed": not unresolved, "execution_or_admission": False}


def closure(module, entries, maximum=650):
    queue, nodes, deferred = deque(entries), {}, []
    while queue:
        entry = queue.popleft()
        if entry in nodes:
            continue
        if len(nodes) >= maximum or not module.executable(entry):
            deferred.append(entry)
            continue
        node = walk(module, entry)
        nodes[entry] = node
        queue.extend(c["target"] for c in node["direct_calls"])
    return nodes, sorted(set(deferred))


def subgraph(nodes, entry):
    todo, seen = [entry], set()
    while todo:
        value = todo.pop()
        if value in seen:
            continue
        seen.add(value)
        if value in nodes:
            todo.extend(c["target"] for c in nodes[value]["direct_calls"])
    return sorted(seen)


def authored_controls():
    class Fixture:
        imports = {0x2000: {"library": "fixture", "name": "measured"}}
        rows = {}
        def executable(self, pc): return 0x1000 <= pc < 0x1100
        def section(self, pc): return None
    fixture = Fixture()
    def row(pc, code, asm):
        m, _, o = asm.partition(" ")
        return {"pc": pc, "bytes": code, "size": len(bytes.fromhex(code)), "mnemonic": m, "operands": o}
    controls = []
    fixture.rows = {0x1000: row(0x1000, "75fe", "jne 0x1000"), 0x1002: row(0x1002, "c3", "ret")}
    g = walk(fixture, 0x1000)
    require(g["instruction_count"] == 2 and len(g["edges"]) == 2 and g["local_decode_closed"], "Backward loop/exit")
    controls.append("backward conditional retains both loop and return")
    for broken in [row(0x1000, "75fe", "jne 0x1002"), row(0x1000, "6675fe", "jne 0x1000")]:
        try: relative_target(broken)
        except ValueError: pass
        else: raise ValueError("Corrupted direct branch accepted")
        controls.append("reject displacement/text mismatch or unsupported prefix")
    fixture.rows = {0x1000: row(0x1000, "ffe0", "jmp eax")}
    require(not walk(fixture, 0x1000)["local_decode_closed"], "Indirect target became closed")
    controls.append("unresolved indirect JMP remains open")
    fixture.rows = {0x1000: row(0x1000, "ffd0", "call eax"), 0x1002: row(0x1002, "c3", "ret")}
    g = walk(fixture, 0x1000)
    require(len(g["returns"]) == 1 and len(g["unresolved_controls"]) == 1, "Indirect call continuation")
    controls.append("indirect CALL continuation is conditional and retains denial")
    fixture.rows = {0x1000: row(0x1000, "ff1500200000", "call dword ptr [0x2000]"),
                    0x1006: row(0x1006, "c3", "ret")}
    require(len(walk(fixture, 0x1000)["import_sites"]) == 1, "Owning fixture IAT")
    controls.append("exact import bytes and owning IAT admitted statically")
    fixture.rows[0x1000]["bytes"] = "ff1504200000"
    try: walk(fixture, 0x1000)
    except ValueError: pass
    else: raise ValueError("Wrong encoded IAT became accepted")
    controls.append("encoded other IAT rejected despite decoder text")
    fixture.rows[0x1000] = row(0x1000, "ff1500200000", "call dword ptr [0x2000]")
    fixture.imports = {}
    require(len(walk(fixture, 0x1000)["unresolved_controls"]) == 1, "Unowned IAT became import")
    controls.append("unowned absolute slot remains unresolved")
    fixture.rows = {0x1000: row(0x1000, "eb01", "jmp 0x1003")}
    require(not walk(fixture, 0x1000)["local_decode_closed"], "Missing target boundary")
    controls.append("missing decoded branch boundary remains open")
    fixture.rows = {0x1000: row(0x1000, "90", "nop"), 0x1001: row(0x1001, "c3", "ret")}
    require(not walk(fixture, 0x1000, limit=1)["local_decode_closed"], "Bounded traversal became closed")
    controls.append("instruction bound remains explicit")
    fixture.rows = {0x1000: row(0x1000, "6810100000", "push 0x1010"),
                    0x1005: row(0x1005, "c3", "ret"), 0x1010: row(0x1010, "cc", "int3")}
    g = walk(fixture, 0x1000)
    require(g["instruction_count"] == 2 and len(g["executable_literals"]) == 1, "Callback dispatch invented")
    controls.append("executable literal is reported without dispatch")
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    require(out == ROOT / "reports/m4-service-initializers/static-r1" and not out.exists(), "Fresh exact private output required")
    before = []
    for name, expected in IDENTITIES.items():
        item = bind(ROOT / name)
        require(item["sha256"] == expected, "Input identity mismatch: " + name)
        before.append(item)
    old = ROOT / "reports/m4-initializer-inventory/r1"
    old_paths = [old / p for p in ["report.json", "function-graphs.json", "pins.json", "instruction-lookup.json", "linear-lookup-only.txt"]]
    before.extend(bind(p) for p in old_paths)
    checks = authored_controls()
    out.mkdir(parents=True)
    modules = {"game": Module(ROOT / "MW3/Mech3.exe")}
    for name in ["MSVCRT.DLL", "MSVCP50.DLL", "MFC42.DLL"]:
        modules[name] = Module(ROOT / "local/mw3-staged/Shared_DLLs" / name)
    decodes = {key: value.decode(out) for key, value in modules.items()}
    game = modules["game"]
    slots = [{"slot": a, "entry": game.image.rva_u32(a - game.base)} for a in range(0x5E0000, 0x5E0244, 4)]
    require(len(slots) == 145 and sum(bool(x["entry"]) for x in slots) == 144, "Initializer table changed")
    all_nodes, deferred = closure(game, [s["entry"] for s in slots if s["entry"]])
    old_nodes = json.loads((old / "function-graphs.json").read_text(encoding="utf-8"))
    require(set(all_nodes) == {int(p) for p in old_nodes} and not deferred, "Fresh/inventory entry set mismatch")
    for entry, node in all_nodes.items():
        previous = old_nodes[str(entry)]
        require([r["pc"] for r in node["instructions"]] == previous["instruction_pcs"], "Fresh/inventory reachable PCs mismatch")
        require(node["instruction_bytes_sha256"] == previous["instruction_bytes_sha256"], "Fresh/inventory byte identity mismatch")
    roots, groups = [], {}
    for slot in slots:
        if not slot["entry"]:
            continue
        entries = subgraph(all_nodes, slot["entry"])
        nodes = [all_nodes[e] for e in entries]
        services = sorted({n["symbol"]["library"] + ":" + str(n["symbol"].get("name", n["symbol"].get("ordinal")))
                           for g in nodes for n in g["import_sites"]})
        row = {**slot, "local_entries": entries,
               "unique_instructions": len({r["pc"] for g in nodes for r in g["instructions"]}),
               "imports": services, "import_sites": [s for g in nodes for s in g["import_sites"]],
               "FS_sites": [s for g in nodes for s in g["FS_sites"]],
               "FP_sites": sorted({s for g in nodes for s in g["FP_sites"]}),
               "unresolved_controls": [s for g in nodes for s in g["unresolved_controls"]],
               "executable_literals": [s for g in nodes for s in g["executable_literals"]]}
        roots.append(row)
        key = (tuple(services), bool(row["FS_sites"]), len(row["unresolved_controls"]))
        groups.setdefault(key, []).append({k: row[k] for k in ("slot", "entry", "unique_instructions")})
    group_rows = [{"import_set": list(k[0]), "FS": k[1], "unresolved_controls_per_root": k[2],
                   "count": len(v), "roots": v} for k, v in sorted(groups.items(), key=lambda kv: (-len(kv[1]), str(kv[0])))]
    extra, extra_deferred = closure(game, EXTRA_ROOTS)
    provider_requests = {"MSVCRT.DLL": ["_hypot", "_onexit", "__dllonexit", "_strdup"],
                         "MSVCP50.DLL": ["?max@?$numeric_limits@M@std@@SAMXZ", "??0_Lockit@std@@QAE@XZ", "??1_Lockit@std@@QAE@XZ"],
                         "MFC42.DLL": [823, 825, 540, 561, 1168]}
    provider_reports = {}
    for name, requests in provider_requests.items():
        module = modules[name]
        resolved = []
        for request in requests:
            matches = [e for e in module.exports if (request == e["ordinal"]
                       if isinstance(request, int) else request in e["names"])]
            require(len(matches) == 1 and "forwarder" not in matches[0], "Export not uniquely resolved")
            export = matches[0]
            address = module.base + export["rva"]
            require(module.executable(address), "Requested provider export is not RX-backed code")
            resolved.append({"requested": request, "export": export, "preferred_va": address,
                             "section": module.section(address), "actual_loaded_module_known": False})
        graph, pending = closure(module, [r["preferred_va"] for r in resolved])
        for item in resolved:
            entries = subgraph(graph, item["preferred_va"])
            item["local_entries"] = entries
            item["unique_instructions"] = len({r["pc"] for e in entries if e in graph for r in graph[e]["instructions"]})
            item["nested_imports"] = [i for e in entries if e in graph for i in graph[e]["import_sites"]]
            item["unresolved_controls"] = [i for e in entries if e in graph for i in graph[e]["unresolved_controls"]]
            item["FS_sites"] = [i for e in entries if e in graph for i in graph[e]["FS_sites"]]
            item["deferred_local_entries"] = [e for e in entries if e not in graph]
        provider_reports[name] = {"identity": bind(module.path), "preferred_base": module.base,
                                  "requested_exports": resolved, "graphs": graph, "deferred_entries": pending}
        save(out / (name + ".provider.json"), provider_reports[name])
    save(out / "game-all-initializer-graphs.json", all_nodes)
    save(out / "game-extra-callback-SEH-graphs.json", {"graphs": extra, "deferred": extra_deferred})
    save(out / "root-classification.json", {"slots": slots, "roots": roots, "groups": group_rows})
    save(out / "controls.json", {"passed": True, "count": len(checks), "controls": checks})
    selected = {hex(p): {"root": next(r for r in roots if r["entry"] == p),
                          "graphs": {e: all_nodes[e] for e in subgraph(all_nodes, p)}} for p in FP_ROOTS}
    save(out / "three-FP-root-graphs.json", selected)
    data = {"numeric_max_float": modules["MSVCP50.DLL"].data(0x78115004, 4),
            "hypot_constructor_one": game.data(0x5C93A8, 8),
            "zero_comparison": game.data(0x5CAD6C, 4), "unit_direction": game.data(0x5EDA70, 12),
            "default_vector": game.data(0x63D870, 12), "window_defaults": game.data(0x5E6000, 24),
            "onexit_table_first": game.data(0x9A17F0, 4), "onexit_table_last": game.data(0x9A17EC, 4)}
    save(out / "private-data-observations.json", data)
    report = {"schema_version": 1, "scope": "Read-only static service-initializer recovery; no original/native execution or admission",
              "passed_static_checks": True, "table_slots": len(slots), "nonzero_roots": len(roots),
              "fresh_graph_nodes": len(all_nodes), "fresh_inventory_PC_and_byte_sets_equal": True,
              "FP_roots": sum(bool(r["FP_sites"]) for r in roots), "FS_roots": sum(bool(r["FS_sites"]) for r in roots),
              "three_remaining_FP_roots": [{k: r[k] for k in ("slot", "entry", "local_entries", "unique_instructions", "imports", "FS_sites", "unresolved_controls")}
                                            for r in roots if r["entry"] in FP_ROOTS],
              "group_count": len(group_rows), "independent_authored_controls": len(checks), "decode_commands": decodes,
              "inputs": before, "source": bind(Path(__file__)),
              "limits": ["Static preferred provider identity is exact; actual game-loaded module identity and initialization are unobserved.",
                         "Direct conditional graph includes both branches and possible normal call continuations, not dynamic reachability or noreturn proof.",
                         "Import services, indirect calls, exception handlers, callbacks, aliases, mutated globals and their lifetimes need explicit execution contracts.",
                         "Linear lookup boundaries are not a proof against overlapping x86 instructions; any missing boundary remains unresolved.",
                         "Data values are PE initial backing/zero-fill only; they are not claims about initialized module state.",
                         "No M4 startup, native service, game, menu or renderer acceptance is provided."]}
    save(out / "recovery.json", report)
    for item in before:
        require(bind(item["path"]) == item, "Read-only input changed during analysis")
    save(out / "recovery-pins.json", {"schema_version": 1, "bindings": before + [bind(Path(__file__))] +
         [bind(p) for p in sorted(out.iterdir()) if p.is_file()]})
    print(json.dumps({k: report[k] for k in ("passed_static_checks", "nonzero_roots", "FP_roots", "FS_roots", "group_count")}))


if __name__ == "__main__":
    main()
