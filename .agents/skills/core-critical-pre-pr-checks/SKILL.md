---
name: core-critical-pre-pr-checks
description: Run this repository's build, tests, C++ formatting check and style check before opening or updating a pull request, then record each result and remaining limit in the PR template's Validation section. Use whenever a change is ready for a PR or a PR branch gets new commits.
---

# Pre-PR checks

Run these from the repository root on the PR branch. Each doc named here owns its
commands; where it and this list disagree, follow the doc.

1. **Build and test**, as in "Build the asset-free runtime" in `README.md`:
   - `cmake --preset default` (on Windows, from a Visual Studio developer shell,
     add `-A x64`)
   - `cmake --build --preset default`
   - `ctest --preset default`
2. **C++ formatting:** `cmake --build build/default --target format-check`. The
   target exists only when CMake found clang-format; if it is missing, configure
   again with `-DMW34_CLANG_FORMAT=<path to clang-format>`. The pinned version is
   in `tools/style/README.md`.
3. **Style:** `python tools/style/check_style.py` (one-time setup in
   `tools/style/README.md`). Before committing, run it with `--fix`, as
   `CODE_STYLE.md` says. Languages not yet switched on only report counts; note
   any new findings in the files you changed.
4. **Area checks:** if the changed area's own README lists checks (for example the
   launcher checks in `tools/mw3-remaster-launcher-tests`), run those too.

Then fill in the Validation section of the PR description
(`.github/pull_request_template.md`), as "Issues and pull requests" in
`CONTRIBUTING.md` asks:

- Each check you ran, with its result (for example "ctest: 23 of 23 passed").
- Each check you couldn't run here, marked not run with the reason (a missing
  tool, the wrong OS). Never list it as passed.
- Every remaining limit of the change.
- Tick the template's checkboxes only when they are true.

Claim no more than the checks show; `docs/project-status-reporting.md` says what
a build or test does and doesn't establish.
