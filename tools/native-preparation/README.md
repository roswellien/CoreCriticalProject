# Native preparation work in progress

This is the original-file generation boundary for the launcher installer and
signed native updates. It recompiles selected x86 routines to native AMD64
objects. It does not execute the original game, interpret game instructions,
load captured startup state, or substitute cached developer translations.

`export_recipe.py` and `export_control.py` run only during development. They
export addresses, lengths, hashes, symbols and optimization choices from the
selected private lineage. Recipes contain no original bytes, LLVM IR or objects.
The adjacent lineage receipt stays local.

`stage_tools.py` stages the pinned LLVM 21.1.8 and Remill toolchain, upstream
notices and authored lowering functions. It extracts computational adapter code
without its historical report paths or capture readers. It requires an existing
LLVM notice file if the local compiler installation lacks one. It does not
download dependencies or establish redistribution clearance.

The player-side prototypes read only explicit input paths:

- `translate.py`: ordinary translated bodies, heap and argument routines.
- `startup_entry.py`: the retail game entry.
- `startup_small.py`: command-line writer and the project-authored ABI shim.
- `startup_control.py`: CRT control and FDIV startup writer.

All tools and original inputs are hash checked. Each generated object must match
the selected build's full SHA256; the recipe restores the non-executable COFF
timestamp for reproducibility. Unsupported images, profiles, ABI shapes or CFGs
fail. Inputs remain read-only. Intermediate IR and all generated outputs are
private local derived material under the distribution policy.

`translate.py --resume` requires the identical producer, tool manifest, recipe
and component selection. It verifies completed objects and regenerates corrupted
or missing outputs. A Windows file lock prevents simultaneous writers. Worker
submission is bounded; one or two workers are supported. A final `generation.json`
and `objects.txt` are written only after every selected component succeeds.

Run the authored-only checks from the project root:

```powershell
python -m unittest discover -s tools/native-preparation -p test_preparation.py
```

`local_link.py` is a **private integration helper**, not a player-side preparer.
It replaces every game-code object in the selected Ninja link with the matching
freshly generated input, checks all 37,348 component identities, and retains the
seven existing authored host objects. The actual link requires the developer's
Windows SDK environment. It refuses an incomplete object set before creating an
output directory and never deploys or packages its result.
`finish_local_trial.ps1` can wait for one already-running producer, identified
by PID and creation time, then perform that private link after full success.
It starts no second producer and leaves the working launcher unchanged.

October 22: full generation (37,201 bodies), complete native linking (37,348
generated objects), and isolated live-menu/normal-close checks now pass. No
Training or mission acceptance is claimed. `link_translated.py` links the game
DLL without installed SDK/CRT import libraries; the separately shipped host
contains seven authored objects and synthetic import metadata.

`prepare_runtime.py` implements signed v2 preparation, verified prior-code reuse,
and owned resume work. `original_codec.py` derives the relocated codec from the
player's files. `bootstrap.cpp` starts bundled Python. Development exporters
`stage_preparer.py` and `build_source_update.py` package tools/recipes and the
authored host, excluding original images and the compiled translated game DLL.
The signed installer update/reuse integration passes. A fresh packaged first
install is running and remains unproven until final validation/activation.
Performance, production trust/feed, distribution review and clean-Windows tests
remain open. See the [October 22 handoff](../../docs/source-installer-integration-2026-10-22.md).

Evidence and continuation details:
[native generation preparation](../../docs/native-generation-preparation-2026-10-21.md).
