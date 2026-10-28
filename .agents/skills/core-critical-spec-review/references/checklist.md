# Spec review checklist

Read the spec as someone trying to make it fail. For each area, ask the
questions, check every claim that can be checked (a file exists, a PR is open,
a command works), and write down a finding for each gap.

## What to check

1. **Scope gaps:** is anything the issue asks for missing from "in"? Is
   anything in "in" that the issue didn't ask for? Is "out" explicit enough
   that a planner won't drift into it?
2. **Hidden assumptions:** what must be true for the approach to work (a file's
   layout, a tool's behaviour, another PR having merged)? Is each one stated,
   and does it hold today?
3. **Failure modes:** what happens if a step fails halfway, a tool is missing,
   or an input is unusual? Does the spec say what the user, player or
   contributor sees?
4. **Blast radius:** what else uses the files, formats or behaviour being
   changed: the launcher, the runtime, packs, CI, releases, other docs?
5. **Rollback:** can the change be undone by reverting its PR? If not (data
   written, files renamed, a release shipped), does the spec say how?
6. **Measurable criteria:** can each acceptance criterion be checked against
   the diff or a command's output, with no judgment call?
7. **Dependencies:** which issues, PRs or people does it wait on, and does it
   say what happens if they change or don't land?
8. **Security and distribution:** does anything risk committing original game
   media, generated game code, private build outputs, credentials or signing
   material (see `docs/legal.md` and `CONTRIBUTING.md`)? Does it run untrusted
   input?
9. **Conflicts:** does it contradict `AGENTS.md`, `CONTRIBUTING.md`,
   `CODE_STYLE.md` or `docs/github-workflow.md`? Do open PRs touch the same
   files (`gh pr list --state open` and their diffs)?

## Severity

**Major** (fixed in the loop): the spec, as written, would lead to any of

- a broken build, failing CI, or a regression players or contributors would
  notice;
- lost or overwritten work or data, or a state that can't be undone;
- committed material the distribution policy forbids, or a security hole;
- a change that doesn't meet the issue's goal, or acceptance criteria nobody
  can check;
- a claim about the repository that is false today, where the approach depends
  on it.

**Minor** (reported, not fixed): unclear wording, a missing detail a planner
would find in minutes, an unlikely edge case, or a risk that is stated but
could be handled better.
