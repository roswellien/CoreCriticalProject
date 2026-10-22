using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text.Json;
using MW3RemasterLauncher.Core;

static class PlaytestSupportChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "MW3 support checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
            var app = Path.Combine(root, "old application");
            var data = Path.Combine(root, "persistent user data");
            Directory.CreateDirectory(Path.Combine(app, "user"));
            var legacy = Path.Combine(app, "user", "settings.json");
            var original = """{"Width":1920,"Height":1080,"ActivePacks":["test.mech"],"InstantReplay":true,"ReplayVideoSettingsVersion":1}""";
            File.WriteAllText(legacy, original);
            var settings = new SettingsManager(app, data);
            Check(settings.Current.Width == 1920 && settings.Current.InstantReplay && settings.Current.ActivePacks.SequenceEqual(new[] { "test.mech" }), "Legacy choices not migrated");
            Check(File.ReadAllText(legacy) == original, "Migration modified legacy settings");
            settings.Current.Width = 2560; settings.Save();
            Check(File.ReadAllText(settings.SettingsPath + ".previous") == original, "Previous settings not retained");
            File.WriteAllText(legacy, "{broken legacy settings");
            settings = new SettingsManager(app, data);
            Check(settings.Current.Width == 2560, "An older installation replaced persistent settings");
            PackStorage.DeleteOwnedTree(app);
            settings = new SettingsManager(Path.Combine(root, "updated application"), data);
            Check(settings.Current.Width == 2560, "Application removal lost settings");
            settings.Current.Height = 1440; settings.Save();
            var broken = "{broken persistent settings";
            File.WriteAllText(settings.SettingsPath, broken);
            settings = new SettingsManager(app, data);
            Check(settings.LoadWarning != null, "Unreadable settings were silently replaced");
            Check(Directory.GetFiles(data, "settings.json.unreadable-*").Any(file => File.ReadAllText(file) == broken), "Rejected settings bytes were not preserved");
            settings.Save();
            using (JsonDocument.Parse(File.ReadAllText(settings.SettingsPath))) { }

            var runner = new GameRunner(app, data);
            try { runner.LaunchGame(new LauncherSettings { GamePath = Path.Combine(root, "missing game") }, new()); throw new Exception("Missing game accepted"); }
            catch (InvalidOperationException) { }
            Check(runner.LastLogPath != null && File.Exists(runner.LastLogPath), "Prelaunch failure has no log");
            Check(PlaytestDiagnostics.FailureSummary(runner.LastLogPath).StartsWith("ERROR:"), "Prelaunch error not explained");
            Check(LauncherPaths.LatestLaunchLog(data) == runner.LastLogPath, "Latest-session lookup failed");
            var session = Path.GetDirectoryName(runner.LastLogPath)!;
            Directory.CreateDirectory(Path.Combine(session, "native"));
            settings.Current.GamePath = Path.Combine(root, "private game directory");
            var privateText = "ERROR: Cannot open " + settings.Current.GamePath + "\\file.bin\n";
            File.WriteAllText(runner.LastLogPath!, new string('x', PlaytestDiagnostics.MaxLogBytes * 3) + "\n" + privateText);
            File.WriteAllText(Path.Combine(session, "native", "stderr.txt"), "loader-order entry fault: authored fixture failure\n");
            File.WriteAllText(Path.Combine(session, "native", "stdout.txt"), "fixture output\n");
            File.WriteAllText(Path.Combine(session, "native", "original.exe"), "DO_NOT_EXPORT_GAME_BYTES");
            File.WriteAllText(Path.Combine(session, "profile.json"), "DO_NOT_EXPORT_PRIVATE_PROFILE");
            Check(PlaytestDiagnostics.ReadTail(runner.LastLogPath!).Length <= PlaytestDiagnostics.MaxLogBytes, "Log tail is unbounded");
            Check(PlaytestDiagnostics.FailureSummary(runner.LastLogPath).Contains("authored fixture failure"), "Native error not preferred");
            var report = Path.Combine(root, "report.zip");
            PlaytestDiagnostics.Export(report, settings.Current,
                new[] { new PackManifest { Id = "test.mech", Version = "1.2.3", DirectoryPath = root } }, runner.LastLogPath, app);
            using (var zip = ZipFile.OpenRead(report))
            {
                Check(zip.Entries.Select(entry => entry.FullName).Order().SequenceEqual(new[] { "launcher.log", "native-stderr.txt", "native-stdout.txt", "report.json" }), "Report exported nonallowlisted content");
                foreach (var entry in zip.Entries)
                {
                    using var reader = new StreamReader(entry.Open());
                    var text = reader.ReadToEnd();
                    Check(!text.Contains(root) && !text.Contains("DO_NOT_EXPORT"), "Report exposed private paths/content");
                    if (entry.FullName == "report.json")
                    {
                        using var document = JsonDocument.Parse(text);
                        Check(!document.RootElement.GetProperty("settings").TryGetProperty("GamePath", out _), "Report included game path");
                    }
                }
            }
            using var quick = Process.Start(new ProcessStartInfo("cmd.exe", "/d /c exit 7") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })!;
            quick.WaitForExit();
            Check(GameRunner.WaitForCompletionAsync(quick).GetAwaiter().GetResult() == 7, "Already-exited launch was missed");
            Console.WriteLine("Settings migration/recovery, update preservation, bounded/redacted diagnostics and fast-exit checks passed.");
        }
        finally { PackStorage.DeleteOwnedTree(root); }
    }
}
