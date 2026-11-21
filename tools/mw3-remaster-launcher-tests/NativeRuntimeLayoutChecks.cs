using System.IO;
using System.Reflection;
using System.Text;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class NativeRuntimeLayoutChecks
{
    /// <summary>Test-only transport through production readers and the sole argv planner; never launch the payload.</summary>
    public static void RunMw3ReStagePlan(string payload, string gameDirectory, string dataRoot, string profileId)
    {
        var contract = Mw3ReRuntimeContract.ReadStructure(payload);
        var options = Mw3RePlanningProfile.Read(contract);
        var request = Mw3ReLaunchRequest.Create(contract, options, gameDirectory, dataRoot, profileId);
        Console.WriteLine(RunMw3RePlanner(request).ToJsonString());
    }

    public static void Run()
    {
        var app = Path.Combine(Path.GetTempPath(), "MW3 installed layout " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(app);
        try
        {
            var executable = Path.Combine(AppContext.BaseDirectory, "LauncherChecks.exe");
            NativeRuntimeLayout.ValidateLaunchExecutable(executable);
            var libraryBytes = File.ReadAllBytes(executable);
            var peOffset = BitConverter.ToInt32(libraryBytes, 60);
            var characteristics = peOffset + 22;
            libraryBytes[characteristics + 1] |= 0x20; // Reproduce DLL flag in a file named .exe.
            var badExecutable = Path.Combine(app, "library-named-exe.exe");
            File.WriteAllBytes(badExecutable, libraryBytes);
            Reject(() => NativeRuntimeLayout.ValidateLaunchExecutable(badExecutable));
            File.WriteAllText(badExecutable, "authored malformed executable");
            Reject(() => NativeRuntimeLayout.ValidateLaunchExecutable(badExecutable));
            if (NativeRuntimeLayout.FindInstalled(app) != null) throw new Exception("Unexpected installed runtime.");
            var marker = Path.Combine(app, "launcher-installation.json");
            File.WriteAllText(marker, "{\"schema_version\":1,\"native_runtime\":\"requires-user-file-generation\"}");
            Reject(() => NativeRuntimeLayout.FindInstalled(app));
            File.Delete(marker);
            var root = Path.Combine(app, "Runtime");
            Directory.CreateDirectory(root);
            Reject(() => NativeRuntimeLayout.FindInstalled(app));
            var files = new Dictionary<string, object>();
            foreach (var name in new[] { "profile.json", "coordinator.py", "python.exe" })
            {
                File.WriteAllText(Path.Combine(root, name), "authored fixture " + name);
                var bytes = File.ReadAllBytes(Path.Combine(root, name));
                files[name] = new { bytes = bytes.Length, sha256 = Convert.ToHexString(SHA256.HashData(bytes)) };
            }
            var manifest = new { schema_version = 1, profile = "profile.json", coordinator = "coordinator.py", python = "python.exe", files };
            File.WriteAllText(Path.Combine(root, "runtime.json"), JsonSerializer.Serialize(manifest));
            var installed = NativeRuntimeLayout.FindInstalled(app)!;
            if (installed.Root != root || installed.Python != Path.Combine(root, "python.exe"))
                throw new Exception("Installed paths escaped the application folder.");
            var profile = """{"native":{"installation_layout":1,"executable":"@runtime/bin/host.exe","prepared_pack_roots":[1,"retained",{"path":"@runtime/content/file.bin"}],"runtime_environment":{"MW34_SEED":"host","MW34_STARTUP":"loader","MW34_VALUE":"1"}}} """;
            var resolved = JsonNode.Parse(NativeRuntimeLayout.ResolveProfile(profile, root))!;
            if (resolved["native"]!["executable"]!.GetValue<string>() != Path.Combine(root, "bin", "host.exe") ||
                resolved["native"]!["runtime_environment"]!["MW34_VALUE"]!.GetValue<string>() != "1")
                throw new Exception("Installed profile path/flag resolution failed.");
            Reject(() => NativeRuntimeLayout.ResolveProfile(profile.Replace("bin/host.exe", "../escape.exe"), root));
            Reject(() => NativeRuntimeLayout.ResolveProfile(profile.Replace("\"host\"", "\"captured\""), root));
            var manifestPath = Path.Combine(root, "runtime.json");
            var originalManifest = File.ReadAllText(manifestPath);
            var preparation = Path.Combine(app, "Preparation");
            Directory.CreateDirectory(preparation);
            File.WriteAllText(Path.Combine(preparation, "initial.mw3update"), "stale source installer metadata");
            if (!BundledPreparation.IsAvailable(app)) throw new Exception("Legacy source preparation lost.");
            var precompiled = JsonNode.Parse(originalManifest)!;
            precompiled["precompiled_runtime_version"] = 1;
            File.WriteAllText(manifestPath, precompiled.ToJsonString());
            if (!NativeRuntimeLayout.HasPrecompiledRuntime(app) || BundledPreparation.IsAvailable(app))
                throw new Exception("A precompiled install attempted legacy source generation.");
            File.WriteAllText(manifestPath, originalManifest);
            var modulePath = Path.Combine(root, "translated.dll");
            File.WriteAllText(modulePath, "authored native module fixture");
            var moduleManifest = JsonNode.Parse(originalManifest)!;
            moduleManifest["files"]!["translated.dll"] = new JsonObject
            {
                ["bytes"] = new FileInfo(modulePath).Length,
                ["sha256"] = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(modulePath)))
            };
            moduleManifest["native_modules"] = new JsonArray("translated.dll");
            File.WriteAllText(manifestPath, GameRunner.SerializeLaunchProfile(moduleManifest.AsObject()));
            NativeRuntimeLayout.FindInstalled(app);
            File.AppendAllText(modulePath, "corrupt");
            Reject(() => NativeRuntimeLayout.FindInstalled(app));
            File.Delete(modulePath);
            Reject(() => NativeRuntimeLayout.FindInstalled(app));
            File.WriteAllText(manifestPath, originalManifest);
            File.AppendAllText(installed.Coordinator, "damaged");
            Reject(() => NativeRuntimeLayout.FindInstalled(app));
            RunMw3ReStageA();
            Console.WriteLine("Installed runtime discovery, containment, integrity and startup checks passed.");
        }
        finally { Directory.Delete(app, true); }
    }
    /// <summary>Stage A routing tracer: an installed schema1 descriptor with an explicit engine tag must not remain eligible for legacy selection.</summary>
    public static void RunMw3ReStageA()
    {
        var app = Path.Combine(Path.GetTempPath(), "MW3 mw3-re routing " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(app);
        try
        {
            var root = Path.Combine(app, "Runtime");
            Directory.CreateDirectory(root);
            var files = new JsonObject();
            foreach (var name in new[] { "profile.json", "coordinator.py", "python.exe" })
            {
                File.WriteAllText(Path.Combine(root, name), "authored mw3-re routing fixture " + name);
                var bytes = File.ReadAllBytes(Path.Combine(root, name));
                files[name] = new JsonObject
                {
                    ["bytes"] = bytes.Length,
                    ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes))
                };
            }
            var manifest = new JsonObject
            {
                ["schema_version"] = 1,
                ["profile"] = "profile.json",
                ["coordinator"] = "coordinator.py",
                ["python"] = "python.exe",
                ["files"] = files
            };
            var manifestPath = Path.Combine(root, "runtime.json");
            var baseJson = manifest.ToJsonString();
            File.WriteAllText(manifestPath, baseJson);
            if (NativeRuntimeLayout.ReadRoot(root).Root != root)
                throw new Exception("Untagged schema1 descriptor no longer reads through ReadRoot.");
            if (NativeRuntimeLayout.FindInstalled(app)?.Root != root)
                throw new Exception("Untagged schema1 descriptor no longer resolves through FindInstalled.");
            if (NativeRuntimeLayout.HasPrecompiledRuntime(app))
                throw new Exception("Untagged schema1 descriptor without the flag reported a precompiled runtime.");
            File.WriteAllText(manifestPath, WithManifestFields(baseJson, "\"precompiled_runtime_version\":1"));
            if (!NativeRuntimeLayout.HasPrecompiledRuntime(app))
                throw new Exception("Untagged schema1 flagged control lost precompiled_runtime_version 1.");
            File.WriteAllText(manifestPath, baseJson);
            (string input, string field)[] engineTags =
            {
                ("engine \"mw3-re\"", "\"engine\":\"mw3-re\""),
                ("unknown engine", "\"engine\":\"not-an-installed-engine\""),
                ("null engine", "\"engine\":null"),
                ("non-string engine", "\"engine\":7"),
                ("mis-cased Engine", "\"Engine\":\"mw3-re\"")
            };
            foreach (var (input, field) in engineTags)
            {
                File.WriteAllText(manifestPath, WithManifestFields(baseJson, field));
                RejectEngineRouted("ReadRoot", input, () => NativeRuntimeLayout.ReadRoot(root));
                RejectEngineRouted("FindInstalled", input, () => NativeRuntimeLayout.FindInstalled(app));
                RejectEngineRouted("HasPrecompiledRuntime", input, () => NativeRuntimeLayout.HasPrecompiledRuntime(app));
                File.WriteAllText(manifestPath, WithManifestFields(baseJson, field, "\"precompiled_runtime_version\":1"));
                RejectEngineRouted("HasPrecompiledRuntime(flagged)", input, () => NativeRuntimeLayout.HasPrecompiledRuntime(app));
            }
            File.WriteAllText(manifestPath, baseJson);
            if (NativeRuntimeLayout.ReadRoot(root).Root != root || NativeRuntimeLayout.FindInstalled(app)?.Root != root ||
                NativeRuntimeLayout.HasPrecompiledRuntime(app))
                throw new Exception("Correctly pinned legacy profile changed after the engine routing table.");
            foreach (var duplicate in new[]
            {
                WithManifestFields(baseJson, "\"schema_version\":1"),
                WithManifestFields(baseJson, "\"note\":1", "\"note\":2"),
                WithManifestFields(baseJson, "\"data\":{\"value\":1,\"value\":2}")
            })
            {
                File.WriteAllText(manifestPath, duplicate);
                RejectLegacyJson("ReadRoot duplicate", "Duplicate JSON", () => NativeRuntimeLayout.ReadRoot(root));
                RejectLegacyJson("FindInstalled duplicate", "Duplicate JSON", () => NativeRuntimeLayout.FindInstalled(app));
                RejectLegacyJson("HasPrecompiledRuntime duplicate", "Duplicate JSON", () => NativeRuntimeLayout.HasPrecompiledRuntime(app));
            }
            File.WriteAllText(manifestPath, baseJson);
            File.WriteAllText(manifestPath, WithManifestFields(baseJson, "\"note\":\"" + new string('x', PackStorage.MaxJsonBytes) + "\""));
            RejectLegacyJson("ReadRoot size", "large", () => NativeRuntimeLayout.ReadRoot(root));
            RejectLegacyJson("HasPrecompiledRuntime size", "large", () => NativeRuntimeLayout.HasPrecompiledRuntime(app));
            File.WriteAllText(manifestPath, baseJson);
            CheckLegacyProfileRouting(root);
            CheckMw3ReIntegrityContract();
            Console.WriteLine("MW3-RE stage A installed-descriptor engine routing checks passed.");
        }
        finally { Directory.Delete(app, true); }
    }
    private static void CheckMw3ReIntegrityContract()
    {
        var root = Path.Combine(Path.GetTempPath(), "MW3 integrity contract " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "bin"));
        try
        {
            File.Copy(Path.Combine(AppContext.BaseDirectory, "LauncherChecks.exe"), Path.Combine(root, "bin", "mw3.exe"));
            File.WriteAllText(Path.Combine(root, "profile.json"), "{\"authored\":true}");
            File.WriteAllText(Path.Combine(root, "support.txt"), "authored support closure");
            File.WriteAllText(Path.Combine(root, "bin", "SDL3_sound.dll"), "authored SDL3_sound dependency fixture");
            File.WriteAllText(Path.Combine(root, "bin", "mw3indeo.exe"), "authored x86 helper pin fixture");
            var pins = new JsonObject();
            foreach (var relative in new[] { "bin/mw3.exe", "profile.json", "support.txt", "bin/SDL3_sound.dll",
                         "bin/mw3indeo.exe" })
            {
                var bytes = File.ReadAllBytes(Path.Combine(root, relative));
                pins[relative] = new JsonObject { ["bytes"] = bytes.Length, ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes)) };
            }
            var descriptor = new JsonObject
            {
                ["schema_version"] = 2, ["engine"] = "mw3-re",
                ["roles"] = new JsonObject { ["executable"] = "bin/mw3.exe", ["profile"] = "profile.json" },
                ["dependencies"] = new JsonArray("support.txt", "bin/SDL3_sound.dll", "bin/mw3indeo.exe"),
                ["files"] = pins,
                ["provenance"] = new JsonObject { ["source_commit"] = new string('a', 40), ["build_id"] = "authored-build", ["builder"] = "fixture" },
                ["capabilities"] = new JsonObject
                {
                    ["authored-capability"] = new JsonArray(1, 2),
                    ["controller-profile"] = new JsonArray(1)
                }
            };
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(descriptor));
            var before = Directory.GetFiles(root, "*", SearchOption.AllDirectories)
                .ToDictionary(path => path, path => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))));
            var type = typeof(Mw3ReRuntimeContract);
            var contract = Mw3ReRuntimeContract.ReadStructure(root);
            CheckMw3ReRequestProjection(contract);
            CheckNativePreviewProjection(contract);
            CheckPinnedProfileSnapshot(root);
            CheckMw3RePlanningProfile(root);
            if (!contract.SupportsControllerProfiles)
                throw new Exception("Runtime controller-profile capability was not recognized.");
            if (contract.Root != Path.GetFullPath(root) || contract.Executable != Path.Combine(root, "bin", "mw3.exe"))
                throw new Exception("Integrity snapshot did not preserve its root/executable identity.");
            if (!contract.Dependencies.Contains("bin/SDL3_sound.dll", StringComparer.Ordinal))
                throw new Exception("Integrity snapshot did not retain the pinned SDL3_sound dependency.");
            if (contract.FindDeclaredFile("bin/mw3indeo.exe") != Path.Combine(root, "bin", "mw3indeo.exe"))
                throw new Exception("Integrity snapshot did not retain the pinned Indeo helper dependency.");
            if (Directory.GetFiles(root, "*", SearchOption.AllDirectories).Length != before.Count ||
                before.Any(pair => !File.Exists(pair.Key) || Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(pair.Key))) != pair.Value))
                throw new Exception("Integrity reading changed its input closure.");
            if (!type.IsSealed || type.GetConstructors().Length != 0 ||
                type.GetProperties().Any(property => property.SetMethod != null))
                throw new Exception("Integrity snapshot exposes a mutable/publicly constructible interface.");
            void RejectMutation(Action mutate)
            {
                try { mutate(); }
                catch (NotSupportedException) { return; }
                throw new Exception("Integrity snapshot exposed a mutable collection.");
            }
            RejectMutation(() => ((IDictionary<string, string>)contract.Roles)["profile"] = "changed.json");
            RejectMutation(() => ((IList<string>)contract.Dependencies).Clear());
            RejectMutation(() => ((IList<int>)contract.Capabilities["authored-capability"]).Add(7));
            var noControllerCapability = descriptor.DeepClone().AsObject();
            noControllerCapability["capabilities"]!.AsObject().Remove("controller-profile");
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(noControllerCapability));
            if (Mw3ReRuntimeContract.ReadStructure(root).SupportsControllerProfiles)
                throw new Exception("A runtime without controller capability was marked compatible.");
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(descriptor));
            void RejectDescriptor(Action<JsonObject> change, string reason = "")
            {
                var candidate = descriptor.DeepClone().AsObject();
                change(candidate);
                File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(candidate));
                try { Mw3ReRuntimeContract.ReadStructure(root); }
                catch (InvalidDataException invalid) when (invalid.Message.Contains(reason, StringComparison.OrdinalIgnoreCase)) { return; }
                throw new Exception("Invalid native integrity descriptor accepted; expected " + reason);
            }
            foreach (var change in new Action<JsonObject>[]
            {
                json => json["schema_version"] = 1,
                json => json["schema_version"] = true,
                json => json["engine"] = "legacy",
                json => json["extra"] = 1,
                json => json.Remove("engine"),
                json => json["roles"]!["extra"] = "support.txt",
                json => json["roles"]!.AsObject().Remove("profile"),
                json => json["roles"]!["profile"] = "bin/mw3.exe",
                json => json["roles"]!["profile"] = "Profile.json",
                json => json["roles"]!["profile"] = "../escape.json",
                json => json["roles"]!["profile"] = "C:/escape.json",
                json => json["roles"]!["coordinator"] = "support.txt",
                json => json["dependencies"] = new JsonArray("profile.json"),
                json => json["dependencies"] = new JsonArray("support.txt", "SUPPORT.TXT"),
                json => json["files"]!.AsObject().Remove("support.txt"),
                json => json["files"]!["SUPPORT.TXT"] = json["files"]!["support.txt"]!.DeepClone(),
                json => json["files"]!["runtime.json"] = json["files"]!["support.txt"]!.DeepClone(),
                json => json["files"]!["other.txt"] = json["files"]!["support.txt"]!.DeepClone(),
                json => json["files"]!["support.txt"]!["extra"] = 1,
                json => json["files"]!["support.txt"]!["bytes"] = true,
                json => json["files"]!["support.txt"]!["bytes"] = 0,
                json => json["files"]!["support.txt"]!["bytes"] = 4294967297L,
                json => json["files"]!["support.txt"]!["sha256"] = "wrong",
                json => json["provenance"]!["extra"] = "fixture",
                json => json["provenance"]!["source_commit"] = new string('A', 40),
                json => json["provenance"]!["build_id"] = "NUL",
                json => json["capabilities"]!["authored-capability"] = new JsonArray(1, 1),
                json => json["capabilities"]!["authored-capability"] = new JsonArray(0),
                json => json["capabilities"]!["authored-capability"] = new JsonArray(true),
                json => json["capabilities"]!["BAD"] = new JsonArray(1)
            }) RejectDescriptor(change);
            RejectDescriptor(json => json["capabilities"]!["authored-capability"] = new JsonArray(Enumerable.Range(1, 17).Select(value => (JsonNode)JsonValue.Create(value)).ToArray()));
            RejectDescriptor(json =>
            {
                var excessive = new JsonObject();
                for (var i = 0; i < 65; i++) excessive["cap-" + i] = new JsonArray(1);
                json["capabilities"] = excessive;
            });
            RejectDescriptor(json =>
            {
                var excessive = new JsonObject();
                for (var i = 0; i < 20001; i++) excessive["f" + i] = new JsonObject { ["bytes"] = 1, ["sha256"] = new string('0', 64) };
                json["files"] = excessive;
            });
            RejectDescriptor(json => json["files"]!["support.txt"]!["sha256"] = new string('0', 64), "hash");
            // Quota rejection must precede opening the deliberately absent payload.
            RejectDescriptor(json =>
            {
                json["dependencies"] = new JsonArray("absent.bin", "bin/SDL3_sound.dll", "bin/mw3indeo.exe");
                json["files"]!.AsObject().Remove("support.txt");
                json["files"]!["absent.bin"] = new JsonObject { ["bytes"] = 4294967296L, ["sha256"] = new string('0', 64) };
            }, "size");
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(descriptor));
            var emptyCapabilities = descriptor.DeepClone().AsObject();
            emptyCapabilities["capabilities"] = new JsonObject();
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(emptyCapabilities));
            if (Mw3ReRuntimeContract.ReadStructure(root).Capabilities.Count != 0)
                throw new Exception("Integrity reader manufactured empty capability declarations.");
            var badExecutable = File.ReadAllBytes(Path.Combine(root, "bin", "mw3.exe"));
            var originalExecutable = badExecutable.ToArray();
            badExecutable[BitConverter.ToInt32(badExecutable, 60) + 23] |= 0x20;
            File.WriteAllBytes(Path.Combine(root, "bin", "mw3.exe"), badExecutable);
            RejectDescriptor(json => json["files"]!["bin/mw3.exe"]!["sha256"] = Convert.ToHexString(SHA256.HashData(badExecutable)), "executable");
            File.WriteAllBytes(Path.Combine(root, "bin", "mw3.exe"), originalExecutable);
            var text = GameRunner.SerializeLaunchProfile(descriptor);
            foreach (var raw in new[] { text[..^1] + ",\"schema_version\":2}", text[..^1] + ",}", "[]" })
            {
                File.WriteAllText(Path.Combine(root, "runtime.json"), raw);
                Reject(() => Mw3ReRuntimeContract.ReadStructure(root));
            }
            File.WriteAllText(Path.Combine(root, "runtime.json"), text);
            Reject(() => NativeRuntimeLayout.ReadRoot(root));
            var paired = descriptor.DeepClone().AsObject();
            foreach (var role in new[] { "coordinator", "python" })
            {
                var relative = role + ".fixture";
                File.WriteAllText(Path.Combine(root, relative), "authored optional transport bytes");
                var bytes = File.ReadAllBytes(Path.Combine(root, relative));
                paired["roles"]![role] = relative;
                paired["files"]![relative] = new JsonObject { ["bytes"] = bytes.Length, ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes)) };
            }
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(paired));
            Mw3ReRuntimeContract.ReadStructure(root);
            CheckMw3RePomProjection(root, paired);
            File.WriteAllText(Path.Combine(root, "runtime.json"), text);
            var linkTarget = Directory.CreateDirectory(Path.Combine(root, "target")).FullName;
            File.Copy(Path.Combine(root, "support.txt"), Path.Combine(linkTarget, "support.txt"));
            var link = Path.Combine(root, "linked");
            var junction = new System.Diagnostics.ProcessStartInfo("cmd.exe")
            {
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true
            };
            foreach (var argument in new[] { "/c", "mklink", "/J", link, linkTarget }) junction.ArgumentList.Add(argument);
            using (var process = System.Diagnostics.Process.Start(junction) ?? throw new Exception("Junction control did not start."))
            {
                var output = process.StandardOutput.ReadToEnd();
                var error = process.StandardError.ReadToEnd();
                process.WaitForExit();
                if (process.ExitCode != 0) throw new Exception("Required junction control unavailable: " + error + output);
            }
            try
            {
                RejectDescriptor(json =>
                {
                    json["dependencies"] = new JsonArray("linked/support.txt", "bin/SDL3_sound.dll", "bin/mw3indeo.exe");
                    json["files"]!["linked/support.txt"] = json["files"]!["support.txt"]!.DeepClone();
                    json["files"]!.AsObject().Remove("support.txt");
                }, "link");
            }
            finally { Directory.Delete(link); }
            Console.WriteLine("Native integrity snapshot: schema, closure, hash, bounds and immutable-interface controls passed.");
        }
        finally { Directory.Delete(root, true); }
    }

    private static void CheckPinnedProfileSnapshot(string root)
    {
        const string sentinel = "AUTHORED_PRIVATE_SENTINEL";
        var method = typeof(Mw3ReRuntimeContract).GetMethod("ReadPinnedPlanningProfile",
            BindingFlags.Instance | BindingFlags.NonPublic, null, Type.EmptyTypes, null)
            ?? throw new Exception("Required pinned profile snapshot method is missing.");
        var manifestPath = Path.Combine(root, "runtime.json");
        var manifestBytes = File.ReadAllBytes(manifestPath);
        var descriptor = JsonNode.Parse(manifestBytes)!.AsObject();
        var relative = descriptor["roles"]!["profile"]!.GetValue<string>();
        var profilePath = Path.Combine(root, relative);
        var profileBytes = File.ReadAllBytes(profilePath);
        int cases = 0;
        void SetProfile(byte[] bytes)
        {
            File.WriteAllBytes(profilePath, bytes);
            var candidate = descriptor.DeepClone().AsObject();
            candidate["files"]![relative] = new JsonObject
            {
                ["bytes"] = bytes.Length,
                ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes))
            };
            File.WriteAllText(manifestPath, GameRunner.SerializeLaunchProfile(candidate));
        }
        Mw3ReRuntimeContract Fresh(byte[] bytes)
        {
            SetProfile(bytes);
            return Mw3ReRuntimeContract.ReadStructure(root);
        }
        string Read(Mw3ReRuntimeContract contract) => (string)method.Invoke(contract, null)!;
        void RejectSnapshot(Mw3ReRuntimeContract contract)
        {
            try { Read(contract); }
            catch (TargetInvocationException error) when (error.InnerException is InvalidDataException)
            {
                if (error.InnerException.ToString().Contains(sentinel, StringComparison.Ordinal))
                    throw new Exception("Pinned profile error disclosed private content.");
                cases++;
                return;
            }
            throw new Exception("Invalid pinned profile snapshot was accepted.");
        }
        try
        {
            var original = Fresh(profileBytes);
            if (Read(original) != new UTF8Encoding(false, true).GetString(profileBytes))
                throw new Exception("Pinned profile baseline content changed.");
            cases++;
            var valid = Encoding.UTF8.GetBytes("{\"v\":\"" + sentinel + "\"}");
            var pinned = Fresh(valid);
            var replacement = valid.ToArray();
            replacement[replacement.Length - 3] ^= 1;
            SetProfile(replacement);
            RejectSnapshot(pinned);
            pinned = Fresh(valid);
            SetProfile(Encoding.UTF8.GetBytes("{\"v\":\"different length\"}"));
            RejectSnapshot(pinned);
            RejectSnapshot(Fresh(new byte[] { 0xc3, 0x28 }));
            RejectSnapshot(Fresh(Encoding.Unicode.GetPreamble().Concat(Encoding.Unicode.GetBytes("{}" )).ToArray()));
            RejectSnapshot(Fresh(Encoding.UTF32.GetPreamble().Concat(Encoding.UTF32.GetBytes("{}")).ToArray()));
            var bomText = "{\"v\":\"bom\"}";
            var bom = new byte[] { 0xef, 0xbb, 0xbf }.Concat(Encoding.UTF8.GetBytes(bomText)).ToArray();
            if (Read(Fresh(bom)) != bomText) throw new Exception("UTF8 BOM snapshot decoding failed.");
            cases++;
            RejectSnapshot(Fresh(new byte[2 * 1024 * 1024 + 1]));
            if (cases != 8) throw new Exception("Pinned profile case count mismatch.");
            Console.WriteLine($"Pinned profile snapshots: {cases} cases passed.");
        }
        finally
        {
            File.WriteAllBytes(profilePath, profileBytes);
            File.WriteAllBytes(manifestPath, manifestBytes);
        }
    }

    private static void CheckMw3RePlanningProfile(string root)
    {
        const string sentinel = "AUTHORED_PRIVATE_SENTINEL";
        const string recipe = """{"schema_version":1,"engine":"mw3-re","purpose":"planning-defaults","options":{"renderer":"vulkan-wsi","width":1280,"height":720,"aa":"fxaa","af":16,"window_mode":"windowed","render_thread":true,"lighting":"off"}}""";
        var manifestPath = Path.Combine(root, "runtime.json");
        var profilePath = Path.Combine(root, "profile.json");
        var manifestBytes = File.ReadAllBytes(manifestPath);
        var profileBytes = File.ReadAllBytes(profilePath);
        var descriptor = JsonNode.Parse(manifestBytes)!.AsObject();
        var dataRoot = Path.Combine(Path.GetTempPath(), "MW3 profile planning " + Guid.NewGuid().ToString("N"));
        var defaults = new Mw3RePlanningOptions();
        int accepted = 0, rejected = 0, plannerRejected = 0;
        Mw3ReRuntimeContract Fresh(byte[] bytes)
        {
            File.WriteAllBytes(profilePath, bytes);
            var candidate = descriptor.DeepClone().AsObject();
            candidate["files"]!["profile.json"] = new JsonObject
            {
                ["bytes"] = bytes.Length,
                ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes))
            };
            File.WriteAllText(manifestPath, GameRunner.SerializeLaunchProfile(candidate));
            return Mw3ReRuntimeContract.ReadStructure(root);
        }
        string Changed(string field, string rawValue, bool atRoot = false)
        {
            var candidate = JsonNode.Parse(recipe)!.AsObject();
            var target = atRoot ? candidate : candidate["options"]!.AsObject();
            target[field] = JsonNode.Parse(rawValue);
            return candidate.ToJsonString();
        }
        Mw3RePlanningOptions ReadOnly(Mw3ReRuntimeContract contract)
        {
            var before = Directory.GetFiles(root, "*", SearchOption.AllDirectories)
                .ToDictionary(path => path, path => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))));
            try { return Mw3RePlanningProfile.Read(contract); }
            finally
            {
                var after = Directory.GetFiles(root, "*", SearchOption.AllDirectories);
                if (after.Length != before.Count ||
                    before.Any(pair => !File.Exists(pair.Key) ||
                        Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(pair.Key))) != pair.Value))
                    throw new Exception("Planning profile reading changed its input closure.");
            }
        }
        void RejectContract(Mw3ReRuntimeContract contract)
        {
            try { ReadOnly(contract); }
            catch (InvalidDataException error)
            {
                if (error.InnerException != null || error.ToString().Contains(sentinel, StringComparison.Ordinal))
                    throw new Exception("Planning profile error disclosed private content or parser details.");
                rejected++;
                return;
            }
            throw new Exception("Invalid planning profile was accepted.");
        }
        void RejectText(string raw) => RejectContract(Fresh(Encoding.UTF8.GetBytes(raw)));
        void RoundTrip(byte[] raw, Mw3RePlanningOptions expected, string aa, bool blocked = false)
        {
            var contract = Fresh(raw);
            var options = ReadOnly(contract);
            if (options.Assets.Count != 0 || options with { Assets = expected.Assets } != expected)
                throw new Exception("Planning profile silently changed a typed option.");
            var request = Mw3ReLaunchRequest.Create(contract, options, "D:/Original MW3", dataRoot, "profile-a");
            var wire = JsonNode.Parse(request)!;
            var original = JsonNode.Parse(new UTF8Encoding(false, true).GetString(
                raw.AsSpan(raw.AsSpan().StartsWith(new byte[] { 0xef, 0xbb, 0xbf }) ? 3 : 0)))!;
            foreach (var field in new[] { "renderer", "width", "height", "aa", "af", "window_mode", "render_thread", "lighting" })
                if (!JsonNode.DeepEquals(wire[field], original["options"]![field]))
                    throw new Exception("Planning projection substituted a packaged option.");
            var planned = RunMw3RePlanner(request);
            if (blocked)
            {
                if (planned["ok"]!.GetValue<bool>() || planned["argv"] != null ||
                    planned["reasons"]!.AsArray().Count == 0)
                    throw new Exception("Unsupported saved options produced argv.");
            }
            else
            {
                var expectedWrite = Path.Combine(dataRoot, "mw3-re", "profiles", "profile-a");
                // MW3-RE is desktop fullscreen by default; only a windowed choice adds window arguments.
                var window = expected.WindowMode == Mw3ReWindowMode.Windowed
                    ? new[] { "--window", expected.Width + "x" + expected.Height, "--windowed" }
                    : Array.Empty<string>();
                var argv = new[] { contract.Executable, "--install", "D:/Original MW3", "--write-dir", expectedWrite,
                    "--cc-vulkan-wsi" }.Concat(window).Concat(new[] {
                    "--cc-aa", aa, "--cc-af", expected.AnisotropicFiltering.ToString(),
                    "--cc-render-thread", expected.RenderThread ? "1" : "0", "--cc-lighting",
                    original["options"]!["lighting"]!.GetValue<string>(),
                    "--cc-flare-style", "modern" }).ToArray();
                if (!planned["ok"]!.GetValue<bool>() ||
                    !planned["argv"]!.AsArray().Select(value => value!.GetValue<string>()).SequenceEqual(argv) ||
                    planned["working_directory"]!.GetValue<string>() != Path.GetDirectoryName(contract.Executable))
                    throw new Exception("Packaged planning profile did not reach the actual full argv planner.");
            }
            if (!File.ReadAllBytes(profilePath).SequenceEqual(raw) || Directory.Exists(dataRoot))
                throw new Exception("Planning changed the packaged choices or created user data.");
            accepted++;
        }
        try
        {
            RoundTrip(Encoding.UTF8.GetBytes(recipe), defaults, "fxaa");
            foreach (var (value, choice, argv) in new[]
            {
                ("off", Mw3ReAntialiasing.Off, "off"), ("1", Mw3ReAntialiasing.One, "off"),
                ("fxaa", Mw3ReAntialiasing.Fxaa, "fxaa"), ("2", Mw3ReAntialiasing.Two, "ssaa2"),
                ("4", Mw3ReAntialiasing.Four, "ssaa4"), ("8", Mw3ReAntialiasing.Eight, "")
            })
                RoundTrip(Encoding.UTF8.GetBytes(Changed("aa", JsonSerializer.Serialize(value))),
                    defaults with { Antialiasing = choice }, argv, choice == Mw3ReAntialiasing.Eight);
            foreach (var (value, choice) in new[]
            {
                ("windowed", Mw3ReWindowMode.Windowed), ("fullscreen", Mw3ReWindowMode.Fullscreen),
                ("borderless", Mw3ReWindowMode.Borderless)
            })
                RoundTrip(Encoding.UTF8.GetBytes(Changed("window_mode", JsonSerializer.Serialize(value))),
                    defaults with { WindowMode = choice }, "fxaa");
            foreach (var (value, choice) in new[]
            {
                ("off", Mw3ReLighting.Off), ("flat", Mw3ReLighting.Flat), ("normal", Mw3ReLighting.Normal)
            })
                RoundTrip(Encoding.UTF8.GetBytes(Changed("lighting", JsonSerializer.Serialize(value))),
                    defaults with { Lighting = choice }, "fxaa");
            foreach (var value in new[] { false, true })
                RoundTrip(Encoding.UTF8.GetBytes(Changed("render_thread", value ? "true" : "false")),
                    defaults with { RenderThread = value }, "fxaa");
            var alternate = JsonNode.Parse(recipe)!;
            alternate["options"]!["width"] = 1920;
            alternate["options"]!["height"] = 1080;
            alternate["options"]!["af"] = 8;
            RoundTrip(Encoding.UTF8.GetBytes(alternate.ToJsonString()),
                defaults with { Width = 1920, Height = 1080, AnisotropicFiltering = 8 }, "fxaa");
            RoundTrip(new byte[] { 0xef, 0xbb, 0xbf }.Concat(Encoding.UTF8.GetBytes(recipe)).ToArray(), defaults, "fxaa");
            foreach (var field in new[] { "schema_version", "engine", "purpose", "options" })
            {
                var candidate = JsonNode.Parse(recipe)!.AsObject();
                candidate.Remove(field);
                RejectText(candidate.ToJsonString());
            }
            foreach (var field in new[] { "renderer", "width", "height", "aa", "af", "window_mode", "render_thread", "lighting" })
            {
                var candidate = JsonNode.Parse(recipe)!;
                candidate["options"]!.AsObject().Remove(field);
                RejectText(candidate.ToJsonString());
            }
            foreach (var value in new[] { "0", "2", "true", "\"1\"", "1.0", "1e0", "null" })
                RejectText(Changed("schema_version", value, atRoot: true));
            foreach (var field in new[] { "engine", "purpose" })
                foreach (var value in new[] { JsonSerializer.Serialize(sentinel), "null", "true", "1" })
                    RejectText(Changed(field, value, atRoot: true));
            foreach (var value in new[] { "[]", "null", "\"options\"", "1", "true" })
                RejectText(Changed("options", value, atRoot: true));
            foreach (var field in new[] { "width", "height", "af" })
                foreach (var value in new[] { "\"1280\"", "true", "null", "1.5", "1e3", "2147483648" })
                    RejectText(Changed(field, value));
            foreach (var field in new[] { "renderer", "aa", "window_mode", "lighting" })
                foreach (var value in new[] { JsonSerializer.Serialize(sentinel), "null", "true", "1", "[]" })
                    RejectText(Changed(field, value));
            foreach (var value in new[] { "1", "\"true\"", "null", "[]" })
                RejectText(Changed("render_thread", value));
            RejectText(Changed("extra", JsonSerializer.Serialize(sentinel), atRoot: true));
            RejectText(Changed("assets", "[]"));
            foreach (var raw in new[]
            {
                recipe[..^1] + ",\"schema_version\":1}",
                recipe[..^1] + ",\"\\u0065ngine\":\"mw3-re\"}",
                recipe.Replace("\"width\":1280", "\"width\":1280,\"width\":1280"),
                Changed("extra", "[{\"value\":1,\"value\":2}]", atRoot: true)
            }) RejectText(raw);
            foreach (var raw in new[]
            {
                "[]", "null", "{", recipe + ",", recipe.Replace("1280", sentinel), recipe + "/*" + sentinel + "*/"
            }) RejectText(raw);
            RejectText(recipe[..^1] + ",\"extra\":" + new string('[', 65) + "0" + new string(']', 65) + "}");
            foreach (var raw in new[]
            {
                Encoding.UTF8.GetBytes(recipe + sentinel).Concat(new byte[] { 0xc3, 0x28 }).ToArray(),
                Encoding.Unicode.GetPreamble().Concat(Encoding.Unicode.GetBytes(recipe + sentinel)).ToArray(),
                Encoding.UTF32.GetPreamble().Concat(Encoding.UTF32.GetBytes(recipe + sentinel)).ToArray()
            }) RejectContract(Fresh(raw));
            foreach (var width in new[] { "1920", "640" })
            {
                var pinned = Fresh(Encoding.UTF8.GetBytes(recipe));
                Fresh(Encoding.UTF8.GetBytes(Changed("width", width)));
                RejectContract(pinned);
            }
            foreach (var (field, value) in new[] { ("width", "0"), ("af", "3") })
            {
                var contract = Fresh(Encoding.UTF8.GetBytes(Changed(field, value)));
                var options = ReadOnly(contract);
                var planned = RunMw3RePlanner(Mw3ReLaunchRequest.Create(contract, options, "D:/Original MW3", dataRoot, "profile-a"));
                if (planned["validation_error"]?.GetValue<bool>() != true || planned["argv"] != null)
                    throw new Exception("The actual planner did not enforce numeric bounds.");
                plannerRejected++;
            }
            if (accepted != 17 || rejected != 92 || plannerRejected != 2)
                throw new Exception($"Planning profile case count mismatch: {accepted}/{rejected}/{plannerRejected}.");
            Console.WriteLine($"Pinned planning profiles: {accepted} roundtrips, {rejected} rejections, {plannerRejected} planner-bound controls passed.");
        }
        finally
        {
            File.WriteAllBytes(profilePath, profileBytes);
            File.WriteAllBytes(manifestPath, manifestBytes);
        }
    }

    private static void CheckMw3ReRequestProjection(Mw3ReRuntimeContract contract)
    {
        var dataRoot = Path.Combine(Path.GetTempPath(), "MW3 planned writes " + Guid.NewGuid().ToString("N"));
        var assets = new List<string> { "F:/Mods Pack/alpha", "F:/Mods/é" };
        var options = new Mw3RePlanningOptions
        {
            Antialiasing = Mw3ReAntialiasing.Two, AnisotropicFiltering = 8, RenderThread = false,
            Lighting = Mw3ReLighting.Normal, Assets = assets
        };
        var json = Mw3ReLaunchRequest.Create(contract, options, "D:/Original MW3", dataRoot, "pilot-a");
        if (options.Pom || json != Mw3ReLaunchRequest.Create(contract, options with { Pom = false },
            "D:/Original MW3", dataRoot, "pilot-a"))
            throw new Exception("Default POM changed ordinary schema2 request bytes.");
        var wire = JsonNode.Parse(json)!.AsObject();
        var expectedWrite = Path.Combine(dataRoot, "mw3-re", "profiles", "pilot-a");
        if (wire["schema_version"]!.GetValue<int>() != 2 || wire["engine"]!.GetValue<string>() != "mw3-re" ||
            wire["runtime_root"]!.GetValue<string>() != contract.Root ||
            wire["executable"]!.GetValue<string>() != contract.Executable ||
            wire["write_dir"]!.GetValue<string>() != expectedWrite || wire["width"]!.GetValue<int>() != 1280 ||
            wire["render_thread"]!.GetValue<bool>())
            throw new Exception("Typed projection lost an identity, write root, number or Boolean.");
        assets.Add("F:/later-caller-mutation");
        if (wire["assets"]!.AsArray().Count != 2) throw new Exception("Projected assets alias caller-owned state.");
        foreach (var (choice, token) in new[]
        {
            (Mw3ReAntialiasing.Off, "off"), (Mw3ReAntialiasing.One, "1"), (Mw3ReAntialiasing.Fxaa, "fxaa"),
            (Mw3ReAntialiasing.Two, "2"), (Mw3ReAntialiasing.Four, "4"), (Mw3ReAntialiasing.Eight, "8")
        })
        {
            var projected = JsonNode.Parse(Mw3ReLaunchRequest.Create(contract, options with { Antialiasing = choice }, "D:/Original MW3", dataRoot, "pilot-a"))!;
            if (projected["aa"]!.GetValue<string>() != token) throw new Exception("Native AA projection silently remapped a saved choice.");
        }
        Reject(() => Mw3ReLaunchRequest.Create(contract, options, "D:/Original MW3", dataRoot, "../escape"));
        Reject(() => Mw3ReLaunchRequest.Create(contract, options with { Renderer = (Mw3ReRenderer)99 }, "D:/Original MW3", dataRoot, "pilot-a"));
        Reject(() => Mw3ReLaunchRequest.Create(contract, options with { FlareStyle = (Mw3ReFlareStyle)99 },
            "D:/Original MW3", dataRoot, "pilot-a"));
        var planned = RunMw3RePlanner(json);
        var expected = new[] { contract.Executable, "--install", "D:/Original MW3", "--write-dir", expectedWrite,
            "--cc-vulkan-wsi", "--window", "1280x720", "--windowed", "--cc-aa", "ssaa2", "--cc-af", "8",
            "--cc-render-thread", "0", "--cc-lighting", "normal", "--cc-flare-style", "modern",
            "--assets", "F:/Mods Pack/alpha", "--assets", "F:/Mods/é" };
        if (!planned["ok"]!.GetValue<bool>() ||
            !planned["argv"]!.AsArray().Select(value => value!.GetValue<string>()).SequenceEqual(expected) ||
            planned["working_directory"]!.GetValue<string>() != Path.GetDirectoryName(contract.Executable))
            throw new Exception("Actual Python argv did not preserve the typed native request.");
        if (Directory.Exists(expectedWrite)) throw new Exception("Planning unexpectedly created a write directory.");
        Console.WriteLine("Typed native JSON -> isolated actual Python argv planner passed; no game process.");
    }

    private static void CheckNativePreviewProjection(Mw3ReRuntimeContract contract)
    {
        // Authored packs in the installed layout; the actual Python planner reads them.
        var packs = Path.Combine(Path.GetTempPath(), "MW3 preview packs " + Guid.NewGuid().ToString("N"));
        var dataRoot = Path.Combine(Path.GetTempPath(), "MW3 preview writes " + Guid.NewGuid().ToString("N"));
        try
        {
            var mechs = Path.Combine(packs, "mechs");
            Directory.CreateDirectory(Path.Combine(mechs, "payload"));
            Directory.CreateDirectory(Path.Combine(mechs, "models"));
            foreach (var name in new[] { "mesh", "tex", "nrm" }) File.WriteAllText(Path.Combine(mechs, "payload", name + ".bin"), "x");
            File.WriteAllText(Path.Combine(mechs, "pack.json"), """{"schema_version":2,"native_payload":{"profile":"prepared-native-v1","registry":"models/models.json","path_base":"pack-root"}}""");
            File.WriteAllText(Path.Combine(mechs, "models", "models.json"), """{"schema_version":2,"models":[{"id":"owens","backend":"native","status":"runtime-ready","environment":{"MW34_OWENS_MESH":"payload/mesh.bin","MW34_OWENS_TEXTURES":"payload/tex.bin","MW34_OWENS_NORMALS":"payload/nrm.bin"}}]}""");
            var map = Path.Combine(packs, "training");
            Directory.CreateDirectory(map);
            File.WriteAllText(Path.Combine(map, "pack.json"), """{"schema_version":2,"files":{"environment/a.zbd":{"bytes":10,"sha256":"00"}},"native_payload":{"profile":"prepared-environment-v1"}}""");
            var shared = Path.Combine(packs, "shared");
            Directory.CreateDirectory(shared);
            File.WriteAllText(Path.Combine(shared, "pack.json"), """{"schema_version":2,"files":{"environment/rmechtex.zbd":{"bytes":5000000000,"sha256":"00"}},"native_payload":{"profile":"prepared-environment-v1"}}""");
            var ui = Path.Combine(packs, "menu-ui");
            Directory.CreateDirectory(Path.Combine(ui, "ui", "sprites"));
            var spriteBytes = new byte[32];
            "MW3H"u8.CopyTo(spriteBytes);
            BitConverter.GetBytes(1u).CopyTo(spriteBytes, 4); BitConverter.GetBytes(1u).CopyTo(spriteBytes, 8);
            BitConverter.GetBytes(0f).CopyTo(spriteBytes, 12); BitConverter.GetBytes(0f).CopyTo(spriteBytes, 16);
            BitConverter.GetBytes(1f).CopyTo(spriteBytes, 20); BitConverter.GetBytes(1f).CopyTo(spriteBytes, 24);
            spriteBytes[28] = 1; spriteBytes[31] = 255;
            File.WriteAllBytes(Path.Combine(ui, "ui", "sprites", "0123456789abcdef.rgba"), spriteBytes);
            var backgroundBytes = "MWHDBG1\0"u8.ToArray().Concat(new byte[]
                { 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0 }).ToArray();
            File.WriteAllBytes(Path.Combine(ui, "ui", "background.mwhd"), backgroundBytes);
            var registryBytes = Encoding.UTF8.GetBytes("""{"schema_version":2,"payload_profile":"prepared-ui-v1","kind":"menu","sprites":{"0123456789abcdef":"ui/sprites/0123456789abcdef.rgba"},"background":"ui/background.mwhd"}""");
            File.WriteAllBytes(Path.Combine(ui, "ui", "ui.json"), registryBytes);
            File.WriteAllText(Path.Combine(ui, "pack.json"), JsonSerializer.Serialize(new
            {
                schema_version = 2, game_id = "mw3", id = "test.menu-ui", name = "Test menu UI",
                files = new Dictionary<string, object>
                {
                    ["ui/ui.json"] = new
                    { bytes = registryBytes.Length, sha256 = Convert.ToHexString(SHA256.HashData(registryBytes)).ToLowerInvariant() },
                    ["ui/sprites/0123456789abcdef.rgba"] = new
                    { bytes = spriteBytes.Length, sha256 = Convert.ToHexString(SHA256.HashData(spriteBytes)).ToLowerInvariant(), format = "MW3H-v1" },
                    ["ui/background.mwhd"] = new
                    { bytes = backgroundBytes.Length, sha256 = Convert.ToHexString(SHA256.HashData(backgroundBytes)).ToLowerInvariant(), format = "MWHDBG1" }
                },
                native_payload = new { profile = "prepared-ui-v1", registry = "ui/ui.json", path_base = "pack-root" }
            }));
            if (!NativeGameRunner.SelectUiPacks(new[] { ui }).SequenceEqual(new[] { Path.GetFullPath(ui) }))
                throw new Exception("Enabled prepared UI packs were not selected for native planning.");
            var unreadableUi = Path.Combine(packs, "unreadable-ui");
            Directory.CreateDirectory(unreadableUi);
            File.WriteAllText(Path.Combine(unreadableUi, "pack.json"), "not json");
            foreach (var invalidUi in new[] { unreadableUi, "invalid\0ui-pack" })
            {
                var unreadableUiReports = new List<string>();
                if (!NativeGameRunner.SelectUiPacks(new[] { invalidUi, ui }, unreadableUiReports.Add)
                        .SequenceEqual(new[] { Path.GetFullPath(ui) }) ||
                    unreadableUiReports.Count != 1 ||
                    !unreadableUiReports[0].Contains("could not be read", StringComparison.Ordinal) ||
                    !unreadableUiReports[0].Contains(invalidUi, StringComparison.Ordinal))
                    throw new Exception("Unreadable pack was not reported as skipped or stopped later UI selection.");
            }

            if (NativeGameRunner.WindowModeForSettings("windowed") != Mw3ReWindowMode.Windowed ||
                NativeGameRunner.WindowModeForSettings("fullscreen") != Mw3ReWindowMode.Fullscreen ||
                NativeGameRunner.WindowModeForSettings("fullscreen_windowed") != Mw3ReWindowMode.Borderless)
                throw new Exception("Saved window mode did not reach the MW3-RE planner mode.");

            var settings = new LauncherSettings
            {
                Width = 1280, Height = 720, WindowMode = "windowed", RenderThread = true,
                AntiAliasing = "fxaa", AnisotropicFiltering = 16, DrawDistance = 1200,
                DynamicLighting = true, Shadows = true,
                WaterDetail = false, CloudDetail = false, FlareStyle = "original"
            };
            var options = NativeGameRunner.PlanningOptionsForSettings(settings, contract,
                NativeGameRunner.PreviewDrawDistance(settings.DrawDistance, out _),
                new[] { mechs }, new[] { map, shared }, null, new[] { ui });
            var json = Mw3ReLaunchRequest.Create(contract, options, "D:/Original MW3", dataRoot, NativeGameRunner.ProfileId);
            var wire = JsonNode.Parse(json)!;
            if (wire["schema_version"]!.GetValue<int>() != 4 || wire["preview"]!["draw_distance"]!.GetValue<int>() != 1200 ||
                wire["preview"]!["ui_packs"]![0]!.GetValue<string>() != ui ||
                !wire["preview"]!["dynamic_lighting"]!.GetValue<bool>() ||
                !wire["preview"]!["shadows"]!.GetValue<bool>() ||
                wire["visuals"]!["pom"]!.GetValue<bool>() != true ||
                wire["preview"]!["water_detail"]!.GetValue<bool>() ||
                wire["preview"]!["cloud_detail"]!.GetValue<bool>())
                throw new Exception("Native preview projection lost its schema, distance, dynamic lighting, shadows, POM or detail choices.");
            if (wire["flare_style"]!.GetValue<string>() != "original")
                throw new Exception("Saved lens flare style did not reach the native preview request.");
            if (wire["disk_cache"]!.GetValue<bool>() != (Environment.GetEnvironmentVariable("MW3_DISK_CACHE") != "0"))
                throw new Exception("The load cache default did not reach the native request.");
            var planned = RunMw3RePlanner(json);
            CheckLoadCacheSwitch(settings, contract, dataRoot, ui, mechs, map, shared);
            var argv = planned["argv"]!.AsArray().Select(value => value!.GetValue<string>()).ToList();
            if (argv[argv.IndexOf("--cc-dynamic-lighting") + 1] != "1" ||
                argv[argv.IndexOf("--cc-sun-shadows") + 1] != "1" ||
                argv[argv.IndexOf("--cc-flare-style") + 1] != "original")
                throw new Exception("Native launcher dynamic lighting and shadows choices did not reach the runtime argv.");
            var expectedTail = new[] { "--cc-pom", "1", "--cc-environment-packs-explicit", "--cc-draw-distance", "1200", "--cc-hud", "core-critical",
                "--cc-hud-text", "1", "--cc-menu-background", Path.Combine(ui, "ui", "background.mwhd"),
                "--cc-hud-artwork", ui, "--cc-geometry", "partial",
                "--cc-model", "owens", "0", Path.Combine(mechs, "payload", "mesh.bin"), Path.Combine(mechs, "payload", "tex.bin"),
                "--cc-model-normals", "owens", "0", Path.Combine(mechs, "payload", "nrm.bin"),
                "--cc-environment-pack", map };
            // This fixture has no effect-light catalog, so local lights are also skipped.
            if (!planned["ok"]!.GetValue<bool>() || !argv.Skip(argv.Count - expectedTail.Length).SequenceEqual(expectedTail) ||
                planned["skipped_packs"]!.AsArray().Count != 3 ||
                // Exact order: the shared environment pack (no feature key), then the
                // dynamic-lighting local-light skips. The menu background is routed, not skipped.
                planned["skipped_packs"]![0]!["root"]!.GetValue<string>() != shared ||
                planned["skipped_packs"]![0]!["feature"] != null ||
                planned["skipped_packs"]![1]!["feature"]?.GetValue<string>() != "effect_lights" ||
                planned["skipped_packs"]![2]!["feature"]?.GetValue<string>() != "fixture_lights")
                throw new Exception("Native preview request did not reach the planner's pack translation intact.");

            var noUiOptions = options with
            {
                Preview = options.Preview! with { UiPacks = Array.Empty<string>(), Hud = null, HudText = null }
            };
            var noUiRequest = Mw3ReLaunchRequest.Create(contract, noUiOptions, "D:/Original MW3", dataRoot,
                NativeGameRunner.ProfileId);
            var noUiPlan = RunMw3RePlanner(noUiRequest);
            var noUiArgv = noUiPlan["argv"]!.AsArray().Select(value => value!.GetValue<string>()).ToList();
            if (noUiArgv.Contains("--cc-hud") || noUiArgv.Contains("--cc-hud-text"))
                throw new Exception("No UI packs should leave saved MW3-RE HUD settings unset.");

            // Keep the saved request intact even when a dependency disables shadows for this launch.
            var suppressedSettings = new LauncherSettings { Shadows = true, DynamicLighting = false };
            var suppressedOptions = NativeGameRunner.PlanningOptionsForSettings(suppressedSettings,
                contract, NativeGameRunner.PreviewDrawDistance(suppressedSettings.DrawDistance, out _),
                Array.Empty<string>(), Array.Empty<string>(), null);
            foreach (var lighting in new[] { Mw3ReLighting.Normal, Mw3ReLighting.Off })
            {
                var suppressedJson = Mw3ReLaunchRequest.Create(contract, suppressedOptions with
                    { Lighting = lighting, Pom = lighting == Mw3ReLighting.Normal },
                    "D:/Original MW3", dataRoot, NativeGameRunner.ProfileId);
                var suppressedWire = JsonNode.Parse(suppressedJson)!;
                if (!suppressedWire["preview"]!["shadows"]!.GetValue<bool>() ||
                    suppressedWire["preview"]!["dynamic_lighting"]!.GetValue<bool>())
                    throw new Exception("Native settings projection erased the requested shadows or enabled dynamic lighting.");
                var suppressedPlan = RunMw3RePlanner(suppressedJson);
                var suppressedArgv = suppressedPlan["argv"]!.AsArray()
                    .Select(value => value!.GetValue<string>()).ToList();
                if (!suppressedPlan["ok"]!.GetValue<bool>() ||
                    suppressedArgv[suppressedArgv.IndexOf("--cc-dynamic-lighting") + 1] != "0" ||
                    suppressedArgv[suppressedArgv.IndexOf("--cc-sun-shadows") + 1] != "0")
                    throw new Exception("Planner enabled shadows or dynamic lighting for a suppressed saved request.");
                var shadowSkips = suppressedPlan["skipped_packs"]!.AsArray()
                    .Where(item => item?["feature"]?.GetValue<string>() == "sun_shadows").ToList();
                var expectedReason = lighting == Mw3ReLighting.Off
                    ? "sun shadows require sun lighting" : "sun shadows require dynamic lighting";
                if (shadowSkips.Count != 1 ||
                    shadowSkips[0]!["root"]!.GetValue<string>() != contract.Root ||
                    shadowSkips[0]!["reason"]!.GetValue<string>() != expectedReason)
                    throw new Exception("Planner lost the sun_shadows suppression record for saved launcher choices.");
            }
            if (!suppressedSettings.Shadows || suppressedSettings.DynamicLighting)
                throw new Exception("Planning mutated the saved lighting choices.");

            // 800 keeps the original geometry range and needs no explicit argument.
            var original = RunMw3RePlanner(Mw3ReLaunchRequest.Create(contract, options with
                { Preview = options.Preview with { DrawDistance = 800 } }, "D:/Original MW3", dataRoot, NativeGameRunner.ProfileId));
            if (original["argv"]!.AsArray().Any(value => value!.GetValue<string>() == "--cc-draw-distance"))
                throw new Exception("Original scenery distance added a preview argument.");
            foreach (var distance in new[] { 2400, 3200 })
            {
                var extended = RunMw3RePlanner(Mw3ReLaunchRequest.Create(contract, options with
                    { Preview = options.Preview with { DrawDistance = distance } },
                    "D:/Original MW3", dataRoot, NativeGameRunner.ProfileId));
                var extendedArguments = extended["argv"]!.AsArray()
                    .Select(value => value!.GetValue<string>()).ToList();
                var distanceIndex = extendedArguments.IndexOf("--cc-draw-distance");
                if (distanceIndex < 0 || distanceIndex + 1 >= extendedArguments.Count ||
                    extendedArguments[distanceIndex + 1] != distance.ToString())
                    throw new Exception("Planner lost the extended scenery distance.");
            }
            var refused = RunMw3RePlanner(Mw3ReLaunchRequest.Create(contract, options with
                { Preview = options.Preview with { DrawDistance = 1000 } },
                "D:/Original MW3", dataRoot, NativeGameRunner.ProfileId));
            if (refused["validation_error"]?.GetValue<bool>() != true) throw new Exception("Planner accepted an unsupported preview distance.");

            if (NativeGameRunner.PreviewDrawDistance(3200, out var reduced) != 3200 || reduced ||
                NativeGameRunner.PreviewDrawDistance(1200, out reduced) != 1200 || reduced)
                throw new Exception("Saved scenery distance was reduced for the native runtime.");
            // Unknown saved choices are refused before any process starts.
            static void Refused(Action action)
            {
                try { action(); }
                catch (InvalidOperationException) { return; }
                throw new Exception("Native preview accepted an unknown saved choice.");
            }
            Refused(() => NativeGameRunner.PreviewDrawDistance(1000, out _));
            Refused(() => NativeGameRunner.PreviewDrawDistance(4000, out _));
            if (NativeGameRunner.PreviewAntialiasing("fxaa") != Mw3ReAntialiasing.Fxaa) throw new Exception("Saved FXAA was remapped.");
            Refused(() => NativeGameRunner.PreviewAntialiasing("msaa"));
            if (Directory.Exists(dataRoot)) throw new Exception("Planning unexpectedly created a write directory.");
            Console.WriteLine("Native preview typed request -> actual Python planner pack translation passed; no game process.");
        }
        finally
        {
            if (Directory.Exists(packs)) Directory.Delete(packs, true);
        }
    }

    private static void CheckMw3RePomProjection(string root, JsonObject paired)
    {
        var manifestPath = Path.Combine(root, "runtime.json");
        var original = File.ReadAllBytes(manifestPath);
        var dataRoot = Path.Combine(Path.GetTempPath(), "MW3 POM planned writes " + Guid.NewGuid().ToString("N"));
        var options = new Mw3RePlanningOptions { Lighting = Mw3ReLighting.Normal, Pom = true };
        string Project(Mw3ReRuntimeContract contract, Mw3RePlanningOptions value) =>
            Mw3ReLaunchRequest.Create(contract, value, "D:/Original MW3", dataRoot, "pom-fixture");
        Mw3ReRuntimeContract Snapshot(JsonObject descriptor)
        {
            File.WriteAllText(manifestPath, GameRunner.SerializeLaunchProfile(descriptor));
            return Mw3ReRuntimeContract.ReadStructure(root);
        }
        try
        {
            // Only authored fixtures make this combined claim; it does not attest native execution.
            var compatible = paired.DeepClone().AsObject();
            compatible["capabilities"]!["pom"] = new JsonArray(1);
            foreach (var version in new[] { 0, 2 })
            {
                var unsupported = compatible.DeepClone().AsObject();
                if (version == 0) unsupported["capabilities"]!.AsObject().Remove("pom");
                else unsupported["capabilities"]!["pom"] = new JsonArray(version);
                var snapshot = Snapshot(unsupported);
                Reject(() => Project(snapshot, options));
                if (JsonNode.Parse(Project(snapshot, options with { Pom = false }))!["schema_version"]!.GetValue<int>() != 2)
                    throw new Exception("Unsupported POM claim changed default-Off planning.");
            }
            var noTransport = compatible.DeepClone().AsObject();
            foreach (var role in new[] { "coordinator", "python" })
            {
                var relative = noTransport["roles"]![role]!.GetValue<string>();
                noTransport["roles"]!.AsObject().Remove(role);
                noTransport["files"]!.AsObject().Remove(relative);
            }
            var missingRoles = Snapshot(noTransport);
            Reject(() => Project(missingRoles, options));
            var admitted = Snapshot(compatible);
            foreach (var lighting in new[] { Mw3ReLighting.Off, Mw3ReLighting.Flat })
                Reject(() => Project(admitted, options with { Lighting = lighting }));
            var json = Project(admitted, options);
            var wire = JsonNode.Parse(json)!.AsObject();
            if (wire["schema_version"]!.GetValue<int>() != 3 || !wire["visuals"]!["pom"]!.GetValue<bool>())
                throw new Exception("Explicit typed POM was not captured into schema3.");
            options = options with { Pom = false };
            Snapshot(paired);
            if (Project(admitted, options with { Pom = true }) != json ||
                !JsonNode.Parse(json)!["visuals"]!["pom"]!.GetValue<bool>())
                throw new Exception("POM projection changed after caller/descriptor replacement.");
            var planned = RunMw3RePlanner(json);
            var args = planned["argv"]!.AsArray().Select(value => value!.GetValue<string>()).ToList();
            if (!planned["ok"]!.GetValue<bool>() || args.Count(value => value == "--cc-pom") != 1 ||
                args[args.IndexOf("--cc-pom") + 1] != "1")
                throw new Exception("Actual Python planner did not produce explicit POM exactly once.");
            args.RemoveRange(args.IndexOf("--cc-pom"), 2);
            var offJson = Project(admitted, options);
            var baseline = RunMw3RePlanner(offJson)["argv"]!.ToJsonString();
            if (new JsonArray(args.Select(value => (JsonNode?)JsonValue.Create(value)).ToArray()).ToJsonString() != baseline)
                throw new Exception("POM changed an unrelated actual Python argument.");
            foreach (var visuals in new JsonObject?[] { null, new(), new() { ["pom"] = false } })
            {
                var neutral = JsonNode.Parse(offJson)!.AsObject();
                neutral["schema_version"] = 3;
                if (visuals != null) neutral["visuals"] = visuals;
                if (RunMw3RePlanner(neutral.ToJsonString())["argv"]!.ToJsonString() != baseline)
                    throw new Exception("Optional schema3 visuals changed default-Off argv.");
            }
            var raw = wire.ToJsonString();
            foreach (var invalid in new[]
            {
                raw[..^1] + ",\"schema_version\":3}",
                raw.Replace("\"pom\":true", "\"pom\":false,\"pom\":true"),
                raw.Replace("\"pom\":true", "\"pom\":1"),
                raw.Replace("\"pom\":true", "\"pom\":null"),
                raw.Replace("\"pom\":true", "\"pom\":true,\"unknown\":false"),
                raw[..^1] + ",\"unknown\":false}",
                raw.Replace("\"lighting\":\"normal\"", "\"lighting\":\"off\""),
                raw.Replace("\"lighting\":\"normal\"", "\"lighting\":\"flat\"")
            })
            {
                if (RunMw3RePlanner(invalid)["validation_error"]?.GetValue<bool>() != true)
                    throw new Exception("Raw typed POM request bypassed Python wire validation.");
            }
            if (Directory.Exists(dataRoot)) throw new Exception("POM planning created user data.");
            Console.WriteLine("Typed POM observational schema3 -> actual Python controls passed; installed admission pending.");
        }
        finally { File.WriteAllBytes(manifestPath, original); }
    }

    /// <summary>The saved Load Cache choice reaches the child environment and nothing else.</summary>
    private static void CheckLoadCacheSwitch(LauncherSettings settings, Mw3ReRuntimeContract contract,
        string dataRoot, string ui, string mechs, string map, string shared)
    {
        var off = new LauncherSettings
        {
            Width = settings.Width, Height = settings.Height, WindowMode = settings.WindowMode,
            RenderThread = settings.RenderThread, AntiAliasing = settings.AntiAliasing,
            AnisotropicFiltering = settings.AnisotropicFiltering, DrawDistance = settings.DrawDistance,
            DynamicLighting = settings.DynamicLighting, Shadows = settings.Shadows,
            WaterDetail = settings.WaterDetail, CloudDetail = settings.CloudDetail,
            FlareStyle = settings.FlareStyle, LoadCache = false
        };
        if (!new LauncherSettings().LoadCache || GraphicsPreferences.From(off).LoadCache)
            throw new Exception("Load Cache must default on and round-trip through graphics preferences.");
        var offOptions = NativeGameRunner.PlanningOptionsForSettings(off, contract,
            NativeGameRunner.PreviewDrawDistance(off.DrawDistance, out _),
            new[] { mechs }, new[] { map, shared }, null, new[] { ui });
        var offRequest = Mw3ReLaunchRequest.Create(contract, offOptions, "D:/Original MW3", dataRoot,
            NativeGameRunner.ProfileId);
        if (JsonNode.Parse(offRequest)!["disk_cache"]!.GetValue<bool>())
            throw new Exception("Turning Load Cache off did not reach the native request.");
        using var offPlan = System.Text.Json.JsonDocument.Parse(RunMw3RePlanner(offRequest).ToJsonString());
        var offStart = new System.Diagnostics.ProcessStartInfo("mw3.exe");
        NativeGameRunner.ApplyCacheEnvironment(offStart, offPlan.RootElement);
        if (offStart.Environment["MW3_DISK_CACHE"] != "0")
            throw new Exception("Turning Load Cache off did not reach the game's environment.");

        foreach (var invalid in new[] { "{\"environment\":{\"PATH\":\"C:/x\"}}",
                     "{\"environment\":{\"MW3_DISK_CACHE\":\"yes\"}}", "{\"environment\":[]}" })
        {
            using var document = System.Text.Json.JsonDocument.Parse(invalid);
            try
            {
                NativeGameRunner.ApplyCacheEnvironment(new System.Diagnostics.ProcessStartInfo("mw3.exe"),
                    document.RootElement);
                throw new Exception("An unexpected planner environment was passed to the game: " + invalid);
            }
            catch (InvalidDataException) { }
        }
        using var older = System.Text.Json.JsonDocument.Parse("{}");
        var olderStart = new System.Diagnostics.ProcessStartInfo("mw3.exe");
        olderStart.Environment.Remove("MW3_DISK_CACHE");
        NativeGameRunner.ApplyCacheEnvironment(olderStart, older.RootElement);
        if (olderStart.Environment.ContainsKey("MW3_DISK_CACHE"))
            throw new Exception("An older planner without an environment changed the game's environment.");
    }

    private static JsonNode RunMw3RePlanner(string json)
    {
        var python = D7VkRunner.FindPythonExecutable(requirePython311: true)
            ?? throw new Exception("Native planner integration requires Python3.11 or later.");
        var info = new System.Diagnostics.ProcessStartInfo(python)
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true
        };
        foreach (var argument in new[] { "-I", "-c",
            "import importlib.util,json,sys; s=importlib.util.spec_from_file_location('mw3_re_launch',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)\ntry: result=m.plan_json(sys.stdin.read())\nexcept ValueError: result={'validation_error':True}\nprint(json.dumps(result))",
            Path.Combine(AppContext.BaseDirectory, "mw3_re_launch.py") }) info.ArgumentList.Add(argument);
        using var child = System.Diagnostics.Process.Start(info) ?? throw new Exception("Python planner test child did not start.");
        child.StandardInput.Write(json);
        child.StandardInput.Close();
        var output = child.StandardOutput.ReadToEnd();
        var error = child.StandardError.ReadToEnd();
        child.WaitForExit();
        if (child.ExitCode != 0) throw new Exception("Actual Python planner rejected projected JSON: " + error);
        return JsonNode.Parse(output)!;
    }

    private static string WithManifestFields(string baseJson, params string[] fields) =>
        fields.Length == 0 ? baseJson : baseJson[..^1] + "," + string.Join(",", fields) + "}";

    private static void CheckLegacyProfileRouting(string root)
    {
        const string profile = """{"schema_version":1,"graphics":{},"native":{"installation_layout":1,"runtime_environment":{"MW34_SEED":"host","MW34_STARTUP":"loader"}}}""";
        var settings = new LauncherSettings
        {
            Width = 1280, Height = 720, AntiAliasing = "off", AnisotropicFiltering = 1,
            WindowMode = "windowed", DynamicLighting = false, Headlights = false,
            PerformanceMonitor = false, LocalCdAudio = false
        };
        NativeRuntimeLayout.ResolveProfile(profile, root);
        GameRunner.CreateLaunchProfile(profile, settings);
        foreach (var invalid in new[]
        {
            WithManifestFields(profile, "\"engine\":\"mw3-re\""),
            WithManifestFields(profile, "\"Engine\":null"),
            profile.Replace("\"schema_version\":1", "\"schema_version\":2"),
            profile.Replace("\"schema_version\":1", "\"Schema_Version\":1"),
            profile.Replace("\"schema_version\":1", "\"schema_version\":true"),
            profile.Replace("\"installation_layout\":1", "\"installation_layout\":1,\"engine\":\"mw3-re\"")
        })
        {
            RejectLegacyJson("ResolveProfile routing", "routing", () => NativeRuntimeLayout.ResolveProfile(invalid, root));
            RejectLegacyJson("CreateLaunchProfile routing", "routing", () => GameRunner.CreateLaunchProfile(invalid, settings));
        }
        foreach (var fields in new[]
        {
            "\"note\":1,\"note\":2",
            "\"note\":1,\"\\u006eote\":2",
            "\"data\":{\"__type\":\"a\",\"__type\":\"b\"}",
            "\"data\":[{\"item\":1,\"item\":2}]",
            "\"data\":{\"\":1,\"\":2}"
        })
        {
            var invalid = WithManifestFields(profile, fields);
            RejectLegacyJson("ResolveProfile duplicate", "Duplicate JSON", () => NativeRuntimeLayout.ResolveProfile(invalid, root));
            RejectLegacyJson("CreateLaunchProfile duplicate", "Duplicate JSON", () => GameRunner.CreateLaunchProfile(invalid, settings));
        }
        var repeatedValues = WithManifestFields(profile, "\"data\":[{\"item\":1},{\"item\":1}],\"values\":[1,1]");
        NativeRuntimeLayout.ResolveProfile(repeatedValues, root);
        GameRunner.CreateLaunchProfile(repeatedValues, settings);
        var oversized = WithManifestFields(profile, "\"note\":\"" + new string('x', PackStorage.MaxJsonBytes) + "\"");
        RejectLegacyJson("ResolveProfile size", "large", () => NativeRuntimeLayout.ResolveProfile(oversized, root));
        RejectLegacyJson("CreateLaunchProfile size", "large", () => GameRunner.CreateLaunchProfile(oversized, settings));
    }

    private static void RejectLegacyJson(string entryPoint, string reason, Action action)
    {
        try { action(); }
        catch (InvalidDataException error) when (error.Message.Contains(reason, StringComparison.OrdinalIgnoreCase)) { return; }
        catch (Exception error) { throw new Exception(entryPoint + " rejected input for the wrong reason.", error); }
        throw new Exception(entryPoint + " accepted invalid legacy JSON; expected " + reason + ".");
    }
    private static void RejectEngineRouted(string entryPoint, string input, Action action)
    {
        try { action(); }
        catch (InvalidDataException error) when (error.Message.Contains("engine", StringComparison.OrdinalIgnoreCase) ||
            error.Message.Contains("routing", StringComparison.OrdinalIgnoreCase))
        { return; }
        catch (InvalidDataException error)
        {
            throw new Exception(entryPoint + " rejected engine-tagged input (" + input + ") for a non-routing reason: " + error.Message);
        }
        throw new Exception(entryPoint + " accepted engine-tagged schema1 descriptor (" + input +
            "); an explicit engine must not remain eligible for legacy selection.");
    }
    private static void Reject(Action action)
    {
        try { action(); }
        catch (Exception error) when (error is InvalidDataException or IOException) { return; }
        throw new Exception("Invalid installed runtime unexpectedly accepted.");
    }
}
