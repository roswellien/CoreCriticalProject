using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using MW3RemasterLauncher;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncherTests;

public static class PackEntryTickChecks
{
    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    private static string Archive(string root, string fixture, string version = "1.0.0", bool campaign = false)
    {
        var path = Path.Combine(root, Guid.NewGuid() + ".mw3pack");
        ZipFile.CreateFromDirectory(Path.Combine(PackContractChecks.FindRepositoryRoot(),
            "tests", "fixtures", "packs", "valid", fixture), path);
        if (version != "1.0.0" || campaign)
        {
            using var zip = ZipFile.Open(path, ZipArchiveMode.Update);
            var manifest = zip.GetEntry("pack.json")!;
            JsonObject json;
            using (var reader = new StreamReader(manifest.Open())) json = JsonNode.Parse(reader.ReadToEnd())!.AsObject();
            manifest.Delete();
            json["version"] = version;
            if (campaign)
            {
                json["id"] = "example-campaign";
                foreach (var (filename, text) in new[]
                {
                    ("mod/mod.txt", "name=Pack campaign\ncampaign=First.txt\n"),
                    ("mod/First.txt", "name=First chapter\nmission=c1 1\n")
                })
                {
                    zip.GetEntry(filename)?.Delete();
                    var bytes = Encoding.UTF8.GetBytes(text);
                    using (var stream = zip.CreateEntry(filename).Open()) stream.Write(bytes);
                    json["files"]![filename] = new JsonObject
                    {
                        ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant(),
                        ["bytes"] = bytes.Length
                    };
                }
            }
            using var writer = new StreamWriter(zip.CreateEntry("pack.json").Open());
            writer.Write(json.ToJsonString());
        }
        return path;
    }

    private static string TickPath(string writeDirectory, string entry) =>
        Path.Combine(writeDirectory, "campaigns", entry, "mods.txt");

    private static void WriteEntry(string writeDirectory, string entry, byte[] bytes)
    {
        var path = TickPath(writeDirectory, entry);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(Path.Combine(Path.GetDirectoryName(path)!, "mw3-campaign.txt"), "Test campaign entry\n");
        File.WriteAllBytes(path, bytes);
    }

    private static void Lifecycle(string root)
    {
        var manager = new PackManager(root);
        var writeDirectory = manager.EntryTicks.WriteDirectory;
        var originalMw3 = "# Original campaign\r\nmod=player-mod\r\n"u8.ToArray();
        WriteEntry(writeDirectory, "mw3", originalMw3);
        WriteEntry(writeDirectory, "imported~first", "mod=player-mod\n"u8.ToArray());
        WriteEntry(writeDirectory, "saved-copy", []);
        foreach (var (id, text) in new[]
        {
            ("unplayed", "name=Unplayed campaigns\nfor=mw3 1.2\ncampaign=chapters/First.txt\ncampaign=Second.txt\n"),
            ("new-copy", "name=New copy\nbase=mw3\n")
        })
        {
            var directory = Path.Combine(writeDirectory, "mods", id);
            Directory.CreateDirectory(directory);
            File.WriteAllText(Path.Combine(directory, "mod.txt"), text);
        }
        var playerFiles = Directory.GetFiles(Path.Combine(writeDirectory, "mods"), "*", SearchOption.AllDirectories)
            .ToDictionary(path => path, File.ReadAllBytes);
        var archive = Archive(root, "gameplay-only");
        var pack = manager.InstallPack(archive);
        var entries = manager.ReadEntryTicks(pack);
        foreach (var id in new[] { "ia", "mp", "imported~first", "saved-copy", "unplayed~First", "unplayed~Second", "new-copy" })
        {
            Assert(entries.Any(tick => tick.Entry.Id == id && tick.IsTicked), "Default tick missing for " + id);
            Assert(File.ReadAllText(TickPath(writeDirectory, id)).EndsWith("mod=" + pack.Id + "\n"), "Default tick was not appended.");
        }
        Assert(!entries.Single(tick => tick.Entry.Id == "mw3").IsTicked, "Original campaign ticked by default.");
        Assert(File.ReadAllBytes(TickPath(writeDirectory, "mw3")).SequenceEqual(originalMw3), "Original campaign changed at install.");
        Assert(File.ReadAllText(TickPath(writeDirectory, "imported~first")) == "mod=player-mod\nmod=" + pack.Id + "\n", "Default tick changed existing precedence.");
        Assert(File.Exists(Path.Combine(writeDirectory, "campaigns", "ia", "mw3-campaign.txt")), "New entry lacks runtime marker.");

        // entry_save_ticks writes exact mod= lines, LF, and the folder ID in precedence order.
        File.WriteAllText(TickPath(writeDirectory, "mw3"), "mod=player-mod\nmod=" + pack.Id + "\n");
        File.WriteAllText(TickPath(writeDirectory, "ia"), "mod=player-mod\n");
        Assert(manager.ReadEntryTicks(pack).Single(tick => tick.Entry.Id == "mw3").IsTicked, "Runtime-form ticks were not read directly from disk.");
        manager.InstallPack(archive);
        var updated = manager.InstallPackAsync(Archive(root, "gameplay-only", "1.1.0")).GetAwaiter().GetResult();
        Assert(updated.Version == "1.1.0", "Update fixture did not change version.");
        var reopened = new PackManager(root);
        reopened.RefreshPacks();
        entries = reopened.ReadEntryTicks(updated);
        Assert(!entries.Single(tick => tick.Entry.Id == "ia").IsTicked && entries.Single(tick => tick.Entry.Id == "mw3").IsTicked, "Reinstall or update reset player choices.");
        var visual = manager.InstallPack(Archive(root, "visuals-only"));
        Assert(!visual.HasGameplay && manager.ReadEntryTicks(visual).Count == 0, "Visual-only pack has entry ticks.");
        Assert(!Directory.GetFiles(Path.Combine(writeDirectory, "campaigns"), "mods.txt", SearchOption.AllDirectories)
            .Any(path => File.ReadAllText(path).Contains("mod=" + visual.Id)), "Visual-only install wrote a tick.");
        // A pack without gameplay never owned a tick, so a mod= line with its ID belongs to
        // a player's own mod of the same name and must survive the pack's uninstall.
        var sameNameTick = Encoding.UTF8.GetBytes("mod=" + visual.Id + "\n");
        WriteEntry(writeDirectory, "same-name-player-mod", sameNameTick);
        manager.UninstallPack(visual);
        Assert(File.ReadAllBytes(TickPath(writeDirectory, "same-name-player-mod")).SequenceEqual(sameNameTick),
            "Uninstalling a visual-only pack removed a player's tick of the same name.");
        var campaign = manager.InstallPack(Archive(root, "gameplay-only", campaign: true));
        Assert(manager.ReadEntryTicks(campaign).Any(tick =>
            tick.Entry.Id == "example-campaign~First" && tick.IsTicked),
            "Unplayed campaign from the newly installed pack missed its default tick.");
        WriteEntry(writeDirectory, "orphaned-folder", Encoding.UTF8.GetBytes("# keep\r\nmod=" + pack.Id + "\r\nfuture=stay"));
        manager.UninstallPack(updated);
        Assert(!Directory.Exists(updated.DirectoryPath), "Uninstall retained the pack folder.");
        Assert(File.ReadAllText(TickPath(writeDirectory, "orphaned-folder")) == "# keep\r\nfuture=stay", "Uninstall missed an entry or changed unknown text.");
        Assert(!Directory.GetFiles(Path.Combine(writeDirectory, "campaigns"), "mods.txt", SearchOption.AllDirectories)
            .Any(path => File.ReadAllText(path).Contains("mod=" + pack.Id)), "Uninstall left a tick.");
        Assert(playerFiles.All(file => File.ReadAllBytes(file.Key).SequenceEqual(file.Value)) &&
            Directory.GetFiles(Path.Combine(writeDirectory, "mods"), "*", SearchOption.AllDirectories).Length == playerFiles.Count, "Launcher wrote into the player's mods folder.");
        Console.WriteLine("PASS: defaults, runtime entry names/markers/readback, reinstall/update, visual-only and uninstall.");
    }

