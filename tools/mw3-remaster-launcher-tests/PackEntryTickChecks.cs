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

    private static void FailedDefaults(string root)
    {
        var manager = new PackManager(root);
        WriteEntry(manager.EntryTicks.WriteDirectory, "mp", "mod=other\n"u8.ToArray());
        var path = TickPath(manager.EntryTicks.WriteDirectory, "mp");
        var failed = false;
        using (var held = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            try { manager.InstallPack(Archive(root, "gameplay-only")); }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException) { failed = true; }
        }
        Assert(failed, "Failed default write reported success.");
        Assert(File.ReadAllText(path) == "mod=other\n", "Failed default write changed old file.");
        Assert(!Directory.Exists(Path.Combine(manager.ModsRoot, "example-gameplay")), "Failed install activated the pack.");
        Assert(!File.Exists(TickPath(manager.EntryTicks.WriteDirectory, "ia")), "Failed defaults retained an earlier tick.");
        Console.WriteLine("PASS: failed defaults restore earlier ticks and roll back pack activation.");
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
            foreach (var name in new[] { "lifecycle", "preservation", "failure", "window" })
                Directory.CreateDirectory(Path.Combine(temporary.FullName, name));
            Lifecycle(Path.Combine(temporary.FullName, "lifecycle"));
            PreservationAndRefusals(Path.Combine(temporary.FullName, "preservation"));
            FailedDefaults(Path.Combine(temporary.FullName, "failure"));
            WindowToggle(Path.Combine(temporary.FullName, "window"));
            Console.WriteLine("Pack entry tick checks passed.");
        }
        finally { temporary.Delete(recursive: true); }
    }
}
