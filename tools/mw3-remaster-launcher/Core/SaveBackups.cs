using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

public sealed record SaveSnapshot(int SchemaVersion, string Label, DateTime CreatedUtc, Dictionary<string, UpdateFile> Files);

/// <summary>Portable local snapshots of player files, with validated restore and automatic undo backup.</summary>
public sealed class SaveBackups
{
    private sealed class NoSavedFilesException() : InvalidOperationException("No saved pilots or configurations were found yet.");
    private const long MaxTotal = 256L * 1024 * 1024;
    private const long MaxFile = 32L * 1024 * 1024;
    private readonly string _game;
    private readonly string? _registry;
    public string DirectoryPath { get; }

    public SaveBackups(string game, string dataRoot, string? registry = null)
    {
        _game = Path.GetFullPath(game);
        PackStorage.EnsureNoLinks(_game);
        if (!Directory.Exists(_game)) throw new DirectoryNotFoundException("Choose your game folder first.");
        _registry = registry == null ? null : Path.GetFullPath(registry);
        DirectoryPath = PackStorage.Resolve(dataRoot, "save-backups");
        PackStorage.EnsureNoLinks(DirectoryPath);
        Directory.CreateDirectory(DirectoryPath);
    }

    public static void RequireGameClosed()
    {
        foreach (var name in new[] { "entry_commandline", "Mech3" })
        {
            var processes = Process.GetProcessesByName(name);
            try { if (processes.Length != 0) throw new InvalidOperationException("Close the game before backing up or restoring saves."); }
            finally { foreach (var process in processes) process.Dispose(); }
        }
    }

    public string[] List() => Directory.GetFiles(DirectoryPath, "*.mw3save.zip")
        .OrderByDescending(File.GetLastWriteTimeUtc).ToArray();

