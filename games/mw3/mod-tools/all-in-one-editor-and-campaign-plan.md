# MechWarrior 3: All-In-One Mod Studio & Campaign Creator Plan

**Document:** `games/mw3/mod-tools/all-in-one-editor-and-campaign-plan.md`  
**Date:** 2026-11-02  
**Status:** Approved Architecture & Implementation Roadmap  
**Scope:** Unified Map, Mission, and Campaign Authoring Toolset for `MW34Recomp`

---

## 1. Executive Summary & Goals

This plan establishes a single, comprehensive authoring suite for MechWarrior 3 mods, unifying map editing, mission design, asset placement, atmospheric lighting, dynamic weather, event scripting, and multi-mission campaign creation into one application.

### Key Requirements

1. **All-in-1 Unified Viewport (2D Top-Down $\leftrightarrow$ 3D Studio):**
   - Eliminate disconnected tools. A single WebGL-based desktop application allows instant toggling between a calibrated 2D orthographic top-down tactical map (derived from `maps.zrd` recon bitmaps in `rimage.zbd`) and a full 3D perspective viewport with free-camera navigation, elevation, lighting, shadows, and mesh gizmos.
2. **Categorized In-Game Asset & Texture Library:**
   - Visual catalog of original game assets extracted from `gamez.zbd`, `mechlib.zbd`, and `texture*.zbd`, organized into intuitive taxonomies (Combat Units, Defenses, Facilities, Civic/Urban, Environmental Props, and Surface Textures).
3. **Authentic In-Game Assets (With Smart Transient Proxies):**
   - **Transient Proxies Allowed During Initial Placement:** Lightweight generic proxies (wireframe bounds, neutral placeholder volumes) may be displayed while an entity is unassigned or before a specific asset/texture is selected.
   - **Immediate Authentic Asset Replacement:** The moment an asset or texture is chosen (or placed from the palette), the proxy is instantly replaced with the actual in-game 3D mesh geometry, extracted textures, and real physical proportions.
   - In **3D Mode**, models render with their extracted meshes and selected textures. Terrain renders with authentic multi-texture blending.
   - In **2D Tactical Mode**, entities render with their accurate top-down geometric silhouettes, real collision perimeters, and directional headings, rather than abstract dots. Real satellite recon map rasters and terrain textures form the ground backdrop.
4. **Real-Time Terrain Sculpting Engine:**
   - Real-time brush-based terrain sculpting in the editor viewport (Raise, Lower, Flatten/Plateau, Smooth, and Procedural Noise).
   - Adjustable brush radius, strength, and radial falloff.
   - Live synchronization: Sculpted elevation dynamically updates the 3D terrain surface, 2D topographic contour lines, and automatically snaps placed units and structures to the new ground height ($Y$).
   - Compiles terrain vertex height deltas into `gamez.zbd` terrain node meshes.
5. **Deep Unit Customization & Multi-Tier AI:**
   - **Stock & Custom Loadouts:** Place standard stock variants (e.g. *Mad Cat Prime*, *Bushwacker Standard*, *SRM Turret Dual*) or enter the in-editor MechLab to fully customize hardpoints, weapons, armor tonnage, heatsinks, and jump jets.
   - **Multi-Tier AI Controls:** Expose both basic orders (Faction, Guard, Patrol, Ambush) and advanced tactical parameters (Pilot Skill: Green, Regular, Veteran, Elite; Engagement Range; Retreat/Eject thresholds).
6. **Multi-Media Narrative, Audio & FMV Video:**
   - **Text Dossiers:** Tactical operational briefings and on-screen mission subtitles.
   - **Original Voice Library:** Trigger original in-game radio chatter, Betty cockpit alerts, and base alarms.
   - **Custom Audio & Video Assets:** Creators can bundle custom `.wav`/`.ogg` voiceovers, music, and custom briefing/cinematic video FMVs directly into the mod.
7. **Branching Campaign Engine & Configurable Continuity:**
   - Supports both **linear mission chains** (M1 $\rightarrow$ M2 $\rightarrow$ M3) and **branching mission graphs** (alternative paths unlocked by primary/secondary objective outcomes).
   - **Creator-Configurable Continuity:** Choose between automatic reset, authentic battlefield salvage carryover (recovered enemy chassis and weapons pool), or limited MFB repair points.
