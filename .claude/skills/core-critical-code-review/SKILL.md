---
name: core-critical-code-review
description: Review a plan file or the current branch for bugs, breakage, security and code structure, fix major findings by editing the plan or the code, and loop until it is clean or the loop stops, then report what is left. Use on a plan after the plan review (stage 3 of core-critical-workflow), and on a branch in a fresh session as the independent review before a PR (stage 5).
---

# Code review

Part of stages 3 and 5 of [the plan-and-review flow](../core-critical-workflow/SKILL.md).

## Targets

- **A plan file** (stage 3): review the design the plan proposes against the
  real code it will touch. Fixes are edits to the plan; the code is never
  edited.
- **The current branch** (stage 5): review its changes against
  `origin/develop`, plus uncommitted changes. Fixes are edits to the code.
  Confirm first that the branch is the intended topic branch.

If the target is unclear, ask which.

## On a branch: a fresh session only

Before anything else on a branch, confirm that this session didn't write the
change: it has no earlier turns that edited these files or carried out this
plan. If it did, stop and tell the requester that the review needs a fresh
session (or a person) that didn't write the change, and that the implementing
session should hand over. This is the independent review the definition of
done asks for.

## Run

The loop in `.agents/skills/core-critical-workflow/references/review-loop.md`,
with [references/checklist.md](references/checklist.md) as the checklist. Each
pass covers both checklist passes, correctness and structure.

On a branch, keep each pass's fixes building and the existing tests passing.
Once the loop ends, commit each pass's fixes as their own commits on the topic
branch, then run `.agents/skills/core-critical-pre-pr-checks/SKILL.md` and fix
anything it reports before the walkthrough. If no PR exists yet, keep the
check results in the report for the PR description. Never push, open or mark
ready a PR from this skill. On a plan, skip the commits and the checks.

## Reasons not to skip this step

| Excuse | Answer |
| --- | --- |
| "The tests pass." | Tests check what someone thought to test. This checks what the change breaks elsewhere and how it is built. |
| "The plan was already reviewed." | The plan review checks the plan is complete and accurate; this checks the design and the code it produces. |
| "The implementing session can review its own work." | It reads what it meant to write. A fresh session reads what was written. |
| "The maintainer will review the PR anyway." | Every problem caught here is one the maintainer doesn't have to find, explain and wait on. |
| "It's docs only." | Docs-only changes still break links, name missing files, or contradict other rules. A clean pass is quick. |
