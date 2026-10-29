# MW4 Mercenaries: Windows 10/11 compatibility research

Researched 2026-10-09 against the installed retail build `50.06.09.3002`.
**The strongest next candidate is an existing source-based compatibility
conversion that recognizes all three of our protection inputs exactly.** It
could establish both a playable reference and a readable image for the
recompilation project. This research has not executed a conversion or qualified
any downloaded runtime on this machine.

## Match to the observed failure

Our [launch tests](mw4-launch-test.md) recorded three blocked `Secdrv` starts.
With Disc 1 at `H:`, the launcher showed an administrator-privileges error.
This makes protection startup the first obstacle to resolve; graphics and
mission behavior have not yet been tested.

[Microsoft KB3086255](https://support.microsoft.com/en-us/servicing/os/windows-server/2015/09/ms15-097-description-of-the-security-update-for-the-graphics-component-in-windows-september-8-2015)
documents disabling the `secdrv.sys` service and the resulting older-game
failures. Its service-reenable instructions apply to the older Windows versions
listed in the article, ending at Windows 8.1. They do not establish a Windows 11
remedy. Our actual Windows 11 event identifies a blocked driver, so merely
running the same launcher as administrator is not an established fix.

## Solutions ranked for this installation

| Priority | Candidate | Evidence and applicability |
| --- | --- | --- |
| 1 | **MechWarrior 4 Remastered source-based conversion** | Its pinned release source recognizes our exact retail EXE, ICD and player DLL hashes. It derives compatible executables from supplied original media and includes official-update, graphics, movie and input handling. Strongest candidate for a separate test installation and code-recovery review. |
| 2 | **SafeDiscShim** | Driver-free emulation of communication with SafeDisc's blocked driver. It preserves disc requirements and might allow the original protected build to start. Exact Mercenaries compatibility and authentication with our mounted ISO remain unproven. |
| 3 | **dgVoodoo2** | Wraps old DirectDraw/Direct3D interfaces onto modern Direct3D. Relevant after protection startup succeeds; its documented purpose does not resolve our `Secdrv` failure. |
| 4 | **Windowed mode, movie/input isolation, DirectPlay and compatibility mode** | Useful diagnostics for later black-screen, movie, input or legacy-component failures. Apply one change at a time after establishing executable startup. |
| 5 | **MekTek 3.1 as a separate build** | First-hand Windows 10/11 reports exist. It changes the reference build and content, so it requires separate admission for recompilation comparisons. |

## Exact-build conversion: the useful new lead

[MechWarrior 4 Remastered](https://github.com/Icehellionx/MechWarrior-4-Remastered)
is a community preservation installer using user-supplied media. It applies
official updates and reproducible compatibility transforms, with game-local
graphics/movie/input support. It continues to run the original game engine;
it is a possible execution reference for this project's native recompilation.

The [release-pinned Mercenaries conversion source](https://github.com/Icehellionx/MechWarrior-4-Remastered/blob/v0.6.47.5/src/MW4Remastered.Core/Install/MercenariesExecutableTransform.cs)
declares these inputs for `mercenaries-retail-50.06.09.3002-sd15020-v6`. Fresh
local SHA-256 calculations matched every digest:

| Installed input | Matching SHA-256 |
| --- | --- |
| `MW4Mercs.exe` | `fa317099c1336acabd1c1a3e9736d05533c6e19fb6603fa16e31a87d362bf8cf` |
| `MW4MERCS.ICD` | `37cdc4025c5dc2e8c48f22b2e02a2ef296878e5114453de40bcfaa835f0cc39c` |
| `dplayerx.dll` | `b77a09889b0e8731db4510ff1e44936bcff851fc97d666a89456d57882919110` |

That source declares retail output SHA-256
`a6ad2a76a391fb61e79ae5ed6f263b7ae0adfa204727e0a0fddee35901208739`.
This is an upstream expectation, not a locally reproduced output. It separately
defines PR1 `50.07.01.2105`; applying that update changes the admitted build.

The [current release, presented as 1.0 with immutable tag `v0.6.47.5`](https://github.com/Icehellionx/MechWarrior-4-Remastered/releases/tag/v0.6.47.5),
was published 2026-10-02. The author reports mission tests for all three games,
including saved joystick bindings, in a Windows VM. GPU/default-renderer and
physical-controller coverage remain limited. These are upstream results;
this installation still needs its own menu, mission and save/reload tests.

## Other fixes and their limits

[SafeDiscShim's author](https://github.com/RibShark/SafeDiscShim) describes
intercepting driver requests without installing a kernel driver, while retaining
the original-disc requirement. [Release `v0.9.0`](https://github.com/RibShark/SafeDiscShim/releases/tag/v0.9.0)
(2025-09-29, prerelease) changes DLL initialization and adds a `drvmgt.dll`
workaround. An [open Vengeance 2.0 report](https://github.com/RibShark/SafeDiscShim/issues/48)
still describes a local `drvmgt.dll` conflict. That is another MW4 title, not
proof of failure or success for our Mercenaries revision. A shim test needs
logs and a clear distinction between driver emulation and optical-media
authentication. A mounted ISO alone does not qualify that route.

[dgVoodoo2's official documentation](https://github.com/dege-diosg/dgVoodoo2)
describes DirectDraw and Direct3D 3/5/6/7/8/9 support on D3D11/12. For the
original x86 game, use the x86 runtime DLLs, selected for its actual API, beside
the game executable. Keep graphics options conservative for the first menu and
mission tests. Wrapper use for an original-game reference does not change the
native project's selected Vulkan implementation target.

For later startup problems, [first-hand Windows 11 testing](https://www.reddit.com/r/mechwarrior/comments/1g9unxb/)
reports `-window` helping a nested-exception failure. A [Windows 10 setup
author](https://www.reddit.com/r/OutreachHPG/comments/pyxoib/)
uses `/gosNoVideo` and `/gosNoJoystick` to isolate movie/input startup.
These switches change the tested behavior and should be removed or tested
individually once startup is reliable. DirectPlay's current state remains
unknown because the read-only optional-feature query required elevation.

[Microsoft's MW4 support reply](https://learn.microsoft.com/en-us/answers/questions/4294126/microsoft-mech-warrior-4-mercenaries-to-play-on-wi)
suggests XP SP3 compatibility and renaming a game-local `imagehlp.dll`.
Our file inventory found no such DLL, so the latter advice does not apply to
this installed tree. It also found no game-local dgVoodoo graphics DLLs.

The [Campaign Overhaul author's MekTek-based package](https://www.nexusmods.com/mechwarrior4/mods/3?tab=description)
reports the author's own Windows 10/NVIDIA success and others' Windows 11
results, with explicit support limitations. It changes campaign missions,
balance and audiovisual content. A clean MekTek build may be a useful separate
playability option; an overhaul would add unnecessary differences to the
initial retail recompilation reference.

[SafeDiscLoader2](https://github.com/nckstwrt/SafeDiscLoader2) targets SafeDisc
2.0–4.9. Our exact-match conversion identifies SafeDisc 1.50.20, so the generic
instruction to drop its `version.dll` beside an EXE is not an established
solution for this build.

## Proposed next validation

1. Review the pinned exact-build conversion and reproduce it in a separate
   local output directory. Bind the three original hashes, source revision,
   declared output and actual output to a receipt. Preserve the original retail
   inputs as the comparison baseline.
2. Validate the derived PE's sections, imports, entry and modified regions;
   import it into Ghidra and check that actual gameplay functions are readable.
   Record protection/title checks changed by the conversion.
3. Establish a menu, pilot creation, one offline mission, save/reload and orderly
   exit, then repeat. Apply graphics/movie/input changes against observed
   failures, retaining the launch configuration used for each result.
4. Admit PR1 separately if selected. Keep MekTek separate if it becomes a
   fallback. A launch fix earns no native-recompilation credit by itself.

The [MW4P-0 gate](mw4-execution-plan.md) remains open until these local proofs
exist. Retained research receipts are in ignored
[`reports/mw4-compatibility-research-2026-10-09/`](../../reports/mw4-compatibility-research-2026-10-09/):
`exact-input-match.json` and `local-applicability.json`.
