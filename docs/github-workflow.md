# GitHub development and release workflow

The owner adopted this workflow on October 27, 2026.

| Branch | Purpose | How changes arrive |
| --- | --- | --- |
| `main` | Stable code used for normal playtest releases | Reviewed release PR from `develop` |
| `develop` | Shared integration and testing | Feature/fix PRs |
| `codex/<topic>` | One implementation task | Task-scoped commits; PR to `develop` |

Start a task from the latest `origin/develop`. Use an isolated worktree when
the existing checkout contains other uncommitted work. For example:

```powershell
git fetch origin
git worktree add -b codex/short-description ../MW34-short-description origin/develop
```

Implement and validate the task, commit only its authored source and relevant
documentation, and push the topic branch. Open a PR against `develop` explaining
the problem, resulting behavior, checks and remaining limitations. Separate
unrelated fixes into separate PRs. Existing normal-map experiments, original
media, generated game code, private build outputs and signing material must
not be swept into a feature commit.

The maintainer reviews and merges the PR after the applicable checks pass.
Agents may create task-scoped commits and PRs for requested work, but do not
merge PRs or enable auto-merge without an explicit user request. Do not push
directly or force-push to `main` or `develop`.

When the integration branch is ready for a release, open a separate PR from
`develop` to `main` summarizing the included changes and release validation.
After that PR is merged, compile the release from the resulting `main` commit
and retain its SHA in build/publication evidence. Existing versioned installer,
update naming, signing, original-file verification and rollback requirements
continue to apply. Development previews require an explicit request and a clear
development label.

The bootstrap-check workflow already runs on both pushes and pull requests,
including `develop`; it does not need a branch-filter change for this setup.
Relevant native/launcher checks supplement CI where private original inputs
are required. Preserve the existing strict native acceptance accounting.

GitHub currently rejects branch-protection and ruleset access for this private
repository with HTTP 403, requesting GitHub Pro or a public repository. The
repository remains private. Until the owner enables a supporting plan, the PR
requirement is a project rule rather than a GitHub-enforced restriction. Once
available, protect both shared branches against direct pushes, force-pushes and
deletion, and require PRs and the applicable passing CI checks. Keep `main` as
the repository's default branch.
