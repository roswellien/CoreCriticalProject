# Style checks

The rules for writing readable code are in [CODE_STYLE.md](../../CODE_STYLE.md). This
folder holds the tools that check layout and common mistakes, so people and agents get
the same answer.

Every check starts **report only**: CI shows how many files or findings each language
has, and nothing fails. Each language is switched on by its own small cleanup PR (see
below). Until then, `--fix` leaves that language alone, so a small change never turns
into a whole-file reformat.

## What each file is for

| File | Purpose |
| --- | --- |
| `check_style.py` | Runs every checker on tracked files and prints a count per language and check. Python standard library only. |
| `check_powershell.ps1` | Runs PSScriptAnalyzer, which only works inside PowerShell. Holds its pinned version. |
| `exclude.txt` | Files no checker reads or rewrites: frozen, hash-pinned evidence, third-party and generated code. |
| `requirements.txt` | Ruff and clang-format, pinned with every published hash. |
| `package.json`, `package-lock.json` | Prettier, pinned with its integrity hash. |
| `PSScriptAnalyzerSettings.psd1` | PowerShell layout rules (a copy of PSScriptAnalyzer's `CodeFormatting` preset). |

Settings for the checkers live at the repository root where editors find them:
`.clang-format` (C++), `.editorconfig` (C# and indentation everywhere), `ruff.toml`
(Python), `.prettierrc.json` and `.prettierignore` (JavaScript, CSS, HTML).

`exclude.txt` is the master list. The same lines are copied into `ruff.toml` and
`.prettierignore` so running those tools by hand can't touch excluded files either.
`check_style.py` stops with an error if the copies differ.

## Setup (Windows, PowerShell 7)

```powershell
python -m venv tools/style/.venv
tools/style/.venv/Scripts/python -m pip install --require-hashes -r tools/style/requirements.txt
npm ci --prefix tools/style
pwsh -File tools/style/check_powershell.ps1 -Mode Install
```

C# needs a .NET 8 SDK (`dotnet format` comes with it). On Linux and macOS the venv tools
are in `tools/style/.venv/bin`.

## Running it

```powershell
python tools/style/check_style.py                                # counts for every language
python tools/style/check_style.py --language python              # one language
python tools/style/check_style.py --preflight --language python  # pre-cleanup safety checks
python tools/style/check_style.py --verbose                      # also list each file or finding
python tools/style/check_style.py --list                         # which files each language checks
python tools/style/check_style.py --fix                          # format languages that are switched on
```

Exit codes: 0 when nothing switched on has findings, 1 when a switched-on check has
findings, 2 when a checker is missing, the wrong version or crashed.

## Switching a language on

Each language gets one cleanup PR for layout and, for Python and PowerShell, a later one
for lint findings. Never mix a cleanup with other changes. Steps:

1. Run the pre-cleanup safety checks and handle every hit:
   `python tools/style/check_style.py --preflight --language <language>`.
   For stored-hash hits, leave those files out of the cleanup by adding them to
   `exclude.txt`, or update the stored hashes and duplicate files in the same PR with
   the owner's approval. For text-read hits, check whether the callers depend on exact
   bytes or templates and exclude or adapt them.
2. Add the check to `ENFORCED` in `check_style.py`, for example `"python": {"format"}`.
   That is the only switch; the CI workflow needs no edit.
3. Run `python tools/style/check_style.py --fix --language <language>`.
4. Prove nothing but layout changed (cleanups require AST or token equivalence between
   the original and formatted files), then build and run every test the changed files touch.
5. Commit, then add that commit's hash to `.git-blame-ignore-revs` in a second commit so
   GitHub's blame view skips it.

For C++, keep includes whose order matters (such as `<initguid.h>` before `<ddraw.h>`)
in their own blank-line-separated block: clang-format sorts includes within a block.

## Versions

Every tool is pinned to an exact release at least one month old, in exactly one place:

| Tool | Pinned in |
| --- | --- |
| Ruff, clang-format | `requirements.txt` |
| Prettier | `package.json` and `package-lock.json` |
| PSScriptAnalyzer | `check_powershell.ps1` |
| Node.js, .NET SDK | `.github/workflows/build.yml` |

When bumping one, update [docs/dependencies.md](../../docs/dependencies.md) in the same
commit.
