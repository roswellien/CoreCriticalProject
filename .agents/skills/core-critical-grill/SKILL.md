---
name: core-critical-grill
description: Interviews the requester one question at a time about an issue until both sides share one understanding of what to build, before any spec is written. Use at the start of work on an issue, as the first stage of core-critical-workflow.
---

# Grill

The first stage of [the plan-and-review flow](../core-critical-workflow/SKILL.md).
The requester is whoever asked for the work. The goal is a shared understanding
the spec can be written from, with every real decision made by the requester.

## Before the first question

- Read the issue, its linked issues and PRs, and the files it names.
- Unless it's already clear, ask in a sentence or two what the result is for
  and what happens to it next. Build the later questions from that answer.
- When the decisions form one connected process (stages, loops, gates), draft
  the whole process first and ask only about its real choices, not about each
  step on its own. Step-by-step questions about a connected process tend to
  undo each other.

## Asking

- One decision per question, and one question per message. Wait for the answer
  before asking the next.
- Give numbered options, your recommended one first, with the reason in one
  line. A bare "yes" or a number must not be ambiguous.
- Look facts up instead of asking: the code, git history, open issues and PRs,
  the docs. Decisions belong to the requester; facts don't.
- Check that every option is real and current (it exists and still works)
  before offering it. Say what a recommendation rests on.
- Before each question, check it against the earlier answers. If an earlier
  answer causes the problem, say so and offer to revisit that answer instead
  of working around it.
- When asking again about some options of an earlier question, keep their
  original numbers. Renumbering makes an answer easy to misread.
- When the recommendation is "take all of them", state it as settled instead
  of asking.

## Ending

- Summarise the decisions in a short list and ask whether that is a shared
  understanding.
- A "yes" starts the spec, in the same turn. Anything else means more
  questions.
- Before writing the spec, re-check anything the decisions depend on (open
  PRs, issue states, files); it may have changed during the interview.

## Reasons not to skip this step

| Excuse | Answer |
| --- | --- |
| "The issue already says what to do." | Issues say what, rarely why or what is out of scope. One question often finds a constraint the issue left out. |
| "I can make the decisions myself." | Facts, yes. Choices between reasonable options are the requester's; guessing them is how a reviewed spec still gets rejected. |
| "Asking one question at a time is slow." | Several questions at once get partial or mixed-up answers, which cost more turns to untangle. |
| "The requester will see it in the spec." | A spec built on a wrong guess has to be rewritten and reviewed again. |
