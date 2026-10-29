# Release filenames

Every launcher installer and update release must follow these filename rules.

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
