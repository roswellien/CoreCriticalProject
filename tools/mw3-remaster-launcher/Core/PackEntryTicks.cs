using System.Diagnostics;
using System.IO;
using System.Text;

namespace MW3RemasterLauncher.Core;

public sealed record PackCampaignEntry(string Id, string Name);
public sealed record PackEntryTick(PackCampaignEntry Entry, bool IsTicked);

/// <summary>
/// Reads the runtime's campaigns/&lt;entry&gt;/mods.txt directly. Only exact mod= lines
/// are interpreted; all other bytes belong to the runtime or the player.
/// </summary>
public sealed class PackEntryTicks
{
    private const string Marker = "mw3-campaign.txt";
    private readonly string dataRoot;
    private readonly Func<bool> gameIsRunning;
    public string WriteDirectory { get; }

    public PackEntryTicks(string dataRoot, string? writeDirectory = null, Func<bool>? gameIsRunning = null)
    {
        this.dataRoot = Path.GetFullPath(dataRoot);
        // This is NativeGameRunner's standard profile. Legacy modular content profiles
        // use a different write directory and are not part of this pack-tick path.
        WriteDirectory = Path.GetFullPath(writeDirectory ?? Path.Combine(dataRoot,
            "mw3-re", "profiles", NativeGameRunner.ProfileId));
        this.gameIsRunning = gameIsRunning ?? AnyGameRunning;
    }

    private static bool AnyGameRunning()
    {
        foreach (var name in new[] { "entry_commandline", "Mech3", "MW3RemasterNative", "mw3", "mw3pm" })
        {
            var processes = Process.GetProcessesByName(name);
            try { if (processes.Length != 0) return true; }
            finally { foreach (var process in processes) process.Dispose(); }
        }
        return false;
    }

    public void RequireGameClosed()
    {
        if (gameIsRunning())
            throw new InvalidOperationException("Close the game before changing gameplay pack ticks.");
    }

    private string EntryDirectory(string id)
    {
        PackStorage.ValidatePath(id);
        if (id.Contains('/')) throw new InvalidDataException("An entry ID must be one folder name.");
        var directory = PackStorage.Resolve(WriteDirectory, "campaigns/" + id);
        PackStorage.EnsureNoLinks(directory);
        return directory;
    }

    private string TickPath(string id)
    {
        var directory = EntryDirectory(id);
        PackStorage.EnsureNoLinks(Path.Combine(directory, Marker));
        var path = Path.Combine(directory, "mods.txt");
        PackStorage.EnsureNoLinks(path);
        return path;
    }

    private bool TryTickPath(string id, out string path)
    {
        try
        {
            path = TickPath(id);
            return true;
        }
        catch (Exception error) when (error is InvalidDataException or ArgumentException or
            NotSupportedException or PathTooLongException)
        {
            // One unusable folder or campaign row must not block the other entries.
            path = "";
            return false;
        }
    }

    /// <summary>
    /// Mirrors campaign_entries.cpp's names, including unplayed campaigns and saved copies.
    /// This only locates entries; pack validity and content reporting remain separate.
    /// </summary>
    public IReadOnlyList<PackCampaignEntry> Entries(IEnumerable<PackManifest> installedPacks)
    {
        var entries = new Dictionary<string, PackCampaignEntry>(StringComparer.Ordinal);
        void Add(string id, string name)
        {
            if (TryTickPath(id, out _)) entries.TryAdd(id, new(id, name));
        }
        Add("mw3", "MechWarrior 3");
        Add("ia", "Instant Action");
        Add("mp", "Multiplayer");

        var mods = Path.Combine(WriteDirectory, "mods");
        PackStorage.EnsureNoLinks(mods);
        if (Directory.Exists(mods))
            foreach (var directory in Directory.GetDirectories(mods).OrderBy(path => path, StringComparer.Ordinal))
                AddModEntries(directory, Path.GetFileName(directory), Add);
        foreach (var pack in installedPacks.Where(pack => pack.HasGameplay))
        {
            // The runtime leaves a pack out when a player's mod already owns its folder name.
            if (Directory.Exists(Path.Combine(mods, pack.Id))) continue;
            AddModEntries(PackStorage.Resolve(pack.DirectoryPath, pack.Gameplay!.Root), pack.Id, Add);
        }

        var campaigns = Path.Combine(WriteDirectory, "campaigns");
        PackStorage.EnsureNoLinks(campaigns);
        if (Directory.Exists(campaigns))
        {
            foreach (var directory in Directory.GetDirectories(campaigns).OrderBy(path => path, StringComparer.Ordinal))
            {
                if (!TryTickPath(Path.GetFileName(directory), out _)) continue;
                if (File.Exists(Path.Combine(directory, Marker)))
                    Add(Path.GetFileName(directory), Path.GetFileName(directory));
            }
        }
        return entries.Values.ToList();
    }

