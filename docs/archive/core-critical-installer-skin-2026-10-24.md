# Core Critical installer branding

The actual Inno Setup wizard now follows the existing launcher's charcoal and
amber identity. This is a packaging/UI change to the private 1.0.30 preview;
launcher and game binaries remain those of the stock-presentation build.

`tools/mw3-remaster-launcher/installer.iss` uses Inno Setup 7's native modern
dark theme, including the title bar, a branded welcome/finish illustration,
the Core Critical mark on interior pages, and the application icon for setup
and uninstall. Welcome and finish text describe original-file verification,
graphics setup, stock content and optional packs. The launcher-only variant
has separate text appropriate for an update.

Artwork in `Assets/Installer` is derived from the existing launcher
`Assets/Plates/hero-art.png` and `brand-mark.png`, using the existing Orbitron
and Barlow fonts. The welcome panel is 492 x 942 and the small mark 192 x 192.
These PNGs are compiled into setup; their files are excluded from the installed
application asset tree. No third-party skin DLL is required.

The AppId, per-user install location, destination/shortcut/Steam choices,
precompiled runtime delivery, signing, silent installation and first-run
`--setup-game` launch remain intact. Display preferences continue in the
launcher's first-run setup, using the same controls as its Display tab.

## Evidence

Private artifact:
`D:/CoreCriticalInstallerSkin-20261024-r1/Installer/corecriticalinstaller-1.0.30-preview.exe`

- SHA256: `0168cc1e2ca51f85827c2c84cef4863811ed2668262083fa2736fd6c8f614586`.
- Build completed with signed setup/uninstaller; signature verification passed.
- Actual wizard visually inspected through Welcome, Destination, Start Menu,
  Additional Tasks and Ready. Preview cancelled before installation.
- A fresh isolated silent install passed: signed launcher EXE/DLL matched the
  publication and all 660 runtime files matched their manifest. No native
  generation trigger was installed. Test uninstall registration was restored.
- Initial test incorrectly rejected an empty excluded-art directory; inspection
  confirmed it contained no files. The corrected file-content check passed.
- `install-check.json`, `install-trial.log`, build/signature receipts and the
  private test script are retained under the artifact root. This was tested on
  the development PC, not a separate clean Windows machine. Install-progress
  and finish pages were not separately inspected visually.

This advances installer presentation only. Formal native acceptance remains
131/144. The build was initially local only; the owner subsequently authorized
[publication to the protected playtest site](playtest-release-1.0.30-2026-10-24.md).
Existing update packages were not regenerated for this cosmetic change. No Git
commit was made.