    private string Destination(string name)
    {
        if (name == "player-registry.txt")
            return _registry ?? throw new InvalidDataException("This backup includes native player settings, but this installation has no settings destination.");
        if (!(name.StartsWith("pilots/", StringComparison.Ordinal) || name.StartsWith("configs/", StringComparison.Ordinal)) ||
            !name.EndsWith(".mw3", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Unsupported save entry: " + name);
        return PackStorage.Resolve(_game, name);
    }

    public string Create(string label)
    {
        using var storageLock = new FileStream(Path.Combine(DirectoryPath, ".save-lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        return CreateSnapshot(label);
    }

    private string CreateSnapshot(string label)
    {
        RequireGameClosed();
        var paths = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var folder in new[] { "pilots", "configs" })
        {
            var root = PackStorage.Resolve(_game, folder);
            if (!Directory.Exists(root)) continue;
            // Walk one directory at a time so links are rejected before descent.
            void Walk(string directory)
            {
                PackStorage.EnsureNoLinks(directory);
                foreach (var path in Directory.EnumerateFileSystemEntries(directory))
                {
                    PackStorage.EnsureNoLinks(path);
                    if (Directory.Exists(path)) Walk(path);
                    else if (path.EndsWith(".mw3", StringComparison.OrdinalIgnoreCase))
                        paths.Add(Path.GetRelativePath(_game, path).Replace('\\', '/'), path);
                    if (paths.Count > 10000) throw new InvalidDataException("Too many save files.");
                }
            }
            Walk(root);
        }
        if (_registry != null && File.Exists(_registry)) paths.Add("player-registry.txt", _registry);
        if (paths.Count == 0) throw new NoSavedFilesException();
        var target = Path.Combine(DirectoryPath, DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N")[..8] + ".mw3save.zip");
        var temporary = target + ".partial";
        try
        {
            using (var file = new FileStream(temporary, FileMode.CreateNew))
            using (var archive = new ZipArchive(file, ZipArchiveMode.Create))
            {
                var pins = new Dictionary<string, UpdateFile>();
                long total = 0;
                foreach (var (name, path) in paths)
                {
                    PackStorage.EnsureNoLinks(path);
                    using var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
                    if (input.Length > MaxFile || (total += input.Length) > MaxTotal) throw new InvalidDataException("Save backup exceeds its size limit.");
                    var bytes = new byte[checked((int)input.Length)];
                    input.ReadExactly(bytes);
                    using var entry = archive.CreateEntry(name, CompressionLevel.Optimal).Open();
                    entry.Write(bytes);
                    pins.Add(name, new(bytes.LongLength, Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()));
                }
                using var manifest = archive.CreateEntry("snapshot.json").Open();
                JsonSerializer.Serialize(manifest, new SaveSnapshot(1, label[..Math.Min(label.Length, 120)], DateTime.UtcNow, pins));
            }
            File.Move(temporary, target);
            return target;
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    public string Restore(string backup)
    {
        using var storageLock = new FileStream(Path.Combine(DirectoryPath, ".save-lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        RequireGameClosed();
        PackStorage.EnsureNoLinks(backup);
        if (new FileInfo(backup).Length > MaxTotal + 1024 * 1024) throw new InvalidDataException("Backup archive is too large.");
        var content = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
        using (var archive = ZipFile.OpenRead(backup))
        {
            if (archive.Entries.Count > 10001) throw new InvalidDataException("Too many backup entries.");
            var manifests = archive.Entries.Where(e => e.FullName == "snapshot.json").ToArray();
            if (manifests.Length != 1 || manifests[0].Length > 2 * 1024 * 1024) throw new InvalidDataException("Missing or excessive save snapshot metadata.");
            using var metadata = manifests[0].Open();
            var snapshot = JsonSerializer.Deserialize<SaveSnapshot>(metadata) ?? throw new InvalidDataException("Empty save snapshot.");
            if (snapshot.SchemaVersion != 1 || snapshot.Files == null || snapshot.Files.Count == 0 || snapshot.Files.Count > 10000)
                throw new InvalidDataException("Unsupported save snapshot.");
            long total = 0;
            foreach (var entry in archive.Entries.Where(e => e.FullName != "snapshot.json"))
            {
                if (!snapshot.Files.TryGetValue(entry.FullName, out var pin) || pin == null || pin.Bytes < 0 || pin.Bytes > MaxFile ||
                    entry.Length != pin.Bytes || (total += pin.Bytes) > MaxTotal || content.ContainsKey(entry.FullName))
                    throw new InvalidDataException("Invalid or duplicate save entry.");
                var destination = Destination(entry.FullName);
                PackStorage.EnsureNoLinks(destination);
                using var source = entry.Open();
                var data = new byte[checked((int)pin.Bytes)];
                source.ReadExactly(data);
                if (source.ReadByte() != -1 || !Convert.ToHexString(SHA256.HashData(data)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Save backup is damaged: " + entry.FullName);
                content.Add(entry.FullName, data);
            }
            if (content.Count != snapshot.Files.Count) throw new InvalidDataException("Save backup is incomplete.");
        }
        // Validate the entire archive before touching player files.
        string safety;
        try { safety = CreateSnapshot("Automatic backup before restore"); }
        catch (NoSavedFilesException) { safety = "No existing saves to replace"; }
        RequireGameClosed();
        var previous = new Dictionary<string, byte[]?>();
        try
        {
            foreach (var (name, data) in content)
            {
                var path = Destination(name);
                PackStorage.EnsureNoLinks(path);
                if (File.Exists(path) && new FileInfo(path).Length > MaxFile) throw new InvalidDataException("Existing save is too large.");
                previous.Add(path, File.Exists(path) ? File.ReadAllBytes(path) : null);
                WriteAtomic(path, data);
            }
        }
        catch
        {
            foreach (var (path, data) in previous.Reverse())
            {
                if (data == null) { if (File.Exists(path)) File.Delete(path); }
                else WriteAtomic(path, data);
            }
            throw;
        }
        return safety;
    }

    private static void WriteAtomic(string path, byte[] data)
    {
        PackStorage.EnsureNoLinks(path);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + ".restore-" + Guid.NewGuid().ToString("N");
        try { File.WriteAllBytes(temp, data); File.Move(temp, path, true); }
        finally { if (File.Exists(temp)) File.Delete(temp); }
    }
}
