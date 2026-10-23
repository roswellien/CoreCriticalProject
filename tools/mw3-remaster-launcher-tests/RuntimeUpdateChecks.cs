using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class RuntimeUpdateChecks
{
    private static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };
    private static UpdateFile Pin(string path) => new(new FileInfo(path).Length, Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))));

    // A process fixture exercises the preparation protocol; these files are authored text, not a game runtime.
    public static async Task GenerateFixture(string[] arguments)
    {
        string Arg(string name) => arguments[Array.IndexOf(arguments, name) + 1];
        var version = Arg("--version");
        if (version == "fail") { Environment.ExitCode = 7; return; }
        if (version == "cancel") await Task.Delay(TimeSpan.FromSeconds(30));
        WriteRuntime(Arg("--output"));
        if (version == "invalid") File.AppendAllText(Path.Combine(Arg("--output"), "host.exe"), "corrupt");
    }

    private static void WriteRuntime(string root)
    {
        Directory.CreateDirectory(root);
        // Authored executable-format fixture, never executed as a game.
        File.Copy(Path.Combine(AppContext.BaseDirectory, "LauncherChecks.exe"), Path.Combine(root, "host.exe"), true);
        File.WriteAllText(Path.Combine(root, "coordinator.py"), "authored coordinator fixture");
        File.WriteAllText(Path.Combine(root, "python.exe"), "authored interpreter path fixture");
        var host = Pin(Path.Combine(root, "host.exe"));
        File.WriteAllText(Path.Combine(root, "profile.json"), JsonSerializer.Serialize(new
        {
            native = new { installation_layout = 1, executable = "@runtime/host.exe", executable_sha256 = host.Sha256,
                runtime_environment = new { MW34_SEED = "host", MW34_STARTUP = "loader" } }
        }));
        var files = new[] { "host.exe", "coordinator.py", "python.exe", "profile.json" }.ToDictionary(n => n, n => Pin(Path.Combine(root, n)));
        File.WriteAllText(Path.Combine(root, "runtime.json"), JsonSerializer.Serialize(new
        { schema_version = 1, profile = "profile.json", coordinator = "coordinator.py", python = "python.exe", files }, Json));
    }

    public static async Task Run()
    {
        var trial = Path.Combine(Path.GetTempPath(), "MW3-update-checks-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(trial);
        try
        {
            var app = Path.Combine(trial, "App");
            var data = Path.Combine(trial, "UserData");
            var game = Path.Combine(trial, "OriginalGame");
            Directory.CreateDirectory(app); Directory.CreateDirectory(game);
            File.WriteAllText(Path.Combine(game, "MECH3.EXE"), "AUTHORED original input fixture");
            WriteRuntime(Path.Combine(app, "Runtime"));
            using var rsa = RSA.Create(3072);
            var trust = new RuntimeUpdateTrust("", new() { ["fixture"] = rsa.ExportSubjectPublicKeyInfoPem() });
            var updates = new RuntimeUpdates(app, trust, data);
            var archive = Path.Combine(trial, "source-tools.zip");
            var toolFiles = new Dictionary<string, UpdateFile>();
            // The test apphost needs its own managed dependencies; the fixture mode runs before all checks.
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Create))
                foreach (var file in Directory.GetFiles(AppContext.BaseDirectory).Where(p =>
                    p.EndsWith(".dll", StringComparison.OrdinalIgnoreCase) || p.EndsWith(".json", StringComparison.OrdinalIgnoreCase) ||
                    Path.GetFileName(p).Equals("LauncherChecks.exe", StringComparison.OrdinalIgnoreCase)))
                {
                    var name = Path.GetFileName(file);
                    zip.CreateEntryFromFile(file, name);
                    toolFiles[name] = Pin(file);
                }
            var package = Pin(archive);
            var manifest = new RuntimeUpdateManifest(1, "v1", 1, "1.0.0", "mw3-local-runtime-v1", "", package.Bytes, package.Sha256,
                "LauncherChecks.exe", toolFiles, new() { ["MECH3.EXE"] = Pin(Path.Combine(game, "MECH3.EXE")) });
            byte[] Sign(RuntimeUpdateManifest value)
            {
                var payload = JsonSerializer.SerializeToUtf8Bytes(value, Json);
                return JsonSerializer.SerializeToUtf8Bytes(new { key_id = "fixture", payload = Convert.ToBase64String(payload),
                    signature = Convert.ToBase64String(rsa.SignData(payload, HashAlgorithmName.SHA256, RSASignaturePadding.Pss)) });
            }
            var signer = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../mw3-remaster-launcher/sign_runtime_update.ps1"));
            if (!File.Exists(signer))
                signer = Path.GetFullPath("tools/mw3-remaster-launcher/sign_runtime_update.ps1");
            if (!File.Exists(signer)) throw new Exception("Missing release signing tool.");
            var privateKey = Path.Combine(trial, "fixture-private-key.pem");
            var manifestFile = Path.Combine(trial, "manifest.json");
            var envelopeFile = Path.Combine(trial, "signed.mw3update");
            File.WriteAllText(privateKey, rsa.ExportPkcs8PrivateKeyPem());
            File.WriteAllText(manifestFile, JsonSerializer.Serialize(manifest, Json));
            var signInfo = new System.Diagnostics.ProcessStartInfo("pwsh") { UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (var value in new[] { "-NoProfile", "-File", signer, "-Manifest", manifestFile, "-SigningKey", privateKey,
                "-KeyId", "fixture", "-OutputFile", envelopeFile }) signInfo.ArgumentList.Add(value);
            using (var signing = System.Diagnostics.Process.Start(signInfo)!)
            {
                var signingOut = signing.StandardOutput.ReadToEndAsync();
                var signingError = signing.StandardError.ReadToEndAsync();
                await signing.WaitForExitAsync();
                await Task.WhenAll(signingOut, signingError);
                if (signing.ExitCode != 0) throw new Exception("Release signing tool failed: " + signingError.Result);
            }
            updates.Verify(File.ReadAllBytes(envelopeFile));
            async Task Reject(Func<Task> operation)
            {
                try { await operation(); }
                catch (Exception error) when (error is IOException or InvalidDataException or CryptographicException or OperationCanceledException) { return; }
                throw new Exception("Invalid runtime update was accepted.");
            }
            void RejectEnvelope(byte[] envelope) => Reject(() => { updates.Verify(envelope); return Task.CompletedTask; }).GetAwaiter().GetResult();
            var tampered = JsonNode.Parse(Sign(manifest))!;
            tampered["payload"] = Convert.ToBase64String(Encoding.UTF8.GetBytes("{}"));
            RejectEnvelope(Encoding.UTF8.GetBytes(tampered.ToJsonString()));
            tampered = JsonNode.Parse(Sign(manifest))!; tampered["key_id"] = "unknown";
            RejectEnvelope(Encoding.UTF8.GetBytes(tampered.ToJsonString()));
            RejectEnvelope(Sign(manifest with { MinimumLauncherVersion = "999.0.0" }));
            RejectEnvelope(Sign(manifest with { PreparationContract = "unknown-service" }));
            RejectEnvelope(Sign(manifest with { PreparationContract = "mw3-source-runtime-v2" })); // incomplete original-input set
            RejectEnvelope(Sign(manifest with { Files = new() { ["../escape.exe"] = package } }));
            RejectEnvelope(Sign(manifest with { PackageUrl = "http://example.invalid/update.zip" }));
            await Reject(() => updates.PrepareAsync(updates.Verify(Sign(manifest with { PackageSha256 = new string('0', 64) })), game, archive));
            var extraArchive = Path.Combine(trial, "extra-entry.zip");
            using (var zip = ZipFile.Open(extraArchive, ZipArchiveMode.Create))
            using (var writer = new StreamWriter(zip.CreateEntry("../escape.txt").Open())) writer.Write("authored traversal fixture");
            var extraPin = Pin(extraArchive);
            await Reject(() => updates.PrepareAsync(updates.Verify(Sign(manifest with
            { PackageBytes = extraPin.Bytes, PackageSha256 = extraPin.Sha256 })), game, extraArchive));
            if (File.Exists(Path.Combine(trial, "escape.txt"))) throw new Exception("Update archive escaped staging.");
            var original = File.ReadAllText(Path.Combine(game, "MECH3.EXE"));
            File.AppendAllText(Path.Combine(game, "MECH3.EXE"), "bad");
            await Reject(() => updates.PrepareAsync(updates.Verify(Sign(manifest)), game, archive));
            File.WriteAllText(Path.Combine(game, "MECH3.EXE"), original);
            foreach (var version in new[] { "fail", "invalid" })
            {
                await Reject(() => updates.PrepareAsync(updates.Verify(Sign(manifest with { Version = version })), game, archive));
                if (updates.State().Active != null) throw new Exception("Failed preparation changed the selected runtime.");
            }
            var cancelledUpdate = updates.Verify(Sign(manifest with { Version = "cancel" }));
            using (var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(2)))
                await Reject(() => updates.PrepareAsync(cancelledUpdate, game, archive, cancellation: cancellation.Token));
            var cancelledWork = Path.Combine(updates.Store, ".preparing-" + cancelledUpdate.ManifestSha256[..24]);
            var cachedArchive = Pin(Path.Combine(cancelledWork, "source-tools.zip"));
            using (var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(2)))
                await Reject(() => updates.PrepareAsync(cancelledUpdate, game, archive, cancellation: cancellation.Token));
            if (Pin(Path.Combine(cancelledWork, "source-tools.zip")) != cachedArchive ||
                Directory.GetFiles(cancelledWork, "prepare-*.stdout.log").Length != 2)
                throw new Exception("Interrupted preparation did not retain its verified tools and separate attempt logs.");
            var unexpectedTool = Path.Combine(cancelledWork, "tools", "unregistered.dll");
            File.WriteAllText(unexpectedTool, "authored unregistered tool fixture");
            await Reject(() => updates.PrepareAsync(cancelledUpdate, game, archive));
            File.Delete(unexpectedTool);
            // Mutation of a caller-visible dictionary must not change the signed tool/input instructions.
            var verified = updates.Verify(Sign(manifest));
            verified.Manifest.Files["unexpected.txt"] = package;
            await updates.PrepareAsync(verified, game, archive);
            if (updates.State().Active != "v1" || NativeRuntimeLayout.FindInstalled(app, data)!.Root != Path.Combine(updates.Store, "versions", "v1"))
                throw new Exception("Prepared runtime was not selected by installed game discovery.");
            var bundledPath = Path.Combine(app, "Runtime", "runtime.json");
            var bundledBytes = File.ReadAllBytes(bundledPath);
            var bundledManifest = JsonNode.Parse(bundledBytes)!;
            bundledManifest["supersedes_runtime_versions"] = new JsonArray("older-release");
            File.WriteAllText(bundledPath, bundledManifest.ToJsonString());
            if (RuntimeUpdates.SelectedRoot(app, data) == null)
                throw new Exception("A future runtime update was hidden by an installer.");
            bundledManifest["supersedes_runtime_versions"] = new JsonArray("v1");
            File.WriteAllText(bundledPath, bundledManifest.ToJsonString());
            if (NativeRuntimeLayout.FindInstalled(app, data)!.Root != Path.Combine(app, "Runtime") || updates.State().Active != "v1")
                throw new Exception("Full installer did not supersede only the retired runtime without deleting its selection.");
            File.WriteAllBytes(bundledPath, bundledBytes);
            var selectionFile = Path.Combine(updates.Store, "selection.json");
            // Model power loss between directory publication and pointer activation.
            File.Delete(selectionFile);
            await updates.PrepareAsync(updates.Verify(Sign(manifest)), game, archive);
            if (updates.State().Active != "v1") throw new Exception("Interrupted activation could not resume.");
            var selectionBytes = File.ReadAllBytes(selectionFile);
            updates.Rollback();
            if (updates.State().Active != null || NativeRuntimeLayout.FindInstalled(app, data)!.Root != Path.Combine(app, "Runtime"))
                throw new Exception("Rollback to the included runtime failed.");
            File.WriteAllBytes(selectionFile, selectionBytes);
            await Reject(() => updates.PrepareAsync(updates.Verify(Sign(manifest)), game, archive));
            await updates.PrepareAsync(updates.Verify(Sign(manifest with { Version = "v2", Sequence = 2 })), game, archive);
            updates.Rollback();
            if (updates.State().Active != "v1" || updates.State().HighestSequence != 2) throw new Exception("Rollback lost update downgrade protection.");
            File.AppendAllText(Path.Combine(updates.Store, "versions", "v2", "host.exe"), "bad");
            await Reject(() => { updates.Rollback(); return Task.CompletedTask; });
            if (updates.State().Active != "v1") throw new Exception("Corrupt rollback target was selected.");
            using (var locked = new FileStream(Path.Combine(updates.Store, ".update-lock"), FileMode.Open, FileAccess.ReadWrite, FileShare.None))
                await Reject(() => updates.PrepareAsync(updates.Verify(Sign(manifest with { Version = "v3", Sequence = 3 })), game, archive));
            if (File.ReadAllText(Path.Combine(game, "MECH3.EXE")) != original) throw new Exception("Original input changed.");
            Console.WriteLine("Signed runtime update checks passed: real preparation child process, activation/discovery, tampering, unknown keys/services, source integrity, failed output, cancellation, downgrade rejection, rollback and locking. Authored fixtures only; no gameplay credit.");
        }
        finally { Directory.Delete(trial, true); }
    }
}