    private static void AddModEntries(string directory, string modId, Action<string, string> add)
    {
        var path = Path.Combine(directory, "mod.txt");
        try { PackStorage.EnsureNoLinks(path); }
        catch (InvalidDataException) { return; }
        if (!File.Exists(path)) return;
        var fields = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var campaigns = new List<string>();
        foreach (var raw in File.ReadLines(path))
        {
            var line = raw.Trim();
            if (line.StartsWith('#')) continue;
            var equals = line.IndexOf('=');
            if (equals < 0) continue;
            var key = line[..equals].Trim();
            var value = line[(equals + 1)..].Trim();
            fields[key] = value;
            if (key.Equals("campaign", StringComparison.OrdinalIgnoreCase) && value.Length > 0)
                campaigns.Add(value);
        }
        fields.TryGetValue("name", out var name);
        fields.TryGetValue("kind", out var kind);
        fields.TryGetValue("base", out var baseEntry);
        fields.TryGetValue("for", out var game);
        if (string.IsNullOrEmpty(name) || (!string.IsNullOrEmpty(game) &&
            !game.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries)[0]
                .Equals("mw3", StringComparison.OrdinalIgnoreCase))) return;
        if (string.Equals(kind, "assets", StringComparison.OrdinalIgnoreCase)) return;
        if (campaigns.Count == 0)
        {
            if (string.Equals(kind, "campaign", StringComparison.OrdinalIgnoreCase) || !string.IsNullOrEmpty(baseEntry))
                add(modId, name);
            return;
        }
        foreach (var campaign in campaigns)
        {
            // campaign_load takes the filename without .txt, never an authored title, as the ID.
            var filename = Path.GetFileName(campaign.Replace('\\', '/'));
            var id = filename.EndsWith(".txt", StringComparison.OrdinalIgnoreCase) ? filename[..^4] : filename;
            add(modId + "~" + id, name + " (" + id + ")");
        }
    }

    public IReadOnlyList<PackEntryTick> Read(PackManifest pack, IEnumerable<PackManifest> installedPacks)
    {
        if (!pack.HasGameplay) return Array.Empty<PackEntryTick>();
        return Entries(installedPacks).Select(entry => new PackEntryTick(entry,
            ContainsTick(ReadBytes(TickPath(entry.Id)), pack.Id))).ToList();
    }

    private static byte[] ReadBytes(string path)
    {
        try { return File.ReadAllBytes(path); }
        catch (FileNotFoundException) { return []; }
        catch (DirectoryNotFoundException) { return []; }
    }

    private static IEnumerable<(int Start, int ContentEnd, int End)> Lines(byte[] bytes)
    {
        for (var start = 0; start < bytes.Length;)
        {
            var newline = Array.IndexOf(bytes, (byte)'\n', start);
            var end = newline < 0 ? bytes.Length : newline + 1;
            var contentEnd = newline < 0 ? end : newline;
            if (contentEnd > start && bytes[contentEnd - 1] == '\r') contentEnd--;
            yield return (start, contentEnd, end);
            start = end;
        }
    }

    private static bool Matches(byte[] bytes, int start, int end, string id) =>
        bytes.AsSpan(start, end - start).SequenceEqual(Encoding.ASCII.GetBytes("mod=" + id));

    private static bool ContainsTick(byte[] bytes, string id) =>
        Lines(bytes).Any(line => Matches(bytes, line.Start, line.ContentEnd, id));

    private static byte[] Change(byte[] bytes, string id, bool ticked)
    {
        if (ticked)
        {
            if (ContainsTick(bytes, id)) return bytes;
            var newline = bytes.AsSpan().IndexOf("\r\n"u8) >= 0 ? "\r\n" : "\n";
            var separator = bytes.Length > 0 && bytes[^1] != '\n' ? newline : "";
            return bytes.Concat(Encoding.ASCII.GetBytes(separator + "mod=" + id + newline)).ToArray();
        }
        using var output = new MemoryStream();
        foreach (var line in Lines(bytes))
            if (!Matches(bytes, line.Start, line.ContentEnd, id))
                output.Write(bytes, line.Start, line.End - line.Start);
        return output.ToArray();
    }

    private void Replace(string path, byte[] bytes)
    {
        RequireGameClosed();
        PackStorage.EnsureNoLinks(path);
        var temporary = path + ".launcher-" + Guid.NewGuid().ToString("N") + ".new";
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                stream.Write(bytes);
                stream.Flush(flushToDisk: true);
            }
            RequireGameClosed();
            File.Move(temporary, path, overwrite: true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    private void EnsureEntry(PackCampaignEntry entry, string directory,
        List<string>? createdFiles, List<string>? createdDirectories)
    {
        RequireGameClosed();
        var marker = Path.Combine(directory, Marker);
        if (Directory.Exists(directory) && !File.Exists(marker) &&
            Directory.EnumerateFileSystemEntries(directory).Any())
            throw new InvalidOperationException("Cannot change gameplay ticks for " + entry.Id +
                ": this folder holds files the game did not put there.");

        var missing = new Stack<string>();
        for (var parent = directory; parent != null && !Directory.Exists(parent);
            parent = Path.GetDirectoryName(parent))
            missing.Push(parent);
        foreach (var path in missing)
        {
            RequireGameClosed();
            Directory.CreateDirectory(path);
            createdDirectories?.Add(path);
        }
        if (!File.Exists(marker))
        {
            RequireGameClosed();
            using var stream = new FileStream(marker, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            createdFiles?.Add(marker);
            var text = $"\"{entry.Name}\" ({entry.Id}): its mods, pilots and saves, made by the game. " +
                "Deleting this folder deletes them." + Environment.NewLine;
            stream.Write(Encoding.UTF8.GetBytes(text));
        }
        // Tick editing needs only the marker. The runtime's entry_ensure creates
        // pilots/games and configs when it prepares this entry for play.
    }

    private void WriteTick(PackCampaignEntry entry, string packId, bool ticked,
        List<string>? createdFiles = null, List<string>? createdDirectories = null)
    {
        if (!TryTickPath(entry.Id, out var path)) return;
        EnsureEntry(entry, Path.GetDirectoryName(path)!, createdFiles, createdDirectories);
        var before = ReadBytes(path);
        var after = Change(before, PackStorage.ValidateId(packId), ticked);
        if (!before.AsSpan().SequenceEqual(after)) Replace(path, after);
    }

    public void SetTick(PackManifest pack, PackCampaignEntry entry, bool ticked)
    {
        if (!pack.HasGameplay) throw new InvalidOperationException("Visual-only packs have no gameplay ticks.");
        RequireGameClosed();
        using var gate = GameUpdateGate.Acquire(dataRoot);
        RequireGameClosed();
        WriteTick(entry, pack.Id, ticked);
    }

    // The caller holds GameUpdateGate throughout installation/uninstallation.
    internal void InstallDefaults(PackManifest pack, IEnumerable<PackManifest> installedPacks)
    {
        if (!pack.HasGameplay) return;
        var entries = Entries(installedPacks.Append(pack)).Where(entry => entry.Id != "mw3").ToList();
        var originals = entries.Select(entry =>
        {
            var path = TickPath(entry.Id);
            return (Path: path, Existed: File.Exists(path), Bytes: ReadBytes(path));
        }).ToList();
        var createdFiles = new List<string>();
        var createdDirectories = new List<string>();
        try
        {
            foreach (var entry in entries)
                WriteTick(entry, pack.Id, true, createdFiles, createdDirectories);
        }
        catch (Exception failure)
        {
            // A default-tick failure must not leave a failed install ticked in earlier entries.
            var failures = new List<Exception> { failure };
            foreach (var original in originals.AsEnumerable().Reverse())
            {
                try
                {
                    if (File.Exists(original.Path) == original.Existed &&
                        ReadBytes(original.Path).AsSpan().SequenceEqual(original.Bytes)) continue;
                    RequireGameClosed();
                    PackStorage.EnsureNoLinks(original.Path);
                    if (original.Existed) Replace(original.Path, original.Bytes);
                    else File.Delete(original.Path);
                }
                catch (Exception restoreFailure) { failures.Add(restoreFailure); }
            }
            // The journal records successful creations, including a partially written
            // marker. Nonrecursive deletion preserves any unrelated content added later.
            foreach (var marker in createdFiles.AsEnumerable().Reverse())
            {
                try
                {
                    RequireGameClosed();
                    PackStorage.EnsureNoLinks(marker);
                    File.Delete(marker);
                }
                catch (Exception restoreFailure) { failures.Add(restoreFailure); }
            }
            foreach (var directory in createdDirectories.AsEnumerable().Reverse())
            {
                try
                {
                    RequireGameClosed();
                    PackStorage.EnsureNoLinks(directory);
                    Directory.Delete(directory, recursive: false);
                }
                catch (Exception restoreFailure) { failures.Add(restoreFailure); }
            }
            if (failures.Count > 1)
                throw new AggregateException("Default gameplay ticks failed; some tick files could not be restored.", failures);
            throw;
        }
    }

    internal void RemovePack(string packId)
    {
        RequireGameClosed();
        var campaigns = Path.Combine(WriteDirectory, "campaigns");
        PackStorage.EnsureNoLinks(campaigns);
        if (!Directory.Exists(campaigns)) return;
        foreach (var directory in Directory.GetDirectories(campaigns))
        {
            var id = Path.GetFileName(directory);
            if (!TryTickPath(id, out var path)) continue;
            var official = new[] { "mw3", "ia", "mp" }.Contains(id, StringComparer.OrdinalIgnoreCase);
            if (!official && !File.Exists(Path.Combine(directory, Marker))) continue;
            if (!File.Exists(path)) continue;
            // entry_ticks reads the three built-ins even without a marker. Cleanup
            // only edits their existing ticks; it must not adopt these folders.
            var before = ReadBytes(path);
            var after = Change(before, PackStorage.ValidateId(packId), false);
            if (!before.AsSpan().SequenceEqual(after)) Replace(path, after);
        }
    }
}
