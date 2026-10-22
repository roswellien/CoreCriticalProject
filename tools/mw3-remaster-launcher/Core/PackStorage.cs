using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Bounded pack extraction. Content is verified before replacing an owned installation.</summary>
public static class PackStorage
{
    // Operation 4 includes both C4 and C4b (over 8 GiB of prepared banks).
    public const long MaxExpandedBytes = 16L * 1024 * 1024 * 1024;
    public const int MaxJsonBytes = 2 * 1024 * 1024;

    public static string ValidateId(string id)
    {
        if (!Regex.IsMatch(id, @"\A[a-z0-9][a-z0-9._-]{0,127}\z") || id.EndsWith('.'))
            throw new InvalidDataException("Invalid pack ID.");
        ValidatePath(id);
        return id;
    }

    public static void ValidatePath(string path)
    {
        if (string.IsNullOrEmpty(path) || path.Length > 240 || path.Contains('\\'))
            throw new InvalidDataException("Invalid pack path: " + path);
        foreach (var part in path.Split('/'))
        {
            if (part.Length == 0 || part == "." || part == ".." || part.EndsWith('.') || part.EndsWith(' ') ||
                part.Any(c => c < 32 || "<>:\"|?*".Contains(c)) ||
                Regex.IsMatch(part.Split('.')[0], @"\A(CON|CONIN\$|CONOUT\$|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³])\z", RegexOptions.IgnoreCase))
                throw new InvalidDataException("Unsafe pack path: " + path);
        }
    }

    public static string Resolve(string root, string relative)
    {
        ValidatePath(relative);
        root = Path.GetFullPath(root);
        var result = Path.GetFullPath(Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
        var prefix = Path.EndsInDirectorySeparator(root) ? root : root + Path.DirectorySeparatorChar;
        if (!result.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Pack path leaves its content root.");
        EnsureNoLinks(result);
        return result;
    }

    public static void EnsureNoLinks(string path)
    {
        for (var item = Path.GetFullPath(path); item != null; item = Path.GetDirectoryName(item))
        {
            if ((File.Exists(item) || Directory.Exists(item)) &&
                (File.GetAttributes(item) & FileAttributes.ReparsePoint) != 0)
                throw new InvalidDataException("Links are not allowed in pack storage: " + item);
        }
    }

    public static PackManifest ReadManifest(string file)
    {
        EnsureNoLinks(file);
        if (new FileInfo(file).Length > MaxJsonBytes) throw new InvalidDataException("Pack manifest is too large.");
        var json = File.ReadAllText(file);
        using (var document = JsonDocument.Parse(json)) ValidateUniqueProperties(document.RootElement);
        var manifest = JsonSerializer.Deserialize<PackManifest>(json)
            ?? throw new InvalidDataException("Empty pack manifest.");
        ValidateId(manifest.Id);
        if (manifest.SchemaVersion != 1 && manifest.SchemaVersion != 2)
            throw new InvalidDataException("Unsupported pack schema.");
        if (manifest.SchemaVersion == 2)
        {
            var environment = manifest.NativePayload?.Profile == "prepared-environment-v1";
            var music = manifest.NativePayload?.Profile == MusicPack.Profile;
            var ui = manifest.NativePayload?.Profile == UiPack.Profile;
            var cinematic = manifest.NativePayload?.Profile == CinematicPack.Profile;
            var registry = cinematic ? CinematicPack.Registry : ui ? UiPack.Registry : music ? MusicPack.Registry : environment ? "environment/environment.json" : "models/models.json";
            if ((manifest.NativePayload?.Profile != "prepared-native-v1" && !environment && !music && !ui && !cinematic) || manifest.NativePayload!.PathBase != "pack-root" ||
                manifest.NativePayload.Registry != registry || manifest.Files == null || manifest.Files.Count > 10000)
                throw new InvalidDataException("Unsupported prepared-native pack contract.");
            var paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "pack.json" };
            long total = 0;
            foreach (var (path, entry) in manifest.Files)
            {
                ValidatePath(path);
                if (!paths.Add(path) || entry == null || entry.Bytes < 0 || entry.Bytes > MaxExpandedBytes ||
                    !Regex.IsMatch(entry.Sha256, @"\A[0-9a-fA-F]{64}\z"))
                    throw new InvalidDataException("Invalid pack file table.");
                total = checked(total + entry.Bytes);
            }
            if (total > MaxExpandedBytes || !manifest.Files.ContainsKey(registry))
                throw new InvalidDataException("Missing registry or excessive pack size.");
        }
        return manifest;
    }

    private static void ValidateUniqueProperties(JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            var names = new HashSet<string>(StringComparer.Ordinal);
            foreach (var property in value.EnumerateObject())
            {
                if (!names.Add(property.Name)) throw new InvalidDataException("Duplicate JSON property.");
                ValidateUniqueProperties(property.Value);
            }
        }
        else if (value.ValueKind == JsonValueKind.Array)
            foreach (var item in value.EnumerateArray()) ValidateUniqueProperties(item);
    }

