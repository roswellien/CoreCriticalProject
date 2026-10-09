# Supported executable identities

**One exact MechWarrior 3 research input is verified:** the U.S. retail
installation updated to version 1.2 on 2026-10-06. Its `Mech3.exe` is 2,384,384
bytes, with SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
The executable's file and product version resources are `1, 2, 22, 0`, and the
installed registry version is `1.2`. See [installation provenance](media-inventory.md).
This establishes input identity, not a working recompiled game or tested gameplay.

Possession of an installer, ISO, patch installer, filename or version label alone
does not identify an installed game executable. Other byte variants, including
the preserved unpatched baseline, are not admitted by the current manifest.

The authoritative manifest is
[`games/mw3/config/supported-binaries.json`](../games/mw3/config/supported-binaries.json).
Never insert a fabricated digest or treat a patch installer hash as a game binary
hash. A support record identifies bytes for research; execution compatibility
requires separate evidence and tests.

## Schema version 1

The root object has exactly these keys:

| Key | Meaning |
| --- | --- |
| `schema_version` | Integer `1` |
| `game` | String `mw3` |
| `binaries` | Array of verified binary records; empty until verification |

Each binary record requires:

| Key | Meaning |
| --- | --- |
| `id` | Unique lowercase letters/digits/hyphens profile identifier |
| `title` | Human-readable release/region/patch identity backed by evidence |
| `filename` | Original basename; documentation only, never used as identity |
| `sha256` | Full 64-character lowercase SHA-256 digest of the entire file |
| `size_bytes` | Exact positive integer length, at most 536870912 bytes |
| `pe.machine` | Integer `332` (`IMAGE_FILE_MACHINE_I386`, hexadecimal `0x14c`) |
| `pe.optional_magic` | Integer `267` (`PE32`, hexadecimal `0x10b`) |
| `pe.image_base` | Unsigned 32-bit integer preferred image base |
| `pe.entry_point_rva` | Unsigned 32-bit integer entry point relative to image base |

Optional `provenance` is a non-empty string documenting how the installed image
and its version were established. Optional `notes` is an array of strings.
No other fields are allowed. IDs and hashes must be unique. Duplicate JSON keys,
partial hashes, booleans standing in for integers and unsupported schemas fail.
JSON numeric addresses are decimal; documentation may also show hexadecimal.

An intentionally non-executable format example, without fake hashes:

```text
record.id = evidence-backed profile name
record.title = verified release, region and patch
record.filename = observed installed executable basename
record.sha256 = SHA-256 calculated from that entire local file
record.size_bytes = observed file size
record.pe = machine, optional_magic, image_base, entry_point_rva from PE analysis
record.provenance = installation and version evidence, without personal paths
```

## Establishing the first record

1. Use a legally obtained installation. Identify the **installed game executable**
   and document the media, language, release and applied patch from evidence.
2. Run `python tools/analysis/analyze.py <executable> --output reports/mw3.json`.
   The result is explicitly unknown until reviewed and entered in the manifest.
3. Independently calculate SHA-256 (for example, PowerShell `Get-FileHash -Algorithm
   SHA256`) and compare size and the reported PE identity.
4. Review which version claims are supported. Add the exact identity record and
   provenance, with no proprietary bytes or arbitrary extracted strings.
5. Run `python tools/binary-validator/validate.py <executable>` and preserve the
   command/result as private local verification evidence. Add a concise metadata
   finding to `games/mw3/docs/` with uncertainty marked.

Validation always compares full hash, size and PE identity. Filename, timestamps,
patch labels and image base alone are insufficient. Unknown hashes fail closed.
The analyzer can inspect unknown binaries, but this never changes the manifest or
grants them supported status. A changed executable requires a distinct reviewed
record; modifications, unpacking or patching must never silently inherit a hash.

Manifests are trusted project configuration, not a signature or supply-chain
security boundary. The loader validates their structure, while review establishes
provenance. Do not commit proprietary executables or generated full disassembly to
make validation reproducible; use metadata and project-authored test fixtures.
