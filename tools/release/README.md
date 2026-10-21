# Release preparation tools

These commands create local review candidates. They do not push source, create
a GitHub release, change visibility or include original game content.

## Mod Tools source preview

From the repository root:

```powershell
python -B tools/release/build_mod_tools.py --output-dir reports/releases/mod-tools-review-1
```

Use a fresh output folder. `mod-tools-files.json` is an explicit list of source,
launch scripts, setup and notices. The builder checks the Three.js source hashes,
rejects missing/external/duplicate paths, writes a repeatable ZIP, embeds the
per-file `PACKAGE-CONTENTS.json`, and writes `SHA256SUMS.txt` alongside it. The
ZIP does not include the checkout's `local/`, game archives, extracted preview
geometry, exported maps, binaries or Python environment.

Extract the candidate outside the checkout into a folder with spaces. Follow
`MOD_TOOLS_README.txt` and [setup](../../docs/setup-mod-tools.md), then verify
`Setup Mod Tools.cmd --check`, editor imports, selected archive catalog loading,
cache ownership and original-file conservation. The initial source preview is
not a validated portable Studio export/play release.

Run the asset-free package and request-boundary tests with:

```powershell
python -B -m unittest discover -s tests -p test_release_tools.py -v
```

CMake also registers them as `release_and_mod_tools`. Local game integration
scripts under the editor's tests require an installation and converter tools;
do not put proprietary data in CI to satisfy them.

## Game / Launcher package

There is no equivalent complete package command yet. The existing
`tools/mw3-remaster-launcher/installer.iss` packages the development GUI, not its
private runtime/preparation dependencies. Its development labeling and repository
URL are corrected, but it has not been compiled or validated as an installer in
this preparation pass. Do not create a game ZIP by recursively copying the current
host, asset registries or `local/` directory.

Close the reproducible local-generation, binary-admission, notices, user-data and
fresh-install criteria in [release readiness](../../docs/public-release-readiness.md)
before implementing or publishing a playable installer. Original-code execution
is not an authorized production fallback, and generated game code stays local
under the existing policy. Neither package earns native-game acceptance credit.
