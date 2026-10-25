namespace MW3RemasterLauncher.Core;

/// <summary>Authored mappings, adapted to MW3's existing native commands and input format.</summary>
public static class ControlPresets
{
    public const string Mw5Id = "eb2fc23f53dc4665ac573c8b5e9a7001";

    public static ControlProfile Mw5()
    {
        var p = new ControlProfile {
            Id = Mw5Id, Name = "MW5-style (MW3)",
            Description = "MW5-style keyboard layout adapted for MW3. WASD movement; X stop; C/F center torso/legs; R/T target; V camera. " +
                "1–5 select a weapon group; left mouse fires it. MW3 has no sixth group or direct multi-group firing. " +
                "Middle mouse zooms; right mouse or L uses freelook; M uses MASC; Z reverses throttle. " +
                "Numpad 2–9 sets 20–90% throttle; Numpad 0 sets full. Numpad 1, side buttons and wheel are unsupported here. " +
                "Other unmapped actions remain unassigned. Mouse axes and sensitivity stay unchanged.",
            Bindings = ControlProfiles.Actions.ToDictionary(a => a.Name, _ => new ControlBinding())
        };
        // DirectInput scan codes, including extended arrow codes and MW3 modifier masks.
        void Key(string action, int code) => p.Bindings[action].Primary = code;
        Key("CMD_THROTTLE_UP", 0x11); // W
        Key("CMD_THROTTLE_DN", 0x1f); // S
        Key("CMD_TURN_LEFT", 0x1e); // A
        Key("CMD_TURN_RIGHT", 0x20); // D
        Key("CMD_CENTER_TORSO", 0x2e); // C
        Key("CMD_CENTER_LEGS", 0x21); // F
        Key("CMD_THROTTLE1", 0x2d); // X: native command 27 is STOP, not 10%.
        Key("CMD_THROTTLE_REV", 0x2c); // Z: MW3 adaptation.
        int[] numpad = { 0x50, 0x51, 0x4b, 0x4c, 0x4d, 0x47, 0x48, 0x49 };
        for (int n = 2; n <= 9; n++) Key("CMD_THROTTLE" + n, numpad[n - 2]);
        Key("CMD_THROTTLE0", 0x52); // Numpad 0: FULL, not stop.
        for (int n = 1; n <= 5; n++)
        {
            Key("CMD_WEPGRP_" + n, n + 1); // Selection only; native trigger fires.
            Key("CMD_MOVETOWG_" + n, (n + 1) | 0x400); // Shift + number.
        }
        p.Bindings["CMD_TRIGGER1"].Mouse = 1;
        Key("CMD_WEP_PREV", 0xc8); Key("CMD_WEP_NEXT", 0xd0); // Up / down.
        Key("CMD_WEPGRP_PREV", 0xcb); Key("CMD_WEPGRP_NEXT", 0xcd); // Left / right.
        Key("CMD_FIREMODE", 0x0e); // Backspace.
        Key("CMD_JJ_UP", 0x39); // Space.
        Key("CMD_SHUTDOWN", 0x19); Key("CMD_SHUT_OVER", 0x18); // P / O.
        Key("CMD_MASC", 0x32); // M: standalone Alt cannot be encoded as a command key.
        Key("CMD_CYCLE_CAM", 0x2f); // V.
        Key("CMD_FREELOOK", 0x26); p.Bindings["CMD_FREELOOK"].Mouse = 2; // L / right mouse.
        p.Bindings["CMD_RETICULE_ZOOM"].Mouse = 3;
        Key("CMD_TARGET_CURSOR", 0x13); // R.
        Key("CMD_TARGET_NEXT_E", 0x14); Key("CMD_TARGET_PREV_E", 0x414); // T / Shift T.
        Key("CMD_TARGET_NONE", 0x413); // Shift R.
        Key("CMD_TARGET_CLOSE_F", 0x10); // Q: MW3 closest friendly.
        Key("CMD_OBJECTIVES", 0x0f); // Tab.
        Key("CMD_RADAR_MAP_TOGGLE", 0x30); // B.
        Key("CMD_HUD_TOGGLE", 0x125); // Alt K.
        Key("CMD_MCB_COMMAND", 0x3b); // F1: MW3 command menu.
        return p;
    }
}
