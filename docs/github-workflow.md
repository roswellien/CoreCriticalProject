# GitHub development and release workflow

The owner adopted and reaffirmed this workflow on October 27, 2026. It is a
standing project rule until the owner explicitly changes it. It applies to all
contributors and agents and to all new source, documentation, tests, fixes,
build scripts, release/version changes and authored content-pipeline changes.
Urgency or missing GitHub enforcement does not create an exception.

`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` and `CONTRIBUTING.md`
point here for the complete workflow. Older session-specific commit instructions
do not override this rule; the distribution policy and unrelated-work protections
continue to apply.

## Branch roles

| Branch | Purpose | How changes arrive |
| --- | --- | --- |
| `main` | Stable code used for normal playtest releases | Reviewed release PR from `develop` |
| `develop` | Shared integration and testing | Feature/fix PRs |
| `codex/<topic>` | One implementation task | Task-scoped commits; PR to `develop` |

Codex uses the `codex/` prefix. Other collaborators may use descriptive topic
prefixes; the PR targets and review requirements are the same. Keep `main` as
the repository default branch and keep `develop` as the shared integration branch.

## Start a task

1. Read the project instructions, this guide and the distribution policy.
2. Inspect `git status`, the current branch, worktrees and running build/game
   processes. Preserve existing work and respect other writers.
3. Fetch the current remote branches. Start a task-specific branch from
   `origin/develop`; do not start development on either shared branch.

Start a task from the latest `origin/develop`. Use an isolated worktree when
the existing checkout contains other uncommitted work. For example:

```powershell
git fetch origin
git worktree add -b codex/short-description ../MW34-short-description origin/develop
```

Use a fresh worktree directory. Do not reset, clean, mass-stash or commit other
contributors' work to obtain a clean tree. Existing local experiments remain
uncommitted until deliberately separated into their own task branches/PRs.

## Implement, validate and open a PR

Implement and validate the task, commit only its authored source and relevant
documentation, and push the topic branch. Open a PR against `develop` explaining
the problem, resulting behavior, checks and remaining limitations. Separate
unrelated fixes into separate PRs. Existing normal-map experiments, original
media, generated game code, private build outputs and signing material must
not be swept into a feature commit.

Inspect the staged diff and filenames before committing. Stage explicit paths
rather than using a blanket add in a mixed working tree. Push only the topic
branch, then create a PR with `develop` as its base. The PR should explain:

- The concrete problem and the resulting behavior.
- Relevant tests, native validation where applicable, and remaining limitations.
- Concrete execution/fidelity evidence under the [status reporting rule](project-status-reporting.md), without an unchanged historical startup fraction.
- Launcher/runtime/pack compatibility, version or release consequences, or that
  the change is documentation only.

Local feature builds, test packs and game captures may validate a PR before it
merges; they are not normal published releases. Documentation-only work needs
link/diff/evidence checks, not an unnecessary game capture or native recompile.

## Review and merge

The maintainer reviews and merges the PR after the applicable checks pass.
Agents may create task-scoped commits and PRs for requested work, but do not
merge PRs or enable auto-merge without an explicit user request. Do not push
directly or force-push to `main` or `develop`.

Creating a PR or saying its implementation is ready does not authorize merging
it or publishing a release. Address review feedback on the same topic branch
while its PR is open; rerun checks affected by the new commits. Resolve conflicts
on the topic branch, preserving both sides' required behavior, and update the PR.

Once a PR has merged, a new fix or follow-up uses a fresh branch from current
`origin/develop` and a new PR. Do not reuse a merged PR's old topic branch for
additional changes. At handoff, report the branch, PR URL, checks and open limits;
distinguish "awaiting review" from "merged" and "published".

## Promote and publish a release

When the integration branch is ready for a release, open a separate PR from
`develop` to `main` summarizing the included changes and release validation.
After that PR is merged, compile the release from the resulting `main` commit
and retain its SHA in build/publication evidence. Existing versioned installer,
update naming, signing, original-file verification and rollback requirements
continue to apply. Development previews require an explicit request and a clear
development label.

Include release/version edits and release notes in reviewed source changes
before the release build; do not silently modify source or version values after
checking out the release commit. Record the merged SHA, relevant build/tool
identities and artifact hashes. Verify signing, installation/update/rollback and
the applicable playtest path before publishing the requested release. Preserve
historical artifacts and compatibility URLs. Optional pack publication still
obeys the distribution policy; large local assets do not belong in a PR.

For an urgent repair, use the same feature/fix PR and release PR route. Any
different route requires an explicit owner instruction for that specific case;
agents must not invent a direct-push exception.

## Synchronize the branches

`develop` advances through feature PRs; `main` advances through release PRs.
After a release, compare both remote branches. If `main` contains commits that
`develop` lacks, open a synchronization PR from `main` to `develop` and describe
that it brings the release history back into integration. Do not push a merge,
reset, rebase or force-push directly onto either shared branch. Synchronization
does not add an exception for unrelated new work to target `main`.

## Checks and enforcement

The bootstrap-check workflow already runs on both pushes and pull requests,
including `develop`; it does not need a branch-filter change for this setup.
Relevant native/launcher checks supplement CI where private original inputs
are required. Preserve the existing strict native acceptance accounting.

GitHub currently rejects branch-protection and ruleset access for this private
repository with HTTP 403 as of October 27, 2026, requesting GitHub Pro or a public
repository. The repository remains private. Until the owner enables a supporting plan, the PR
requirement is a project rule rather than a GitHub-enforced restriction. Once
available, protect both shared branches against direct pushes, force-pushes and
deletion, and require PRs and the applicable passing CI checks. Keep `main` as
the repository's default branch. Do not change account plans, repository
visibility or access controls as a workaround without explicit owner direction.
