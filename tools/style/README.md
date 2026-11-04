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
| `style_preflight.py` | The pre-cleanup scans behind `check_style.py --preflight` (stored hashes and text reads). Python standard library only. |
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
python tools/style/check_style.py --fix --files <path> ...       # format only these files (the git hook uses this)
```

Exit codes: 0 when nothing switched on has findings, 1 when a switched-on check has
findings, 2 when a checker is missing, the wrong version or crashed.

## Switching a language on

Each language gets one cleanup PR for layout and, for Python and PowerShell, a later one
for lint findings. Never mix a cleanup with other changes. Steps:

1. Run the pre-cleanup safety checks and handle every hit:
   `python tools/style/check_style.py --preflight --language <language>`.
   Digest-only hits are candidates, not proof of a path-specific pin; verify the
   associated path before changing a stored hash. Both scans look only at the files
   the formatter would change, since a file whose bytes stay the same can't break
   whatever reads it. Before a lint cleanup, add `--check lint`: both scans then look
   at the files with lint findings instead. The text-read search prints one line per
   place to check, in three kinds:
   - `tools/a.py:12: reads runtime/b.py`: the line names that file by its path.
   - `tools/a.py:12: names b.py (could be 2 files: x/b.py, y/b.py)`: the line names
     only a file name, so check which of those files it means.
   - `tools/a.py:12: lists files (.py)`: the line lists a folder (`glob`, `walk`,
     `Get-ChildItem` and so on), so it may read any changed file of those types, or of
     any type when the script names none. The types come from anywhere in the script,
     not just that line, so a script that names only other types (`*.txt`) is left out.
   Folder listings inside `tools/m4-*/` and `tools/x87-*/` are not reported. Those
   folders hold frozen evidence scripts that can't change, and the stored-hash scan
   still finds any of them that keeps a changed file's hash in the repository. A
   frozen script that finds files only by listing a folder and keeps its hashes
   outside the repository is not reported. An
   unreadable input makes preflight exit with an error instead of reporting an
   incomplete scan. A code file that isn't valid UTF-8 is still searched: the
   text-read search reads it as Latin-1, which keeps every byte.
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
