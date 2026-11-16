using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Data-only soundtrack pack. Paths are pack-relative; decoders come from the runtime.</summary>
public static class MusicPack
{
    public const string Profile = "prepared-music-v1";
    public const string Registry = "music/music.json";
    private const string StagedRecord = "launcher-staged.json";

    private sealed record StagedTrack(string FileName, long Bytes, string Sha256, string PackId, string PackVersion);


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

    /// <summary>Expose enabled soundtrack packs to MW3-RE's write-directory music lookup.</summary>
    public static int StageForNative(IEnumerable<string> directories, string writeDirectory, Action<string>? log = null)
    {
        string? selected = null;
        PackManifest? manifest = null;
        foreach (var directory in directories)
        {
            var root = PackStorage.CanonicalPackRoot(directory);
            var candidate = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
            if (candidate.SchemaVersion == 2 && candidate.NativePayload?.Profile == Profile)
            {
                selected = root;
                manifest = candidate;
                break;
            }
        }
        var musicDirectory = Path.Combine(Path.GetFullPath(writeDirectory), "music");
        PackStorage.EnsureNoLinks(musicDirectory);
        if (selected != null || Directory.Exists(musicDirectory))
        {
            Directory.CreateDirectory(musicDirectory);
            PackStorage.EnsureNoLinks(musicDirectory);
        }

        var recordPath = Path.Combine(musicDirectory, StagedRecord);
        PackStorage.EnsureNoLinks(recordPath);
        var recorded = ReadStagedRecord(recordPath);
        var owned = new Dictionary<string, StagedTrack>(StringComparer.OrdinalIgnoreCase);
        if (recorded != null)
        {
            foreach (var item in recorded)
            {
                var path = Path.Combine(musicDirectory, item.FileName);
                PackStorage.EnsureNoLinks(path);
                if (File.Exists(path) && FileMatchesRecord(path, item)) owned[item.FileName] = item;
                else log?.Invoke($"MW3-RE soundtrack file {item.FileName} changed after staging and is now treated as user music.");
            }
        }

        var tracks = selected == null ? new List<(int Number, string Source, string FileName)>() :
            ReadVerifiedInputs(selected, manifest!, null).AsObject()["tracks"]!.AsArray()
                .Select(track =>
                {
                    var number = track!["cd_track"]!.GetValue<int>();
                    var source = track["source"]!.GetValue<string>();
                    return (Number: number, Source: source, FileName: $"track{number:00}{Path.GetExtension(source).ToLowerInvariant()}");
                }).ToList();
        // A launcher-staged file the enabled pack no longer supplies under the same name is removed. A file
        // that cannot be removed now (for example still open) stays recorded and is retried next launch.
        foreach (var previous in owned.Values.ToArray())
        {
            var stillSupplied = tracks.Any(track =>
                track.FileName.Equals(previous.FileName, StringComparison.OrdinalIgnoreCase));
            if (stillSupplied) continue;
            try
            {
                File.Delete(Path.Combine(musicDirectory, previous.FileName));
                owned.Remove(previous.FileName);
                log?.Invoke($"MW3-RE launcher-staged soundtrack {previous.FileName} removed because the enabled pack no longer supplies it.");
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException)
            {
                log?.Invoke($"MW3-RE launcher-staged soundtrack {previous.FileName} could not be removed yet: {error.Message}");
            }
        }

        var staged = 0;
        // Every format MW3-RE looks for. A file of any of them that the launcher did not stage belongs to the
        // player, and the pack then leaves that track number alone whichever format would win the lookup.
        var extensions = new[] { ".ogg", ".flac", ".wav", ".mp3" };
        try
        {
            foreach (var track in tracks)
            {
                var number = track.Number;
                var source = track.Source;
                var destination = Path.Combine(musicDirectory, track.FileName);
                var playerFile = extensions
                    .Select(item => Path.Combine(musicDirectory, $"track{number:00}{item}"))
                    .FirstOrDefault(path => File.Exists(path) && !owned.ContainsKey(Path.GetFileName(path)));
                if (playerFile != null)
                {
                    log?.Invoke($"MW3-RE soundtrack track {number:00} was left out because {playerFile} is the player's own.");
                    continue;
                }
                try
                {
                    StagedTrack currentRecord;
                    using (var sourceStream = File.OpenRead(source))
                        currentRecord = new StagedTrack(track.FileName, sourceStream.Length,
                            Convert.ToHexString(SHA256.HashData(sourceStream)).ToLowerInvariant(),
                            manifest!.Id, manifest.Version);
                    PackStorage.EnsureNoLinks(destination);
                    if (File.Exists(destination) && FilesMatch(source, destination))
                    {
                        log?.Invoke($"MW3-RE soundtrack track {number:00} is already current.");
                        owned[track.FileName] = currentRecord;
                        continue;
                    }
                    // A copy, not a hard link: a player editing the profile track must not change the
                    // installed, hash-verified pack file. The copy goes to a temporary name first so a
                    // failed copy never leaves a partial track under the real name.
                    var temporary = Path.Combine(musicDirectory, $".track{number:00}.{Guid.NewGuid():N}.tmp");
                    PackStorage.EnsureNoLinks(temporary);
                    try
                    {
                        File.Copy(source, temporary);
                        File.Move(temporary, destination, true);
                    }
                    finally
                    {
                        if (File.Exists(temporary)) File.Delete(temporary);
                    }
                    owned[track.FileName] = currentRecord;
                    ++staged;
                    log?.Invoke($"MW3-RE soundtrack track {number:00} staged from pack {manifest.Id} {manifest.Version}.");
                }
                catch (Exception error) when (error is IOException or UnauthorizedAccessException)
                {
                    // The previous record (if any) is kept, so a still-matching old copy stays launcher-owned.
                    log?.Invoke($"MW3-RE soundtrack track {number:00} was not staged: {error.Message}");
                }
            }
        }
        finally
        {
            // Recorded even after a failure, so files staged earlier in this pass stay launcher-owned.
            if (Directory.Exists(musicDirectory)) WriteStagedRecord(recordPath, owned.Values);
        }
        return staged;
    }

