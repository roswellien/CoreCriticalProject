using System.Buffers.Binary;
using System.Text;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class ControlProfileChecks
{
    public static void Run()
    {
        void Check(bool value, string message) { if (!value) throw new Exception(message); }
        void Invalid(Action action) { try { action(); } catch (System.IO.InvalidDataException) { return; } throw new Exception("Invalid controls input accepted"); }
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
            Check(mw5.Bindings["CMD_THROTTLE1"].Primary == 0x2d && mw5.Bindings["CMD_THROTTLE0"].Primary == 0x52,
                "MW5 stop/full throttle semantics reversed");
            Check(mw5.Bindings["CMD_WEPGRP_1"].Primary == 2 && mw5.Bindings["CMD_TRIGGER1"].Mouse == 1,
                "MW3 weapon group selection/fire adaptation changed");
            Check(mw5.Bindings.Values.All(b => b.Mouse is >= 0 and <= 3 && b.Joystick == 0 &&
                new[] { b.Primary, b.Secondary }.All(k => (k & 255) is not (0x43 or 0x44 or 0x57 or 0x58))), "Unsupported or reserved input in MW5 layout");
            Check(store.Load().Profiles.Count == 2 && System.IO.File.Exists(System.IO.Path.Combine(root, "controls/mw3/profiles.json")), "Built-in layouts not persisted or duplicated");
            mw5.Name = "Edited MW5"; mw5.Bindings["CMD_THROTTLE_UP"].Primary = 0;
            store.Save(doc);
            Check(store.Load().Profiles.Single(p => p.Id == ControlPresets.Mw5Id).Name == "Edited MW5" && store.Load().Profiles.Single(p => p.Id == ControlPresets.Mw5Id).Bindings["CMD_THROTTLE_UP"].Primary == 0,
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
            var fullStore = new ControlProfiles(System.IO.Path.Combine(root, "full"));
            var full = new ControlDocument { Profiles = Enumerable.Range(0, 24).Select(n => ControlProfiles.Clone(mw5, "Layout " + n)).ToList() };
            full.ActiveId = full.Profiles[0].Id;
            System.IO.Directory.CreateDirectory(System.IO.Path.Combine(root, "full/controls/mw3"));
            System.IO.File.WriteAllText(System.IO.Path.Combine(root, "full/controls/mw3/profiles.json"), System.Text.Json.JsonSerializer.Serialize(full));
            Check(fullStore.Load().Profiles.Count == 24 && fullStore.Load().ActiveId == full.ActiveId, "Built-in seeding damaged full library");
            var p = ControlProfiles.ImportRegistry(text);
            Check(p.Bindings.Count == 105 && p.Bindings.Values.All(b => b.Primary == 0x1e && b.Secondary == 0x21e && b.Mouse == 2 && b.Joystick == 5), "Button packing changed");
            Check(ControlProfiles.Conflicts(p).Count == 2, "Shared keys not detected");
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
            var path = System.IO.Path.Combine(root, "controls/mw3/profiles.json");
            System.IO.File.WriteAllText(path, "{bad-json");
            try { store.Load(); throw new Exception("Corrupt profiles silently reset"); } catch (System.Text.Json.JsonException) { }
            Check(System.IO.File.ReadAllText(path) == "{bad-json", "Corrupt profiles overwritten");
        }
        finally { System.IO.Directory.Delete(root, true); }
        Console.WriteLine("Controls profile isolation, import, clearing, restart and original-settings restoration checks passed.");
    }
}
