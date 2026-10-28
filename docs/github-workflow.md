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
| `<username>/<type>/<issue>-<slug>` | One implementation task | Task-scoped commits; PR to `develop` |

Every contributor and agent uses the branch format in
[Names and formats](#names-and-formats). Agents use the GitHub username of the
account they push with. Keep `main` as the repository default branch and keep
`develop` as the shared integration branch.

## Start a task

1. Read the project instructions, this guide and the distribution policy.
2. Inspect `git status`, the current branch, worktrees and running build/game
   processes. Preserve existing work and respect other writers.
3. Find the task's issue, or file one if it has none, then assign yourself and
   set its card to In progress (see [Project board](#project-board)).
4. Fetch the current remote branches. Start a task-specific branch from
   `origin/develop`; do not start development on either shared branch.

Start a task from the latest `origin/develop`. Use an isolated worktree when
the existing checkout contains other uncommitted work. For example:

```powershell
git fetch origin
git worktree add -b <username>/fix/<issue>-short-description ../MW34-short-description origin/develop
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

## Names and formats

These formats apply to every contributor and agent. The PR conventions check
(`.github/workflows/pr-conventions.yml`) enforces the base-branch rule and
warns about names that don't follow them.

### Branches

`<username>/<type>/<issue>-<slug>`, all lowercase. The username is the GitHub
account that pushes the branch; an agent uses the account it pushes with. The
type is `feature`, `fix`, `docs`, `ci` or `refactor`. The issue number comes
first in the last part when an issue exists and is left out when none does.
Examples: `carson-nr/fix/10-setup-verify-optional-tiers`,
`roswellien/feature/torso-mode-preset`.

### Commit messages

The subject is one plain imperative sentence: capitalized, no type prefix, no
trailing period, about 72 characters or fewer, for example "Match lighting
headers to the CI formatter". An optional body after a blank line says why,
wrapped at 72 characters. GitHub's own merge commits are exempt. The project
does not use Conventional Commits: branch types and labels already carry the
kind of change.

### PR titles

`<Verb> <area>: <what changed>`, for example "Fix launcher: add the torso-mode
toggle to the MW5 control preset" or "Add docs: illustrated field guide for new
contributors". The verb is imperative and capitalized. The area is one of the
area label names below (written `CI` for `ci`) or `docs`, and matches one of
the PR's labels. No trailing period, about 72 characters or fewer.

Release PRs from `develop` to `main` are titled "Release <what ships>", for
example "Release launcher 1.0.45 and runtime 1.0.46". Sync PRs from `main` to
`develop` are titled "Sync main into develop after <release>".

### PR descriptions

Use the PR template. What every PR must contain is in
[Issues and pull requests](../CONTRIBUTING.md#issues-and-pull-requests). Write
`Closes #<issue>` when the PR finishes an issue.

### Issues

Bug titles state the symptom as a plain sentence ("Set Up Game rejects a normal
retail install"). Other titles are imperative ("Add a project board that agents
keep up to date"). No tags in brackets.

File issues with the issue forms; blank issues are turned off. Each form adds
its type label:

| Form | Label | Use it for |
| --- | --- | --- |
| Bug | `bug` | Something that doesn't work as it should |
| Playtest report | `playtest` | How a playtest session went on given hardware |
| Task | `enhancement` | A feature, fix or other piece of work, written so a person or agent can pick it up without the conversation that produced it |
| Research finding | `research` | A reverse-engineering or investigation result with its evidence |
| Release checklist | `release` | One release, from merged `main` to published files |
| General | `needs-triage` | Anything else, including questions; triage turns it into a focused issue or closes it |

Issues filed with `gh issue create` skip the forms. Use the same headings the
form would produce, in this order, and pass its label with `--label`:

- Bug: `### What happens`, `### What should happen`, `### Steps to reproduce`,
  `### Launcher version`, `### Runtime version`, `### Game and version`,
  `### Operating system`, `### GPU and driver`, `### Windows HDR`,
  `### Input devices`, `### Logs or screenshots`.
- Playtest report: `### Versions`, `### Hardware`, `### What was played`,
  `### What worked`, `### Problems found`, `### Performance`.
- Task: `### Goal`, `### Why`, `### Acceptance criteria`,
  `### Likely files or area`, `### Checks to run`, `### Out of scope`.
- Research finding: `### Question investigated`, `### Executable SHA-256`,
  `### Address kind`, `### Addresses`, `### Tool and version`, `### Method`,
  `### Confidence`, `### Evidence`, `### Unresolved alternatives`,
  `### Full write-up`.
- Release checklist: `### Version`, `### Merged main SHA`,
  `### Products in this release`, `### Checklist`.
- General: `### Summary`, `### Details`, `### Area`.

### Labels

Each issue and PR gets one type label and at least one area label. Type labels
are `bug`, `enhancement`, `documentation` (pairs with the `docs` title area),
`playtest`, `research` and `release`. `needs-triage` marks issues from the
General form until they're sorted, and `needs-info` marks issues waiting on
more detail from the reporter.

| Area label | Covers |
| --- | --- |
| `area: launcher` | `tools/mw3-remaster-launcher/`, `mw3_launcher.py`, `tools/remaster-launcher/play_*` |
| `area: runtime` | `runtime/` except `runtime/graphics/` (audio, core, input, memory, mfc, win32), `tools/m4-crt-heap-carry/` |
| `area: renderer` | `runtime/graphics/`, `tools/remaster-launcher/native-overrides/` |
| `area: mod-tools` | `games/mw3/mod-tools/` |
| `area: content` | `mods/` and the asset and pack pipelines |
| `area: analysis` | `tools/analysis/`, `tools/binary-validator/`, `tools/lifting/`, `recomp/` |
| `area: ci` | `.github/`, `cmake/`, `tools/github/` |
| `area: website` | `website/` |

### The PR conventions check

A PR into `main` from any branch other than `develop` fails the check. A branch
name or title that doesn't follow the formats above, or a branch whose username
doesn't match the PR author, gets a warning on the PR but doesn't block it.

### No AI tool attribution

Commits, PRs, issues and comments carry no AI tool attribution: no agent
`Co-authored-by` lines and no "Generated with" lines.

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

After a PR into `develop` merges, close its issue with a comment naming the PR,
as described in [Project board](#project-board).

## Project board

The [project board](https://github.com/users/roswellien/projects/1) shows where
each piece of work is. Only issues go on it; a PR shows on its issue's card
through the `Closes #<issue>` line in its description. So every piece of work
gets an issue before its PR: if there is none, file one first. Release and sync
PRs are the exception: a release is tracked by its Release checklist issue,
which stays open until the files are published.

| Column | Meaning | Who moves the card there |
| --- | --- | --- |
| Backlog | Filed, not yet ready to start | GitHub, when the issue is filed |
| Ready | Clear enough to pick up | Whoever triages it |
| In progress | A person or agent is working on it | Whoever starts the work |
| In review | Its PR is open | Whoever opens the PR |
| Done | The issue is closed | GitHub, when the issue closes |

1. **Start:** assign yourself and set the card to In progress.
2. **Open the PR:** write `Closes #<issue>` in its description and set the card
   to In review. Linking the PR makes GitHub set the card to In progress, so set
   In review after the PR exists. Linking a PR to an already closed issue does
   the same; set that card back to Done.
3. **After merge:** close the issue with a comment naming the PR. GitHub closes
   an issue by itself only when a PR merges into `main`, the default branch, so
   a merge into `develop` leaves it open. Closing it moves the card to Done;
   never set Done by hand.
4. **If work stops before a PR:** unassign yourself and set the card back to
   Ready or Backlog.

The Priority field says what to pick up first: P0 blocks players or other work,
P1 is next up, P2 is later. Set it when you file an issue if you know it; the
maintainer may change it.

Agents and the command line make these moves with `gh`. Run
`gh auth refresh -s project` once so your login may change the board, then:

```powershell
# Assign yourself
gh issue edit <issue> --add-assignee "@me"

# Find the issue's card id
gh project item-list 1 --owner roswellien --limit 1000 --format json --jq '.items[] | select(.content.number == <issue>) | .id'

# Set the card's status or priority
gh project item-edit --project-id PVT_kwHODf7y6M4BpC8L --id <card id> --field-id <field id> --single-select-option-id <option id>
```

| Field | Field id | Option ids |
| --- | --- | --- |
| Status | `PVTSSF_lAHODf7y6M4BpC8LzhngSSM` | Backlog `f75ad846`, Ready `61e4505c`, In progress `47fc9ee4`, In review `df73e18b` |
| Priority | `PVTSSF_lAHODf7y6M4BpC8LzhngSb0` | P0 `79628723`, P1 `0a877460`, P2 `da944a9c` |

To unassign yourself, use `gh issue edit <issue> --remove-assignee "@me"`.

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

Native host releases use the maintained [host-only build](../tools/m4-crt-heap-carry/HOST_BUILD.md)
from the merged release checkout. Build `entry_commandline.exe` directly from
the committed `host/` sources with `build_host.ps1 -Release`; retain its complete
source/dependency receipt in the staged runtime metadata and compare fingerprints
before publication. The existing local `MW3Translated.dll` remains unchanged
for host-only fixes. Private patched host folders, saved object lists and an
unrecorded `apply_*.py` sequence are not release build inputs.

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

`python tools/github/check_board.py` lists where the project board, the issues
and the PRs disagree: open issues off the board or without a priority or
labels, cards whose status doesn't match their issue or PR, empty PRs, PRs that
close no issue, and recently closed issues or merged PRs that don't line up,
against the rules in [Project board](#project-board). It only reads, using your own `gh` login with the `project` scope, and it exits
with 1 when it finds something. Run it before a release and whenever the board
looks out of date.

GitHub currently rejects branch-protection and ruleset access for this private
repository with HTTP 403 as of October 27, 2026, requesting GitHub Pro or a public
repository. The repository remains private. Until the owner enables a supporting plan, the PR
requirement is a project rule rather than a GitHub-enforced restriction. The PR
conventions check fails PRs into `main` that don't come from `develop`, but it
cannot stop a direct push. Once
available, protect both shared branches against direct pushes, force-pushes and
deletion, and require PRs and the applicable passing CI checks. Keep `main` as
the repository's default branch. Do not change account plans, repository
visibility or access controls as a workaround without explicit owner direction.
