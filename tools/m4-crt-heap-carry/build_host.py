"""Build maintained host sources without lifting or linking translated objects.

The existing translated DLL is a local, integrity-checked dependency. Its import
and export names describe the host/DLL seam; LLVM regenerates the import library.
No original image is executed and no generated game object enters the repository.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GAME_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
SYMBOL = re.compile(r"[A-Za-z_][A-Za-z0-9_.$]*\Z")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_symbols(text):
    """Parse the pinned llvm-readobj COFF text format, rejecting unknown seams."""
    exported = []
    imported = []
    for block in re.findall(r"^Export \{\n(.*?)^\}", text, re.M | re.S):
        names = re.findall(r"^  Name: (\S+)$", block, re.M)
        require(len(names) == 1, "Malformed native export record")
        exported.extend(names)
    for block in re.findall(r"^Import \{\n(.*?)^\}", text, re.M | re.S):
        module = re.findall(r"^  Name: (\S+)$", block, re.M)
        require(module == ["entry_commandline.exe"], "Unexpected translated DLL import module")
        symbols = re.findall(r"^  Symbol: (\S+) \(\d+\)$", block, re.M)
        require(len(symbols) == len(re.findall(r"^  Symbol:", block, re.M)),
                "Unnamed or malformed translated DLL import")
        imported.extend(symbols)
    for names in (exported, imported):
        require(0 < len(names) < 65535, "Missing or excessive native seam symbols")
        require(len(set(names)) == len(names), "Duplicate native seam symbol")
        require(all(SYMBOL.fullmatch(name) for name in names), "Unsafe native seam symbol")
    return sorted(exported), sorted(imported)


def write_definition(path, library, symbols):
    path.write_text("LIBRARY " + library + "\nEXPORTS\n" + "\n".join(symbols) + "\n",
                    encoding="utf-8")


def source_pins():
    return {path.relative_to(HERE / "host").as_posix(): sha(path)
            for path in sorted((HERE / "host").rglob("*")) if path.is_file()}


def run(command, output, label, cwd=None):
    result = subprocess.run(list(map(str, command)), cwd=cwd, capture_output=True)
    (output / (label + ".stdout")).write_bytes(result.stdout)
    (output / (label + ".stderr")).write_bytes(result.stderr)
    require(result.returncode == 0, f"{label} failed; inspect {output / (label + '.stderr')}")
    return result.stdout.decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "runtime", "remill-include", "vulkan-include", "llvm", "cmake", "ninja", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    require(sys.platform == "win32", "Windows x64 is required")
    require(1 <= args.jobs <= 32, "Use 1 to 32 build workers")
    game = args.game.resolve(strict=True)
    runtime = args.runtime.resolve(strict=True)
    module = runtime / "bin/MW3Translated.dll"
    manifest = json.loads((runtime / "runtime.json").read_text(encoding="utf-8-sig"))
    pin = manifest["files"]["bin/MW3Translated.dll"]
    require(module.stat().st_size == pin["bytes"] and sha(module) == pin["sha256"],
            "Translated module differs from the supplied runtime manifest")
    original = next((p for p in game.iterdir() if p.name.lower() == "mech3.exe"), None)
    require(original is not None and sha(original) == GAME_SHA, "Supported original MW3 1.2 installation required")
    dependencies = json.loads((HERE / "host-dependencies.json").read_text())
    for name, directory in (("remill", args.remill_include), ("vulkan", args.vulkan_include)):
        for relative, digest in dependencies[name]["files"].items():
            path = directory / relative
            require(path.is_file() and sha(path) == digest, f"Pinned {name} header mismatch: {relative}")
    pins = source_pins()
    expected = json.loads((HERE / "host-source-manifest.json").read_text())["files"]
    changed = sorted(set(pins) ^ set(expected) | {name for name in pins.keys() & expected.keys()
                                               if pins[name] != expected[name]["sha256"]})
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if args.release:
        require(not changed and not dirty, "Release requires clean committed source matching its manifest")
    output = args.output.resolve()
    require(not output.exists(), "Use a fresh output directory")
    require(not (HERE / "host").is_relative_to(output) and not output.is_relative_to(HERE),
            "Build output must stay outside maintained source")
    output.mkdir(parents=True)
    compiler = args.llvm / "clang-cl.exe"
    version = run([compiler, "--version"], output, "compiler-version")
    require("clang version 21.1.8" in version, "Use LLVM clang-cl 21.1.8")
    text = run([args.llvm / "llvm-readobj.exe", "--coff-exports", "--coff-imports", module],
               output, "translated-symbols")
    exported, imported = parse_symbols(text.replace("\r\n", "\n"))
    write_definition(output / "translated.def", "MW3Translated.dll", exported)
    write_definition(output / "host.def", "entry_commandline.exe", imported)
    run([args.llvm / "llvm-lib.exe", "/machine:x64", "/def:" + str(output / "translated.def"),
         "/out:" + str(output / "translated.lib")], output, "import-library")
    configure = [args.cmake, "-S", HERE / "native", "-B", output / "build", "-G", "Ninja",
                 "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=" + str(compiler),
                 "-DCMAKE_MAKE_PROGRAM=" + str(args.ninja), "-DMW34_HOST_ONLY=ON",
                 "-DMW34_REMILL_INCLUDE=" + str(args.remill_include.resolve()),
                 "-DMW34_VULKAN_INCLUDE=" + str(args.vulkan_include.resolve()),
                 "-DMW34_TRANSLATED_LIBRARY=" + str(output / "translated.lib"),
                 "-DMW34_HOST_DEFINITION=" + str(output / "host.def"),
                 "-DMW34_GAME_DIRECTORY=" + game.as_posix()]
    run(configure, output, "configure")
    print("Building seven maintained host objects; translated DLL is unchanged.", flush=True)
    run([args.cmake, "--build", output / "build", "--parallel", str(args.jobs)], output, "compile")
    executable = output / "build/entry_commandline.exe"
    require(executable.is_file(), "Host executable was not linked")
    shutil.copyfile(executable, output / "entry_commandline.exe")
    shutil.copyfile(module, output / "MW3Translated.dll")
    for name in ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"):
        path = runtime / "bin" / name
        if path.is_file():
            identity = manifest["files"]["bin/" + name]
            require(sha(path) == identity["sha256"], "Runtime support library integrity failure")
            shutil.copyfile(path, output / name)
    require(pins == source_pins() and sha(module) == pin["sha256"], "Source/dependency changed while building")
    ninja_deps = run([args.ninja, "-C", output / "build", "-t", "deps"], output, "dependencies")
    repo_pins = {}
    for line in ninja_deps.splitlines():
        path = Path(line.strip())
        if path.is_file() and path.resolve().is_relative_to(ROOT):
            repo_pins[path.resolve().relative_to(ROOT).as_posix()] = sha(path)
    for path in (HERE / "native").glob("*.cmake"):
        repo_pins[path.relative_to(ROOT).as_posix()] = sha(path)
    for path in (HERE / "native/CMakeLists.txt", HERE / "build_host.py", HERE / "build_host.ps1",
                 HERE / "host-source-manifest.json", HERE / "host-dependencies.json"):
        repo_pins[path.relative_to(ROOT).as_posix()] = sha(path)
    receipt = dict(schema_version=1, github_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   source_dirty=bool(dirty), changed_source_files=changed, host_source_pins=pins,
                   repository_source_pins=dict(sorted(repo_pins.items())), original_game_sha256=GAME_SHA,
                   translated_module_sha256=pin["sha256"], translated_module_unchanged=True,
                   generation_required=False, host_objects=7, translated_object_inputs=0,
                   executable_sha256=sha(output / "entry_commandline.exe"),
                   tool_pins={tool:sha(args.llvm / tool) for tool in ("clang-cl.exe", "lld-link.exe", "llvm-lib.exe", "llvm-readobj.exe")},
                   dependency_header_pins=dependencies,
                   runtime_version=manifest["version"], windows_signed=False)
    (output / "source-snapshot.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Built {output / 'entry_commandline.exe'}; recorded {len(pins)} host files and {len(repo_pins)} repository dependencies.")


if __name__ == "__main__":
    main()
