# Code review checklist

Review the change together with what it touches: the files and modules it
changes, their callers and callees, and anywhere else in the repository that
does the same job. Report a bug found along the way even if the change didn't
cause it, and label it as pre-existing.

## Correctness pass

1. **Bugs:** logic errors, wrong conditions, off-by-one, unhandled errors,
   wrong units or sizes, broken ABI or floating-point behaviour.
2. **Breakage:** what existing behaviour, callers, tests, CI jobs, file formats
   or docs does the change break?
3. **Security and distribution:** untrusted input, credentials or signing
   material, and original game media, generated game code or private build
   outputs that must not be committed (`docs/legal.md`).
4. **Contributor experience:** does it break a build preset, a documented
   command, a check, or a setup step other contributors rely on?
5. **Release and pack impact:** does it change launcher, runtime or pack
   compatibility, versions, installer or update names
   (`docs/release-filenames.md`)?
6. **Execution boundary:** for native behaviour, is the boundary the change
   advances named, as `AGENTS.md` requires, with the original comparison or
   fixture used?

## Structure pass

1. **Duplication:** does it copy logic that already exists and should be
   reused, or leave old code it makes redundant?
2. **File size:** does it push a file from under 1,000 lines to over 1,000
   without a reason?
3. **Boundaries:** does feature logic leak into shared paths, or one module
   reach into another's internals?
4. **Simpler equivalents:** is there a clearly simpler way to do the same
   thing, such as removing a branch, a wrapper, a cast or an option nobody
   needs?
5. **Readability:** does it follow `CODE_STYLE.md`?

## On a branch, also

- **Acceptance criteria:** for each criterion in the issue, name where the
  diff meets it, or report it as missing.
- **Definition of done:** check the change against "Definition of done" and
  "Tests" in `CONTRIBUTING.md`; don't repeat them here.

## Severity

**Major** (fixed in the loop):

- from the correctness pass: a medium-or-worse bug, breakage, security or
  distribution problem, contributor breakage, or unstated release impact,
  traced end to end;
- from the structure pass: a clear structural regression, duplication of
  existing code, a file pushed past 1,000 lines, branching bolted onto an
  existing flow, feature logic in a shared path, or a missed simplification
  with a visible path;
- on a branch, an acceptance criterion the diff doesn't meet.

**Minor** (reported, not fixed): lower-confidence findings, naming, small
readability points, and suggestions the rules don't require.
