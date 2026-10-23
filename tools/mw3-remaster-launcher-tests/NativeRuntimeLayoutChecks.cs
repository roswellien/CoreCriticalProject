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
            Console.WriteLine("Installed runtime discovery, containment, integrity and startup checks passed.");
        }
        finally { Directory.Delete(app, true); }
    }
    private static void Reject(Action action)
    {
        try { action(); }
        catch (Exception error) when (error is InvalidDataException or IOException) { return; }
        throw new Exception("Invalid installed runtime unexpectedly accepted.");
    }
}
