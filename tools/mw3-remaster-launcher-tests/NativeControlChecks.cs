using System.IO;
using MW3RemasterLauncher.Core;

internal static class NativeControlChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "cc-native-controls-" + Guid.NewGuid().ToString("N"));
        var write = Path.Combine(root, "mw3-re", "profiles", "profile-a");
        var game = Path.Combine(root, "original-game");
        Directory.CreateDirectory(write);
        Directory.CreateDirectory(game);
        try
        {
            var log = new List<string>();
            var settings = new LauncherSettings();
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            Check(log.Any(line => line.Contains("No launcher key layout")), "No-layout launch was not reported.");
            Check(!File.Exists(Path.Combine(root, "controls", "mw3", "profiles.json")),
                "Reading launch controls seeded or changed the user's controls library.");

            var originalMap = "hex:" + string.Join(',', Enumerable.Repeat("00", 167 * sizeof(uint)));
            var existing = "Windows Registry Editor Version 5.00\r\n\r\n" +
                "[HKEY_CURRENT_USER\\SOFTWARE\\MicroProse\\MechWarrior 3\\1.0]\r\n" +
                "\"InGameVMode\"=dword:0000000b\r\n" +
                "\"ActiveCtlCfg\"=hex:4f,6c,64,00\r\n" +
                "\"DefaultCmdMap\"=" + originalMap + "\r\n";
            var settingsPath = Path.Combine(write, "settings.reg");
            File.WriteAllText(settingsPath, existing);
            File.WriteAllText(Path.Combine(write, "Old"), "( KEYS () AXES ((Throttle joystick(Z) slope(-0.5) intercept(0.5) deadzone(0.05))) )");
            var store = new ControlProfiles(root);
            var profile = Mw3DefaultControls.Create();
            profile.Bindings["CMD_TRIGGER1"].Primary = 0x2c;
            var doc = new ControlDocument { Profiles = [profile], ActiveId = profile.Id };
            store.Save(doc);
            log.Clear();
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var applied = File.ReadAllText(settingsPath);
            Check(applied.Contains("\"InGameVMode\"=dword:0000000b"), "Native controls changed another registry setting.");
            Check(!applied.Replace("\r\n", "").Contains('\n'), "Rewriting settings.reg changed its CRLF line endings.");
            Check(applied.Contains("\"ActiveCtlCfg\"=hex:") && applied.Contains("\"DefaultCmdMap\"=hex:"),
                "Native control registry values were not written.");
            var keyFiles = Directory.GetFiles(Path.Combine(write, "keys"), "CC-*.zrd");
            Check(keyFiles.Length == 1 && File.ReadAllText(keyFiles[0]).Contains("CMD_TRIGGER1 keya(0x2c)"),
                "The selected key map did not reach the per-profile ZRD file.");
            Check(File.ReadAllText(keyFiles[0]).Contains("AXES ((Throttle joystick(Z)"),
                "Applying key bindings discarded the runtime profile's original axis settings.");

            File.WriteAllText(settingsPath, applied.Replace("dword:0000000b", "dword:00000007"));
            doc.ActiveId = null;
            store.Save(doc);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var restored = File.ReadAllText(settingsPath);
            Check(restored.Contains("\"ActiveCtlCfg\"=hex:4f,6c,64,00") &&
                restored.Contains("\"DefaultCmdMap\"=" + originalMap),
                "Using game controls did not restore the runtime profile's original control values.");
            Check(restored.Contains("00000007"), "Restoring controls discarded another runtime setting change.");

            // A later in-game edit of both saved controls values becomes the
            // next restore baseline, even while the launcher layout is active.
            doc.ActiveId = profile.Id;
            store.Save(doc);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var launcherAppliedAgain = File.ReadAllText(settingsPath);
            var playerMap = "\"DefaultCmdMap\"=hex:" + string.Join(',', Enumerable.Repeat("fe", 167 * sizeof(uint)));
            var playerConfig = "\"ActiveCtlCfg\"=hex:50,6c,61,79,65,72,00";
            var editedInGame = string.Join("\r\n", launcherAppliedAgain.Split("\r\n")
                .Where(row => !row.StartsWith("\"DefaultCmdMap\"=", StringComparison.Ordinal) &&
                    !row.StartsWith("\"ActiveCtlCfg\"=", StringComparison.Ordinal))) + "\r\n" + playerMap + "\r\n" + playerConfig + "\r\n";
            File.WriteAllText(settingsPath, editedInGame);
            doc.ActiveId = null;
            store.Save(doc);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var latestRestore = File.ReadAllText(settingsPath);
            Check(latestRestore.Contains(playerMap) && latestRestore.Contains(playerConfig),
                "Restoring game controls discarded the player's latest in-game controls.");
            Check(log.Any(line => line.Contains("preserved the latest in-game controls")),
                "An in-game control edit was not reported when updating the restore baseline.");

            // An in-game edit of only the key map must not replace the other value's baseline with the
            // launcher's applied preset path.
            doc.ActiveId = profile.Id;
            store.Save(doc);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var appliedThirdTime = File.ReadAllText(settingsPath);
            var playerMapOnly = "\"DefaultCmdMap\"=hex:" + string.Join(',', Enumerable.Repeat("fd", 167 * sizeof(uint)));
            var mapOnlyEdit = string.Join("\r\n", appliedThirdTime.Split("\r\n")
                .Where(row => !row.StartsWith("\"DefaultCmdMap\"=", StringComparison.Ordinal))) + "\r\n" + playerMapOnly + "\r\n";
            File.WriteAllText(settingsPath, mapOnlyEdit);
            doc.ActiveId = null;
            store.Save(doc);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var singleEditRestore = File.ReadAllText(settingsPath);
            Check(singleEditRestore.Contains(playerMapOnly) && singleEditRestore.Contains(playerConfig),
                "An in-game edit of one control value replaced the other value's restore baseline.");

            settings.DirectInputJoystickProductName = "Test Flight Stick";
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            Check(File.ReadAllText(Path.Combine(write, "mw3.cfg")).Contains("joystick=Test Flight Stick"),
                "The selected joystick product name did not reach the profile mw3.cfg.");
            settings.DirectInputJoystickNone = true;
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            Check(File.ReadAllText(Path.Combine(write, "mw3.cfg")).Contains("joystick=none"),
                "The joystick None choice did not reach the profile mw3.cfg.");
            settings.DirectInputJoystickNone = false;
            settings.DirectInputJoystickProductName = "";
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            Check(!File.ReadAllText(Path.Combine(write, "mw3.cfg")).Contains("joystick="),
                "Automatic joystick selection retained a prior device choice.");

            var controller = new ControllerProfile { Enabled = true, DeviceKey = new string('a', 64) };
            controller.Buttons[0] = 12;
            controller.Axes = [1, 0, 2, 3];
            profile.Bindings["CMD_TRIGGER1"].Joystick = 9;
            store.Save(new ControlDocument { Profiles = [profile], ActiveId = profile.Id });
            new ControllerProfiles(root).Save(controller);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            // Earlier steps leave other launcher presets in the profile; the controller launch wrote the newest.
            var controllerPreset = File.ReadAllText(Directory.GetFiles(Path.Combine(write, "keys"), "CC-*.zrd")
                .OrderByDescending(File.GetLastWriteTimeUtc).First());
            Check(controllerPreset.Contains("joystick(Y)"), "The controller launch did not write its axis preset.");
            Check(controllerPreset.Contains("CMD_JJ_UP keya("), "Controller button action was not projected.");
            Check(controllerPreset.Contains("joybtn(0x1)"), "Controller button slot was not projected.");
            Check(controllerPreset.Contains("Throttle joystick(Y) slope(-0.5) intercept(0.5)"), "Controller throttle affine mapping was incorrect.");
            var triggerLine = controllerPreset.Split('\n').Single(row => row.Contains("(CMD_TRIGGER1 ", StringComparison.Ordinal));
            Check(triggerLine.Contains("joybtn(0x0)", StringComparison.Ordinal),
                "A joystick binding from the saved key profile survived controller projection.");
            Check(log.Any(line => line.Contains("Trigger mappings")), "Unsupported controller mappings were not reported.");
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

        Console.WriteLine("Native controls profile projection and isolation checks passed.");

        var fallbackRoot = Path.Combine(Path.GetTempPath(), "cc-native-controls-fallback-" + Guid.NewGuid().ToString("N"));
        var fallbackWrite = Path.Combine(fallbackRoot, "mw3-re", "profiles", "profile-a");
        Directory.CreateDirectory(fallbackWrite);
        try
        {
            var profile = Mw3DefaultControls.Create();
            new ControlProfiles(fallbackRoot).Save(new ControlDocument { Profiles = [profile], ActiveId = profile.Id });
            NativeControls.PrepareLaunch(fallbackRoot, fallbackWrite, Path.Combine(fallbackRoot, "game"),
                new LauncherSettings(), _ => { });
            var preset = File.ReadAllText(Directory.GetFiles(Path.Combine(fallbackWrite, "keys"), "CC-*.zrd").Single());
            Check(preset.Contains("AXES") && preset.Contains("Throttle joystick(Z) slope(-0.5) intercept(0.5) deadzone(0.05)"),
                "A fresh profile without ActiveCtlCfg did not receive the runtime's standard axes.");

            File.WriteAllText(Path.Combine(fallbackWrite, "keys", "KeysOnly.zrd"), "( KEYS () )");
            File.WriteAllText(Path.Combine(fallbackWrite, "settings.reg"),
                "[HKEY_CURRENT_USER\\SOFTWARE\\MicroProse\\MechWarrior 3\\1.0]\n" +
                "\"ActiveCtlCfg\"=hex:6b,65,79,73,5c,4b,65,79,73,4f,6e,6c,79,2e,7a,72,64,00\n");
            NativeControls.PrepareLaunch(fallbackRoot, fallbackWrite, Path.Combine(fallbackRoot, "game"),
                new LauncherSettings(), _ => { });
            preset = File.ReadAllText(Directory.GetFiles(Path.Combine(fallbackWrite, "keys"), "CC-*.zrd")
                .Select(path => new { Path = path, Text = File.ReadAllText(path) })
                .Single(item => item.Text.Contains("Throttle joystick(Z) slope(-0.5) intercept(0.5)"))
                .Path);
            Check(preset.Contains("AXES") && preset.Contains("Throttle joystick(Z) slope(-0.5) intercept(0.5) deadzone(0.05)"),
                "A resolved KEYS-only profile did not fall back to valid standard axes.");
        }
        finally
        {
            if (Directory.Exists(fallbackRoot)) Directory.Delete(fallbackRoot, true);
        }
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
