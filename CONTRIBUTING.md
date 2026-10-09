# Contributing to MW34 RECOMP

Work on MechWarrior 3 first. Start with an observation, record its evidence,
then make the smallest change that preserves the observed behavior.

Read [the distribution policy](docs/legal.md) before adding files. Never submit
game executables, media, assets, memory dumps, or unreviewed generated code.
Keep user inputs under ignored `local/` (or outside the checkout), and analysis
output under ignored `reports/`. Ignore rules are a convenience, not proof that
a commit is safe: inspect `git diff --cached` before committing.

Use C++20 for the runtime and Python 3.11+ standard library for lightweight
offline analysis. No external runtime dependencies are currently required.
Proposed dependencies must record license, exact version/commit, integrity
hash where available, and why an existing dependency cannot do the job.

Build and run CTest as described in the README. Tests use only project-authored
fixtures. Cover malformed PE data and boundary conditions for memory changes.
Do not add game files to CI. Run `cmake --build build/default --target format`
when clang-format is installed; `format-check` verifies formatting. Enable
`MW34_ENABLE_CLANG_TIDY` with a Ninja or Makefiles generator for optional
compiler-integrated static analysis. CMake's Visual Studio generator does not
run clang-tidy; on Windows, use Ninja from a developer command prompt.

For findings, include executable SHA-256, RVA/VA distinction, tool and version,
method, confidence, reproducible evidence, and unresolved alternatives. Keep
unknown functions named `sub_XXXXXXXX`; only add semantic aliases with evidence.
Distinguish tests of synthetic code from validation of real game behavior.

Changes to timing, rendering, or input behavior need an original-behavior
baseline. Unknown APIs must fail explicitly; a success-returning placeholder
must never masquerade as compatibility. No remote repository or release is
created automatically by this bootstrap.