    private static void Refused(Action action)
    {
        try { action(); }
        catch (InvalidOperationException error) when (error.Message.Contains("Close the game")) { return; }
        throw new Exception("Running-game edit was accepted or lacked a plain refusal message.");
    }

    private static void PreservationAndRefusals(string root)
    {
        var running = false;
        var ticks = new PackEntryTicks(root, gameIsRunning: () => running);
        var manager = new PackManager(root, entryTicks: ticks);
        var pack = new PackManifest { SchemaVersion = 3, Id = "example-gameplay", Gameplay = new() { Root = "mod" } };
        var entry = new PackCampaignEntry("ia", "Instant Action");
        var path = TickPath(ticks.WriteDirectory, "ia");
        foreach (var original in new[]
        {
            "# comment\r\nmod=other\nfuture=keep\r\n"u8.ToArray(),
            "future=no-newline"u8.ToArray(), new byte[] { 0xff, 0xfe, 0, 10 }, Array.Empty<byte>()
        })
        {
            WriteEntry(ticks.WriteDirectory, "ia", original);
            ticks.SetTick(pack, entry, true);
            var enabled = File.ReadAllBytes(path);
            Assert(enabled.AsSpan(0, original.Length).SequenceEqual(original), "Tick changed unknown bytes or order.");
            Assert(ticks.Read(pack, []).Single(tick => tick.Entry.Id == "ia").IsTicked, "Appended tick did not read back.");
            ticks.SetTick(pack, entry, true);
            Assert(File.ReadAllBytes(path).SequenceEqual(enabled), "Repeated tick duplicated the line.");
            ticks.SetTick(pack, entry, false);
            var expected = original.Length > 0 && original[^1] != '\n' ? original.Concat("\n"u8.ToArray()).ToArray() : original;
            Assert(File.ReadAllBytes(path).SequenceEqual(expected), "Untick changed an unrelated line.");
        }
        WriteEntry(ticks.WriteDirectory, "ia", "mod=example-gameplay\r\nmod=example-gameplay-extra\n mod=example-gameplay\nmod=example-gameplay\nfuture=stay"u8.ToArray());
        ticks.SetTick(pack, entry, false);
        Assert(File.ReadAllText(path) == "mod=example-gameplay-extra\n mod=example-gameplay\nfuture=stay", "Untick removed another line or left a duplicate.");
        var originalBytes = File.ReadAllBytes(path);
        using (var held = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            var failed = false;
            try { ticks.SetTick(pack, entry, true); }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException) { failed = true; }
            Assert(failed, "Locked destination unexpectedly replaced.");
            Assert(File.ReadAllBytes(path).SequenceEqual(originalBytes), "Failed replacement changed old file.");
        }
        Assert(Directory.GetFiles(Path.GetDirectoryName(path)!, "*.new").Length == 0, "Failed replacement left staging files.");
        var beforeRunning = Directory.GetFiles(root, "*", SearchOption.AllDirectories).ToDictionary(path => path, File.ReadAllBytes);
        running = true;
        Refused(() => ticks.SetTick(pack, entry, true));
        Refused(() => ticks.SetTick(pack, new("mp", "Multiplayer"), true));
        var archive = Archive(Path.GetDirectoryName(root)!, "gameplay-only");
        Refused(() => manager.InstallPack(archive));
        pack.DirectoryPath = Path.Combine(manager.ModsRoot, pack.Id);
        Refused(() => manager.UninstallPack(pack));
        Assert(beforeRunning.All(file => File.ReadAllBytes(file.Key).SequenceEqual(file.Value)) &&
            Directory.GetFiles(root, "*", SearchOption.AllDirectories).Length == beforeRunning.Count, "Running-game refusal wrote files.");
        running = false;
        using (GameUpdateGate.Acquire(root))
        {
            var refused = false;
            try { ticks.SetTick(pack, entry, true); }
            catch (InvalidOperationException) { refused = true; }
            Assert(refused, "Active launcher session gate did not block tick edits.");
        }
        Console.WriteLine("PASS: byte preservation, exact removal, idempotence, failed replacement, game refusal and session gate.");
    }

    private static void FailedDefaults(string root, bool keepEmptyDirectory = false, bool denyReads = false)
    {
        var manager = new PackManager(root);
        WriteEntry(manager.EntryTicks.WriteDirectory, "mp", "mod=other\n"u8.ToArray());
        WriteEntry(manager.EntryTicks.WriteDirectory, "empty-saved", []);
        WriteEntry(manager.EntryTicks.WriteDirectory, "zz-failure", "mod=other\n"u8.ToArray());
        var iaDirectory = Path.GetDirectoryName(TickPath(manager.EntryTicks.WriteDirectory, "ia"))!;
        if (keepEmptyDirectory) Directory.CreateDirectory(iaDirectory);
        var path = TickPath(manager.EntryTicks.WriteDirectory, "zz-failure");
        var failed = false;
        using (var held = new FileStream(path, FileMode.Open, FileAccess.Read,
            denyReads ? FileShare.None : FileShare.Read))
        {
            try { manager.InstallPack(Archive(root, "gameplay-only", campaign: true)); }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException) { failed = true; }
        }
        Assert(failed, "Failed default write reported success.");
        Assert(File.ReadAllText(path) == "mod=other\n", "Failed default write changed old file.");
        Assert(!Directory.Exists(Path.Combine(manager.ModsRoot, "example-campaign")), "Failed install activated the pack.");
        Assert(!File.Exists(TickPath(manager.EntryTicks.WriteDirectory, "ia")), "Failed defaults retained an earlier tick.");
        Assert(!File.Exists(Path.Combine(iaDirectory, "mw3-campaign.txt")),
            "Failed defaults retained a newly created marker.");
        Assert(Directory.Exists(iaDirectory) == keepEmptyDirectory,
            "Failed defaults retained a new folder or deleted a preexisting empty folder.");
        if (keepEmptyDirectory)
            Assert(!Directory.EnumerateFileSystemEntries(iaDirectory).Any(),
                "Failed defaults changed a preexisting empty folder.");
        Assert(!Directory.Exists(Path.GetDirectoryName(
            TickPath(manager.EntryTicks.WriteDirectory, "example-campaign~First"))),
            "Failed campaign-pack install left an orphan campaign folder.");
        Assert(File.ReadAllText(TickPath(manager.EntryTicks.WriteDirectory, "mp")) == "mod=other\n",
            "Failed defaults did not restore the preexisting multiplayer ticks.");
        Assert(File.ReadAllText(Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns", "mp",
            "mw3-campaign.txt")) == "Test campaign entry\n", "Rollback replaced a preexisting marker.");
        var emptyTicks = TickPath(manager.EntryTicks.WriteDirectory, "empty-saved");
        Assert(File.Exists(emptyTicks) && new FileInfo(emptyTicks).Length == 0,
            "Rollback deleted or changed a preexisting empty tick file.");
        Console.WriteLine("PASS: failed defaults restore earlier ticks and roll back pack activation.");
    }

    private static void CreateJunction(string path, string target)
    {
        // Junctions exercise Windows reparse points without requiring symlink privileges.
        var command = new System.Diagnostics.ProcessStartInfo
        {
            FileName = Path.Combine(Environment.SystemDirectory, "WindowsPowerShell", "v1.0", "powershell.exe"),
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardError = true,
            RedirectStandardOutput = true
        };
        command.ArgumentList.Add("-NoProfile");
        command.ArgumentList.Add("-NonInteractive");
        command.ArgumentList.Add("-Command");
        command.ArgumentList.Add("$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path '" +
            path.Replace("'", "''") + "' -Target '" + target.Replace("'", "''") + "' | Out-Null");
        using var process = System.Diagnostics.Process.Start(command)!;
        if (!process.WaitForExit(10000))
        {
            process.Kill(entireProcessTree: true);
            throw new Exception("Timed out creating the temporary junction.");
        }
        Assert(process.ExitCode == 0, "Temporary junction setup failed: " + process.StandardError.ReadToEnd());
        Assert((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0,
            "Temporary junction was not a reparse point.");
    }

    private static void OddEntry(string root, string kind, string operation)
    {
        var manager = new PackManager(root);
        PackManifest pack = null;
        if (operation != "install") pack = manager.InstallPack(Archive(root, "gameplay-only"));
        var campaigns = Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns");
        Directory.CreateDirectory(campaigns);
        string untouchedTicks = null;
        string junction = null;
        try
        {
            var oddId = "NUL.test";
            if (kind == "folder")
            {
                var directory = @"\\?\" + Path.Combine(campaigns, oddId);
                Directory.CreateDirectory(directory);
                File.WriteAllText(Path.Combine(directory, "mw3-campaign.txt"), "Test marker\n");
                untouchedTicks = Path.Combine(directory, "mods.txt");
            }
            else if (kind == "link")
            {
                oddId = "linked-entry";
                var target = Path.Combine(root, "link-target");
                Directory.CreateDirectory(target);
                File.WriteAllText(Path.Combine(target, "mw3-campaign.txt"), "Test marker\n");
                untouchedTicks = Path.Combine(target, "mods.txt");
                junction = Path.Combine(campaigns, oddId);
                CreateJunction(junction, target);
            }
            else
            {
                oddId = "broken~trailing ";
                var source = Path.Combine(manager.EntryTicks.WriteDirectory, "mods", "broken");
                Directory.CreateDirectory(source);
                File.WriteAllText(Path.Combine(source, "mod.txt"),
                    "name=Bad entry name\nfor=mw3 1.2\ncampaign=trailing .txt\n");
            }
            const string original = "mod=example-gameplay\n# leave this alone\n";
            if (untouchedTicks != null) File.WriteAllText(untouchedTicks, original);
            if (operation == "install") pack = manager.InstallPack(Archive(root, "gameplay-only"));
            if (operation == "uninstall")
                Assert(manager.UninstallPack(pack) && !Directory.Exists(pack.DirectoryPath),
                    "Odd entry blocked uninstall.");
            else
            {
                var entries = manager.ReadEntryTicks(pack);
                Assert(entries.Any(tick => tick.Entry.Id == "ia" && tick.IsTicked),
                    "Odd entry prevented reading normal dialog entries.");
                Assert(entries.All(tick => tick.Entry.Id != oddId), "Unsafe entry was offered as a tick target.");
            }
            if (untouchedTicks != null)
                Assert(File.ReadAllText(untouchedTicks) == original, "Unsafe entry or link target was edited.");
        }
        finally
        {
            // Remove the junction itself before the fixture recursively removes its own folders.
            if (junction != null && Directory.Exists(junction)) Directory.Delete(junction);
        }
    }

    private static void UninstallOwnership(string root)
    {
        var manager = new PackManager(root);
        var pack = manager.InstallPack(Archive(root, "gameplay-only"));
        var original = Encoding.UTF8.GetBytes("# keep\r\nmod=" + pack.Id + "\nother=bytes");
        var unmarked = TickPath(manager.EntryTicks.WriteDirectory, "unmarked-custom");
        Directory.CreateDirectory(Path.GetDirectoryName(unmarked)!);
        File.WriteAllBytes(unmarked, original);
        foreach (var entry in new[] { "mw3", "ia", "mp" })
        {
            var path = TickPath(manager.EntryTicks.WriteDirectory, entry);
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.Delete(Path.Combine(Path.GetDirectoryName(path)!, "mw3-campaign.txt"));
            File.WriteAllBytes(path, original);
        }
        WriteEntry(manager.EntryTicks.WriteDirectory, "marked-custom", original);
        manager.UninstallPack(pack);
        Assert(File.ReadAllBytes(unmarked).SequenceEqual(original),
            "Uninstall edited an unmarked custom folder ignored by the runtime.");
        foreach (var entry in new[] { "mw3", "ia", "mp", "marked-custom" })
        {
            var path = TickPath(manager.EntryTicks.WriteDirectory, entry);
            Assert(File.ReadAllText(path) == "# keep\r\nother=bytes",
                "Uninstall missed runtime-owned ticks in " + entry);
            if (entry != "marked-custom")
                Assert(!File.Exists(Path.Combine(Path.GetDirectoryName(path)!, "mw3-campaign.txt")),
                    "Uninstall adopted an unmarked official entry.");
        }
    }

    private static void BrokenOfficialLink(string root)
    {
        var manager = new PackManager(root);
        var campaigns = Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns");
        Directory.CreateDirectory(campaigns);
        var target = Path.Combine(root, "missing-target");
        Directory.CreateDirectory(target);
        var junction = Path.Combine(campaigns, "ia");
        CreateJunction(junction, target);
        try
        {
            Directory.Delete(target);
            var pack = manager.InstallPack(Archive(root, "gameplay-only"));
            var entries = manager.ReadEntryTicks(pack);
            Assert(entries.All(tick => tick.Entry.Id != "ia") &&
                entries.Any(tick => tick.Entry.Id == "mp" && tick.IsTicked),
                "Broken built-in link was offered as a tick target or blocked normal defaults.");
            manager.UninstallPack(pack);
            Assert(!Directory.Exists(target), "Tick editing recreated the broken link's target.");
        }
        finally { Directory.Delete(junction); }
    }

    private static void UppercaseGame(string root)
    {
        var manager = new PackManager(root);
        var source = Path.Combine(manager.EntryTicks.WriteDirectory, "mods", "uppercase");
        Directory.CreateDirectory(source);
        File.WriteAllText(Path.Combine(source, "mod.txt"),
            "name=Uppercase target\nfor=MW3 1.2\ncampaign=Chapter.txt\n");
        var pack = manager.InstallPack(Archive(root, "gameplay-only"));
        Assert(manager.ReadEntryTicks(pack).Any(tick =>
            tick.Entry.Id == "uppercase~Chapter" && tick.IsTicked),
            "for=MW3 was not discovered and default-ticked.");
    }

    private static void ForeignFolder(string root, bool existingTick)
    {
        var ticks = new PackEntryTicks(root);
        var pack = new PackManifest { SchemaVersion = 3, Id = "example-gameplay", Gameplay = new() };
        var path = TickPath(ticks.WriteDirectory, "ia");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var foreignPath = existingTick ? path : Path.Combine(Path.GetDirectoryName(path)!, "player-note.txt");
        var bytes = existingTick ? "mod=example-gameplay\n"u8.ToArray() : "Keep my note\n"u8.ToArray();
        File.WriteAllBytes(foreignPath, bytes);
        var refused = false;
        try { ticks.SetTick(pack, new("ia", "Instant Action"), true); }
        catch (InvalidOperationException error) when (error.Message.Contains("game did not put there"))
        {
            refused = true;
        }
        Assert(refused, "Nonempty unmarked entry was not refused with a plain message.");
        Assert(File.ReadAllBytes(foreignPath).SequenceEqual(bytes) &&
            Directory.EnumerateFileSystemEntries(Path.GetDirectoryName(path)!).Count() == 1,
            "Refused edit wrote into a nonempty unmarked folder.");
    }

    private static void RuntimeMarker(string root, bool existingEmpty)
    {
        var ticks = new PackEntryTicks(root);
        var directory = Path.GetDirectoryName(TickPath(ticks.WriteDirectory, "ia"))!;
        if (existingEmpty) Directory.CreateDirectory(directory);
        var pack = new PackManifest { SchemaVersion = 3, Id = "example-gameplay", Gameplay = new() };
        ticks.SetTick(pack, new("ia", "Instant Action"), true);
        var expected = "\"Instant Action\" (ia): its mods, pilots and saves, made by the game. " +
            "Deleting this folder deletes them." + Environment.NewLine;
        Assert(File.ReadAllBytes(Path.Combine(directory, "mw3-campaign.txt"))
            .SequenceEqual(Encoding.UTF8.GetBytes(expected)), "New marker differs from entry_ensure's text.");
    }

    private static void RollbackGuards(string root, bool gameRunning)
    {
        var running = false;
        var manager = new PackManager(root,
            entryTicks: new PackEntryTicks(root, gameIsRunning: () => running));
        manager.InstallPack(Archive(root, "gameplay-only"));
        var pack = manager.InstallPack(Archive(root, "gameplay-only", "1.1.0"));
        var manifestPath = Path.Combine(pack.DirectoryPath, "pack.json");
        var before = File.ReadAllBytes(manifestPath);
        if (gameRunning)
        {
            running = true;
            Refused(() => manager.RollbackPack(pack));
            running = false;
        }
        else
        {
            using var gate = GameUpdateGate.Acquire(root);
            var refused = false;
            try { manager.RollbackPack(pack); }
            catch (InvalidOperationException error) when (error.Message.Contains("starting/running"))
            {
                refused = true;
            }
            Assert(refused, "Rollback did not acquire the launcher game-session gate.");
        }
        Assert(File.ReadAllBytes(manifestPath).SequenceEqual(before) && manager.Packs.Single().Version == "1.1.0",
            "Refused rollback swapped pack contents or collection state.");
        manager.RollbackPack(pack);
        Assert(manager.Packs.Single().Version == "1.0.0", "Game-closed rollback no longer works.");
    }

    private static void ReviewRegressions(string root)
    {
        var cases = new List<(string Name, Action<string> Check)>();
        foreach (var kind in new[] { "folder", "link", "row" })
            foreach (var operation in new[] { "install", "uninstall", "dialog" })
                cases.Add(($"1-{kind}-{operation}", folder => OddEntry(folder, kind, operation)));
        cases.Add(("2-uninstall-ownership", UninstallOwnership));
        cases.Add(("1-broken-official-link", BrokenOfficialLink));
        cases.Add(("3-uppercase-for", UppercaseGame));
        cases.Add(("4-foreign-folder", folder => ForeignFolder(folder, false)));
        cases.Add(("4-foreign-existing-tick", folder => ForeignFolder(folder, true)));
        cases.Add(("4-new-marker", folder => RuntimeMarker(folder, false)));
        cases.Add(("4-empty-marker", folder => RuntimeMarker(folder, true)));
        cases.Add(("5-new-folder-cleanup", folder => FailedDefaults(folder)));
        cases.Add(("5-preserve-empty-folder", folder => FailedDefaults(folder, true)));
        cases.Add(("6-running-rollback", folder => RollbackGuards(folder, true)));
        cases.Add(("6-session-rollback", folder => RollbackGuards(folder, false)));
        cases.Add(("r2-1-refused-defaults", RefusedDefaults));
        cases.Add(("r2-2-linked-mods", LinkedPlayerMods));
        cases.Add(("r2-2-linked-campaigns", LinkedCampaigns));
        foreach (var kind in new[] { "malformed", "mismatched-id", "bad-root", "missing-root" })
        {
            cases.Add(($"r2-3-{kind}-install", folder => InvalidSibling(folder, kind, false)));
            cases.Add(($"r2-3-{kind}-dialog", folder => InvalidSibling(folder, kind, true)));
        }
        cases.Add(("r2-campaign-labels", CampaignLabels));
        cases.Add(("r2-locked-tick-read", folder => FailedDefaults(folder, denyReads: true)));
        cases.Add(("r2-unreadable-player-mod", UnreadablePlayerMod));
        foreach (var kind in new[] { "tick-folder", "marker-folder", "entry-file", "campaigns-file" })
            cases.Add(($"r2-{kind}", folder => TickPathCollision(folder, kind)));
        var failures = new List<Exception>();
        foreach (var (name, check) in cases)
        {
            var folder = Path.Combine(root, name);
            Directory.CreateDirectory(folder);
            try
            {
                check(folder);
                Console.WriteLine("PASS review regression: " + name);
            }
            catch (Exception error)
            {
                Console.WriteLine("FAIL review regression: " + name + ": " + error.Message);
                failures.Add(new Exception(name, error));
            }
        }
        if (failures.Count != 0) throw new AggregateException("Review regressions failed.", failures);
    }

    private static void RefusedDefaults(string root)
    {
        var manager = new PackManager(root);
        var ia = TickPath(manager.EntryTicks.WriteDirectory, "ia");
        Directory.CreateDirectory(Path.GetDirectoryName(ia)!);
        File.WriteAllText(ia, "mod=player-mod\n");
        var source = Path.Combine(manager.EntryTicks.WriteDirectory, "mods", "foreign");
        Directory.CreateDirectory(source);
        File.WriteAllText(Path.Combine(source, "mod.txt"), "name=Foreign campaign\nkind=campaign\n");
        var custom = Path.GetDirectoryName(TickPath(manager.EntryTicks.WriteDirectory, "foreign"))!;
        Directory.CreateDirectory(custom);
        File.WriteAllText(Path.Combine(custom, "player-note.txt"), "Keep this\n");
        var archive = Archive(root, "gameplay-only");
        var pack = manager.InstallPack(archive);
        foreach (var id in new[] { "ia", "foreign" })
            Assert(pack.DefaultTickWarnings.Any(warning => warning.EntryId == id &&
                warning.Reason.Contains("game did not put there")),
                "Skipped default entry and its reason were not returned for " + id);
        Assert(manager.ReadEntryTicks(pack).Single(tick => tick.Entry.Id == "mp").IsTicked,
            "An unusable IA/custom entry blocked normal multiplayer defaults.");
        Assert(File.ReadAllText(ia) == "mod=player-mod\n" &&
            !File.Exists(Path.Combine(Path.GetDirectoryName(ia)!, "mw3-campaign.txt")),
            "Default ticks adopted an entry that entry_ensure refuses.");
        manager.UninstallPack(pack);
        manager.InstallPack(archive);
        Assert(File.ReadAllText(ia) == "mod=player-mod\n" &&
            File.ReadAllText(Path.Combine(custom, "player-note.txt")) == "Keep this\n",
            "Reinstall after uninstall changed refused entries.");
    }

    private static void LinkedPlayerMods(string root)
    {
        var manager = new PackManager(root);
        var target = Path.Combine(root, "player-mods-target");
        var source = Path.Combine(target, "redirected");
        Directory.CreateDirectory(source);
        File.WriteAllText(Path.Combine(source, "mod.txt"),
            "name=Redirected mod\nfor=MW3 1.2\ncampaign=Chapter.txt\n");
        File.WriteAllText(Path.Combine(source, "Chapter.txt"), "name=Redirected chapter\nmission=c1 1\n");
        Directory.CreateDirectory(manager.EntryTicks.WriteDirectory);
        var junction = Path.Combine(manager.EntryTicks.WriteDirectory, "mods");
        CreateJunction(junction, target);
        try
        {
            var original = File.ReadAllBytes(Path.Combine(source, "mod.txt"));
            var pack = manager.InstallPack(Archive(root, "gameplay-only"));
            Assert(manager.ReadEntryTicks(pack).Any(tick =>
                tick.Entry.Id == "redirected~Chapter" && tick.IsTicked),
                "Read-only redirected player mods were not discovered/default-ticked.");
            manager.UninstallPack(pack);
            Assert(File.ReadAllBytes(Path.Combine(source, "mod.txt")).SequenceEqual(original),
                "Read-only redirected player mod was edited.");
        }
        finally { Directory.Delete(junction); }
    }

    private static void LinkedCampaigns(string root)
    {
        var manager = new PackManager(root);
        var target = Path.Combine(root, "campaigns-target");
        Directory.CreateDirectory(target);
        var sentinel = Path.Combine(target, "mods.txt");
        File.WriteAllText(sentinel, "Leave this target alone\n");
        Directory.CreateDirectory(manager.EntryTicks.WriteDirectory);
        var junction = Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns");
        CreateJunction(junction, target);
        try
        {
            var pack = manager.InstallPack(Archive(root, "gameplay-only"));
            Assert(pack.DefaultTickWarnings.Any(warning => warning.Reason.Contains("link")),
                "Linked campaigns warning was not returned after installation.");
            Assert(manager.ReadEntryTicks(pack).Count == 0,
                "A linked campaigns root offered writable entries.");
            Assert(manager.EntryWarnings.Any(warning => warning.Reason.Contains("link")),
                "Linked campaigns warning was not returned to the dialog.");
            var refused = false;
            try { manager.EntryTicks.SetTick(pack, new("ia", "Instant Action"), true); }
            catch (InvalidOperationException error) when (error.Message.Contains("link")) { refused = true; }
            Assert(refused, "Explicit toggle through linked campaigns was not visibly refused.");
            manager.UninstallPack(pack);
            Assert(manager.EntryWarnings.Any(warning => warning.Reason.Contains("link")),
                "Skipped uninstall cleanup did not return a linked campaigns warning.");
            Assert(!Directory.Exists(pack.DirectoryPath) && File.ReadAllText(sentinel) ==
                "Leave this target alone\n" && Directory.GetFileSystemEntries(target).Length == 1,
                "Linked campaigns prevented uninstall or caused target writes.");
        }
        finally { Directory.Delete(junction); }
    }

    private static void InvalidSibling(string root, string kind, bool openingDialog)
    {
        var manager = new PackManager(root);
        var archive = Archive(root, "gameplay-only");
        PackManifest pack = openingDialog ? manager.InstallPack(archive) : null;
        var sibling = Path.Combine(manager.ModsRoot, "broken-sibling");
        ZipFile.ExtractToDirectory(archive, sibling);
        var manifestPath = Path.Combine(sibling, "pack.json");
        var json = JsonNode.Parse(File.ReadAllText(manifestPath))!.AsObject();
        json["id"] = kind == "mismatched-id" ? "impostor" : "broken-sibling";
        if (kind == "bad-root") json["gameplay"]!["root"] = "../elsewhere";
        if (kind == "missing-root") json["gameplay"]!["root"] = "missing";
        File.WriteAllText(Path.Combine(sibling, "mod", "mod.txt"),
            "name=Broken sibling\ncampaign=Ghost.txt\n");
        File.WriteAllText(manifestPath, kind == "malformed" ? "{" : json.ToJsonString());
        var before = File.ReadAllBytes(manifestPath);
        if (!openingDialog) pack = manager.InstallPack(archive);
        var entries = manager.ReadEntryTicks(pack);
        Assert(manager.EntryWarnings.Any(warning => warning.EntryId == "broken-sibling"),
            "Ignored sibling was not reported to the dialog.");
        if (!openingDialog)
            Assert(pack.DefaultTickWarnings.Any(warning => warning.EntryId == "broken-sibling"),
                "Ignored sibling was not reported after install.");
        Assert(entries.Any(tick => tick.Entry.Id == "ia" && tick.IsTicked),
            "Bad sibling blocked reading the valid pack's defaults.");
        Assert(entries.All(tick => !tick.Entry.Id.StartsWith("impostor", StringComparison.Ordinal)),
            "A mismatched sibling identity supplied campaign entries.");
        Assert(File.ReadAllBytes(manifestPath).SequenceEqual(before), "Bad sibling was edited.");
    }

    private static void CampaignLabels(string root)
    {
        var manager = new PackManager(root);
        var source = Path.Combine(manager.EntryTicks.WriteDirectory, "mods", "named");
        Directory.CreateDirectory(source);
        File.WriteAllText(Path.Combine(source, "mod.txt"),
            "name=Mod fallback\ncampaign=Chapter.txt\ncampaign=Untitled.txt\ncampaign=Missing.txt\n");
        File.WriteAllText(Path.Combine(source, "Chapter.txt"), "name=Campaign heading\nmission=c1 1\n");
        File.WriteAllText(Path.Combine(source, "Untitled.txt"), "mission=c1 1\n");
        var pack = manager.InstallPack(Archive(root, "gameplay-only"));
        var entries = manager.ReadEntryTicks(pack);
        Assert(entries.Single(tick => tick.Entry.Id == "named~Chapter").Entry.Name == "Campaign heading",
            "Campaign heading did not come from its own name= line.");
        foreach (var id in new[] { "named~Untitled", "named~Missing" })
            Assert(entries.Single(tick => tick.Entry.Id == id).Entry.Name == "Mod fallback",
                "Campaign without a readable name did not fall back to the mod name.");
        Assert(File.ReadAllText(Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns", "named~Chapter",
            "mw3-campaign.txt")).StartsWith("\"Campaign heading\" (named~Chapter)", StringComparison.Ordinal),
            "Campaign marker label disagrees with the dialog.");
    }

    private static void UnreadablePlayerMod(string root)
    {
        var manager = new PackManager(root);
        var source = Path.Combine(manager.EntryTicks.WriteDirectory, "mods", "locked-source");
        Directory.CreateDirectory(source);
        var path = Path.Combine(source, "mod.txt");
        File.WriteAllText(path, "name=Locked mod\nkind=campaign\n");
        using var held = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.None);
        var pack = manager.InstallPack(Archive(root, "gameplay-only"));
        Assert(pack.DefaultTickWarnings.Any(warning => warning.EntryId == "locked-source"),
            "Unreadable discovery source did not produce an install warning.");
        Assert(manager.ReadEntryTicks(pack).Any(tick => tick.Entry.Id == "ia" && tick.IsTicked),
            "An unreadable player-mod source blocked normal entries.");
        Assert(manager.EntryWarnings.Any(warning => warning.EntryId == "locked-source"),
            "Unreadable discovery source did not produce a dialog warning.");
    }

    private static void TickPathCollision(string root, string kind)
    {
        var manager = new PackManager(root);
        var campaigns = Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns");
        var entry = Path.Combine(campaigns, "ia");
        var collision = kind switch
        {
            "campaigns-file" => campaigns,
            "entry-file" => entry,
            "marker-folder" => Path.Combine(entry, "mw3-campaign.txt"),
            _ => Path.Combine(entry, "mods.txt")
        };
        Directory.CreateDirectory(Path.GetDirectoryName(collision)!);
        if (kind.EndsWith("file", StringComparison.Ordinal)) File.WriteAllText(collision, "Keep me\n");
        else Directory.CreateDirectory(collision);
        var pack = manager.InstallPack(Archive(root, "gameplay-only"));
        Assert(pack.DefaultTickWarnings.Count > 0, "An unusable tick path was not reported.");
        var entries = manager.ReadEntryTicks(pack);
        Assert(kind == "campaigns-file" ? entries.Count == 0 :
            entries.Any(tick => tick.Entry.Id == "mp" && tick.IsTicked),
            "An unrelated tick path collision blocked usable defaults.");
        manager.UninstallPack(pack);
        Assert(kind.EndsWith("file", StringComparison.Ordinal) ?
            File.ReadAllText(collision) == "Keep me\n" : Directory.Exists(collision),
            "An unusable tick path was edited or removed.");
    }

    private static void WindowToggle(string root)
    {
        Exception failure = null;
        var thread = new Thread(() =>
        {
            PackEntriesWindow window = null;
            try
            {
                var running = false;
                var manager = new PackManager(root,
                    entryTicks: new PackEntryTicks(root, gameIsRunning: () => running));
                var pack = manager.InstallPack(Archive(root, "gameplay-only"));
                Assert(!File.Exists(TickPath(manager.EntryTicks.WriteDirectory, "mw3")),
                    "Fresh install created a tick file for the original campaign.");
                Assert(!Directory.Exists(Path.Combine(manager.EntryTicks.WriteDirectory, "mods")),
                    "Fresh install wrote a player mods directory.");
                window = new PackEntriesWindow(manager, pack);
                window.Show(); window.UpdateLayout();
                var panel = (DockPanel)window.Content;
                var entries = (StackPanel)panel.Children.OfType<ScrollViewer>().Single().Content;
                var checkbox = entries.Children.OfType<CheckBox>().Single(box => (string)box.ToolTip == "ia");
                Assert(checkbox.IsChecked == true, "Window did not display default tick.");
                checkbox.IsChecked = false;
                checkbox.RaiseEvent(new RoutedEventArgs(ButtonBase.ClickEvent));
                Assert(!manager.ReadEntryTicks(pack).Single(tick => tick.Entry.Id == "ia").IsTicked, "Window click did not persist untick.");
                running = true;
                checkbox = entries.Children.OfType<CheckBox>().Single(box => (string)box.ToolTip == "ia");
                checkbox.IsChecked = true;
                checkbox.RaiseEvent(new RoutedEventArgs(ButtonBase.ClickEvent));
                Assert(!manager.ReadEntryTicks(pack).Single(tick => tick.Entry.Id == "ia").IsTicked,
                    "Window changed ticks while the game-running probe was true.");
                var footer = panel.Children.OfType<StackPanel>().Single();
                Assert(footer.Children.OfType<TextBlock>().Single().Text.Contains("Close the game"),
                    "Window did not display the game-running refusal.");
                running = false;
                File.WriteAllText(TickPath(manager.EntryTicks.WriteDirectory, "ia"), "mod=" + pack.Id + "\n");
                footer.Children.OfType<Button>().Single().RaiseEvent(new RoutedEventArgs(ButtonBase.ClickEvent));
                Assert(entries.Children.OfType<CheckBox>().Single(box => (string)box.ToolTip == "ia").IsChecked == true,
                    "Refresh did not display a runtime-form edit made outside the window.");
                File.Delete(Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns", "ia", "mw3-campaign.txt"));
                checkbox = entries.Children.OfType<CheckBox>().Single(box => (string)box.ToolTip == "ia");
                checkbox.IsChecked = false;
                checkbox.RaiseEvent(new RoutedEventArgs(ButtonBase.ClickEvent));
                Assert(footer.Children.OfType<TextBlock>().Single().Text.Contains("game did not put there") &&
                    File.ReadAllText(TickPath(manager.EntryTicks.WriteDirectory, "ia")) == "mod=" + pack.Id + "\n",
                    "Dialog did not visibly refuse editing an unmarked nonempty entry.");

                var campaigns = Path.Combine(manager.EntryTicks.WriteDirectory, "campaigns");
                var target = Path.Combine(root, "redirected-campaigns");
                Directory.Move(campaigns, target);
                try
                {
                    CreateJunction(campaigns, target);
                    try
                    {
                        footer.Children.OfType<Button>().Single().RaiseEvent(new RoutedEventArgs(ButtonBase.ClickEvent));
                        Assert(entries.Children.Count == 0 &&
                            footer.Children.OfType<TextBlock>().Single().Text.Contains("link"),
                            "Dialog did not hide entries and explain the linked campaigns folder.");
                    }
                    finally { Directory.Delete(campaigns); }
                }
                finally { Directory.Move(target, campaigns); }
            }
            catch (Exception error) { failure = error; }
            finally { window?.Close(); }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start(); thread.Join();
        if (failure != null) throw new Exception("Entry window check failed.", failure);
        Console.WriteLine("PASS: entry window opened and Instant Action toggle invoked with temporary library.");
    }

    public static void Run()
    {
        var temporary = Directory.CreateTempSubdirectory("MW3PackTicks-");
        try
        {
            ReviewRegressions(temporary.FullName);
            foreach (var name in new[] { "lifecycle", "preservation", "failure", "window" })
                Directory.CreateDirectory(Path.Combine(temporary.FullName, name));
            Lifecycle(Path.Combine(temporary.FullName, "lifecycle"));
            PreservationAndRefusals(Path.Combine(temporary.FullName, "preservation"));
            WindowToggle(Path.Combine(temporary.FullName, "window"));
            Console.WriteLine("Pack entry tick checks passed.");
        }
        finally { temporary.Delete(recursive: true); }
    }
}
