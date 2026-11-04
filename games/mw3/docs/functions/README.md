# Function write-ups

What each studied function in `Mech3.exe` does, and why it has the name it has.
[`../../symbols/functions.tsv`](../../symbols/functions.tsv) is the index: one
line per function, with its evidence column pointing at the function's section
here. The table's own rules (address format, names, confidence words) are in
the [symbols README](../../symbols/README.md).

The files are grouped by what the code is about, one topic per file, one section
per function. A new function goes in the topic file that fits what it does; a
new topic file is added only when none fits, and is listed below.

| Topic file | What it covers |
| --- | --- |
| [`containers.md`](containers.md) | Standard-library vector and list helpers the game uses |
| [`globals.md`](globals.md) | Building the game's global objects at startup |
| [`heap.md`](heap.md) | Allocating and freeing memory |
| [`objects.md`](objects.md) | Object constructors and the game's list of numbered objects |
| [`startup.md`](startup.md) | The C runtime startup that runs before the game's own code |
| [`textures.md`](textures.md) | Loading textures from the game's texture banks |

## Repeating the work

Every write-up covers the profile `mw3-us-1-2-retail`, image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. Import your
own copy of that `Mech3.exe` into Ghidra 12.1.3 with the default analysis, then
go to each address. Addresses are virtual addresses at image base `0x400000`;
an RVA is the address minus `0x400000`. Write-ups name functions by address,
never by Ghidra's labels, which differ between projects. Import slots are
checked against [`../imports-mw3-us-1-2-retail.csv`](../imports-mw3-us-1-2-retail.csv).

Never copy executable bytes or decompiler output into a write-up. Describe what
the code does in your own words, with addresses.

## Section format

Each function gets a heading `## sub_XXXXXXXX` (address in uppercase; links use
the lowercase anchor, `#sub_xxxxxxxx`) and these fields, in this order:

- **Name and confidence:** the table's name and confidence word.
- **Kind:** import thunk, statically linked Microsoft library code, the game's
  own code, or a merged body that stands for several functions.
- **Extent:** first and last address, and size in bytes.
- **Callers:** how many functions call it, a few examples, and how they use it.
- **What it does:** every step, including each branch.
- **Reads and writes:** memory, globals and import slots it touches.
- **How the host reaches it:** which native host file runs or checks it. This is
  context only: the host runs a lifted copy of the original code, so it never
  proves a name.
- **Why this name:** the proof, under the rules below.
- **Still unknown:** what the section can't settle.

[`startup.md#sub_005ac5a0`](startup.md#sub_005ac5a0) is a worked example.

## Proof needed for `confirmed`

- **Import thunk:** a single jump through an import slot. Its name is the
  imported name in the import CSV. A slot imported by number only needs a cited
  source that maps the number to a name; without one the row stays `likely`.
- **Statically linked library code:** its steps match the known Microsoft
  runtime or MFC routine, compared step by step, and its callers use it that
  way.
- **The game's own code:** every step of its behaviour is described, including
  each branch; its callers are listed and agree with that reading. A branch
  that can never run counts as described when the section says why it can't.
- **Merged body:** one body that the linker shares between several identical
  functions. Every instruction is described; the section gives the caller count
  with a few examples instead of listing them all, since the body alone settles
  what every caller gets. A library name that fits only some callers goes in
  the section, not the table.

Anything short of that keeps its `sub_` name and is `likely` (a strong reading
with one gap) or `guess`.

## Names

A library routine keeps its official name, written as a C identifier
(`operator new` becomes `operator_new`; leading underscores stay, as in
`_initterm`). The game's own code gets an `Area_Action` name, such as
`GameHeap_Free`. A merged body that no single official name fits gets an
`Area_Action` name for what it does, such as `Stub_Return`.
