# Contributing to MW34 RECOMP

Work on MechWarrior 3 first. Start with an observation, record its evidence,
then make the smallest change that preserves the observed behavior.

## Before starting

Use the [GitHub PR workflow](docs/github-workflow.md): create a feature branch
from `develop`, submit a PR back to `develop`, then promote a reviewed release
through a `develop` -> `main` PR. Do not push changes directly to either shared
branch. Keep unrelated work on its own branches or worktrees.

This is a standing rule for all contributors and agents, including changes to
documentation, tests, build scripts, fixes and release versions. New follow-up
work after a merged PR starts a new branch/PR. Agents may make task-scoped
commits and open PRs for requested work; PR merges require explicit owner
direction. The full guide includes branch synchronization and release steps.

Use the [code guide](docs/code-guide.md) to find the active component. Check open
issues and describe substantial changes before investing in a redesign. Bug fixes,
hardware playtest reports, Mod Tools improvements and clear documentation are
welcome. Keep a pull request focused on one behavior or one readability concern.
Do not mix a large formatting pass with gameplay or renderer changes.

Follow the [faithful modernization plan](docs/faithful-modernization-plan.md):
preserve recompiled gameplay while implementing modern platform services behind
observed contracts. State the execution boundary advanced by each implementation
and validate it narrowly. Existing acceptance gates remain strict; backend
fixtures, original-game hooks and saved-scene replay are not native gameplay.
Follow the [status reporting rule](docs/project-status-reporting.md): describe
demonstrated behavior, fidelity coverage, defects and release checks. The paused
startup-equivalence inventory is historical evidence, not routine project
progress or a prerequisite for normal development/releases.
For documentation-only changes, check links, diff and evidence consistency;
do not launch game captures or full verifier runs solely to update documents.

Read [the distribution policy](docs/legal.md) before adding files. Never submit
game executables, media, assets, memory dumps, or unreviewed generated code.
Keep user inputs under ignored `local/` (or outside the checkout), and analysis
output under ignored `reports/`. Ignore rules are a convenience, not proof that
a commit is safe: inspect `git diff --cached` before committing.

Use C++20 for the runtime and Python 3.11+ standard library for lightweight
offline analysis. The asset-free bootstrap needs no external runtime libraries;
the separate Mod Tools preview has its own pinned dependencies and setup guide.
Proposed dependencies must record license, exact version/commit, integrity
hash where available, and why an existing dependency cannot do the job.

Build and run CTest as described in the README. Tests use only project-authored
fixtures. Cover malformed PE data and boundary conditions for memory changes.
Do not add game files to CI. Run `cmake --build build/default --target format`
when clang-format is installed; `format-check` verifies formatting. Enable
`MW34_ENABLE_CLANG_TIDY` with a Ninja or Makefiles generator for optional
compiler-integrated static analysis. CMake's Visual Studio generator does not
run clang-tidy; on Windows, use Ninja from a developer command prompt.

The asset-free CMake tests, launcher tests and local original-game comparisons
have different prerequisites. State which you ran and which require private
inputs. The Mod Tools currently include local-installation integration scripts;
do not describe them as asset-free CI tests. The public setup/package path is
tracked in [release readiness](docs/public-release-readiness.md).

## Tests

Keep the test suite small and meaningful: each test should catch a failure that
no other test catches.

- Before adding a test, find the existing test for that behavior. When the new
  case has the same setup and the same check, add it as a row in that test's
  table of cases (a list of inputs and expected results the test loops over).
  Otherwise extend that test. Add a new test file only for code that has no
  test yet, and say why in the PR.
- Show that each new or changed test fails when the behavior it covers breaks:
  break the code locally, run the test, see it fail, then restore the code. Say
  so in the PR.
- Every check must be able to fail. Do not loosen a check until it passes, and
  do not write tests that only check a mock or stub.
- Remove throwaway tests written while debugging before opening the PR, unless
  they cover behavior worth keeping.
