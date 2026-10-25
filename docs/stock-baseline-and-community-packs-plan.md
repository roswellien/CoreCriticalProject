# Stock baseline and community content packs

Owner direction recorded **2026-10-24**. This governs subsequent launcher,
renderer, content-pack and editor implementation. It clarifies the faithful
modernization strategy; it does not authorize a gameplay remake or change
formal acceptance (**131/144**).

## Required product behavior

With no enabled packs and optional graphics enhancements off, MW3 must use
the supplied original game's models, textures, lighting, sky, environments,
weather, weapons, missions, audio and other content. Removing packs must not
leave remastered bindings, campaign art presets or enhanced weapon visuals
behind. Modern platform services, compatibility/crash fixes and user-selected
display/input options remain runtime responsibilities; their existence is not
proof of pixel-perfect original fidelity.

The launcher must expose **Dynamic Lighting** under **Display / Graphics**.
It defaults off for the stock baseline and persists the user's explicit choice.
Its final label/help text must accurately describe the enhanced lighting it
controls. Installing or updating a pack must not silently enable it.

| Enabled packs | Dynamic Lighting | Intended result |
| --- | --- | --- |
| None | Off | Original assets and original lighting/environment/weather |
| None | On | Original assets/environment/weather with the explicitly selected enhanced lighting |
| Model/texture replacements | Off | Selected replacement assets, original lighting behavior |
| Model/texture replacements | On | Selected replacement assets with enhanced lighting |
| Explicit environment/map/mission pack | Either | Only that pack's selected content/conditions; enhanced lighting still respects the user's switch |

The no-pack stock requirement and independent lighting toggle coexist: enabling
the switch is an explicit graphics opt-in, not a pack installation. Original
campaign conditions must not be replaced by the remaster's lore/art schedule
merely because enhanced lighting is on.

The campaign art direction and October 24 environment audit remain useful
authoring/evidence. Their altered times, skies and weather belong in an
**optional campaign environment pack**, not unconditional stock-game behavior.
Sky source and environment presentation must become versioned pack/mission
data rather than a permanent hardcoded assignment for the original 20 IDs.
Preserve underground behavior for the stock interior maps. New maps need their
own explicit interior/exterior metadata instead of inheriting a stock ID's
assumptions accidentally.

Enhanced missile exhaust, weapon-light gains, remastered status models and any
other changed visuals must have an explicit enhancement/content owner. A model
replacement must follow the selected model pack, including previews and LODs.
The no-pack/off path must not retain those enhancements as invisible defaults.

## Packs extend or replace stock content

The owner wants optional, authorable packs for:

1. MW5 model replacements for existing MW3 chassis.
2. Remastered textures for individual models/assets, groups, maps or operations.
3. Environment/lighting/weather authoring, including the established campaign art plan.
4. New maps.
5. New missions and eventually campaigns.
6. New mech chassis, not only visual replacements of existing roster slots.
7. New weapons, with declared behavior supported by the runtime.
8. Other supported content such as HUD/menu art, sounds, music and cinematics.

Packs may combine supported components but must not require unrelated upgrades.
Model and texture replacements can declare necessary mesh/UV/material
dependencies. Content addressing must be specific enough to replace one asset
without requiring a whole-operation texture bank replacement.

Install packs separately from original game files. Resolve selected content as
an overlay over the original resources; an absent replacement falls back to
the original asset. A selected but missing/corrupt dependency must fail visibly,
not masquerade as a successful fallback. Disabling/removing a pack restores the
underlying content and invalidates its prepared bindings/cache entries.

Use stable namespaced content IDs for additions. Declare pack ID/version,
required runtime capabilities, dependencies and conflicts, and resolve overlaps
deterministically. Do not silently rewrite existing save references when a
required added mech, weapon or mission pack is unavailable.

## Current capability versus required implementation

Source inspection on October 24 establishes the following; these are not
whole-campaign fidelity claims.

