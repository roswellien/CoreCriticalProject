using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Reflection.PortableExecutable;

namespace MW3RemasterLauncher.Core;

/// <summary>Application-local native launch files. A present but incomplete install never falls back to a checkout.</summary>
public sealed record NativeRuntimeLayout(string Root, string Profile, string Coordinator, string Python)
{
    public static void ValidateLaunchExecutable(string path)
    {
        PackStorage.EnsureNoLinks(path);
        try
        {
            using var input = File.OpenRead(path);
            using var image = new PEReader(input);
            var headers = image.PEHeaders;
            var pe = headers.PEHeader;
            if (headers.CoffHeader.Machine != Machine.Amd64 ||
                (headers.CoffHeader.Characteristics & Characteristics.ExecutableImage) == 0 ||
                (headers.CoffHeader.Characteristics & Characteristics.Dll) != 0 ||
                pe == null || pe.Magic != PEMagic.PE32Plus || pe.AddressOfEntryPoint <= 0 ||
                !headers.SectionHeaders.Any(section =>
                    (section.SectionCharacteristics & SectionCharacteristics.MemExecute) != 0 &&
                    pe.AddressOfEntryPoint >= section.VirtualAddress &&
                    (long)pe.AddressOfEntryPoint < (long)section.VirtualAddress + Math.Max(section.VirtualSize, section.SizeOfRawData)))
                throw new InvalidDataException("This game update contains an invalid launch executable. Install a corrected game update.");
        }
        catch (BadImageFormatException error)
        {
            throw new InvalidDataException("This game update contains an invalid launch executable. Install a corrected game update.", error);
        }
    }

    public static bool HasPrecompiledRuntime(string applicationDirectory)
    {
        var manifest = Path.Combine(applicationDirectory, "Runtime", "runtime.json");
        if (!File.Exists(manifest)) return false;
        PackStorage.EnsureNoLinks(manifest);
        if (new FileInfo(manifest).Length > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Installed runtime manifest is too large.");
        using var document = JsonDocument.Parse(File.ReadAllText(manifest));
        if (!document.RootElement.TryGetProperty("precompiled_runtime_version", out var version)) return false;
        if (version.GetInt32() != 1) throw new InvalidDataException("Unsupported precompiled runtime version.");
        return true;
    }

    public static bool IsInstalledApplication(string directory) =>
        Directory.Exists(Path.Combine(directory, "Runtime")) || File.Exists(Path.Combine(directory, "launcher-installation.json"));

    public static NativeRuntimeLayout? FindInstalled(string applicationDirectory, string? dataRoot = null)
    {
        var selected = RuntimeUpdates.SelectedRoot(applicationDirectory, dataRoot);
        var root = selected ?? Path.Combine(applicationDirectory, "Runtime");
        var manifestPath = Path.Combine(root, "runtime.json");
        if (!File.Exists(manifestPath))
        {
            if (selected != null || Directory.Exists(root)) throw new InvalidDataException("The installed game runtime is incomplete. Repair the installation.");
            if (IsInstalledApplication(applicationDirectory))
                throw new FileNotFoundException("This launcher preview can set up original files and packs. The remaining game components must be prepared before Play is available.");
            return null; // Existing development launches remain available until a runtime is installed.
        }
        return ReadRoot(root);
    }

    public static NativeRuntimeLayout ReadRoot(string root)
    {
        var manifestPath = PackStorage.Resolve(root, "runtime.json");
        PackStorage.EnsureNoLinks(manifestPath);
        if (new FileInfo(manifestPath).Length > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Installed runtime manifest is too large.");
        using var manifest = JsonDocument.Parse(File.ReadAllText(manifestPath));
        var document = manifest.RootElement;
        if (document.GetProperty("schema_version").GetInt32() != 1)
            throw new InvalidDataException("Unsupported installed runtime version.");
        var files = document.GetProperty("files");
        if (files.EnumerateObject().Count() > 20000) throw new InvalidDataException("Excessive runtime file table.");
        string Registered(string name)
        {
            var path = PackStorage.Resolve(root, name);
            if (!files.TryGetProperty(name, out var pin)) throw new InvalidDataException("Unregistered runtime file " + name);
            using var stream = File.OpenRead(path);
            if (stream.Length != pin.GetProperty("bytes").GetInt64() ||
                !Convert.ToHexString(SHA256.HashData(stream)).Equals(pin.GetProperty("sha256").GetString(), StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Installed runtime file changed: " + name + ". Repair the installation.");
            return path;
        }
        string Required(string field) => Registered(document.GetProperty(field).GetString()
            ?? throw new InvalidDataException("Missing runtime " + field));
        if (document.TryGetProperty("native_modules", out var modules))
        {
            if (modules.ValueKind != JsonValueKind.Array || modules.GetArrayLength() is < 1 or > 16)
                throw new InvalidDataException("Invalid native module table.");
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var module in modules.EnumerateArray())
            {
                var name = module.GetString() ?? "";
                if (!name.EndsWith(".dll", StringComparison.OrdinalIgnoreCase) || !seen.Add(name))
                    throw new InvalidDataException("Invalid or duplicate native module.");
                Registered(name);
            }
        }
        return new(root, Required("profile"), Required("coordinator"), Required("python"));
    }

    /// <summary>Resolve only explicitly marked installation paths; preserve numeric flags and user pack choices.</summary>
    public static string ResolveProfile(string json, string root, string? gameDirectory = null)
    {
        var profile = JsonNode.Parse(json)?.AsObject() ?? throw new InvalidDataException("Empty installed profile.");
        JsonNode? Resolve(JsonNode? node)
        {
            if (node is JsonObject obj)
                foreach (var name in obj.Select(p => p.Key).ToArray())
                {
                    var old = obj[name];
                    var resolved = Resolve(old);
                    if (!ReferenceEquals(old, resolved)) obj[name] = resolved;
                }
            else if (node is JsonArray array)
                for (var i = 0; i < array.Count; i++)
                {
                    var old = array[i];
                    var resolved = Resolve(old);
                    if (!ReferenceEquals(old, resolved)) array[i] = resolved;
                }
            else if (node is JsonValue value && value.TryGetValue<string>(out var text) && text.StartsWith("@runtime/", StringComparison.Ordinal))
                return JsonValue.Create(PackStorage.Resolve(root, text[9..]));
            else if (node is JsonValue gameValue && gameValue.TryGetValue<string>(out var gameText) && gameText.StartsWith("@game/", StringComparison.Ordinal))
                return JsonValue.Create(PackStorage.Resolve(gameDirectory ?? throw new InvalidDataException("Select original game data first."), gameText[6..]));
            return node;
        }
        Resolve(profile);
        if (profile["native"]?["installation_layout"]?.GetValue<int>() != 1 ||
            profile["native"]?["runtime_environment"]?["MW34_SEED"]?.GetValue<string>() != "host" ||
            profile["native"]?["runtime_environment"]?["MW34_STARTUP"]?.GetValue<string>() != "loader")
            throw new InvalidDataException("Installed runtime requires host-initialized loader startup.");
        return GameRunner.SerializeLaunchProfile(profile);
    }
}
