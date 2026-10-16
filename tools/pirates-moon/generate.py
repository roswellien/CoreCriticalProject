"""Generate isolated PM host profile and dispatch from closed, pinned lift reports."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from target import GAME, ROOT, code_ranges, load_target, require_closure


def verified_rows(target: dict, pairs: list[tuple[Path, str]]) -> list[tuple]:
    rows = {}
    expected = {k: v["pin"]["sha256"] for k, v in target["inputs"].items()}
    for directory, digest in pairs:
        data = (directory / "report.json").read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("lift report digest mismatch")
        report = json.loads(data)
        if report.get("target") != GAME or report.get("images") != expected:
            raise ValueError("lift report belongs to different target inputs")
        closure_bytes = (directory / "closure.json").read_bytes()
        if hashlib.sha256(closure_bytes).hexdigest() != report["closure_sha256"]:
            raise ValueError("lift closure digest mismatch")
        require_closure(target, json.loads(closure_bytes))
        for failed in report.get("failed", {}):
            if failed.startswith("m_"):
                rows.pop(int(failed[2:], 16), None)
        for name, row in report["components"].items():
            if not name.startswith("m_") or int(name[2:], 16) != row["entry"]:
                raise ValueError("component identity mismatch")
            owners = [v for v in target["inputs"].values()
                      if any(lo <= row["start"] <= row["entry"] < row["end"] <= hi
                             for lo, hi in code_ranges(v["image"]))]
            if len(owners) != 1:
                raise ValueError("component outside one exact target code section")
            owner = owners[0]
            start = owner["image"].rva_range(row["start"] - owner["image"].image_base,
                                              row["end"] - row["start"])[0]
            source = owner["data"][start:start + row["end"] - row["start"]]
            if hashlib.sha256(source).hexdigest() != row["source_sha256"]:
                raise ValueError("component source differs from target bytes")
            artifact = directory / (name + "-O2.obj")
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != row["objects"]["O2"]["sha256"]:
                raise ValueError("native object differs from closed lift report")
            rows[row["entry"]] = (name, row, artifact.resolve())
    return [(entry, *rows[entry]) for entry in sorted(rows)]


def generate(target: dict, pairs: list[tuple[Path, str]], output: Path) -> None:
    rows = verified_rows(target, pairs)
    if output.exists():
        raise FileExistsError(output)
    modules = target["inputs"]
    mfc, game = modules["mfc42"]["image"], modules["game"]["image"]
    writable = [s for s in mfc.sections if s["writable"]]
    game_writable = [s for s in game.sections if s["writable"]]
    if len(writable) != 1 or len(game_writable) != 1:
        raise ValueError("native stage requires one writable section per image")
    def mapped_end(image, section):
        return image.image_base + section["virtual_address"] + ((max(section["virtual_size"], section["raw_size"]) + 4095) & ~4095)
    values = dict(base=mfc.image_base, image_end=mfc.image_base + mfc.size_of_image,
                  data=mfc.image_base + writable[0]["virtual_address"], data_end=mapped_end(mfc, writable[0]),
                  entry=mfc.image_base + mfc.entry_point_rva, crt_entry=target["entry"],
                  game_end=game.image_base + game.size_of_image,
                  game_data=game.image_base + game_writable[0]["virtual_address"],
                  game_data_end=mapped_end(game, game_writable[0]),
                  game_code_begin=code_ranges(game)[0][0], game_code_end=code_ranges(game)[0][1],
                  initializer_begin=target["initializer_tables"][1][0],
                  initializer_end=target["initializer_tables"][1][1],
                  initterm_thunk=0x5cf186, entry_continuation=0x5cf0b2)
    # Source stores: MFC42 5F40F9EC and MSVCP60 780C1028 -> [entry ESP+8].
    values["attach_result_argument_offset"] = 8
    header = "// Experimental PM target; generated from exact local input identities.\n"
    header += "".join(f"inline constexpr unsigned {k}=0x{v:x};\n" for k, v in values.items())
    header += f'inline constexpr char image_sha[]="{modules["mfc42"]["pin"]["sha256"]}";\n'
    ordered = [modules[k] for k in ("game", "msvcrt", "mfc42", "msvcp60", "mech3msg")]
    for field, key in (("names", "filename"), ("hashes", "sha256")):
        header += "inline constexpr std::array<const char*,5>pm_module_" + field + "{{"
        header += ",".join(json.dumps(m["pin"][key]) for m in ordered) + "}};\n"
    header += "inline constexpr std::array<unsigned,5>pm_module_bases{{"
    header += ",".join(hex(m["image"].image_base) for m in ordered) + "}};\n"
    entries = "".join(f'extern "C" void*mw34_attach_{name}_body(State*,unsigned,void*) noexcept(false);\n'
                      for _, name, _, _ in rows)
    entries += f"inline constexpr std::array<Entry,{len(rows)}>mfc_entries{{{{"
    entries += ",".join(f"{{0x{a:x},mw34_attach_{name}_body}}" for a, name, _, _ in rows) + "}};\n"
    bridges = {b for _, _, row, _ in rows for b in row["bridges"]}
    if any(b.startswith(("sub_", "mw34_mfc_sub_")) for b in bridges):
        raise ValueError("foreign direct router in PM object")
    routers = "".join(f'extern "C" void*{b}(State*s,unsigned a,void*p)noexcept(false){{return mf_called(s,a,p);}}\n'
                      for b in sorted(bridges) if b.startswith("mw34_pm_sub_"))
    routers += "".join(f'extern "C" unsigned char {b}()noexcept(false){{return mf_undefined();}}\n'
                       for b in sorted(bridges) if b.endswith("_undefined_8"))
    output.mkdir(parents=True)
    for name, content in (("target.inc", header), ("entries.inc", entries), ("routers.inc", routers),
                          ("objects.txt", "".join(obj.as_posix() + "\n" for _, _, _, obj in rows))):
        (output / name).write_text(content, encoding="utf-8")
    print(f"PM profile and {len(rows)} verified native entries -> {output}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("--installation", type=Path, default=ROOT / "MW3-PiratesMoon")
    p.add_argument("--lift", nargs=2, action="append", required=True, metavar=("DIRECTORY", "SHA256"))
    args = p.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports/pirates-moon").resolve()):
        p.error("generated output must stay under reports/pirates-moon/")
    generate(load_target(args.installation), [(Path(d), h) for d, h in args.lift], output)


if __name__ == "__main__":
    main()
