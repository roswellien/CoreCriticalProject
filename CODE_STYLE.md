# Code style

How to write code in this repository, for people and AI agents alike. It builds on
[Readable, maintainable code](CONTRIBUTING.md#readable-maintainable-code) in
CONTRIBUTING.md and [How code should explain itself](docs/code-guide.md#how-code-should-explain-itself)
in the code guide; read those too.

## Write for a junior developer

Assume the next person to change this code is new to the project and to the language.

- Prefer clear over clever. No dense one-liners, chained ternaries or tricks that need a
  second read.
- Give intermediate results a name. An explaining variable such as
  `tool_finished_normally = exit_code in (0, found_code)` says what a condition means.
- Pull a step into a named helper when the name explains something the code doesn't.
  Don't split a function just to make it shorter.
- Spell names out: `surface_width`, not `sw`. Short names are fine for loop counters
  and well-known terms (`rva`, `fp`).

## Comments say why

- Explain why a constraint exists, a binary layout, units, ownership, lifetimes and
  unusual ABI or floating-point behaviour.
- Never restate what the code already says.
- Write enough that someone who wasn't in this project's chats can follow it.

## Unproven game functions

- Keep unproven original functions named `sub_XXXXXXXX`. A name needs evidence; a guess
  is not proof.
- In maintained code that calls one, describe what you think it does in a comment, with
  a confidence word (guess, likely, confirmed) and where the evidence is, in this shape:
  `// sub_XXXXXXXX: <what it seems to do> (<guess|likely|confirmed>; evidence: <where>)`
- Evidence records live in [games/mw3/symbols/](games/mw3/symbols/README.md).
- Never add such comments to files on the exclusion list below; those notes go in the
  symbols records instead.

## Formatting and checks

- Layout is decided by tools, not by hand: clang-format (C++), Ruff (Python),
  `dotnet format` (C#), Prettier (JavaScript, CSS, HTML) and PSScriptAnalyzer
  (PowerShell), all at 100 columns. Setup and versions: [tools/style/README.md](tools/style/README.md).
- Before committing, run `python tools/style/check_style.py --fix`. It only formats
  languages whose one-time cleanup has landed, so a small change never becomes a
  whole-file reformat. Don't mix a formatting pass with other changes.
- Never reformat, rename or "clean up" anything in
  [tools/style/exclude.txt](tools/style/exclude.txt): frozen, hash-pinned evidence,
  third-party and generated files.

Checks switched on today: web format (JavaScript, CSS, HTML). Every other language is
report-only until its cleanup PR lands; CI shows the counts on each run.
