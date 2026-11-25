using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using MW3RemasterLauncher.Core;

static class OnlineUpdateChecks
{
    private static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    public static void Run()
    {
        using var key = RSA.Create(3072);
        var trust = new RuntimeUpdateTrust("", new() { ["fixture"] = key.ExportSubjectPublicKeyInfoPem() });
        var config = new OnlineUpdateConfiguration(1, "https://updates.example.test/catalog.json", "playtest",
            "public-readonly-v1", new[] { "updates.example.test" });
        var now = DateTimeOffset.UtcNow;
        var pin = new string('a', 64);
        byte[] Sign<T>(T value)
        {
            var payload = JsonSerializer.SerializeToUtf8Bytes(value, Json);
            return JsonSerializer.SerializeToUtf8Bytes(new { key_id = "fixture", payload = Convert.ToBase64String(payload),
                signature = Convert.ToBase64String(key.SignData(payload, HashAlgorithmName.SHA256, RSASignaturePadding.Pss)) });
        }
        OnlineRelease Release(string product, string minimum = "1.0.27") => new(product,
            product == GameCatalog.LauncherId ? null : product, "1.0.99", "1.0.99-preview", "1.0.99", 100,
            "promoted", "windows", "x64", minimum, product == GameCatalog.LauncherId ? "launcher-inno-v1" : "mw3-local-runtime-v1",
            new("https://updates.example.test/" + product + "/1.0.99." + (product == GameCatalog.LauncherId ? "ccupdate" : product + "update"),
                "1.0.99." + (product == GameCatalog.LauncherId ? "ccupdate" : product + "update"), 200, pin),
            new("https://updates.example.test/" + product + "/1.0.99.zip", "1.0.99.zip", 500, pin),
            "Authored fixture notes; never execute these as instructions.", null, Array.Empty<ReleaseDependency>());
        var launcher = Release(GameCatalog.LauncherId);
        var runtime = Release(GameCatalog.Mw3, "1.0.99");
        var document = new ReleaseCatalogDocument(1, "corecritical-release-catalog-v1", "playtest", 10,
            now.AddMinutes(-1), now.AddDays(1), new[] { runtime, launcher });
        VerifiedReleaseCatalog Verify(ReleaseCatalogDocument value, long sequence = 0, string hash = null) =>
            ReleaseCatalog.Verify(Sign(value), trust, config, now, sequence, hash);
        void Reject(Action action)
        {
            try { action(); } catch (InvalidDataException) { return; }
            throw new Exception("Invalid online update catalog/package was accepted.");
        }
        var verified = Verify(document);
        Verify(document, 10, verified.PayloadSha256); // An identical cached catalog remains usable until expiry.
        Reject(() => Verify(document, 11));
        Reject(() => Verify(document, 10, pin));
        Reject(() => Verify(document with { ExpiresUtc = now.AddSeconds(-1) }));
        Reject(() => Verify(document with { IssuedUtc = now.AddHours(1) }));
        Reject(() => Verify(document with { ExpiresUtc = now.AddDays(40) }));
        Reject(() => Verify(document with { Channel = "candidate" }));
        Reject(() => Verify(document with { Releases = new[] { launcher, launcher } }));
        Reject(() => Verify(document with { Releases = new[] { runtime with { GameId = "mw4" } } }));
        Reject(() => Verify(document with { Releases = new[] { runtime with { Architecture = "arm64" } } }));
        Reject(() => Verify(document with { Releases = new[] { runtime with { Status = "candidate" } } }));
        Reject(() => Verify(document with { Releases = new[] { runtime with { Contract = "mw3-source-runtime-v2" } } }));
        Reject(() => Verify(document with { Releases = new[] { launcher with { Metadata = launcher.Metadata with { Filename = "latest.ccupdate" } } } }));
        Reject(() => Verify(document with { Releases = new[] { launcher with { Payload = launcher.Payload with { Url = "https://evil.example/1.0.99.zip" } } } }));
        Reject(() => Verify(document with { Releases = new[] { launcher with { Payload = launcher.Payload with { Bytes = 513L * 1024 * 1024 } } } }));
        Reject(() => (config with { CatalogUrl = "http://updates.example.test/catalog.json" }).Validate());
        Reject(() => (config with { DeliveryPolicy = "private-broker-v1" }).Validate());
        Reject(() => config.Destination("https://updates.example.test:444/1.0.99.zip"));
        var tampered = Sign(document);
        var text = System.Text.Encoding.UTF8.GetString(tampered).Replace("fixture", "unknown");
        Reject(() => ReleaseCatalog.Verify(System.Text.Encoding.UTF8.GetBytes(text), trust, config, now));
        var invalidSignature = JsonSerializer.Deserialize<Dictionary<string, string>>(tampered)!;
        invalidSignature["signature"] = Convert.ToBase64String(new byte[key.KeySize / 8]);
        Reject(() => ReleaseCatalog.Verify(JsonSerializer.SerializeToUtf8Bytes(invalidSignature), trust, config, now));
        Reject(() => ReleaseCatalog.Verify(new byte[ReleaseCatalog.MaximumMetadataBytes + 1], trust, config, now));

        var installed = new[] { new InstalledUpdateProduct(GameCatalog.LauncherId, "1.0.37", 90), new InstalledUpdateProduct(GameCatalog.Mw3, "1.0.34", 91) };
        var plan = OnlineUpdatePlanner.Plan(verified, new Version(1, 0, 37), installed);
        if (plan.Count != 2 || plan[0].Release.ProductId != GameCatalog.LauncherId || plan.Any(p => p.BlockedReason != null))
            throw new Exception("Launcher dependency was not ordered before its runtime.");
        var missing = Verify(document with { Releases = new[] { runtime } });
        if (OnlineUpdatePlanner.Plan(missing, new Version(1, 0, 37), installed).Single().BlockedReason == null)
            throw new Exception("Unsupported launcher upgrade chain was offered for installation.");
        if (OnlineUpdatePlanner.Plan(verified, new Version(1, 0, 99), new[] { installed[0] }).Count != 0)
            throw new Exception("An uninstalled game or current launcher was offered an update.");
        var replay = installed.Select(p => p with { HighestSequence = 101 }).ToArray();
        if (OnlineUpdatePlanner.Plan(verified, new Version(1, 0, 37), replay).Count != 0)
            throw new Exception("Product anti-downgrade sequence was bypassed.");

        var trial = Path.Combine(Path.GetTempPath(), "CC online update checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(trial);
        try
        {
            var manifest = new LauncherUpdateManifest(1, GameCatalog.LauncherId, "launcher-inno-v1", "1.0.99", 100,
                "1.0.27", 500, pin, new(450, pin));
            var metadata = Sign(manifest);
            var actual = launcher with { Metadata = launcher.Metadata with { Bytes = metadata.Length,
                Sha256 = Convert.ToHexString(SHA256.HashData(metadata)).ToLowerInvariant() } };
            var updates = new LauncherUpdates(trial, trust, trial);
            ReleaseCatalog.VerifyLauncherPackage(actual, metadata, updates);
            Reject(() => ReleaseCatalog.VerifyLauncherPackage(actual with { Sequence = 101 }, metadata, updates));
            Reject(() => ReleaseCatalog.VerifyLauncherPackage(actual with { Payload = actual.Payload with { Sha256 = new string('b', 64) } }, metadata, updates));
            Reject(() => ReleaseCatalog.VerifyLauncherPackage(actual, Sign(manifest with { Sequence = 101 }), updates));
            var gameManifest = new RuntimeUpdateManifest(1, "1.0.99", 100, "1.0.27", "mw3-local-runtime-v1", "", 500, pin,
                "copy.exe", new() { ["copy.exe"] = new(123, pin) }, new() { ["MECH3.EXE"] = new(123, pin) });
            var gameMetadata = Sign(gameManifest);
            var gameRelease = Release(GameCatalog.Mw3) with { Metadata = runtime.Metadata with { Bytes = gameMetadata.Length,
                Sha256 = Convert.ToHexString(SHA256.HashData(gameMetadata)).ToLowerInvariant() } };
            var runtimeUpdates = new RuntimeUpdates(trial, trust, trial);
            ReleaseCatalog.VerifyRuntimePackage(gameRelease, gameMetadata, runtimeUpdates);
            Reject(() => ReleaseCatalog.VerifyRuntimePackage(gameRelease with { Sequence = 101 }, gameMetadata, runtimeUpdates));
            File.WriteAllBytes(Path.Combine(trial, "online-updates.json"), JsonSerializer.SerializeToUtf8Bytes(config, Json));
            OnlineUpdateConfiguration.Read(trial);
            if (File.Exists(Path.Combine(trial, "update-trust.json"))) throw new Exception("Discovery changed installed trust.");

            File.WriteAllBytes(Path.Combine(trial, "update-trust.json"), JsonSerializer.SerializeToUtf8Bytes(trust, Json));
            string pendingFile;
            using (var service = new OnlineUpdateService(trial, trial, trial))
                pendingFile = service.PendingFile;
            var stage = Path.Combine(updates.Store, "pending-reconciliation-fixture");
            Directory.CreateDirectory(stage);
            var job = Path.Combine(stage, "job.json");
            File.WriteAllText(job, "{}");
            var resultFile = Path.Combine(stage, "result.txt");
            var sequenceFile = Path.Combine(updates.Store, "installed-sequence.json");
            void SavePlan(ReleaseCatalogDocument savedCatalog, string[] products = null)
            {
                var pending = new PendingOnlineUpdates(1, Path.TrimEndingDirectorySeparator(Path.GetFullPath(trial)),
                    config.Channel, Convert.ToBase64String(Sign(savedCatalog)),
                    products ?? new[] { GameCatalog.LauncherId }, job);
                File.WriteAllBytes(pendingFile, JsonSerializer.SerializeToUtf8Bytes(pending, Json));
            }
            void CheckPending(string name, bool expected)
            {
                var savedBytes = File.ReadAllBytes(pendingFile);
                using var service = new OnlineUpdateService(trial, trial, trial);
                if (service.HasPending != expected ||
                    (expected && !savedBytes.SequenceEqual(File.ReadAllBytes(pendingFile))))
                    throw new Exception("Launcher restart reconciliation failed: " + name);
            }
            var currentVersion = typeof(OnlineUpdateService).Assembly.GetName().Version;
            var numericVersion = currentVersion.ToString(3);
            var olderVersion = new Version(currentVersion.Major, currentVersion.Minor,
                currentVersion.Build - 1).ToString();
            var newerVersion = new Version(currentVersion.Major, currentVersion.Minor,
                currentVersion.Build + 1).ToString();
            var completedRelease = launcher;
            foreach (var test in new[]
            {
                (Name: "older running launcher", Version: newerVersion, Sequence: 100L, Pending: true),
                (Name: "missing installed sequence", Version: numericVersion, Sequence: 0L, Pending: true),
                (Name: "older installed sequence", Version: numericVersion, Sequence: 99L, Pending: true),
                (Name: "newer running launcher", Version: olderVersion, Sequence: 100L, Pending: false),
                (Name: "newer installed sequence", Version: numericVersion, Sequence: 101L, Pending: false),
                (Name: "four-part numeric version", Version: currentVersion.ToString(), Sequence: 100L, Pending: false),
                (Name: "invalid numeric version", Version: "invalid", Sequence: 100L, Pending: true),
                (Name: "missing numeric version", Version: (string)null, Sequence: 100L, Pending: true),
                (Name: "preview assembly matches numeric release", Version: numericVersion, Sequence: 100L, Pending: false)
            })
            {
                var savedMetadata = Sign(manifest with { Version = test.Version });
                File.WriteAllBytes(Path.Combine(stage, "update.ccupdate"), savedMetadata);
                completedRelease = launcher with
                {
                    Version = test.Version, NumericVersion = test.Version, DisplayVersion = test.Version + "-preview",
                    Metadata = new("https://updates.example.test/" + test.Version + ".ccupdate",
                        test.Version + ".ccupdate", savedMetadata.Length,
                        Convert.ToHexString(SHA256.HashData(savedMetadata)).ToLowerInvariant()),
                    Payload = launcher.Payload with
                    {
                        Url = "https://updates.example.test/" + test.Version + ".zip",
                        Filename = test.Version + ".zip"
                    }
                };
                if (test.Sequence == 0) File.Delete(sequenceFile);
                else File.WriteAllText(sequenceFile, JsonSerializer.Serialize(test.Sequence));
                File.WriteAllText(resultFile, "Core Critical updated to " + test.Version);
                SavePlan(document with { Releases = new[] { completedRelease } });
                CheckPending(test.Name, test.Pending);
            }

            // A signed null entry reaches a NullReferenceException outside the old catch filter.
            var unexpectedFailure = document with { Releases = new OnlineRelease[] { null } };
            try
            {
                Verify(unexpectedFailure);
                throw new Exception("The unexpected-exception fixture no longer raises NullReferenceException.");
            }
            catch (NullReferenceException) { }
            SavePlan(unexpectedFailure);
            CheckPending("unexpected verifier exception leaves the plan unchanged", true);

            var completedCatalog = document with { Releases = new[] { completedRelease } };
            File.Delete(resultFile);
            SavePlan(completedCatalog);
            CheckPending("missing helper receipt", true);
            File.WriteAllText(resultFile, "Core Critical updated to " + numericVersion);
            SavePlan(document with { Releases = new[] { completedRelease, runtime } },
                new[] { GameCatalog.LauncherId, GameCatalog.Mw3 });
            CheckPending("saved game update survives restart", true);
            SavePlan(completedCatalog);
            using (var workflowLock = new FileStream(Path.Combine(Path.GetDirectoryName(pendingFile), ".workflow-lock"),
                FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
                CheckPending("busy workflow lock leaves the plan unchanged", true);
            CheckPending("completed update clears after the workflow lock is released", false);
        }
        finally { Directory.Delete(trial, true); }
        Console.WriteLine("Online update contract checks passed: signed catalog, freshness, product/channel/host policy, dependency order, package cross-checks, independent configuration and restart reconciliation.");
    }
}
