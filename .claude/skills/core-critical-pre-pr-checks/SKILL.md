---
name: core-critical-pre-pr-checks
description: Run this repository's build, tests, C++ formatting check and style check before opening or updating a pull request, then record each result and remaining limit in the PR template's Validation section. Use whenever a change is ready for a PR or a PR branch gets new commits.
---

# Pre-PR checks

Run these from the repository root on the PR branch. Each doc named here owns its
commands; where it and this list disagree, follow the doc.

1. **Build, test, C++ formatting and style:** `python tools/check.py` (once per
   worktree, `python tools/check.py --setup` first). It runs the same checks as CI
   and ends with one pass, fail or not run line per check; exit 2 means something
   didn't run, and its line says how to fix that. Add `--area launcher` when the
   launcher changed. Before committing, run `python tools/style/check_style.py --fix`,
   as `CODE_STYLE.md` says; style languages not yet switched on only report counts,
   so run `check_style.py --verbose` and note any findings in the files you changed.
2. **Other area checks:** if the changed area's own README lists checks that
   `tools/check.py` doesn't run (for example the launcher's "Narrow checks" in
   `tools/remaster-launcher/README.md`), run those too.

Then fill in the Validation section of the PR description
(`.github/pull_request_template.md`), as "Issues and pull requests" in
`CONTRIBUTING.md` asks:

- Each check you ran, with its result (for example "ctest: 23 of 23 passed").
- Each check you couldn't run here, marked not run with the reason (a missing
  tool, the wrong OS). Never list it as passed.
- Every remaining limit of the change, and any failure that already exists on
  `develop`.
- Each item of "Definition of done" in `CONTRIBUTING.md`: the issue's acceptance
  criteria and where the change meets each, tests seen failing with their
  behavior broken, a launcher or game run (or a "Playtest <what to check>"
  issue), and a review by someone who didn't write the change.
- Keep every checkbox from the template. Tick one only when it is true; for one
  that doesn't apply, leave it unticked and say why beside it.

Claim no more than the checks show; `docs/project-status-reporting.md` says what
a build or test does and doesn't establish.
