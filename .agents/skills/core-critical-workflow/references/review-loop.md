# Review loop

The spec review, plan review and code review all run this loop. The calling
skill gives two things:

- **The target:** a spec or plan file, or the current branch's changes against
  `origin/develop`.
- **The checklist:** the checklist file in that skill's own references folder,
  which lists what to check and what makes a finding major or minor.

## Loop

Keep a running change log (each edit and the finding it resolved) and the
findings from every pass. Then repeat:

1. **Evaluate.** Open the checklist file and read it, on every pass. A
   skill's reference files load only when they are read, so a pass that didn't
   open the checklist doesn't count; redo it. Re-read the target and every
   file it touches or names; never rely on an earlier read. On a branch, `git fetch origin` and recompute
   `git diff origin/develop...HEAD`, plus uncommitted changes. Check every item
   on the checklist. Rate each finding major or minor by the checklist's rules.
   Only report a finding you have traced to the file and line, or the
   sentence, it is about.
2. **Check whether to stop**, before fixing anything:
   - **Clean:** no major findings this pass.
   - **Cap:** this was the fifth pass.
   - **Repeat:** the major findings this pass match those of an earlier pass,
     or a fix brought back a finding an earlier fix resolved, or the target is
     back to an earlier state.

   If any is true, go to the report.

   - **Same kind:** the major findings this pass and the last are the same kind
     of problem reached by a new route (a new way around the same guard, for
     example). Stop fixing and ask the requester how much of that risk they
     accept; more fixes of that kind rarely converge. Continue with their
     answer.
3. **Fix major findings only**, by editing the target. Leave minor findings
   for the report. On a spec or plan, keep step numbers, file lists and check
   steps consistent after each edit. On a branch, keep the build and tests
   passing after each pass's fixes, and change behaviour only where a finding
   requires it. Add each edit to the change log, then go back to step 1.

A major finding whose fix is large, unrelated to the issue, risky to deliver
in this change, or in files another open PR is changing is not fixed here. It
goes in the report as a recommended follow-up issue.

Never commit, push or open a PR from inside the loop.

## Report

One report when the loop stops:

1. **Outcome:** the target, how many passes ran, and the stop reason (clean,
   cap or repeat). If it stopped on the cap or a repeat with major findings
   left, say plainly that the target isn't ready, and list those findings
   first, each with a suggested fix.
2. **What changed:** the change log, one short line per edit.
3. **Minor findings left:** each with where it is, what it is and a suggested
   action. Leave out any whose suggestion is "do nothing".
4. **Recommended follow-up issues**, if any.
5. **Open questions** the target still can't answer.
6. **Claims checked**, for a spec: each claim checked, whether it held, and
   the evidence (a file, a command's output, an issue or PR).

For a spec or plan, point to the file instead of reprinting it; the file is
the record.

The walkthrough in the workflow skill then takes the requester through every
finding the report leaves: any major findings from item 1 first, then items 3
to 5.
