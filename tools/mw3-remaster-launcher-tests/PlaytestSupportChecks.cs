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
            var redactedPaths = PlaytestDiagnostics.Redact(
                "Local: C:\\Users\\jcbla\\private\\Mech3.exe\nNetwork: \\\\nas01\\users\\jcbla\\Mech3.exe",
                @"C:\Users\jcbla");
            Check(!redactedPaths.Contains(@"C:\Users\jcbla", StringComparison.OrdinalIgnoreCase) &&
                !redactedPaths.Contains(@"\\nas01\users\jcbla", StringComparison.OrdinalIgnoreCase) &&
                redactedPaths.Contains("<local-path>") && redactedPaths.Contains("<network-path>"),
                "Crash-report path scrubbing exposed a local or network path");
            var nestedPath = PlaytestDiagnostics.Redact(
                @"C:\Users\jcbla\AppData\Local\Packages\Launcher\sessions\profile.json", @"C:\Users\jcbla");
            Check(nestedPath == "<local-path>", "Crash-report path scrubbing exposed the suffix after a known local root");
            var d7vkReport = JsonSerializer.SerializeToDocument(PlaytestDiagnostics.CreateCrashReport(
                new LauncherSettings { EngineMode = "d7vk", Width = 3840, D7VkResolution = "1920x1080" },
                Array.Empty<PackManifest>(), null, app, "1.2.3", 7,
                new HardwareInventoryData(
                    new[] { new ProcessorInventory("AMD", "Ryzen Example", 8, 16) },
                    new MemoryInventory(32UL * 1024 * 1024 * 1024,
                        new[] { new MemoryModuleInventory(16UL * 1024 * 1024 * 1024, "DDR5", 5600) }),
                    new[] { new GraphicsAdapterInventory("Example GPU", 12UL * 1024 * 1024 * 1024,
                        8UL * 1024 * 1024 * 1024, "1.2.3", new DateTime(2026, 1, 1)) })));
            var d7vkSettings = d7vkReport.RootElement.GetProperty("settings");
            Check(d7vkReport.RootElement.GetProperty("runtime_version").GetString() == "1.2.3" &&
                d7vkReport.RootElement.GetProperty("exit_code").GetInt32() == 7 &&
                d7vkSettings.GetProperty("D7VkResolution").GetString() == "1920x1080" &&
                !d7vkSettings.TryGetProperty("Width", out _),
                "Crash report omitted runtime/exit details or used native graphics settings for D7VK");
            var hardware = d7vkReport.RootElement.GetProperty("hardware");
            Check(hardware.GetProperty("Processors")[0].GetProperty("Model").GetString() == "Ryzen Example" &&
                hardware.GetProperty("Memory").GetProperty("Modules")[0].GetProperty("Type").GetString() == "DDR5" &&
                hardware.GetProperty("GraphicsAdapters")[0].GetProperty("DedicatedVideoMemoryBytes").GetUInt64() ==
                    12UL * 1024 * 1024 * 1024,
                "Crash report omitted CPU, memory type, or full-width VRAM inventory");
            Check(HardwareInventory.MemoryTypeName(34, null) == "DDR5" &&
                HardwareInventory.MemoryTypeName(null, null) == "Unknown",
                "RAM type codes were not described safely");
            var capturedHardware = HardwareInventory.Capture();
            Check(capturedHardware.Processors.Count > 0 && capturedHardware.Memory != null,
                "Hardware inventory did not read processor and installed-memory information");
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
            File.WriteAllText(Path.Combine(session, "native", "stderr.txt"),
                "SEH flat fault address=00000000 esp=20001000 ebp=20001080 eax=00000000 ecx=00000004 edx=00000010 esi=50000000 edi=00000000 depth=1\n" +
                "  return[0]=00412345 slot=20001004\nloader-order entry fault: authored fixture failure\n");
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
                    if (entry.FullName == "native-stderr.txt")
                        Check(text.Contains("SEH flat fault address=00000000") && text.Contains("return[0]=00412345"),
                            "Remote crash report dropped the native registers/return chain");
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
