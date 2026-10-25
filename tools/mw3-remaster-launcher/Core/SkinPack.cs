using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Portable additive skins. A pack never owns a chassis or an A–H slot.</summary>
public static class SkinPack
{
    public const string Profile = "prepared-skins-v1";
    public const string Registry = "skins/skins.json";
    public sealed record Skin(string Id, string Name, string Chassis);

    public static List<Skin> Read(string root, PackManifest manifest)
    {
        if (manifest.NativePayload?.Profile != Profile || manifest.NativePayload.Registry != Registry ||
            !manifest.NativePayload.RequiredFormats.SequenceEqual(new[] { "BWTEX1" }) ||
            manifest.Provides?.Mechs?.Count > 0 || manifest.Dependencies?.Count > 0 || manifest.Conflicts?.Count > 0 ||
            manifest.Files == null || manifest.Files.Count > 513 || manifest.Files.Values.Sum(p => p.Bytes) > 1024L * 1024 * 1024)
            throw new InvalidDataException("Invalid additional skin pack contract.");
        void Verify(string name)
        {
            if (!manifest.Files.TryGetValue(name, out var pin)) throw new InvalidDataException("Undeclared skin resource.");
            using var stream = File.OpenRead(PackStorage.Resolve(root, name));
            if (stream.Length != pin.Bytes || stream.Length > 256L * 1024 * 1024 ||
                !Convert.ToHexString(SHA256.HashData(stream)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Skin integrity failure: " + name);
        }
        Verify(Registry);
        var path = PackStorage.Resolve(root, Registry);
        if (new FileInfo(path).Length > PackStorage.MaxJsonBytes) throw new InvalidDataException("Skin registry too large.");
        using var document = JsonDocument.Parse(File.ReadAllText(path));
        var data = document.RootElement;
        if (data.GetProperty("schema_version").GetInt32() != 2 || data.GetProperty("payload_profile").GetString() != Profile)
            throw new InvalidDataException("Unsupported skin registry.");
        var skins = data.GetProperty("skins");
        if (skins.GetArrayLength() is < 1 or > 128) throw new InvalidDataException("Invalid skin count.");
        var ids = new HashSet<string>(StringComparer.Ordinal);
        var used = new HashSet<string>(StringComparer.Ordinal) { Registry };
        var result = new List<Skin>();
        foreach (var skin in skins.EnumerateArray())
        {
            var id = skin.GetProperty("id").GetString() ?? "";
            var name = skin.GetProperty("name").GetString() ?? "";
            var chassis = skin.GetProperty("chassis").GetString() ?? "";
            if (!id.StartsWith(manifest.Id + ":", StringComparison.Ordinal) ||
                !Regex.IsMatch(id, @"\A[a-z0-9][a-z0-9._-]{0,127}:[a-z0-9][a-z0-9._-]{0,63}\z") || !ids.Add(id) ||
                name.Length is < 1 or > 64 || name.Any(c => c < 32 || c > 126) ||
                !Regex.IsMatch(chassis, @"\A[a-z][a-z0-9_-]{0,31}\z"))
                throw new InvalidDataException("Invalid skin identity or name.");
            var hashes = skin.GetProperty("mesh_sha256");
            var textures = skin.GetProperty("textures");
            if (hashes.EnumerateObject().Count() != 2 || textures.EnumerateObject().Count() != 2)
                throw new InvalidDataException("Skin needs close/distance resources.");
            foreach (var lod in new[] { "close", "distance" })
            {
                if (!Regex.IsMatch(hashes.GetProperty(lod).GetString() ?? "", @"\A[0-9a-f]{64}\z"))
                    throw new InvalidDataException("Invalid required mesh identity.");
                var texture = textures.GetProperty(lod).GetString() ?? "";
                Verify(texture);
                using var stream = File.OpenRead(PackStorage.Resolve(root, texture));
                using var reader = new BinaryReader(stream);
                if (manifest.Files[texture].Format != "BWTEX1" || !reader.ReadBytes(8).SequenceEqual("BWTEX1\0\0"u8.ToArray()))
                    throw new InvalidDataException("Unsupported skin texture format.");
                used.Add(texture);
            }
            result.Add(new(id, name, chassis));
        }
        if (!used.SetEquals(manifest.Files.Keys)) throw new InvalidDataException("Unused skin pack file.");
        return result;
    }
}
