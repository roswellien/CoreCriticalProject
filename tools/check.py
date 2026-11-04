"""Run every check a pull request must pass, the same way CI runs them.

Usage, from the repository root:
    python tools/check.py --setup          install the pinned tools the checks need
    python tools/check.py                  build, CTest, C++ format check and style check
    python tools/check.py --only style     run only the named checks (repeatable)
    python tools/check.py --area launcher  add an area's own checks to the run

Each check streams its own output, then the run ends with one summary line per check:
"<check>: pass", "<check>: fail" or "<check>: not run (<reason>; <fix>)". Paste that
summary into the Validation section of the PR description.

Exit codes:
    0  every selected check passed
    1  a check failed
    2  a check didn't run (a missing tool, the wrong version, no build yet). This wins
       over 1, as in tools/style/check_style.py: the run is incomplete until setup is
       fixed, and the summary still lists every failure.

--setup installs only into ignored folders (tools/style/.venv, tools/style/node_modules,
local/) and only what the selected checks need. A plain run never uses the network.
The .NET SDK, PowerShell, Node.js, CMake and Visual Studio are not installed here; a check
that needs one that is missing says where to get it.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STYLE_DIR = REPO_ROOT / "tools/style"
BUILD_DIR = REPO_ROOT / "build/default"
VENV_DIR = STYLE_DIR / ".venv"
SDL3_FOLDER_PATTERN = "local/third-party/SDL3-*"

EXIT_CLEAN = 0
EXIT_FAILED = 1
EXIT_NOT_RUN = 2

PASS = "pass"
FAIL = "fail"
NOT_RUN = "not run"

INSTALL_LINKS = {
    "cmake": "https://cmake.org/download/",
    "dotnet": "https://dotnet.microsoft.com/download/dotnet/8.0",
    "npm": "https://nodejs.org/en/download",
    "pwsh": "https://learn.microsoft.com/powershell/scripting/install/installing-powershell",
    "visual-studio": "https://visualstudio.microsoft.com/downloads/ (Desktop development with C++)",
}
SETUP_FIX = "run python tools/check.py --setup"


@dataclass
class Result:
    """What one check or setup step ended with; detail explains a "not run"."""

    name: str
    status: str
    detail: str = ""

    def summary_line(self) -> str:
        if self.status == NOT_RUN:
            return f"{self.name}: {NOT_RUN} ({self.detail})"
        return f"{self.name}: {self.status}"


def is_windows() -> bool:
    return os.name == "nt"


def run_command(command: list[str]) -> int:
    """Run a command from the repository root, streaming its output; return its exit code."""
    print(f"$ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def find_on_path(name: str) -> str | None:
    return shutil.which(name)


def pinned_clang_format() -> str | None:
    """The clang-format installed by --setup. Never one from PATH, whose version may differ."""
    scripts = "Scripts" if is_windows() else "bin"
    return shutil.which("clang-format", path=str(VENV_DIR / scripts))


def visual_studio_found() -> bool:
    """Whether vswhere, at its standard path, reports a Visual Studio with the x64 C++ tools.

    CMake's Visual Studio generator (-A x64) finds MSVC by itself, as the CI Windows job
    does, so no developer shell is needed; this only tells "not installed" apart from a
    real configure failure.
    """
    program_files = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere = Path(program_files) / "Microsoft Visual Studio/Installer/vswhere.exe"
    if not vswhere.is_file():
        return False
    completed = subprocess.run(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


def sdl3_runtime_found() -> bool:
    return any(REPO_ROOT.glob(SDL3_FOLDER_PATTERN))


def configure_command(clang_format: str | None) -> list[str]:
    """The cmake configure CI uses on this OS.

    MW34_CLANG_FORMAT is passed on every configure, because find_program in CMakeLists.txt
    keeps whatever an earlier configure cached.
    """
    command = ["cmake", "--preset", "default"]
    command += ["-A", "x64"] if is_windows() else ["-DCMAKE_CXX_COMPILER=clang++"]
    if clang_format:
        command.append(f"-DMW34_CLANG_FORMAT={clang_format}")
    return command


def missing(tool: str) -> str:
    return f"{tool} not found; install it from {INSTALL_LINKS[tool]}"


def configure_problem() -> str:
    """Why configure can't run here, or "" when it can."""
    if find_on_path("cmake") is None:
        return missing("cmake")
    if is_windows() and not visual_studio_found():
        return "Visual Studio C++ x64 tools not found; install " + INSTALL_LINKS["visual-studio"]
    return ""


