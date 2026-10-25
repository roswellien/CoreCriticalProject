# Current project direction

Read `docs/faithful-modernization-plan.md`, `docs/roadmap.md` and
`docs/m4-Codex-work-review-2026-10-11.md` before choosing implementation work.
The execution-first strategy was authorized on2026-10-11: preserve original
MW3 gameplay through recompilation, integrate modern platform services/Vulkan,
and advance native host -> live menu -> live Training. Do not restart as a remake.

Keep existing acceptance criteria and evidence intact. Last verified count is
131/144; probes, replay and original-game hooks do not grant native-game credit.
The detailed acceptance lane is retained in `docs/m4-execution-plan-r14.md`, but
it is not the sole implementation queue. Legacy priority text is historical
where it conflicts with the current strategy; guest ABI/FP/resource contracts
and required initialization effects still apply.

Inspect current process identities before expensive work. Protect the existing
controls composer/watcher and never open active SQLite or duplicate a long job.
Use admissionv2 after actual successful closure and independently review the
post-composer chain. Preserve uncommitted work and other graphics/asset writers.

State the execution boundary advanced by each change and run narrow meaningful
checks. Add no verifier/report layer without an identified missing criterion or
concrete defect. Fail unknown required services visibly; no AFTER seeding or fake
API success. No production interpreter/original-code fallback is authorized.

Read `CONTRIBUTING.md` and `docs/legal.md`; original media and generated game
code stay local. Full continuation instructions are in
`docs/Codex-m4-continuation-handoff.md`. Do not commit unless the user asks.

## Required launcher installer filenames

Every launcher installer download must retain its release version in the actual
filename: `corecriticalinstaller-<version>.exe`, for example
`corecriticalinstaller-1.0.34-preview.exe`. This applies to the built artifact,
cloud/R2 object basename, website link, download filename, instructions and
checksums. A versioned folder or link label does not satisfy this requirement.
Publish the exact `setup_filename` from the installer build receipt; never
rename a new release to `corecriticalinstaller.exe` or another unversioned name.
Preserve historical release evidence and existing compatibility URLs.

## Required update filenames

All future update releases must use the public release version as the filename
stem, with the correct lowercase product extension:

- Game runtime: `<version>.<game-abbreviation>update`, for example
  `1.0.34.mw3update` or `2.0.0.mw4update`. Use the game's registered file stem
  (`mw3`, `mw3pm`, `mw4`, etc.); the placeholders do not impose a length limit.
- Core Critical Launcher: `<version>.ccupdate`, for example `1.0.34.ccupdate`.

Do not prepend product names or substitute descriptive build/task IDs for the
release version. Apply this rule to packaging scripts, release checks, site
links and instructions before publishing. Keep matching payload ZIP names and
signed metadata references consistent. An optional download wrapper ZIP must
also identify its version and target and contain the correctly named update;
renaming ZIP bytes to an update extension is not a valid conversion. Preserve
published historical artifacts and their verification evidence.
