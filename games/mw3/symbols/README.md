# Symbol evidence

What is known about the original game's functions. The game code is lifted from
`Mech3.exe` into LLVM IR that nobody reads directly, so this folder is where its
functions get explained.

## Function table

[`functions.tsv`](functions.tsv) has one line per function in `Mech3.exe`: where
it is, what it is called, how certain that is, where the proof is, and what it does. It
covers one binary, profile `mw3-us-1-2-retail` (image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`, see
[supported-binaries.json](../config/supported-binaries.json)); another version
would get its own table. Rows are added as functions are studied (about 6,500 to
7,000 in all).

The file is UTF-8 text with LF line endings, one tab between columns and no
quoting, so spreadsheets, `csv` and `awk` read it as is. The first line is the
header; every other line is one function. No blank or comment lines.

| Column | What goes in it |
| --- | --- |
| `address` | Entry virtual address, 8 uppercase hex digits, no `0x`: `00409ED0`. Rows are sorted by address, each address once. |
| `name` | `sub_<address>`, for example `sub_00409ED0`, until the function is confirmed. A confirmed row may get a real name: a C identifier (letters, digits, underscore) that no other row uses and that doesn't start with `sub_`. |
| `confidence` | `guess`, `likely` or `confirmed`, as in [CODE_STYLE.md](../../../CODE_STYLE.md). It applies to the purpose, and to the name when it isn't `sub_`. |
| `evidence` | Where the proof is: a repository path with forward slashes, such as `games/mw3/docs/first-function.md`, optionally with `#heading`, or `none`. Any path given must be a file committed to the repository; a local-only file, such as a private report under `reports/`, doesn't count. A confirmed row must give a path. |
| `purpose` | One line saying what the function does, with no spaces at the start or end. A function nobody has studied yet gets `guess`, `none` and `unknown`. |

To add or change a row: keep the rows in address order, keep the `sub_` name until
the function is proven, point a confirmed row at its evidence, and run
`python -B -m unittest discover -s tests -p test_function_table.py -v`, which
checks every rule above.

## Evidence records

Longer evidence goes in a record here or a dossier under [`../docs/`](../docs/).
Per-function write-ups, one section per function grouped by topic, are in
[`../docs/functions/`](../docs/functions/README.md). Record entries with binary SHA-256, RVA, original label (`sub_XXXXXXXX` for
unknown functions), evidence, confidence and any supported alias. Bounded
camera/controller dataflow is recorded in the
[camera history evidence](../../../docs/fidelityfx-camera-history.md). A function
keeps its `sub_XXXXXXXX` name until it is confirmed; these records do not
establish whole-game fidelity or original/native equivalence. Do not copy executable bytes here.

[`sub_00409ED0`](sub_00409ed0.json) has a reviewed static
[contract](../docs/first-function.md), exact image/slice digests and an extraction
tool. Its native code matched the original in the G2 comparison recorded in the
dossier; a gameplay name remains pending. The record's `review_status` keeps its
first static-review label because `tools/analysis/extract_mw3_leaf.py` reads the
record and refuses to run unless it matches a copy pinned in the script, so don't
edit or reformat it.
