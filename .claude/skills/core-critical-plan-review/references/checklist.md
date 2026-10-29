# Plan review checklist

Read the plan, its spec and every file the plan names or will change. Check
each area and write down a finding for each problem.

## What to check

1. **Completeness:** does every part of the spec's scope and every acceptance
   criterion have a step? Does every step name its files, what done looks like
   and how it is checked? Does the plan end with exact build, lint and test
   commands?
2. **Accuracy:** do the files, functions, headings, commands, presets and
   paths it names exist as written today? Do its facts about other issues and
   PRs still hold (`gh issue view`, `gh pr view`)?
3. **Redundancy:** does any step duplicate another, or rebuild something that
   already exists in the repository and should be reused?
4. **Bugs:** would any step, done as written, produce wrong code, a wrong
   command or a broken file? Are steps in an order that works?
5. **Sanity:** is this the simplest plan that meets the spec? Is anything done
   that the spec didn't ask for?
6. **Security and distribution:** does any step risk committing original game
   media, generated game code, private build outputs, credentials or signing
   material, or staging files by folder instead of by name?
7. **Regressions:** what existing behaviour, tests, CI jobs or docs could the
   change break, and does the plan check them?
8. **Conformance:** does the plan follow `CODE_STYLE.md`, `CONTRIBUTING.md` and
   "Names and formats" in `docs/github-workflow.md` (branch, commit subjects,
   PR title, labels, PR template)? Does it start from `origin/develop` and
   target `develop`?
9. **Open PRs:** do open PRs change the same files, and does the plan place its
   edits so they don't conflict?

## Severity

**Major** (fixed in the loop):

- a missing step for something in the spec's scope or acceptance criteria;
- a file, command, heading or fact that is wrong today;
- a step that would break the build, tests, CI or existing behaviour, or that
  is in an order that can't work;
- a risk of committing forbidden material or of losing others' work;
- breaking a rule in `CODE_STYLE.md`, `CONTRIBUTING.md` or "Names and formats".

**Minor** (reported, not fixed): wording, a check that could be sharper, a step
that could be simpler but works as written, or a style choice the rules don't
settle.
