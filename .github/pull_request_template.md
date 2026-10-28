<!-- Title: <Verb> <area>: <what changed>. Branch: <username>/<type>/<issue>-<slug>. See "Names and formats" in docs/github-workflow.md. -->

## Change

<!-- Describe the problem and the resulting behavior. -->

Closes #<!-- Issue number. Every task has one; file it first if needed. Delete this line only in a release or sync PR. -->

<!-- Native behavior: name the execution boundary changed and the original comparison or fixture used. -->

## Validation

<!-- List the relevant checks and any remaining limitations. -->
<!-- Describe actual behavior/coverage; do not append the historical startup-audit fraction. See docs/project-status-reporting.md. -->

- [ ] Correct base: `develop` for feature/fix or synchronization work; `main` for a release from `develop`.
- [ ] Changes are task-scoped; unrelated work and private/generated inputs are excluded.
- [ ] Relevant checks and remaining limitations are recorded above.
- [ ] Each acceptance criterion of the issue is listed above with where this change meets it. (Skip for a release or sync PR.)
- [ ] Tests: extended ___ (name the test), or added a new file because ___; each new or changed test was seen failing with its behavior broken. (Skip if no tests changed.)
- [ ] A change players or modders would notice was run in the launcher or game, with a log line or screenshot above, or the reason it wasn't and a "Playtest <what to check>" issue filed. (Skip for documentation only.)
- [ ] Reviewed by someone who didn't write it; findings are fixed or listed above.

## Release impact

<!-- Note launcher/runtime/pack implications, or state that this is documentation only. -->

<!-- See docs/github-workflow.md. Opening this PR does not merge it or publish a release. -->
