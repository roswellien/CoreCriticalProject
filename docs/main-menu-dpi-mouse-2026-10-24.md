# Main-menu mouse and display scaling — runtime candidate 1.0.35

The owner reports main-menu pointer movement restricted to the edges on one
laptop, requiring Ctrl+Alt+Delete to terminate the game. A second laptop works.
The affected display is 1920×1080 at 125%; both an external mouse and the
built-in touchpad are affected. Reducing Windows scaling restored control.
This confirms a scale-dependent trigger, not every cursor call responsible.

The selected 1.0.34 native source has no explicit DPI-awareness setup. Real
DirectInput and USER32 cursor calls are forwarded; scripted mouse input cannot
reproduce or close this physical-device report. The correction targets native
display/cursor coordinate consistency rather than mouse sensitivity or gameplay.

## Candidate correction

`runtime/graphics/native_host.manifest` declares PerMonitorV2 before process or
window initialization, following Microsoft's recommended
[embedded-manifest approach](https://learn.microsoft.com/en-us/windows/win32/hidpi/setting-the-default-dpi-awareness-for-a-process).
Native window/cursor calls then use physical pixels without Windows bitmap
virtualization. The user's desktop scale is unchanged.

The entry point checks/logs effective DPI awareness before original game
initialization. An incompatible Windows DPI override fails visibly before
guest startup. `--check-display-dpi` checks the actual executable without a game
launch. The check preserves last-error state. `apply_display_dpi.py` patches a
fresh host snapshot, and the optimized native builder embeds its manifest.
No interpreter, original-process fallback, guest-state seeding or fake success.

Signed runtime test update **1.0.35**, sequence **2026102410**, requires launcher
**1.0.34+**. It retains the published 1.0.34 runtime's translated module and all
664 registered files/components. This targeted candidate does not activate over
concurrent DEV/model work or replace the main installer/catalog. No launcher
update is needed. Physical 125% laptop retesting remains required.

## Verification and limits

Evidence: `D:/MW3DisplayDpiRepair-20261024-r1`.

- Hidden authored-window tests pass: real PMv2 process/window contexts, exact
  client/screen center round trips, last-error preservation, rejection of an
  explicitly unaware thread. The test never moves/clips/captures the real mouse.
  The local monitor is 96 DPI (100%), not the affected laptop's 125% display.
- Compiled and signed native executable checks report `PerMonitorV2=1`.
- Native menu presents 150 Vulkan frames. Scripted input enters Training and
  presents 500 frames with real 3D draws. Runs end at deliberately requested
  frame-budget exceptions, not a normal-quit claim.
- The first Training attempt was interrupted by the old timing harness when
  Blender started and is retained as interrupted. The completed functional run
  permits background rendering while protecting other games. No timing claim.
- Signed game-update verification, installation, activation, validation and
  rollback pass from published runtime 1.0.34. Source snapshot pins 153 files.
- Signed host SHA256:
  `2e8184b7ac866caf1097d7b972428b29e689544772a613e7627e8c83fae3cd97`.

Keep MW3-004 open until physical main-menu control and button clicks pass at
125% on the affected laptop with both devices. Multi-monitor DPI transitions
and all campaign missions are unverified. Native acceptance remains 131/144.

## Retest delivery

[Signed 1.0.35 game update](https://playtest.corecritical.dev/updates/1.0.35/1.0.35-mw3-update.zip)
contains `1.0.35.mw3update`, matching `1.0.35.zip`, and instructions. Extract
together and import through MW3 Updates. Restore Windows scale to 125%, restart
the game, then test the main menu. Publication/readback evidence is retained in
the private directory. Existing signing identity/Access protection remain.
No Git commit is made.
