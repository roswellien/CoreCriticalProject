"""Extract a pinned original perspective loop into a private, asset-free fixture.

Generated original IR remains under local/. No game launch or retained lift edit.
"""

from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "reports/m4-crt-attach/lifts-r42/m_53f2e0-host.ll"
SHA = "f0020463391c3b3f95ca57161333ab15297cf8f24d1d94c72c2e5db85436a8f3"
LLVM = ROOT / "local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin"


def extract(raw, lit_loop=False):
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError("Exact original host module pin required")
    t = raw.decode().replace("\r\n", "\n")
    start = t.index("define ptr @mw34_attach_m_53f2e0_body(")
    end = t.index("\n}", start) + 2
    body = t[start:end]
    entry = body[: body.index("  br label %46")]
    entry = entry.replace("@mw34_attach_m_53f2e0_body(", "@mw34_projection_fixture(")
    entry = entry.replace("ptr noalias %memory) {", "ptr noalias %memory, i32 %skip) {")
    loop_label, end_label, exit_label, loop_pc = (
        ("51193", "52271", "51156", 0x540985) if lit_loop else ("71250", "72328", "71213", 0x5412A5)
    )
    setup = """  store i32 %program_counter, ptr %ECX, align 4
  %fixture_last = sub i32 %program_counter, 1
  %fixture_skip = icmp ne i32 %skip, 0
  %fixture_index = select i1 %fixture_skip, i32 %fixture_last, i32 0
  %fixture_count = sub i32 %program_counter, %fixture_index
  %fixture_aoffset = mul i32 %fixture_index, 12
  %fixture_doffset = mul i32 %fixture_index, 32
  %fixture_a = add i32 %fixture_aoffset, 7632548
  %fixture_d = add i32 %fixture_doffset, 7533600
  store i32 %fixture_a, ptr %EAX, align 4
  store i32 %fixture_d, ptr %EDX, align 4
  store i32 %fixture_count, ptr %ESI, align 4
  store i32 LOOP_PC, ptr %NEXT_PC, align 4
  br label %LOOP_LABEL

"""
    setup = setup.replace("LOOP_PC", str(loop_pc)).replace("LOOP_LABEL", loop_label)
    loop = body[body.index(loop_label + ":") : body.index(end_label + ":")]
    # Comments list old predecessors; remove them to avoid misleading provenance.
    loop = re.sub(r"; preds =[^\n]*", "; extracted original loop", loop)
    tail = """EXIT_LABEL:
  %fixture_memory = load ptr, ptr %MEMORY, align 4
  ret ptr %fixture_memory
}
"""
    tail = tail.replace("EXIT_LABEL", exit_label)
    result = t[:start] + entry + setup + loop + tail + t[end:]
    # Original numeric SSA slots are sparse after extraction. Give every numeric
    # identifier and block a name; no instruction semantics are changed.
    result = re.sub(r"%(\d+)\b", r"%origin_\1", result)
    result = re.sub(r"^(\d+):", r"origin_\1:", result, flags=re.M)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out", type=Path, default=ROOT / "local/gpu-projection-bypass-r1/fixture-unlit"
    )
    p.add_argument(
        "--merge-x87", action="store_true", help="Use the production simplifycfg/merge_x87 recipe"
    )
    p.add_argument(
        "--lit-loop",
        action="store_true",
        help="Test textured lit loop540985, otherwise unlit5412A5",
    )
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ir = out / "projection-loop.ll"
    ir.write_text(extract(SOURCE.read_bytes(), args.lit_loop))
    merge_stats = None
    if args.merge_x87:
        cfg = out / "projection-loop-cfg.ll"
        subprocess.run(
            [str(LLVM / "opt.exe"), "-passes=simplifycfg", "-S", str(ir), "-o", str(cfg)],
            check=True,
        )
        sys.path.insert(0, str(ROOT / "tools/m4-crt-heap-carry"))
        import merge_x87

        merged, merge_stats = merge_x87.transform(cfg.read_text())
        ir = out / "projection-loop-merged.ll"
        ir.write_text(merged)
    script = out / "run.ps1"
    script.write_text(
        """$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
"""
        + f"""& '{LLVM/'clang.exe'}' -O2 -c '{ir}' -o '{out/'projection-loop.obj'}'
if($LASTEXITCODE){{throw 'IR fixture compile failed'}}
& '{LLVM/'clang-cl.exe'}' /nologo /std:c++20 /MD /EHsc /O2 '{ROOT/'tools/remaster-launcher/test_projection_loop.cpp'}' '/Fe:{out/'projection-loop.exe'}' '/Fo:{out/'fixture.obj'}' /link '{out/'projection-loop.obj'}'
if($LASTEXITCODE){{throw 'C++ fixture compile failed'}}
Set-Location '{out}'
& '{out/'projection-loop.exe'}'
exit $LASTEXITCODE
"""
    )
    run = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True,
        text=True,
    )
    (out / "run.log").write_text(run.stdout + run.stderr)
    result = dict(
        source_sha256=SHA,
        generated_sha256=hashlib.sha256(ir.read_bytes()).hexdigest(),
        exit_code=run.returncode,
        source=str(SOURCE),
        generated=str(ir),
        log=str(out / "run.log"),
        merge_x87=merge_stats,
    )
    result["loop"] = "0x540985" if args.lit_loop else "0x5412a5"
    result["fixture_cpp_sha256"] = hashlib.sha256(
        (ROOT / "tools/remaster-launcher/test_projection_loop.cpp").read_bytes()
    ).hexdigest()
    result["extractor_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["clang_sha256"] = hashlib.sha256((LLVM / "clang.exe").read_bytes()).hexdigest()
    if args.merge_x87:
        result["merge_transform_sha256"] = hashlib.sha256(
            (ROOT / "tools/m4-crt-heap-carry/merge_x87.py").read_bytes()
        ).hexdigest()
    (out / "closure.json").write_text(json.dumps(result, indent=2))
    print(run.stdout + run.stderr)
    print(json.dumps(result, indent=2))
    raise SystemExit(run.returncode)


if __name__ == "__main__":
    main()
