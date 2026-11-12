using System.Text.Json.Nodes;
using System.IO;
using MW3RemasterLauncher.Core;

internal static class ModProfilesChecks
{
    public static async Task Run(string contentTool)
    {
        var root = Path.Combine(Path.GetTempPath(), "corecritical-content-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var tool = new ContentToolClient(contentTool);
            await tool.RunAsync(new[] { "capabilities" });
            var source = Path.Combine(root, "authored source");
            Directory.CreateDirectory(source);
            await File.WriteAllTextAsync(Path.Combine(source, "pack.json"), """
                {"schema_version":3,"game_id":"mw3","id":"authored-demo","version":"1.0.0",
                 "files":{},"definitions":[],"patches":[],"dependencies":[],"required_capabilities":{}}
                """);
            var compiled = Path.Combine(root, "compiled");
            await tool.RunAsync(new[] { "compile", source, compiled });
            var store = Path.Combine(root, "store");
            await tool.RunAsync(new[] { "install", compiled, "--store", store });
            var inventory = await tool.RunAsync(new[] { "list", "--store", store });
            if (inventory["packages"] is not JsonArray rows || rows.Count != 1)
                throw new Exception("Native inventory did not retain the installed exact version.");
            var exactPin = rows[0]!.DeepClone();
            var manifestPath = Path.Combine(source, "pack.json");
            var alteredManifest = JsonNode.Parse(await File.ReadAllTextAsync(manifestPath))!.AsObject();
            alteredManifest["name"] = "Same version, different package integrity";
            await File.WriteAllTextAsync(manifestPath, alteredManifest.ToJsonString());
            await tool.RunAsync(new[] { "install", source, "--store", store });
            var variants = (await tool.RunAsync(new[] { "list", "--store", store }))["packages"]!.AsArray();
            if (variants.Count != 2 || variants.Count(pin => ModProfiles.SamePin(exactPin, pin)) != 1)
                throw new Exception("A saved integrity pin selected multiple same-version packages.");
            var replacement = variants.Single(pin => !ModProfiles.SamePin(exactPin, pin));
            var missing = ModProfiles.UnavailablePins(new JsonArray(exactPin.DeepClone()), new[] { replacement!.AsObject() });
            if (missing.Count != 1 || !JsonNode.DeepEquals(missing[0], exactPin))
                throw new Exception("An unavailable exact hash was dropped or replaced by another package of the same version.");
            var profiles = new ModProfiles(root);
            var text = """
                {"schema_version":1,"id":"my-profile","packages":[{"id":"authored-demo","version":"1.0.0"}],"selections":{}}
                """;
            var path = await profiles.SaveAsync(text, tool, store);
            var original = File.ReadAllText(path);
            bool refused = false;
            try { await profiles.SaveAsync(text.Replace("1.0.0", "9.9.9"), tool, store); }
            catch (ContentToolException) { refused = true; }
            if (!refused || File.ReadAllText(path) != original) throw new Exception("Rejected pins changed a saved profile.");
            refused = false;
            try { await profiles.SaveAsync(text.Replace("my-profile", "../escape"), tool, store); }
            catch (InvalidDataException) { refused = true; }
            if (!refused) throw new Exception("A profile name escaped its storage directory.");
            var librarySource = Path.Combine(root, "library");
            Directory.CreateDirectory(librarySource);
            var library = (JsonObject)alteredManifest.DeepClone();
            library["id"] = "transitive-library";
            await File.WriteAllTextAsync(Path.Combine(librarySource, "pack.json"), library.ToJsonString());
            await tool.RunAsync(new[] { "install", librarySource, "--store", store });
            var dependentSource = Path.Combine(root, "dependent");
            Directory.CreateDirectory(dependentSource);
            var dependent = (JsonObject)alteredManifest.DeepClone();
            dependent["id"] = "authored-with-dependency";
            dependent["dependencies"] = new JsonArray(new JsonObject { ["id"] = "transitive-library", ["min_version"] = "1.0.0" });
            await File.WriteAllTextAsync(Path.Combine(dependentSource, "pack.json"), dependent.ToJsonString());
            var requested = new JsonObject { ["schema_version"] = 1, ["id"] = "locked-dependencies", ["selections"] = new JsonObject(),
                ["packages"] = new JsonArray(new JsonObject { ["id"] = "authored-with-dependency", ["version"] = "1.0.0", ["path"] = dependentSource }) };
            var dependencyProfile = await profiles.SaveAsync(requested.ToJsonString(), tool, store);
            var savedPins = JsonNode.Parse(await File.ReadAllTextAsync(dependencyProfile))!["packages"]!.AsArray();
            if (savedPins.Count != 2 || savedPins.Any(pin => pin?["sha256"]?.ToString().Length != 64) ||
                savedPins.Single(pin => pin?["id"]?.ToString() == "authored-with-dependency")?["path"]?.ToString() != dependentSource)
                throw new Exception("Saved profile did not preserve the complete exact lock and explicit root path.");
            library["version"] = "2.0.0";
            await File.WriteAllTextAsync(Path.Combine(librarySource, "pack.json"), library.ToJsonString());
            await tool.RunAsync(new[] { "install", librarySource, "--store", store });
            var dependencyResolution = await tool.RunAsync(new[] { "resolve", dependencyProfile, "--store", store });
            var resolvedPins = dependencyResolution["content"]!["lock"]!["packages"]!.AsArray();
            if (resolvedPins.Single(pin => pin?["id"]?.ToString() == "transitive-library")?["version"]?.ToString() != "1.0.0")
                throw new Exception("Installing a new dependency silently upgraded a saved profile.");
            var settings = new LauncherSettings { ModularRuntimeExecutable = contentTool,
                ModularContentProfile = path, ModularContentStore = store, WindowMode = "windowed" };
            var start = ModProfiles.LaunchInfo(settings, Path.Combine(root, "game 'quoted'"), Path.Combine(root, "saves"));
            if (start.UseShellExecute || !start.ArgumentList.Contains("--content-profile") ||
                !start.ArgumentList.Contains(path) || !start.ArgumentList.Contains("--windowed"))
                throw new Exception("Native profile launch did not preserve structured arguments.");
            Console.WriteLine("Native content profile installation, pinning, rejection preservation and launch arguments passed.");
        }
        finally { Directory.Delete(root, recursive: true); }
    }
}
