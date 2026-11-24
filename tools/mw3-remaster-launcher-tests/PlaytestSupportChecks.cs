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
            var privateNetworkRoot = @"\\nas01\users\Jane Doe\private-game";
            var redactedNetworkPath = PlaytestDiagnostics.Redact(
                "Network: " + privateNetworkRoot + @"\file.bin", privateNetworkRoot);
            Check(redactedNetworkPath == "Network: <network-path>" &&
                !redactedNetworkPath.Contains("Jane Doe", StringComparison.Ordinal) &&
                !redactedNetworkPath.Contains("private-game", StringComparison.Ordinal),
                "Crash-report path scrubbing exposed a spaced UNC path suffix");
            var nestedPath = PlaytestDiagnostics.Redact(
                @"C:\Users\jcbla\AppData\Local\Packages\Launcher\sessions\profile.json", @"C:\Users\jcbla");
            Check(nestedPath == "<local-path>", "Crash-report path scrubbing exposed the suffix after a known local root");
            var crashReport = PlaytestDiagnostics.CreateCrashReport(
                new LauncherSettings { EngineMode = "d7vk", Width = 3840, D7VkResolution = "1920x1080" },
                Array.Empty<PackManifest>(), null, app, "1.2.3", 7,
                new HardwareInventoryData(
                    new[] { new ProcessorInventory("AMD", "Ryzen Example", 8, 16) },
                    new MemoryInventory(32UL * 1024 * 1024 * 1024,
                        new[] { new MemoryModuleInventory(16UL * 1024 * 1024 * 1024, "DDR5", 5600) }),
                    new[] { new GraphicsAdapterInventory("Example GPU", 12UL * 1024 * 1024 * 1024,
                        8UL * 1024 * 1024 * 1024, "1.2.3", new DateTime(2026, 1, 1)) }));
            var d7vkReport = JsonSerializer.SerializeToDocument(crashReport);
            var d7vkSettings = d7vkReport.RootElement.GetProperty("settings");
            Check(d7vkReport.RootElement.GetProperty("runtime_version").GetString() == "1.2.3" &&
                d7vkReport.RootElement.GetProperty("exit_code").GetInt32() == 7 &&
                d7vkSettings.GetProperty("D7VkResolution").GetString() == "1920x1080" &&
                !d7vkSettings.TryGetProperty("Width", out _),
                "Crash report omitted runtime/exit details or used native graphics settings for D7VK");
            var webHardware = JsonSerializer.SerializeToDocument(crashReport,
                new JsonSerializerOptions(JsonSerializerDefaults.Web)).RootElement.GetProperty("hardware");
            Check(webHardware.TryGetProperty("processors", out var webProcessors) &&
                webProcessors[0].GetProperty("model").GetString() == "Ryzen Example" &&
                webHardware.GetProperty("memory").GetProperty("modules")[0].GetProperty("type").GetString() == "DDR5" &&
                webHardware.GetProperty("graphicsAdapters")[0]
                    .GetProperty("dedicatedVideoMemoryBytes").GetUInt64() == 12UL * 1024 * 1024 * 1024,
                "Crash report's HTTP JSON format did not serialize hardware with camelCase fields");
            var hardware = d7vkReport.RootElement.GetProperty("hardware");
            Check(hardware.GetProperty("Processors")[0].GetProperty("Model").GetString() == "Ryzen Example" &&
                hardware.GetProperty("Memory").GetProperty("Modules")[0].GetProperty("Type").GetString() == "DDR5" &&
                hardware.GetProperty("GraphicsAdapters")[0].GetProperty("DedicatedVideoMemoryBytes").GetUInt64() ==
                    12UL * 1024 * 1024 * 1024,
                "Crash report omitted CPU, memory type, or full-width VRAM inventory");
            Check(HardwareInventory.MemoryTypeName(18, null) == "DDR" &&
                HardwareInventory.MemoryTypeName(19, null) == "DDR2" &&
                HardwareInventory.MemoryTypeName(20, null) == "DDR2 FB-DIMM" &&
                HardwareInventory.MemoryTypeName(27, null) == "LPDDR" &&
                HardwareInventory.MemoryTypeName(30, null) == "LPDDR4" &&
                HardwareInventory.MemoryTypeName(35, null) == "LPDDR5" &&
                HardwareInventory.MemoryTypeName(null, 20) == "DDR" &&
                HardwareInventory.MemoryTypeName(null, 27) == "LPDDR3" &&
                HardwareInventory.MemoryTypeName(null, 30) == "LPDDR5" &&
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

            // Windows 10 vs 11 vs Server OS edition and public launcher version checks
            Check(PlaytestDiagnostics.FormatWindowsDescription(22631, 4317, "Client", "23H2") == "Windows 11 23H2 (OS Build 10.0.22631.4317)",
                "Windows 11 client build was not distinguished from Windows 10");
            Check(PlaytestDiagnostics.FormatWindowsDescription(19045, 5011, "Client", "22H2") == "Windows 10 22H2 (OS Build 10.0.19045.5011)",
                "Windows 10 client build was not formatted accurately");
            Check(PlaytestDiagnostics.FormatWindowsDescription(20348, 2520, "Server", "21H2") == "Windows Server 2022 21H2 (OS Build 10.0.20348.2520)",
                "Windows Server installation type was not distinguished from Windows client");
            var publicVersion = PlaytestDiagnostics.LauncherVersionString();
            Check(!string.IsNullOrWhiteSpace(publicVersion) && !publicVersion.Contains('+') && !publicVersion.EndsWith(".0", StringComparison.Ordinal),
                "Launcher version string did not drop build metadata or trailing .0 assembly revision: " + publicVersion);
            Check(PlaytestDiagnostics.FormatExitCode(-1073741819) == "-1073741819 (0xC0000005)" &&
                PlaytestDiagnostics.FormatExitCode(7) == "7 (0x00000007)",
                "Exit code formatter did not include signed decimal and 8-digit hexadecimal status");

            // Redaction of native crash paths while preserving fault module, hex offset and access metadata
            var faultLineWithPath = PlaytestDiagnostics.Redact(
                @"HOST EXCEPTION c0000005 at C:\Games\Core Critical\NativePreview\bin\mw3.exe +0x45678 (access 0 address 0000000000000018)" + "\n" +
                @"HOST EXCEPTION c0000005 at \\nas01\share\NativePreview\bin\mw3.exe+0x45678" + "\n" +
                @"mw3: minidump: C:\Users\Jane Doe\crash.dmp" + "\n" +
                @"Regular diagnostic: C:\Games\Core Critical\private-name.exe +0x1234",
                @"C:\Users\Jane Doe", @"C:\Games\Core Critical");
            Check(!faultLineWithPath.Contains("Jane Doe", StringComparison.OrdinalIgnoreCase) &&
                !faultLineWithPath.Contains("Core Critical", StringComparison.OrdinalIgnoreCase) &&
                !faultLineWithPath.Contains("nas01", StringComparison.OrdinalIgnoreCase) &&
                !faultLineWithPath.Contains("private-name", StringComparison.OrdinalIgnoreCase) &&
                faultLineWithPath.Contains("<local-path>/mw3.exe +0x45678 (access 0 address 0000000000000018)", StringComparison.Ordinal) &&
                faultLineWithPath.Contains("<network-path>/mw3.exe+0x45678", StringComparison.Ordinal) &&
                faultLineWithPath.Contains("mw3: minidump: <local-path>", StringComparison.Ordinal),
                "Path redaction discarded native fault module/offset/access suffix or leaked user path");

            // Stale mw3.log vs current mw3.log and appended crash.txt collection checks
            var profileDir = Path.Combine(root, "mw3-re-profile");
            Directory.CreateDirectory(profileDir);
            var staleLogPath = Path.Combine(profileDir, "mw3.log");
            var crashTxtPath = Path.Combine(profileDir, "crash.txt");
            var dumpPath = Path.Combine(profileDir, "crash.dmp");
            File.WriteAllText(staleLogPath, "mw3: fatal error from stale previous run\n");
            var staleTimestamp = DateTime.UtcNow;
            File.SetCreationTimeUtc(staleLogPath, staleTimestamp);
            File.SetLastWriteTimeUtc(staleLogPath, staleTimestamp);
            File.WriteAllText(crashTxtPath, "mw3: crashed: exception 0xc0000094 at 0x00401000 module base 0x00400000 RVA 0x1000\n");
            File.WriteAllText(dumpPath, "DO_NOT_COLLECT_MINIDUMP_BYTES");

            var staleBaseline = PlaytestDiagnostics.CaptureNativeBaseline(profileDir);
            var staleSessionDir = Path.Combine(root, "session-stale");
            Directory.CreateDirectory(staleSessionDir);
            var staleLauncherLog = Path.Combine(staleSessionDir, "mw3-re.log");
            File.WriteAllText(staleLauncherLog, "MW3-RE, launcher " + publicVersion + "\nStartup: Checking game files... [launcher elapsed 12 ms]\n");
            PlaytestDiagnostics.CollectNativeSessionArtifacts(staleBaseline, staleSessionDir);
            Check(!File.Exists(Path.Combine(staleSessionDir, "native", "mw3.log")) &&
                !File.Exists(Path.Combine(staleSessionDir, "native", "crash.txt")) &&
                !File.Exists(Path.Combine(staleSessionDir, "native", "crash.dmp")),
                "Stale mw3.log, unappended crash.txt, or minidump was collected into a new session");
            Check(PlaytestDiagnostics.FailureSummary(staleLauncherLog) == "No specific failure was recorded.",
                "Routine startup output without specific failure evidence did not produce the exact fallback summary");

            // Fresh mw3.log and newly appended crash.txt in active session
            var activeBaseline = PlaytestDiagnostics.CaptureNativeBaseline(profileDir);
            File.WriteAllText(staleLogPath,
                "mw3: crash details, if any, are written to " + crashTxtPath + "\n" +
                "mw3: window 1920x1080 on Vulkan device\n" +
                "mw3: could not load mission archive from " + settings.Current.GamePath + "\\zbd\\missions.zbd\n");
            File.SetLastWriteTimeUtc(staleLogPath, DateTime.UtcNow.AddSeconds(2));
            File.AppendAllText(crashTxtPath,
                "mw3: crashed: exception 0xc0000005 at 0x00007ff600451234 module base 0x00007ff600400000 RVA 0x51234\n" +
                "mw3: access violation: read (0) target 0x0000000000000000\n" +
                "mw3: registers: RIP=0x00007ff600451234 RAX=0x0000000000000000 RBX=0x0000000000000001 RCX=0x0000000000000002 RDX=0x0000000000000003\n" +
                "mw3: minidump: " + dumpPath + "\n");

            var activeSessionDir = Path.Combine(root, "session-active");
            Directory.CreateDirectory(activeSessionDir);
            var activeLauncherLog = Path.Combine(activeSessionDir, "mw3-re.log");
            File.WriteAllText(activeLauncherLog, "MW3-RE, launcher " + publicVersion + "\nStarting MW3-RE: 1920x1080\n");
            PlaytestDiagnostics.CollectNativeSessionArtifacts(activeBaseline, activeSessionDir);

            Check(File.Exists(Path.Combine(activeSessionDir, "native", "crash.txt")) &&
                File.Exists(Path.Combine(activeSessionDir, "native", "mw3.log")) &&
                !File.Exists(Path.Combine(activeSessionDir, "native", "crash.dmp")),
                "Active session did not collect crash.txt and mw3.log or collected a dump");
            var collectedCrash = File.ReadAllText(Path.Combine(activeSessionDir, "native", "crash.txt"));
            Check(!collectedCrash.Contains("0xc0000094", StringComparison.Ordinal) &&
                collectedCrash.Contains("0xc0000005", StringComparison.Ordinal) &&
                collectedCrash.Contains("RVA 0x51234", StringComparison.Ordinal),
                "Appended crash.txt capture included prior crash bytes or lost new exception details");
            var activeSummary = PlaytestDiagnostics.FailureSummary(activeLauncherLog);
            Check(activeSummary == "mw3: crashed: exception 0xc0000005 at 0x00007ff600451234 module base 0x00007ff600400000 RVA 0x51234 (access violation: read (0) target 0x0000000000000000)",
                "Native crash fault summary was not preferred over routine output: " + activeSummary);

            var activeCrashReport = PlaytestDiagnostics.CreateCrashReport(
                settings.Current,
                new[] { new PackManifest { Id = "test.mech", Version = "1.2.3", SchemaVersion = 2, IsEnabled = true, Priority = 1, DirectoryPath = root } },
                activeLauncherLog,
                app,
                "mw3-re-2026.11 (abcdef123456)",
                unchecked((int)0xC0000005));
            var activeReportBytes = JsonSerializer.SerializeToUtf8Bytes(activeCrashReport, new JsonSerializerOptions(JsonSerializerDefaults.Web));
            Check(activeReportBytes.Length <= PlaytestDiagnostics.MaxRequestBytes, "Serialized crash report exceeded 256 KiB request cap");
            using (var activeDoc = JsonDocument.Parse(activeReportBytes))
            {
                var rootEl = activeDoc.RootElement;
                Check(rootEl.GetProperty("exit_code").GetInt32() == unchecked((int)0xC0000005) &&
                    rootEl.GetProperty("runtime_version").GetString() == "mw3-re-2026.11 (abcdef123456)" &&
                    rootEl.GetProperty("launcher_version").GetString() == publicVersion,
                    "Active crash report did not preserve signed exit code, runtime build ID or launcher version");
                var logsEl = rootEl.GetProperty("logs");
                Check(logsEl.TryGetProperty("native_crash", out var nativeCrashLog) &&
                    nativeCrashLog.GetString()!.Contains("RVA 0x51234", StringComparison.Ordinal) &&
                    !nativeCrashLog.GetString()!.Contains("0xc0000094", StringComparison.Ordinal) &&
                    logsEl.TryGetProperty("native_run", out var nativeRunLog) &&
                    nativeRunLog.GetString()!.Contains("window 1920x1080 on Vulkan device", StringComparison.Ordinal) &&
                    !nativeRunLog.GetString()!.Contains(root, StringComparison.OrdinalIgnoreCase),
                    "Active crash report logs omitted native_crash/native_run or leaked private paths");
            }

            var activeZip = Path.Combine(root, "active-report.zip");
            PlaytestDiagnostics.Export(activeZip, settings.Current,
                new[] { new PackManifest { Id = "test.mech", Version = "1.2.3", DirectoryPath = root } },
                activeLauncherLog, app, runtimeVersion: "mw3-re-2026.11 (abcdef123456)", exitCode: unchecked((int)0xC0000005));
            using (var zip = ZipFile.OpenRead(activeZip))
            {
                Check(zip.Entries.Select(entry => entry.FullName).Order().SequenceEqual(
                    new[] { "launcher.log", "native-crash.txt", "native-mw3.log", "report.json" }),
                    "Active native export ZIP did not include the expected allowlisted log files");
                foreach (var entry in zip.Entries)
                {
                    using var reader = new StreamReader(entry.Open());
                    var text = reader.ReadToEnd();
                    Check(!text.Contains(root, StringComparison.OrdinalIgnoreCase) &&
                        !text.Contains("DO_NOT_COLLECT_MINIDUMP_BYTES", StringComparison.Ordinal),
                        "Active native export ZIP leaked private path or dump content in " + entry.FullName);
                }
            }
            Console.WriteLine("Settings migration/recovery, update preservation, bounded/redacted diagnostics and fast-exit checks passed.");
        }
        finally { PackStorage.DeleteOwnedTree(root); }
    }
}