    private static List<StagedTrack>? ReadStagedRecord(string path)
    {
        if (!File.Exists(path)) return new List<StagedTrack>();
        try
        {
            var root = JsonNode.Parse(File.ReadAllText(path))!.AsObject();
            if (root["schema_version"]?.GetValue<int>() != 1 || root["tracks"] is not JsonArray tracks)
                return null;
            var result = new List<StagedTrack>();
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var node in tracks)
            {
                var fileName = node!["file_name"]!.GetValue<string>();
                var bytes = node["bytes"]!.GetValue<long>();
                var hash = node["sha256"]!.GetValue<string>();
                var packId = node["pack_id"]!.GetValue<string>();
                var packVersion = node["pack_version"]!.GetValue<string>();
                if (!System.Text.RegularExpressions.Regex.IsMatch(fileName, @"^track\d{2}\.(ogg|flac|wav|mp3)$", System.Text.RegularExpressions.RegexOptions.IgnoreCase) ||
                    bytes < 0 || hash.Length != 64 || !hash.All(Uri.IsHexDigit) || string.IsNullOrWhiteSpace(packId) ||
                    string.IsNullOrWhiteSpace(packVersion) || !names.Add(fileName)) return null;
                result.Add(new StagedTrack(fileName, bytes, hash, packId, packVersion));
            }
            return result;
        }
        catch (Exception exception) when (exception is IOException or JsonException or InvalidOperationException or FormatException or NullReferenceException)
        {
            return null;
        }
    }

    private static bool FileMatchesRecord(string path, StagedTrack track)
    {
        var info = new FileInfo(path);
        if (info.Length != track.Bytes) return false;
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).Equals(track.Sha256, StringComparison.OrdinalIgnoreCase);
    }

    private static void WriteStagedRecord(string path, IEnumerable<StagedTrack> tracks)
    {
        var document = new JsonObject
        {
            ["schema_version"] = 1,
            ["tracks"] = new JsonArray(tracks
                .OrderBy(track => track.FileName, StringComparer.OrdinalIgnoreCase)
                .Select(track => (JsonNode)new JsonObject
                {
                    ["file_name"] = track.FileName,
                    ["bytes"] = track.Bytes,
                    ["sha256"] = track.Sha256,
                    ["pack_id"] = track.PackId,
                    ["pack_version"] = track.PackVersion
                }).ToArray())
        };
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        PackStorage.EnsureNoLinks(temporary);
        try
        {
            File.WriteAllText(temporary, document.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
            File.Move(temporary, path, true);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }

    private static bool FilesMatch(string first, string second)
    {
        var firstInfo = new FileInfo(first);
        var secondInfo = new FileInfo(second);
        if (firstInfo.Length != secondInfo.Length) return false;
        using var firstStream = File.OpenRead(first);
        using var secondStream = File.OpenRead(second);
        return CryptographicOperations.FixedTimeEquals(SHA256.HashData(firstStream), SHA256.HashData(secondStream));
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
