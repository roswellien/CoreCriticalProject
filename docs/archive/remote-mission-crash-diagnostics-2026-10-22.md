# Remote c1m1 crash — diagnostic launcher 1.0.23

**Successor:** the new remote 1.0.23 report exposes the texture-read call chain.
The [1.0.24 full installer](large-texture-archive-repair-2026-10-22.md) repairs a
confirmed enhanced-archive offset defect; remote c1m1 retesting remains required.
The diagnostic-release history below is retained.

**Update withdrawal:** at the owner's request, the 1.0.23 `.ccupdate` and companion
ZIP were removed from both Setup lists and R2 because the metadata file was not
downloadable on the test machine. Use the full `corecriticalinstaller.exe` for
1.0.23, including upgrades. Download notes and checksums now describe only that
installer. Local update build/test evidence below is retained; these two update
files are no longer published. This does not cancel future launcher update packs.

Two supplied reports from launcher 1.0.22 reach the enhanced menu and open c1m1,
then stop with a guest write to address zero at memcpy entry 0x7800160e. Both
report AMD Radeon 760M graphics and no submitted geometry. The owner confirms
the failure happens while loading Operation 1 Mission 1 on the other machine,
and explicitly directs that detailed diagnostics must run on that machine.
This remains unresolved; do not claim a local menu test fixes mission loading.

Launcher 1.0.23 enables the shipped native host's existing `MW34_SEH_LOG=1`
switch in every launch profile. On a guest memory fault, native stderr now
records general registers, stack pointers, call depth and the guest return
chain. The switch logs only on failure. The signed native host/module are
unchanged. Both prepared-pack composition stages retain the switch, and the
existing report ZIP includes these stderr lines without exporting memory dumps,
profiles, saves or original files. Formal acceptance remains 131/144.

The owner should import the 1.0.23 .ccupdate with its matching ZIP, retry c1m1,
and export a new report from the affected machine. Capture the caller and
allocation/resource path from that report before choosing a native fix.

The full launcher suite passes, including launch-profile diagnostics and
register/return-chain preservation in exported reports. A real installed
1.0.22 verifies and stages the signed update. The exact staged installer
upgrades it to 1.0.23.0 while preserving native host/module bytes and the
precompiled installation marker. The helper restart itself was not exercised
in that isolated check. The trial was uninstalled.

The full installer is now published as `corecriticalinstaller.exe` (renamed
from `CoreCriticalLauncherSetup.exe` at the owner's request), alongside
`corecritical-1.0.23.ccupdate` and its matching ZIP. All three are published in
the existing protected R2 bucket under `installers/2026-10-22-r8/`; both Setup
pages label this as crash diagnostics, with c1m1 still under investigation.
Full remote payload and sidecar hashes match, and the full installer retains a
valid timestamped Windows signature. Asset/ISO/patch links and Access policies
are preserved. Private evidence: D:/MW3MissionLaunchRepair-20261022-r1.

The interrupted local asset-preparation attempt and bounded navigation trials
are retained as evidence, and are not successful c1m1 reproduction or repair.
