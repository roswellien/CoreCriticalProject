# Operation and Training environment packs

The subsequent [mission-lighting integration](environment-pack-mission-lighting-2026-10-21.md)
adds pack-owned day/night, atmosphere and weather settings and rebuilds all five
collections as 1.1.0. The native runtime still implements dynamic lighting; the
packs now carry its per-mission presentation data too.

Local packaging work authorized on 2026-10-21. Five collections: Training,
Operation 1, Operation 2, Operation 3 and Operation 4. Operation 4 owns both C4
and C4b. The three global/mech banks are excluded; they belong to the separate
mech texture work. Original media and derived packs stay local. No upload or
public distribution is authorized by this work.

## Content and launcher contract

Schema 2, `native_payload.profile = prepared-environment-v1`, registry
`environment/environment.json`, `path_base = pack-root`. The exhaustive file
table declares each resource's size, SHA-256 and binary format. Archives carry
prepared ZBD colour banks, authored and automatic world normal pages, matching
surface detail and the selected effect-light catalog. They contain no native
executable, game code, artwork projects, scripts or absolute development paths.

Each pack requires the exact native host identity recorded in its manifest.
The matching host contains the reviewed fixture definitions and the UV-stable
placement, retention and shadow implementation. Lighting is not an executable
plugin inside a texture archive. A subsequent host requires a reviewed admission
or new pack revision; compatibility is not inferred from a newer version number.

The C# importer retains its staging, bounded extraction, checksums, rollback and
path checks. Its expanded-byte cap is now 16 GiB because C4 plus C4b alone exceeds
8 GiB before compression. Schema-2 dispatch distinguishes environment registries
from prepared mech registries. Unknown profiles fail visibly.

`GameRunner` sends enabled environment roots separately from mech roots. The
Python coordinator verifies installed resources and chooses a whole region from
the first enabled pack in priority order. It composes private bank indices and
normal catalogs per launch; installed packs remain read-only. Shared resources
must agree, conflicting normal images fail, and identical images are deduplicated.
Native page limits are enforced: at most 16 authored pages / 256 world pages,
bounded image/file sizes and a 512 MiB total per catalog. Relative manifest entries
are filenames, as required by the native readers.

An empty enabled environment list removes development texture/normal bindings
and reads the selected user's original archives. It does not emit a zero-entry
MWBANK index, which the native reader rejects. Model preparation bypasses the
development configured-bank manifest in the installed environment path. Final
PowerShell profiles retain the composed installed resources, preventing older
development paths from replacing them.

## Repairs included before freezing

The C3 DUST01 terrain treatment was incorrect. Six entries are restored from
the pre-C3 selected colour banks. Header, dimensions, alpha and unrelated entry
bytes are preserved. Explicit flat normal exclusions cover restored and erroneous
colour identities, so automatic relief cannot reappear on flying dust.

C4/C4b now has 91 additional exact-content lamp/glow/hot-surface registrations.
Masks isolate reviewed UV islands; red status indicators are glow-only, including
mixed white/red panels. AIRP19 white streaks are reflections, not lamps. Six
remaining stale legacy definitions are removed; other flagged shared stale keys
were already removed by the Training correction. Source-owned lightning, thruster
and rocket sprites are preserved without duplicate persistent fixture lights.
The six normal/material flags are resolved without inventing shared-world usage.

The source snapshot and selected profile pin the rebuilt host. Existing 64-light
limit, range/retention, shadows, graphics settings and C2M4 ambient 0.40 remain.
Private evidence/backups: `local/work-ahead/environment-packs-20261021-r1/`.
The compact authored catalog has 560 keys in seven pages, 201,839,620 bytes;
deduplication preserves image pixels and all prior exclusions.

## Build and validation

Builder: `tools/remaster-launcher/build_environment_packs.py`. Final local output:
`local/asset-packs/environments-20261021-r1/`. A completed `packs.json` with
`verified: true` is the publication marker; prepared directories or `.partial`
archives are not completed packs. Private source provenance remains beside the
archives. Every archive member is independently read back and hashed, and selected
inputs are rechecked before publishing the completion marker.

Native compilation, C# importer checks and Python operation-selection checks have
passed. Actual archive installation/relocation checks are recorded with the
completed output. No game launch belongs to this texture-pack work. Archive
integrity does not certify whole-campaign appearance or performance. The execution
boundary advanced is optional presentation content to launcher-installed resource
selection. Native gameplay acceptance remains 131/144; no commit.

Completed archive check: all five archives imported using the C# installer to D:/MW3 Environment Pack Trial 20261021-r1. The mods folder was renamed to relocated mods. Each collection alone, all 36 banks together and disabling all collections passed. Ordinary coordinator --prepare-only with the two installed mech collections returned zero, and its final PowerShell profile uses relocated banks and composed normal pages. See local/work-ahead/environment-packs-20261021-r1/installation.json. No game launched.
