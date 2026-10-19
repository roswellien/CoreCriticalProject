# MW3 storage relocation — 2026-10-18

User authorization: relocate older work-ahead revisions and all reports to the
Games drive, retaining current texture revisions locally. Migration completed
at 22:31 on October 18. D: has 1,314.39 GiB free (about 1.28 TiB).

Destination: `G:/MW34Recomp-Archive/storage-relocation-20261018/`.
The existing archive on Games is retained, including earlier cinematic archives.
No existing destination folder is overwritten or merged during relocation.

The plan retains 35 current texture/model source directories on D:, selected
from current profiles, model registries, configured bank maps and latest
standalone texture-family releases. Other revision directories are archived.
Loose work-ahead tools/manifests remain local. Thirty-one legacy ZIP/checksum
package files are separately moved to `work-ahead/loose-packages/` and verified
with SHA-256; the current training-mech package remains local. The exact retained list
and reasons are in the migration plan on C: and its archive copy.

Each archived directory receives a junction at its original D: location.
The complete `reports` root points to G:, so future report output also goes
to Games. Do not replace these links with new local copies. New current texture
work may continue in fresh directories under the physical D: work-ahead root.

Migration checks include before/after source metadata fingerprints, destination
file/directory inventory comparison, reparse-target readback and SHA-256 checks
of large files and report databases. Originals are removed only after successful
verification and junction readback. Recursive cleanup does not follow reparse
points. Partial destinations and errors stop the move and preserve originals.

Windows Restart Manager reported no open file owners for 20 report database paths
before copying; no SQLite database was opened through a database connection.
Protected Python processes 5196 and 6536 are untouched. A source modified during
copy fails its inventory comparison rather than being silently removed.

Local migration plan, copy logs, per-directory verification pins and completion
events: `C:/Users/jcbla/MW34SunTests/storage-migration-20261018/`.
The script is a local, user-authorized storage maintenance action, not a new
acceptance verifier. Rendering behavior and acceptance 131/144 are unchanged.

## Completion checks

All 130 directory moves are complete: 129 older asset/work-ahead directories
and the reports root. All original directory paths resolve through verified
junctions to Games; no temporary relocation backups remain. The 35 retained
source directories remain physical directories on D:. All 31 loose legacy
packages/checksums were verified again at their archive destinations.

The report copy contains 8,691,789 files and 595,978,302,409 bytes. Source and
destination metadata inventories match; selected large files and all 20 report
database paths also passed SHA-256 comparisons. Restart Manager found no owners
for those database paths before removal. Verification resumed under PowerShell 7
after the older runtime encountered a long archive path; that failure retained
the originals until successful verification. Cleanup did not follow junctions.

The acceptance-131 receipt remains byte-identical through its original path:
`aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061`.
Material Normal Preview's launch check passes with 39 banks and all 15 registered
models. No executable, profile, normal strength or acceptance criterion changed
as part of the relocation.

The complete migration receipts are also archived at
`G:/MW34Recomp-Archive/storage-relocation-20261018/migration-receipts/`, including
`completion.json`, the exact keep/move plan, copy summaries and content pins.
The storage boundary advanced is report/asset placement; it grants no new game
execution credit. Campaign 1 normal-map work follows this maintenance action.