8. **Tactical 2D Viewport Controls:**
   - Automatic elevation snapping: placed objects automatically calculate ground height at $(X, Z)$ with an inspector height offset slider for elevated pads or airborne dropships.
   - Multi-selection: drag-box selection for moving, rotating, and managing unit groups and patrol routes simultaneously.
9. **In-Editor Event Scripting & Trigger Engine:**
   - Author mission logic directly inside the editor without external code. Define triggers (proximity radii, target destruction, mission timers, health thresholds) and actions (spawn reinforcement lances, radio messages, objective updates, evac activation).
10. **Dual-View Objectives, Win Conditions & Nav Points:**
   - Place and connect Nav points (Alpha, Baker, Charlie, Evac) with interactive visual gizmos in both 2D and 3D. Bind primary and secondary objectives directly to placed world entities with explicit victory and loss criteria.
11. **Native Game Integration & Seamless Formats:**
   - Project source saved in human-readable JSON (`project.json`, `campaign.json`, `environment.json`).
   - Export compiles cleanly into standard engine contracts:
     - **`MW34ENV1`** (`mission-lighting.bin`): Native binary catalog for time of day, sun position, ambient/direct colors, fog, and weather.
     - **`MWBANK1`** (`map-banks.bin`): Zero-install redirect banks routing original `gamez.zbd` and `reader.zbd` paths to mod files without modifying base game files.
     - Standalone execution scripts (`Play Map - <id>.cmd` and `Play Campaign - <id>.cmd`).
12. **Complete Environment, Lighting, Time of Day & Weather System:**
   - Full control of 24-hour time of day, sun azimuth/elevation, direct and ambient light colors/intensities, sky glow, distance fog, valley mist, rain, puddle wetness, lightning, dust storms, industrial smog, heat shimmer, volcanic ash, and interior sealed isolation.

---

