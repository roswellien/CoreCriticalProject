---
name: core-critical-workflow
description: Run a change through this repository's plan-and-review flow (grill, spec, plan, implement, review) and say which skill each stage uses and where to stop for approval. Use when starting work on an issue, or when unsure which stage comes next.
---

# Plan-and-review workflow

The flow, its stop rules and the short path are written once, in
[Plan and review](../../../docs/github-workflow.md#plan-and-review). Read that
section first; this skill says how to run it.

The requester is whoever asked for the work. They approve every move to the
next stage. Never start the next stage on your own, except that implementing
runs straight on into review.

## Stages and their skills

Open each skill at its path and follow it, whether or not your tool can call
one skill from another.

1. **Grill:** `.agents/skills/core-critical-grill/SKILL.md`. Ends when the
   requester confirms a shared understanding; that "yes" starts the spec.
2. **Spec:** write it to the spec sections in
   [references/spec-and-plan-sections.md](references/spec-and-plan-sections.md),
   then run `.agents/skills/core-critical-spec-review/SKILL.md`, then walk the
   requester through what it leaves. **Stop** until the requester approves the
   spec.
3. **Plan:** write it to the plan sections in the same file, then run
   `.agents/skills/core-critical-plan-review/SKILL.md`, then
   `.agents/skills/core-critical-code-review/SKILL.md` on the plan file, then
   one walkthrough of what both leave. **Stop** until the requester approves
   implementing.
4. **Implement:** carry out the whole plan, including its check steps, without
   stopping for a go-ahead and without editing the plan. If the plan turns out
   to be wrong, stop and tell the requester; the plan is fixed before going on.
5. **Review:** in a fresh session that didn't write the change, run
   `.agents/skills/core-critical-code-review/SKILL.md` on the branch (it ends
   by rerunning the checks with
   `.agents/skills/core-critical-pre-pr-checks/SKILL.md`), then walk the
   requester through what is left. The implementing session stops after its
   checks; the requester, or the tool where it can, starts the review session.
   The PR opens as a draft and stays one until the requester says it's ready.

**Short path:** a change that fits the guide's short path skips stages 1 to 3
when the requester agrees for that change, and still gets stage 5. The guide
says which changes fit and which are exempt.

Specs and plans are working files kept outside every checkout and never
committed: `MW3Recomp-Private-specs/<issue>-<slug>-spec.md` and
`<issue>-<slug>-plan.md`, beside the main checkout.

## Walkthroughs

- Apply every finding whose fix is obvious and low-risk (a small, clearly
  correct edit with no real alternative) and list those in one line.
- Put each remaining finding to the requester one at a time, most severe first,
  with your recommendation: fix now, file a follow-up issue, or drop. Never
  drop or defer a finding without asking.
- A large, independent or risky refactor a review finds becomes a follow-up
  issue, not part of this change.

## Reasons not to skip this step

| Excuse | Answer |
| --- | --- |
| "It's a small change." | Small changes are what the short path is for, and it still needs the requester's yes. Without that yes, it gets the full flow. |
| "The requester is busy." | A stop costs them one message. A PR built on a wrong guess costs them a review and a redo. |
| "I already know what to build." | The grill and spec exist to find out whether the requester agrees. Writing it down is how that gets checked. |
| "The reviews will just slow this down." | Each review stops after five passes at most, and a clean first pass ends it at once. |
| "I wrote it, so I can review it." | Fresh-session review catches more than self-review; that's why stage 5 runs in a session that didn't write the change. |

The "reasons not to skip" idea comes from addyosmani/agent-skills (MIT); no text
is copied from it.
