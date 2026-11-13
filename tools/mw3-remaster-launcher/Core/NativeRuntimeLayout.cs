using System.IO;
using System.Security.Cryptography;
using System.Text;
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

    private static void ValidateLegacyRouting(JsonElement document)
    {
        if (document.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("Legacy routing requires a JSON object.");
        PackStorage.ValidateUniqueProperties(document);
        foreach (var property in document.EnumerateObject())
        {
            if (property.Name.Equals("engine", StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("A legacy runtime cannot declare an explicit engine routing field.");
            if (property.Name.Equals("schema_version", StringComparison.OrdinalIgnoreCase) &&
                (property.Name != "schema_version" || property.Value.ValueKind != JsonValueKind.Number ||
                 !property.Value.TryGetInt32(out var version) || version != 1))
                throw new InvalidDataException("Unsupported legacy routing schema.");
            if (property.Name.Equals("native", StringComparison.OrdinalIgnoreCase) &&
                property.Value.ValueKind == JsonValueKind.Object)
            {
                foreach (var binding in property.Value.EnumerateObject())
                    if (binding.Name.Equals("engine", StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("A legacy profile cannot declare native engine routing.");
            }
        }
    }

    internal static JsonObject ParseLegacyProfile(string json)
    {
        if (Encoding.UTF8.GetByteCount(json) > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Legacy profile JSON is too large.");
        try
        {
            using var document = JsonDocument.Parse(json, new JsonDocumentOptions { MaxDepth = 64 });
            ValidateLegacyRouting(document.RootElement);
            // Parse this immutable snapshot, never a second file read that could differ.
            return JsonNode.Parse(json)!.AsObject();
        }
        catch (JsonException error)
        {
            throw new InvalidDataException("Invalid legacy profile JSON.", error);
        }
    }

    internal static string ReadJsonSnapshot(string path)
    {
        PackStorage.EnsureNoLinks(path);
        using var stream = File.OpenRead(path);
        var buffer = new byte[PackStorage.MaxJsonBytes + 1];
        var count = 0;
        while (count < buffer.Length)
        {
            var read = stream.Read(buffer, count, buffer.Length - count);
            if (read == 0) break;
            count += read;
        }
        if (count > PackStorage.MaxJsonBytes) throw new InvalidDataException("Runtime JSON is too large.");
        using var snapshot = new MemoryStream(buffer, 0, count, false);
        using var reader = new StreamReader(snapshot, Encoding.UTF8, true);
        var json = reader.ReadToEnd();
        if (Encoding.UTF8.GetByteCount(json) > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Runtime JSON is too large.");
        return json;
    }

    public static bool HasPrecompiledRuntime(string applicationDirectory)
    {
        var manifest = Path.Combine(applicationDirectory, "Runtime", "runtime.json");
        if (!File.Exists(manifest)) return false;
        PackStorage.EnsureNoLinks(manifest);
        using var document = JsonDocument.Parse(ReadJsonSnapshot(manifest));
        ValidateLegacyRouting(document.RootElement);
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
        using var manifest = JsonDocument.Parse(ReadJsonSnapshot(manifestPath));
        var document = manifest.RootElement;
        ValidateLegacyRouting(document);
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
        var profile = ParseLegacyProfile(json);
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
