# Current project direction

Follow the Required GitHub PR workflow below and `docs/github-workflow.md`. Read
before choosing work:
- `docs/renderer-feature-parity.md` — MW3-RE work packages, gates and pickup rules.
- `docs/roadmap.md` — active tracks and feature plans.
- `docs/faithful-modernization-plan.md` — fidelity rules and host/service contracts.

MW3-RE (`runtime/mw3-re/`) is the shipping native runtime; the retired recompiled
runtime is a reference only. Preserve original MW3 gameplay with modern services,
Vulkan and opt-in Core Critical features; do not restart as a remake.

Follow `docs/project-status-reporting.md` in updates, PRs and releases: report live
native behavior, fidelity coverage, defects and validation. Probes, saved replay
and original-binary hooks aren't live gameplay. Guest ABI, floating-point
contracts, resource lifetimes and required initialization effects apply.

Check running processes before heavy builds, tests or captures; don't duplicate
long jobs or contend with active builds or captures. Preserve uncommitted work and
coordinate with graphics or asset writers.

State the execution boundary advanced and run narrow checks. Don't add a new
verifier or report tool unless it closes a named missing check or fixes a concrete
defect. Fail unknown required services visibly; never stub fake API success or
pre-seed expected output state. No runtime interpreter or original-binary fallback.

Follow `CODE_STYLE.md`, `docs/legal.md` and `CONTRIBUTING.md` ("Tests" and
"Definition of done"). Keep original media and generated code local; never commit
private reports, build outputs, credentials or signing material.

## Required GitHub PR workflow

Owner direction, 2026-10-27: use pull requests for all new changes. This remains
mandatory until the owner explicitly changes it, including for documentation,
tests, build scripts, hotfixes and release/version changes. It supersedes older
task-specific commit instructions; it does not expand a task's file scope.

- `main` is the stable release branch; `develop` is the shared integration branch.
- Start each task on a `<username>/<type>/<issue>-<topic>` branch (see "Names
  and formats" in `docs/github-workflow.md`) from current `origin/develop`,
  preferably in an isolated worktree when other work is uncommitted.
- Task-scoped commits, feature-branch pushes and PR creation are authorized as
  part of implementing a requested change. Commit only that task's authored
  files; preserve unrelated changes and keep generated code/media local. Keep
  unrelated tasks in separate PRs.
- Open feature/fix PRs against `develop`. Promote reviewed integration work
  through a separate `develop` -> `main` release PR. If a prior task's PR has
  already merged, start a new branch and PR rather than extending its old branch.
- Never push directly or force-push to `main` or `develop`. Do not merge PRs or
  enable auto-merge unless the user explicitly requests it.
- Run relevant checks and describe behavior, validation and release impact in
  each PR. Build normal playtest releases from merged `main`, recording its SHA.
  An explicitly requested development preview must be identified as such.
- Track each task as an issue on the project board, and move its card as the
  task starts and its PR opens (see "Project board" in `docs/github-workflow.md`).
- Report the topic branch, PR URL, checks and remaining limitations at handoff.
  A PR awaiting review is not a merged or published change. Synchronize changes
  from `main` back into `develop` through a synchronization PR when needed.

Current private-repository plan restrictions prevent GitHub branch-protection
enforcement; this workflow still applies, and the limitation doesn't authorize
making the repository public.

## Where to find more

- `docs/github-workflow.md`: the full PR, issue, project board and release workflow.
- `docs/github-workflow.md` "Plan and review": the flow every change follows before
  its PR; the `core-critical-*` skills run each stage.
- `CONTRIBUTING.md`: what every contribution and PR must include.
- `CODE_STYLE.md`: how to write and format code.
- `docs/legal.md`: what may and may not be distributed.
- `docs/project-status-reporting.md`: how to report progress and what not to claim.
- `docs/release-filenames.md`: required installer and update filenames; follow it
  before naming or publishing any release file.
- `docs/roadmap.md`: what is planned next.
- `docs/code-guide.md`: how the code is organized and how it should explain itself.
- `.agents/skills/`: shared agent skills. `.claude/skills/` is a generated copy for
  Claude Code; never edit it by hand, and run `python tools/agents/sync_skills.py`
  after changing a skill.
- `.githooks/`: commit and push checks, including formatting; turn them on once per
  clone with `git config core.hooksPath .githooks`.
- `runtime/mw3-re/docs/arena.md`: the AI arena, for testing AI changes on bot
  matches; `tools/arena-runner/run_batch.py` runs a batch with no window.
- `docs/archive/claude-m4-continuation-handoff.md`: full continuation instructions.

Agent rules live only in this file. `CLAUDE.md`, `GEMINI.md` and
`.github/copilot-instructions.md` point here; edit this file instead.

## Commands and layout

Fresh checkout, from the root unless noted. Presets: `CMakePresets.json`.
Detail: `docs/code-guide.md`.
One command runs the checks a PR must pass on Windows or Linux: build, CTest,
the pinned C++ format check and the style check. `--setup` installs the pinned
tools into ignored folders once per checkout; `--area launcher` adds the WPF
launcher and launcher dispatch checks (authored fixtures, no game install).
On Windows it uses Visual Studio's C++ x64 tools; no developer shell needed.
It ends with a pass, fail or not run line per check for the PR's Validation
section. The exact commands it runs are in `tools/check.py`.

```sh
python tools/check.py --setup
python tools/check.py
python tools/check.py --setup --area launcher
python tools/check.py --area launcher
```
Launcher publish, from the root on Windows (`net8.0-windows`), after
`python tools/check.py --setup --area launcher`. Ignored `local/` output; not a release.

```sh
dotnet publish tools/mw3-remaster-launcher/MW3RemasterLauncher.csproj -c Release -r win-x64 --self-contained true -o local/launcher-publish
```
Website, from `website/`. Open http://127.0.0.1:4173/.

```sh
python build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```
Installer, signing, upload, the update feed and Cloudflare deploy are
maintainer-only (`docs/launcher-and-website-release.md`). Issue 40 tracks
moving those steps into the repo.
CTest and the checks above need no original installation. These do, and they
are not asset-free CI tests; keep inputs and output local:
`tools/analysis/extract_mw3_leaf.py` and dated `tools/m4-*` / `tools/x87-*`
comparisons that take a Mech3.exe path; `launchers/Setup Mod Tools.cmd` with
`--game-root` and `games/mw3/mod-tools/editor/core/extract_assets_3d.py`;
`tools/mw3-remaster-launcher-tests` commands `--verify-original`,
`--install-original-source`, `--install-original-iso`, `--prepare-support` and
`--launch-installed-trial`.
Layout: `.agents` shared skills (edit only here); `.claude` generated skill
copy (do not edit; run `python tools/agents/sync_skills.py`); `.github`
workflows, forms and templates; `cmake` shared CMake modules; `docs` plans and
evidence; `games` MW3, Pirate's Moon and Mod Tools; `launchers` Windows play
and setup shortcuts; `mods` authored map packs, not original media; `recomp`
translator and patches, generated game code under ignored `recomp/generated/`;
`runtime` asset-free C++ host services; `tests` asset-free CTest fixtures;
`tools` launcher, analysis, lifting, style and historical evidence; `website`
static site (`website/build.py`).
