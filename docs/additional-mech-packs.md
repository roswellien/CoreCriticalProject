# Additional mech packs

Statistics and named-variant reference:
[Marauder statistics and MW3 mapping](marauder-stats-reference-2026-10-25.md).

The intended modder workflow matches additional skin packs: author content,
build a data-only `.mw3pack`, install it under Mods & Packs, enable it and select
the additional mech in the normal Mech Lab. Installing a new compatible chassis
must not require editing native source, assigning an engine number or rebuilding
the launcher. The Marauder is the first integration case, not a special engine
branch. The private October 25 candidate now installs and discovers these packs
through the launcher and reaches a live mission. It is not yet a released or
fully validated content capability.

## Authoring responsibilities

A mech project will describe its stable namespaced identity, display name,
gameplay definition and default loadouts, visual model/LODs and materials,
animation/controller compatibility, weapon attachment points and damage parts.
These are content data. The authoring tool should generate legacy resource
names, compiled payloads, integrity hashes and the package manifest. Modders
should not need to learn native addresses or hand-edit the original archives.

Existing compatible animation/controller templates may be reused through data.
Adding an entirely new animation system or engine behavior can require engine
work; adding another mech within the supported content contract should not.
Additional skins should target the new chassis's stable identity and appear in
its normal skin selector, preserving its other skins.

## Identity and compatibility

Pack/chassis IDs are stable, namespaced strings. Runtime numeric IDs are private
to a session and must never be the durable identity in a save. Stock indices
0–18 and the original Mech Lab's unselected marker at 19 remain reserved.
Disabling required content must produce a useful missing-content message;
reordering installed packs must not silently change a saved mech.

The engine must reject duplicate chassis/resource identities, unsupported
payload versions, missing dependencies and invalid definitions. Ordinary mech
content packs remain data-only community content; they are not executable
launcher/game updates. Hashes establish payload identity, not a requirement
that every community modder obtain a code-signing certificate.

## Implemented private boundary

The current work adds a bounded catalogue bridge, additional resource composition,
native definition lookup/cache ownership, Instant Action list insertion and
Mech Lab inventory/preview construction. The original game constructor and
definition parser still create and validate each object. Existing reader archive
members and metadata are retained byte for byte. Unknown catalogue fields and
stock-name collisions are rejected.

The first metadata bridge inherits mass, weight class and technology from a
named stock template, including the original floating-point return contract.
This is a deliberately limited loader boundary, not the final arbitrary-stat
authoring contract. It must not be published as completed chassis-pack support.

The private native check constructs two data-defined entries at indices 32 and
33, verifies separate caches and unchanged stock Mad Cat identity, and exercises
the original destructor/operator-delete cleanup. The test definitions are copies
of the local original Mad Cat definition under new resource names. They prove
additional definition loading, not completed Marauder stats or gameplay.

## Native Marauder prototype: October 25

The Marauder now appears independently in Instant Action and the original Mech
Lab stockpile. Original stockpile ordering follows chassis IDs; the additional
entry is after the stock mechs. The real list callback selects its configuration,
the original parser accepts its own 75-ton loadout, and the native renderer
displays its assembled MW5 body, cockpit and five weapon meshes. The stock Mad
Cat remains a separate entry and retains its own replacement model.

Catalogue version 2 can bind an additional chassis to two prepared geometry/
texture pairs and a named original visual controller. Gameplay metadata and the
visual controller are separate: this prototype uses Orion's 75-ton Inner Sphere
metadata and Mad Cat's articulated controller. The renderer extends its existing
stock table from validated data and distinguishes resource/actor identity before
matching controller mesh signatures. There is no Marauder branch in native code.

The private prototype uses review colours, dominant-bone rigid geometry and
unoptimised full geometry at both distances. Its MW3-compatible field refit has
two ER PPCs, two medium lasers, an Ultra AC/5, a standard 300 engine and standard
structure. It is not a claim of the classic MAD-3R's standard PPC/AC5 weapons.
Movement, collision, damage, muzzle alignment and saved-content compatibility
still need their own evidence.

