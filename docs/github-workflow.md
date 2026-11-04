# GitHub development and release workflow

The owner adopted and reaffirmed this workflow on October 27, 2026. It is a
standing project rule until the owner explicitly changes it. It applies to all
contributors and agents and to all new source, documentation, tests, fixes,
build scripts, release/version changes and authored content-pipeline changes.
Urgency or missing GitHub enforcement does not create an exception.

`AGENTS.md` (which `CLAUDE.md` and `.github/copilot-instructions.md` point to)
and `CONTRIBUTING.md` point here for the complete workflow. Older
session-specific commit instructions do not override this rule; the
distribution policy and unrelated-work protections continue to apply.

## Branch roles

| Branch | Purpose | How changes arrive |
| --- | --- | --- |
| `main` | Stable code used for normal playtest releases | Reviewed release PR from `develop` |
| `develop` | Shared integration and testing | Feature/fix PRs |
| `<username>/<type>/<issue>-<slug>` | One implementation task | Task-scoped commits; PR to `develop` |

Every contributor and agent uses the branch format in
[Names and formats](#names-and-formats). Agents use the GitHub username of the
account they push with. `develop` is the repository's default branch, so a
merged PR's `Closes #<issue>` line closes its issue; `main` is the release
branch.

## Start a task

1. Read the project instructions, this guide and the distribution policy.
2. Inspect `git status`, the current branch, worktrees and running build/game
   processes. Preserve existing work and respect other writers.
3. Find the task's issue, or grill and file one if it has none (see
   [Plan and review](#plan-and-review)), then assign yourself and set its card
   to In progress (see [Project board](#project-board)).
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

## Plan and review

Every change follows this flow before its PR leaves draft, whoever or whatever
does the work. The requester (whoever asked for the work) approves each move to
the next stage; an agent never starts the next stage on its own. Each stage
except Implement has a shared skill in `.agents/skills/` (copied to
`.claude/skills/`); a tool that can't load skills opens the `SKILL.md` at the
path given and follows it.

1. **Grill:** interview the requester one question at a time until they confirm
   a shared understanding of the work. The grill runs before the issue is
   filed, and the issue is written from what it settled, under the form's
   usual headings. Whoever picks the issue up decides whether a second, shorter
   grill is needed on what is still open (implementation details, or anything
   that changed since filing), runs it if so, and tells the requester which
   they chose. Issues filed without a grill, including `needs-triage` captures
   (see [Triage](#triage)), get the full grill when picked up; if you can't
   tell whether an issue was grilled (it was filed before this rule, or is a
   sorted capture), treat it as not grilled. Before filing, the requester's
   "yes" at the end of the grill files the issue; at pickup, it starts the
   spec.
   Skill: `.agents/skills/core-critical-grill/SKILL.md`.
2. **Spec:** write the spec, run the spec review, then walk the requester
   through what it leaves. Stop until the requester approves the spec.
   Skill: `.agents/skills/core-critical-spec-review/SKILL.md`.
3. **Plan:** write the plan, run the plan review, then the code review on the
   plan, then one walkthrough of what both leave. Stop until the requester
   approves implementing. Skills: `.agents/skills/core-critical-plan-review/SKILL.md`
   and `.agents/skills/core-critical-code-review/SKILL.md`.
4. **Implement:** carry out the plan through its own checks, then hand over to a
   fresh session for stage 5 without waiting for approval.
5. **Review:** run the code review on the branch in a fresh session that didn't
   write the change; it ends by rerunning the change's checks. Then walk the
   requester through what is left. The PR stays a draft until the requester
   says it's ready. Skill: `.agents/skills/core-critical-code-review/SKILL.md`.

`.agents/skills/core-critical-workflow/SKILL.md` ties the stages together and
holds the spec and plan sections. Each review loops: fix only major findings,
re-read and review again, and stop on a clean pass, after five passes, or when
the same major findings come back. The full loop is in
`.agents/skills/core-critical-workflow/references/review-loop.md`.

Each stage's reviews end with one walkthrough of what they leave, run as
"Walkthroughs" in the workflow skill says.

Short path: a change that can be described in one sentence and is already
covered by tests skips the grill (both before filing and at pickup), spec and
plan when the requester agrees. It
still gets stage 5. Release promotions (`develop` -> `main`) and branch syncs
carry no new change and are exempt. Cloud agents (Copilot cloud agent, Codex
cloud) take only short-path tasks, since they can't hold the interview or keep
a local spec.

Specs and plans are working files, never committed. Keep them outside every
checkout, in `MW3Recomp-Private-specs/` beside the main checkout, named
`<issue>-<slug>-spec.md` and `<issue>-<slug>-plan.md`. The folder is named
after the repository so that the spec, plan and review of one task, each
possibly in a different worktree, find the same files.

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

Mark a PR ready for review only once it meets the
[definition of done](../CONTRIBUTING.md#definition-of-done) in `CONTRIBUTING.md`.

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
first in the last part. Every task has an issue (see
[Project board](#project-board)); only branches made before that rule leave it out.
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
`playtest`, `research` and `release`. `needs-triage` marks captures (issues from
the General form or filed quickly with that label) until they're sorted; they
need no type or area label until then (see [Triage](#triage)). `needs-info`
marks issues waiting on more detail from the reporter.

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

After merge, check that the issue's card is Done (see [Project board](#project-board)).

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
   the same; restore that card to Done using the status command below.
3. **After merge:** GitHub closes the issue named by `Closes #<issue>`, which
   moves its card to Done. If the PR had no such line, close the issue with a
   comment naming the PR. Setting a card to Done also closes its issue, so set
   Done by hand only to restore a closed issue's card after linking a PR.
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
| Status | `PVTSSF_lAHODf7y6M4BpC8LzhngSSM` | Backlog `f75ad846`, Ready `61e4505c`, In progress `47fc9ee4`, In review `df73e18b`, Done `98236657` |
| Priority | `PVTSSF_lAHODf7y6M4BpC8LzhngSb0` | P0 `79628723`, P1 `0a877460`, P2 `da944a9c` |

To unassign yourself, use `gh issue edit <issue> --remove-assignee "@me"`.

## Triage

Capture what you find without stopping your work, and keep the board small
enough to choose from.

- **No issue needed:** something found mid-task that's in the task's scope and
  takes under about 15 minutes is fixed in the same PR. A known limit the PR
  leaves goes in its list of remaining limitations.
- **Capture everything else** as a `needs-triage` issue: the General form, or
  `gh issue create --label needs-triage` with its headings (`### Summary`,
  `### Details`, `### Area`). It needs no type label or priority yet; add an
  area label if it's obvious.
- **Where captures show:** the board's "Inbox" view lists open `needs-triage`
  issues; the "Triaged" view shows everything else.
- **Sorting:** the maintainer, or someone they ask, sorts the Inbox on a regular
  check and whenever it passes 10 open issues. Each capture becomes a focused
  issue (its form's headings, type and area labels, a priority, and
  `needs-triage` removed), is closed as a duplicate
  (`gh issue close <issue> --duplicate-of <other>`), or is closed as not planned
  with a one-line reason (`gh issue close <issue> --reason "not planned" --comment "<reason>"`).
- **Idle issues:** on the same check, P2 issues with no activity for 60 days
  (the board check lists them) are kept or closed as not planned with a reason. No bot closes issues, so a
  report is never closed without someone reading it.

## Promote and publish a release

GitHub Releases are the canonical home for release notes. When preparing a
release, generate notes from the previous release tag to the new tag using
`.github/release.yml`, then lightly edit them to clarify the shipped products,
versions and player impact without changing the generated PR groups. The
playtest site should link to the corresponding GitHub Release rather than
maintaining a second copy; GitHub Release access follows this private
repository's access settings. Do not duplicate the notes in a changelog or a
dated preparation document. Before generating the first release, the maintainer
must create a baseline tag at the source commit of the latest already-published
release, verified from its release receipt; do not infer that commit from a
preparation document.

When the integration branch is ready for a release, open a separate PR from
`develop` to `main` summarizing the included changes and release validation.
After that PR is merged, compile the release from the resulting `main` commit
and retain its SHA in build/publication evidence. Existing versioned installer,
update naming (see `docs/release-filenames.md`), signing, original-file
verification and rollback requirements continue to apply. Development previews
require an explicit request and a clear development label.

Follow the repository-only [launcher and website release checklist](launcher-and-website-release.md)
for launcher inputs, packaging, signing, install/update validation, R2 upload,
signed feed promotion and Cloudflare Pages deployment. It names the maintainer-
supplied credentials and the externally generated runtime input without storing
them in Git.

Include release/version edits in reviewed source changes before the release
build; draft and review release notes in the GitHub Release before publishing.
Do not silently modify source or version values after checking out the release
commit. Record the merged SHA, relevant build/tool identities and artifact
hashes. Verify signing, installation/update/rollback and the applicable
playtest path before publishing the requested release. Preserve historical
artifacts and compatibility URLs. Optional pack publication still
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
close no issue, recently closed issues or merged PRs that don't line up, P2 issues idle for
60 days, and an Inbox of more than 10 captures, against the rules in [Project board](#project-board)
and [Triage](#triage). Captures (`needs-triage`) need no type, area or priority. It only reads, using your own `gh` login with the `project` scope, and it exits
with 1 when it finds something. Run it before a release and whenever the board
looks out of date.

GitHub currently rejects branch-protection and ruleset access for this private
repository with HTTP 403 as of October 27, 2026, requesting GitHub Pro or a public
repository. The repository remains private. Until the owner enables a supporting plan, the PR
requirement is a project rule rather than a GitHub-enforced restriction. The PR
conventions check fails PRs into `main` that don't come from `develop`, but it
cannot stop a direct push. Once
available, protect both shared branches against direct pushes, force-pushes and
deletion, and require PRs and the applicable passing CI checks. Keep `develop`
as the repository's default branch. Do not change account plans, repository
visibility or access controls as a workaround without explicit owner direction.