| Area | Current support | Additional work |
| --- | --- | --- |
| MW5 replacement models | Prepared mech packs bind supported existing chassis/LOD/skins | Component independence and complete no-pack cleanup/stock validation |
| Remastered model/operation textures | Prepared mech/environment resources and stock-model texture packs exist | Consistent granular overlays, dependencies and independent activation |
| Environment settings | Versioned mission-lighting catalogs and installed resources exist | Separate from stock; make sky/environment policy data-driven; retain independent graphics choice |
| New maps/missions | Editor/Map Studio preview and export foundations exist | Portable native registration, selection, world/objective/spawn loading, AI, completion and save/load validation |
| New chassis | Current prepared model reader enumerates existing MW3 chassis IDs | Extend roster/stat/loadout/animation/damage/AI/save contracts beyond replacing a fixed slot |
| New weapons | Existing weapon/effect runtime is available | Versioned weapon/ammo/projectile definitions and runtime hooks; selection, damage, AI, attachments and saves |
| UI/music/cinematics | Existing versioned content capabilities | Continue the same editor-to-pack contracts; unsupported behavior requires actual runtime work |

Important present violations of the intended separation:

- `prepared_environment_packs.profile_bindings` disables selected effect/detail
  channels with no environment packs, but can retain base-profile sun, automatic
  campaign presets and weather flags. Installing an environment pack also
  currently enables effect lights in those bindings. Neither behavior is an
  independent user lighting switch.
- Built-in campaign art presets and the new mission-ID sky policy can affect
  the base host without a selected environment catalog. Those are optional
  presentation features to gate, not the stock environment definition.
- Existing pack capability declarations cover resource readers. They do not
  establish support for arbitrary new mission, chassis or weapon IDs. Advertising
  a new capability requires implementing and validating its runtime behavior.

## Creator workflow

The intended workflow is **editor project → validate/preview → export content
pack → import/enable in launcher → play**. The owner's editors and community
tools must target the same documented resource schemas and runtime contracts.
Do not require creators to modify native source or rebuild the engine for
ordinary content that the declared capabilities support.

Use original asset references or distributable authored deltas/content as
appropriate. Export original-dependent material locally; do not bundle the
original game indiscriminately. Existing private precompiled-runtime delivery
does not authorize committing generated game code or media.

Community content packs already do not require a project signing certificate;
retain that property. Launcher/runtime code updates keep their existing trusted
signature checks. A content pack must not grant itself a runtime capability or
silently install executable behavior. A weapon with new behavior outside the
implemented definition types needs a runtime extension delivered separately.

## Implementation order and acceptance

1. **Establish the stock launch path.** Audit every enhancement/binding and gate
   it explicitly. Check fresh installs and installations that previously enabled
   packs. Done when no-pack/off launches original content and disable/restart
   removes stale enhanced resources/presets without changing original files.
2. **Add the independent graphics switch.** Apply user intent after content
   composition so a pack cannot re-enable disabled lighting. Keep supported
   texture/model packs usable with lighting off; validate on/off in packed and
   unpacked launches and preserve the choice through updates.
3. **Separate and migrate existing packs.** Split model/texture/environment
   components as needed, move the campaign art schedule to optional data, and
   make overlays/cache identities reflect the exact selected components.
4. **Add maps/missions end to end.** Implement one authored addition with a new
   identity through editor export, portable import, native selection, gameplay,
   objectives, normal completion and save/reload before advertising support.
5. **Extend mech/weapon registries.** Prove one genuinely added chassis and
   weapon without displacing a stock entry. Check loadouts, AI, damage, ammo,
   attachments, preview/HUD and save references before generalizing the editor.

Use signed cumulative `.mw3update` packs for required native/coordinator changes
and launcher updates for UI/manager changes. Code updates must not silently
enable optional packs or reset user graphics choices. Pack compatibility follows
implemented capability/format versions rather than each native executable hash.

The first stock-selection/graphics milestone is now implemented in
[Core Critical 1.0.30](stock-presentation-and-first-run-setup-2026-10-24.md),
including shared first-run/Display options and independent shadow preferences.
The linked record states the checks and limits. Finer pack component separation,
independent environment/effects authoring and additive content registries remain
implementation work; this plan does not claim they already function.
