using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class NativeRuntimeLayoutChecks
{
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
            var pins = new JsonObject();
            foreach (var relative in new[] { "bin/mw3.exe", "profile.json", "support.txt" })
            {
                var bytes = File.ReadAllBytes(Path.Combine(root, relative));
                pins[relative] = new JsonObject { ["bytes"] = bytes.Length, ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes)) };
            }
            var descriptor = new JsonObject
            {
                ["schema_version"] = 2, ["engine"] = "mw3-re",
                ["roles"] = new JsonObject { ["executable"] = "bin/mw3.exe", ["profile"] = "profile.json" },
                ["dependencies"] = new JsonArray("support.txt"), ["files"] = pins,
                ["provenance"] = new JsonObject { ["source_commit"] = new string('a', 40), ["build_id"] = "authored-build", ["builder"] = "fixture" },
                ["capabilities"] = new JsonObject { ["authored-capability"] = new JsonArray(1, 2) }
            };
            File.WriteAllText(Path.Combine(root, "runtime.json"), GameRunner.SerializeLaunchProfile(descriptor));
            var before = Directory.GetFiles(root, "*", SearchOption.AllDirectories)
                .ToDictionary(path => path, path => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))));
            var type = typeof(Mw3ReRuntimeContract);
            var contract = Mw3ReRuntimeContract.ReadStructure(root);
            if (contract.Root != Path.GetFullPath(root) || contract.Executable != Path.Combine(root, "bin", "mw3.exe"))
                throw new Exception("Integrity snapshot did not preserve its root/executable identity.");
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
                json["dependencies"] = new JsonArray("absent.bin");
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
                    json["dependencies"] = new JsonArray("linked/support.txt");
                    json["files"]!["linked/support.txt"] = json["files"]!["support.txt"]!.DeepClone();
                    json["files"]!.AsObject().Remove("support.txt");
                }, "link");
            }
            finally { Directory.Delete(link); }
            Console.WriteLine("Native integrity snapshot: schema, closure, hash, bounds and immutable-interface controls passed.");
        }
        finally { Directory.Delete(root, true); }
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
