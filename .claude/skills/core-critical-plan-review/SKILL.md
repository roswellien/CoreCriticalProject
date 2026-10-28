---
name: core-critical-plan-review
description: Review an implementation plan for this repository against the real files and its spec, fix major problems by editing the plan, and loop until it passes or the loop stops, then report what is left. Use after writing a plan, as stage 3 of core-critical-workflow, before the code review of the plan.
---

# Plan review

Part of stage 3 of [the plan-and-review flow](../core-critical-workflow/SKILL.md).

**Input:** the path of the plan file, which lives outside the checkout in the
MW3Recomp-Private-specs folder next to its spec. If none is given and more than
one plan could be meant, ask which. Read the spec too; the plan is checked
against it.

**Run:** the loop in
`.agents/skills/core-critical-workflow/references/review-loop.md`, with the
plan as the target and [references/checklist.md](references/checklist.md) as
the checklist. Fixes are edits to the plan only; never carry out a plan step
during the review.

After the loop's report, run `.agents/skills/core-critical-code-review/SKILL.md`
on the same plan file, then give the requester one walkthrough of what both
reviews leave. The plan waits for their approval before anything is
implemented.

## Reasons not to skip this step

| Excuse | Answer |
| --- | --- |
| "The spec was already reviewed." | The spec says what; the plan says exactly which files and commands. Most mistakes live in that detail. |
| "I'll notice problems while implementing." | Implementing doesn't edit the plan, so a wrong step means stopping and asking anyway, later and with half-done work. |
| "It's only a few steps." | A short plan is a short review. A wrong file name or missing check still breaks the PR. |
| "Checking every file is slow." | Accuracy against the real files is the one thing a plan can't be trusted without. |