    public static FileStream Lock(string root)
    {
        var path = Resolve(root, ".pack-lock");
        return new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }

    // A stopped update may leave the previous directory beside the destination.
    // Recovery favors the previous version if activation did not complete.
    public static void Recover(string root)
    {
        EnsureNoLinks(root);
        foreach (var previous in Directory.GetDirectories(root, ".rollback-*"))
        {
            var id = ValidateId(Path.GetFileName(previous)[10..]);
            var target = Resolve(root, id);
            EnsureNoLinks(previous);
            if (!Directory.Exists(target)) Directory.Move(previous, target);
        }
    }

    public static PackManifest Install(string root, string archivePath)
    {
        root = Path.GetFullPath(root);
        EnsureNoLinks(root);
        Directory.CreateDirectory(root);
        using var storageLock = Lock(root);
        Recover(root);
        var stage = Path.Combine(root, ".staging-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(stage);
        try
        {
            using var archive = ZipFile.OpenRead(archivePath);
            if (archive.Entries.Count > 10000) throw new InvalidDataException("Too many pack members.");
            var manifestEntry = archive.GetEntry("pack.json") ?? throw new InvalidDataException("pack.json must be at the archive root.");
            if (manifestEntry.Length > MaxJsonBytes) throw new InvalidDataException("Pack manifest is too large.");
            ExtractBounded(manifestEntry, Path.Combine(stage, "pack.json"));
            var manifest = ReadManifest(Path.Combine(stage, "pack.json"));
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            long total = 0;
            foreach (var entry in archive.Entries)
            {
                var directory = entry.FullName.EndsWith('/');
                var path = directory ? entry.FullName[..^1] : entry.FullName;
                ValidatePath(path);
                if (!seen.Add(path) || ((entry.ExternalAttributes >> 16) & 0xF000) == 0xA000 ||
                    (entry.ExternalAttributes & (int)FileAttributes.ReparsePoint) != 0)
                    throw new InvalidDataException("Duplicate or linked archive member.");
                total = checked(total + entry.Length);
                if (total > MaxExpandedBytes) throw new InvalidDataException("Pack expanded size exceeds limit.");
                var dest = Resolve(stage, path);
                if (directory)
                {
                    if (manifest.SchemaVersion == 2 && !manifest.Files!.Keys.Any(p => p.StartsWith(path + "/", StringComparison.Ordinal)))
                        throw new InvalidDataException("Undeclared pack directory.");
                    Directory.CreateDirectory(dest);
                    continue;
                }
                if (path == "pack.json") continue;
                PackFile? declared = null;
                if (manifest.SchemaVersion == 2 && (!manifest.Files!.TryGetValue(path, out declared) || declared.Bytes != entry.Length))
                    throw new InvalidDataException("Undeclared member or incorrect size: " + path);
                Directory.CreateDirectory(Path.GetDirectoryName(dest)!);
                ExtractBounded(entry, dest);
                if (declared != null)
                {
                    using var stream = File.OpenRead(dest);
                    if (!Convert.ToHexString(SHA256.HashData(stream)).Equals(declared.Sha256, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("Pack hash mismatch: " + path);
                }
            }
            if (manifest.SchemaVersion == 2)
            {
                foreach (var path in manifest.Files!.Keys)
                    if (!File.Exists(Resolve(stage, path))) throw new InvalidDataException("Missing declared pack member: " + path);
                var registry = Resolve(stage, manifest.NativePayload!.Registry);
                if (new FileInfo(registry).Length > MaxJsonBytes) throw new InvalidDataException("Model registry is too large.");
                using var document = JsonDocument.Parse(File.ReadAllText(registry));
                ValidateUniqueProperties(document.RootElement);
                if (document.RootElement.GetProperty("schema_version").GetInt32() != 2 ||
                    document.RootElement.GetProperty("payload_profile").GetString() != manifest.NativePayload.Profile)
                    throw new InvalidDataException("Unsupported model registry.");
                if (manifest.NativePayload.Profile == CinematicPack.Profile)
                    CinematicPack.Read(stage, manifest);
                else if (manifest.NativePayload.Profile == UiPack.Profile)
                    UiPack.Read(stage, manifest);
                else if (manifest.NativePayload.Profile == MusicPack.Profile)
                    MusicPack.ReadInputs(stage, manifest);
                else if (manifest.NativePayload.Profile == "prepared-native-v1")
                {
                    foreach (var model in document.RootElement.GetProperty("models").EnumerateArray())
                        foreach (var binding in model.GetProperty("environment").EnumerateObject())
                            if (!manifest.Files.ContainsKey(binding.Value.GetString()!)) throw new InvalidDataException("Undeclared model binding.");
                }
                else
                {
                    var data = document.RootElement;
                    void Declared(string name) { if (!manifest.Files.ContainsKey(name)) throw new InvalidDataException("Undeclared environment resource."); }
                    if (data.TryGetProperty("lighting", out var lighting))
                    {
                        var name = lighting.GetString() ?? throw new InvalidDataException("Missing lighting catalog path.");
                        Declared(name);
                        var lightingPath = Resolve(stage, name);
                        if (new FileInfo(lightingPath).Length > MaxJsonBytes) throw new InvalidDataException("Lighting catalog is too large.");
                        using var catalog = JsonDocument.Parse(File.ReadAllText(lightingPath));
                        ValidateUniqueProperties(catalog.RootElement);
                        if (catalog.RootElement.GetProperty("schema_version").GetInt32() != 1 ||
                            catalog.RootElement.GetProperty("missions").ValueKind != JsonValueKind.Object ||
                            catalog.RootElement.GetProperty("maps").ValueKind != JsonValueKind.Object)
                            throw new InvalidDataException("Unsupported lighting catalog.");
                    }
                    foreach (var bank in data.GetProperty("banks").EnumerateObject()) Declared(bank.Value.GetString()!);
                    var sharedMechs = data.GetProperty("operation").GetString() == "shared-mechs";
                    foreach (var role in sharedMechs ? new[] { "authored" } : new[] { "authored", "world" })
                        foreach (var page in data.GetProperty(role).EnumerateArray()) Declared(page.GetString()!);
                    foreach (var role in sharedMechs ? new[] { "authored_manifest" } : new[] { "effects", "authored_manifest", "world_manifest" }) Declared(data.GetProperty(role).GetString()!);
                    if (!sharedMechs)
                        foreach (var detail in data.GetProperty("detail").EnumerateObject()) Declared(detail.Value.GetString()!);
                }
            }
            var target = Resolve(root, manifest.Id);
            var previous = Resolve(root, ".rollback-" + manifest.Id);
            // Retain a recoverable previous version until the next successful replacement.
            if (Directory.Exists(previous)) DeleteOwnedTree(previous);
            if (Directory.Exists(target)) Directory.Move(target, previous);
            try { Directory.Move(stage, target); }
            catch
            {
                if (!Directory.Exists(target) && Directory.Exists(previous)) Directory.Move(previous, target);
                throw;
            }
            manifest.DirectoryPath = target;
            return manifest;
        }
        finally { if (Directory.Exists(stage)) DeleteOwnedTree(stage); }
    }

    private static void ExtractBounded(ZipArchiveEntry entry, string destination)
    {
        using var input = entry.Open();
        using var output = new FileStream(destination, FileMode.CreateNew);
        var buffer = new byte[65536];
        long written = 0;
        int count;
        while ((count = input.Read(buffer)) != 0)
        {
            written = checked(written + count);
            if (written > entry.Length) throw new InvalidDataException("Expanded member exceeds declared size.");
            output.Write(buffer, 0, count);
        }
        if (written != entry.Length) throw new InvalidDataException("Truncated pack member.");
    }

    public static void DeleteOwnedTree(string path)
    {
        EnsureNoLinks(path);
        foreach (var entry in Directory.EnumerateFileSystemEntries(path))
        {
            EnsureNoLinks(entry);
            if (Directory.Exists(entry)) DeleteOwnedTree(entry);
            else File.Delete(entry);
        }
        Directory.Delete(path);
    }
}
