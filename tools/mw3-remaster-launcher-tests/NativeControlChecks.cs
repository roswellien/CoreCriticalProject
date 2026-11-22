using System.Buffers.Binary;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
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
            CheckExtendedBindings(Path.Combine(root, "extended"), game);
            CheckGameOptions(Path.Combine(root, "jump-jets"), game);

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
            Check(controllerPreset.Contains("CMD_JJ_UP keya("), "Controller action row was not retained.");
            Check(controllerPreset.Contains("joybtn(0x0)"), "A controller button could be applied twice through the .zrd map.");
            Check(controllerPreset.Contains("Throttle joystick(Y) slope(-0.5) intercept(0.5) deadzone(0)"), "Controller axis routing or sensitivity was incorrect.");
            var triggerLine = controllerPreset.Split('\n').Single(row => row.Contains("(CMD_TRIGGER1 ", StringComparison.Ordinal));
            Check(triggerLine.Contains("joybtn(0x0)", StringComparison.Ordinal),
                "A joystick binding from the saved key profile survived controller projection.");
            var controllerPath = NativeControls.ControllerProfilePath(write);
            Check(File.Exists(controllerPath) && File.ReadAllText(controllerPath).StartsWith("CC_MW3_CONTROLLER_V1\n"),
                "The full controller profile was not exported into the runtime profile.");
            Check(NativeControls.ControllerArguments(controller, controllerPath).SequenceEqual(new[] { "--cc-controller", controllerPath }),
                "The native controller option or exported file argument was missing.");
            Check(log.Any(line => line.Contains("full saved controller profile")) &&
                !log.Any(line => line.Contains("unsupported", StringComparison.OrdinalIgnoreCase)),
                "The supported controller profile was still reported as unsupported.");
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

    private const string RegistrySection = @"[HKEY_CURRENT_USER\SOFTWARE\MicroProse\MechWarrior 3\1.0]";

    private static void CheckExtendedBindings(string root, string game)
    {
        var write = Path.Combine(root, "write profile");
        Directory.CreateDirectory(write);
        var layoutPath = Path.Combine(root, "controls", "mw3", "profiles.json");
        var store = new ControlProfiles(root);
        var profile = ControlProfileChecks.LegacyMw5(3);
        var doc = new ControlDocument { Profiles = [profile], ActiveId = profile.Id };
        store.Save(doc);
        var legacy = File.ReadAllBytes(layoutPath);
        var log = new List<string>();
        string Prepare() => NativeControls.PrepareLaunch(root, write, game, new LauncherSettings(), log.Add);

        var inputPath = Prepare();
        Check(inputPath == Path.Combine(write, "mw3-input.txt") && File.ReadAllBytes(layoutPath).SequenceEqual(legacy),
            "Native launch did not use the in-memory MW5 migration or it wrote the profile library.");
        int Command(string name) => ControlProfiles.Actions.Single(action => action.Name == name).Command;
        var expected = new (int Command, string Binding)[]
        {
            (Command("CMD_WEP_NEXT"), "MOUSE " + Command("CMD_WEP_NEXT") + " 6"),
            (Command("CMD_WEP_PREV"), "MOUSE " + Command("CMD_WEP_PREV") + " 7"),
            (Command("CMD_JJ_FORWARD"), "COMBO " + Command("CMD_JJ_FORWARD") + " 1 2 K:0x11 K:0x39"),
            (Command("CMD_JJ_BACKWARD"), "COMBO " + Command("CMD_JJ_BACKWARD") + " 1 2 K:0x1f K:0x39"),
            (Command("CMD_JJ_LEFT"), "COMBO " + Command("CMD_JJ_LEFT") + " 1 2 K:0x1e K:0x39"),
            (Command("CMD_JJ_RIGHT"), "COMBO " + Command("CMD_JJ_RIGHT") + " 1 2 K:0x20 K:0x39")
        };
        var wire = "CC_MW3_INPUT_V1\n" + string.Join('\n', expected.OrderBy(row => row.Command).Select(row => row.Binding)) + "\n";
        Check(File.ReadAllText(inputPath) == wire && Prepare() == inputPath && File.ReadAllText(inputPath) == wire &&
            log.Any(line => line.Contains("6 extended") && line.Contains("MW2JJets: enabled")),
            "Native MW5 launch did not emit the stable versioned input map and report its application.");

        profile = Mw3DefaultControls.Create();
        doc = new ControlDocument { Profiles = [profile], ActiveId = profile.Id };
        var actions = new[] { "CMD_TRIGGER1", "CMD_WEP_NEXT", "CMD_WEP_PREV", "CMD_JJ_UP" };
        for (var index = 0; index < actions.Length; index++) profile.Bindings[actions[index]].Mouse = index + 4;
        profile.Bindings["CMD_MCB_COMMAND"].Combos =
        [
            new ControlCombo
            {
                Suppress = false,
                Inputs = [new(ControlComboInputKind.Mouse, 5), new(ControlComboInputKind.Key, 0x9d)]
            },
            new ControlCombo
            {
                Inputs = [new(ControlComboInputKind.Key, 0x39), new(ControlComboInputKind.Key, 0x11)]
            }
        ];
        store.Save(doc);
        Prepare();
        var settingsPath = Path.Combine(write, "settings.reg");
        var map = ReadMap(settingsPath);
        foreach (var action in actions)
            Check(((BinaryPrimitives.ReadUInt32LittleEndian(map.AsSpan(Command(action) * 4)) >> 26) & 3) == 0,
                $"Extended mouse spilled into the legacy {action} command map.");
        Check(((BinaryPrimitives.ReadUInt32LittleEndian(map.AsSpan(Command("CMD_MCB_COMMAND") * 4)) >> 26) & 3) ==
            profile.Bindings["CMD_MCB_COMMAND"].Mouse, "Legacy mouse field changed.");
        wire = File.ReadAllText(inputPath);
        Check(wire.Contains($"COMBO {Command("CMD_MCB_COMMAND")} 0 2 K:0x9d M:5\n") &&
            wire.Contains($"MOUSE {Command("CMD_TRIGGER1")} 4\n") &&
            wire.Contains($"MOUSE {Command("CMD_WEP_NEXT")} 5\n"), "Mixed combo or X-button wire format changed.");
        var combos = profile.Bindings["CMD_MCB_COMMAND"].Combos;
        combos.Reverse();
        foreach (var combo in combos) combo.Inputs.Reverse();
        store.Save(doc);
        Prepare();
        Check(File.ReadAllText(inputPath) == wire, "Reordering bindings changed the exported wire file.");

        profile = Mw3DefaultControls.Create();
        store.Save(new ControlDocument { Profiles = [profile], ActiveId = profile.Id });
        Check(Prepare() == null && !File.Exists(inputPath) && !File.Exists(inputPath + ".previous"),
            "Switching to a legacy-compatible layout retained extended input.");
        store.Save(new ControlDocument { Profiles = [ControlPresets.Mw5()], ActiveId = ControlPresets.Mw5Id });
        Prepare();
        store.Save(new ControlDocument());
        Check(Prepare() == null && !File.Exists(inputPath), "Using game controls retained extended input.");
    }

    private static byte[] ReadMap(string path)
    {
        const string prefix = "\"DefaultCmdMap\"=hex:";
        var lines = File.ReadAllLines(path);
        var first = Array.FindIndex(lines, line => line.StartsWith(prefix, StringComparison.Ordinal));
        var last = first;
        while (lines[last].EndsWith('\\')) last++;
        var hex = lines[first][prefix.Length..] + string.Concat(lines[(first + 1)..(last + 1)]);
        return Convert.FromHexString(new string(hex.Where(Uri.IsHexDigit).ToArray()));
    }

    private static void CheckGameOptions(string root, string game)
    {
        var write = Path.Combine(root, "write");
        Directory.CreateDirectory(write);
        var settingsPath = Path.Combine(write, "settings.reg");
        var restorePath = Path.Combine(write, "launcher-controls.restore.json");
        var store = new ControlProfiles(root);
        var profile = Mw3DefaultControls.Create();
        var doc = new ControlDocument { Profiles = [profile], ActiveId = profile.Id };
        const string anotherSection = "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Unrelated]\r\n\"GameOptions\"=dword:87654321\r\n";
        const string prefix = "Windows Registry Editor Version 5.00\r\n\r\n" + anotherSection +
            RegistrySection + "\r\n\"MusicVolume\"=dword:00000012\r\n";
        string Option(uint value) => FormattableString.Invariant($"\"GameOptions\"=dword:{value:x8}");
        string Live() => File.ReadAllText(settingsPath);
        bool HasOption(uint value) => File.ReadAllLines(settingsPath).Contains(Option(value));
        void Launch(bool? jumpJets, bool active = true)
        {
            profile.Mw2JumpJets = jumpJets;
            doc.ActiveId = active ? profile.Id : null;
            store.Save(doc);
            NativeControls.PrepareLaunch(root, write, game, new LauncherSettings(), _ => { });
        }

        foreach (var oldVersion in new[] { 1, 2 })
        {
            File.WriteAllText(settingsPath, prefix + Option(0x80000049) + "\r\n");
            File.WriteAllText(restorePath, JsonSerializer.Serialize(new
            {
                Version = oldVersion,
                DefaultMap = new[] { "\"DefaultCmdMap\"=hex:01" },
                ActiveConfig = new[] { "\"ActiveCtlCfg\"=hex:02" }
            }));
            Launch(true);
            var state = JsonNode.Parse(File.ReadAllText(restorePath));
            Check(HasOption(0x800000c9) && state["Version"].GetValue<int>() == 3 &&
                state["HasOriginalGameOptions"].GetValue<bool>() &&
                state["OriginalGameOptions"].GetValue<uint>() == 0x80000049 &&
                state["LastAppliedGameOptions"].GetValue<uint>() == 0x800000c9,
                $"Restore v{oldVersion} did not take ownership of the live DWORD correctly.");
            File.WriteAllText(settingsPath, Live().Replace(Option(0x800000c9), Option(0x800001c9)));
            Launch(true);
            Check(HasOption(0x800001c9), "Reapplying jump jets discarded a live unrelated bit.");
            Launch(false);
            Check(HasOption(0x80000149), "Disabling jump jets changed other bits.");
            Launch(null, active: false);
            Check(HasOption(0x80000149) && Live().Contains("\"DefaultCmdMap\"=hex:01") &&
                Live().Contains("\"ActiveCtlCfg\"=hex:02") && !File.Exists(restorePath),
                $"Restore v{oldVersion} lost original controls or the reconciled option.");
        }

        File.WriteAllText(settingsPath, prefix);
        Launch(false);
        Check(HasOption(0x49), "Missing GameOptions did not seed the stock disabled defaults.");
        Launch(true);
        Check(HasOption(0xc9), "Missing GameOptions did not seed the stock enabled defaults.");
        Launch(null, active: false);
        Check(!HasOption(0x49) && !HasOption(0xc9) && Live().Contains(anotherSection) &&
            !Live().Replace("\r\n", "").Contains('\n'), "Absent GameOptions or another section was restored incorrectly.");

        File.WriteAllText(settingsPath, prefix + Option(0x40000049) + "\r\n");
        Launch(true);
        File.WriteAllText(settingsPath, Live().Replace(Option(0x400000c9) + "\r\n", ""));
        Launch(true);
        Check(HasOption(0xc9), "A removed GameOptions value did not reseed from the game's defaults.");
        Launch(null, active: false);
        Check(HasOption(0x40000049), "The launcher mistook its reseeded defaults for edits to the original option.");

        var controllerStore = new ControllerProfiles(root);
        controllerStore.Save(new ControllerProfile { Enabled = true, DeviceKey = new string('a', 64) });
        File.WriteAllText(settingsPath, prefix + Option(0x800000c9) + "\r\n");
        Launch(false);
        Check(HasOption(0x80000049), "Controller-managed launch could not clear the jump-jet bit.");
        File.WriteAllText(settingsPath, Live().Replace(Option(0x80000049), Option(0x80000149)));
        Launch(null);
        var controllerState = JsonNode.Parse(File.ReadAllText(restorePath));
        Check(HasOption(0x800001c9) && !controllerState["HasOriginalGameOptions"].GetValue<bool>(),
            "A null jump-jet override did not restore the original bit while controller controls stayed active.");
        Launch(false);
        Launch(null, active: false);
        Check(HasOption(0x800001c9) && File.Exists(restorePath),
            "Using game keys while retaining a controller profile did not restore GameOptions.");

        controllerStore.Save(new ControllerProfile());
        Launch(null, active: false);
        File.WriteAllText(settingsPath, prefix + Option(0x49) + "\r\n");
        Launch(true);
        // Recreate the durable pre-write record if the process stopped just after settings.reg was replaced.
        var interrupted = JsonNode.Parse(File.ReadAllText(restorePath)).AsObject();
        interrupted["Pending"] = new JsonObject
        {
            ["DefaultMap"] = interrupted["LastAppliedDefaultMap"].DeepClone(),
            ["ActiveConfig"] = interrupted["LastAppliedActiveConfig"].DeepClone(),
            ["WritesGameOptions"] = true,
            ["KeepsGameOptionsOverride"] = true,
            ["GameOptions"] = 0xc9
        };
        interrupted["LastAppliedGameOptions"] = 0x49;
        File.WriteAllText(restorePath, interrupted.ToJsonString());
        Launch(false);
        Launch(null, active: false);
        Check(HasOption(0x49), "Retry mistook an interrupted launcher-applied bit for a player's edit.");

        var invalid = prefix + "\"GameOptions\"=hex:80,00,00,00\r\n";
        File.WriteAllText(settingsPath, invalid);
        try { Launch(true); throw new Exception("A non-DWORD HKCU GameOptions was accepted."); }
        catch (InvalidDataException error) when (error.Message.Contains("GameOptions")) { }
        Check(Live() == invalid && !File.Exists(restorePath), "An invalid DWORD changed control files.");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
