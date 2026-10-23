# Clean-install renderer setup repair — 1.0.22-preview

The supplied 1.0.20 playtest report stops before drawing frames with the original
game's Video Error: the Software Render Files component was not installed.
The launcher's new per-player registry started empty. Unlike a retail installer,
copying verified game data did not record the installed renderer component.
The development machine's original Windows registry could supply the missing
values, masking the clean-machine defect during earlier launch checks.

Retail 1.2 reads HKLM InstallOptions at VA 0x59803d into 0x731954;
0x597d80 masks the requested option bits. Startup's HWCardFlag setup calls that
mask with 0xff at 0x40c47e. Missing installation options disable the hardware
path and reach the reported software-renderer error. The admitted media manifest
identifies Hardware_Texture_8 as six regional rtexture.zbd banks.

Installed native launches now hash-check those six original hardware banks,
including applicable patch overrides, before recording the component selection
in the per-player registry overlay: InstallOptions=4, HWCardFlag=1, HWCardDev=0.
The native backend exposes one Vulkan-backed hardware device. This setup runs on
existing failed installs too. It changes only the three renderer setup values;
controls and other player configuration remain intact. Writes are atomic and
retain the existing settings backup. No machine registry, captured configuration,
guest memory patch, original-code fallback or native rebuild is used.

The execution boundary advanced is installed-game renderer initialization.
The native host/module remain playtest-20261022-r5. Formal acceptance is unchanged
at 131/144.

## Validation

An isolated overlay with explicit missing-value markers prevents fallback to
the development machine's three original-installer values. Before repair it
reproduces the exact Software Render Files error at site 0x001df12a, with zero
frames. After applying the production setup method to that same configuration,
the unchanged native runtime presents 300 Vulkan frames. This diagnostic run
ends at its explicit frame budget; it is not a normal-quit or Training test.
The reporting machine's AMD Radeon 760M still needs the owner's retest.

The complete launcher suite passes, including fresh renderer initialization,
repair of zero-valued settings, player-state preservation, idempotence, and
refusal to advertise missing hardware files. The signed 1.0.22 installer passes
an isolated install in 6.05 seconds locally, byte comparison, installed runtime
validation and timestamped uninstaller verification. The trial was uninstalled.
Private evidence is under D:/MW3CleanLaunchRepair-20261022-r1.

## Delivery

For subsequent builds, the owner selected `corecriticalinstaller.exe` as
the installer filename for every package variant. The build and signing scripts
use that name. The 1.0.22 artifact linked below retains its published filename.

The owner explicitly cleared publication of 1.0.22 for retesting after the
temporary website hold. Both existing Setup lists now link the corrected build.
The full remote payload matches the local size/hash and has a valid timestamped
Windows signature. Remote catalogs and sidecars match intended bytes; all prior
asset, ISO and patch links remain. Access policies and update feeds are unchanged.

Setup size: 92,297,192 bytes. SHA-256:
`f55eb35759616aaccbbef4a70adebe7742f832a8fe431d05344b963f14278d7c`.

[Download 1.0.22-preview](https://playtest.corecritical.dev/installers/2026-10-22-r7/MW3Remaster-Playtest-Preview-Setup.exe).

Install over the existing launcher and reuse its original game folder and packs.
The repair is applied on the next launch. Asset-installation progress from 1.0.21
is included, and precompiled delivery still avoids first-install code generation.
