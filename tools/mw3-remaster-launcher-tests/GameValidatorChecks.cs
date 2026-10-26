using System.IO;
using MW3RemasterLauncher.Core;

static class GameValidatorChecks
{
    public static void Run()
    {
        // Retail 1.0/1.2 installer shape: MicroProse\MechWarrior 3\1.0 holds Program with a trailing backslash.
        var retailKey = new Dictionary<(string, string), string> { [("1.0", "Program")] = @"D:\Games\MechWarrior3\", [("1.0", "Version")] = "1.2" };
        var paths = GameValidator.ReadRegistryInstallPaths(new[] { "1.0" }, (key, value) => retailKey.GetValueOrDefault((key ?? "", value)));
        if (!paths.SequenceEqual(new[] { @"D:\Games\MechWarrior3" }))
            throw new Exception("Retail version-subkey Program path was not read and trimmed.");
        var mixedKey = new Dictionary<(string, string), string> { [("", "InstallDir")] = @"C:\MW3", [("1.2", "Program")] = @"D:\" };
        paths = GameValidator.ReadRegistryInstallPaths(new[] { "1.2" }, (key, value) => mixedKey.GetValueOrDefault((key ?? "", value)));
        if (!paths.SequenceEqual(new[] { @"C:\MW3", @"D:\" }))
            throw new Exception("Base-key order or drive-root separator lost.");
        if (GameValidator.ReadRegistryInstallPaths(Array.Empty<string>(), (key, value) => null).Count != 0)
            throw new Exception("Empty key produced a path.");

        var install = Path.Combine(Path.GetTempPath(), "mw3-validator-check-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(install);
        try
        {
            File.WriteAllText(Path.Combine(install, "Mech3.exe"), "authored fixture");
            var trailingKey = new Dictionary<(string, string), string> { [("1.0", "Program")] = install + @"\" };
            paths = GameValidator.ReadRegistryInstallPaths(new[] { "1.0" }, (key, value) => trailingKey.GetValueOrDefault((key ?? "", value)));
            if (paths.Count != 1 || GameValidator.FindExecutableInDirectory(paths[0]) == null)
                throw new Exception("Registry path did not resolve to Mech3.exe.");
            Console.WriteLine("Game auto-detect registry checks passed.");
        }
        finally { Directory.Delete(install, true); }
    }
}
