# C1M1 fresh-install versus dev texture selection

## Finding

The remote surface-arena crash is reproducible on the development PC. The
deciding difference is the original game's saved `TextureMemory_HW` value,
not a different arena limit on the other PC. The old working dev test/player
profile has DWORD 6; fresh installed player state does not supply that value.
The native original game consequently selects different upgraded archive
variants from the same enabled Operation 1 pack.

| Private original setting | Selected bank | Requested surface pixels | Outcome |
| --- | --- | --- | --- |
| Value absent, original default | `c1-rtexture.zbd` | 2,052.79 MiB through the failed request | Arena fault at `0xef93c000`, before any 3D draws |
| DWORD 6, matching working dev state | `c1-rtexture2.zbd` | 599.71 MiB | C1M1 renders; bounded 1,500-frame stop |

These are nominal original retail 8 MB and 2 MB texture-bank families, whose
replacement pixels are much larger than the original retail data. This does
not mean the replacement banks contain only 8 MB or 2 MB. The large bank has
about 1,133.8 MiB of 16-bit color pixels; its smaller variant about 308.4 MiB.
The original texture creation route requests both system-memory and texture
surfaces (`00001800` and `04001000` caps). The final failed request is the second
16 MiB surface for a 4096x2048 image. Only 2,850,816 bytes of retired surface
pages are collectable in the local reproduction, insufficient for that request.
This load is not explained by physical RAM alone or by reclaiming a large pool
of already released surfaces.

## Isolation and evidence

The public r5 native executable is
`b40764e2b5f2a44f34daff77dabfaebc6930f1723d0847917a8192695baced92`.
It successfully loads C1M1 on the dev PC with the saved configuration. All six
developer C1 bank files were freshly SHA-256 checked against the installed
Operation 1 pack's pins; they match. Source comparison shows the same arena
limits in r5 and the later dev r6 host. The successful path does not depend on
the newer dev host.

A private host derived from frozen r5 source records surface requests, actual
registry-query results, opened bank paths and actual DirectDraw memory-query
results. It changes no allocation, API return, texture contents or guest state.
Two runs use that identical host, original module, PC, game files, input route,
1920x1080 output, 800-unit scenery setting and banks. Their private registry
files differ only in `texturememory_hw`: the explicit overlay deletion marker
models an absent value and prevents the dev machine's real registry filling it
in. The ordinary translated game then chooses its default itself. The other run
supplies the existing saved value 6. Both report installed component flags 4,
the same value supplied by the launcher on clean installs.

Changing only the component flags from the dev original installer flags to 4
while retaining texture-memory 6 also succeeds. Component flags therefore do
not explain this particular failure. The private fresh-default run duplicates
the remote error site `0x380028f0`, failing arena cursor `0xef93c000` and absence
of 3D submission. Low remote available RAM remains relevant to performance and
other allocation failures, but is not needed to reproduce this arena failure.

A final repeat with the exact published r5 executable, without instrumentation,
also fails at `0xef93c000` under the fresh-default setting. It starts with
8,512 MiB of physical RAM available on the dev machine. The saved-setting
control with that same published executable renders C1M1 successfully. Thus the
diagnostic logging is not responsible for the reproduced failure.

Private source, scripts, logs, bank pins and controlled results are under
`local/work-ahead/c1m1-surface-investigation-20261023-r1`. All runs use isolated
game/player copies and ordinary original menu input. They do not alter the
working dev profile, user saves, installed packs or public downloads. Replays
and injected game-state seeding are not used. The first unshifted input attempt
stayed in menus and is retained as a failed route, not a successful C1M1 test.

Execution boundary established: fresh player configuration -> original archive
selection -> paired surface requests -> exact remote arena failure, with a
single-setting successful control. Formal acceptance remains 131/144. This is
an investigation, not a deployed repair or complete mission/gameplay validation.

## Consequence

The dev build was already selecting a smaller variant despite having the same
Operation 1 pack enabled. Fresh and dev installs need explicit, consistent
texture-selection behavior. Full-size variant support separately needs surface
allocation work; increasing the PC's RAM does not remove the guest arena limit.
No silent quality change or live configuration modification was made here.
