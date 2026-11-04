# Code review checklist

## How to review

- **Reach:** review the change together with what it touches: the files and
  modules it changes, their callers and callees, and anywhere else in the
  repository that does the same job. Report a bug found along the way even if
  the change didn't cause it, and label it as pre-existing.
- **Trace it through:** a small change in one place often breaks something in
  another module, a script or a pack that reads its output. Follow every side
  effect of the change to its end before deciding it is safe.
- **Finish the research:** never report "this is wrong unless the other side
  handles it" when the other side is in the repository; read it and decide.
- **Don't overstate:** rate a finding by what it does once traced end to end.
  Calling minor things major teaches people to ignore the review.
- **Intended breakage:** when the change sets out to remove or break something
  (a check, a feature, a fallback) and its scope is tight, don't report that as
  a finding, unless its full effect looks unknown to the author.
- **Others' comments come last:** on a branch with an open PR, do your own
  review first. Then read the PR's review comments (Copilot code review and
  people), check each one, include the valid ones, and say where they came
  from.

## Correctness pass

1. **Bugs:** logic errors, wrong conditions, off-by-one, unhandled errors,
   wrong units or sizes, broken ABI or floating-point behaviour.
2. **Breakage:** what existing behaviour, callers, tests, CI jobs, file formats
   or docs does the change break?
3. **Security and distribution:** untrusted input, credentials or signing
   material, and original game media, generated game code or private build
   outputs that must not be committed (`docs/legal.md`).
4. **Contributor experience:** does it break a build preset, a documented
   command, a check, or a setup step other contributors rely on? Watch for a
   changed place where secrets or tokens are read, a renamed or new environment
   variable, a changed port, or a new step everyone must run for something to
   keep working. A new dependency installed by the usual package manager
   doesn't count; one that needs a manual download or install does.
5. **Gated features:** does anything meant to stay behind a switch leak out:
   a preview channel, a development-only option, an unreleased pack, a
   maintainer-only release step?
6. **Release and pack impact:** does it change launcher, runtime or pack
   compatibility, versions, installer or update names
   (`docs/release-filenames.md`)?
7. **Execution boundary:** for native behaviour, is the boundary the change
   advances named, as `AGENTS.md` requires, with the original comparison or
   fixture used?

## Structure pass

Aim high: look for a way to restructure the change so whole branches, helpers,
modes or layers disappear, not just for small tidy-ups. Working code isn't
enough when the same behaviour can be had with a clearly cleaner design.

1. **Duplication:** does it copy logic that already exists and should be
   reused, or leave old code it makes redundant? Does it add its own helper
   where the repository already has one for the job?
2. **File size:** does it push a file from under 1,000 lines to over 1,000
   without a reason?
3. **Boundaries:** does feature logic leak into shared paths, or one module
   reach into another's internals? Does the logic live in the module that owns
   the concept?
4. **Simpler equivalents:** is there a clearly simpler way to do the same
   thing, such as removing a branch, a wrapper, a cast or an option nobody
   needs? Does a refactor actually remove complexity, or only move it around?
5. **Special cases:** does it add one-off conditions, flags or modes to an
   unrelated or already busy flow? Repeated conditions often mean a missing
   type, table or helper. Is a "temporary" branch likely to stay for good?
6. **Hidden behaviour:** does it rely on clever or magic handling where plain
   code would do? Does a wrapper or pass-through helper add a layer without
   making anything clearer?
7. **Types and contracts:** does it add optional values, casts, loosely shaped
   data or silent fallbacks that hide what must actually be true? Would a
   clearer type or an explicit check make the flow simpler?
8. **Ordering and state:** is independent work done one after another for no
   reason? Can related updates be left half applied if one fails?
9. **Readability:** does it follow `CODE_STYLE.md`?

## On a branch, also

- **Acceptance criteria:** for each criterion in the issue (the number in the
  branch name, or the PR's `Closes #N`), name where the diff meets it, or
  report it as missing.
- **Definition of done:** check the change against "Definition of done" and
  "Tests" in `CONTRIBUTING.md`; don't repeat them here.

## Finding order

Report structural regressions and missed simplifications first, then special
cases, then type and boundary problems, file size and readability. Keep nits
few and only when they are actionable; a long list of small points buries the
ones that matter.

## Severity

**Major** (fixed in the loop):

- from the correctness pass: a medium-or-worse bug, breakage, security or
  distribution problem, contributor breakage, gated feature leak, or unstated
  release impact, traced end to end;
- from the structure pass: a clear structural regression, duplication of
  existing code, a file pushed past 1,000 lines, branching bolted onto an
  existing flow, feature logic in a shared path, or a missed simplification
  with a visible path;
- on a branch, an acceptance criterion the diff doesn't meet.

**Minor** (reported, not fixed): lower-confidence findings, naming, small
readability points, and suggestions the rules don't require.
