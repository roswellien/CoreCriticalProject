using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using MW3RemasterLauncher.Core;

static class EnvironmentPackChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "MW3 environment checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var archive = Path.Combine(root, "environment.mw3pack");
            var payload = new byte[] { 1, 2, 3, 4 };
            var registry = JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 2, payload_profile = "prepared-environment-v1", operation = "training", lighting = "environment/lighting.json", banks = new Dictionary<string, string> { ["zbd/t1/texture.zbd"] = "environment/data.bin" }, authored = new[] { "environment/data.bin" }, world = new[] { "environment/data.bin" }, effects = "environment/data.bin", authored_manifest = "environment/data.bin", world_manifest = "environment/data.bin", detail = new { water = "environment/data.bin", surf = "environment/data.bin", cloud = "environment/data.bin" } });
            var members = new Dictionary<string, byte[]> { ["environment/environment.json"] = registry, ["environment/data.bin"] = payload,
                ["environment/lighting.json"] = JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 1, missions = new { }, maps = new { } }) };
            var files = members.ToDictionary(x => x.Key, x => new { bytes = x.Value.Length, sha256 = Convert.ToHexString(SHA256.HashData(x.Value)).ToLowerInvariant() });
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Create))
            {
                void Write(string name, byte[] bytes) { using var stream = zip.CreateEntry(name).Open(); stream.Write(bytes); }
                Write("pack.json", JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 2, id = "test.environment", name = "Authored environment fixture", native_payload = new { profile = "prepared-environment-v1", registry = "environment/environment.json", path_base = "pack-root" }, files }));
                foreach (var pair in members) Write(pair.Key, pair.Value);
            }
            var installed = PackStorage.Install(Path.Combine(root, "mods"), archive);
            if (installed.NativePayload?.Profile != "prepared-environment-v1" || !File.Exists(Path.Combine(installed.DirectoryPath, "environment/data.bin")))
                throw new Exception("Environment install did not preserve its payload.");
        }
        finally { Directory.Delete(root, true); }
    }
}
