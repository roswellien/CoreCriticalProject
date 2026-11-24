using System.Buffers.Binary;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Windows.Input;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class ControlProfileChecks
{
    public static void Run()
    {
        var root = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "CoreCriticalControls-" + Guid.NewGuid().ToString("N"));
        System.IO.Directory.CreateDirectory(root);
        const string key = @"hkcu\software\microprose\mechwarrior 3\1.0";
        var map = new byte[167 * 4];
        foreach (var a in ControlProfiles.Actions)
            BinaryPrimitives.WriteUInt32LittleEndian(map.AsSpan(a.Command * 4), (uint)(0x1e | (0x21e << 11) | (5 << 22) | (2 << 26)));
        var text = "K " + key + "\nV " + key + "\tdefaultcmdmap\t3\t" + Convert.ToHexString(map) + "\nV " + key + "\tactivectlcfg\t3\t" +
            Convert.ToHexString(Encoding.ASCII.GetBytes("Original\0")) + "\nV authored\tunrelated\t4\t12345678\n";
        try
        {
            Check(ControlProfiles.Actions.Count == 105 && ControlProfiles.Actions.Select(a => a.Command).Distinct().Count() == 105, "Action metadata incomplete");
            var letter = ControlKeys.Capture(System.Windows.Input.Key.A, System.Windows.Input.ModifierKeys.None);
            Check(ControlKeys.Capture(System.Windows.Input.Key.A, System.Windows.Input.ModifierKeys.Shift) == (letter | 0x400), "Shift modifier encoding changed");
            Check(ControlKeys.Capture(System.Windows.Input.Key.A, System.Windows.Input.ModifierKeys.Alt) == (letter | 0x100), "Alt modifier encoding changed");
            Check(ControlKeys.Capture(System.Windows.Input.Key.Return, System.Windows.Input.ModifierKeys.Control, 0x9c) == 0x29c, "Numpad Enter lost its physical identity");
            var arrow = ControlKeys.Capture(System.Windows.Input.Key.Up, System.Windows.Input.ModifierKeys.Control);
            Check(arrow == 0x2c8, $"Extended arrow or Ctrl encoding changed: {arrow:x}");
            CheckPhysicalCapture();
            var store = new ControlProfiles(root);
            var doc = store.Load();
            Check(doc.ActiveId == null && doc.Profiles.Count == 2, "Optional layouts missing or auto-enabled");
            var mw5 = doc.Profiles.Single(p => p.Id == ControlPresets.Mw5Id);
            var defaults = doc.Profiles.Single(p => p.Id == Mw3DefaultControls.Id);
            Check(defaults.Bindings.Count == 105 && ControlProfiles.Conflicts(defaults).Count == 0, "MW3 defaults incomplete or conflicting");
            Check(defaults.Bindings["CMD_THROTTLE_UP"].Primary == 0xc8 && defaults.Bindings["CMD_THROTTLE1"].Primary == 2 &&
                defaults.Bindings["CMD_THROTTLE0"].Primary == 11 && defaults.Bindings["CMD_TRIGGER1"].Primary == 0x39 &&
                defaults.Bindings["CMD_TRIGGER1"].Mouse == 1 && defaults.Bindings["CMD_TRIGGER1"].Joystick == 1 &&
                defaults.Bindings["CMD_CENTER_TORSO"].Primary == 0x435, "Original MW3 defaults changed");
            Check(mw5.Bindings.Count == 105 && ControlProfiles.Conflicts(mw5).Count == 0, "MW5 layout incomplete or conflicting");
            Check(mw5.Bindings["CMD_FREELOOK"].Primary == 0 && mw5.Bindings["CMD_FREELOOK"].Mouse == 2 &&
                !mw5.Bindings.Values.Any(b => b.Primary == 0x26 || b.Secondary == 0x26),
                "MW5-style freelook conflicts with the default L headlight toggle");
            Check(mw5.Bindings["CMD_TOGGLE_TMODE"].Primary == 0x252 &&
                ControlProfiles.Preset(mw5).Contains("CMD_TOGGLE_TMODE keya(0x252)"), "MW5 torso mode reset missing");
            Check(mw5.Bindings["CMD_THROTTLE1"].Primary == 0x2d && mw5.Bindings["CMD_THROTTLE0"].Primary == 0x52,
                "MW5 stop/full throttle semantics reversed");
            Check(mw5.Bindings["CMD_WEPGRP_1"].Primary == 2 && mw5.Bindings["CMD_TRIGGER1"].Mouse == 1,
                "MW3 weapon group selection/fire adaptation changed");
            Check(mw5.Bindings.Values.All(b => b.Mouse is >= 0 and <= 7 && b.Joystick == 0 &&
                new[] { b.Primary, b.Secondary }.All(k => (k & 255) is not (0x43 or 0x44 or 0x57 or 0x58))), "Unsupported or reserved input in MW5 layout");
            Check(store.Load().Profiles.Count == 2 && System.IO.File.Exists(System.IO.Path.Combine(root, "controls/mw3/profiles.json")), "Built-in layouts not persisted or duplicated");
            Check(mw5.Bindings["CMD_ZOOM_LOCK"].Mouse == 3 &&
                mw5.Bindings["CMD_RETICULE_ZOOM"].Mouse == 0 && mw5.Bindings["CMD_WEP_NEXT"].Mouse == 6 &&
                mw5.Bindings["CMD_WEP_PREV"].Mouse == 7 && mw5.Mw2JumpJets == true,
                "MW5-style mouse and MW2 jump-jet defaults changed.");
            foreach (var (name, scan) in new[]
            {
                ("CMD_JJ_FORWARD", 0x11), ("CMD_JJ_BACKWARD", 0x1f),
                ("CMD_JJ_LEFT", 0x1e), ("CMD_JJ_RIGHT", 0x20)
            })
            {
                var combo = mw5.Bindings[name].Combos.Single();
                Check(combo.Suppress && combo.Inputs.SequenceEqual(new[] { KeyInput(scan), KeyInput(0x39) }),
                    $"MW5-style {name} combo changed.");
            }
            Check(mw5.Bindings.Values.Sum(binding => binding.Combos?.Count ?? 0) == 4,
                "Unexpected MW5-style directional combos.");
            CheckLegacyMigration(Path.Combine(root, "migration"));
            CheckComboValidation();
            CheckProfileBudget(Path.Combine(root, "full"));
            mw5.Name = "Edited MW5"; mw5.Bindings["CMD_THROTTLE_UP"].Primary = 0;
            mw5.Bindings["CMD_TOGGLE_TMODE"].Primary = 0;
            store.Save(doc);
            Check(store.Load().Profiles.Single(p => p.Id == ControlPresets.Mw5Id).Name == "Edited MW5" && store.Load().Profiles.Single(p => p.Id == ControlPresets.Mw5Id).Bindings["CMD_THROTTLE_UP"].Primary == 0 &&
                store.Load().Profiles.Single(p => p.Id == ControlPresets.Mw5Id).Bindings["CMD_TOGGLE_TMODE"].Primary == 0,
                "Built-in seeding overwrote user edits");
            defaults.Name = "Edited MW3"; defaults.Bindings["CMD_TRIGGER1"].Primary = 0;
            doc.ActiveId = defaults.Id; store.Save(doc);
            Check(store.Load().ActiveId == defaults.Id && store.Load().Profiles.Single(p => p.Id == defaults.Id).Bindings["CMD_TRIGGER1"].Primary == 0,
                "Default preset edits or active selection overwritten");
            // Upgrade a library created before the MW3 default option existed.
            doc.Profiles.Remove(defaults); doc.ActiveId = mw5.Id; store.Save(doc);
            doc = store.Load();
            Check(doc.Profiles.Count == 2 && doc.ActiveId == mw5.Id && doc.Profiles.Single(p => p.Id == Mw3DefaultControls.Id).Name == "MW3 default",
                "Existing library did not gain the optional MW3 default safely");
            var p = ControlProfiles.ImportRegistry(text);
            Check(p.Bindings.Count == 105 && p.Bindings.Values.All(b => b.Primary == 0x1e && b.Secondary == 0x21e && b.Mouse == 2 && b.Joystick == 5), "Button packing changed");
            Check(ControlProfiles.Conflicts(p).Count == 3, "Shared keys and mouse inputs not detected");
            var copy = ControlProfiles.Clone(p, "Independent");
            copy.Bindings["CMD_THROTTLE_UP"].Primary = 0;
            Check(p.Bindings["CMD_THROTTLE_UP"].Primary == 0x1e && copy.Id != p.Id, "Layouts share mutable bindings");
            doc.Profiles.Add(copy); doc.ActiveId = copy.Id; store.Save(doc);
            Check(new ControlProfiles(root).Load().ActiveId == copy.Id, "Active profile did not survive restart");
            var preset = ControlProfiles.Preset(copy);
            Check(preset.Contains("CMD_THROTTLE_UP keya(0x0)") && !preset.Contains("AXES"), "Cleared keys or axes preservation changed");
            const string template = "( KEYS ((OLD keya(1))) AXES (X(sensitivity(0.75))) ) // KEYS (ignored)\n";
            var composed = ControlProfiles.Preset(copy, template);
            Check(composed.Contains("AXES (X(sensitivity(0.75)))") && !composed.Contains("OLD keya"), "Custom axes were not retained");
            Invalid(() => ControlProfiles.Preset(copy, "(KEYS( broken"));
            Invalid(() => ControlProfiles.Preset(copy, "(KEYS())(KEYS())"));
            Invalid(() => ControlProfiles.ImportRegistry(text + text));
            Invalid(() => ControlProfiles.ImportRegistry(""));
            var bad = ControlProfiles.Clone(copy, "Bad"); bad.Bindings.Remove("CMD_THROTTLE_UP");
            Invalid(() => ControlProfiles.Validate(new() { Profiles = new() { bad } }));
            bad = ControlProfiles.Clone(copy, "Bad"); bad.Bindings["CMD_THROTTLE_UP"].Primary = 0x800;
            Invalid(() => ControlProfiles.Validate(new() { Profiles = new() { bad } }));
            Invalid(() => ControlProfiles.Validate(new() { GameId = "mw3pm" }));
            Invalid(() => ControlProfiles.Validate(new() { ActiveId = "missing" }));
            var seed = System.IO.Path.Combine(root, "seed.txt");
            System.IO.File.WriteAllText(seed, text);
            JsonObject Profile() => new() { ["native"] = new JsonObject { ["runtime_environment"] = new JsonObject { ["MW34_REG_OVERLAY"] = seed } } };
            var game = System.IO.Path.Combine(root, "game"); System.IO.Directory.CreateDirectory(game);
            System.IO.File.WriteAllText(System.IO.Path.Combine(game, "Original"), template);
            var profile = Profile(); store.PrepareLaunch(profile, root, game);
            var registry = profile["native"]!["runtime_environment"]!["MW34_REG_OVERLAY"]!.GetValue<string>();
            Check(registry != seed && System.IO.File.ReadAllText(seed) == text, "Published registry was changed");
            Check(System.IO.File.ReadAllText(registry).Contains("V authored\tunrelated\t4\t12345678"), "Unrelated settings lost");
            Check(System.IO.Directory.GetFiles(System.IO.Path.Combine(game, "keys"), "*.zrd").Length == 1, "Preset not deployed");
            var importedOriginal = store.ImportCurrent(new[] { registry });
            Check(importedOriginal.Bindings["CMD_THROTTLE_UP"].Primary == 0x1e, "Copy current lost original controls backup");
            // Simulate native save: it persists the selected profile's map and another preference.
            var changed = (byte[])map.Clone(); BinaryPrimitives.WriteUInt32LittleEndian(changed.AsSpan(0x18 * 4), 0);
            System.IO.File.WriteAllText(registry, System.IO.File.ReadAllText(registry).Replace(Convert.ToHexString(map), Convert.ToHexString(changed)) + "V authored\tnew-value\t4\t01000000\n");
            Check(store.ImportCurrent(new[] { registry }).Bindings["CMD_THROTTLE_UP"].Primary == 0, "Copy current ignored in-game edits");
            Check(store.ImportOriginal(new[] { registry }).Bindings["CMD_THROTTLE_UP"].Primary == 0x1e, "Reset original imported the active custom layout");
            doc.ActiveId = null; store.Save(doc);
            store.PrepareLaunch(Profile(), root, game);
            var restored = System.IO.File.ReadAllText(registry);
            Check(restored.Contains(Convert.ToHexString(map)) && restored.Contains("\tnew-value\t"), "Original controls restoration lost live preferences");
            Check(restored.Contains("\tactivectlcfg\t3\t" + Convert.ToHexString(Encoding.ASCII.GetBytes("Original\0"))), "Original control selection lost");
            Check(System.IO.File.ReadAllText(System.IO.Path.Combine(game, "Original")) == template, "Original preset was changed");
            var fresh = Profile(); store.PrepareLaunch(fresh, root, game);
            Check(fresh["native"]!["runtime_environment"]!["MW34_REG_OVERLAY"]!.ToString() == seed, "Inactive profiles changed launch");
            System.IO.File.Delete(System.IO.Path.Combine(game, "Original"));
            doc.ActiveId = copy.Id; store.Save(doc);
            Invalid(() => store.PrepareLaunch(Profile(), root, game));
            Check(System.IO.File.ReadAllText(registry) == restored, "Failed apply changed original settings");
            foreach (var mouse in new[] { 4, 5, 6, 7, 0 })
            {
                var extended = Mw3DefaultControls.Create();
                extended.Bindings["CMD_TRIGGER1"].Mouse = mouse;
                if (mouse == 0) extended.Bindings["CMD_TRIGGER1"].Combos = [Chord(KeyInput(0x39), MouseInput(1))];
                store.Save(new ControlDocument { Profiles = [extended], ActiveId = extended.Id });
                var row = ControlProfiles.Preset(extended).Split('\n').Single(line => line.Contains("(CMD_TRIGGER1 "));
                Check(row.Contains("mousebtn(0x0)"), "Extended mouse escaped into a legacy ZRD field.");
                var launch = Profile();
                var beforeLaunch = launch.ToJsonString();
                var deployed = Directory.GetFiles(Path.Combine(game, "keys"), "*.zrd");
                Invalid(() => store.PrepareLaunch(launch, root, game));
                Check(launch.ToJsonString() == beforeLaunch && File.ReadAllText(registry) == restored &&
                    Directory.GetFiles(Path.Combine(game, "keys"), "*.zrd").SequenceEqual(deployed),
                    "D7VK extended binding rejection mutated control artifacts.");
            }
            var path = System.IO.Path.Combine(root, "controls/mw3/profiles.json");
            System.IO.File.WriteAllText(path, "{bad-json");
            try { store.Load(); throw new Exception("Corrupt profiles silently reset"); } catch (System.Text.Json.JsonException) { }
            Check(System.IO.File.ReadAllText(path) == "{bad-json", "Corrupt profiles overwritten");
        }
        finally { System.IO.Directory.Delete(root, true); }
        Console.WriteLine("Controls profile isolation, import, clearing, restart and original-settings restoration checks passed.");
    }
    internal static ControlProfile LegacyMw5(int version)
    {
        const string introduction = "MW5-style keyboard layout adapted for MW3. WASD movement; X stop; C/F center torso/legs; R/T target; V camera. " +
            "1–5 select a weapon group; left mouse fires it. MW3 has no sixth group or direct multi-group firing. ";
        const string tail = "Numpad 2–9 sets 20–90% throttle; Numpad 0 sets full. Numpad 1, side buttons and wheel are unsupported here. " +
            "Other unmapped actions remain unassigned. Mouse axes and sensitivity stay unchanged.";
        var profile = new ControlProfile
        {
            Id = "eb2fc23f53dc4665ac573c8b5e9a7001",
            Name = "MW5-style (MW3)",
            Description = introduction + (version switch
            {
                1 => "Middle mouse zooms; right mouse or L uses freelook; M uses MASC; Z reverses throttle. ",
                2 => "Middle mouse zooms; right mouse or L uses freelook; M uses MASC; Z reverses throttle. Ctrl + numpad 0 toggles torso mode. ",
                3 => "Middle mouse zooms; right mouse uses freelook; L toggles headlights; M uses MASC; Z reverses throttle. Ctrl + numpad 0 toggles torso mode. ",
                _ => throw new ArgumentOutOfRangeException(nameof(version))
            }) + tail,
            Bindings = ControlProfiles.Actions.ToDictionary(action => action.Name, _ => new ControlBinding())
        };
        (string Action, int Scan)[] keys =
        [
            ("THROTTLE_UP", 0x11), ("THROTTLE_DN", 0x1f), ("TURN_LEFT", 0x1e), ("TURN_RIGHT", 0x20),
            ("CENTER_TORSO", 0x2e), ("CENTER_LEGS", 0x21), ("THROTTLE1", 0x2d), ("THROTTLE_REV", 0x2c),
            ("THROTTLE2", 0x50), ("THROTTLE3", 0x51), ("THROTTLE4", 0x4b), ("THROTTLE5", 0x4c),
            ("THROTTLE6", 0x4d), ("THROTTLE7", 0x47), ("THROTTLE8", 0x48), ("THROTTLE9", 0x49),
            ("THROTTLE0", 0x52),
            ("WEPGRP_1", 2), ("WEPGRP_2", 3), ("WEPGRP_3", 4), ("WEPGRP_4", 5), ("WEPGRP_5", 6),
            ("MOVETOWG_1", 0x402), ("MOVETOWG_2", 0x403), ("MOVETOWG_3", 0x404), ("MOVETOWG_4", 0x405), ("MOVETOWG_5", 0x406),
            ("WEP_PREV", 0xc8), ("WEP_NEXT", 0xd0), ("WEPGRP_PREV", 0xcb), ("WEPGRP_NEXT", 0xcd),
            ("FIREMODE", 0x0e), ("JJ_UP", 0x39), ("SHUTDOWN", 0x19), ("SHUT_OVER", 0x18),
            ("MASC", 0x32), ("CYCLE_CAM", 0x2f), ("TARGET_CURSOR", 0x13), ("TARGET_NEXT_E", 0x14),
            ("TARGET_PREV_E", 0x414), ("TARGET_NONE", 0x413), ("TARGET_CLOSE_F", 0x10),
            ("OBJECTIVES", 0x0f), ("RADAR_MAP_TOGGLE", 0x30), ("HUD_TOGGLE", 0x125), ("MCB_COMMAND", 0x3b)
        ];
        foreach (var (action, scan) in keys) profile.Bindings["CMD_" + action].Primary = scan;
        profile.Bindings["CMD_FREELOOK"].Primary = version < 3 ? 0x26 : 0;
        profile.Bindings["CMD_TOGGLE_TMODE"].Primary = version > 1 ? 0x252 : 0;
        profile.Bindings["CMD_TRIGGER1"].Mouse = 1;
        profile.Bindings["CMD_FREELOOK"].Mouse = 2;
        profile.Bindings["CMD_RETICULE_ZOOM"].Mouse = 3;
        return profile;
    }

    private static void CheckLegacyMigration(string root)
    {
        var store = new ControlProfiles(root);
        var path = Path.Combine(root, "controls", "mw3", "profiles.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        foreach (var version in new[] { 1, 2, 3 })
        {
            var legacy = LegacyMw5(version);
            legacy.Bindings["CMD_JJ_LEFT"].Combos = [];
            var defaults = Mw3DefaultControls.Create();
            var doc = new ControlDocument { Profiles = [legacy, defaults], ActiveId = legacy.Id };
            // Use a historical JSON shape, including an explicit empty list and a null list.
            File.WriteAllText(path, JsonSerializer.Serialize(doc));
            var migrated = store.Load();
            Check(migrated.ActiveId == legacy.Id &&
                JsonSerializer.Serialize(migrated.Profiles[0]) == JsonSerializer.Serialize(ControlPresets.Mw5()) &&
                JsonSerializer.Serialize(migrated.Profiles[1]) == JsonSerializer.Serialize(defaults),
                $"Legacy MW5 v{version} migration changed selection or another layout.");
            var once = File.ReadAllBytes(path);
            store.Load();
            Check(File.ReadAllBytes(path).SequenceEqual(once), $"Legacy MW5 v{version} migration repeated.");

            foreach (var change in new Action<ControlProfile>[]
            {
                profile => profile.Name += " edited",
                profile => profile.Description += " ",
                profile => profile.Bindings["CMD_FREELOOK"].Primary = 0x20,
                profile => profile.Bindings["CMD_RETICULE_ZOOM"].Mouse = 0,
                profile => profile.Bindings["CMD_JJ_LEFT"].Combos = [Chord(KeyInput(0x1e), KeyInput(0x39))],
                profile => profile.Mw2JumpJets = false
            })
            {
                var edited = LegacyMw5(version);
                change(edited);
                doc.Profiles[0] = edited;
                store.Save(doc);
                var before = File.ReadAllBytes(path);
                Check(JsonSerializer.Serialize(store.Load().Profiles[0]) == JsonSerializer.Serialize(edited) &&
                    File.ReadAllBytes(path).SequenceEqual(before), "MW5 migration overwrote an authored change.");
            }
        }
    }

    private static void CheckPhysicalCapture()
    {
        foreach (var (key, scan, label) in new[]
        {
            (Key.LeftShift, 0x2a, "LShift"), (Key.RightShift, 0x36, "RShift"),
            (Key.LeftCtrl, 0x1d, "LCtrl"), (Key.RightCtrl, 0x9d, "RCtrl"),
            (Key.LeftAlt, 0x38, "LAlt"), (Key.RightAlt, 0xb8, "RAlt")
        })
            Check(ControlKeys.CapturePhysical(key) == scan && ControlKeys.Label(scan) == label,
                $"Physical modifier identity changed for {key}.");
        Check(ControlKeys.CapturePhysical(Key.Return) == 0x1c &&
            ControlKeys.CapturePhysical(Key.Return, 0x9c) == 0x9c &&
            ControlKeys.CapturePhysical(Key.Up) == 0xc8 && ControlKeys.CapturePhysical(Key.F12) == 0x58,
            "Physical DIK capture changed for Enter, navigation, or F12.");
        Check(Enumerable.Range(0, 8).Select(ControlKeys.MouseLabel).SequenceEqual(
            new[] { "Unassigned", "Left", "Right", "Middle", "Mouse 4", "Mouse 5", "Wheel Up", "Wheel Down" }),
            "Mouse labels changed.");
    }

    private static void CheckComboValidation()
    {
        var profile = ControlPresets.Mw5();
        var left = profile.Bindings["CMD_JJ_LEFT"];
        var forward = profile.Bindings["CMD_JJ_FORWARD"];
        var manual = profile.Bindings["CMD_MCB_COMMAND"];
        var doc = new ControlDocument { Profiles = [profile] };
        manual.Combos = [Chord(MouseInput(1), KeyInput(0x39)), Chord(KeyInput(0x58), KeyInput(0x39))];
        ControlProfiles.Validate(doc);
        Check(ControlProfiles.Conflicts(profile).Count == 0,
            "Distinct overlapping combos or overlapping single inputs conflict.");
        var copy = ControlProfiles.Clone(profile, "Independent combos");
        var copiedCombo = copy.Bindings["CMD_JJ_LEFT"].Combos[0];
        var sourceCombo = left.Combos[0];
        Check(copy.Mw2JumpJets == true && !ReferenceEquals(copiedCombo, sourceCombo) &&
            !ReferenceEquals(copiedCombo.Inputs[0], sourceCombo.Inputs[0]), "Combo clone shared objects.");
        copiedCombo.Inputs.Clear();
        copy.Bindings["CMD_JJ_LEFT"].Combos.Clear();
        Check(left.Combos.Count == 1 && sourceCombo.Inputs.Count == 2, "Combo clone shared lists.");

        var reversed = Chord(forward.Combos[0].Inputs.AsEnumerable().Reverse().ToArray());
        reversed.Suppress = false;
        manual.Combos = [reversed];
        Check(ControlProfiles.Conflicts(profile).Count == 1, "Reordered combo conflict was hidden.");
        Invalid(() => ControlProfiles.Validate(doc));
        manual.Combos = null;
        forward.Combos.Add(reversed);
        Check(ControlProfiles.Conflicts(profile).Count == 1, "Duplicate combo within one action was hidden.");
        Invalid(() => ControlProfiles.Validate(doc));
        forward.Combos.RemoveAt(1);
        foreach (var mouse in Enumerable.Range(1, 7))
        {
            var fixture = Mw3DefaultControls.Create();
            fixture.Bindings["CMD_TRIGGER1"].Mouse = mouse;
            fixture.Bindings["CMD_FIREMODE"].Mouse = mouse;
            Check(ControlProfiles.Conflicts(fixture).Any(conflict =>
                conflict.StartsWith(ControlKeys.MouseLabel(mouse) + ": ", StringComparison.Ordinal)),
                "A duplicate mouse binding was missed.");
            var mouseDoc = new ControlDocument { Profiles = [fixture] };
            if (mouse <= 3) ControlProfiles.Validate(mouseDoc);
            else Invalid(() => ControlProfiles.Validate(mouseDoc));
        }

        foreach (var inputs in new[]
        {
            new[] { KeyInput(0x39) },
            new[] { KeyInput(1), KeyInput(2), KeyInput(3), KeyInput(4) },
            new[] { KeyInput(0x39), KeyInput(0x39) },
            new[] { MouseInput(6), MouseInput(7) },
            new[] { KeyInput(0), MouseInput(1) },
            new[] { KeyInput(0x439), MouseInput(1) },
            new[] { KeyInput(0x43), MouseInput(1) },
            new[] { KeyInput(0x44), MouseInput(1) },
            new[] { KeyInput(0x57), MouseInput(1) },
            new[] { KeyInput(1), MouseInput(0) },
            new[] { KeyInput(1), MouseInput(8) },
            new[] { KeyInput(1), new ControlComboInput((ControlComboInputKind)7, 1) }
        })
        {
            manual.Combos = [Chord(inputs)];
            Invalid(() => ControlProfiles.Validate(doc));
        }
        manual.Combos = Enumerable.Range(0x60, 9).Select(scan => Chord(KeyInput(scan), KeyInput(0x39))).ToList();
        Invalid(() => ControlProfiles.Validate(doc));
        manual.Combos = null;
        manual.Mouse = 8;
        Invalid(() => ControlProfiles.Validate(doc));
    }

    private static void CheckProfileBudget(string root)
    {
        var store = new ControlProfiles(root);
        var path = Path.Combine(root, "controls", "mw3", "profiles.json");
        var profile = Mw3DefaultControls.Create();
        for (var actionIndex = 0; actionIndex < 8; actionIndex++)
            profile.Bindings[ControlProfiles.Actions[actionIndex].Name].Combos = Enumerable.Range(0x60 + actionIndex * 8, 8)
                .Select(scan => Chord(KeyInput(scan), KeyInput(0x39), MouseInput(1))).ToList();
        profile.Bindings[ControlProfiles.Actions[9].Name].Combos = [];
        var full = new ControlDocument
        {
            Profiles = Enumerable.Range(0, 24).Select(n => ControlProfiles.Clone(profile, $"Layout {n}")).ToList()
        };
        full.ActiveId = full.Profiles[0].Id;
        store.Save(full);
        var json = File.ReadAllText(path);
        var bytes = Encoding.UTF8.GetByteCount(json);
        const int limit = 1024 * 1024;
        Check(bytes > 256 * 1024 && bytes <= limit, "A 24-profile combo library exceeded the supported budget.");
        var loaded = store.Load();
        Check(loaded.Profiles.Count == 24 && loaded.ActiveId == full.ActiveId &&
            loaded.Profiles[0].Mw2JumpJets == null &&
            loaded.Profiles[0].Bindings[ControlProfiles.Actions[9].Name].Combos == null &&
            loaded.Profiles[0].Bindings.Values.Sum(binding => binding.Combos?.Count ?? 0) == 64 &&
            json.Contains("\"Kind\": \"Key\"") && json.Contains("\"Kind\": \"Mouse\""),
            "Full library lost its selection, combo bindings, or compact JSON.");
        profile.Bindings[ControlProfiles.Actions[8].Name].Combos = [Chord(KeyInput(0x39), KeyInput(0xa1))];
        Invalid(() => ControlProfiles.Validate(new ControlDocument { Profiles = [profile] }));

        File.WriteAllText(path, json + new string(' ', limit - bytes));
        Check(store.LoadForLaunch().Profiles.Count == 24, "An exact 1 MiB layout library was rejected.");
        File.AppendAllText(path, " ");
        Invalid(() => store.LoadForLaunch());
    }

    private static ControlComboInput KeyInput(int scan) => new(ControlComboInputKind.Key, scan);
    private static ControlComboInput MouseInput(int mouse) => new(ControlComboInputKind.Mouse, mouse);
    private static ControlCombo Chord(params ControlComboInput[] inputs) => new() { Inputs = [.. inputs] };

    private static void Check(bool value, string message)
    {
        if (!value) throw new Exception(message);
    }

    private static void Invalid(Action action)
    {
        try { action(); }
        catch (InvalidDataException) { return; }
        throw new Exception("Invalid controls input accepted.");
    }
}
