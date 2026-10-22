using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using MW3RemasterLauncher.Core;

internal static class SaveBackupChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "MW3 save fixtures " + Guid.NewGuid().ToString("N"));
        var game = Path.Combine(root, "Game");
        var user = Path.Combine(root, "User");
        Directory.CreateDirectory(Path.Combine(game, "pilots", "games"));
        Directory.CreateDirectory(Path.Combine(game, "configs"));
        var pilot = Path.Combine(game, "pilots", "test.mw3");
        var save = Path.Combine(game, "pilots", "games", "test0101.mw3");
        var config = Path.Combine(game, "configs", "custom.mw3");
        var registry = Path.Combine(root, "registry.txt");
        File.WriteAllText(pilot, "authored pilot"); File.WriteAllText(save, "authored campaign");
        File.WriteAllText(config, "authored config"); File.WriteAllText(registry, "authored registry");
        void Check(bool value, string message) { if (!value) throw new Exception(message); }
        try
        {
            var backups = new SaveBackups(game, user, registry);
            var snapshot = backups.Create("Manual fixture");
            File.WriteAllText(pilot, "newer pilot"); File.WriteAllText(save, "newer campaign");
            File.WriteAllText(config, "newer config"); File.WriteAllText(registry, "newer registry");
            var extra = Path.Combine(game, "pilots", "extra.mw3"); File.WriteAllText(extra, "keep extra");
            var safety = backups.Restore(snapshot);
            Check(File.ReadAllText(pilot) == "authored pilot" && File.ReadAllText(save) == "authored campaign", "Pilot/campaign restore failed");
            Check(File.ReadAllText(config) == "authored config" && File.ReadAllText(registry) == "authored registry", "Config/registry restore failed");
            Check(File.ReadAllText(extra) == "keep extra" && File.Exists(safety), "Extra save or safety backup lost");
            backups.Restore(safety);
            Check(File.ReadAllText(save) == "newer campaign", "Automatic safety backup cannot undo restore");
            var emptyGame = Path.Combine(root, "EmptyGame"); Directory.CreateDirectory(Path.Combine(emptyGame, "pilots"));
            new SaveBackups(emptyGame, Path.Combine(root, "EmptyUser"), Path.Combine(root, "empty-registry.txt")).Restore(snapshot);
            Check(File.ReadAllText(Path.Combine(emptyGame, "pilots", "test.mw3")) == "authored pilot", "Restore into a fresh installation failed");

            var damaged = Path.Combine(root, "damaged.zip"); File.Copy(snapshot, damaged);
            using (var zip = ZipFile.Open(damaged, ZipArchiveMode.Update))
            { zip.GetEntry("pilots/test.mw3")!.Delete(); using var entry = new StreamWriter(zip.CreateEntry("pilots/test.mw3").Open()); entry.Write("tampered"); }
            var before = File.ReadAllText(pilot); var count = backups.List().Length;
            try { backups.Restore(damaged); throw new Exception("Damaged backup accepted"); } catch (InvalidDataException) { }
            Check(File.ReadAllText(pilot) == before && backups.List().Length == count, "Failed validation changed saves or created backup");

            void Malformed(string name, bool duplicate = false)
            {
                var path = Path.Combine(root, Guid.NewGuid().ToString("N") + ".zip");
                using (var archive = ZipFile.Open(path, ZipArchiveMode.Create))
                {
                    var bytes = new byte[] { 1, 2, 3 };
                    var files = new Dictionary<string, UpdateFile> { [name] = new(3, Convert.ToHexString(SHA256.HashData(bytes))) };
                    using (var meta = archive.CreateEntry("snapshot.json").Open()) JsonSerializer.Serialize(meta, new SaveSnapshot(1, "fixture", DateTime.UtcNow, files));
                    using (var entry = archive.CreateEntry(name).Open()) entry.Write(bytes);
                    if (duplicate) { using var entry = archive.CreateEntry(name).Open(); entry.Write(bytes); }
                }
                try { backups.Restore(path); throw new Exception("Unsafe snapshot accepted: " + name); } catch (InvalidDataException) { }
            }
            Malformed("pilots/../../outside.mw3"); Malformed("pilots/code.exe"); Malformed("pilots/test.mw3", true);
            Check(File.ReadAllText(pilot) == before, "Unsafe archive modified player data");
            using (var locked = new FileStream(Path.Combine(backups.DirectoryPath, ".save-lock"), FileMode.Open, FileAccess.ReadWrite, FileShare.None))
            { try { backups.Create("overlap"); throw new Exception("Concurrent writer accepted"); } catch (IOException) { } }
            Console.WriteLine("Save backups: pilot/campaign/config/registry restore, automatic undo, preservation, corruption, traversal, executable/duplicate rejection and writer locking passed.");
        }
        finally { Directory.Delete(root, true); }
    }
}
