"""Original lit-loop fixture through the production cleanup/strict/flat recipe."""

from pathlib import Path
import hashlib, json, subprocess, sys
import test_projection_loop as original
import flat_projection_watch as watch

ROOT = original.ROOT
OUT = ROOT / "local/gpu-projection-bypass-r1/fixture-lit-optimized"
LLVM = original.LLVM


def main():
    global OUT
    watching = "--unwatched" not in sys.argv
    if not watching:
        OUT = ROOT / "local/gpu-projection-bypass-r1/fixture-lit-optimized-unwatched"
    OUT.mkdir(parents=True, exist_ok=True)
    source = original.extract(original.SOURCE.read_bytes(), lit_loop=True)
    source = source.replace("@mw34_projection_fixture(", "@mw34_attach_projection_fixture_body(")
    source, cleanup = watch._cleanup.transform(source)
    raw = OUT / "clean.ll"
    raw.write_text(source)
    cfg = OUT / "cfg.ll"
    subprocess.run(
        [str(LLVM / "opt.exe"), "-passes=simplifycfg", "-S", str(raw), "-o", str(cfg)], check=True
    )
    sys.path.insert(0, str(ROOT / "tools/m4-crt-heap-carry"))
    import merge_x87

    source, merged = merge_x87.transform(cfg.read_text())
    source, annotated = watch._cleanup.annotate(source)
    source, strict = watch._cleanup.strict_x87(source)
    if not strict["strict_applied"]:
        raise RuntimeError("Production strict FP did not apply")
    stats = {}
    source = (watch.watched_flat_mem if watching else watch._cleanup.flat_mem)(source, stats)
    if watching and stats["flat_watch_unhandled_count"]:
        raise RuntimeError("Uncovered guest memory calls")
    ir = OUT / "watched.ll"
    ir.write_text(source)
    support = OUT / "observer.cpp"
    support.write_text(
        """#include <iostream>
#include <stdexcept>
#include <cstdlib>
#include <cstring>
static unsigned long long reads=0,writes=0;
extern "C" void mw34_projection_flat_access(void*state,void*token,unsigned address,unsigned size,unsigned write)noexcept(false){
 alignas(16) unsigned char saved[512];__asm__ volatile("fxsave64 %0":"=m"(saved)::"memory");
 try{
  if(!state||!token)throw std::runtime_error("Explicit noalias observer identity missing");
  unsigned pc;std::memcpy(&pc,static_cast<unsigned char*>(state)+2472,4);
  unsigned offset=(address-0x72f41cU)%32;
  unsigned expected_pc=offset==0?0x5409a9U:offset==4?0x5409bdU:0x540995U;
  if(!write||size!=4||offset>8||pc!=expected_pc)throw std::runtime_error("Observer did not see original noalias State PC");
  unsigned payload;std::memcpy(&payload,static_cast<unsigned char*>(token)+address,4);
  if((payload&0x7f800000U)==0x7f800000U)throw std::runtime_error("Observed original output is nonfinite");
  if(write)++writes;else++reads;
  // Deliberately change the FP environment; the runtime-style wrapper must
  // restore it before the next constrained original FP operation.
  unsigned short altered=0x27f;__asm__ volatile("fldcw %0"::"m"(altered):"memory");
  __asm__ volatile("fnclex":::"memory");
 }catch(...){__asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");throw;}
 __asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");
}
struct Report{~Report(){if(!writes){std::cerr<<"No watched original writes executed\\n";std::abort();}std::cout<<"Optimized original watcher writes="<<writes<<" reads="<<reads<<" (projection body reads camera data outside TL)\\n";}}report;
"""
    )
    if not watching:
        support.write_text(
            support.read_text()
            .replace("if(!writes){", "if(writes){")
            .replace(
                "No watched original writes executed", "Unexpected watcher in unwatched fixture"
            )
        )
    # Include the runtime gate's upper count limit in this private fixture copy.
    fixture = OUT / "fixture.cpp"
    fixture_text = (ROOT / "tools/remaster-launcher/test_projection_loop.cpp").read_text()
    for old, new in [
        ("n>64", "n>128"),
        ("1U,2U,3U,4U,64U", "1U,2U,3U,4U,64U,128U"),
        ("initial.data(),65)", "initial.data(),129)"),
    ]:
        if fixture_text.count(old) != 1:
            raise ValueError("Original fixture count contract changed: " + old)
        fixture_text = fixture_text.replace(old, new)
    fixture.write_text(fixture_text)
    script = OUT / "run.ps1"
    script.write_text(
        """$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
"""
        + f"""& '{LLVM/'opt.exe'}' '-passes=default<O2>' '{ir}' -o '{OUT/'optimized.bc'}'
if($LASTEXITCODE){{throw 'Original fixture first optimization failed'}}
& '{LLVM/'opt.exe'}' '-passes=dse,gvn,dse,instcombine<no-verify-fixpoint>,simplifycfg,dse' '{OUT/'optimized.bc'}' -o '{OUT/'extra.bc'}'
if($LASTEXITCODE){{throw 'Original fixture extra DSE failed'}}
& '{LLVM/'clang.exe'}' -O2 -c '{OUT/'extra.bc'}' -o '{OUT/'loop.obj'}'
if($LASTEXITCODE){{throw 'Optimized loop compile failed'}}
& '{LLVM/'llvm-objcopy.exe'}' --redefine-sym mw34_attach_projection_fixture_body=mw34_projection_fixture '{OUT/'loop.obj'}'
if($LASTEXITCODE){{throw 'Fixture symbol rename failed'}}
& '{LLVM/'clang-cl.exe'}' /nologo /std:c++20 /MD /EHsc /O2 /c '{support}' '/Fo:{OUT/'observer.obj'}'
if($LASTEXITCODE){{throw 'FP-preserving observer compile failed'}}
& '{LLVM/'clang-cl.exe'}' /nologo /std:c++20 /MD /EHsc /O2 '{fixture}' '/Fe:{OUT/'fixture.exe'}' '/Fo:{OUT/'fixture.obj'}' /link '{OUT/'loop.obj'}' '{OUT/'observer.obj'}'
if($LASTEXITCODE){{throw 'Optimized fixture link failed'}}
Set-Location '{OUT}'
& '{OUT/'fixture.exe'}'
exit $LASTEXITCODE
"""
    )
    run = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True,
        text=True,
    )
    (OUT / "run.log").write_text(run.stdout + run.stderr)
    result = dict(
        exit_code=run.returncode,
        loop="0x540985",
        watching=watching,
        original_sha256=original.SHA,
        cleanup=cleanup,
        merge=merged,
        annotate=annotated,
        strict=strict,
        watch=stats,
    )
    files = [
        Path(__file__),
        Path(original.__file__),
        Path(watch.__file__),
        watch._path,
        ROOT / "tools/m4-crt-heap-carry/merge_x87.py",
        ROOT / "tools/remaster-launcher/test_projection_loop.cpp",
        fixture,
        ir,
        support,
        LLVM / "clang.exe",
        LLVM / "opt.exe",
    ]
    result["pins"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
    }
    (OUT / "closure.json").write_text(json.dumps(result, indent=2))
    print(run.stdout + run.stderr)
    print(json.dumps(result, indent=2))
    raise SystemExit(run.returncode)


if __name__ == "__main__":
    main()
