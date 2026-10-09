# PE reconnaissance tooling

These Python 3.11+ tools use only the standard library. They read local input and
never load its DLLs, execute its entry point or extract game resources.

```powershell
python tools/analysis/analyze.py "C:/Games/MechWarrior3/Mech3.exe" --output reports/mw3.json
python tools/analysis/analyze.py "C:/Games/MechWarrior3/Mech3.exe" --require-supported
```

The example path is illustrative. The JSON report includes SHA-256, file size,
PE/COFF headers, entry point, section extents/flags, ordinary imports, named and
ordinal exports, forwarded exports, base relocation counts, API-family candidates
and an entry-point function seed named `sub_XXXXXXXX`. It contains metadata names
from import/export/section tables, not arbitrary game strings or code bytes.
The security directory uses a file offset; other directory addresses are RVAs.

Unknown input is permitted for reconnaissance and marked `unknown_binary` in the
report. `--require-supported` instead fails with exit code 2. Invalid structures
produce exit code 3; I/O failures produce 4. Passing a profile match proves only
the declared identity. Malformed profiles never silently become unknown input.

API categories are candidate labels derived from DLL names and imported symbol
prefixes. They do not establish subsystem boundaries, function reachability,
rendering API versions, or dynamically resolved behavior. Direct3D COM method
calls in particular will need call-site and vtable analysis. Ordinal imports
remain ordinals until resolved against the appropriate user-supplied DLL version.

## Optional local disassembly

Install LLVM independently and put `llvm-objdump` on PATH, or supply its absolute
path. The project does not fetch an executable or install a disassembler.

```powershell
python tools/analysis/disassemble.py "C:/Games/MechWarrior3/Mech3.exe" --output reports/mw3-disassembly.txt
```

The adapter checks PE32/i386 structure, selects file-backed sections marked
executable, and invokes `llvm-objdump --disassemble --no-show-raw-insn
--x86-asm-syntax=intel` with each selected section. Arguments are passed without a
shell. Output is written atomically after success; the default timeout is 60
seconds. LLVM is optional, so this command fails clearly when it is unavailable.

Disassembly can contain protected expression even without raw-byte columns.
Keep it in ignored private research storage. Do not commit bulk disassembly or
generated code from proprietary inputs. A linear sweep can decode data as code;
neither section flags nor this output recover trustworthy function boundaries.
Review the entry point, exports, branch targets and call targets in a separately
installed Ghidra or another analysis tool before selecting the first function.

## Limits and testing

The parser accepts PE32/i386 only, at most 512 MiB, 96 sections and 65,536 entries
per export/import/relocation table. It rejects overlapping sections, out-of-file
reads, virtual-only data-directory content and unterminated metadata. These are
deliberate bounds for reconnaissance, not a complete model of the Windows loader.
Certificates, debug formats, resources, TLS callbacks, delay/bound imports, x87,
SSE/MMX, SEH, RTTI, globals, strings, indirect control flow and function boundaries
are not decoded. There is no translator or interpreter in this directory.

```powershell
python -m unittest discover -s tests -p test_binary_tools.py -v
```

Fixtures are generated from project-authored bytes at test time and held in a
temporary directory. They are unrelated to proprietary game executables. Tests
of the disassembler adapter mock its host tool invocation; LLVM integration must
be checked separately when an actual tool is available.

## Reviewed MW3 slice extraction

`extract_mw3_leaf.py` admits only the reviewed `sub_00409ED0` slice from the exact
supported MW3 1.2 image. It verifies the full image identity, pinned metadata,
raw/virtual mapping, section permissions and slice digest before writing bytes.
Output must be in ignored `reports/`, `local/` or `recomp/generated/` storage.
It does not relocate code, resolve imports, initialize the PE image or execute it.

```powershell
python tools/analysis/extract_mw3_leaf.py MW3/Mech3.exe
```

See the [function dossier](../../games/mw3/docs/first-function.md). Six local
admission controls passed; game-derived bytes are not part of public CI. Real
LLVM 21.1.8 integration has now run on the installed image, with metadata imports
cross-checked against `llvm-readobj` and the leaf decoded independently by
Remill/XED. The bulk linear view still does not recover whole-image boundaries.
