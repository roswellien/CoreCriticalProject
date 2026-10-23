using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using MW3RemasterLauncher.Core;

static class UniversalLauncherChecks
{
    private static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };
    private static void Reject(Action action)
    {
        try { action(); } catch (Exception e) when (e is InvalidDataException or JsonException) { return; }
        throw new Exception("Invalid cross-product input was accepted.");
    }
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "CoreCritical-checks-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var mw3 = new PackManager(root);
            var pm = new PackManager(root, "mw3pm");
            if (mw3.ModsRoot != Path.Combine(root, "mods") || mw3.ModsRoot == pm.ModsRoot) throw new Exception("Game stores are not isolated or MW3 storage moved.");
            foreach (var game in GameCatalog.Games)
            {
                if (game.UpdateExtension != "." + game.FileStem + "update" || game.PackExtension != "." + game.FileStem + "pack") throw new Exception("Wrong extension mapping.");
            }
            Reject(() => GameCatalog.Get("unknown"));
            Reject(() => GameCatalog.RequirePackTarget("mw3pm", "mw3"));
            Reject(() => GameCatalog.RequirePackTarget("mw3", "mw3", "wrong.mw4pack"));
            string Pack(string stem, string game)
            {
                var file = Path.Combine(root, stem + ".zip");
                using var zip = ZipFile.Open(file, ZipArchiveMode.Create);
                using var output = zip.CreateEntry("pack.json").Open();
                var metadata = new Dictionary<string, object> { ["schema_version"] = 1, ["id"] = "fixture.shared-id", ["name"] = "Authored fixture" };
                if (game != null) metadata["game_id"] = game;
                JsonSerializer.Serialize(output, metadata); return file;
            }
            var old = mw3.InstallPack(Pack("legacy", null));
            if (old.GameId != "mw3") throw new Exception("Legacy MW3 pack migration failed.");
            var pmArchive = Pack("moon", "mw3pm");
            Reject(() => mw3.InstallPack(pmArchive));
            var installed = pm.InstallPack(pmArchive);
            if (installed.DirectoryPath == old.DirectoryPath) throw new Exception("Matching IDs collided across games.");
            var renamed = Path.Combine(root, "renamed.mw3pack"); File.Copy(pmArchive, renamed);
            Reject(() => mw3.InstallPack(renamed));
            if (!File.Exists(Path.Combine(old.DirectoryPath, "pack.json"))) throw new Exception("Rejected import changed the old game library.");
            // Discovery must also reject a wrong-game manifest copied into an existing library.
            var wrong = Path.Combine(mw3.ModsRoot, "fixture.other"); Directory.CreateDirectory(wrong);
            File.WriteAllText(Path.Combine(wrong, "pack.json"), """{"schema_version":1,"id":"fixture.other","game_id":"mw4"}""");
            mw3.RefreshPacks();
            if (mw3.Packs.Count != 1 || mw3.DiscoveryErrors.Count != 1) throw new Exception("Wrong-game installed content was exposed.");

            var app = Path.Combine(root, "app"); Directory.CreateDirectory(app);
            using var rsa = RSA.Create(3072);
            var trust = new RuntimeUpdateTrust("", new() { ["fixture"] = rsa.ExportSubjectPublicKeyInfoPem() });
            var updates = new LauncherUpdates(app, trust, root);
            byte[] Sign(object manifest)
            {
                var payload = JsonSerializer.SerializeToUtf8Bytes(manifest, Json);
                return JsonSerializer.SerializeToUtf8Bytes(new { key_id = "fixture", payload = Convert.ToBase64String(payload),
                    signature = Convert.ToBase64String(rsa.SignData(payload, HashAlgorithmName.SHA256, RSASignaturePadding.Pss)) });
            }
            var archive = Path.Combine(root, "launcher.zip");
            using (var zip = ZipFile.Open(archive, ZipArchiveMode.Create))
            { using var stream = zip.CreateEntry("CoreCriticalSetup.exe").Open(); stream.Write("Authored unsigned fixture"u8); }
            UpdateFile Pin(string path) => new(new FileInfo(path).Length, Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))));
            var pin = Pin(archive);
            var manifest = new LauncherUpdateManifest(1, "corecritical", "launcher-inno-v1", "99.0.0", 1, "1.0.19", pin.Bytes, pin.Sha256,
                new("Authored unsigned fixture"u8.Length, Convert.ToHexString(SHA256.HashData("Authored unsigned fixture"u8.ToArray()))));
            var verified = updates.Verify(Sign(manifest));
            Reject(() => updates.Verify(Sign(manifest with { ProductId = "mw3" })));
            Reject(() => updates.Verify(Sign(manifest with { UpdateType = "run-anything" })));
            Reject(() => updates.Verify(Sign(manifest with { Version = "1.0.0" })));
            Reject(() => updates.Verify(Sign(manifest with { MinimumLauncherVersion = "999.0.0" })));
            Reject(() => updates.Verify(Sign(manifest with { Sequence = 0 })));
            Reject(() => updates.Verify(Sign(manifest with { PackageBytes = long.MaxValue })));
            var untrusted = new LauncherUpdates(app, new("", new()), root);
            Reject(() => untrusted.Verify(Sign(manifest)));
            var tampered = Sign(manifest); tampered[^4] ^= 1;
            try { updates.Verify(tampered); throw new Exception("Tampered envelope accepted."); }
            catch (Exception e) when (e is JsonException or FormatException or InvalidDataException) { }
            Reject(() => new RuntimeUpdates(app, trust, root).Verify(Sign(manifest)));
            var runtime = new RuntimeUpdateManifest(1, "fixture-v1", 1, "1.0.0", "mw3-local-runtime-v1", "", 1, new string('0', 64),
                "prepare.exe", new() { ["prepare.exe"] = new(1, new string('0', 64)) }, new() { ["MECH3.EXE"] = new(1, new string('0', 64)) });
            var runtimeUpdates = new RuntimeUpdates(app, trust, root);
            Reject(() => runtimeUpdates.Verify(Sign(runtime with { GameId = "mw3pm" })));
            Reject(() => updates.Verify(Sign(runtime)));
            var legacy = System.Text.Json.Nodes.JsonNode.Parse(JsonSerializer.Serialize(runtime, Json))!.AsObject();
            legacy.Remove("game_id");
            if (runtimeUpdates.Verify(Sign(legacy)).Manifest.GameId != "mw3") throw new Exception("Old signed MW3 metadata lost its target default.");
            // No Windows-signed release required: an unsigned installer must never reach application mutation.
            Reject(() => updates.Stage(verified, archive));
            if (Directory.GetFileSystemEntries(app).Length != 0) throw new Exception("Rejected launcher update modified application files.");
            // Exercise real Windows trust and successful staging using an existing Microsoft-signed tool.
            // It is never executed as an installer. No release certificate or network credential is used.
            var signedTool = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Windows Kits/10/bin/10.0.26100.0/x64/signtool.exe");
            if (File.Exists(signedTool))
            {
                foreach (var file in new[] { "Core Critical Launcher.exe", "Core Critical Launcher.dll", "Core Critical Launcher.deps.json", "Core Critical Launcher.runtimeconfig.json" })
                {
                    var source = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../mw3-remaster-launcher/bin/Debug/net8.0-windows", file));
                    if (!File.Exists(source)) source = Path.Combine(AppContext.BaseDirectory, file);
                    File.Copy(source, Path.Combine(app, file));
                }
                File.WriteAllText(Path.Combine(app, "launcher-installation.json"), "{}");
                var signedZip = Path.Combine(root, "signed-fixture.zip");
                using (var zip = ZipFile.Open(signedZip, ZipArchiveMode.Create)) zip.CreateEntryFromFile(signedTool, "CoreCriticalSetup.exe");
                var zipPin = Pin(signedZip);
                var signed = updates.Verify(Sign(manifest with { PackageBytes = zipPin.Bytes, PackageSha256 = zipPin.Sha256, Installer = Pin(signedTool) }));
                var job = updates.Stage(signed, signedZip);
                if (!File.Exists(job) || !File.Exists(Path.Combine(Path.GetDirectoryName(job)!, "helper", "Core Critical Launcher.exe")))
                    throw new Exception("Verified updater staging did not produce its helper.");
                Console.WriteLine("Windows trust and staging passed with an existing Microsoft-signed tool; no installer was executed.");
            }
            Directory.CreateDirectory(updates.Store);
            File.WriteAllText(Path.Combine(updates.Store, "installed-sequence.json"), "5");
            Reject(() => updates.Verify(Sign(manifest)));
            if (Directory.GetFiles(root, "*.pem", SearchOption.AllDirectories).Length != 0) throw new Exception("A test private key was persisted.");
            Console.WriteLine("Core Critical/game identities, extension and library isolation, legacy MW3 packs, signed launcher targeting, downgrade/size/trust rejection and unsigned installer preservation passed.");
        }
        finally { Directory.Delete(root, true); }
    }
}
