# M2 next-slice admission

`admission.py` validates an asset-free isolated guest context and always blocks
execution until the exact real function translation and comparison are reviewed.
It has no guest interpreter, native body substitute, API stub or game launcher.

Run public controls:

```
C:/Python314/python.exe -m unittest discover -s tests/m2-slice-admission -v
```

Run the required private image check (missing/wrong input fails):

```
C:/Python314/python.exe tools/m2-slice-admission/inspect_image.py --image MW3/Mech3.exe
```

Full image/disassembly evidence remains in ignored local reports. The public
sources contain identities and contracts, not proprietary executable bytes.
See `docs/m2-next-slice-context.md` for the complete function choice and context.
