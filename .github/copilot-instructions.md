# Copilot Instructions

## Standing project rules

Read `AGENTS.md`, `CONTRIBUTING.md`, `docs/github-workflow.md` and `docs/legal.md`
before changing this repository. The owner's October 27, 2026 PR workflow applies
to all future changes, including documentation, fixes, tests, build scripts and
release/version changes. It supersedes older session-specific commit scopes.

- Start a descriptive topic branch from current `origin/develop`; use an isolated
  worktree when other work is uncommitted. Keep unrelated tasks in separate PRs.
- Task-scoped commits, topic-branch pushes and PR creation are authorized for
  requested work. Open feature/fix PRs against `develop`.
- Release through a separate `develop` -> `main` PR. Do not push directly or
  force-push to `main` or `develop`. Do not merge or enable auto-merge without an
  explicit owner request. Follow-up work after a merge needs a new branch/PR.
- Run relevant checks; describe the problem, resulting behavior, validation and
  release impact. Report the PR URL and remaining limitations at handoff.
- Normal playtest releases are built from merged `main` with the commit SHA
  recorded. Local feature builds are for validation; published development
  previews require an explicit request and a development label.
- Preserve unrelated uncommitted work. Never commit original game files, generated
  translations, private reports/build outputs, credentials or signing material.
  Keep the existing acceptance criteria and evidence intact.

The private repository's current plan cannot enforce branch protection. That
limitation does not waive these rules or authorize making the repository public.
