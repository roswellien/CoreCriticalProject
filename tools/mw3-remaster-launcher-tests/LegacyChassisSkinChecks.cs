using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class LegacyChassisSkinChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "CC legacy skins " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var descriptor = JsonNode.Parse("""
                {"schema_version":2,"resource":"example","definition":"raw.bin",
                 "materials":"raw.bin","silhouette":"raw.bin",
                 "models":{"close":"raw.bin","distance":"raw.bin","cockpit":"raw.bin"},
                 "motions":{"example_walk":"raw.bin"},"animations":{"anim_example.zrd":"raw.bin"},
                 "textures":{"example01":"raw.bin"},"skins":[]}
                """)!;
            var skins = descriptor["skins"]!.AsArray();
            for (var index = 0; index < 8; index++)
                skins.Add(new JsonObject
                {
                    ["id"] = index == 0 ? "primary" : "variant" + (char)('b' + index - 1),
                    ["message"] = index == 0 ? "MSG_SKIN_PRIMARY" : "MSG_SKIN_VARIANT" + (char)('A' + index),
                    ["suffix"] = index == 0 ? "" : "_" + (char)('a' + index)
                });
            var registry = JsonNode.Parse("""
                {"schema_version":2,"payload_profile":"additional-chassis-v1","chassis":[
                  {"id":"community.skins:mech","name":"Example","metadata_template":"annihilator","legacy":"legacy.json"}]}
                """)!;
            var resources = new Dictionary<string, byte[]>
            {
                ["raw.bin"] = new byte[] { 1 }, // Binary semantics belong to the coordinator.
                ["legacy.json"] = JsonSerializer.SerializeToUtf8Bytes(descriptor),
                [ChassisPack.Registry] = JsonSerializer.SerializeToUtf8Bytes(registry)
            };
            var manifest = new PackManifest
            {
                SchemaVersion = 2,
                Id = "community.skins",
                Name = "Eight legacy skins",
                Provides = new PackProvides { Mechs = new() { "community.skins:mech" } },
                NativePayload = new NativePackPayload
                {
                    Profile = ChassisPack.Profile,
                    Registry = ChassisPack.Registry,
                    PathBase = "pack-root",
                    RequiredFormats = new() { "MW3LEGACY" },
                    RequiredCapabilities = new() { ["additional-mech-chassis"] = 3, [LegacyChassisSkins.Capability] = 1 }
                },
                Files = resources.ToDictionary(p => p.Key, p => new PackFile
                {
                    Bytes = p.Value.Length,
                    Sha256 = Convert.ToHexString(SHA256.HashData(p.Value)).ToLowerInvariant()
                })
            };
            var archive = Path.Combine(root, "fixture.mw3pack");
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Create))
            {
                foreach (var (name, bytes) in resources)
                {
                    using var stream = zip.CreateEntry(name).Open();
                    stream.Write(bytes);
                }
                using var output = zip.CreateEntry("pack.json").Open();
                JsonSerializer.Serialize(output, manifest);
            }
            var installed = new PackManager(Path.Combine(root, "library")).InstallPack(archive);
            if (ChassisPack.Read(installed.DirectoryPath, installed).Single().Id != "community.skins:mech")
                throw new Exception("Eight skins changed the chassis identity.");
            var host = JsonNode.Parse("""{"content_capabilities":{"additional-mech-chassis":[1,2,3]}}""")!.AsObject();
            void Reject(Action action)
            {
                try { action(); }
                catch (InvalidDataException) { return; }
                throw new Exception("Malformed or unsupported legacy skins were accepted.");
            }
            Reject(() => RuntimeContentCapabilities.Require(host, installed.NativePayload!, installed.Id));
            host["content_capabilities"]![LegacyChassisSkins.Capability] = new JsonArray(1);
            RuntimeContentCapabilities.Require(host, installed.NativePayload!, installed.Id);

            void WriteDescriptor(JsonNode value)
            {
                var bytes = JsonSerializer.SerializeToUtf8Bytes(value);
                File.WriteAllBytes(Path.Combine(installed.DirectoryPath, "legacy.json"), bytes);
                installed.Files!["legacy.json"] = new PackFile
                {
                    Bytes = bytes.Length,
                    Sha256 = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()
                };
            }
            foreach (var mutate in new Action<JsonNode>[] {
                d => d["skins"]![1]!["id"] = "primary",
                d => d["skins"]![1]!["message"] = "MSG_SKIN_VARIANTC",
                d => d["skins"]![1]!["suffix"] = "../b",
                d => d["skins"]![2]!["suffix"] = "_b",
                d => d["skins"]![0]!["suffix"] = "_a",
                d => d["skins"]![1]!["extra"] = 1,
                d => d["skins"] = new JsonArray(),
                d => d["schema_version"] = true,
                d => d["schema_version"] = 3,
                d => d["textures"]!["EXAMPLE01"] = "raw.bin",
                d => d["textures"]!["example01"] = "../raw.bin",
                d => d["textures"]!["example01"] = "missing.bin"
            })
            {
                var bad = descriptor.DeepClone();
                mutate(bad);
                WriteDescriptor(bad);
                Reject(() => ChassisPack.Read(installed.DirectoryPath, installed));
            }
            WriteDescriptor(descriptor);
            installed.NativePayload!.RequiredCapabilities.Remove(LegacyChassisSkins.Capability);
            Reject(() => ChassisPack.Read(installed.DirectoryPath, installed));
            installed.NativePayload.RequiredCapabilities[LegacyChassisSkins.Capability] = 1;
            File.WriteAllBytes(Path.Combine(installed.DirectoryPath, "raw.bin"), new byte[] { 2 });
            Reject(() => ChassisPack.Read(installed.DirectoryPath, installed));
            Console.WriteLine("Legacy skin checks passed: eight slots, import, capability gate, metadata and integrity rejection.");
        }
        finally { Directory.Delete(root, true); }
    }
}