def pass_or_fail(name: str, exit_code: int) -> Result:
    return Result(name, PASS if exit_code == 0 else FAIL)


# ---------------------------------------------------------------------------------------
# The checks, in the order they run
# ---------------------------------------------------------------------------------------


def check_build() -> Result:
    problem = configure_problem()
    if problem:
        return Result("build", NOT_RUN, problem)
    if run_command(configure_command(pinned_clang_format())) != 0:
        return Result("build", FAIL)
    return pass_or_fail("build", run_command(["cmake", "--build", "--preset", "default"]))


def check_ctest() -> Result:
    if find_on_path("ctest") is None:
        return Result("ctest", NOT_RUN, missing("cmake"))
    if not (BUILD_DIR / "CTestTestfile.cmake").is_file():
        return Result("ctest", NOT_RUN, "no build; run the build check first")
    return pass_or_fail("ctest", run_command(["ctest", "--preset", "default"]))


def check_format() -> Result:
    clang_format = pinned_clang_format()
    if clang_format is None:
        return Result("format-check", NOT_RUN, f"pinned clang-format not installed; {SETUP_FIX}")
    problem = configure_problem()
    if problem:
        return Result("format-check", NOT_RUN, problem)
    if run_command(configure_command(clang_format)) != 0:
        return Result("format-check", FAIL)
    target = ["cmake", "--build", str(BUILD_DIR), "--target", "format-check"]
    return pass_or_fail("format-check", run_command(target))


def check_style() -> Result:
    exit_code = run_command([sys.executable, "tools/style/check_style.py"])
    if exit_code in (0, 1):
        return pass_or_fail("style", exit_code)
    # check_style.py exits 2 when a checker is missing, the wrong version or crashed.
    return Result("style", NOT_RUN, f"a style checker is missing or failed; {SETUP_FIX}")


def check_launcher_wpf() -> Result:
    if find_on_path("dotnet") is None:
        return Result("launcher-wpf", NOT_RUN, missing("dotnet"))
    if not sdl3_runtime_found():
        fix = f"{SETUP_FIX} --area launcher"
        return Result("launcher-wpf", NOT_RUN, f"SDL3 controller runtime not fetched; {fix}")
    command = ["dotnet", "run", "--project", "tools/mw3-remaster-launcher-tests", "-c", "Release"]
    return pass_or_fail("launcher-wpf", run_command(command))


def check_launcher_dispatch() -> Result:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tools/remaster-launcher"]
    command += ["-p", "test_launcher_dispatch.py"]
    return pass_or_fail("launcher-dispatch", run_command(command))


@dataclass(frozen=True)
class Check:
    name: str
    run: Callable[[], Result]
    # What --setup installs for this check: "venv", "npm", "psscriptanalyzer", "sdl3".
    needs: tuple[str, ...] = ()
    windows_only: bool = False


CHECKS = (
    Check("build", check_build),
    Check("ctest", check_ctest),
    Check("format-check", check_format, needs=("venv",)),
    Check("style", check_style, needs=("venv", "npm", "psscriptanalyzer")),
    Check("launcher-wpf", check_launcher_wpf, needs=("sdl3",), windows_only=True),
    Check("launcher-dispatch", check_launcher_dispatch),
)
DEFAULT_CHECKS = ("build", "ctest", "format-check", "style")
AREAS = {"launcher": ("launcher-wpf", "launcher-dispatch")}


