using System.IO;
using System.Security.Cryptography;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Data-only soundtrack pack. Paths are pack-relative; decoders come from the runtime.</summary>
public static class MusicPack
{
    public const string Profile = "prepared-music-v1";
    public const string Registry = "music/music.json";

    private static JsonObject ReadVerifiedInputs(string directory, PackManifest manifest, JsonNode? decoder)
    {
        var registry = PackStorage.Resolve(directory, Registry);
        if (manifest.SchemaVersion != 2 || manifest.NativePayload?.Profile != Profile ||
            manifest.Files == null || !manifest.Files.TryGetValue(Registry, out var declared))
            throw new InvalidDataException("Unsupported soundtrack component.");
        using var input = File.OpenRead(registry);
        if (input.Length != declared.Bytes || !Convert.ToHexString(SHA256.HashData(input)).Equals(declared.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Soundtrack registry integrity check failed.");
        return ReadInputs(directory, manifest, decoder);
    }

    public static JsonObject ReadInputs(string directory, PackManifest manifest, JsonNode? decoder = null)
    {
        var path = PackStorage.Resolve(directory, Registry);
        if (new FileInfo(path).Length > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Music registry is too large.");
        var data = JsonNode.Parse(File.ReadAllText(path))!;
        if (data["schema_version"]?.GetValue<int>() != 2 || data["payload_profile"]?.GetValue<string>() != Profile)
            throw new InvalidDataException("Unsupported soundtrack registry.");
        var tracks = data["tracks"]?.AsArray();
        if (tracks == null || tracks.Count != 2)
            throw new InvalidDataException("Soundtrack packs require CD tracks 2 and 3.");
        var resolved = new JsonArray();
        var sources = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        for (var i = 0; i < 2; ++i)
        {
            if (tracks[i]?["cd_track"]?.GetValue<int>() != i + 2)
                throw new InvalidDataException("Soundtrack tracks must be ordered 2, 3.");
            var name = tracks[i]!["source"]!.GetValue<string>();
            var extension = Path.GetExtension(name);
            if ((!extension.Equals(".wav", StringComparison.OrdinalIgnoreCase) &&
                 !extension.Equals(".flac", StringComparison.OrdinalIgnoreCase)) || !sources.Add(name))
                throw new InvalidDataException("Soundtrack sources must be two distinct FLAC or PCM WAV files.");
            var source = PackStorage.Resolve(directory, name);
            if (!manifest.Files!.TryGetValue(name, out var declared) || !File.Exists(source) ||
                new FileInfo(source).Length != declared.Bytes)
                throw new InvalidDataException("Missing or undeclared soundtrack source: " + name);
            using var input = File.OpenRead(source);
            if (!Convert.ToHexString(SHA256.HashData(input)).Equals(declared.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Soundtrack integrity check failed: " + name);
            resolved.Add(new JsonObject { ["cd_track"] = i + 2, ["source"] = source });
        }
        return new JsonObject { ["schema_version"] = 2, ["enabled"] = true,
            ["decoder"] = decoder?.DeepClone(), ["tracks"] = resolved };
    }

    /// <summary>First enabled pack wins, matching the launcher's displayed priority.</summary>
    public static bool Apply(JsonObject profile, IEnumerable<string> directories, bool enabled, string? originalGameDirectory = null)
    {
        string? selected = null;
        PackManifest? manifest = null;
        foreach (var directory in directories)
        {
            var candidate = PackStorage.ReadManifest(Path.Combine(directory, "pack.json"));
            if (candidate.SchemaVersion == 2 && candidate.NativePayload?.Profile == Profile)
            { selected = directory; manifest = candidate; break; }
            if (candidate.Provides?.CdMusic == true)
                throw new InvalidDataException("Convert this soundtrack pack to prepared-music-v1: " + candidate.Name);
        }
        var native = profile["native"]!.AsObject();
        native.Remove("music_inputs");
        native["runtime_environment"]?.AsObject().Remove("MW34_MUSIC_PACK");
        native["local_cd_audio"] = enabled && selected != null;
        if (enabled && selected != null)
        {
            RuntimeContentCapabilities.Require(native, manifest!.NativePayload!, manifest.Id);
            native["music_inputs"] = ReadVerifiedInputs(selected, manifest, native["music_decoder"]);
        }
        else if (enabled && originalGameDirectory != null)
        {
            // Original user-supplied CD tracks are base game resources. A music
            // replacement pack takes priority, but is not required to play them.
            var first = Path.Combine(originalGameDirectory, "Music", "1-02. MechWarrior 3 - Track 01.flac");
            var second = Path.Combine(originalGameDirectory, "Music", "1-03. MechWarrior 3 - Track 02.flac");
            if (File.Exists(first) && File.Exists(second))
            {
                native["local_cd_audio"] = true;
                native["music_inputs"] = new JsonObject
                {
                    ["schema_version"] = 2, ["enabled"] = true,
                    ["decoder"] = native["music_decoder"]?.DeepClone(),
                    ["tracks"] = new JsonArray(
                        new JsonObject { ["cd_track"] = 2, ["source"] = Path.GetFullPath(first) },
                        new JsonObject { ["cd_track"] = 3, ["source"] = Path.GetFullPath(second) })
                };
            }
        }
        if (enabled && !native["local_cd_audio"]!.GetValue<bool>() && native["stock_soundtrack"] is JsonObject stock)
        {
            if (stock["schema_version"]?.GetValue<int>() != 1 || stock["root"]?.GetValue<string>() is not string directory ||
                !Path.IsPathFullyQualified(directory))
                throw new InvalidDataException("Default soundtrack metadata is incompatible. Repair the game runtime.");
            var stockManifest = PackStorage.ReadManifest(PackStorage.Resolve(directory, "pack.json"));
            if (stockManifest.NativePayload?.Profile != Profile)
                throw new InvalidDataException("Default soundtrack component is incompatible. Repair the game runtime.");
            RuntimeContentCapabilities.Require(native, stockManifest.NativePayload!, stockManifest.Id);
            native["music_inputs"] = ReadVerifiedInputs(directory, stockManifest, native["music_decoder"]);
            native["local_cd_audio"] = true;
        }
        return selected != null;
    }
}
