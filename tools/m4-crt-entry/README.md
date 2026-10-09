# CRT entry preparation

This isolated preparation compiles all eleven exact game CRT entry/helper
roots into x64 objects. It does not link or launch a native game.

From the workspace, run each command with a fresh output directory:

```powershell
& 'C:/Python314/python.exe' tools/m4-crt-entry/prepare.py reports/m4-crt-entry/preparation-r3
& 'C:/Python314/python.exe' tools/m4-crt-entry/adapt.py reports/m4-crt-entry/native-preparation-r2
```

The adapter consumes the frozen, hash-checked `preparation-r2` baseline;
the first command independently reproduces the source preparation. Existing
outputs reject rather than being replaced. Source and generated artifact
identities are bound in each report and `pins.json`.

The native objects deliberately require unimplemented checked bridge symbols.
Guest addresses remain 32-bit values, all named State type layouts are
verified against the x64 layout, and no original code or provider is executed.
Eight direct calls use the required dispatcher and all eleven entries require
an ownership check. Undefined arithmetic flag behavior still requires an
explicit reviewed representative at its bridge.

See [the CRT entry preparation record](../../docs/m4-crt-entry-preparation.md)
for required integration stages and the remaining full startup scope.
