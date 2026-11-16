# Original mech headlight placements

`original-mounts.json` is owner-authored placement metadata for the 18 original
MW3 mech models. Its model SHA-256 values identify the source models; the file
contains no original media. The placements are staged as an MWHDLT1 runtime
catalog by `tools/remaster-launcher/build_stock_headlights.py`.
For each profile, the catalog's required 32-byte identity is the raw digest bytes
of `model_sha256`; this ties it to the same model identity used by stock binding.