## 2. System Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                    MECHWARRIOR 3 MOD STUDIO                                        |
|  [Campaign: Operation Damocles v1.0]  [Mission: 02 - Canyon Ambush v]  [Mode: 2D Top-Down | 3D Studio]  |
+------------------------------------+----------------------------------+----------------------------+
|        ASSET PALETTE & LIBS        |      UNIFIED VIEWPORT (2D / 3D)   |    INSPECTOR & SCRIPTING   |
|                                    |                                  |                            |
| [*] Units (Mechs, Turrets, Tanks)  |  - 2D Orthographic Mode:         | [Entity Properties]        |
| [*] Installations (Bunkers, Comms) |    Calibrated recon map,         |   - Name, Faction, Health  |
| [*] Urban/Civic (Bridges, Blocks)  |    grid, tactical symbols.       |   - Pos (X,Y,Z), Heading   |
| [*] Environmental Props (Craters)  |  - 3D Perspective Mode:          |                            |
| [*] Tactical (Spawns, Navs, Trigs) |    Full terrain, shadows,        | [Event Scripting]          |
| [*] Texture & Material Browser     |    mesh transforms, fly camera.  |   - IF: Target Destroyed   |
|                                    |  - Interactive Gizmos:           |   - THEN: Spawn Patrol Beta|
| [Campaign Flow Manager]            |    Move, rotate, place entities. |   - RADIO: Audio Msg 04    |
|   M1 (Recon) -> M2 (Ambush) -> M3  |                                  |                            |
+------------------------------------+----------------------------------+----------------------------+
| [TIMELINE / MISSION OBJECTIVES]    Primary: [x] Destroy Radar Array   Secondary: [ ] Capture Convoy |
+----------------------------------------------------------------------------------------------------+
```

### Module Responsibilities

| Component | Path | Responsibilities |
| :--- | :--- | :--- |
| **Unified Web/3D Frontend** | `editor/web/index.html`<br>`editor/web/static/js/studio.js`<br>`editor/web/static/css/studio.css` | Dual 2D/3D WebGL viewport (Three.js), transform gizmos, asset palette, inspector, environment sliders, event trigger builder, campaign sequence manager. |
| **Studio Server & APIs** | `run_studio.py` | Local HTTP server, pack listing, export endpoints (`/api/export-pack`, `/api/export-campaign`), process execution (`/api/launch-map`, `/api/launch-campaign`). |
| **Campaign Model & Builder** | `editor/core/campaign.py` | Multi-mission campaign data structures, progression validation, pilot roster, salvage rules, campaign manifest compiler, multi-stage launcher generation. |
| **Map & Mission Model** | `editor/core/map_pack.py`<br>`editor/core/project.py` | Entity placement records, archetype mapping, objectives, drop configurations, undo/redo command stack, project serialization. |
| **Atmosphere & Weather Engine** | `editor/core/environment.py`<br>`tools/remaster-launcher/mission_lighting.py` | Time-of-day math, lighting calculation, weather parameters, and binary compilation into the native **`MW34ENV1`** wire contract. |
| **Binary Formats & Archives** | `editor/core/formats.py`<br>`editor/core/exporter.py` | Archive packing (`gamez.zbd`, `reader.zbd`), redirect bank compiler (`MWBANK1`), checksum validation, and read-only source preservation. |

---

## 3. Detailed Feature Breakdown

### A. Viewport Unification (2D Tactical & 3D Studio)
- **Shared Scene State:** Placed entities, spawns, nav points, and trigger volumes exist once in memory.
- **Camera Switching:**
  - **2D Tactical Mode:** Orthographic top-down camera locked to $-Y$. Displays the satellite recon bitmap calibrated via meters-per-pixel (`mpp`) and world offsets (`offset_x`, `offset_z`). Tactical military icons (friendly blue, enemy red, neutral yellow) represent units and installations.
  - **3D Perspective Mode:** Perspective camera with orbit/pan/fly controls, directional sun shadows, terrain surface materials, 3D meshes, and 3-axis translate/rotate gizmos.
- **Toggle Mechanism:** Top-level mode button and hotkey (`Tab` or `Space`) smoothly transitions camera projection without reloading the scene.

### B. Categorized Asset & Texture Palette
Assets are cataloged into clear categories:
1. **Combat Units:**
   - *Mechs:* Inner Sphere (Bushwacker, Shadowcat) and Clan (Mad Cat, Thor, Vulture, Daishi).
   - *Stationary Turrets:* SRM Turret, Laser Turret, Heavy Tripod Gun, Missile Battery.
   - *Support Craft & Vehicles:* Dropships, Cargo Transports, Hovercraft.
2. **Defenses & Military Fortifications:**
   - Hardened Bunkers, Perimeter Defense Walls, Heavy Security Gates, Radar Outposts, Communications Dishes.
3. **Facilities & Industrial:**
   - Manufacturing Plants, Fuel Silos, Power Stations, Repair Gantries, MFB Maintenance Bays, Pipeline Assemblies.
4. **Civic & Urban:**
   - Modular City Buildings, Office Complexes, Highway Ramps, Bridges, Shore Docks.
5. **Environmental Props & Natural Formats:**
   - Rock Outcroppings, Desert Mesas, Impact Craters, Fallen Debris, Concrete Barricades.
6. **Surface Texture & Biome Browser:**
   - Browse terrain texture banks by operation (`c1` Coastal, `c2` Desert, `c3` Volcanic, `c4` Highlands, `t1` Training).

### C. Authentic In-Game Assets & Texture Presentation (With Transient Proxies)
The editor supports lightweight transient proxies during preliminary actions, followed by immediate authentic replacement:
- **Transient Placement Proxies:** When creating a new entity or before the user selects a specific model/texture from the catalog, the editor displays a lightweight wireframe or bounding box proxy for rapid layout planning.
- **Immediate Authentic Replacement:** As soon as an asset or texture is chosen (or placed from the categorized palette), the proxy is instantly upgraded to:
  - **3D Perspective Mode:** Exact polygon meshes extracted from game archives (`gamez.zbd`, `mechlib.zbd`) with authentic diffuse textures and materials applied in real time.
  - **2D Tactical Mode:** True-to-scale top-down geometric silhouettes and bounding footprints matching the actual 3D geometry and yaw orientation, rendered over the calibrated satellite recon raster (`maps.zrd`) and authentic surface textures.

### D. Environment, Lighting, Time of Day & Weather Studio
Real-time controls with instant viewport updates:
- **Time of Day:**
  - 24-Hour continuous slider (00:00 to 24:00) driving sun position and ambient temperature.
  - One-click presets: *Dawn*, *Morning*, *High Noon*, *Sunset*, *Dusk*, *Night (Moonlit)*, *Pitch Black*.
- **Direct Sun & Ambient Lighting:**
  - Sun Azimuth ($-360^\circ$ to $360^\circ$) and Elevation ($0^\circ$ to $90^\circ$).
  - Sun Color (RGB) & Intensity ($0.0$ to $4.0$).
  - Ambient Color (RGB) & Intensity ($0.0$ to $2.0$).
  - Sky Tint (RGB), Sky Brightness, Sky Glow Color, and Glow Focus spread.
- **Distance Fog & Atmospheric Haze:**
  - Fog Distance ($0$ to $10,000$ meters) and Haze Color (RGB).
  - Horizon Low/High blend thresholds.
  - Valley Fog Altitude and Density (low-lying ground fog/smog).
- **Dynamic Weather System:**
  - Rain Intensity ($0\%$ to $100\%$) and Surface Puddle Wetness / Specular Sheen ($0\%$ to $100\%$).
  - Lightning Flash toggle (periodic atmospheric strikes).
  - Dust Storm Intensity ($0\%$ to $100\%$).
  - Industrial Smog / Smoke Intensity ($0\%$ to $100\%$).
  - Heat Shimmer / Mirage ($0\%$ to $100\%$).
  - Volcanic Ash & Lava Glow ($0\%$ to $100\%$).
  - Interior / Sealed Flag (suppresses sky dome and outdoor weather for underground facilities).

### D. Mission Logic, Nav Points & Event Scripting
- **Interactive Nav Network:**
  - Place and position Nav points (Alpha, Baker, Charlie, Delta, Evac) in 2D or 3D.
  - Automatic waynet connection lines displaying route progression.
- **Objectives Manager:**
  - Configure Primary, Secondary, and Hidden/Bonus objectives.
  - Bind objectives to map assets (e.g., target a specific radar antenna node, defend fuel silos, reach evac zone).
  - Explicit victory conditions (e.g. All Primaries complete + Reach Evac) and loss conditions (Player mech destroyed, VIP destroyed, timer elapsed).
- **Rule-Based Visual Scripting Engine:**
  - **Conditions:** `OnAreaEntered(nav_point, radius)`, `OnTargetDestroyed(asset_id)`, `OnHealthBelow(asset_id, pct)`, `OnTimerElapsed(seconds)`.
  - **Actions:** `SpawnLance(chassis_list, spawn_point)`, `SetAIOrders(patrol | guard | attack)`, `PlayRadioDialogue(message_id, audio_track)`, `CompleteObjective(obj_id)`, `FailObjective(obj_id)`, `ActivateNavPoint(nav_id)`.

### E. Campaign Creator & Multi-Mission Sequencer
- **Campaign Manifest (`campaign.json`):**
  - Campaign Title, ID, Faction (Inner Sphere / Clan / Mercenary), Lore Briefing, Operation Theater.
- **Mission Flow Graph:**
  - Sequence order: Mission 1 $\rightarrow$ Mission 2 $\rightarrow$ Mission 3 $\rightarrow$ Mission 4.
  - Support for branching mission choices based on optional objective outcomes.
- **Inter-Mission Continuity:**
  - Pilot roster state (status: Active, Injured, KIA; assigned chassis).
  - Salvage pool carryover (recovered enemy mechs, weapons, and ammo between drops).
  - MFB / field repair resource availability.
- **Campaign Exporter:**
  - Compiles full campaign directory into `mods/campaign-packs/<campaign_id>/`.
  - Generates unified multi-stage runner `Play Campaign - <campaign_id>.cmd` with stage selection.

---

## 4. In-Game Integration & File Contracts

The editor writes two categories of files:

### 1. Distributable Project Sources (Human-Readable JSON)
- `project.json`: Complete map layout, placed assets, transforms, and properties.
- `environment.json`: Time of day, sun angles, colors, fog, and weather settings.
- `campaign.json`: Multi-mission sequence, briefings, pilot rosters, and salvage rules.

### 2. Compiled Engine Runtime Data (Zero-Install Mod Overlay)
- **`mission-lighting.bin` (`MW34ENV1` Contract):**
  - Little-endian binary catalog parsed directly by `mw34::packs::load_mission_environments` in the native host (`MW34_MISSION_ENVIRONMENTS`). Encodes sun angles, colors, sky properties, shadows, and all weather channels.
- **`map-banks.bin` (`MWBANK1` Contract):**
  - Binary file redirect bank parsed by the native engine. Maps `zbd/<op>/gamez.zbd` and `zbd/<op>/reader.zbd` to the mod's authored archives.
- **`gamez.zbd` & `reader.zbd`:**
  - Repacked binary archives containing the modified scene node hierarchy, spawn coordinates, and waypoints. Base game files are never modified.

---

## 5. Staged Implementation Phases

### Phase 1: Viewport Unification & Atmosphere/Weather Studio
- Integrate 2D orthographic top-down camera with calibrated recon map texture directly into the 3D Studio viewport with a 1-click toggle (`2D Tactical` $\leftrightarrow$ `3D Perspective`).
- Build the **Environment & Atmosphere Studio** panel with 24-hr time slider, sun position/color, fog, and dynamic weather controls with real-time Three.js viewport preview.
- Integrate the `MW34ENV1` binary export into `editor/core/environment.py`.

### Phase 2: Real-Time Terrain Sculpting Engine
- Build real-time brush-based terrain sculpting directly in the editor viewport (Raise, Lower, Flatten/Plateau, Smooth, Noise) with brush radius, strength, and falloff controls.
- Implement live ground elevation sampling: all placed entities and structures automatically snap their ground elevation ($Y$) to the sculpted terrain at $(X, Z)$ with an optional inspector height offset.
- Real-time topographic contour line overlay in 2D mode and terrain displacement compilation for `gamez.zbd` export.

### Phase 3: Categorized In-Game Asset & Texture Catalog
- Implement the structured taxonomy catalog (Combat Units, Defenses, Facilities, Civic, Props, Textures) with transient proxy placement and immediate authentic asset replacement.
- Add category filters, search bar, and thumbnail previews to the Studio sidebar.
- Enable drag-box multi-selection in both 2D and 3D modes for group manipulation.

### Phase 4: Unit Customization & Multi-Tier AI
- Integrate stock variant presets and custom in-editor MechLab loadout editor (weapons, armor tonnage, heatsinks, jump jets).
- Implement multi-tier AI controls: Faction (Friendly/Enemy/Neutral), base stance (Guard/Patrol/Ambush), and pilot skill tiers (Green, Regular, Veteran, Elite) with engagement and retreat thresholds.
- Dual-mode interactive Nav point placing, waynet route lines, and objective target binding.

### Phase 5: In-Editor Event Scripting & Multi-Media Narrative
- Build the rule-based event trigger editor (Conditions $\rightarrow$ Actions).
- Support multi-media narrative: text briefings, original radio/Betty audio callouts, custom `.wav`/`.ogg` audio import, and custom cinematic video FMVs.

### Phase 6: Campaign Creator & Branching Mission Progression
- Create `editor/core/campaign.py` managing `CampaignProject`, `CampaignMission`, and `CampaignBuilder`.
- Support both linear mission chains and branching mission graphs with creator-configurable salvage/repair rules and pilot roster tracking.
- Build the Campaign Manager modal in the Studio UI.
- Implement `/api/export-campaign` and `/api/launch-campaign` endpoints.

### Phase 7: Verification Suite & Launcher Validation
- Add automated regression tests in `games/mw3/mod-tools/tests/test_campaign_builder.py`, `test_terrain_sculptor.py`, and `test_environment_builder.py`.
- Validate `MW34ENV1` binary round-trips and `MWBANK1` redirect integrity.
- Verify clean launch in the native engine without modifying base game files.
- Add automated regression tests in `games/mw3/mod-tools/tests/test_campaign_builder.py` and `test_environment_builder.py`.
- Validate `MW34ENV1` binary round-trips and `MWBANK1` redirect integrity.
- Verify clean launch in the native engine without modifying base game files.