Original actor getters can fuse a direct tail jump into a lifted body. The
catalogue adapter covers the recovered actor-to-definition and actor-to-tech
getters as well as ordinary catalogue calls. It still executes the original
return path and obtains genuine constructed definitions; it does not seed actor
state or make an unknown service succeed.

## Launcher discovery and packaged Marauder: October 25

`additional-chassis-v1` is now understood by the launcher pack importer and
Python coordinator. `chassis/chassis.json` supplies namespaced IDs, display
names, metadata/controller templates, an authored JSON definition and two
geometry/material bindings. Neither the importer nor native loader contains a
Marauder-specific registration. An additional compatible pack is discovered
from the enabled manifests on the next launch; no source edit or rebuild is
needed. Older runtimes reject the new capability with an update message.

`build_chassis_pack.py` produces an unsigned, data-only `.mw3pack`. The launcher
composes private reader/model resource aliases from the player's original
archives, preserving every original member. A resource alias derives from the
stable chassis ID rather than installation order. Authored definitions cannot
execute commands or replace original archive members. Mass, weight class and
technology must match the declared metadata template in this first contract.

Separate skin packs can target the new namespaced chassis ID. They use the
existing additional-skin discovery, mesh identity checks, Mech Lab selector and
saved skin preference mechanism. The native visual/damage bridge inherits the
declared controller's verified arm-loss signatures instead of comparing an
additional mech ID to stock names.

The local Marauder `0.1.0-preview` pack was imported through the real C#
PackManager, composed with the currently installed stock replacement pack and
selected in the original Mech Lab. The native run reached a live mission and
the intended 2,700-frame limit with scripted movement and firing inputs. Logs
identify the additional Marauder actor and replacement geometry in the world.
This is bounded integration evidence, not proof of collision, damage, AI or
save/reload correctness. Its UV-locked body masks/wear and shared weapon detail
replace the earlier flat review colours. Distance geometry remains full detail
and the retained normal map is not yet bound by this profile.

Review exposed two Mech Lab presentation defects: fitting each frame's rotated
silhouette caused the mech to grow/shrink, and the inherited camera looked up
from ground level. The maintained candidate now computes a rotation-invariant
framing sphere from donor rest geometry, retains the turntable yaw, and uses a
long-lens camera ten degrees above the target. Full-turn mathematical checks
verify a constant focal scale, fixed centre, panel containment and above-target
view for both projection-axis conventions. A 1,500-frame native Mech Lab run
confirmed the framing at several angles, including front, rear and three-quarter
views. This change has not been activated in DEV.

The normal Mech Lab Save/Done route also wrote a `Primarytest` user variant to
the stable, ID-derived configuration filename. A two-pack reload test moved
Marauder from session index 32 to 33, but the guard stopped that run when a
separate video encoder started. It did not reach the Mech Lab; save/reload
compatibility therefore remains unverified. The prior saved file and interrupted
run evidence are preserved.

Local artifacts and runtime checks are under
`local/work-ahead/marauder-prototype-20261024-r1/` and
`D:/MW3MarauderPackNative-20261025-r2/`. Generated/original resources remain
local. Authoring instructions: [Additional mech authoring](authoring-additional-mechs.md).

## Remaining integration

- Finish mission and lifecycle validation of the additional selection path.
- Finish donor textures, distance optimisation, collision/muzzle/damage bindings,
  and additional-skin discovery for namespaced chassis IDs.
- Support independent gameplay metadata and validate authored loadouts through
  the original rules.
- Persist stable chassis/skin IDs across saves and report absent content.
- Validate selection, movement, aiming, firing, damage, AI and save/reload with
  at least two independent chassis packs before freezing the authoring schema.

The experimental profile is supported by the new importer/coordinator but is
not advertised by the installed DEV host. A private host supplied the capability
for the above integration run. Do not advertise it in a public runtime until the
remaining lifecycle and compatibility checks pass. Acceptance stays 131/144.