def selected_checks(only: list[str] | None, areas: list[str] | None) -> list[Check]:
    """The checks to run, in table order, without Windows-only ones elsewhere."""
    names = set(only or DEFAULT_CHECKS)
    for area in areas or []:
        names.update(AREAS[area])
    return [
        check
        for check in CHECKS
        if check.name in names and (is_windows() or not check.windows_only)
    ]


def overall_exit_code(results: list[Result]) -> int:
    if any(result.status == NOT_RUN for result in results):
        return EXIT_NOT_RUN
    if any(result.status == FAIL for result in results):
        return EXIT_FAILED
    return EXIT_CLEAN


# ---------------------------------------------------------------------------------------
# --setup
# ---------------------------------------------------------------------------------------


def setup_venv() -> Result:
    """Ruff and clang-format, hash-pinned, into tools/style/.venv."""
    if not VENV_DIR.is_dir():
        venv_created = run_command([sys.executable, "-m", "venv", str(VENV_DIR)]) == 0
        if not venv_created:
            return Result("setup venv", FAIL)
    scripts = "Scripts" if is_windows() else "bin"
    python = str(VENV_DIR / scripts / "python")
    requirements = str(STYLE_DIR / "requirements.txt")
    install = [python, "-m", "pip", "install", "--require-hashes", "-r", requirements]
    return pass_or_fail("setup venv", run_command(install))


def setup_npm() -> Result:
    """Prettier, lockfile-pinned, into tools/style/node_modules."""
    npm = find_on_path("npm")
    if npm is None:
        return Result("setup npm", NOT_RUN, missing("npm"))
    return pass_or_fail("setup npm", run_command([npm, "ci", "--prefix", "tools/style"]))


def setup_psscriptanalyzer() -> Result:
    """PSScriptAnalyzer, at the version check_powershell.ps1 pins."""
    if find_on_path("pwsh") is None:
        return Result("setup psscriptanalyzer", NOT_RUN, missing("pwsh"))
    command = ["pwsh", "-NoProfile", "-File", "tools/style/check_powershell.ps1"]
    return pass_or_fail("setup psscriptanalyzer", run_command(command + ["-Mode", "Install"]))


def setup_sdl3() -> Result:
    """The SDL3 controller runtime the WPF launcher tests load, into local/."""
    if find_on_path("pwsh") is None:
        return Result("setup sdl3", NOT_RUN, missing("pwsh"))
    script = "tools/mw3-remaster-launcher/fetch_controller_runtime.ps1"
    return pass_or_fail("setup sdl3", run_command(["pwsh", "-NoProfile", "-File", script]))


SETUP_STEPS: dict[str, Callable[[], Result]] = {
    "venv": setup_venv,
    "npm": setup_npm,
    "psscriptanalyzer": setup_psscriptanalyzer,
    "sdl3": setup_sdl3,
}


def setup_steps_for(checks: list[Check]) -> list[str]:
    needed = {need for check in checks for need in check.needs}
    return [step for step in SETUP_STEPS if step in needed]


# ---------------------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------------------


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        action="append",
        choices=[check.name for check in CHECKS],
        help="run only this check (repeatable)",
    )
    parser.add_argument(
        "--area", action="append", choices=sorted(AREAS), help="add an area's checks"
    )
    parser.add_argument(
        "--setup", action="store_true", help="install the pinned tools the checks need"
    )
    return parser.parse_args(argv)


def run_and_summarize(steps: list[Callable[[], Result]]) -> int:
    results = []
    for step in steps:
        results.append(step())
    print("\nSummary:")
    for result in results:
        print(result.summary_line())
    return overall_exit_code(results)


def main(argv: list[str]) -> int:
    arguments = parse_arguments(argv)
    checks = selected_checks(arguments.only, arguments.area)
    if arguments.setup:
        steps = [SETUP_STEPS[name] for name in setup_steps_for(checks)]
        if not steps:
            print("Nothing to install for the selected checks.")
            return EXIT_CLEAN
        return run_and_summarize(steps)
    return run_and_summarize([check.run for check in checks])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
