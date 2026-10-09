# REA / Ghidra evaluation tools

Static-only tools for the exact admitted MW3 executable and staged MSVCRT DLL. They never execute or alter the original binaries and confer no initializer acceptance.

`initializer_inventory.py OUTPUT` verifies the known game SHA and reads the actual 145-DWORD table at `5E0000..5E0244`. It writes 144 unique nonzero function-entry seeds to a fresh receipt. This is separate from Ghidra's default function inventory.

`headless_pilot.py --mode provider|game --output FRESH_DIRECTORY` imports an artifact into a fresh persistent Ghidra project, exports representative functions, and repeats the export using `-process -noanalysis -readOnly`. The Java postscript verifies artifact identity, conservatively seeds game entries without replacing overlapping functions, and exports body ranges, bytes, instructions, calls and pseudocode. The Python runner verifies every exported body range against the original PE and retains logs, timings and hashes.

The game pilot establishes table-entry availability and representative export behavior. It does not establish all 144 function boundaries, ABI contracts, or native execution correctness. Provider import names can reflect the current host export cache; they require checking against the staged provider and original execution.

Keep each completed pilot directory frozen. Keep its Ghidra project for reuse; new exports and refinements belong in a fresh output receipt. The measured REA neutral snapshot retained evidence but did not eliminate cold Ghidra initialization. Related REA requests should share one open target.

See [evaluation](../../docs/m4-tooling-evaluation.md) and [execution plan r4](../../docs/m4-execution-plan-r4.md) for the adopted division of work. Exact instruction translation and original/native validation remain in the existing Remill/LLVM pipeline.
