# Optional MW5-style MW3 keyboard layout

The launcher now seeds an editable **MW5-style (MW3)** saved layout. It is
available under MW3 Controls and only becomes active after **Save & use next
launch**. Existing active layouts and edits are preserved. A full layout library
is left intact rather than deleting a user layout to make room.

Reference: this PC's MW5 Mercenaries saved keyboard layout in
`%LOCALAPPDATA%/MW5Mercs/Saved/Config/WindowsNoEditor/GameUserSettings.ini`.
This is an authored adaptation of that configuration, not a claim about all MW5
factory defaults. No original game configuration or generated code is shipped.

Core mappings: W/S throttle, A/D turn legs, X stop, C/F center torso/legs,
V camera, P power, O shutdown override, Space jump jets, R target under cursor,
T/Shift-T next/previous hostile, Shift-R clear target, Q closest friendly,
Tab objectives, B map, Alt-K HUD. Arrow keys select weapons/groups.

MW3-specific adaptations shown in the editor:

- 1–5 select a group and left mouse fires the selected group. These are not
  independent MW5 fire-group commands; MW3 has five groups, not six.
- Middle mouse uses MW3 reticle zoom. Side buttons/wheel are not representable
  in the existing saved mouse-button format.
- Right mouse/L freelook, M MASC, Z reverse. Standalone modifier keys cannot be
  encoded as ordinary command keys by this editor.
- Numpad 2–9 sets 20–90% throttle, Numpad 0 full. Native `CMD_THROTTLE1` is
  **stop**, so X uses it and Numpad 1 remains unassigned rather than pretending
  it sets 10%. Unsupported actions remain unassigned.
- Shift 1–5 moves the selected weapon to a group; F1 opens MW3's command menu.

Mouse axes, sensitivity and original gameplay remain governed by the existing
native controls path. No native recompile or input behavior adapter is included.
Execution boundary advanced: launcher saved-layout selection through the existing
native MW3 preset deployment path. Native acceptance credit remains 131/144.

Validation: Release controls-only checks cover all 105 actions, no duplicate
keys/reserved capture keys, stop/full throttle semantics, group/fire mappings,
persisted inactive seeding, preservation of user edits and full libraries,
axis retention, registry isolation and restoration. Release launcher compiles.
Native in-mission feel has not been tested for this new layout.

DEV launcher is version 1.0.29-preview. Repository shortcuts already target its
Release build output; the public installer and R2 releases are not changed here.

## MW3 default saved option

The same development build also seeds **MW3 default**, independently of the
MW5-style option. Its declarative 105-command key/button table follows the
recovered US retail 1.2 effective registration defaults, including original
mouse and legacy joystick button ownership. It does not copy the user's current
custom bindings or change the active selection. User edits to either saved
option survive reloads. Existing libraries gain the option when space permits;
full libraries remain intact.

Original F9–F11 assignments overlap remaster capture/replay controls; the layout
description calls this out rather than silently changing those default keys.
The separate controller setup and mouse axes are unchanged. Release controls
checks pass for both presets, upgrading an existing library, preserving edited
defaults and active selection, and the existing launch/restoration checks.
No game launch or native rebuild was performed for this addition, and no
acceptance credit changes.
