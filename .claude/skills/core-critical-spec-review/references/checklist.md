# Spec review checklist

Read the spec as someone trying to make it fail: assume it is wrong until the
files and commands show otherwise. Before the first area, read the issue it
answers and every document it relies on (linked issues and PRs, the guides it
cites). For each area, ask the questions, check every claim that can be checked
(a file exists, a PR is open, a command works), and write down a finding for
each gap. Each finding names the part of the spec it is about, what could go
wrong and what that would cost; "consider adding more detail" is not a finding.

## What to check

1. **Scope gaps:** is anything the issue asks for missing from "in"? Is
   anything in "in" that the issue didn't ask for? Is "out" explicit enough
   that a planner won't drift into it? What does the spec quietly leave for
   some other change, person or tool to handle?
2. **Hidden assumptions:** what must be true for the approach to work (a file's
   layout, a tool's behaviour, another PR having merged)? Is each one stated,
   and does it hold today? For each, what happens if it turns out to be false?
3. **Procedures:** for every step, command or catch-up routine the spec tells
   someone to run, follow it through the real code and files it touches, as
   they are today, and confirm it produces what the spec says. A step that
   reads well but does nothing, or does something else, is a finding. Check
   the order too: is every in-between state safe, and does each step still
   work when an earlier one has already run?
4. **Failure modes:** what happens if a step fails halfway, a tool is missing,
   or an input is unusual? Walk through the usual ways things fail: a change
   applied only in part, steps run in a different order, a timeout or rate
   limit, two runs at once, a cold start with no cache or earlier state, and
   empty or missing input. Does the spec say what the user, player or
   contributor sees?
5. **Blast radius:** what else uses the files, formats or behaviour being
   changed: the launcher, the runtime, packs, CI, releases, other docs?
6. **Rollback:** can the change be undone by reverting its PR? If not (data
   written, files renamed, a release shipped), does the spec say how? Is there
   a point after which it can't be undone, and does the spec say where? How
   would anyone notice that the change went wrong?
7. **Measurable criteria:** can each acceptance criterion be checked against
   the diff or a command's output, with no judgment call? Could every criterion
   pass while the change is still broken? What does the change do that no
   criterion measures?
8. **Dependencies:** which issues, PRs or people does it wait on, and does it
   say what happens if they change or don't land?
9. **Security and distribution:** does anything risk committing original game
   media, generated game code, private build outputs, credentials or signing
   material (see `docs/legal.md` and `CONTRIBUTING.md`)? Does it run untrusted
   input, and could that input reach a command, a path or a query? Does it
   widen who or what may read or change something (tokens, workflow
   permissions, download locations)? Does it add a dependency, and is that
   dependency maintained and trustworthy?
10. **Conflicts:** does it contradict `AGENTS.md`, `CONTRIBUTING.md`,
    `CODE_STYLE.md` or `docs/github-workflow.md`? Do open PRs touch the same
    files (`gh pr list --state open` and their diffs)?
11. **Timing and concurrency:** does anything depend on when it runs or on
    what else runs at the same time: CI runs on the same branch, a release in
    progress, the update service rolling out, other contributors' or agents'
    sessions working in the same files, caches that take time to refresh?
12. **Cost and limits:** what does it use up, and what is the worst case: CI
    minutes, Cloudflare or GitHub limits, download sizes, AI review or agent
    usage, disk space on a player's machine?
13. **Observability:** once it ships, how will anyone see that it works or that
    it broke (a log line, a CI result, a check, a report)? Is that signal in
    place before the risky step, not added after?
14. **Who must be present:** which steps need a person to approve, sign, run
    or watch them (the maintainer, the requester, a playtester)? Does the spec
    quietly assume a step runs unattended that shouldn't?

A known, built-in behaviour of a tool or format the requester already chose is
not a finding that reopens the choice. Note it in one line under open
questions, unless it defeats the issue's goal.

Then write down the sharp questions a hostile reviewer would ask that the spec
can't answer yet. They often find gaps the areas above miss; turn any that
expose a major gap into a finding, and put the rest under open questions in
the report.

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
