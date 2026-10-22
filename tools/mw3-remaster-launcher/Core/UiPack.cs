using System.IO;
using System.Security.Cryptography;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Verified artwork for the existing identity-based HUD/menu readers.</summary>
public static class UiPack
{
    public const string Profile = "prepared-ui-v1";
    public const string Registry = "ui/ui.json";
    public sealed record Content(string Kind, string SpriteDirectory, string? Background,
        Dictionary<string, string> SpriteHashes);

    public static Content Read(string root, PackManifest manifest)
    {
        void Verify(string name)
        {
            if (!manifest.Files!.TryGetValue(name, out var pin)) throw new InvalidDataException("Undeclared UI resource: " + name);
            var path = PackStorage.Resolve(root, name);
            using var stream = File.OpenRead(path);
            if (stream.Length != pin.Bytes || !Convert.ToHexString(SHA256.HashData(stream)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("UI resource integrity failure: " + name);
        }
        Verify(Registry);
        var registryPath = PackStorage.Resolve(root, Registry);
        if (new FileInfo(registryPath).Length > PackStorage.MaxJsonBytes) throw new InvalidDataException("UI registry is too large.");
        var data = JsonNode.Parse(File.ReadAllText(registryPath))!.AsObject();
        var expectedKeys = new HashSet<string> { "schema_version", "payload_profile", "kind", "sprites", "background" };
        if (!expectedKeys.SetEquals(data.Select(p => p.Key)) || data["schema_version"]!.GetValue<int>() != 2 ||
            data["payload_profile"]!.GetValue<string>() != Profile)
            throw new InvalidDataException("Unsupported UI registry.");
        var kind = data["kind"]!.GetValue<string>();
        if (kind != "hud" && kind != "menu") throw new InvalidDataException("Unknown UI pack kind.");
        var sprites = data["sprites"]!.AsObject();
        if (sprites.Count > 256) throw new InvalidDataException("Too many UI sprites.");
        var declared = new HashSet<string>(StringComparer.Ordinal) { Registry };
        var hashes = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var (key, value) in sprites)
        {
            var name = value!.GetValue<string>();
            if (!Regex.IsMatch(key, "\\A[0-9a-f]{16}\\z") || name != "ui/sprites/" + key + ".rgba")
                throw new InvalidDataException("UI sprite identity/path mismatch.");
            Verify(name); declared.Add(name);
            if (manifest.Files![name].Format != "MW3H-v1") throw new InvalidDataException("Invalid UI sprite format declaration.");
            using var reader = new BinaryReader(File.OpenRead(PackStorage.Resolve(root, name)));
            if (!reader.ReadBytes(4).SequenceEqual("MW3H"u8.ToArray())) throw new InvalidDataException("Invalid UI sprite header.");
            var width = reader.ReadUInt32(); var height = reader.ReadUInt32();
            var u0 = reader.ReadSingle(); var v0 = reader.ReadSingle(); var u1 = reader.ReadSingle(); var v1 = reader.ReadSingle();
            if (width == 0 || height == 0 || width > 8192 || height > 8192 ||
                reader.BaseStream.Length != 28 + 4L * width * height ||
                !float.IsFinite(u0) || !float.IsFinite(v0) || !float.IsFinite(u1) || !float.IsFinite(v1) ||
                u0 < 0 || v0 < 0 || u1 > 1 || v1 > 1 || u0 >= u1 || v0 >= v1)
                throw new InvalidDataException("Invalid UI sprite dimensions or UV coordinates.");
            hashes[key] = manifest.Files[name].Sha256.ToLowerInvariant();
        }
        string? background = null;
        if (data["background"] != null)
        {
            var name = data["background"]!.GetValue<string>();
            if (kind != "menu" || name != "ui/background.mwhd") throw new InvalidDataException("Unsupported UI background binding.");
            Verify(name); declared.Add(name);
            if (manifest.Files![name].Format != "MWHDBG1") throw new InvalidDataException("Invalid menu background format declaration.");
            background = PackStorage.Resolve(root, name);
            using var reader = new BinaryReader(File.OpenRead(background));
            if (!reader.ReadBytes(8).SequenceEqual("MWHDBG1\0"u8.ToArray())) throw new InvalidDataException("Invalid menu background header.");
            var w = reader.ReadUInt32(); var h = reader.ReadUInt32(); var sw = reader.ReadUInt32(); var sh = reader.ReadUInt32();
            if (w == 0 || h == 0 || sw == 0 || sh == 0 || w > 16384 || h > 16384 || sw > 16384 || sh > 16384 ||
                reader.BaseStream.Length != 24 + 3L * w * h) throw new InvalidDataException("Invalid menu background dimensions.");
        }
        if (!declared.SetEquals(manifest.Files!.Keys) || manifest.Files.Values.Sum(f => f.Bytes) > 512L * 1024 * 1024 ||
            (sprites.Count == 0 && background == null)) throw new InvalidDataException("Unused, excessive or empty UI payload.");
        var formats = new HashSet<string>();
        if (sprites.Count > 0) formats.Add("MW3H-v1");
        if (background != null) formats.Add("MWHDBG1");
        if (!formats.SetEquals(manifest.NativePayload!.RequiredFormats)) throw new InvalidDataException("Unsupported UI format requirements.");
        var spriteDirectory = PackStorage.Resolve(root, "ui/sprites");
        if (Directory.Exists(spriteDirectory))
        {
            PackStorage.EnsureNoLinks(spriteDirectory);
            foreach (var file in Directory.EnumerateFiles(spriteDirectory))
                if (!declared.Contains("ui/sprites/" + Path.GetFileName(file))) throw new InvalidDataException("Unregistered file in UI sprite directory.");
        }
        return new(kind, spriteDirectory, background, hashes);
    }

    public static void Apply(JsonObject profile, IEnumerable<string> directories)
    {
        var native = profile["native"]!.AsObject();
        native["runtime_environment"] ??= new JsonObject();
        var environment = native["runtime_environment"]!.AsObject();
        // Explicitly stop the native HUD reader's historical directory fallback.
        environment["MW34_HIRES_HUD"] = "0";
        environment.Remove("MW34_HIRES_MENU"); environment.Remove("MW34_MENU_HD_BG");
        var selected = new Dictionary<string, Content>();
        foreach (var directory in directories)
        {
            var manifest = PackStorage.ReadManifest(Path.Combine(directory, "pack.json"));
            if (manifest.NativePayload?.Profile != Profile) continue;
            var content = Read(directory, manifest);
            if (selected.ContainsKey(content.Kind)) continue;
            if (!NativeHostCompatibility.Matches(manifest.NativePayload.ReferenceHostSha256, native["executable_sha256"]!.GetValue<string>()))
                throw new InvalidDataException($"UI pack '{manifest.Id}' requires its matched native runtime. " +
                    $"Pack reference: {manifest.NativePayload.ReferenceHostSha256}; " +
                    $"selected runtime: {native["executable_sha256"]!.GetValue<string>()}. Update the pack or runtime.");
            selected.Add(content.Kind, content);
        }
        // Both readers share an identity table in the current host.
        if (selected.TryGetValue("hud", out var hud) && selected.TryGetValue("menu", out var menu))
            foreach (var (key, hash) in hud.SpriteHashes)
                if (menu.SpriteHashes.TryGetValue(key, out var other) && other != hash)
                    throw new InvalidDataException("Selected HUD and menu packs replace the same image differently: " + key);
        foreach (var content in selected.Values)
        {
            environment[content.Kind == "hud" ? "MW34_HIRES_HUD" : "MW34_HIRES_MENU"] = content.SpriteDirectory;
            if (content.Background != null) environment["MW34_MENU_HD_BG"] = content.Background;
        }
    }
}