- When you find a near-copy of another test while working, merge the two in the
  same PR if that takes under about 15 minutes; otherwise file it as a
  `needs-triage` issue.
- A PR that removes or loosens a test names it and says why.

## Readable, maintainable code

Write modules around a clear responsibility and describe their entry points,
input/output formats, ownership and failure behavior. Prefer descriptive names
and small named helpers over compressed one-line control flow. Comments should
explain why a constraint exists, a binary layout, units, a lifecycle rule or an
unusual ABI/FP contract; avoid restating obvious assignments. Include enough
context that a developer can understand the code without this project's chats.

Keep unresolved guest functions named `sub_XXXXXXXX` and retain evidence-backed
addresses. Human readability does not justify invented gameplay semantics.
Preserve frozen source models, hashes and historical evidence. Refactor maintained
code with narrow checks; propose separate replacements for pinned historical tools
rather than silently formatting or renaming their source.
The day-to-day rules and style checks are in [CODE_STYLE.md](CODE_STYLE.md).

For Mod Tools, keep the original installation read-only and place caches/projects/
exports in a separate writable location. Validate identifiers, paths and sizes
before file access or process launch. Exported game archives are local derived
content; a successful export does not authorize sharing it or prove native play.

## Issues and pull requests

File issues with the repository's issue forms and follow
[Names and formats](docs/github-workflow.md#names-and-formats) for branches,
commits, PR titles and labels.

For a bug, include the component/build, OS/GPU/driver when relevant, the supported
game profile, steps to reproduce, expected result and actual result. Attach only
reviewed, redacted logs/screenshots. Never upload archives, executables, memory
dumps, saves containing original data or generated translations to an issue.

A pull request should explain the problem and resulting behavior, list meaningful
checks and their results, and identify remaining limits. For native behavior,
name the execution boundary changed and the original comparison or fixture used.
For docs, review links and claims. New dependencies need exact pins, provenance
and applicable license notices. Include notices in the package as well as source.
A PR leaves draft only once it meets the [definition of done](#definition-of-done).

Follow the project's existing license for your own contributions and identify
third-party material explicitly. This draft adds no contributor agreement or
mandatory external service. Release publication, repository visibility and any
history replacement remain maintainer decisions after review.

For findings, include executable SHA-256, RVA/VA distinction, tool and version,
method, confidence, reproducible evidence, and unresolved alternatives. Keep
unknown functions named `sub_XXXXXXXX`; only add semantic aliases with evidence.
Distinguish tests of synthetic code from validation of real game behavior.

Changes to timing, rendering, or input behavior need an original-behavior
baseline. Unknown APIs must fail explicitly; a success-returning placeholder
must never masquerade as compatibility. No remote repository or release is
created automatically by this bootstrap.

## Definition of done

Open every PR as a draft. It is ready to leave draft when:

- It lists each acceptance criterion of its issue and where the change meets
  it, or says that it doesn't (not for release or sync PRs).
- For code changes, the build, CTest and `format-check` pass locally, and the
  `style` check passes in CI. That check runs `python tools/style/check_style.py`,
  which also runs locally once its tools from
  [tools/style/README.md](tools/style/README.md) are installed. Fix C++ layout
  with the `format` CMake target, and other languages with
  `check_style.py --fix` once they are switched on in its `ENFORCED` list.
  Documentation-only changes need link, diff and evidence checks instead.
  Either way, the PR names any failure that already exists on `develop`.
- Its tests follow [Tests](#tests).
- A change a player or modder would notice has been run in the real program
  (the launcher, or the game up to the affected screen), with a log line or
  screenshot in the PR. When that isn't possible, the PR says so and a
  `needs-triage` issue titled "Playtest <what to check>" is filed for it.
  Documentation-only changes don't need a run.
- Someone who didn't write the change (a fresh agent session or another person)
  has reviewed it against its issue and these rules, and each finding is fixed
  or listed in the PR.
