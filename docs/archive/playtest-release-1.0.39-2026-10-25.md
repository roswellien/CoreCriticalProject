# Core Critical 1.0.39 — Steam shortcut repair

Launcher **1.0.39-preview** fixes Add to Steam. Native runtime remains **1.0.37**;
the full installer includes that unchanged runtime. Use Settings & Steam →
Updates to download the launcher release. Exit Steam using Steam → Exit before
adding a shortcut, then reopen Steam to see it in the Library.

- [Full installer](https://playtest.corecritical.dev/installers/2026-10-25-r4/corecriticalinstaller-1.0.39-preview.exe)
- [Local update import bundle](https://playtest.corecritical.dev/updates/corecritical-1.0.39/1.0.39-cc-update.zip)

The previous writer appended every shortcut with index 0, detected existing
entries through unstructured text, could retain obsolete executable targets,
and suppressed failures. It also wrote while Steam could overwrite its changes.
The replacement parses bounded binary KeyValues, assigns unique indexes,
updates owned stale entries and preserves valid separate installations, other
games, stable shortcut IDs, custom launch options and artwork. It selects the
active/recent Steam profile rather than writing every userdata directory.

Changes use an exclusive lock, atomic replacement, an exact original backup and
readback verification. Malformed input and ambiguous profiles fail visibly.
The UI targets Core Critical Launcher.exe. Silent installer integration returns
failure honestly, and setup explains how to retry without failing installation.

## Verification

The complete C# fixture suite passed. Steam-specific fixtures cover insertion,
idempotence, stale targets, duplicate indexes/entries, unrelated shortcut bytes,
stable IDs/options, malformed input, profile selection, backups and artwork.
An actual signed 1.0.38 → 1.0.39 installer upgrade preserved every runtime file
and a user fixture; installed launcher/configuration bytes matched the release.
Its temporary application and uninstall registration were cleaned/restored.
The existing launcher helper/restart implementation was unchanged and was not
retested for this release; its preceding release evidence remains intact.

The local DEV shortcut was added while Steam was closed, preserving the existing
separate legacy launcher entry. The new Core Critical entry and artwork were
confirmed in the real Steam Library. A subsequent attempt with Steam running
failed without modifying the shortcut file. Launching a game through Steam was
not tested. The open DEV launcher was not replaced or interrupted.

Release evidence is retained locally at
`D:/CoreCriticalSteamRepair-20261025-r1/`. Publication uses the existing signed
public update-only feed; historical routes remain allowed. The private site's
Setup installer and launcher bundle are replaced by this version while runtime,
asset packs and original-media rows remain intact. Native acceptance remains
**131/144**. No native rebuild, commit or push is part of this release.
