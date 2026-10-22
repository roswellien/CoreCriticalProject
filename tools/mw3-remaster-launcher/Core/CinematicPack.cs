using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

public static class CinematicPack
{
    public const string Profile = "prepared-cinematic-v1";
    public const string Registry = "cinematics/cinematics.json";
    public sealed record Clip(string Id, string Title, string Source, string? Replaces);

    // This version deliberately retains the observed original AVI playback contract.
    // Modern MP4 additions are watched in the launcher; they are not sent to VfW.
    public static void ValidateAvi(string path)
    {
        using var input = new BinaryReader(File.OpenRead(path));
        string Tag() => Encoding.ASCII.GetString(input.ReadBytes(4));
        if (Tag() != "RIFF" || input.ReadUInt32() + 8L != input.BaseStream.Length || Tag() != "AVI ")
            throw new InvalidDataException("Replacement must be a complete RIFF AVI movie.");
        int videos = 0, audios = 0, chunks = 0;
        void Chunks(long end, int depth, bool stream = false)
        {
            if (depth > 4) throw new InvalidDataException("AVI headers are too deeply nested.");
            string? type = null; byte[]? format = null;
            while (input.BaseStream.Position < end)
            {
                if (++chunks > 10000 || end - input.BaseStream.Position < 8) throw new InvalidDataException("Invalid AVI chunk table.");
                var tag = Tag(); var size = input.ReadUInt32(); var start = input.BaseStream.Position;
                var next = start + size + (size & 1);
                if (next > end) throw new InvalidDataException("Truncated AVI chunk.");
                if (tag == "LIST")
                {
                    if (size < 4) throw new InvalidDataException("Invalid AVI list.");
                    var list = Tag();
                    if (list == "hdrl" || list == "strl") Chunks(start + size, depth + 1, list == "strl");
                }
                else if (stream && tag == "strh")
                {
                    if (size < 56 || size > 4096 || type != null) throw new InvalidDataException("Invalid AVI stream header.");
                    type = Tag(); var handler = Tag();
                    input.BaseStream.Position = start + 20;
                    var scale = input.ReadUInt32(); var rate = input.ReadUInt32();
                    if (type == "vids" && (handler != "IV50" || scale != 1 || rate != 15))
                        throw new InvalidDataException("In-game replacements currently require IV50 AVI at 15 fps. MP4/HD in-game playback is not available yet.");
                    if (type != "vids" && type != "auds") throw new InvalidDataException("Unsupported AVI stream.");
                }
                else if (stream && tag == "strf")
                {
                    if (size > 4096 || format != null) throw new InvalidDataException("Invalid AVI format header.");
                    format = input.ReadBytes((int)size);
                }
                input.BaseStream.Position = next;
            }
            if (!stream) return;
            if (format == null) throw new InvalidDataException("Missing AVI stream format.");
            if (type == "vids")
            {
                videos++;
                if (format.Length < 40 || BitConverter.ToInt32(format, 0) != 40 || BitConverter.ToInt32(format, 4) != 640 ||
                    BitConverter.ToInt32(format, 8) != 480 || BitConverter.ToUInt16(format, 12) != 1 ||
                    BitConverter.ToUInt16(format, 14) != 24 || Encoding.ASCII.GetString(format, 16, 4) != "IV50")
                    throw new InvalidDataException("In-game replacements currently require original-compatible 640×480 IV50 video.");
            }
            else if (type == "auds")
            {
                audios++;
                if (format.Length < 16 || BitConverter.ToUInt16(format, 0) != 1 ||
                    BitConverter.ToUInt16(format, 2) is not (1 or 2) || BitConverter.ToUInt32(format, 4) != 22050 ||
                    BitConverter.ToUInt16(format, 14) is not (8 or 16))
                    throw new InvalidDataException("Replacement audio must be original-compatible PCM at 22050 Hz.");
            }
            else throw new InvalidDataException("Missing AVI stream header.");
        }
        Chunks(input.BaseStream.Length, 0);
        if (videos != 1 || audios > 1) throw new InvalidDataException("Replacement AVI requires one video stream and at most one audio stream.");
    }

