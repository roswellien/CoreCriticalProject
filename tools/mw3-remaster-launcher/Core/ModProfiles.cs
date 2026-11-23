using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Named user profiles; native CLI validation precedes every activation.</summary>
public sealed class ModProfiles
{
    private readonly string root;
    public ModProfiles(string dataRoot) => root = Path.Combine(Path.GetFullPath(dataRoot), "content-profiles");
    public string DirectoryPath => root;
    public IReadOnlyList<string> List() => Directory.Exists(root)
        ? Directory.GetFiles(root, "*.json").Where(path => !Path.GetFileName(path).StartsWith('.')).Order().ToArray()
        : Array.Empty<string>();

    public static bool SamePin(JsonNode? saved, JsonNode? installed) =>
        saved?["id"]?.ToString() == installed?["id"]?.ToString() &&
        saved?["version"]?.ToString() == installed?["version"]?.ToString() &&
        saved?["sha256"]?.ToString() == installed?["sha256"]?.ToString();

    public static IReadOnlyList<JsonObject> UnavailablePins(JsonArray saved, IEnumerable<JsonObject> installed) =>
        saved.OfType<JsonObject>().Where(pin => !installed.Any(candidate => SamePin(pin, candidate)))
            .Select(pin => (JsonObject)pin.DeepClone()).ToArray();

    public async Task<string> SaveAsync(string text, ContentToolClient tool, string store)
    {
        var value = JsonNode.Parse(text)?.AsObject() ?? throw new InvalidDataException("Profile must be an object.");
        var id = value["id"]?.GetValue<string>() ?? "";
        if (!Regex.IsMatch(id, @"\A[a-z0-9][a-z0-9._-]{0,95}\z") || id is "." or "..")
            throw new InvalidDataException("Use a lowercase profile ID containing letters, digits, dots, underscores or hyphens.");
        Directory.CreateDirectory(root);
        var target = Path.Combine(root, id + ".json");
        var staging = Path.Combine(root, "." + Guid.NewGuid().ToString("N") + ".json");
        try
        {
            await File.WriteAllTextAsync(staging, value.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
            var resolved = await tool.RunAsync(new[] { "resolve", staging, "--store", Path.GetFullPath(store) });
            var selected = value["packages"]?.AsArray() ?? throw new InvalidDataException("Profile omitted its packages.");
            var locked = resolved["content"]?["lock"]?["packages"]?.AsArray()
                ?? throw new InvalidDataException("Content tool omitted its resolved package lock.");
            var pins = new JsonArray();
            foreach (var entry in locked)
            {
                var pin = entry!.DeepClone().AsObject();
                var request = selected.FirstOrDefault(item => item?["id"]?.ToString() == pin["id"]?.ToString());
                if (request?["path"] is JsonNode path) pin["path"] = path.DeepClone();
                pins.Add(pin);
            }
            value["packages"] = pins;
            await File.WriteAllTextAsync(staging, value.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
            await tool.RunAsync(new[] { "resolve", staging, "--store", Path.GetFullPath(store) });
            if (File.Exists(target)) File.Replace(staging, target, target + ".previous");
            else File.Move(staging, target);
            return target;
        }
        finally { if (File.Exists(staging)) File.Delete(staging); }
    }

    public async Task<JsonObject> InspectAsync(JsonObject profile, ContentToolClient tool, string store)
    {
        Directory.CreateDirectory(root);
        var staging = Path.Combine(root, "." + Guid.NewGuid().ToString("N") + ".json");
        try
        {
            await File.WriteAllTextAsync(staging, profile.ToJsonString());
            return await tool.RunAsync(new[] { "inspect", staging, "--store", Path.GetFullPath(store) });
        }
        finally { if (File.Exists(staging)) File.Delete(staging); }
    }

    public static ProcessStartInfo LaunchInfo(LauncherSettings settings, string gameDirectory, string writeDirectory)
    {
        var executable = Path.GetFullPath(settings.ModularRuntimeExecutable);
        if (!File.Exists(executable)) throw new FileNotFoundException("Select the MW3-RE runtime executable.", executable);
        var start = new ProcessStartInfo(executable)
        {
            UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(executable)!
        };
        foreach (var argument in new[] { "--install", Path.GetFullPath(gameDirectory), "--write-dir", Path.GetFullPath(writeDirectory),
            "--content-profile", Path.GetFullPath(settings.ModularContentProfile), "--content-store", Path.GetFullPath(settings.ModularContentStore) })
            start.ArgumentList.Add(argument);
        if (settings.WindowMode == "windowed") start.ArgumentList.Add("--windowed");
        return start;
    }

    public static Process Launch(LauncherSettings settings, string gameDirectory, string dataRoot, Action<string>? log)
    {
        var tool = new ContentToolClient(settings.ModularContentTool);
        tool.RunAsync(new[] { "resolve", Path.GetFullPath(settings.ModularContentProfile), "--store", Path.GetFullPath(settings.ModularContentStore) })
            .GetAwaiter().GetResult();
        var write = Path.Combine(Path.GetFullPath(dataRoot), "mw3-re", "profiles",
            Path.GetFileNameWithoutExtension(settings.ModularContentProfile));
        Directory.CreateDirectory(write);
        var start = LaunchInfo(settings, gameDirectory, write);
        log?.Invoke("Starting MW3-RE with validated content profile " + settings.ModularContentProfile);
        var process = Process.Start(start) ?? throw new IOException("MW3-RE did not start.");
        log?.Invoke("MW3-RE PID " + process.Id);
        return process;
    }
}
