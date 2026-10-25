namespace MW3RemasterLauncher.Core;

public static class Mw3DefaultControls
{
    public const string Id = "76034dc23cd648df93ecb6ac14638503";

    // Declarative command/key facts recovered from MW3 US retail 1.2 registration.
    // Includes effective button ownership after later registrations displace earlier ones.
    // Evidence: controls-modernization-investigation-2026-10-18.md and local r2 research.
    public static ControlProfile Create()
    {
        var p = new ControlProfile {
            Id = Id, Name = "MW3 default",
            Description = "Original MW3 1.2 default key and button layout. Arrow keys move; 1 stops; 0 sets full throttle; " +
                "Space or left mouse fires; F1–F5 select weapon groups; J uses jump jets; X changes camera. " +
                "Original F9–F11 assignments overlap remaster capture controls and may need reassignment. " +
                "Mouse axes, sensitivity and the separate controller setup stay unchanged.",
            Bindings = new()
        };
        (string Action, int Primary, int Secondary, int Mouse, int Joystick)[] bindings = {
            ("CMD_THROTTLE_UP", 0xc8, 0x0, 0, 0),
            ("CMD_THROTTLE_DN", 0xd0, 0x0, 0, 0),
            ("CMD_TURN_LEFT", 0xcb, 0x0, 0, 0),
            ("CMD_TURN_RIGHT", 0xcd, 0x0, 0, 0),
            ("CMD_TWIST_LEFT", 0x33, 0x0, 0, 0),
            ("CMD_TWIST_RIGHT", 0x34, 0x0, 0, 0),
            ("CMD_PITCH_UP", 0xc, 0x0, 0, 0),
            ("CMD_PITCH_DN", 0xd, 0x0, 0, 0),
            ("CMD_CENTER_TORSO", 0x435, 0x0, 0, 0),
            ("CMD_CENTER_LEGS", 0x35, 0x0, 0, 8),
            ("CMD_THROTTLE_REV", 0xe, 0x0, 0, 10),
            ("CMD_THROTTLE1", 0x2, 0x0, 0, 0),
            ("CMD_THROTTLE2", 0x3, 0x0, 0, 0),
            ("CMD_THROTTLE3", 0x4, 0x0, 0, 0),
            ("CMD_THROTTLE4", 0x5, 0x0, 0, 0),
            ("CMD_THROTTLE5", 0x6, 0x0, 0, 0),
            ("CMD_THROTTLE6", 0x7, 0x0, 0, 0),
            ("CMD_THROTTLE7", 0x8, 0x0, 0, 0),
            ("CMD_THROTTLE8", 0x9, 0x0, 0, 0),
            ("CMD_THROTTLE9", 0xa, 0x0, 0, 0),
            ("CMD_THROTTLE0", 0xb, 0x0, 0, 0),
            ("CMD_JJ_UP", 0x24, 0x0, 0, 7),
            ("CMD_JJ_FORWARD", 0xc7, 0x0, 0, 0),
            ("CMD_JJ_BACKWARD", 0xcf, 0x0, 0, 0),
            ("CMD_JJ_LEFT", 0xd3, 0x0, 0, 0),
            ("CMD_JJ_RIGHT", 0xd1, 0x0, 0, 0),
            ("CMD_JJ_ROTLEFT", 0xd2, 0x0, 0, 0),
            ("CMD_JJ_ROTRIGHT", 0xc9, 0x0, 0, 0),
            ("CMD_GETUP", 0x22, 0x0, 0, 0),
            ("CMD_CROUCH", 0x2e, 0x0, 0, 0),
            ("CMD_SHUTDOWN", 0x1f, 0x0, 0, 0),
            ("CMD_MASC", 0x2f, 0x0, 0, 0),
            ("CMD_TRIGGER1", 0x39, 0x0, 1, 1),
            ("CMD_WEPGRP_NEXT", 0x1b, 0x0, 0, 4),
            ("CMD_WEPGRP_PREV", 0x1a, 0x0, 0, 0),
            ("CMD_WEP_PREV", 0x21a, 0x0, 0, 0),
            ("CMD_WEP_NEXT", 0x21b, 0x0, 0, 0),
            ("CMD_NEXT_WEAPON", 0x1c, 0x0, 0, 0),
            ("CMD_WEPGRP_1", 0x3b, 0x0, 0, 0),
            ("CMD_WEPGRP_2", 0x3c, 0x0, 0, 0),
            ("CMD_WEPGRP_3", 0x3d, 0x0, 0, 0),
            ("CMD_WEPGRP_4", 0x3e, 0x0, 0, 0),
            ("CMD_WEPGRP_5", 0x3f, 0x0, 0, 0),
            ("CMD_MOVETOWG_1", 0x43b, 0x0, 0, 0),
            ("CMD_MOVETOWG_2", 0x43c, 0x0, 0, 0),
            ("CMD_MOVETOWG_3", 0x43d, 0x0, 0, 0),
            ("CMD_MOVETOWG_4", 0x43e, 0x0, 0, 0),
            ("CMD_MOVETOWG_5", 0x43f, 0x0, 0, 0),
            ("CMD_FIREMODE", 0x2b, 0x0, 0, 5),
            ("CMD_ALPHASTRIKE", 0x9c, 0x0, 0, 6),
            ("CMD_COOLANTFLUSH", 0x21, 0x0, 0, 0),
            ("CMD_SHUT_OVER", 0x18, 0x0, 0, 0),
            ("CMD_JETTISON_AMMO", 0x425, 0x0, 0, 0),
            ("CMD_CYCLE_CAM", 0x2d, 0x0, 0, 0),
            ("CMD_LOOK_LEFT", 0x14b, 0x0, 0, 0),
            ("CMD_LOOK_RIGHT", 0x14d, 0x0, 0, 0),
            ("CMD_LOOK_UP", 0x150, 0x0, 0, 0),
            ("CMD_LOOK_DOWN", 0x148, 0x0, 0, 0),
            ("CMD_LOOK_REAR", 0x153, 0x0, 0, 0),
            ("CMD_LOOK_FRONT", 0x14c, 0x0, 0, 0),
            ("CMD_VMODE_TOGGLE", 0x42f, 0x0, 0, 0),
            ("CMD_TARGET_NEXT_E", 0x12, 0x0, 0, 3),
            ("CMD_TARGET_PREV_E", 0x412, 0x0, 0, 0),
            ("CMD_TARGET_CLOSE_E", 0x212, 0x0, 0, 0),
            ("CMD_TARGET_NEXT_F", 0x11, 0x0, 0, 0),
            ("CMD_TARGET_PREV_F", 0x411, 0x0, 0, 0),
            ("CMD_TARGET_CLOSE_F", 0x211, 0x0, 0, 0),
            ("CMD_TARGET_CURSOR", 0x10, 0x0, 0, 0),
            ("CMD_TARGET_NONE", 0x14, 0x0, 0, 0),
            ("CMD_TARGET_HEAD", 0x48, 0x0, 0, 0),
            ("CMD_TARGET_LARM", 0x47, 0x0, 0, 0),
            ("CMD_TARGET_RARM", 0x49, 0x0, 0, 0),
            ("CMD_TARGET_TORSO", 0x4c, 0x0, 0, 0),
            ("CMD_TARGET_LTORSO", 0x4b, 0x0, 0, 0),
            ("CMD_TARGET_RTORSO", 0x4d, 0x0, 0, 0),
            ("CMD_TARGET_LLEG", 0x4f, 0x0, 0, 0),
            ("CMD_TARGET_RLEG", 0x51, 0x0, 0, 0),
            ("CMD_RETICULE_ZOOM", 0x2c, 0x0, 0, 0),
            ("CMD_ZOOM_LOCK", 0x52, 0x0, 0, 2),
            ("CMD_TOGGLE_TMODE", 0x252, 0x0, 0, 0),
            ("CMD_FREELOOK", 0x26, 0x0, 2, 0),
            ("CMD_DAMAGE_TOGGLE", 0x20, 0x0, 0, 0),
            ("CMD_EDAMAGE_TOGGLE", 0x220, 0x0, 0, 0),
            ("CMD_RADAR_TOGGLE", 0x13, 0x0, 0, 0),
            ("CMD_RADAR_RANGE", 0x113, 0x0, 0, 0),
            ("CMD_RADAR_MAP_TOGGLE", 0x413, 0x0, 0, 0),
            ("CMD_HUD_TOGGLE", 0x23, 0x0, 0, 0),
            ("CMD_AMS_TOGGLE", 0x1e, 0x0, 0, 0),
            ("CMD_DIRECT_ATTACKT", 0x40, 0x0, 0, 0),
            ("CMD_DIRECT_DEFENDT", 0x41, 0x0, 0, 0),
            ("CMD_DIRECT_FOLLOW", 0x42, 0x0, 0, 0),
            ("CMD_DIRECT_PAUSE", 0x43, 0x0, 0, 0),
            ("CMD_DIRECT_REFITT", 0x44, 0x0, 0, 0),
            ("CMD_DIRECT_POCKET", 0x57, 0x0, 0, 0),
            ("CMD_DIRECT_AWAITCMD", 0x457, 0x0, 0, 0),
            ("CMD_DIRECT_AWAITCMDCANCEL", 0x257, 0x0, 0, 0),
            ("CMD_MCB_COMMAND", 0x32, 0x0, 0, 0),
            ("CMD_NAVPT_NEXT", 0x31, 0x0, 0, 0),
            ("CMD_NAVPT_PREV", 0x431, 0x0, 0, 0),
            ("CMD_NAVPT_NEAR", 0x231, 0x0, 0, 0),
            ("CMD_CHAT_TEAM", 0x4a, 0x0, 0, 0),
            ("CMD_CHAT_ALL", 0x37, 0x0, 0, 0),
            ("CMD_OBJECTIVES", 0x58, 0x0, 0, 0),
            ("CMD_MISSION_COMPLETE", 0x210, 0x0, 0, 0),
            ("CMD_MESSAGE_TOGGLE", 0x29, 0x0, 0, 0),
        };
        foreach (var b in bindings)
            p.Bindings.Add(b.Action, new ControlBinding {
                Primary = b.Primary, Secondary = b.Secondary, Mouse = b.Mouse, Joystick = b.Joystick
            });
        return p;
    }
}
