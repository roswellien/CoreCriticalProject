using System.IO;
using System.Security.Cryptography;
using MW3RemasterLauncher.Core;

static class GameInstallationChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "mw3-install-check-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var fixture = Path.Combine(root, "authored.txt");
            PackStorage.Resolve(Path.GetPathRoot(root)!, "MW3CD.TXT");
            File.WriteAllText(fixture, "authored installation fixture");
            var hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(fixture)));
            GameInstallation.VerifyFile(fixture, hash);
            ExpectFailure(() => GameInstallation.VerifyFile(fixture, new string('0', 64)));
            ExpectFailure(() => GameInstallation.VerifyFile(fixture, hash, 1));
            ExpectFailure(() => GameInstallation.VerifyExistingAsync(root).GetAwaiter().GetResult());
            // An existing destination is protected even if source, patch and tools are invalid.
            var destination = Path.Combine(root, "game");
            Directory.CreateDirectory(destination);
            var sentinel = Path.Combine(destination, "save.dat");
            File.WriteAllText(sentinel, "keep this save");
            ExpectFailure(() => GameInstallation.InstallDirectoryAsync(root, fixture, destination, root).GetAwaiter().GetResult());
            if (File.ReadAllText(sentinel) != "keep this save") throw new Exception("Existing game data was modified.");
            // Failed staging never publishes a destination or leaves a partial installation.
            File.WriteAllText(Path.Combine(root, "unshield.exe"), "authored unknown extractor; must never execute");
            var failed = Path.Combine(root, "new-game");
            ExpectFailure(() => GameInstallation.InstallDirectoryAsync(root, fixture, failed, root).GetAwaiter().GetResult());
            if (Directory.Exists(failed) || Directory.GetDirectories(root, ".mw3-install-*").Length != 0)
                throw new Exception("Failed install left a published/partial game directory.");
            Console.WriteLine("Original-data setup checks passed.");
        }
        finally { Directory.Delete(root, true); }
    }
    private static void ExpectFailure(Action action)
    {
        try { action(); }
        catch (Exception error) when (error is IOException or InvalidDataException) { return; }
        throw new Exception("Invalid installation unexpectedly succeeded.");
    }
}
