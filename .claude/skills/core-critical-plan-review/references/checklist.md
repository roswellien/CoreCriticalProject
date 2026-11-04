# Plan review checklist

Read the plan, its spec and every file the plan names or will change. Check
each area and write down a finding for each problem. Be specific: "step 3 runs
`check_style.py --fix-all`, but the option is `--fix`" is a finding; "some
commands may be wrong" is not.

## Before each pass

Do these on every pass, not only the first; a later pass that relies on an
earlier read misses what the fixes changed.

1. **Branch:** `git fetch origin`. If the plan starts a new branch, read files
   as they are on `origin/develop`; if it continues an existing branch, read
   them on that branch, up to date with its remote. If you can't tell which,
   ask.
2. **Rules:** reread `AGENTS.md`, `CONTRIBUTING.md`, `CODE_STYLE.md` and
   `docs/github-workflow.md`, plus any instruction file (`AGENTS.md`,
   `README.md` with rules for its folder) in a folder the plan touches.
3. **Stack:** confirm the languages and build setup from the project files the
   plan touches (`CMakePresets.json`, `.csproj` files, `requirements` files,
   `website/build.py`), not from memory.
4. **Files:** read every file the plan creates or changes as it is today, and
   the files those depend on where that matters for correctness.
5. **Users:** for anything the plan renames, removes or changes (a function,
   type, file format, config key, command option, documented command or
   heading), search the repository for every place that uses it.

## What to check

1. **Completeness:** does every part of the spec's scope and every acceptance
   criterion have a step? Does every step name its files, what done looks like
   and how it is checked? Are the follow-on changes there: config, dependency,
   test and doc updates, and every file that uses something the plan changes?
   Does the plan end with exact build, lint and test commands, and hand over to
   the review stage?
2. **Accuracy:** do the files, functions, headings, commands, presets and
   paths it names exist as written today? Does code the plan proposes match
   the existing includes, imports, types and module layout? Are version
   numbers, tool names and command options right? Does the overview describe
   what the steps actually do? Are the branch name and base right? Do its facts
   about other issues and PRs still hold (`gh issue view`, `gh pr view`)?
3. **Redundancy:** does any step duplicate another, or rebuild something that
   already exists in the repository and should be reused? Could two steps
   merge without losing clarity? Does a step create a file that a later step
   replaces? Is the same logic written in two places?
4. **Bugs:** would any step, done as written, produce wrong code, a wrong
   command or a broken file? Are steps in an order that works? Look for
   unhandled errors, broken control flow, and edge cases: empty input, a
   missing tool or environment variable, two runs at once. Do changed file
   formats and command options still work for what already reads or calls
   them? Does the plan assume a shape of data that isn't what the code holds?
5. **Sanity:** is this the simplest plan that meets the spec? Is anything done
   that the spec didn't ask for? Do any steps depend on each other in a
   circle? Does the overview contradict a step? Is each code step one commit
   that leaves the build and tests passing on its own, so nothing only works
   once a later step lands?
6. **Security and distribution:** does any step risk committing original game
   media, generated game code, private build outputs, credentials or signing
   material, or staging files by folder instead of by name? Does each step with
   a security concern say so at that step, specific to the change, rather than
   in a separate section? Where the plan touches the website's server
   functions, the update service, launcher downloads, or tools that read files
   a user supplies, check as it applies:
   - who may call or change it, and whether anything skips that check;
   - data it could expose in responses, logs or error messages;
   - input validation, and whether input can reach a command, path or query;
   - where secrets are read from, and whether any could be committed;
   - transport, CORS, cookie and header settings;
   - limits against abuse or runaway use;
   - new or upgraded dependencies: known problems, maintenance, permissions;
   - logging that records failures without recording secrets.
7. **Regressions:** what existing behaviour, tests, CI jobs or docs could the
   change break, and does the plan check them? Does anything else use what a
   step renames or removes? Do other callers of a changed shared helper still
   work? Could a changed path, format or setting break launchers, packs or
   installs already out with players? Does the plan update or mention the
   tests that cover the behaviour it changes?
8. **Conformance:** does the plan follow `CODE_STYLE.md`, `CONTRIBUTING.md` and
   "Names and formats" in `docs/github-workflow.md` (branch, commit subjects,
   PR title, labels, PR template)? Does it start from `origin/develop` and
   target `develop`? Does each step that changes files end with its own
   commit?
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
