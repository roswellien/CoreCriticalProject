# Independent stock-model texture pack — 2026-10-24

The user requested a separate stock-model texture pack alongside the combined
18-model replacement collection. DEV now has `MW3 Stock Model Textures` 1.1.0,
retaining the existing `com.mw3remaster.textures.shared-mechs` ID. It upgrades
textures on original MW3 geometry and contains no replacement meshes. It is
independently selected from `MW3 Remastered Models` 1.2.0.

To use original geometry with upgraded textures, disable MW3 Remastered Models
and leave MW3 Stock Model Textures enabled. Keeping both enabled uses replacement
models where available, with stock texture banks available for original-model
rendering. Turning off the stock pack removes its bank/normal bindings.

The stock pack retains both shared original-model texture banks, original B–H
liveries and existing authored normal images. It incorporates the approved
sharper Black Hawk and Champion repairs that had remained outside the installed
shared pack: 51 changed records across the banks. Dimensions, descriptors,
RGB565 layout, UV contract, record spans and offsets are unchanged. Every other
bank record, including alternate skins and unrelated damage records, compares
byte-for-byte equal to the previous installed shared pack.

Existing normal registration behavior is preserved. Two revised full-color
identities are bound to their existing reviewed normal images; all 711 original
normal keys remain, yielding 713 keys in three pages. The other 49 changed
records had no matching normal registration and remain unregistered; no normal
image was invented. Normal image pixels are unchanged.

Archive: `mw3-stock-model-textures-1.1.0.mw3pack`, 2,023,158,585 bytes, SHA-256
`b7b7dab54cd3b0d947a63ae4b3a316d44cdbf34691bbc18b0ac6a141c19d2470`.
The archive has eight members: manifest, environment registry, two banks,
three normal pages and their index. Complete member integrity and closure passed.
The launcher installed this exact archive through its ordinary PackStorage path.

Selection checks confirm stock-only preparation contains exactly the two
original-model banks and zero replacement-model bindings. The separate combined
pack independently provides all 18 models. Pack closure and DEV enabled selection
passed. Full combined environment/model preparation also passed with all 18
replacement models and 38 environment banks. Both stock bank paths in the
prepared session resolve inside this independent installed stock texture pack.

Private inputs, package, byte-comparison evidence, normal rebindings, selection
checks and logs: `local/work-ahead/stock-model-textures-20261024-r1/`.
The existing model pack and native executable were not changed by this work.
Execution boundary: independent packaged stock texture/normal resources.
Acceptance remains 131/144; no new gameplay credit or commit.

Both protected download catalogs now list this separate Textures entry and
the combined pack under Models. Both archives passed complete remote SHA-256
readback on October 24, and all six catalog/metadata/checksum objects were read
back byte-for-byte. Every unrelated download row, including Setup, ISO and
patch, is unchanged. The new archive is under `packs/2026-10-24-models-r1/`.
The old 1.0.0 object is retired only after a hash-verified local recovery copy.
The combined-pack directory's `r2-publication.json` records the retirement state.
