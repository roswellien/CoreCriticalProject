"""PM adapter to the existing MW3 recursive scanner and Remill/LLVM lifter.

All derived spans, LLVM, objects and dispatch includes stay in ignored reports/.
No import overlap, guessed address offset or MW3 game optimization grants reuse.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path

from target import GAME, ROOT, closure_images, load_target, require_closure

sys.path.insert(0, str(ROOT / "tools/m4-crt-heap-carry"))


def create_closure(target: dict, output: Path, roots: list[int], initializers: bool,
                   max_depth: int | None = None) -> None:
    import mfc_closure as scanner
    if output.exists():
        raise FileExistsError(output)
    if max_depth is not None and max_depth < 0:
        raise ValueError("max depth must be nonnegative")
    scanner.IMAGES = closure_images(target)
    scanner.PES.clear()
    images = {k: scanner.PE(*v[:3]) for k, v in scanner.IMAGES.items()}
    by_dll = {v["pin"]["filename"].casefold(): k for k, v in target["inputs"].items()}
    bounds = {}
    for name, image in images.items():
        bounds[name] = {cell: images[by_dll[dll.casefold()]].export(symbol)
                        for cell, (dll, symbol) in image.imports().items()
                        if dll.casefold() in by_dll}
    if not roots:
        roots = [v["image"].image_base + v["image"].entry_point_rva
                 for v in target["inputs"].values()]
        roots += target.get("additional_startup_roots", [])
    if initializers:
        game = images["game"]
        roots += [game.word(a) for begin, end in target["initializer_tables"]
                  for a in range(begin, end, 4) if game.word(a)]
        for name, intervals in target.get("module_initializer_tables", {}).items():
            module = images[name]
            roots += [module.word(a) for begin, end in intervals
                      for a in range(begin, end, 4) if module.word(a)]
        for name, intervals in target.get("callback_tables", {}).items():
            module = images[name]
            roots += [module.word(a) for begin, end in intervals for a in range(begin, end, 4)]
        for name, maps in target.get("message_maps", {}).items():
            module = images[name]
            for header, begin, end in maps:
                if end < begin or (end - begin) % 24 or module.word(header + 4) != begin:
                    raise ValueError("message-map bounds disagree with the exact image")
                if any(module.word(end + offset) for offset in range(0, 24, 4)):
                    raise ValueError("message-map terminal record is not empty")
                if module.word(header):
                    roots.append(module.word(header))  # MFC's base-map getter, NULL at the root
                roots += [module.word(a + 20) for a in range(begin, end, 24)]
    if any(scanner.image(a) is None for a in roots):
        raise ValueError("root outside exact target executable ranges")
    done, todo = {}, deque((a, 0) for a in roots)
    while todo:
        address, depth = todo.popleft()
        module = scanner.image(address)
        if address in done or module is None:
            continue
        row = scanner.function(address, bounds[module])
        if row["end"] <= address:
            raise ValueError(f"undecodable closure entry {address:#x}")
        done[address] = row
        if max_depth is None or depth < max_depth:
            todo.extend((a, depth + 1) for a in row["calls"] + row["tails"] + row["imms"])
        if len(done) % 100 == 0:
            print(f"{len(done)} static entries; {len(todo)} pending edges", flush=True)
    closure = dict(target=GAME, images={k: v[1] for k, v in scanner.IMAGES.items()},
                   roots=sorted(set(roots)), functions=[done[a] for a in sorted(done)],
                   limitations=["Static bounded recursive descent; indirect targets and initializer callbacks may be missing.",
                                "No execution or whole-program completeness claim."])
    if max_depth is not None:
        closure["selection"] = dict(max_depth=max_depth)
    require_closure(target, closure)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(closure, indent=1) + "\n", encoding="utf-8")
    print(f"{len(done)} entries -> {output}")


def lift(target: dict, source: Path, digest: str, output: Path, partition: str | None,
         skip: list[Path] | None = None, roots: list[int] | None = None,
         max_depth: int | None = None) -> None:
    import lift_attach as lifter
    import lift_closure as common
    import fp_lowering as fp
    import x87_bridges as x87
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("closure SHA-256 mismatch")
    closure = json.loads(data)
    require_closure(target, closure)
    if output.exists():
        raise FileExistsError(output)
    if not re.fullmatch(r"lifts-r[1-9][0-9]*(-p[0-9]+)?", output.name):
        raise ValueError("output must end in lifts-rN or lifts-rN-pK")
    lifter.IMAGES = {k: (v["path"], v["pin"]["sha256"]) for k, v in target["inputs"].items()}
    lifter.PROVIDER, lifter.PROVIDER_SHA = lifter.IMAGES["msvcrt"]
    common.RAW_END.clear()
    functions = closure["functions"]
    if roots or max_depth is not None:
        if max_depth is not None and max_depth < 0:
            raise ValueError("max depth must be nonnegative")
        by_address = {f["entry"]: f for f in functions}
        roots = roots or closure["roots"]
        if any(a not in by_address for a in roots):
            raise ValueError("selected root is absent from the pinned static closure")
        done, todo, level = set(), set(roots), 0
        while todo and (max_depth is None or level <= max_depth):
            current = (todo & by_address.keys()) - done
            done |= current
            todo = {c for a in current for key in ("calls", "tails", "imms")
                    for c in by_address[a][key]} - done
            level += 1
        functions = [f for f in functions if f["entry"] in done]
    entries = {f["entry"] for f in functions}
    spans = [s for f in functions for s in common.spans(f)
             if s[3] == f["entry"] or s[3] not in entries]
    covered, inherited = set(), []
    for directory in skip or []:
        report_bytes = (directory / "report.json").read_bytes()
        previous = json.loads(report_bytes)
        if previous.get("target") != GAME or previous.get("images") != closure["images"]:
            raise ValueError("skip report belongs to different target inputs")
        covered.update(row["entry"] for row in previous["components"].values())
        inherited.append(dict(path=str(directory.resolve()), sha256=hashlib.sha256(report_bytes).hexdigest()))
    spans = [s for s in spans if s[3] not in covered]
    if len({s[0] for s in spans}) != len(spans):
        raise ValueError("duplicate dispatch address across target modules")
    if partition:
        k, n = map(int, partition.split("/"))
        if not 0 <= k < n:
            raise ValueError("partition must be K/N, 0 <= K < N")
        spans = spans[k::n]
    lifter.SPANS = tuple(spans)

    class Renames(dict):
        def get(self, component, default=None):
            text = (output / (component + "-guest.ll")).read_text()
            return {name: "mw34_pm_" + name
                    for name in set(re.findall(r"^declare ptr @(sub_[0-9a-f]+)", text, re.M))}

    lifter.RENAMES = Renames()
    lifter.BRIDGES |= {"__remill_error", "__remill_atomic_begin", "__remill_atomic_end",
                       "__remill_async_hyper_call"} | fp.BRIDGES
    lifter.LOWER_PATCHES, lifter.LLVM_CLASS = fp.PATCHES, fp.llvm_class
    lifter.GUEST_IR_HOOK = lambda text: x87.rewrite(text)[0]
    lifter.TOLERANT = True
    # Keep all x87 exception tracking. MW3's --x87-noexc assumptions are unproved for PM.
    lifter.main(output.name, output_root=output.parent)
    (output / "closure.json").write_bytes(data)
    report_path = output / "report.json"
    report = json.loads(report_path.read_text())
    report.update(target=GAME, images=closure["images"], closure_sha256=digest, skipped_reports=inherited)
    if roots or max_depth is not None:
        report["selection"] = dict(roots=roots, max_depth=max_depth, functions=len(functions))
    report_path.write_text(json.dumps(report, indent=1) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--installation", type=Path, default=ROOT / "MW3-PiratesMoon")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("closure")
    c.add_argument("output", type=Path)
    c.add_argument("--root", action="append", type=lambda s: int(s, 0), default=[])
    c.add_argument("--initializers", action="store_true")
    c.add_argument("--max-depth", type=int)
    l = sub.add_parser("lift")
    l.add_argument("closure", type=Path)
    l.add_argument("sha256")
    l.add_argument("output", type=Path)
    l.add_argument("--partition")
    l.add_argument("--skip", type=Path, action="append", default=[])
    l.add_argument("--root", action="append", type=lambda s: int(s, 0), default=[])
    l.add_argument("--max-depth", type=int)
    args = p.parse_args()
    target = load_target(args.installation)
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports/pirates-moon").resolve()):
        p.error("derived output must stay under reports/pirates-moon/")
    if args.command == "closure":
        create_closure(target, output, args.root, args.initializers, args.max_depth)
    else:
        lift(target, args.closure, args.sha256, output, args.partition, args.skip,
             args.root, args.max_depth)


if __name__ == "__main__":
    main()
