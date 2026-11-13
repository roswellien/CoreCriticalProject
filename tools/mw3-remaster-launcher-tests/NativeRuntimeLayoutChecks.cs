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
            Console.WriteLine("MW3-RE stage A installed-descriptor engine routing checks passed.");
        }
        finally { Directory.Delete(app, true); }
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
