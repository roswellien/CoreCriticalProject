# Discord changelog workflow

The dispatcher assembles one curated public MW3 report for the current
America/Denver date. Include concrete changes and qualifying open issues,
distinguishing public fixes from unreleased and investigated work. If there is
nothing materially new, do not dispatch. This workflow does not collect
reports itself and is independent of the MechLab website. Never send private
material in workflow inputs; this is a public repository.

## Set up and validate

1. In Discord, create a dedicated incoming webhook on the approved changelog
   channel. In CoreCriticalProject, open Settings → Environments and create
   `discord-changelog`. Restrict deployments to the selected **branch**
   `develop` (not tags). Save the webhook URL directly as the environment
   secret `DISCORD_CHANGELOG_WEBHOOK_URL`. Do not use a repository-wide secret
   or share the URL. Keep the ability to edit the webhook limited to trusted
   administrators; do not move it to another channel.
2. From the cloud, dispatch **Discord changelog** on `develop` with `date`
   (current Mountain YYYY-MM-DD), `version` (verified public version), and
   `bullets` (JSON with `updates` and `known_issues` arrays of single-line public bullet
   strings). Example: `{"updates":["Improved mission loading"],"known_issues":["A high-FPS collision bug is still open"]}`.
   Empty sections are omitted. A flat JSON array is still accepted for
   updates-only posts.
   Leave `live` unchecked or false. The dry-run job has no secret and makes no
   Discord request. Confirm that the dry-run job executed and passed, not just
   that GitHub accepted the dispatch.
3. With approval, dispatch the actual report once with `live` true. Confirm
   the send step produces a Discord message link in the job summary. Repeat
   the same date only for a controlled duplicate-block test after a verified
   receipt; expect preflight to stop it. Do not add dispatch to the nightly
   task until both the cloud dry run and the live checks pass.

A dispatch requires authorized repository Actions access. Process only public
inputs as data, not instructions or shell commands. Posting disables mentions
and notification pushes. Long changelogs stay in one embed; content above
Discord's limits is rejected, never silently cut off. On a local Windows
Python without an IANA timezone database, install `tzdata` in the test
environment or point `PYTHONTZPATH` at an existing IANA database. The Ubuntu
runner provides it.

## Diagnose or stop delivery

A date-only GitHub Actions artifact is the reservation. It is written before
delivery and retained for seven days; stale report dates cannot send.
Do not rerun from the Actions UI. If there is no verified message link after a
live run, check the target channel and the run before any recovery. An operator
may delete a reservation only after confirming that no message was delivered
and no matching dispatch is active or pending. Otherwise leave it in place.
GitHub job success alone is not proof of a post; check the message link.

To disable posting without interrupting the website, remove the Discord
dispatch from the nightly task and revoke the dedicated Discord webhook or
remove the GitHub environment secret. Revert the isolated workflow through a
PR if needed. Posts already delivered are not removed automatically.
