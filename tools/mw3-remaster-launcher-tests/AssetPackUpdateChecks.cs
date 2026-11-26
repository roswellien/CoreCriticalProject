using System.IO;
using System.IO.Compression;
using System.Net;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using MW3RemasterLauncher.Core;

static class AssetPackUpdateChecks
{
    private static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    private sealed class Feed(byte[] body) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            if (request.Method != HttpMethod.Get || request.RequestUri?.AbsoluteUri != "https://updates.example.test/assets.json")
                throw new Exception("Asset check sent an unexpected request.");
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent(body) });
        }
    }

    public static async Task Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "Asset update fixture " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            using var key = RSA.Create(3072);
            var config = new OnlineUpdateConfiguration(1, "https://updates.example.test/assets.json", "playtest",
                "public-readonly-v1", new[] { "updates.example.test", "private.example.test" });
            var trust = new RuntimeUpdateTrust("", new() { ["fixture"] = key.ExportSubjectPublicKeyInfoPem() });
            var app = Path.Combine(root, "application");
            var runtime = Path.Combine(app, "Runtime");
            Directory.CreateDirectory(runtime);
            File.WriteAllText(Path.Combine(runtime, "runtime.json"), """{"version":"1.2.0"}""");
            var profile = Path.Combine(runtime, "profile.json");
            const string supportedProfile =
                """{"native":{"mesh_payload_versions":[2],"content_capabilities":{"prepared-mechs":[1]}}}""";
            File.WriteAllText(profile, supportedProfile);
            File.WriteAllBytes(Path.Combine(app, "update-trust.json"), JsonSerializer.SerializeToUtf8Bytes(trust, Json));
            File.WriteAllBytes(Path.Combine(app, AssetPackUpdateService.ConfigurationFile), JsonSerializer.SerializeToUtf8Bytes(config, Json));
            var manager = new PackManager(Path.Combine(root, "player"));
            var now = DateTimeOffset.UtcNow;
            const string id = "fixture.asset-models";

            string WriteArchive(string version)
            {
                var path = Path.Combine(root, $"{version}.mw3pack");
                var mesh = Encoding.UTF8.GetBytes($"authored release {version}");
                var models = Encoding.UTF8.GetBytes("""{"schema_version":2,"payload_profile":"prepared-native-v1","models":[{"environment":{"MW34_ORION_MESH":"payload/mesh.bin"}}]}""");
                var resources = new Dictionary<string, byte[]> { ["payload/mesh.bin"] = mesh, ["models/models.json"] = models };
                var metadata = JsonSerializer.SerializeToUtf8Bytes(new
                {
                    schema_version = 2, id, version, name = "Authored asset fixture",
                    native_payload = new { profile = "prepared-native-v1", registry = "models/models.json",
                        path_base = "pack-root", required_formats = new[] { "BWMESH2" } },
                    files = resources.ToDictionary(pair => pair.Key, pair => new { bytes = pair.Value.Length, sha256 = Sha(pair.Value) })
                });
                using var zip = ZipFile.Open(path, ZipArchiveMode.Create);
                void Write(string name, byte[] bytes)
                {
                    using var stream = zip.CreateEntry(name).Open();
                    stream.Write(bytes);
                }
                Write("pack.json", metadata);
                foreach (var item in resources) Write(item.Key, item.Value);
                return path;
            }

            byte[] Sign(AssetPackCatalogDocument document)
            {
                var payload = JsonSerializer.SerializeToUtf8Bytes(document, Json);
                return JsonSerializer.SerializeToUtf8Bytes(new
                {
                    key_id = "fixture",
                    payload = Convert.ToBase64String(payload),
                    signature = Convert.ToBase64String(key.SignData(payload, HashAlgorithmName.SHA256, RSASignaturePadding.Pss))
                });
            }

            var oldPath = WriteArchive("1.0.0");
            var newPath = WriteArchive("1.1.0");
            var first = manager.InstallPack(oldPath);
            var manifestPath = Path.Combine(first.DirectoryPath, "pack.json");
            var predecessor = File.ReadAllBytes(manifestPath);
            var installed = new InstalledAssetPack(id, GameCatalog.Mw3, "1.0.0", Sha(predecessor));
            var release = new AssetPackRelease(id, GameCatalog.Mw3, "1.1.0", "1.2.0",
                new("https://private.example.test/1.1.0.mw3pack", "1.1.0.mw3pack",
                    new FileInfo(newPath).Length, Sha(File.ReadAllBytes(newPath))), new[] { installed.ManifestSha256 });
            var document = new AssetPackCatalogDocument(1, "corecritical-asset-pack-catalog-v1", "playtest", 10,
                now.AddMinutes(-1), now.AddDays(1), new[] { release });
            var verified = AssetPackUpdateCatalog.Verify(Sign(document), trust, config, now);
            bool Eligible(InstalledAssetPack pack, Version version) => AssetPackUpdateCatalog.Plan(verified,
                new[] { pack }, GameCatalog.Mw3, version).Count == 1;
            if (!Eligible(installed, new Version(1, 2, 0)) ||
                Eligible(installed, new Version(1, 1, 9)) ||
                Eligible(installed with { Version = "1.1.0.0" }, new Version(1, 2, 0)) ||
                Eligible(installed with { Version = "1.2.0" }, new Version(1, 2, 0)) ||
                Eligible(installed with { Version = "unknown" }, new Version(1, 2, 0)) ||
                Eligible(installed with { ManifestSha256 = new string('f', 64) }, new Version(1, 2, 0)) ||
                Eligible(installed with { GameId = "mw3pm" }, new Version(1, 2, 0)) ||
                Eligible(installed with { Id = "another.pack" }, new Version(1, 2, 0)))
                throw new Exception("Pack identity, lineage, or version selection was incorrect.");

            var big = release with { Archive = release.Archive with { Bytes = 2403550232 } };
            AssetPackUpdateCatalog.Verify(Sign(document with { Packs = new[] { big } }), trust, config, now);
            Reject(() => AssetPackUpdateCatalog.Verify(Sign(document with { Packs = new[] { release, release } }), trust, config, now));
            Reject(() => AssetPackUpdateCatalog.Verify(Sign(document), trust, config, now, 11));
            Reject(() => AssetPackUpdateCatalog.Verify(Sign(document with { ExpiresUtc = now.AddSeconds(-1) }), trust, config, now));
            var broken = JsonSerializer.Deserialize<Dictionary<string, string>>(Sign(document))!;
            broken["signature"] = Convert.ToBase64String(new byte[384]);
            Reject(() => AssetPackUpdateCatalog.Verify(JsonSerializer.SerializeToUtf8Bytes(broken), trust, config, now));

            using var service = new AssetPackUpdateService(app, root, manager, new Feed(Sign(document)));
            if ((await service.CheckAsync()).Single().Version != "1.1.0")
                throw new Exception("Asset service did not discover the expected installed pack update.");
            Reject(() => service.InstallDownloaded(id, oldPath));
            using (GameUpdateGate.Acquire(root))
            {
                try { service.InstallDownloaded(id, newPath); throw new Exception("Install did not honor the game gate."); }
                catch (InvalidOperationException) { }
            }
            File.AppendAllText(manifestPath, "\n");
            Reject(() => service.InstallDownloaded(id, newPath));
            File.WriteAllBytes(manifestPath, predecessor);
            File.WriteAllText(profile, supportedProfile.Replace("[2]", "[1]"));
            Reject(() => service.InstallDownloaded(id, newPath));
            File.WriteAllText(profile, supportedProfile);
            var result = service.InstallDownloaded(id, newPath);
            manager.RefreshPacks(new() { id });
            if (result.Version != "1.1.0" || manager.Packs.Single().Version != "1.1.0" ||
                manager.GetActivePackIds().Single() != id ||
                PackStorage.ReadManifest(Path.Combine(manager.ModsRoot, ".rollback-" + id, "pack.json")).Version != "1.0.0")
                throw new Exception("Verified pack update did not preserve the installed ID, selection, and rollback.");
            if ((await service.CheckAsync()).Count != 0)
                throw new Exception("Already installed release was offered again.");
            using var replay = new AssetPackUpdateService(app, root, manager, new Feed(Sign(document with { Sequence = 9 })));
            try { await replay.CheckAsync(); throw new Exception("Saved catalog sequence was not enforced."); }
            catch (InvalidDataException) { }
            if (new LauncherSettings().AutomaticAssetPackChecks)
                throw new Exception("Asset update notifications should be opt-in.");
            Console.WriteLine("Asset pack updates passed signature, freshness, compatibility, lineage, game exclusion, and in-place upgrade checks.");
        }
        finally { PackStorage.DeleteOwnedTree(root); }
    }

    private static string Sha(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();

    private static void Reject(Action action)
    {
        try { action(); }
        catch (InvalidDataException) { return; }
        throw new Exception("An invalid asset pack update was accepted.");
    }
}
