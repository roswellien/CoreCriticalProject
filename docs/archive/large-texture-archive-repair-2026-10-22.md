# Large replacement texture archive repair

The remote 1.0.23 report `MW3-Playtest-20261022-204708.zip` captures the
Operation 1 Mission 1 failure before geometry submission. Replay is disabled.
The failing copy receives a null destination through the texture loader's
palette allocation/read at return `0x00517ea7`. The report does not identify
the exact texture record or allocation size. This is remote evidence; no local
gameplay reproduction is claimed.

## Confirmed archive defect

The installed shared-mechs 1.0.0 pack declares a 3,126,526,488-byte
`rmechtex.zbd`, SHA-256
`582efdb88fa98a98ee8e6d8199f8cd6ba054ff5338cd4c07e413fe824d090ba9`.
Of its 3,360 records, 1,080 begin above `0x7fffffff`; the first is
`puma_d04_c` at 2,148,402,840. Descriptors in this pack have zero palette
counts. The report's palette-read path is therefore consistent with a bad
header read, although it does not by itself establish this exact cause.

Static analysis of admitted MW3 1.2 executable SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`
shows the named texture loader passing its unsigned record offset through
signed-long `fseek` at `0x00518e02`, return `0x00518e08`, then ignoring failure.
The supplied CRT's `_lseek` calls `SetFilePointer` without a high word at
`0x7801210f`, return `0x78012115`. A high-bit offset is consequently treated
as a negative absolute seek. The following texture read proceeds at the wrong
position. An independent read-only review confirmed this chain and the CRT's
success comparison against exactly `0xffffffff`.

## Native repair and scope

`apply_large_texture_seek.py` applies a small adapter to a new host source
snapshot. It tags successful read-only opens of explicitly mapped replacement
banks and removes tags on close. Only the two recovered call-chain sites,
absolute origin, absent high-word pointer and high-bit offset admit widening.
The actual Win32 seek supplies high word zero. CRT locking, buffer flush/reset,
allocation and reads remain in their existing translated paths. Failures retain
the actual operating-system result. Up to eight adapted seeks are logged, plus
any adapted seek errors, for the next remote report.

This does not provide general large-file `ftell`, relative seek support or
coverage of other unproven archive callers. It changes no texture pixels,
resolution, lighting or gameplay. The execution boundary advanced is reading
enhanced texture records beyond the original signed offset limit. Formal
acceptance remains 131/144.

Maintained patch/helper/test live under `tools/remaster-launcher/`. Frozen
development source and its selected launcher profile remain unchanged. The
private derived host and build evidence are under
`D:/MW3LargeTextureRepair-20261022-r1`; the translated native module is reused
unchanged. Signed successor host SHA-256:
`879408f40d492459b7168f5bab6ba7f3cf89f19d1f12feac3bc0cf21154150a4`.
Reviewed pack admissions include that exact successor, retaining pack formats,
catalog readers, shaders and resources.

## Validation

- 34 authored fixture checks pass, including real sparse-file seek/read beyond
  2 GiB, the old negative-seek failure, and exclusion of unrelated call chains,
  original files, explicit high words and relative/end seeks.
- Five environment-pack and seven prepared-mech-pack tests pass.
- Derived host compilation and split-host link succeed. Native generated module
  is unchanged; no translation regeneration or original execution fallback.
- Complete launcher runtime validation passes with the signed host and refreshed
  resource pins.
- Exact signed full installer upgrades an isolated 1.0.23 install to 1.0.24 and
  installs the new native host; the installed runtime validates successfully.
- Exact signed full installer also passes a fresh installation and complete
  runtime validation, retaining the precompiled delivery marker. Both isolated
  trials are uninstalled after checking; no original game launch is claimed.

## Published full installer

[Core Critical 1.0.24](https://playtest.corecritical.dev/installers/2026-10-22-r9/corecriticalinstaller.exe)
is listed in both protected Setup catalogs. It is 92,328,840 bytes, SHA-256
`4024cf09a0c422f320444f497d4ef834db7d58bf729947d06c66cf2fcc98e812`.
A complete R2 readback matches the local installer and has a valid Windows
signature. This replaces native code, so use the full installer in the existing
launcher folder. No launcher-only update is published for this repair. The
withdrawn 1.0.23 `.ccupdate` and ZIP remain withdrawn.

The exact remote mission must still be retested. The confirmed defect is fixed;
the report alone cannot prove that it was the only cause of the c1m1 crash.
