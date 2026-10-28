# Installed enemy mech and skin binding handoff

The user reports the Training instructor's Bushwacker and a Thor in Operation 2
Mission 4 reverting to the original geometry and textures despite installed packs.
No new game session was started or stopped for this diagnosis.

## Observed evidence

Latest retained native session: 00f04fb273344adc8110e72eea387c20, launcher 1.0.18,
performance-monitor native host. Both mech collections and the shared mech texture
pack were enabled. The host loaded all 36 base close/distance resources, but only
two alternate texture bindings: the historical Bushwacker-D close/distance pair.
Its prepared profile and run.json both contain only those two skin bindings.

The log recognizes an enemy Thor's skin F but records replacement_available=false.
Its rejected full mesh signature exactly matches the admitted close Thor roster.
It also records unavailable alternate skins for other recognized chassis. Thus
that Thor's rejection is not explained by an absent base model or an unknown
chassis signature. The renderer intentionally retains stock rendering when an
optional skin set is incomplete; that safeguard remains unchanged.

The installed pack copies visible to the diagnostic process contain B-H skin
sets at both LODs for all 18 chassis. Current composition and asset preparation
produce 252 alternate bindings. Windows resolves their manifest paths into the
Codex LocalCache backing directory; historical session paths use logical AppData
names. The exact origin of the historical two-binding environment is not proven
by this inspection. In particular, do not claim that a clean current cache run
has independently reproduced that historical cache identity or that the Training
instructor's live appearance was checked.

## Fix and execution boundary

The launch handoff previously assigned the entire environment-preparation result
to the final profile, then overlaid it on the process environment. That result
includes inherited host/model settings as well as prepared world resources. It
could replace newly selected mech paths with an older or incomplete returned set.
The final PowerShell stage then reapplied that incomplete profile over preparation.

play_remaster.py now takes every model, LOD, normal and alternate-skin binding from
the freshly prepared selected mechs. Environment preparation cannot replace those
keys, and stale bindings for disabled/unselected chassis are removed from its
result. World-resource bindings remain owned by environment preparation. This
advances the installed-content-to-native-launch boundary only. It does not relax
skin admission, fake success, force a default livery, alter gameplay or recompile
native code. Formal acceptance stays 131/144.

The regression uses authored metadata and reproduces the observed kind of handoff:
complete Bushwacker/Thor B-H selections followed by a returned environment that
contains only the old Bushwacker-D binding and a disabled Orion. Before the fix,
the final session profile loses the alternate bindings. Afterward, every selected
close/distance binding survives, the disabled Orion stays absent and prepared
world banks remain present. All 25 focused dispatch, mech/environment pack and
startup-cache tests pass.

Private preparation evidence is under D:/MW3-Enemy-Pack-Diagnosis-20261022-r1.
The preparation-only run uses the actual installed packs and the recorded session
profile, writes a separate owned output, and never starts the game. It is distinct
from live visual verification. It completed successfully: the final session
profile retains all 252 alternate bindings, with all referenced files present.
Bushwacker and Thor each have B-H textures at both close and distant LODs.
prepared-binding-check.json records those assertions. This is preparation
evidence, not a native texture-load or live actor appearance check.
User settings, packs, previous logs, native host,
the open launcher and protected jobs remain intact. No commit or publication.

Retest the instructor Bushwacker in Training and the reported Thor in C2M4 after
starting a fresh game session. If a specific instance still rejects, inspect its
new source_skin/identity_rejected record and final skin bindings rather than
forcing the replacement onto an unrecognized actor.

## Follow-up after the issue persisted: actual cause and player-folder repair

Session 01e717538e604b678851618a96d35cbc still had only two alternate bindings
and 38 textures_loaded records. The earlier isolated preparation did not establish
that the player's launch context read those same installed pack copies.

A temporary read-only task, running as the logged-in player through the Windows
task service outside Codex's filesystem context, proved the difference. The real
AppData MW5 collection had Bushwacker skin D only; its other chassis had no
alternate skins. The same logical path opened from this chat resolved into
OpenAI.Codex's LocalCache and contained all seven alternate skins. Both copies
used the same pack IDs and version label. This is the actual installation cause;
the preceding coordinator ownership fix remains useful hardening but was not
sufficient to repair the older player-folder packs.

