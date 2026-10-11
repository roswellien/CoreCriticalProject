# MW3 camera fix bootstrap

The original winmm.dll and version.dll ASI-loader trials produced no FOV logs. During the version.dll diagnostic, module observation showed Windows' system VERSION.dll/WINMM.dll despite the local loader being present. The project therefore uses explicit loading through its existing hash-admitted Win32 pre-entry launcher.

Build with Win32 MSVC and CMake. The bootstrap checks the downloaded FOV Fix 1.6 SHA256, explicitly loads it, and waits for its three camera-signature log lines. Failure cancels only the newly created, still-suspended game process. The shared launcher restores its temporary configuration and files after the game session closes. No DirectDraw provider is replaced and no graphics capture hook is installed.

The signature messages precede third-party hook creation. A brief delay is allowed for that worker; messages and module presence establish loading/signature detection, not complete hook correctness or visual success. Gameplay is still required. HUD/menu layout is not corrected by this plugin.

Observed diagnostic: `local/work-ahead/training-game-launchers/widescreen-runs/20261009-181823-228-3440x1440-Native`. Plugin module was present in PID 31000; source log reported aspect at RVA 0xf3e07, horizontal FOV at 0xd5cc and vertical FOV at 0xd5bc. These are observations for the admitted executable only.

Authored bootstrap and launcher compiled with /W4 /WX. Plugin identity self-test passed, and a missing-plugin negative control was rejected without starting a game. Gameplay and UI checks remain pending.

Source of the third-party plugin: https://github.com/alphayellow1/AlphaYellowWidescreenFixes/blob/main/source/fixes/MechWarrior3FOVFix/dllmain.cpp

## User observation after explicit loading

In `20261009-182102-603-3440x1440-Native`, the user reported that world assets seemed correctly proportioned, the HUD stretched, and walking felt jerky at each mech step compared with the smooth baseline. The user did not identify this as a frame-rate problem. Treat this profile as a failed overall compatibility test; camera projection appearance alone is insufficient.

The saved baseline and test configs both use FPSLimit=30, 4x MSAA and aspect-preserving scaling. A configured frame limit is not evidence of identical actual frame pacing. The camera plugin and wide render dimensions remain candidates; no cause of the step-linked motion is established.

`Launch MW3 AI FOV Control 1920x1440.cmd` uses the same explicit camera plugin at the original 4:3 aspect and original 1920x1440 rendering size. Compare it with `Launch MW3 with AI Upscales.cmd` in the same Training mech/viewpoint. This holds texture/graphics settings and resolution constant while changing whether the plugin is active. If the control introduces jerking, investigate plugin hooks first; if only the ultrawide profile does, investigate aspect-dependent projection/camera motion and measured frame pacing. No visual control result is recorded yet.
