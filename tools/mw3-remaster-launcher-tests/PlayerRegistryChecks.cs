#nullable enable
using System.IO;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class PlayerRegistryChecks
{
    public static void Run()
    {
        var temporary = Path.GetFullPath(Path.GetTempPath());
        var root = Path.GetFullPath(Path.Combine(temporary, "MW3PlayerRegistryChecks-" + Guid.NewGuid().ToString("N")));
        if (!root.StartsWith(temporary, StringComparison.OrdinalIgnoreCase)) throw new Exception("Invalid fixture root");
        Directory.CreateDirectory(root);
        JsonObject Profile(string? seed = null) => new()
        {
            ["native"] = new JsonObject { ["runtime_environment"] = seed == null ? new JsonObject() :
                new JsonObject { ["MW34_REG_OVERLAY"] = seed } }
        };
        try
        {
            var fresh = Profile();
            var state = PlayerRegistry.Bind(fresh, Path.Combine(root, "fresh"));
            if (new FileInfo(state).Length != 0) throw new Exception("Fresh setup supplied captured defaults");
            if (fresh["native"]!["runtime_environment"]!["MW34_REG_OVERLAY"]!.ToString() != state)
                throw new Exception("Native game did not receive its writable settings path");
            var renderer = PlayerRegistry.ConfigureHardwareRenderer("");
            if (!renderer.Contains("\tinstalloptions\t4\t04000000") ||
                !renderer.Contains("\thwcardflag\t4\t01000000") || !renderer.Contains("\thwcarddev\t4\t00000000"))
                throw new Exception("Fresh installed renderer configuration is incomplete");
            var damaged = renderer.Replace("04000000", "00000000").Replace("01000000", "00000000")
                + "V hkcu\\software\\microprose\\mechwarrior 3\\1.0\tplayer-control\t4\tabcdef00\n";
            var repaired = PlayerRegistry.ConfigureHardwareRenderer(damaged);
            if (!repaired.Contains("\tinstalloptions\t4\t04000000") ||
                !repaired.Contains("\tplayer-control\t4\tabcdef00") ||
                PlayerRegistry.ConfigureHardwareRenderer(repaired) != repaired)
                throw new Exception("Renderer repair lost player state or was not idempotent");
            var unverified = Path.Combine(root, "unverified");
            try { PlayerRegistry.PrepareInstalledRenderer(Profile(), unverified, root); throw new Exception("Missing hardware files were advertised as installed"); }
            catch (FileNotFoundException) { }
            if (Directory.Exists(unverified)) throw new Exception("Unverified renderer modified player settings");
            var seed = Path.Combine(root, "runtime-registry.txt");
            File.WriteAllText(seed, "K authored-fixture\n");
            var migrated = PlayerRegistry.Bind(Profile(seed), Path.Combine(root, "migrated"));
            if (File.ReadAllText(seed) != "K authored-fixture\n" || File.ReadAllText(migrated) != File.ReadAllText(seed))
                throw new Exception("Migration changed the verified runtime or lost existing settings");
            File.WriteAllText(migrated, "K player-changed-state\n");
            File.WriteAllText(seed, "K updated-runtime-template\n");
            PlayerRegistry.Bind(Profile(seed), Path.Combine(root, "migrated"));
            if (File.ReadAllText(migrated) != "K player-changed-state\n")
                throw new Exception("Runtime update replaced player settings");
            var missingRoot = Path.Combine(root, "missing");
            try { PlayerRegistry.Bind(Profile(Path.Combine(root, "missing-seed")), missingRoot); throw new Exception("Missing old settings silently reset"); }
            catch (FileNotFoundException) { }
            if (File.Exists(Path.Combine(missingRoot, "native-settings/mw3-registry.txt")))
                throw new Exception("Failed migration published partial settings");
            using (var file = File.OpenWrite(seed)) file.SetLength(8 * 1024 * 1024 + 1);
            var oversizedRoot = Path.Combine(root, "oversized");
            try { PlayerRegistry.Bind(Profile(seed), oversizedRoot); throw new Exception("Oversized settings accepted"); }
            catch (InvalidDataException) { }
            if (Directory.EnumerateFiles(oversizedRoot, "*", SearchOption.AllDirectories).Any())
                throw new Exception("Failed settings migration left a partial file");
        }
        finally { Directory.Delete(root, true); }
        Console.WriteLine("Player registry: fresh initialization, migration, update preservation and failure checks passed.");
    }
}
