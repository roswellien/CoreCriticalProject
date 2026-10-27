# Project status reporting

Owner direction, October 27, 2026: report progress through demonstrated native
functionality, relevant fidelity/compatibility coverage, known defects and
release validation. The historical startup-initializer audit is not the current
project progress indicator or the default implementation queue.

## Routine reports and PRs

Describe the concrete result and its evidence:

- **Native execution:** the path exercised, such as startup, menu interaction,
  mission loading, combat, save/load or shutdown, with its tested scope.
- **Fidelity and compatibility:** what was compared with the original, the
  hardware/configuration tested, and what remains unverified.
- **Known defects:** reproducible failures and their practical impact. Identify
  current blockers from current evidence, not from an old unfinished audit.
- **Release readiness:** source commit, launcher/runtime/pack versions and
  applicable signing, install, update, rollback and download checks.

For example: "The native host loaded Instant Action and presented 3,000 frames
with the selected packs; it stopped at the configured budget. Broader campaign
and external-PC coverage remain open." This is a bounded execution result,
not a whole-game completion claim.

Do not append an unchanged startup fraction to routine status updates, PRs,
release notes or documentation-only changes. Do not invent a replacement project
percentage. State implemented, tested, blocked and unknown behavior explicitly.
Probes, saved-scene replay and original-process hooks must still be identified
as such; they do not establish live native gameplay by themselves.

## Historical startup-equivalence audit

The [October 10 acceptance record](m4-progress-startup131.md) accepted 131 of
144 selected startup initializers under that audit's original/native comparison
requirements. Its continuation was paused on October 13. The later
[native execution record](session-summary-2026-10-13-native-host.md) separately
records execution through all 144 initializers, live menus, Training, Instant
Action and normal shutdown. Execution and formal equivalence acceptance are
different claims.

Retain the audit, its receipts, criteria and known limits as historical evidence.
Do not rewrite the accepted count, claim its remaining reviews passed, or
discard required initializer behavior. When the audit itself is the subject,
label it **historical startup-equivalence audit — paused**, give its dates and
explain the scope. It is not a current menu/game completion percentage, a list
of current bugs, or a prerequisite for routine development and playtest releases.

Do not restart the old composer/review/acceptance chain or report its unresolved
paperwork as a present runtime blocker without an explicit audit-resumption
request or a concrete current defect requiring that investigation. Required
guest ABI, floating-point, memory, resource and initialization contracts still
apply. Validate affected behavior and fail unknown required services visibly.

This reporting change grants no new formal milestone credit and does not relax
original-game fidelity, meaningful testing or release requirements.