The two complete local archives from mech-alternates-20261021-r1 were installed
in the player's actual Windows context using PackStorage.Install, with all normal
file tables, hashes, containment checks, staging and rollback. A restricted
--refresh-installed-mech-pack maintenance entry in LauncherChecks only refreshes
these two already-installed collection IDs and requires games to be closed.
The physical MW5 collection now declares 196 alternate texture bindings; the
updated MW3 collection declares 56. Their old current versions are retained as
.rollback directories. User settings hashes match before and after; active order,
enabled packs, saves and native binaries were not modified.

Private receipts: outside-probe.json proves the old player-context skin lists;
the two *-installed.json receipts record the actual imported directories and
rollback identities; settings-preservation.json records unchanged settings.
The temporary probe and repair tasks were removed after successful completion.
No passwords, elevation or persistent schedule were used.

Source prevention: PackStorage.CanonicalPackRoot uses the manifest's open file
handle to resolve its physical directory. GameRunner pins all selected pack roots
before passing them to another process, so a context change cannot silently
select a different pack at a logical AppData alias. This prevention is for the
next rebuilt launcher; the existing open 1.0.18 window is not replaced. The
installed-pack repair itself is effective for that existing launcher.

A preparation-only verification completed in the actual player Windows context
under physical-context-prepared, exit 0. physical-context-success.json records
252 alternate bindings, no missing files and native_started=false. The temporary
verification task was removed. This verifies the corrected player-folder packs
and launch handoff. This preparation check does not establish live appearance.

## Agent-run native Training verification

At the user's request, Training was exercised without requiring their presence.
The private evidence root is D:/MW3-Training-Skin-Check-20261022-r1. The test
uses a separate full game copy, copied pilot/configuration and registry overlay,
the physically prepared player-pack bindings, 1280x720 windowed rendering and
an explicit midday lighting selection. No native rebuild or user-save edit.
The host SHA-256 is
BCDC770655F150423A8DF3B2FAD3446A8E1F7F81CEFF7A82A21A6AD8770FB921.

The established Training route from the lighting-performance investigation was
reused, including ordinary scripted Escape to skip the opening movie. The runner
sets a 50 ms diagnostic virtual clock when scripted input is selected; these
are not real-clock performance measurements. Early attempts consumed menu input
during the movie and supply no mission evidence. A private runner sets the
copied game as the working directory and resolves startup artifact paths before
launch. Production startup files are unchanged by this test harness.

Session-training-instructor-gpu reaches native Training and records:

- 288 textures_loaded records, compared with 38 in the reported broken session.
- A separate instructor root, 1361212952, selects source skin 7 (H), with
  replacement_available=true. The player root 1361200656 selects skin 0.
- The instructor validates as Bushwacker LOD 1 against its 13 source meshes.
  There are 36 replacement_queued records for its H livery, including GPU
  batches for its body parts. No identity_rejected record occurs in this run.
- Both Bushwacker H texture sets load with five RGB565 materials each.

This advances the evidence boundary from preparation into the live native
Training actor/model selection and GPU submission path. It confirms that the
instructor no longer rejects the absent alternate binding in this tested setup.
It does not prove visible pixels solely from queued geometry: the inspected
full-resolution captures show the player, terrain and hangar without a clear
instructor close-up. Detailed instructor appearance and the C2M4 Thor remain
unverified. No whole-mission or acceptance credit; acceptance stays 131/144.

The first successful route and final camera attempt close through normal native
ExitProcess(0); two bounded sweep/capture runs end at their explicit frame budget
(exit 1), not a normal quit. All owned temporary test tasks were removed after
their processes finished. The original registry SHA-256 matches its saved
pre-test identity, and the protected controls processes remain running.
training-render-verification.json retains the compact assertions and limits.
No commit, installer rebuild, signing or upload was performed.
