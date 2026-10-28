# Spec and plan sections

## Spec

One spec covers the whole change, even when it lands as several PRs; it then
lists each PR in order with what it delivers. Keep it under two screens of
text, and link to code rather than pasting it.

1. **Scope:** what is in and what is out.
2. **Target state:** what is true once the change is done.
3. **Approach:** concrete and file-level: which files change and how.
4. **Verification:** how the change will be checked, with the commands or
   steps.
5. **Acceptance criteria:** measurable statements a reviewer can check against
   the diff.
6. **Rollback:** how to undo the change if it goes wrong.
7. **Dependencies and risks:** other issues, PRs or people it waits on, and
   what could go wrong.
8. **Open questions:** what is still undecided. Anything that can be looked up
   now is looked up now, not left here.

## Plan

One plan per PR. When a change spans several PRs, each PR's plan is written
only when the requester says to plan that PR.

1. **Overview:** what the PR does, and the facts the plan rests on, with when
   they were checked.
2. **Ordered steps:** each names the files it touches, what done looks like,
   and how it is checked.
3. **Check the work:** the exact build, lint and test commands, and what to run
   and look at for anything with runtime behaviour.
4. **Open questions and risks.**

Before writing a plan, check the open PRs for files it touches
(`gh pr list --state open` and each PR's diff), and place edits so they don't
conflict. No diagrams.
