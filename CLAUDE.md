# Current project direction

Before changing files, read `AGENTS.md` and `docs/github-workflow.md`. The
owner's October 27, 2026 PR workflow is a standing project rule for every task,
including documentation, fixes, tests, build scripts and release/version changes.

Create a topic branch from current `origin/develop` (`codex/<topic>` is the
default for Codex; other contributors may use a descriptive topic prefix), and
open a feature/fix PR into `develop`. Releases reach `main` through a separate
`develop` -> `main` PR. Never push directly or force-push to either shared branch.
Do not merge PRs or enable auto-merge unless the owner explicitly requests it.
Task-scoped commits and PR creation are authorized for requested work; preserve
unrelated work and keep original media/generated game code local. These rules
supersede older task-specific commit restrictions. At handoff, report the PR
URL, checks and remaining limitations. Normal published builds use merged `main`.

Read `docs/faithful-modernization-plan.md`, `docs/roadmap.md` and
`docs/m4-claude-work-review-2026-10-11.md` before choosing implementation work.
The execution-first strategy was authorized on2026-10-11: preserve original
MW3 gameplay through recompilation, integrate modern platform services/Vulkan,
and advance native host -> live menu -> live Training. Do not restart as a remake.

Keep existing acceptance criteria and evidence intact. Last verified count is
131/144; probes, replay and original-game hooks do not grant native-game credit.
The detailed acceptance lane is retained in `docs/m4-execution-plan-r14.md`, but
it is not the sole implementation queue. Legacy priority text is historical
where it conflicts with the current strategy; guest ABI/FP/resource contracts
and required initialization effects still apply.

Inspect current process identities before expensive work. Protect the existing
controls composer/watcher and never open active SQLite or duplicate a long job.
Use admissionv2 after actual successful closure and independently review the
post-composer chain. Preserve uncommitted work and other graphics/asset writers.

State the execution boundary advanced by each change and run narrow meaningful
checks. Add no verifier/report layer without an identified missing criterion or
concrete defect. Fail unknown required services visibly; no AFTER seeding or fake
API success. No production interpreter/original-code fallback is authorized.

Read `CONTRIBUTING.md` and `docs/legal.md`; original media and generated game
code stay local. Full continuation instructions are in
`docs/claude-m4-continuation-handoff.md`. Follow the standing PR workflow above
for task-scoped commits; do not include unrelated files.
