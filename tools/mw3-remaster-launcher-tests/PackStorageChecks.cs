using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using MW3RemasterLauncher.Core;

static class PackStorageChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "MW3 pack checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var manager = new PackManager(root);
            var archive = Path.Combine(root, "authored.mw3pack");
            void Build(string id = "test.mech", string member = "payload/mesh.bin", bool corrupt = false, int schema = 2)
            {
                var content = Encoding.UTF8.GetBytes("authored mesh");
                var registry = Encoding.UTF8.GetBytes("""{"schema_version":2,"payload_profile":"prepared-native-v1","models":[{"environment":{"MW34_ORION_MESH":"payload/mesh.bin"}}]}""");
                var files = new Dictionary<string, object>();
                foreach (var (name, bytes) in new[] { (member, content), ("models/models.json", registry) })
                    files[name] = new { bytes = bytes.Length, sha256 = corrupt && name == member ? new string('0', 64) : Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant() };
                using var zip = ZipFile.Open(archive, ZipArchiveMode.Create);
                void Write(string name, byte[] bytes) { using var stream = zip.CreateEntry(name).Open(); stream.Write(bytes); }
                Write("pack.json", JsonSerializer.SerializeToUtf8Bytes(new { schema_version = schema, id, name = "Authored fixture", native_payload = new { profile = "prepared-native-v1", registry = "models/models.json", path_base = "pack-root" }, files }));
                Write(member, content);
                Write("models/models.json", registry);
            }
            void Reject(Action action)
            {
                try { action(); }
                catch (InvalidDataException) { return; }
                throw new Exception("Invalid pack was accepted.");
            }
            Build();
            var installed = manager.InstallPack(archive);
            var installedPayload = Path.Combine(installed.DirectoryPath, "payload/mesh.bin");
            if (!File.Exists(installedPayload)) throw new Exception("Pack payload not installed");
            foreach (var bad in new[] { "../escape", "C:/escape", "//host/share", "payload/mesh.bin:stream", "payload/CON.bin", "payload/a. /b", "payload/../escape", "payload\\escape" })
            {
                File.Delete(archive); Build(member: bad);
                Reject(() => manager.InstallPack(archive));
                if (!File.Exists(installedPayload)) throw new Exception("Failed update removed working version");
            }
            File.Delete(archive); Build(id: "../outside"); Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build(corrupt: true); Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build(schema: 3); Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build();
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Update))
            { using var stream = zip.CreateEntry("PAYLOAD/MESH.BIN").Open(); stream.WriteByte(0); }
            Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build();
            manager.InstallPack(archive);
            var updated = manager.Packs.Single();
            manager.RollbackPack(updated);
            if (!File.Exists(installedPayload)) throw new Exception("Rollback lost installed content");
            // Reject links and undeclared members before touching an installed version.
            File.Delete(archive); Build();
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Update))
                zip.GetEntry("payload/mesh.bin")!.ExternalAttributes = unchecked((int)0xA1FF0000);
            Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build();
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Update))
            { using var stream = zip.CreateEntry("undeclared.txt").Open(); stream.WriteByte(0); }
            Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build();
            var truncated = File.ReadAllBytes(archive); File.WriteAllBytes(archive, truncated[..^12]);
            Reject(() => manager.InstallPack(archive));
            File.Delete(archive); Build();
            // A loose archive must never overwrite an installed version on refresh.
            var loose = Path.Combine(manager.ModsRoot, "stale.zip"); File.Copy(archive, loose);
            File.WriteAllText(installedPayload, "keep installed");
            manager.RefreshPacks(new());
            if (File.ReadAllText(installedPayload) != "keep installed" || manager.GetActivePackIds().Count != 0)
                throw new Exception("Refresh mutated installed content or selection");
            Reject(() => manager.UninstallPack(new PackManifest { Id = "test.mech", DirectoryPath = root }));
            manager.UninstallPack(manager.Packs.Single());
            manager.RefreshPacks(new());
            if (manager.Packs.Count != 0) throw new Exception("Uninstalled pack was restored");
            // Recover an interrupted activation without trusting its ID from metadata.
            File.Delete(archive); Build(); installed = manager.InstallPack(archive);
            Directory.Move(installed.DirectoryPath, Path.Combine(manager.ModsRoot, ".rollback-test.mech"));
            manager.RefreshPacks(new() { "test.mech" });
            if (manager.GetActivePackDirectories().Count != 1) throw new Exception("Interrupted update not recovered");
            Console.WriteLine("Pack install, rejection, preservation, disable, uninstall and recovery checks passed.");
        }
        finally { PackStorage.DeleteOwnedTree(root); }
    }
}
