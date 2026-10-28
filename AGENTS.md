# Current project direction

Before changing files, follow the Required GitHub PR workflow below and read
`docs/github-workflow.md`. It is a standing project rule, not a one-session plan.

Read `docs/faithful-modernization-plan.md`, `docs/roadmap.md` and
`docs/archive/m4-claude-work-review-2026-10-11.md` before choosing implementation work.
The execution-first strategy was authorized on 2026-10-11: preserve original
MW3 gameplay through recompilation, integrate modern platform services/Vulkan,
and advance native host -> live menu -> live Training. Do not restart as a remake.

Follow `docs/project-status-reporting.md` when reporting progress in updates,
PRs and release notes. Probes, replay and original-game hooks do not establish
live native gameplay. Guest ABI/FP, resource contracts and required
initialization effects still apply.

Inspect current process identities before expensive work. Protect the existing
controls composer/watcher and never open active SQLite or duplicate a long job.
The historical post-composer/admission/review chain applies when that audit is
explicitly resumed, not to routine tasks. Preserve uncommitted work and other
graphics/asset writers.

State the execution boundary advanced by each change and run narrow meaningful
checks. Add no verifier/report layer without an identified missing criterion or
concrete defect. Fail unknown required services visibly; no AFTER seeding or fake
API success. No production interpreter/original-code fallback is authorized.

Read `CONTRIBUTING.md` and `docs/legal.md`; original media and generated game
code stay local, and private reports, build outputs, credentials and signing
material are never committed. Full continuation instructions are in
`docs/archive/claude-m4-continuation-handoff.md`.
Follow `CODE_STYLE.md` when writing or changing code.

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
- Report the topic branch, PR URL, checks and remaining limitations at handoff.
  A PR awaiting review is not a merged or published change. Synchronize changes
  from `main` back into `develop` through a synchronization PR when needed.

See `docs/github-workflow.md`. Current private-repository plan restrictions
prevent GitHub branch-protection enforcement; this workflow still applies, and
the limitation doesn't authorize making the repository public.

## Where to find more

- `docs/github-workflow.md`: the full PR, issue, project board and release workflow.
- `CONTRIBUTING.md`: what every contribution and PR must include.
- `CODE_STYLE.md`: how to write and format code.
- `docs/legal.md`: what may and may not be distributed.
- `docs/project-status-reporting.md`: how to report progress and what not to claim.
- `docs/release-filenames.md`: required installer and update filenames.
- `docs/roadmap.md`: what is planned next.
- `docs/code-guide.md`: how the code is organized and how it should explain itself.

Agent rules live only in this file. `CLAUDE.md` and
`.github/copilot-instructions.md` point here; edit this file instead.
