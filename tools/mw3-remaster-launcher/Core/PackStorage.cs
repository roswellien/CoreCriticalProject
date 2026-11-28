using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization.Metadata;
using System.Text.RegularExpressions;
using System.Text;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace MW3RemasterLauncher.Core;

public sealed record PackInstallProgress(string Stage, long CompletedBytes, long TotalBytes, bool IsComplete = false)
{
    public double Percent => TotalBytes > 0
        ? Math.Min(IsComplete ? 100 : 99, 100.0 * CompletedBytes / TotalBytes) : 0;
}

/// <summary>The verified catalog identity expected for an installed-pack update.</summary>
public sealed record PackUpdateExpectation(string Id, string Version,
    IReadOnlyList<string>? InstalledManifestSha256s = null, ReleaseArtifact? Archive = null,
    JsonObject? NativeRuntime = null);

/// <summary>Bounded pack extraction. Content is verified before replacing an owned installation.</summary>
public static class PackStorage
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetFinalPathNameByHandleW(SafeFileHandle file, StringBuilder path, uint size, uint flags);

    /// <summary>Pin the physical manifest opened here before handing its pack to another process.</summary>
    public static string CanonicalPackRoot(string directory)
    {
        var physical = CanonicalFilePath(Path.Combine(Path.GetFullPath(directory), "pack.json"));
        if (!Path.GetFileName(physical).Equals("pack.json", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Resolved pack manifest identity changed.");
        return Path.GetDirectoryName(physical)!;
    }

    /// <summary>Resolve MSIX filesystem redirection before handing a file to an external native child.</summary>
    public static string CanonicalFilePath(string path)
    {
        EnsureNoLinks(path);
        using var file = File.OpenRead(path);
        var name = new StringBuilder(32768);
        var length = GetFinalPathNameByHandleW(file.SafeFileHandle, name, (uint)name.Capacity, 0);
        if (length == 0 || length >= name.Capacity)
            throw new IOException("Cannot resolve the physical file path.", new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error()));
        var physical = name.ToString();
        if (physical.StartsWith(@"\\?\UNC\", StringComparison.OrdinalIgnoreCase)) physical = @"\\" + physical[8..];
        else if (physical.StartsWith(@"\\?\", StringComparison.Ordinal)) physical = physical[4..];
        EnsureNoLinks(physical);
        return physical;
    }

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

    // These fields were unknown to legacy readers. Keep ignoring them in schema 1/2,
    // even when their values would be invalid for the new schema 3 types.
    private static readonly JsonSerializerOptions LegacyManifestOptions = new()
    {
        TypeInfoResolver = new DefaultJsonTypeInfoResolver
        {
            Modifiers =
            {
                type =>
                {
                    var ignored = Array.Empty<string>();
                    if (type.Type == typeof(PackManifest))
                        ignored = new[] { "gameplay", "visuals" };
                    else if (type.Type == typeof(PackProvides))
                        ignored = new[] { "weapons", "skins", "maps", "missions", "campaigns" };
                    foreach (var property in type.Properties.Where(property => ignored.Contains(property.Name)).ToArray())
                        type.Properties.Remove(property);
                }
            }
        }
    };

    // Identify the new contract before parsing the entire document, so a truncated
    // schema 3 manifest still receives its problem code. Legacy parse errors stay unchanged.
    private static bool HasSchema3Header(string json)
    {
        var reader = new Utf8JsonReader(Encoding.UTF8.GetBytes(json),
            new JsonReaderOptions { MaxDepth = 1024 });
        try
        {
            while (reader.Read())
            {
                if (reader.TokenType == JsonTokenType.PropertyName && reader.CurrentDepth == 1 &&
                    reader.ValueTextEquals("schema_version") && reader.Read())
                    return reader.TokenType == JsonTokenType.Number &&
                        reader.TryGetDouble(out var version) && version == 3;
            }
        }
        catch (JsonException) { } // The normal parser supplies the actual error below.
        return false;
    }

    private static readonly JsonSerializerOptions Schema3ManifestOptions = new() { MaxDepth = 1024 };

    public static PackManifest ReadManifest(string file)
    {
        EnsureNoLinks(file);
        if (new FileInfo(file).Length > MaxJsonBytes) throw new InvalidDataException("Pack manifest is too large.");
        var json = File.ReadAllText(file);
        var isSchema3 = HasSchema3Header(json);
        JsonDocument parsedDocument;
        try
        {
            if (isSchema3)
                json = new UTF8Encoding(false, true).GetString(File.ReadAllBytes(file));
            parsedDocument = JsonDocument.Parse(json,
                new JsonDocumentOptions { MaxDepth = isSchema3 ? 1024 : 64 });
        }
        catch (Exception error) when (isSchema3 && error is JsonException or DecoderFallbackException)
        {
            throw new InvalidDataException("manifest-invalid: " + error.Message, error);
        }
        using (var document = parsedDocument)
        {
            var root = document.RootElement;
            if (isSchema3)
            {
                try { ValidateUniqueProperties(root); }
                catch (InvalidDataException error)
                {
                    throw new InvalidDataException("manifest-invalid: " + error.Message, error);
                }
                var problems = PackCheck.CheckManifest(root);
                if (problems.Count > 0) throw new InvalidDataException(problems[0].Line);
            }
            else ValidateUniqueProperties(root);
        }
        PackManifest manifest;
        try
        {
            manifest = JsonSerializer.Deserialize<PackManifest>(json,
                isSchema3 ? Schema3ManifestOptions : LegacyManifestOptions)
                ?? throw new InvalidDataException("Empty pack manifest.");
        }
        catch (JsonException error) when (isSchema3)
        {
            throw new InvalidDataException("manifest-invalid: " + error.Message, error);
        }
        ValidateId(manifest.Id);
        GameCatalog.Get(manifest.GameId);
        if (manifest.GameId != GameCatalog.Mw3 && manifest.SchemaVersion == 2)
            throw new InvalidDataException("Prepared content for this game is not supported yet.");
        if (manifest.SchemaVersion != 1 && manifest.SchemaVersion != 2 && manifest.SchemaVersion != 3)
            throw new InvalidDataException("Unsupported pack schema.");
        if (manifest.SchemaVersion == 2)
        {
            if (manifest.NativePayload != null) RuntimeContentCapabilities.ValidateRequirements(manifest.NativePayload);
            var environment = manifest.NativePayload?.Profile == "prepared-environment-v1";
            var music = manifest.NativePayload?.Profile == MusicPack.Profile;
            var ui = manifest.NativePayload?.Profile == UiPack.Profile;
            var cinematic = manifest.NativePayload?.Profile == CinematicPack.Profile;
            var skins = manifest.NativePayload?.Profile == SkinPack.Profile;
            var chassis = manifest.NativePayload?.Profile == ChassisPack.Profile;
            var registry = chassis ? ChassisPack.Registry : skins ? SkinPack.Registry : cinematic ? CinematicPack.Registry : ui ? UiPack.Registry : music ? MusicPack.Registry : environment ? "environment/environment.json" : "models/models.json";
            if ((manifest.NativePayload?.Profile != "prepared-native-v1" && !environment && !music && !ui && !cinematic && !skins && !chassis) || manifest.NativePayload!.PathBase != "pack-root" ||
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

    internal static void ValidateUniqueProperties(JsonElement value)
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
        {
            foreach (var element in value.EnumerateArray())
                ValidateUniqueProperties(element);
        }
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

    internal static Version ParseOnlineVersion(string? value)
    {
        if (string.IsNullOrEmpty(value) || value.Length > 48 || !Regex.IsMatch(value, @"\A[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?\z") ||
            !Version.TryParse(value, out var parsed))
        {
            throw new InvalidDataException("Invalid numeric asset pack version.");
        }
        return new Version(parsed.Major, parsed.Minor, parsed.Build, Math.Max(0, parsed.Revision));
    }

    private static void RequireOnlineUpgrade(string root, string gameId, PackManifest incoming,
        PackUpdateExpectation expected)
    {
        var id = ValidateId(expected.Id);
        if (incoming.SchemaVersion != 2 || incoming.Id != id ||
            ParseOnlineVersion(incoming.Version) != ParseOnlineVersion(expected.Version))
        {
            throw new InvalidDataException("Asset pack archive does not match the signed update identity.");
        }

        var installedPath = Resolve(root, id + "/pack.json");
        if (!File.Exists(installedPath))
        {
            throw new InvalidDataException("The asset pack is no longer installed.");
        }
        var installed = ReadManifest(installedPath);
        GameCatalog.RequirePackTarget(installed.GameId, gameId);
        if (installed.Id != id)
        {
            throw new InvalidDataException("Installed asset pack has a different identity.");
        }
        if (expected.InstalledManifestSha256s != null)
        {
            using var stream = File.OpenRead(installedPath);
            var installedHash = Convert.ToHexString(SHA256.HashData(stream));
            if (!expected.InstalledManifestSha256s.Contains(installedHash, StringComparer.OrdinalIgnoreCase))
            {
                throw new InvalidDataException("Installed asset pack does not match the signed update lineage.");
            }
        }
        if (ParseOnlineVersion(incoming.Version) <= ParseOnlineVersion(installed.Version))
        {
            throw new InvalidDataException("The asset pack update is not newer than the installed version.");
        }
        if (expected.NativeRuntime is { } native && incoming.NativePayload is { } payload)
        {
            RuntimeContentCapabilities.Require(native, payload, id);
            if (payload.Profile == "prepared-native-v1")
            {
                var formats = new HashSet<string>(StringComparer.Ordinal) { "BWTEX1" };
                if (RuntimeContentCapabilities.Advertised(native)["surface-materials"] is JsonArray versions &&
                    versions.Any(item => item!.GetValue<int>() == 1))
                {
                    formats.Add("BWSFM1");
                }
                AddRuntimeFormats("mesh_payload_versions", "BWMESH");
                AddRuntimeFormats("normal_map_formats", "BWNRM");
                if (!payload.RequiredFormats.All(formats.Contains))
                {
                    throw new InvalidDataException("The selected runtime does not support the asset pack's mesh or material formats.");
                }

                void AddRuntimeFormats(string field, string prefix)
                {
                    if (native[field] is not JsonArray versions) return;
                    foreach (var version in versions)
                    {
                        if (version is JsonValue value && value.TryGetValue<int>(out var number))
                            formats.Add(prefix + number.ToString(System.Globalization.CultureInfo.InvariantCulture));
                    }
                }
            }
        }
    }

    public static PackManifest Install(string root, string archivePath, string gameId = GameCatalog.Mw3,
        IProgress<PackInstallProgress>? progress = null, PackUpdateExpectation? expectation = null)
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
            progress?.Report(new("Checking archive", 0, 0));
            using var source = new FileStream(archivePath, FileMode.Open, FileAccess.Read, FileShare.Read);
            if (expectation?.Archive is { } artifact)
            {
                if (source.Length != artifact.Bytes ||
                    !Convert.ToHexString(SHA256.HashData(source)).Equals(artifact.Sha256, StringComparison.OrdinalIgnoreCase))
                {
                    throw new InvalidDataException("Asset pack archive does not match the signed update download.");
                }
                source.Position = 0;
            }
            using var archive = new ZipArchive(source, ZipArchiveMode.Read);
            if (archive.Entries.Count > 10000) throw new InvalidDataException("Too many pack members.");
            var manifestEntry = archive.GetEntry("pack.json") ?? throw new InvalidDataException("pack.json must be at the archive root.");
            if (manifestEntry.Length > MaxJsonBytes) throw new InvalidDataException("Pack manifest is too large.");
            ExtractBounded(manifestEntry, Path.Combine(stage, "pack.json"));
            var manifest = ReadManifest(Path.Combine(stage, "pack.json"));
            GameCatalog.RequirePackTarget(manifest.GameId, gameId, archivePath);
            if (expectation != null)
            {
                RequireOnlineUpgrade(root, gameId, manifest, expectation);
            }
            long expandedBytes = 0;
            foreach (var member in archive.Entries.Where(e => !e.FullName.EndsWith('/')))
                expandedBytes = checked(expandedBytes + member.Length);
            if (expandedBytes > MaxExpandedBytes) throw new InvalidDataException("Pack expanded size exceeds limit.");
            long progressTotal = expandedBytes;
            if (manifest.SchemaVersion == 2)
                foreach (var declaredFile in manifest.Files!.Values)
                    progressTotal = checked(progressTotal + declaredFile.Bytes);
            long completedBytes = manifestEntry.Length;
            var progressClock = System.Diagnostics.Stopwatch.StartNew();
            long lastReport = -100;
            void ReportProgress(string phase, int bytes = 0, bool force = false)
            {
                completedBytes = checked(completedBytes + bytes);
                if (progress == null || (!force && progressClock.ElapsedMilliseconds - lastReport < 100)) return;
                lastReport = progressClock.ElapsedMilliseconds;
                progress.Report(new(phase, completedBytes, progressTotal));
            }
            ReportProgress("Extracting assets", force: true);
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            long total = 0;
            foreach (var entry in archive.Entries)
            {
                var directory = entry.FullName.EndsWith('/');
                var path = directory ? entry.FullName[..^1] : entry.FullName;
                if (manifest.SchemaVersion == 3 && !PackCheck.PathIsSafe(path))
                    throw new InvalidDataException("path-unsafe: " + path);
                try { ValidatePath(path); }
                catch (InvalidDataException error) when (manifest.SchemaVersion == 3)
                {
                    throw new InvalidDataException("path-unsafe: " + error.Message, error);
                }
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
                ExtractBounded(entry, dest, progress == null ? null : bytes => ReportProgress("Extracting assets", bytes));
                if (declared != null)
                {
                    using var stream = File.OpenRead(dest);
                    using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
                    var buffer = new byte[65536];
                    int count;
                    while ((count = stream.Read(buffer)) != 0)
                    {
                        hash.AppendData(buffer, 0, count);
                        ReportProgress("Verifying assets", count);
                    }
                    if (!Convert.ToHexString(hash.GetHashAndReset()).Equals(declared.Sha256, StringComparison.OrdinalIgnoreCase))
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
                if (manifest.NativePayload.Profile == SkinPack.Profile)
                    SkinPack.Read(stage, manifest);
                else if (manifest.NativePayload.Profile == ChassisPack.Profile)
                    ChassisPack.Read(stage, manifest);
                else if (manifest.NativePayload.Profile == CinematicPack.Profile)
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
            if (manifest.SchemaVersion == 3)
            {
                var problems = PackCheck.CheckPack(stage);
                if (problems.Count > 0)
                {
                    throw new InvalidDataException($"{problems[0].Code}: {problems[0].Message}");
                }
            }
            ReportProgress("Activating assets", force: true);
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
            progress?.Report(new("Complete", progressTotal, progressTotal, true));
            return manifest;
        }
        finally { if (Directory.Exists(stage)) DeleteOwnedTree(stage); }
    }

    private static void ExtractBounded(ZipArchiveEntry entry, string destination, Action<int>? onBytes = null)
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
            onBytes?.Invoke(count);
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
