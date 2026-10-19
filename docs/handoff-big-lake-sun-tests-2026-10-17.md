# MW34Recomp: Big Lake Sun Tests Handoff Summary

**Date:** 2026-10-17
**Workspace:** `d:\Projects\MW34Recomp`
**Host Target:** `C:\Users\jcbla\MW34SunTests\big-lake-r1\shadow-r1\host\`
**Launcher Entry Point:** [`Play MW3 - Big Lake Sun Tests.cmd`](file:///d:/Projects/MW34Recomp/Play%20MW3%20-%20Big%20Lake%20Sun%20Tests.cmd)
**Profile Config:** [`local/remaster/big-lake-sun-tests.json`](file:///d:/Projects/MW34Recomp/local/remaster/big-lake-sun-tests.json)

---

## 1. Executive Summary

During this work cycle, we diagnosed and resolved visual and performance issues on the **Big Lake Sun Tests** standalone remaster host (`shadow-r1`), and expanded its high-fidelity model override system from 7 chassis (13 entries) to **all 15 mech chassis** across both LOD0 and LOD1 (**30 models total**).

All 15 mechs now feature:
- Recompiled GPU mesh overrides with visual donor retargeting (`BWMESH4`).
- Directional sun lighting, cascaded shadow mapping, and normal mapping.
- Cockpit and arm damage visual plans.

---

## 2. Issues Investigated & Resolved

### A. Skybox Seams, Horizon Bands, and Performance Hitching
1. **Symptom:** Skybox visual corruption (visible seams/banding, dark lines across the dome), followed by frame hitching.
2. **Root Cause Analysis:**
   - The skybox shader (`sky_procedural.hlsl` / `sky_draw.inc`) was recalculating analytic scattering approximations per-pixel without proper spherical clamping, causing horizon discontinuities when rotating the viewport.
   - Ground/sky contrast re-weighting was introducing micro-stutters during camera rotation due to branch divergency in the pixel shader.
3. **Fixes Applied:**
   - Clamped zenith and horizon spherical mappings smoothly in the pixel shader.
   - Cleaned up duplicate state bindings in the composition pass.
   - Standardized the sun preset profiles in [`tools/remaster-launcher/sun-presets.json`](file:///d:/Projects/MW34Recomp/tools/remaster-launcher/sun-presets.json).

### B. High-Poly Model Override Coverage Expansion
1. **Previous State:**
   - The Big Lake test host only defined 7 chassis (Bushwacker LOD0, Mad Cat, Vulture, Thor, Orion, Daishi, Shadowcat).
   - In Big Lake Instant Action, dynamically spawned mechs (Puma, Annihilator, Cauldron-Born, Sunder, Supernova, Black Hawk, Champion, Strider, and Bushwacker LOD1) triggered `identity_rejected` and fell back to legacy software-rendered geometry.
2. **Ported Architecture & Shaders:**
   - Ported the full visual solver and donor runtime from `local/remaster/gpu-native-bushwacker-skins-r1/host-source/`:
     - [`donor_retarget.hpp`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/donor_retarget.hpp)
     - [`donor_runtime.inc`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/donor_runtime.inc)
     - [`override_cockpit_rosters.inc`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/override_cockpit_rosters.inc)
     - [`override_additional_rosters.inc`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/override_additional_rosters.inc)
     - [`override_additional_lod1_rosters.inc`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/override_additional_lod1_rosters.inc)
     - [`override_bushwacker_lod1.inc`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/override_bushwacker_lod1.inc)
     - [`override_arm_damage_plans.inc`](file:///C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/override_arm_damage_plans.inc) (expanded from 26 to all 58 damage plans).
3. **Asset Migration:**
   - Transferred native mesh binary archives (`*-native.bin`, `*-lod1-native.bin`) and texture bundles (`*-textures.bin`, `*-lod1-textures.bin`) to `C:/Users/jcbla/MW34SunTests/big-lake-r1/assets/models-r2/`.

---

## 3. Current Build & Environment State

### Host Binary
- **Path:** `C:\Users\jcbla\MW34SunTests\big-lake-r1\shadow-r1\host\entry_commandline.exe`
- **Compiler:** Clang-CL (C++20) + Ninja
- **Executable SHA-256:** `f84f567eaf8b9c973c1609fe22f31f7ddd9f7180ea29e85f0ae7e2ba71a5cee6`
- **Build Script:** `C:\Users\jcbla\MW34SunTests\big-lake-r1\shadow-r1\host\build.ps1`

### Launcher Configuration
- Profile [`local/remaster/big-lake-sun-tests.json`](file:///d:/Projects/MW34Recomp/local/remaster/big-lake-sun-tests.json) has been updated with:
  - The latest `entry_commandline.exe` SHA-256 hash.
  - All 30 environment variables mapping meshes and texture archives for all 15 chassis.

### Active Acceptance Status
- Legacy acceptance tests remain intact at **131/144** (preserves project rule in `AGENTS.md`).

---

## 4. Verification Results

In scripted validation run `play-runs/20261017-171614-876`, the host loaded Instant Action and recorded real-time identity matching and rendering:
- `madcat` (LOD 0): Matched & queued (11,204 torso tris, arms, legs).
- `bushwacker` (LOD 0 & LOD 1): Matched & queued with Freya skin D textures.
- `cauldron` (LOD 1): Matched & queued.
- `champion` (LOD 1): Matched & queued (9,864 torso tris, etc.).
- `supernova` (LOD 0): Matched & queued (8,590 torso tris, etc.).

All rendered mechs cast real-time shadows onto Big Lake terrain and water with directional sun shading.

---

## 5. Notes & Outstanding Items for the Next Agent

1. **Unmatched Weapon Configuration Signature:**
   - During match logging, one chassis signature was rejected:
     ```json
     {"event":"identity_rejected","root":1356960744,"meshes":[{"name":"head","vertices":4},{"name":"hip_polys","vertices":16},{"name":"larm","vertices":24},{"name":"lcalf","vertices":24},{"name":"lfoot","vertices":18},{"name":"lhand","vertices":30},{"name":"lthigh","vertices":18},{"name":"ltoe01","vertices":6},{"name":"ltoe02","vertices":6},{"name":"ltoe03","vertices":6},{"name":"rarm","vertices":24},{"name":"rcalf","vertices":24},{"name":"rfoot","vertices":18},{"name":"rhand","vertices":34},{"name":"rthigh","vertices":18},{"name":"rtoe01","vertices":6},{"name":"rtoe02","vertices":10},{"name":"rtoe03","vertices":6},{"name":"torso_polys","vertices":76}]}
     ```
   - This matches the Clan leg setup (Mad Cat / Vulture family) with an alternate torso (76 vertices) and alternate arm pods (`lhand`: 30, `rhand`: 34).
   - If desired, this variant can be added to the chassis roster table so this variant receives the high-poly model as well.

2. **User Launch Shortcut:**
   - The user can launch live gameplay at any time via [`Play MW3 - Big Lake Sun Tests.cmd`](file:///d:/Projects/MW34Recomp/Play%20MW3%20-%20Big%20Lake%20Sun%20Tests.cmd).
