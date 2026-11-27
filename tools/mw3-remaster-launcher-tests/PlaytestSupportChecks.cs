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
            var quotedStartError = PlaytestDiagnostics.Redact(
                "ERROR: An error occurred trying to start process 'C:\\Games\\Core Critical\\Launcher\\NativePreview\\bin\\mw3.exe' with working directory 'C:\\Games\\Core Critical\\Launcher\\NativePreview\\bin'. An Application Control policy has blocked this file.",
                @"C:\Games\Core Critical\Launcher");
            Check(quotedStartError ==
                    "ERROR: An error occurred trying to start process '<local-path>' with working directory '<local-path>'. An Application Control policy has blocked this file." &&
                !quotedStartError.Contains("Core Critical", StringComparison.OrdinalIgnoreCase),
                "Single-quoted Windows paths in launch errors truncated trailing details or leaked paths: " + quotedStartError);
            var apostropheQuotedError = PlaytestDiagnostics.Redact(
                "ERROR: Failed to start 'C:\\Users\\O'Connor\\Core Critical\\mw3.exe' with working directory 'C:\\Users\\O'Connor\\Core Critical'. Access is denied.",
                @"C:\Users\O'Connor");
            Check(apostropheQuotedError ==
                    "ERROR: Failed to start '<local-path>' with working directory '<local-path>'. Access is denied." &&
                !apostropheQuotedError.Contains("O'Connor", StringComparison.OrdinalIgnoreCase) &&
                !apostropheQuotedError.Contains("Core Critical", StringComparison.OrdinalIgnoreCase),
                "Single-quoted path containing an apostrophe leaked or truncated trailing error details: " + apostropheQuotedError);
            var quotedUncError = PlaytestDiagnostics.Redact(
                "'\\\\nas01\\users\\Jane Doe\\mw3.exe' was blocked by policy.",
                @"\\nas01\users\Jane Doe");
            Check(quotedUncError == "'<network-path>' was blocked by policy." &&
                !quotedUncError.Contains("nas01", StringComparison.OrdinalIgnoreCase) &&
                !quotedUncError.Contains("Jane Doe", StringComparison.OrdinalIgnoreCase),
                "Single-quoted UNC path truncated trailing details or leaked host/user: " + quotedUncError);

            var redactionCases = new (string Name, string Input, string[] Roots, string Expected)[]
            {
                (
                    "Multi-line single-quoted local and UNC paths at line starts",
                    "Launcher log:\n'C:\\Games\\Core Critical\\mw3.exe' was blocked.\r\n'\\\\nas01\\share\\Jane Doe\\mw3.exe' was blocked.",
                    new[] { @"C:\Games\Core Critical", @"\\nas01\share\Jane Doe" },
                    "Launcher log:\n'<local-path>' was blocked.\r\n'<network-path>' was blocked."
                ),
                (
                    "Apostrophe followed by space in path and directory with matching privateRoot",
                    "ERROR: Failed to start 'C:\\Users\\James' Folder\\mw3.exe' with working directory 'C:\\Users\\James' Folder'. Access is denied.",
                    new[] { @"C:\Users\James' Folder" },
                    "ERROR: Failed to start '<local-path>' with working directory '<local-path>'. Access is denied."
                ),
                (
                    "Apostrophe followed by space in path without privateRoots",
                    "ERROR: Failed to start 'D:\\Games\\Players' Choice\\Bob's Mods\\mw3.exe' with working directory 'D:\\Games\\Players' Choice'. Access is denied.",
                    Array.Empty<string>(),
                    "ERROR: Failed to start '<local-path>' with working directory '<local-path>'. Access is denied."
                ),
                (
                    "Apostrophe followed by punctuation inside filename",
                    "ERROR: Failed to open 'C:\\Users\\v1'.txt' because locked.",
                    Array.Empty<string>(),
                    "ERROR: Failed to open '<local-path>' because locked."
                ),
                (
                    "Single-quoted UNC path with apostrophe and space",
                    "'\\\\nas01\\users\\Players' Choice\\mw3.exe' in '\\\\nas01\\users\\Players' Choice' was blocked.",
                    Array.Empty<string>(),
                    "'<network-path>' in '<network-path>' was blocked."
                ),
                (
                    "Single-quoted path followed by contractions, slashes in prose, and other single-quoted strings",
                    "ERROR: 'C:\\Games\\a.exe' can't start; 'C:\\Games\\b.exe' failed/errored because users' policy ('reason') blocked it.",
                    Array.Empty<string>(),
                    "ERROR: '<local-path>' can't start; '<local-path>' failed/errored because users' policy ('reason') blocked it."
                ),
                (
                    "Single-quoted path followed by colon and possessive name",
                    "ERROR: 'C:\\Games\\a.exe' failed: James' policy blocked it.",
                    Array.Empty<string>(),
                    "ERROR: '<local-path>' failed: James' policy blocked it."
                ),
                (
                    "Delimiters around single-quoted paths",
                    "('C:\\a\\1.exe') ['C:\\b\\2.exe','C:\\c\\3.exe'] path='C:\\d\\4.exe',dir='\\\\nas01\\s'; {\"exe\":\"'C:\\e\\5.exe'\"} \"'C:\\f\\6.exe' blocked\" `'C:\\g\\7.exe'`",
                    Array.Empty<string>(),
                    "('<local-path>') ['<local-path>','<local-path>'] path='<local-path>',dir='<network-path>'; {\"exe\":\"'<local-path>'\"} \"'<local-path>' blocked\" `'<local-path>'`"
                ),
                (
                    "Unclosed single-quoted paths do not leak",
                    "ERROR: Could not open 'C:\\Users\\Alice\\secret.txt\nUnclosed 'C:\\Users\\Alice\\secret and \"quoted\" 'C:\\Users\\Bob\\other.exe' failed.",
                    new[] { @"C:\Users\Alice" },
                    "ERROR: Could not open '<local-path>\nUnclosed '<local-path>\"quoted\" '<local-path>' failed."
                ),
                (
                    "Double-quoted path containing apostrophe and space",
                    "\"C:\\Users\\James' Folder\\mw3.exe\" was blocked.",
                    new[] { @"C:\Users\James' Folder" },
                    "\"<local-path>\" was blocked."
                ),
                (
                    "Overlapping privateRoots with multi-word apostrophe root and forward slashes",
                    "Starting 'C:/Users/James' New Folder/Sub/mw3.exe' in 'C:\\Users\\James' New Folder'.",
                    new[] { @"C:\Users\James", @"C:\Users\James' New Folder" },
                    "Starting '<local-path>' in '<local-path>'."
                ),
                (
                    "HOST EXCEPTION line combined with single-quoted Process.Start error",
                    "HOST EXCEPTION c0000005 at C:\\Games\\Core Critical\\mw3.exe +0x45678 (access 0 address 0000000000000018)\nERROR: Process 'C:\\Games\\Core Critical\\mw3.exe' blocked.",
                    new[] { @"C:\Games\Core Critical" },
                    "HOST EXCEPTION c0000005 at <local-path>/mw3.exe +0x45678 (access 0 address 0000000000000018)\nERROR: Process '<local-path>' blocked."
                ),
                (
                    "Trailing-separator privateRoots match bare and nested single-quoted apostrophe paths",
                    "Starting 'D:\\Users\\James' New Folder\\mw3.exe' in 'D:\\Users\\James' New Folder' and '\\\\nas01\\share\\James' New Folder'.",
                    new[] { @"D:\Users\James' New Folder\", @"\\nas01\share\James' New Folder\" },
                    "Starting '<local-path>' in '<local-path>' and '<network-path>'."
                ),
                (
                    "Mixed-separator single-quoted paths with apostrophe and space",
                    "Failed 'D:\\Users\\Players' Choice/mw3.exe' in 'D:\\Users\\Players' Choice/NativePreview/bin' and 'D:/Users/Players' Choice\\bin'.",
                    Array.Empty<string>(),
                    "Failed '<local-path>' in '<local-path>' and '<local-path>'."
                ),
                (
                    "Prose slashes before possessive plurals are not swallowed",
                    "ERROR: 'C:\\Games\\b.exe' read/users' policy and 'C:\\Games\\c.exe' read/write/execute because users' policy blocked it.",
                    Array.Empty<string>(),
                    "ERROR: '<local-path>' read/users' policy and '<local-path>' read/write/execute because users' policy blocked it."
                )
            };
            foreach (var (name, input, roots, expected) in redactionCases)
            {
                var actual = PlaytestDiagnostics.Redact(input, roots);
                Check(actual == expected, $"Redaction case '{name}' failed.\nExpected: {expected}\nActual:   {actual}");
            }
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
            Check(PlaytestDiagnostics.FailureSummary(runner.LastLogPath, PlaytestDiagnostics.ApplicationHangExitCode)
                .Contains("authored fixture failure"), "Hang text replaced a native error line");
            var report = Path.Combine(root, "report.zip");
            ReportExport.Export(report, settings.Current,
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
                        Check(document.RootElement.GetProperty("exit_code").ValueKind == JsonValueKind.Null,
                            "Export without a matching session reported an exit code");
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

            // Shipped build ids are "mw3-re-" plus a 64-character hash; the commit must survive.
            const string shippedBuildId = "mw3-re-25ba696081f05063729121e27b7c1f5062fec13a08e5db7ba2d14697d86607a1";
            const string sourceCommit = "9b519d05c23b8f5fc417b4d889e9240ef0d11589";
            var shippedVersion = PlaytestDiagnostics.FormatRuntimeVersion(shippedBuildId, sourceCommit);
            Check(shippedVersion == "mw3-re-25ba696081f05063729121e27b7c1f5062fec13a08e5db7ba2d14697d8 (9b519d05c23b)" &&
                shippedVersion.Length == 80,
                "Runtime version dropped the source commit for a shipped-length build id: " + shippedVersion);
            Check(PlaytestDiagnostics.FormatRuntimeVersion("mw3-re-test", sourceCommit) == "mw3-re-test (9b519d05c23b)" &&
                PlaytestDiagnostics.FormatRuntimeVersion("mw3-re-test", null) == "mw3-re-test" &&
                PlaytestDiagnostics.FormatRuntimeVersion("mw3-re-test", "abc") == "mw3-re-test",
                "Runtime version changed for a short build id or a missing commit");

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

            // A hang that Windows ends with 0xCFFFFFFF usually leaves no error line.
            var hang = PlaytestDiagnostics.ApplicationHangExitCode;
            Check(hang == -805306369 &&
                PlaytestDiagnostics.FailureSummary(staleLauncherLog, hang) == PlaytestDiagnostics.ApplicationHangSummary &&
                PlaytestDiagnostics.FailureSummary(null, hang) == PlaytestDiagnostics.ApplicationHangSummary &&
                PlaytestDiagnostics.FailureSummary(staleLauncherLog, 7) == PlaytestDiagnostics.GenericFailureSummary,
                "Hang exit code without error evidence was not explained, or another exit code was");
            var hangErrorSessionDir = Path.Combine(root, "session-hang-error");
            Directory.CreateDirectory(hangErrorSessionDir);
            var hangErrorLog = Path.Combine(hangErrorSessionDir, "mw3-re.log");
            File.WriteAllText(hangErrorLog, "Startup: Checking game files...\nERROR: authored hang fixture failure\n");
            Check(PlaytestDiagnostics.FailureSummary(hangErrorLog, hang).Contains("authored hang fixture failure"),
                "Hang text replaced a specific error line");

            // The runtime's exit-on-error lines (runtime/mw3-re/src/frontend/sdl/mw3_main.cpp)
            // name the failure; they beat generic error lines, and native faults beat them.
            const string gameLoopLine =
                "mw3: game loop exception (class std::runtime_error): Local lights: invalid projection";
            const string nativeFaultLine = "mw3: crashed: exception 0xc0000005 at 0x00401000";
            var summaryCase = 0;
            string SummaryFor(string launchLog, string nativeStderr = null)
            {
                var sessionDir = Path.Combine(root, "session-game-loop-" + summaryCase++);
                Directory.CreateDirectory(Path.Combine(sessionDir, "native"));
                var logPath = Path.Combine(sessionDir, "mw3-re.log");
                File.WriteAllText(logPath, launchLog);
                if (nativeStderr != null)
                    File.WriteAllText(Path.Combine(sessionDir, "native", "stderr.txt"), nativeStderr);
                return PlaytestDiagnostics.FailureSummary(logPath);
            }
            Check(SummaryFor("Startup: Checking game files...\n" + gameLoopLine + "\n") == gameLoopLine,
                "Game loop exception line was not the failure summary");
            Check(SummaryFor("ERROR: authored earlier error\n" + gameLoopLine + "\n") == gameLoopLine,
                "Earlier ERROR line beat the game loop exception line");
            Check(SummaryFor("mw3: rendering failed: authored render failure\n") ==
                "mw3: rendering failed: authored render failure",
                "Rendering failed line was not the failure summary");
            Check(SummaryFor("mw3: game loop exception (non-standard C++ exception)\n") ==
                "mw3: game loop exception (non-standard C++ exception)",
                "Non-standard game loop exception line was not the failure summary");
            Check(SummaryFor("mw3: game loop failed with an empty exception\n") ==
                "mw3: game loop failed with an empty exception",
                "Empty game loop exception line was not the failure summary");
            Check(SummaryFor(gameLoopLine + "\nmw3: rendering failed: authored render failure\n") ==
                gameLoopLine,
                "Game loop exception line did not win over a rendering failed line");
            Check(SummaryFor(gameLoopLine + "\n", "mw3: rendering failed: authored render failure\n") ==
                gameLoopLine,
                "Rendering failed line in stderr won over a game loop line in the launch log");
            Check(SummaryFor(gameLoopLine + " [launcher elapsed 1234 ms]\n") == gameLoopLine,
                "Launcher elapsed suffix was kept on the game loop summary");
            Check(SummaryFor(gameLoopLine + "\n", "ERROR: authored stderr error\n") == gameLoopLine,
                "ERROR line in stderr won over a game loop line in the launch log");
            Check(SummaryFor(nativeFaultLine + "\n", gameLoopLine + "\n") == nativeFaultLine,
                "Game loop line in stderr beat a native fault in the launch log");
            Check(SummaryFor(nativeFaultLine + "\n", "ERROR: authored stderr error\n") ==
                nativeFaultLine,
                "Generic stderr line beat a native fault in the launch log");
            using (var hangReport = JsonSerializer.SerializeToDocument(PlaytestDiagnostics.CreateCrashReport(
                settings.Current, Array.Empty<PackManifest>(), staleLauncherLog, app, "1.2.3", hang)))
            {
                Check(hangReport.RootElement.GetProperty("exit_code").GetInt32() == hang &&
                    hangReport.RootElement.GetProperty("failure_summary").GetString() == PlaytestDiagnostics.ApplicationHangSummary,
                    "Sent crash report did not explain the hang exit code");
            }
            var hangExport = Path.Combine(root, "hang-report.zip");
            ReportExport.Export(hangExport, settings.Current, Array.Empty<PackManifest>(), staleLauncherLog, app,
                exitCode: hang);
            var d7vkExport = Path.Combine(root, "d7vk-report.zip");
            ReportExport.Export(d7vkExport,
                new LauncherSettings { EngineMode = "d7vk", Width = 3840, D7VkResolution = "1920x1080" },
                Array.Empty<PackManifest>(), staleLauncherLog, app);
            JsonDocument ReadExportedReport(string zipPath)
            {
                using var zip = ZipFile.OpenRead(zipPath);
                using var reader = new StreamReader(zip.GetEntry("report.json")!.Open());
                return JsonDocument.Parse(reader.ReadToEnd());
            }
            using (var exported = ReadExportedReport(hangExport))
            {
                Check(exported.RootElement.GetProperty("exit_code").GetInt32() == hang &&
                    exported.RootElement.GetProperty("failure_summary").GetString() == PlaytestDiagnostics.ApplicationHangSummary,
                    "Exported report dropped the session exit code or the hang explanation");
            }
            using (var exported = ReadExportedReport(d7vkExport))
            {
                var exportedSettings = exported.RootElement.GetProperty("settings");
                Check(exportedSettings.GetProperty("D7VkResolution").GetString() == "1920x1080" &&
                    !exportedSettings.TryGetProperty("Width", out _),
                    "Exported D7VK report used native graphics settings");
            }

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
            ReportExport.Export(activeZip, settings.Current,
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
            ReportContentChecks(root, settings.Current, app, Check);
            Console.WriteLine("Settings migration/recovery, update preservation, bounded/redacted diagnostics and fast-exit checks passed.");
        }
        finally { PackStorage.DeleteOwnedTree(root); }
    }

    /// <summary>
    /// Whole-log collection and export, the 19 MB export cap, upload order, the setup header
    /// and clean-exit problems (issue 521). Authored fixtures only; large logs are written into
    /// the temporary root when the check runs and deleted with it.
    /// </summary>
    private static void ReportContentChecks(string root, LauncherSettings settings, string app,
        Action<bool, string> Check)
    {
        static string NewSession(string root, string name, string launcherLog)
        {
            var session = Path.Combine(root, name);
            Directory.CreateDirectory(Path.Combine(session, "native"));
            var log = Path.Combine(session, "mw3-re.log");
            File.WriteAllText(log, launcherLog);
            return log;
        }
        static string ReadEntry(ZipArchive zip, string name)
        {
            using var reader = new StreamReader(zip.GetEntry(name)!.Open());
            return reader.ReadToEnd();
        }
        static string Lines(string prefix, int count) =>
            string.Concat(Enumerable.Range(0, count).Select(index => $"{prefix} line {index:D7}\n"));

        // A clean-exit session copies mw3.log, mw3.old.log and mw3-problems.log whole, and a
        // problems log left over from an earlier run is skipped.
        var profile = Path.Combine(root, "profile-521");
        Directory.CreateDirectory(profile);
        var gameLog = Path.Combine(profile, PlaytestDiagnostics.NativeRunFileName);
        var oldGameLog = Path.Combine(profile, PlaytestDiagnostics.NativeOldRunFileName);
        var problemsLog = Path.Combine(profile, PlaytestDiagnostics.NativeProblemsFileName);
        File.WriteAllText(problemsLog, "[1.0] E stale problem from an earlier run\n");
        var staleProblemsBaseline = PlaytestDiagnostics.CaptureNativeBaseline(profile);
        var wholeGameLog = Lines("mw3: session", 200_000); // About 5 MB, far past the 64 KB upload cut.
        File.WriteAllText(gameLog, wholeGameLog);
        File.WriteAllText(oldGameLog, "mw3: previous session\n");
        var staleProblemsSession = Path.GetDirectoryName(NewSession(root, "session-521-stale-problems", "launcher\n"))!;
        PlaytestDiagnostics.CollectNativeSessionArtifacts(staleProblemsBaseline, staleProblemsSession);
        Check(File.ReadAllText(Path.Combine(staleProblemsSession, "native", "mw3.log")) == wholeGameLog &&
            File.Exists(Path.Combine(staleProblemsSession, "native", "mw3.old.log")) &&
            !File.Exists(Path.Combine(staleProblemsSession, "native", "mw3-problems.log")),
            "A session did not copy the whole mw3.log and mw3.old.log, or copied a stale problems log");

        var cleanBaseline = PlaytestDiagnostics.CaptureNativeBaseline(profile);
        var problemsText = "[0.5] W startup warning\n[3.0] W play warning\n[4.0] E play error\n";
        File.WriteAllText(problemsLog, problemsText);
        File.AppendAllText(gameLog, "mw3: this session\n");
        var cleanLauncherLog = NewSession(root, "session-521-clean", "MW3-RE launcher fixture\n");
        var cleanSession = Path.GetDirectoryName(cleanLauncherLog)!;
        PlaytestDiagnostics.CollectNativeSessionArtifacts(cleanBaseline, cleanSession);
        Check(File.ReadAllText(Path.Combine(cleanSession, "native", "mw3.log")) == wholeGameLog + "mw3: this session\n" &&
            File.ReadAllText(Path.Combine(cleanSession, "native", "mw3.old.log")) == "mw3: previous session\n" &&
            File.ReadAllText(Path.Combine(cleanSession, "native", "mw3-problems.log")) == problemsText,
            "A clean-exit session did not get all three game files whole");

        // Problems after the first frame prompt; startup ones don't. The clean-exit summary
        // prefers the first E line over earlier W lines, and crashes keep their old summary.
        Check(GameProblemsLog.PlayProblems(cleanSession, 2000).SequenceEqual(
                new[] { "[3.0] W play warning", "[4.0] E play error" }) &&
            GameProblemsLog.PlayProblems(cleanSession, null).Count == 0 &&
            GameProblemsLog.PlayProblems(cleanSession, 5000).Count == 0 &&
            GameProblemsLog.PlayProblems(staleProblemsSession, 0).Count == 0,
            "Play problems included startup lines, or prompted without a first frame or a problems log");
        Check(PlaytestDiagnostics.FailureSummary(cleanLauncherLog, 0) == "play error" &&
            PlaytestDiagnostics.FailureSummary(cleanLauncherLog, 7) == PlaytestDiagnostics.GenericFailureSummary,
            "Clean-exit summary did not take the first E line, or a crash summary used the problems log");

        // Export Report keeps a 5 MB log whole, and the new files get their own zip names.
        var wholeZip = Path.Combine(root, "report-521-whole.zip");
        ReportExport.Export(wholeZip, settings, Array.Empty<PackManifest>(), cleanLauncherLog, app, exitCode: 0);
        using (var zip = ZipFile.OpenRead(wholeZip))
        {
            Check(zip.Entries.Select(entry => entry.FullName).Order().SequenceEqual(new[]
                {
                    "launcher.log", "native-mw3-problems.log", "native-mw3.log", "native-mw3.old.log", "report.json"
                }),
                "Export did not include the problems log and old game log under their zip names");
            Check(ReadEntry(zip, "native-mw3.log") == wholeGameLog + "mw3: this session\n",
                "Export cut a 5 MB game log");
        }

        // Logs that would pass 19 MB are cut so the zip fits, each keeping its first 1 MB and its
        // end. Random text keeps the zip from compressing the logs away.
        var bigLauncherLog = NewSession(root, "session-521-big", "launcher\n");
        var bigNative = Path.Combine(Path.GetDirectoryName(bigLauncherLog)!, "native");
        var random = new Random(521);
        string RandomLog(int megabytes)
        {
            var bytes = new byte[megabytes * 1024 * 1024 * 3 / 4];
            random.NextBytes(bytes);
            return Convert.ToBase64String(bytes, Base64FormattingOptions.InsertLineBreaks).Replace("\r\n", "\n") +
                "\nlast line of the log\n";
        }
        var bigLogs = new Dictionary<string, string>
        {
            ["native-mw3.log"] = RandomLog(20),
            ["native-mw3.old.log"] = RandomLog(6)
        };
        File.WriteAllText(Path.Combine(bigNative, "mw3.log"), bigLogs["native-mw3.log"]);
        File.WriteAllText(Path.Combine(bigNative, "mw3.old.log"), bigLogs["native-mw3.old.log"]);
        var cutZip = Path.Combine(root, "report-521-cut.zip");
        ReportExport.Export(cutZip, settings, Array.Empty<PackManifest>(), bigLauncherLog, app);
        Check(new FileInfo(cutZip).Length <= ReportExport.MaxExportZipBytes, "Export zip passed 19 MB");
        using (var zip = ZipFile.OpenRead(cutZip))
        {
            var cutCount = 0;
            foreach (var (name, original) in bigLogs)
            {
                var exported = ReadEntry(zip, name);
                if (exported == original) continue;
                cutCount++;
                var head = original[..ReportExport.KeptLogHeadChars];
                head = head[..(head.LastIndexOf('\n') + 1)];
                Check(exported.StartsWith(head + ReportExport.CutMarker, StringComparison.Ordinal) &&
                    exported.EndsWith("\nlast line of the log\n", StringComparison.Ordinal),
                    "A cut export log lost its first 1 MB or its end: " + name);
            }
            Check(cutCount > 0, "Export cut no log although the zip would pass 19 MB");
        }

        // The setup header: every game line parsed; unknown keys, malformed values, later
        // duplicates and heaps without a budget skipped; strings redacted and cut to 80.
        var headerLog = Path.Combine(root, "header-mw3.log");
        File.WriteAllText(headerLog,
            "[0.10] I mw3: header vulkan_device=Example GPU 9000\n" +
            "mw3: header vulkan_device=Second device ignored\n" +
            "mw3: header vulkan_api_version=1.3.280\n" +
            "mw3: header vulkan_driver_version=560.94.0.0\n" +
            "mw3: header heap index=0 size_bytes=12884901888 budget_bytes=11811160064 device_local=1\n" +
            "mw3: header heap index=1 size_bytes=34359738368 device_local=0\n" +
            "mw3: header heap index=2 size_bytes=268435456 budget_bytes=201326592 device_local=0\n" +
            "mw3: header resolution=wide\n" +
            "mw3: header resolution=2560x1080\n" +
            "mw3: header window_mode=borderless\n" +
            "mw3: header refresh_hz=144\n" +
            "mw3: header hdr=1\n" +
            "mw3: header favorite_color=blue\n");
        var privateDevice = @"C:\Users\Jane Doe\" + new string('x', 200);
        var packs = new[]
        {
            new PackManifest { Id = "test.textures", IsEnabled = true, Files = new Dictionary<string, PackFile>
            {
                ["textures/a.dds"] = new PackFile { Bytes = 1000 },
                ["textures/b.PNG"] = new PackFile { Bytes = 24 },
                ["audio/c.wav"] = new PackFile { Bytes = 5000 }
            } },
            new PackManifest { Id = "test.disabled", IsEnabled = false, Files = new Dictionary<string, PackFile>
            {
                ["textures/a.dds"] = new PackFile { Bytes = 7 }
            } },
            new PackManifest { Id = "test.no-files", IsEnabled = true }
        };
        var roots = PlaytestDiagnostics.ReportRoots(settings, app);
        var header = ReportHeader.Build(headerLog, packs, new[] { "Flight Stick", privateDevice }, roots);
        var webOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web);
        using (var headerDoc = JsonSerializer.SerializeToDocument(header, webOptions))
        {
            var h = headerDoc.RootElement;
            var heaps = h.GetProperty("heaps");
            var devices = h.GetProperty("input_devices");
            Check(h.GetProperty("vulkan_device").GetString() == "Example GPU 9000" &&
                h.GetProperty("vulkan_api_version").GetString() == "1.3.280" &&
                h.GetProperty("vulkan_driver_version").GetString() == "560.94.0.0" &&
                heaps.GetArrayLength() == 2 &&
                heaps[0].GetProperty("index").GetInt32() == 0 &&
                heaps[0].GetProperty("size_bytes").GetInt64() == 12884901888 &&
                heaps[0].GetProperty("budget_bytes").GetInt64() == 11811160064 &&
                heaps[0].GetProperty("device_local").GetBoolean() &&
                heaps[1].GetProperty("index").GetInt32() == 2 &&
                h.GetProperty("resolution").GetString() == "2560x1080" &&
                h.GetProperty("window_mode").GetString() == "borderless" &&
                h.GetProperty("refresh_hz").GetInt32() == 144 &&
                h.GetProperty("hdr").GetBoolean() &&
                !h.TryGetProperty("favorite_color", out _),
                "Report header did not parse the game's header lines as the contract says: " + h);
            var packTextures = h.GetProperty("pack_texture_bytes");
            Check(packTextures.GetArrayLength() == 1 &&
                packTextures[0].GetProperty("id").GetString() == "test.textures" &&
                packTextures[0].GetProperty("bytes").GetInt64() == 1024,
                "Report header pack texture sizes counted non-textures, disabled packs or packs without files");
            Check(devices.GetArrayLength() == 2 && devices[0].GetString() == "Flight Stick" &&
                devices[1].GetString()!.Length <= ReportHeader.MaxTextLength &&
                !devices[1].GetString()!.Contains("Jane Doe", StringComparison.Ordinal),
                "Report header input device names were not redacted and cut to 80 characters");
        }
        var launcherFactsOnly = ReportHeader.Build(Path.Combine(root, "missing-mw3.log"), packs.Take(2),
            Array.Empty<string>(), roots);
        Check(launcherFactsOnly.Keys.SequenceEqual(new[] { "pack_texture_bytes" }),
            "A header without game lines held more than pack texture sizes");

        // The upload stays within 256 KB, keeps the problems log's first E line and last line,
        // leads with the header, and puts the last health lines first in the game log.
        var uploadLauncherLog = NewSession(root, "session-521-upload", Lines("launcher", 20_000));
        var uploadNative = Path.Combine(Path.GetDirectoryName(uploadLauncherLog)!, "native");
        File.WriteAllText(Path.Combine(uploadNative, "mw3-problems.log"),
            "[2.0] E first trouble\n" + Lines("[3.0] W repeated warning", 8_000) + "[900.0] W last problem\n");
        File.WriteAllText(Path.Combine(uploadNative, "mw3.log"),
            Lines("mw3: early", 5_000) + "mw3: health frame=1 vram=100\n" + Lines("mw3: middle", 20_000) +
            "mw3: health frame=2 vram=200\n" + Lines("mw3: late", 5_000));
        File.WriteAllText(Path.Combine(uploadNative, "stderr.txt"), Lines("stderr", 20_000));
        File.WriteAllText(Path.Combine(uploadNative, "stdout.txt"), Lines("stdout", 20_000));
        var upload = PlaytestDiagnostics.CreateCrashReport(settings, Array.Empty<PackManifest>(), uploadLauncherLog,
            app, "1.2.3", 0, new HardwareInventoryData(Array.Empty<ProcessorInventory>(), null,
                Array.Empty<GraphicsAdapterInventory>()), header);
        var uploadBytes = JsonSerializer.SerializeToUtf8Bytes(upload, webOptions);
        Check(uploadBytes.Length <= PlaytestDiagnostics.MaxRequestBytes, "Upload passed 256 KB: " + uploadBytes.Length);
        using (var uploadDoc = JsonDocument.Parse(uploadBytes))
        {
            var u = uploadDoc.RootElement;
            var fieldNames = u.EnumerateObject().Select(property => property.Name).Take(2).ToArray();
            var logs = u.GetProperty("logs");
            var problems = logs.GetProperty("native_problems").GetString()!;
            var run = logs.GetProperty("native_run").GetString()!;
            Check(fieldNames.SequenceEqual(new[] { "format_version", "header" }) &&
                u.GetProperty("header").GetProperty("vulkan_device").GetString() == "Example GPU 9000" &&
                u.GetProperty("header").GetProperty("heaps").GetArrayLength() == 2,
                "Upload did not lead with the whole header");
            Check(logs.EnumerateObject().First().Name == "native_problems" &&
                problems.StartsWith("[2.0] E first trouble\n", StringComparison.Ordinal) &&
                problems.EndsWith("[900.0] W last problem\n", StringComparison.Ordinal),
                "Upload dropped the problems log, its first E line or its last line");
            Check(run.StartsWith("Last health lines:\nmw3: health frame=1 vram=100\nmw3: health frame=2 vram=200\n",
                    StringComparison.Ordinal),
                "Upload game log did not lead with the last health lines");
            Check(u.GetProperty("failure_summary").GetString() == "first trouble",
                "Clean-exit upload was not summarized by the problems log's first E line");
        }
    }
}