    public static List<Clip> Read(string root, PackManifest manifest)
    {
        void Verify(string name)
        {
            if (!manifest.Files!.TryGetValue(name, out var pin)) throw new InvalidDataException("Undeclared cinematic resource.");
            using var stream = File.OpenRead(PackStorage.Resolve(root, name));
            if (stream.Length != pin.Bytes || !Convert.ToHexString(SHA256.HashData(stream)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Cinematic resource integrity failure: " + name);
        }
        Verify(Registry);
        if (new FileInfo(PackStorage.Resolve(root, Registry)).Length > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Cinematic registry is too large.");
        var data = JsonNode.Parse(File.ReadAllText(PackStorage.Resolve(root, Registry)))!.AsObject();
        if (!new HashSet<string> { "schema_version", "payload_profile", "clips" }.SetEquals(data.Select(x => x.Key)) ||
            data["schema_version"]!.GetValue<int>() != 2 || data["payload_profile"]!.GetValue<string>() != Profile)
            throw new InvalidDataException("Unsupported cinematic registry.");
        var clips = data["clips"]!.AsArray();
        if (clips.Count is < 1 or > 64) throw new InvalidDataException("Invalid cinematic count.");
        var result = new List<Clip>(); var ids = new HashSet<string>(); var targets = new HashSet<string>();
        var files = new HashSet<string> { Registry }; var formats = new HashSet<string>();
        foreach (var item in clips)
        {
            var obj = item!.AsObject();
            if (!new HashSet<string> { "id", "title", "source", "replaces" }.SetEquals(obj.Select(x => x.Key)))
                throw new InvalidDataException("Unknown cinematic fields or triggers.");
            var id = obj["id"]!.GetValue<string>(); var title = obj["title"]!.GetValue<string>();
            var source = obj["source"]!.GetValue<string>(); var target = obj["replaces"]?.GetValue<string>();
            if (!Regex.IsMatch(id, "\\A[a-z0-9][a-z0-9_-]{0,63}\\z") || !ids.Add(id) || title.Length is < 1 or > 160 || title.Any(char.IsControl))
                throw new InvalidDataException("Invalid cinematic identity/title.");
            var format = target == null ? "MP4-library-v1" : "AVI-IV50-original-v1";
            if (source != "cinematics/media/" + id + (target == null ? ".mp4" : ".avi") ||
                (target != null && (!Regex.IsMatch(target, "\\A[a-z0-9_]{1,64}\\z") || !targets.Add(target))))
                throw new InvalidDataException("Invalid cinematic source or replacement target.");
            Verify(source); files.Add(source); formats.Add(format);
            if (manifest.Files![source].Format != format) throw new InvalidDataException("Unsupported cinematic format declaration.");
            var path = PackStorage.Resolve(root, source);
            if (target != null) ValidateAvi(path);
            else
            {
                using var reader = new BinaryReader(File.OpenRead(path));
                if (reader.BaseStream.Length < 16 || reader.ReadUInt32() == 0 || Encoding.ASCII.GetString(reader.ReadBytes(4)) != "ftyp")
                    throw new InvalidDataException("Library additions must be MP4 movies. Playback also requires a Windows-supported codec.");
            }
            result.Add(new(id, title, path, target));
        }
        if (!files.SetEquals(manifest.Files!.Keys) || !formats.SetEquals(manifest.NativePayload!.RequiredFormats))
            throw new InvalidDataException("Unused cinematic files or unknown format requirements.");
        return result;
    }

    public static List<Clip> Library(IEnumerable<string> directories)
    {
        var result = new List<Clip>();
        foreach (var root in directories)
        {
            var manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
            if (manifest.NativePayload?.Profile == Profile) result.AddRange(Read(root, manifest).Where(c => c.Replaces == null));
        }
        return result;
    }

    public static void Apply(JsonObject profile, IEnumerable<string> directories, string session, string game)
    {
        var native = profile["native"]!.AsObject();
        native["runtime_environment"] ??= new JsonObject();
        var environment = native["runtime_environment"]!.AsObject();
        environment.Remove("MW34_CINEMATIC_PATHS");
        bool codecVerified = false;
        if (native["cinematic_codec_sha256"] != null)
        {
            var codec = environment["MW34_IV50_IMAGE"]?.GetValue<string>();
            if (codec == null || !File.Exists(codec))
                throw new InvalidDataException("The original movie decoder is missing from this runtime. Repair the game setup before launching.");
            using var stream = File.OpenRead(codec);
            if (!Convert.ToHexString(SHA256.HashData(stream)).Equals(native["cinematic_codec_sha256"]!.GetValue<string>(), StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("The original movie decoder failed its integrity check. Repair the runtime.");
            codecVerified = true;
        }
        var selected = new Dictionary<string, Clip>();
        foreach (var root in directories)
        {
            var manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
            if (manifest.NativePayload?.Profile != Profile) continue;
            foreach (var clip in Read(root, manifest).Where(c => c.Replaces != null))
            {
                if (selected.ContainsKey(clip.Replaces!)) continue;
                if (!codecVerified || native["cinematic_path_versions"] is not JsonArray versions || !versions.Any(v => v!.GetValue<int>() == 1) ||
                    !NativeHostCompatibility.Matches(manifest.NativePayload.ReferenceHostSha256, native["executable_sha256"]!.GetValue<string>()))
                    throw new InvalidDataException("This cinematic replacement requires its matched native runtime.");
                // New scenes cannot silently invent guest story/mission hooks.
                var video = Directory.EnumerateDirectories(game).FirstOrDefault(d => Path.GetFileName(d).Equals("video", StringComparison.OrdinalIgnoreCase));
                if (video == null || !Directory.EnumerateFiles(video).Any(f => Path.GetFileName(f).Equals(clip.Replaces + ".avi", StringComparison.OrdinalIgnoreCase)))
                    throw new InvalidDataException("No installed original movie matches replacement target: " + clip.Replaces + ". Use a library addition; new in-game triggers require separate runtime support.");
                selected.Add(clip.Replaces!, clip);
            }
        }
        if (selected.Count == 0) return;
        Directory.CreateDirectory(session);
        var map = Path.Combine(session, "cinematic-paths.bin");
        using (var writer = new BinaryWriter(new FileStream(map, FileMode.CreateNew, FileAccess.Write)))
        {
            writer.Write("MWCINE1\0"u8); writer.Write(selected.Count);
            foreach (var (key, clip) in selected)
            {
                var a = Encoding.UTF8.GetBytes(key); var b = Encoding.UTF8.GetBytes(Path.GetFullPath(clip.Source));
                if (b.Length > 2048 || clip.Source.Any(c => c > 127))
                    throw new InvalidDataException("This cinematic runtime needs an ASCII-only media path of at most 2048 bytes. Move the pack storage to a compatible path.");
                writer.Write(a.Length); writer.Write(b.Length); writer.Write(a); writer.Write(b);
            }
        }
        environment["MW34_CINEMATIC_PATHS"] = map;
    }
}
