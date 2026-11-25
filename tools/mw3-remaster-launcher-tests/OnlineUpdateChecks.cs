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
            void SavePlan(ReleaseCatalogDocument savedCatalog, string[] products = null,
                bool includeJob = true)
            {
                var application = Path.TrimEndingDirectorySeparator(Path.GetFullPath(trial));
                var pending = new PendingOnlineUpdates(1, application,
                    config.Channel, Convert.ToBase64String(Sign(savedCatalog)),
                    products ?? new[] { GameCatalog.LauncherId }, includeJob ? job : null);
                File.WriteAllBytes(pendingFile, JsonSerializer.SerializeToUtf8Bytes(pending, Json));
            }
            void CheckPending(string name, bool expected)
            {
                var savedBytes = File.ReadAllBytes(pendingFile);
                using var service = new OnlineUpdateService(trial, trial, trial);
                var planChanged = expected &&
                    !savedBytes.SequenceEqual(File.ReadAllBytes(pendingFile));
                if (service.HasPending != expected || planChanged)
                    throw new Exception("Launcher restart reconciliation failed: " + name);
            }
            void CheckInstallRefuses(string name)
            {
                var savedBytes = File.ReadAllBytes(pendingFile);
                using var service = new OnlineUpdateService(trial, trial, trial);
                Reject(() => service.InstallAsync(null, CancellationToken.None)
                    .GetAwaiter().GetResult());
                var planUnchanged = File.Exists(pendingFile) &&
                    savedBytes.SequenceEqual(File.ReadAllBytes(pendingFile));
                if (!planUnchanged)
                    throw new Exception("Install cleared launcher state without proof: " + name);
            }
            void CheckDiscardRefuses(string name)
            {
                var savedBytes = File.ReadAllBytes(pendingFile);
                using var service = new OnlineUpdateService(trial, trial, trial);
                if (service.CanDiscardLauncherUpdate())
                    throw new Exception("Launcher discard should be disabled: " + name);
                Reject(() => service.DiscardPendingLauncherUpdate());
                var planUnchanged = File.Exists(pendingFile) &&
                    savedBytes.SequenceEqual(File.ReadAllBytes(pendingFile));
                if (!planUnchanged)
                    throw new Exception("Refused discard changed the saved plan: " + name);
            }
            string PreviousVersion(Version version)
            {
                if (version.Build > 0)
                    return new Version(version.Major, version.Minor, version.Build - 1).ToString();
                if (version.Minor > 0)
                    return new Version(version.Major, version.Minor - 1, 0).ToString();
                if (version.Major > 0)
                    return new Version(version.Major - 1, 0, 0).ToString();
                return "0.0.0";
            }
            foreach (var zeroBuildVersion in new[] { "1.1.0", "2.0.0", "0.0.0" })
            {
                var version = Version.Parse(zeroBuildVersion);
                if (Version.Parse(PreviousVersion(version)) > version)
                    throw new Exception("The earlier-version fixture is newer than its input.");
            }
            var currentVersion = typeof(OnlineUpdateService).Assembly.GetName().Version;
            var numericVersion = currentVersion.ToString(3);
            var olderVersion = PreviousVersion(currentVersion);
            var newerVersion = new Version(currentVersion.Major, currentVersion.Minor,
                currentVersion.Build + 1).ToString();
            var completedRelease = launcher;
            foreach (var test in new[]
            {
                (Name: "older running launcher", Version: newerVersion, Sequence: 100L, Pending: true),
                (Name: "missing installed sequence", Version: numericVersion, Sequence: 0L, Pending: true),
                (Name: "older installed sequence", Version: numericVersion, Sequence: 99L, Pending: true),
                (Name: "running launcher meets earlier release", Version: olderVersion,
                    Sequence: 100L, Pending: false),
                (Name: "newer installed sequence", Version: numericVersion, Sequence: 101L, Pending: false),
                (Name: "four-part numeric version", Version: currentVersion.ToString(),
                    Sequence: 100L, Pending: false),
                (Name: "catalog rejects invalid numeric version", Version: "invalid",
                    Sequence: 100L, Pending: true),
                (Name: "catalog rejects missing numeric version", Version: (string)null,
                    Sequence: 100L, Pending: true),
                (Name: "preview assembly matches numeric release", Version: numericVersion,
                    Sequence: 100L, Pending: false)
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
                var numericVersionValid = Version.TryParse(test.Version, out var releaseVersion);
                var releaseAlreadyCurrent = numericVersionValid &&
                    currentVersion >= releaseVersion;
                if (test.Pending && releaseAlreadyCurrent)
                    CheckInstallRefuses(test.Name);
                if (numericVersionValid && currentVersion < releaseVersion)
                    CheckDiscardRefuses(test.Name);
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
            CheckInstallRefuses("missing helper receipt");
            File.WriteAllText(resultFile, "Core Critical updated to " + numericVersion);

            var metadataFile = Path.Combine(stage, "update.ccupdate");
            var originalMetadata = File.ReadAllBytes(metadataFile);
            File.AppendAllText(metadataFile, "tampered");
            SavePlan(completedCatalog);
            CheckPending("helper metadata must match the signed catalog", true);
            CheckInstallRefuses("tampered helper metadata");
            File.WriteAllBytes(metadataFile, originalMetadata);

            SavePlan(completedCatalog, includeJob: false);
            CheckPending("missing launcher job", true);
            CheckInstallRefuses("missing launcher job");

            var expiredCatalog = completedCatalog with
            {
                IssuedUtc = now.AddDays(-3), ExpiresUtc = now.AddDays(-2)
            };
            Reject(() => Verify(expiredCatalog));
            SavePlan(expiredCatalog);
            var defaultSettings = new LauncherSettings();
            if (defaultSettings.AutomaticUpdateChecks)
                throw new Exception("The startup fixture no longer represents default settings.");
            // This is the same offline Task.Run entry point called before the UI preference guard.
            OnlineUpdateService.ReconcileAtStartupAsync(trial, defaultSettings.GamePath, trial)
                .GetAwaiter().GetResult();
            if (File.Exists(pendingFile))
                throw new Exception("Default startup retained a proven expired-catalog update.");

            var unsignedEnvelope = JsonSerializer.Deserialize<Dictionary<string, string>>(
                Sign(expiredCatalog));
            unsignedEnvelope["signature"] = Convert.ToBase64String(new byte[key.KeySize / 8]);
            SavePlan(expiredCatalog);
            var unsignedPlan = JsonSerializer.Deserialize<PendingOnlineUpdates>(
                File.ReadAllBytes(pendingFile), Json);
            File.WriteAllBytes(pendingFile, JsonSerializer.SerializeToUtf8Bytes(unsignedPlan with
            {
                CatalogEnvelope = Convert.ToBase64String(
                    JsonSerializer.SerializeToUtf8Bytes(unsignedEnvelope))
            }, Json));
            CheckPending("expired catalog still requires a valid signature", true);
            CheckInstallRefuses("invalid catalog signature");
            CheckDiscardRefuses("invalid catalog signature");

            // Stage after construction so InstallAsync must do the same offline proof itself.
            File.Delete(pendingFile);
            using (var service = new OnlineUpdateService(trial, trial, trial))
            {
                SavePlan(expiredCatalog);
                var restart = service.InstallAsync(null, CancellationToken.None)
                    .GetAwaiter().GetResult();
                if (restart || service.HasPending)
                    throw new Exception("Install retained a proven local launcher update.");
            }

            SavePlan(document with { Releases = new[] { completedRelease, runtime } },
                new[] { GameCatalog.LauncherId, GameCatalog.Mw3 });
            var mixedPlan = JsonSerializer.Deserialize<PendingOnlineUpdates>(
                File.ReadAllBytes(pendingFile), Json);
            using (var service = new OnlineUpdateService(trial, trial, trial))
            {
                var remaining = JsonSerializer.Deserialize<PendingOnlineUpdates>(
                    File.ReadAllBytes(pendingFile), Json);
                var gamePlanPreserved = service.HasPending &&
                    remaining.Products.SequenceEqual(new[] { GameCatalog.Mw3 }) &&
                    remaining.LauncherJob == null &&
                    remaining.Application == mixedPlan.Application &&
                    remaining.Channel == mixedPlan.Channel &&
                    remaining.CatalogEnvelope == mixedPlan.CatalogEnvelope;
                if (!gamePlanPreserved)
                    throw new Exception("Reconciliation did not preserve the remaining game plan.");
            }
            CheckPending("remaining game plan is valid and unchanged on the next start", true);

            File.WriteAllText(resultFile, "Launcher update failed: authored failure fixture");
            SavePlan(completedCatalog);
            CheckPending("failed helper receipt", true);
            CheckInstallRefuses("failed helper receipt with sufficient installed sequence");
            // Standalone setup does not write helper sequence or receipt state.
            File.Delete(sequenceFile);
            SavePlan(completedCatalog);
            CheckPending("installer repair cannot masquerade as helper success", true);
            CheckInstallRefuses("failed helper after installer repair");
            SavePlan(document with { Releases = new[] { completedRelease, runtime } },
                new[] { GameCatalog.LauncherId, GameCatalog.Mw3 });
            using (var service = new OnlineUpdateService(trial, trial, trial))
            {
                if (!service.CanDiscardLauncherUpdate() || !service.DiscardPendingLauncherUpdate())
                    throw new Exception("Cannot discard a repaired launcher's stale update.");
                var remaining = JsonSerializer.Deserialize<PendingOnlineUpdates>(
                    File.ReadAllBytes(pendingFile), Json);
                var failedReceiptPreserved = File.ReadAllText(resultFile) ==
                    "Launcher update failed: authored failure fixture";
                if (!remaining.Products.SequenceEqual(new[] { GameCatalog.Mw3 }) ||
                    remaining.LauncherJob != null || File.Exists(sequenceFile) ||
                    !failedReceiptPreserved)
                    throw new Exception("Discard changed game selection or success evidence.");
                CheckDiscardRefuses("game-only plan");
                SavePlan(completedCatalog);
                if (!service.CanDiscardLauncherUpdate() ||
                    !service.DiscardPendingLauncherUpdate() || service.HasPending)
                    throw new Exception("Discard did not clear the launcher-only failed attempt.");
            }

            File.WriteAllText(resultFile, "Core Critical updated to " + numericVersion);
            File.WriteAllText(sequenceFile, JsonSerializer.Serialize(100L));
            SavePlan(completedCatalog);
            var workflowDirectory = Path.GetDirectoryName(pendingFile);
            var workflowLockFile = Path.Combine(workflowDirectory, ".workflow-lock");
            using (var workflowLock = new FileStream(workflowLockFile,
                FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
                CheckPending("busy workflow lock leaves the plan unchanged", true);
            CheckPending("completed update clears after the workflow lock is released", false);
        }
        finally { Directory.Delete(trial, true); }
        Console.WriteLine("Online update contract checks passed: signed catalog, freshness, product/channel/host policy, dependency order, package cross-checks, independent configuration and restart reconciliation.");
    }
}
