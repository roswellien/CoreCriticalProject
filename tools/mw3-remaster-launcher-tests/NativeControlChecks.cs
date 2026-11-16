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

            const string existing = "Windows Registry Editor Version 5.00\n\n" +
                "[HKEY_CURRENT_USER\\SOFTWARE\\MicroProse\\MechWarrior 3\\1.0]\n" +
                "\"InGameVMode\"=dword:0000000b\n" +
                "\"ActiveCtlCfg\"=hex:4f,6c,64,00\n" +
                "\"DefaultCmdMap\"=hex:01,02,03,04\n";
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
                restored.Contains("\"DefaultCmdMap\"=hex:01,02,03,04"),
                "Using game controls did not restore the runtime profile's original control values.");
            Check(restored.Contains("00000007"), "Restoring controls discarded another runtime setting change.");

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
            new ControllerProfiles(root).Save(controller);
            NativeControls.PrepareLaunch(root, write, game, settings, log.Add);
            var controllerPreset = Directory.GetFiles(Path.Combine(write, "keys"), "CC-*.zrd")
                .Select(File.ReadAllText).Single(text => text.Contains("joystick(Y)"));
            Check(controllerPreset.Contains("CMD_JJ_UP keya(") && controllerPreset.Contains("joybtn(0x1)") &&
                controllerPreset.Contains("Throttle joystick(Y)"),
                "Representable controller button and axis mappings were not projected.");
            Check(log.Any(line => line.Contains("Trigger mappings")), "Unsupported controller mappings were not reported.");
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

        Console.WriteLine("Native controls profile projection and isolation checks passed.");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
