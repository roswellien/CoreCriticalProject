# Signed media extractor admission repair

The 1.0.27 installer could reject its own shipped extractor with “Unsupported
media extraction tool. Repair the launcher installation.” This happens before
disc cabinet validation and does not establish that the supplied ISO is wrong.

The release signs `unshield.exe`, changing its checksum, security-directory
entry and appended certificate records. Setup admitted the unsigned executable
and one historical signed hash. The freshly signed 1.0.27 extractor instead
hashes to `2671f8be4dac3fd17093bc32bf58dd2ef4f0ea7ce3b02bf20b75582ae5919bda`.
Its unsigned executable prefix remains byte-identical after restoring those
two original zero-valued metadata fields. The canonical 284,672-byte image
retains the existing pinned SHA-256
`134d597a3d5d764188acfa57815d96c88c5ce4a8cb135a548fa78917a9fc2cc2`.

`PinnedPeImage` validates the exact unsigned code/data/header bytes and allows
only checksum/security-directory changes plus bounded, aligned appended
WIN_CERTIFICATE records. It rejects changed executable bytes, truncation,
overlapping or malformed certificate records, and extra appended data. This
checks executable identity, not certificate trust; release signing still
verifies timestamped Windows signatures separately. There is no executable-hash
admission exception per new signing timestamp. Legacy development extractor and
its pinned zlib checks remain available.

The installer builder now invokes the actual launcher extractor-admission check
after signing and before Inno compilation. Authored fixtures cover certificate
attachment and malformed/tampered inputs. Error text identifies the launcher
tool rather than suggesting the ISO is unsupported.

The full ISO integration test exposed another actual setup defect: the mounted
image reports its CD-ROM device, but its Windows Get-Volume association can be
absent. Setup now resolves the same device through exact QueryDosDevice mappings
to one CD-ROM drive. It never chooses an unrelated optical drive or bypasses
original-media verification.

Private evidence: `D:/CoreCriticalMediaRepair-20261023-r1`. The existing user ISO
matches `08c26c0d71375d6130df7716abc2c282147494d869bd48ce13bd5f972f763e49`;
the supplied English 1.2 patch matches the existing manifest. Installation from
that ISO and patch through the corrected production setup path, using the exact
signed 1.0.27 shipped extractor, successfully verifies and publishes a fresh
original-data directory. The full launcher fixture suite also passes.

The repair is released as Core Critical 1.0.28. It retains the latest published
r5 native runtime byte-for-byte (host SHA-256
`b40764e2b5f2a44f34daff77dabfaebc6930f1723d0847917a8192695baced92`).
No native recompile or Op1M1 crash repair is claimed. Execution boundary advanced:
signed installer -> admitted extraction tool -> verified original-data setup.
Formal native acceptance remains 131/144. No commit was requested.

## Final installed release verification

The signed final 1.0.28 installer was installed into a separate directory. A
test harness loaded the exact installed, signed launcher DLL and used its exact
installed, signed extractor. Both an already mounted user ISO and a private
local copy initially unmounted completed the production ISO-and-patch setup
path. All admitted original files verified; the owned test mount was removed.
The signed extractor's hash is
`b9a76daff3f396272fc0b9016a5ca1a51518bdd7b1f63d0841d3f9f7ebd60e07`;
its canonical unsigned identity is unchanged. No original media was downloaded
or included in the installer.

[Corrected installer](https://playtest.corecritical.dev/installers/2026-10-23-r4/corecriticalinstaller-1.0.28-preview.exe)
is 92,621,896 bytes, SHA-256
`303cfec276978cc56f609c25848f2c2942e5b56233f48c8c2126329527a6801e`.
Full remote readback matches and its Windows signature validates. Both live
catalogs match the intended page bytes, retain the restored ISO/patch links and
all asset-pack rows, and replace 1.0.27 with 1.0.28. The obsolete 1.0.27 installer
object was deleted after verifying its private retained backup. The r5 update
row notes that its native runtime is already included in 1.0.28.
