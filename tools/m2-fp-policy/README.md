# Consolidated M2 floating-point policy evidence

This new offline supplement leaves every previous source/worker/contract/report
unchanged. Read [the policy](../../docs/m2-floating-point-policy.md) for the
exact admitted domains and remaining live-state acceptance requirement.
No game assets or game session are required by the authored controls.

From `D:\Projects\MW34Recomp`, using the pinned local Python runtime:

```powershell
& C:/Python314/python.exe -m unittest discover -s tests/m2-fp-policy -v
& C:/Python314/python.exe tools/m2-fp-policy/run_controls.py
& C:/Python314/python.exe tools/m2-fp-policy/exercise_workers.py
& C:/Python314/python.exe tools/m2-fp-policy/freeze_evidence.py --verify
```

The worker recipe requires all three previously accepted families' current
frozen workers/build records and tools. Missing files or changed identities
fail. It reruns complete corpora, then uses valid full corpora with only the
last record changed for an unsupported operand/CW. Fixture controls prepend
FNCLEX, FNINIT or FILD64 and require the code-identity admission diagnostic.
Original, O0 and O2 must all exit1 with zero result bytes for every exclusion.
Existing negative output files cause failure; successful negatives create none.
Only new report files are written.

`build_profiles.py` originally recovered public authored vector tables from
three frozen protocols. `policy.py` admits only its exact hashed manifest and
returns no execution permission. `run_controls.py` saves real control counters.
`freeze_evidence.py --create` establishes a new reviewed identity bundle; it
must not be used to overwrite a frozen bundle after any input changes.
Use `--verify` to rehash the existing bundle without modifying files.

The supplement measures exclusions and exact record replay. It does not
implement invalid integer conversion, two-NaN selection, arbitrary NaN
payloads, unmasked traps, guest exception clearing or exceptional-exit FP
restoration. Live-state profiles remain pending. Earlier failures and their
historical status masks are preserved.
