---
name: core-critical-spec-review
description: Adversarially review a spec for this repository, fix its major gaps by editing the spec, and loop until it holds or the loop stops, then report what is left. Use after writing a spec, as stage 2 of core-critical-workflow.
---

# Spec review

Part of stage 2 of [the plan-and-review flow](../core-critical-workflow/SKILL.md).

**Input:** the path of the spec file, which lives outside the checkout in the
MW3Recomp-Private-specs folder. If none is given and more than one spec could be
meant, ask which.

**Run:** the loop in
`.agents/skills/core-critical-workflow/references/review-loop.md`, with the
spec as the target and [references/checklist.md](references/checklist.md) as
the checklist. Fixes are edits to the spec only. Checking the spec's claims is
read-only: read files, run read-only `git` and `gh` commands, and change
nothing else.

The loop ends with one report. Then the workflow's walkthrough takes the
requester through what it leaves, and the spec waits for their approval before
a plan is written.

## Reasons not to skip this step

| Excuse | Answer |
| --- | --- |
| "The spec is short and obvious." | Short specs hide assumptions best. A clean first pass costs one read. |
| "The plan review will catch it." | The plan review checks the plan against the spec. A wrong spec gives a correct plan for the wrong change. |
| "The requester already agreed in the grill." | They agreed on decisions, not on the written scope, rollback or acceptance criteria. Those are what this checks. |
| "I wrote the spec, so I know it's right." | That's why the review attacks it on purpose instead of re-reading it. |
