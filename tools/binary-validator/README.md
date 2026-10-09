# Binary identity validation

Python 3.11 or newer; standard library only. Run from the repository root:

```powershell
python tools/binary-validator/validate.py "C:/Games/MechWarrior3/Mech3.exe"
python tools/binary-validator/validate.py "C:/Games/MechWarrior3/Mech3.exe" --json
```

The example path is illustrative and is not evidence of the actual filename or
supported distribution. See [the manifest specification](../../docs/supported-binaries.md).
The supplied manifest initially has **no verified executable records**. Every
binary therefore fails validation until an evidence-backed record is added.

An exact SHA-256, size, machine, optional header format, image base and entry point
must agree. Filenames are informational. Renaming a file does not change identity.
The parser also validates its implemented metadata subset. This is identity
verification, not a claim that the binary is safe to execute or can be recompiled.

Exit codes: `0` verified identity; `2` unsupported identity; `3` malformed manifest
or PE; `4` I/O error. A missing file is never accepted. There is no hash override.

For reconnaissance of an unknown binary, use the separate
[metadata analyzer](../analysis/README.md). It labels unknown input explicitly.
