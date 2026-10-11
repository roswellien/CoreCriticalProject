# MW3 widescreen investigation — 2026-10-09

## Findings

True widescreen is a plausible pre-recompile improvement using an existing camera fix and dgVoodoo. It has not been enabled or gameplay validated in this project.

The active desktop reports 3440×1440 (43:18, commonly marketed as 21:9). The shared texture test install currently forces 1920×1440 with aspect-preserving scaling. Its Mech3.exe SHA256 is 95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf, matching the recorded official v1.2 installation. This is not evidence that community patches support this exact executable.

Changing only dgVoodoo's output aspect can stretch the existing camera image. A true wider view requires correcting the game's projection; output resolution and camera aspect must agree.

## Existing implementation

AlphaYellow's MechWarrior3FOVFix release identifies version 1.6. The publicly available C++ source reads Width, Height and FOVFactor, derives target aspect relative to 4:3, and installs three signature-based hooks for aspect and horizontal/vertical camera FOV. It contains no explicit HUD, cockpit, menu or movie layout correction. Therefore those behaviors remain separate acceptance checks.

Author source: https://github.com/alphayellow1/AlphaYellowWidescreenFixes/blob/main/source/fixes/MechWarrior3FOVFix/dllmain.cpp

Author release and installation instructions: https://github.com/alphayellow1/AlphaYellowWidescreenFixes/releases/tag/mechwarrior3

The author specifies the 32-bit Ultimate ASI Loader winmm.dll. For a Zipper Fixup executable, the author instead specifies DLL injection because that loader does not work with it. We should determine executable compatibility before choosing a loading method or replacing any existing DLL.

Community compatibility listing recommends Hi-Res Patch plus FOV Fix for widescreen and ultrawide: https://www.pcgamingwiki.com/wiki/MechWarrior_3

Whether our existing dgVoodoo path can supply the required output without a Hi-Res executable replacement remains untested. A Hi-Res patch may also alter HUD assets, which must be audited against the texture launcher archives before installation.

## Proposed isolated prototype

1. Preserve executable, dgVoodoo configuration, launcher scripts and any affected UI archives. Use a separate experimental profile; retain both existing launchers.
2. Check the fix's executable signatures and loading requirements, and identify whether a Hi-Res resolution patch is actually necessary. Keep community fixes separate from the capture/replay instrumentation.
3. Start at 1920×1080 with FOVFactor 1.0. Compare a fixed Training viewpoint to the 4:3 baseline: more world visible at the sides, consistent vertical view and undistorted objects.
4. Repeat at the actual desktop resolution 3440×1440 with the exact 43:18 aspect, rather than a rounded 21:9 value. Retain the AI profile's 4x MSAA, 16x anisotropic filtering and disabled watermark for the final compatibility pass.
5. Check cockpit, third-person view, zoom, reticle/weapon alignment, HUD readability, radar, menus, mouse targeting, cinematics, movement/fire and normal quit. Revert and verify the baseline.

Success is a wider correctly proportioned game view, usable UI and unchanged normal gameplay. Screenshot output dimensions alone cannot establish success. No game executable, texture archive or launcher was changed during this investigation.

## Recompile relevance

The prototype can provide camera/FOV reference behavior, aspect-ratio test cases and UI requirements for the future renderer. Existing runtime hooks are temporary integration mechanisms rather than the future Vulkan architecture. Captured transformed vertices are already projected, so changing their presentation alone cannot recover the wider view the game never generated.
