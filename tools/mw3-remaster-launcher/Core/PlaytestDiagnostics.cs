using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace MW3RemasterLauncher.Core;

/// <summary>Pre-launch profile state so current-session native logs can be separated from stale prior runs.</summary>
public sealed record NativeSessionDiagnosticsBaseline(
    string WriteDirectory,
    string LogPath,
    bool LogExisted,
    DateTime LogCreationTimeUtc,
    DateTime LogLastWriteTimeUtc,
    long LogLength,
    string CrashPath,
    long CrashOffset,
    DateTime StartedUtc);

/// <summary>Export a small local support bundle, using an explicit allowlist of metadata and log tails.</summary>
public static class PlaytestDiagnostics
{
    public const int MaxLogBytes = 64 * 1024;
    public const int MaxAggregateLogBytes = 160 * 1024;
    public const int MaxRequestBytes = 256 * 1024;
    public const string GenericFailureSummary = "No specific failure was recorded.";

    // Windows ends a program with STATUS_APPLICATION_HANG (0xCFFFFFFF) when its window
    // stops answering messages and the player chooses to close it, so the logs often
    // hold no error line at all.
    public const int ApplicationHangExitCode = unchecked((int)0xCFFFFFFF);
    public const string ApplicationHangSummary = "The game stopped responding and Windows closed it.";
    public const string NativeCrashFileName = "crash.txt";
    public const string NativeRunFileName = "mw3.log";

    // Keep only the fixed diagnostic suffix of the legacy host fault record (issue #150).
    private static readonly Regex WindowsPathWithNativeSuffix = new(
        @"^(?<prefix>HOST EXCEPTION (?:0x)?[0-9a-f]{1,8} at )(?<path>(?:[A-Z]:[\\/]|\\\\)[^\r\n\t""<>|:]{1,1024}?)(?<suffix>\.(?:exe|dll)[ \t]*\+0x[0-9a-f]{1,16}(?: \(access [0-9]+ address (?:0x)?[0-9a-f]{1,16}\))?)(?=\r?$)",
        RegexOptions.Multiline | RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);

    public static string LauncherVersionString(Assembly? assembly = null)
    {
        var target = assembly ?? typeof(GameRunner).Assembly;
        var informational = target.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion;
        if (!string.IsNullOrWhiteSpace(informational))
        {
            var plus = informational.IndexOf('+');
            var clean = (plus >= 0 ? informational[..plus] : informational).Trim();
            if (clean.Length > 0) return clean;
        }
        return target.GetName().Version?.ToString(3) ?? "unknown";
    }

    public static string OperatingSystemDescription()
    {
        try
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                var version = Environment.OSVersion.Version;
                string? installationType = null;
                string? displayVersion = null;
                int? ubr = null;
                try
                {
                    using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion");
                    installationType = key?.GetValue("InstallationType") as string;
                    displayVersion = (key?.GetValue("DisplayVersion") as string) ?? (key?.GetValue("ReleaseId") as string);
                    if (key?.GetValue("UBR") is int ubrValue) ubr = ubrValue;
                }
                catch { }

                return FormatWindowsDescription(version.Build, ubr, installationType, displayVersion);
            }
        }
        catch { }
        return RuntimeInformation.OSDescription;
    }

    public static string FormatWindowsDescription(int build, int? ubr = null, string? installationType = null, string? displayVersion = null)
    {
        if (build <= 0) return RuntimeInformation.OSDescription;
        var isServer = !string.IsNullOrWhiteSpace(installationType) &&
            installationType.Contains("Server", StringComparison.OrdinalIgnoreCase);
        string family;
        if (isServer)
        {
            family = build >= 26100 ? "Windows Server 2025"
                : build >= 20348 ? "Windows Server 2022"
                : build >= 17763 ? "Windows Server 2019"
                : build >= 14393 ? "Windows Server 2016"
                : "Windows Server";
        }
        else
        {
            family = build >= 22000 ? "Windows 11"
                : build >= 10240 ? "Windows 10"
                : "Windows";
        }

        var parts = new List<string> { family };
        if (!string.IsNullOrWhiteSpace(displayVersion)) parts.Add(displayVersion.Trim());
        var buildText = ubr is > 0 ? $"10.0.{build}.{ubr}" : $"10.0.{build}";
        parts.Add($"(OS Build {buildText})");
        return string.Join(" ", parts);
    }

    public static string FormatExitCode(int exitCode) =>
        $"{exitCode} (0x{unchecked((uint)exitCode):X8})";

    public static string FormatRuntimeVersion(Mw3ReRuntimeContract contract) =>
        FormatRuntimeVersion(contract.BuildId, contract.SourceCommit);

    /// <summary>
    /// The build id plus the first 12 characters of the source commit, at most 80 characters
    /// (the crash-report service keeps no more). Shipped build ids are "mw3-re-" plus a
    /// 64-character hash, too long to fit beside the commit, so the build id is cut rather
    /// than the commit: the commit is what finds the source.
    /// </summary>
    public static string FormatRuntimeVersion(string? buildId, string? sourceCommit)
    {
        const int maxLength = 80;
        var id = string.IsNullOrWhiteSpace(buildId) ? "mw3-re" : buildId.Trim();
        var commit = sourceCommit?.Trim() ?? "";
        if (commit.Length < 12) return id.Length <= maxLength ? id : id[..maxLength];

        var commitPart = $" ({commit[..12]})";
        var idRoom = maxLength - commitPart.Length;
        var shownId = id.Length <= idRoom ? id : id[..idRoom];
        return shownId + commitPart;
    }

    public static NativeSessionDiagnosticsBaseline CaptureNativeBaseline(string writeDirectory)
    {
        var fullWriteDir = Path.GetFullPath(writeDirectory);
        var logPath = Path.Combine(fullWriteDir, NativeRunFileName);
        var crashPath = Path.Combine(fullWriteDir, NativeCrashFileName);
        bool logExisted = false;
        DateTime logCreated = DateTime.MinValue;
        DateTime logWritten = DateTime.MinValue;
        long logLength = 0;
        try
        {
            if (File.Exists(logPath) && !HasLinkInChain(logPath))
            {
                var info = new FileInfo(logPath);
                logExisted = true;
                logCreated = info.CreationTimeUtc;
                logWritten = info.LastWriteTimeUtc;
                logLength = info.Length;
            }
        }
        catch { }

        long crashOffset = 0;
        try
        {
            if (File.Exists(crashPath) && !HasLinkInChain(crashPath))
            {
                crashOffset = new FileInfo(crashPath).Length;
            }
        }
        catch { }

        return new NativeSessionDiagnosticsBaseline(
            fullWriteDir,
            logPath,
            logExisted,
            logCreated,
            logWritten,
            logLength,
            crashPath,
            crashOffset,
            DateTime.UtcNow);
    }

    public static void CollectNativeSessionArtifacts(NativeSessionDiagnosticsBaseline? baseline, string sessionDirectory)
    {
        if (baseline == null || string.IsNullOrWhiteSpace(sessionDirectory)) return;
        try
        {
            PackStorage.EnsureNoLinks(sessionDirectory);
            var nativeDir = Path.Combine(sessionDirectory, "native");
            Directory.CreateDirectory(nativeDir);
            PackStorage.EnsureNoLinks(nativeDir);

            // 1. Newly appended crash.txt bytes from this session only.
            try
            {
                if (File.Exists(baseline.CrashPath) && !HasLinkInChain(baseline.CrashPath))
                {
                    using var stream = new FileStream(baseline.CrashPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
                    var length = stream.Length;
                    if (length > baseline.CrashOffset && baseline.CrashOffset >= 0)
                    {
                        var start = Math.Max(baseline.CrashOffset, length - MaxLogBytes);
                        stream.Position = start;
                        var text = ReadStreamSlice(stream, (int)Math.Min(MaxLogBytes, length - start), start > baseline.CrashOffset);
                        if (!string.IsNullOrWhiteSpace(text))
                        {
                            File.WriteAllText(Path.Combine(nativeDir, NativeCrashFileName), text, new UTF8Encoding(false));
                        }
                    }
                }
            }
            catch { }

            // 2. Current-session mw3.log, guarded against stale pre-launch log files.
            try
            {
                if (File.Exists(baseline.LogPath) && !HasLinkInChain(baseline.LogPath))
                {
                    var info = new FileInfo(baseline.LogPath);
                    var fresh = !baseline.LogExisted ||
                        info.LastWriteTimeUtc != baseline.LogLastWriteTimeUtc ||
                        info.CreationTimeUtc != baseline.LogCreationTimeUtc ||
                        info.Length != baseline.LogLength;
                    if (fresh)
                    {
                        var text = ReadLogForSession(baseline.LogPath);
                        if (!string.IsNullOrWhiteSpace(text))
                        {
                            File.WriteAllText(Path.Combine(nativeDir, NativeRunFileName), text, new UTF8Encoding(false));
                        }
                    }
                }
            }
            catch { }
        }
        catch { }
    }

    private static bool HasLinkInChain(string path)
    {
        try
        {
            PackStorage.EnsureNoLinks(path);
            return false;
        }
        catch
        {
            return true;
        }
    }

    private static string ReadStreamSlice(Stream stream, int maxBytes, bool trimPartialFirstLine)
    {
        var buffer = new byte[Math.Min(MaxLogBytes, Math.Max(0, maxBytes))];
        var length = 0;
        int count;
        while (length < buffer.Length && (count = stream.Read(buffer, length, buffer.Length - length)) != 0)
            length += count;
        var text = Encoding.UTF8.GetString(buffer, 0, length);
        if (trimPartialFirstLine)
        {
            var newline = text.IndexOf('\n');
            text = newline < 0 ? "" : text[(newline + 1)..];
        }
        return text;
    }

    private static string ReadLogForSession(string path)
    {
        if (!File.Exists(path)) return "";
        PackStorage.EnsureNoLinks(path);
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
        if (stream.Length <= MaxLogBytes)
            return ReadStreamSlice(stream, (int)stream.Length, trimPartialFirstLine: false);

        // Retain informative startup/fault lines from the head when a long session log is truncated.
        const int headBudget = 12 * 1024;
        const int tailBudget = MaxLogBytes - headBudget - 64;
        stream.Position = 0;
        var head = ReadStreamSlice(stream, headBudget, trimPartialFirstLine: false);
        var lastHeadNewline = head.LastIndexOf('\n');
        if (lastHeadNewline >= 0) head = head[..(lastHeadNewline + 1)];

        var tailStart = Math.Max(headBudget, stream.Length - tailBudget);
        stream.Position = tailStart;
        var tail = ReadStreamSlice(stream, (int)(stream.Length - tailStart), trimPartialFirstLine: true);
        return head + "...\n" + tail;
    }

    public static object CreateCrashReport(LauncherSettings settings, IEnumerable<PackManifest> packs,
        string? launchLog, string applicationRoot, string? runtimeVersion = null, int? exitCode = null,
        HardwareInventoryData? hardwareInventory = null)
    {
        var roots = new[] { applicationRoot, GameRunner.FindRepositoryRoot(applicationRoot) ?? "", settings.GamePath,
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), LauncherPaths.DataRoot };
        var logs = ReadSessionLogs(launchLog, roots);
        var failureSummary = Redact(FailureSummary(launchLog, exitCode), roots);
        if (failureSummary.Length > 2000) failureSummary = failureSummary[..2000];

        var packArray = packs.Select(pack => new { pack.Id, pack.Version, pack.SchemaVersion, pack.IsEnabled, pack.Priority }).ToArray();
        var settingsObject = ReportSettings(settings);
        var hardware = hardwareInventory ?? HardwareInventory.Capture();
        var reportId = Guid.NewGuid().ToString("N");
        var createdUtc = DateTimeOffset.UtcNow;
        var launcherVersion = LauncherVersionString();
        var resolvedRuntimeVersion = string.IsNullOrWhiteSpace(runtimeVersion) ? "unknown" : runtimeVersion;
        var os = OperatingSystemDescription();
        var architecture = RuntimeInformation.ProcessArchitecture.ToString();
        var dotnetRuntime = RuntimeInformation.FrameworkDescription;

        object BuildPayload(Dictionary<string, string> currentLogs) => new
        {
            format_version = 1,
            report_id = reportId,
            created_utc = createdUtc,
            launcher_version = launcherVersion,
            runtime_version = resolvedRuntimeVersion,
            mode = settings.EngineMode,
            exit_code = exitCode,
            os,
            architecture,
            dotnet_runtime = dotnetRuntime,
            hardware,
            failure_summary = failureSummary,
            settings = settingsObject,
            packs = packArray,
            logs = currentLogs
        };

        TrimLogsToFitRequest(logs, BuildPayload);
        return BuildPayload(logs);
    }

    private static readonly (string WireKey, string ZipName, string RelativePath)[] SessionLogMappings =
    {
        ("native_crash", "native-crash.txt", Path.Combine("native", NativeCrashFileName)),
        ("native_run", "native-mw3.log", Path.Combine("native", NativeRunFileName)),
        ("native_stderr", "native-stderr.txt", Path.Combine("native", "stderr.txt")),
        ("launcher", "launcher.log", ""),
        ("native_stdout", "native-stdout.txt", Path.Combine("native", "stdout.txt"))
    };

    private static Dictionary<string, string> ReadSessionLogs(string? launchLog, string[] roots)
    {
        var logs = new Dictionary<string, string>();
        if (launchLog == null) return logs;
        string? folder;
        try { folder = Path.GetDirectoryName(launchLog); }
        catch { return logs; }
        if (string.IsNullOrEmpty(folder)) return logs;

        var remainingBudget = MaxAggregateLogBytes;
        foreach (var (wireKey, _, relativePath) in SessionLogMappings)
        {
            if (remainingBudget <= 0) break;
            var path = relativePath.Length == 0 ? launchLog : Path.Combine(folder, relativePath);
            var text = TryReadRedactedTail(path, roots);
            if (string.IsNullOrEmpty(text)) continue;
            var cap = Math.Min(MaxLogBytes, remainingBudget);
            if (text.Length > cap)
            {
                text = wireKey == "native_crash" ? text[..cap] : SliceTailOnLineBoundary(text, cap);
            }
            if (text.Length == 0) continue;
            logs[wireKey] = text;
            remainingBudget -= text.Length;
        }
        return logs;
    }

    private static string SliceTailOnLineBoundary(string text, int maxChars)
    {
        if (text.Length <= maxChars) return text;
        var sliced = text[^maxChars..];
        var newline = sliced.IndexOf('\n');
        return newline >= 0 && newline + 1 < sliced.Length ? sliced[(newline + 1)..] : sliced;
    }

    private static void TrimLogsToFitRequest(Dictionary<string, string> logs, Func<Dictionary<string, string>, object> buildPayload)
    {
        var trimOrder = new[] { "native_stdout", "launcher", "native_stderr", "native_run", "native_crash" };
        var webOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web);
        for (var attempt = 0; attempt < 16; attempt++)
        {
            var bytes = JsonSerializer.SerializeToUtf8Bytes(buildPayload(logs), webOptions).Length;
            if (bytes <= MaxRequestBytes) return;

            var targetKey = trimOrder.FirstOrDefault(key => logs.TryGetValue(key, out var val) && val.Length > 0);
            if (targetKey == null) return;
            var current = logs[targetKey];
            var excess = bytes - MaxRequestBytes;
            var cut = Math.Max(1024, excess);
            if (current.Length <= cut)
            {
                logs.Remove(targetKey);
            }
            else
            {
                var nextLen = Math.Max(0, current.Length - cut);
                logs[targetKey] = targetKey == "native_crash"
                    ? current[..nextLen]
                    : SliceTailOnLineBoundary(current, nextLen);
                if (logs[targetKey].Length == 0) logs.Remove(targetKey);
            }
        }
    }

    private static string TryReadRedactedTail(string path, string[] roots)
    {
        try
        {
            if (!File.Exists(path)) return "";
            var raw = Path.GetFileName(path).Equals(NativeRunFileName, StringComparison.OrdinalIgnoreCase)
                ? ReadLogForSession(path)
                : ReadTail(path);
            return string.IsNullOrEmpty(raw) ? "" : Redact(raw, roots);
        }
        catch
        {
            return "";
        }
    }

    public static string ReadTail(string path)
    {
        if (!File.Exists(path)) return "";
        PackStorage.EnsureNoLinks(path);
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
        var start = Math.Max(0, stream.Length - MaxLogBytes);
        stream.Position = start;
        var buffer = new byte[MaxLogBytes];
        var length = 0;
        int count;
        while (length < buffer.Length && (count = stream.Read(buffer, length, buffer.Length - length)) != 0) length += count;
        var text = Encoding.UTF8.GetString(buffer, 0, length);
        if (start != 0)
        {
            var newline = text.IndexOf('\n');
            text = newline < 0 ? "" : text[(newline + 1)..];
        }
        return text;
    }

    /// <summary>
    /// The most specific failure line in the session's logs. With none, a hang exit code
    /// still gets a plain explanation; anything else gets the generic text.
    /// </summary>
    public static string FailureSummary(string? launchLog, int? exitCode = null)
    {
        var specificFailure = FindSpecificFailure(launchLog);
        if (specificFailure != null) return specificFailure;
        var windowsClosedHungGame = exitCode == ApplicationHangExitCode;
        return windowsClosedHungGame ? ApplicationHangSummary : GenericFailureSummary;
    }

    private static string? FindSpecificFailure(string? launchLog)
    {
        if (launchLog == null) return null;
        string? directory;
        try { directory = Path.GetDirectoryName(launchLog); }
        catch { return null; }
        if (string.IsNullOrEmpty(directory)) return null;

        // 1. Check native/crash.txt first for direct crash_report.cpp fault lines.
        var crashFile = Path.Combine(directory, "native", NativeCrashFileName);
        var crashLines = SafeReadLines(crashFile);
        if (crashLines.Length > 0)
        {
            var faultLine = FindNativeCrashFaultLine(crashLines);
            if (faultLine != null) return faultLine;
        }

        // 2. Check native/stderr.txt, native/mw3.log, and the launcher log for specific errors.
        var runFile = Path.Combine(directory, "native", NativeRunFileName);
        var stderrFile = Path.Combine(directory, "native", "stderr.txt");
        foreach (var file in new[] { stderrFile, runFile, launchLog })
        {
            var lines = SafeReadLines(file);
            if (lines.Length == 0) continue;

            var nativeFault = FindNativeCrashFaultLine(lines);
            if (nativeFault != null) return nativeFault;

            var error = lines.LastOrDefault(IsSpecificErrorLine);
            if (error != null) return CleanSummaryLine(error);
        }
        return null;
    }

    /// <summary>The graphics settings that apply to the session's engine.</summary>
    private static object ReportSettings(LauncherSettings settings) => settings.EngineMode == "d7vk"
        ? new { settings.D7VkResolution, settings.D7VkAntiAliasing,
            settings.D7VkAnisotropicFiltering, settings.D7VkAiTextures }
        : new { settings.Width, settings.Height, settings.WindowMode, settings.AntiAliasing,
            settings.AnisotropicFiltering, settings.DrawDistance, settings.FogDistance,
            settings.LocalCdAudio, settings.InstantReplay, settings.PerformanceMonitor,
            settings.RenderThread };

    private static string[] SafeReadLines(string path)
    {
        try
        {
            if (!File.Exists(path)) return Array.Empty<string>();
            var text = Path.GetFileName(path).Equals(NativeRunFileName, StringComparison.OrdinalIgnoreCase)
                ? ReadLogForSession(path)
                : ReadTail(path);
            return text.Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        }
        catch
        {
            return Array.Empty<string>();
        }
    }

    private static string? FindNativeCrashFaultLine(string[] lines)
    {
        string? crashedLine = null;
        string? accessLine = null;
        foreach (var raw in lines)
        {
            var line = CleanSummaryLine(raw);
            if (Regex.IsMatch(line, @"^[A-Za-z0-9._-]{1,64}: crashed: ", RegexOptions.CultureInvariant))
                crashedLine = line;
            else if (Regex.IsMatch(line, @"^[A-Za-z0-9._-]{1,64}: access violation: ", RegexOptions.CultureInvariant))
                accessLine = line;
        }
        if (crashedLine != null && accessLine != null)
        {
            var accessSuffix = accessLine[(accessLine.IndexOf(": access violation:", StringComparison.Ordinal) + 2)..];
            return $"{crashedLine} ({accessSuffix})";
        }
        if (crashedLine != null) return crashedLine;
        if (accessLine != null) return accessLine;
        return null;
    }

    private static bool IsSpecificErrorLine(string line)
    {
        var trimmed = line.Trim();
        if (trimmed.Length == 0) return false;
        if (trimmed.Contains("crash details, if any, are written to", StringComparison.OrdinalIgnoreCase))
            return false;
        return trimmed.StartsWith("ERROR:", StringComparison.Ordinal) ||
            trimmed.StartsWith("[D7VK ERR]", StringComparison.Ordinal) ||
            trimmed.StartsWith("HOST EXCEPTION ", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("loader-order entry fault:", StringComparison.Ordinal) ||
            trimmed.Contains("SEH flat fault", StringComparison.Ordinal) ||
            trimmed.Contains("Unhandled exception", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("uncaught exception:", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("Fatal error", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("crash report file could not be opened", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("minidump worker unavailable", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("crash reporting not installed", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("could not create minidump:", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Contains("minidump failed:", StringComparison.OrdinalIgnoreCase) ||
            Regex.IsMatch(trimmed, @"^mw3(?:pm|launcher)?: (?:cannot|could not|failed|error|fatal)\b", RegexOptions.IgnoreCase);
    }

    private static string CleanSummaryLine(string line)
    {
        var trimmed = line.Trim();
        return Regex.Replace(trimmed, @"\s+\[launcher elapsed \d+ ms\]$", "");
    }

    public static string Redact(string text, params string[] privateRoots)
    {
        if (string.IsNullOrEmpty(text)) return "";

        text = WindowsPathWithNativeSuffix.Replace(text, match =>
        {
            var prefix = match.Groups["prefix"].Value;
            var path = match.Groups["path"].Value;
            var suffix = match.Groups["suffix"].Value;
            var token = path.StartsWith(@"\\", StringComparison.Ordinal) ? "<network-path>" : "<local-path>";
            var lastSep = path.LastIndexOfAny(new[] { '\\', '/' });
            var moduleStem = lastSep >= 0 ? path[(lastSep + 1)..] : path;
            if (Regex.IsMatch(moduleStem, @"\A[A-Za-z0-9._-]{1,64}\z"))
                return $"{prefix}{token}/{moduleStem}{suffix}";
            return $"{prefix}{token}{suffix}";
        });

        var orderedRoots = privateRoots
            .Where(root => !string.IsNullOrWhiteSpace(root))
            .OrderByDescending(root => root.Length)
            .ToArray();

        // Replace complete path tokens before substituting known roots, or a
        // replaced root prefix could leave the remainder of a path visible.
        // Scrub single-quoted paths first so trailing text (such as .NET
        // Process.Start errors) is preserved.
        text = ScrubSingleQuotedPaths(text, orderedRoots);
        text = Regex.Replace(text, @"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\r\n\t\""<>|]*", "<local-path>");
        text = Regex.Replace(text, @"\\\\[^\r\n\t""<>|]+", "<network-path>");
        foreach (var root in orderedRoots)
        {
            text = text.Replace(root, "<local-path>", StringComparison.OrdinalIgnoreCase);
            text = text.Replace(root.Replace('\\', '/'), "<local-path>", StringComparison.OrdinalIgnoreCase);
        }
        return text;
    }

    private static string ScrubSingleQuotedPaths(string text, string[] orderedRoots)
    {
        StringBuilder? rewritten = null;
        var copyFrom = 0;
        var index = 0;
        while (index < text.Length)
        {
            if (text[index] != '\'' || !IsQuotedPathOpeningBoundary(text, index))
            {
                index++;
                continue;
            }

            var pathStart = index + 1;
            string? replacement = null;
            var expectedSeparator = '\\';
            if (IsDrivePathStart(text, pathStart))
            {
                replacement = "'<local-path>'";
                expectedSeparator = text[pathStart + 2] == '/' ? '/' : '\\';
            }
            else if (IsUncPathStart(text, pathStart))
            {
                replacement = "'<network-path>'";
            }

            if (replacement == null)
            {
                index++;
                continue;
            }

            var closeQuote = FindSingleQuotedPathClose(
                text, pathStart, pathStart + 3, expectedSeparator, orderedRoots);
            if (closeQuote < 0)
            {
                index++;
                continue;
            }

            rewritten ??= new StringBuilder(text.Length);
            rewritten.Append(text, copyFrom, index - copyFrom);
            rewritten.Append(replacement);
            copyFrom = closeQuote + 1;
            index = copyFrom;
        }

        if (rewritten == null) return text;
        rewritten.Append(text, copyFrom, text.Length - copyFrom);
        return rewritten.ToString();
    }

    private static bool IsDrivePathStart(string text, int start) =>
        start + 2 < text.Length &&
        char.IsAsciiLetter(text[start]) &&
        text[start + 1] == ':' &&
        text[start + 2] is '\\' or '/';

    private static bool IsUncPathStart(string text, int start) =>
        start + 2 < text.Length &&
        text[start] == '\\' &&
        text[start + 1] == '\\' &&
        !IsDisallowedPathChar(text[start + 2]) &&
        text[start + 2] != '\'';

    private static bool IsQuotedPathOpeningBoundary(string text, int quoteIndex) =>
        quoteIndex == 0 ||
        IsOpeningQuoteDelimiter(text[quoteIndex - 1]);

    private static bool IsOpeningQuoteDelimiter(char c) =>
        char.IsWhiteSpace(c) ||
        c is '(' or '[' or '{' or '=' or ',' or ';' or ':' or '"' or '`' or '<';

    private static bool IsQuotedPathClosingBoundary(string text, int quoteIndex) =>
        quoteIndex + 1 >= text.Length ||
        IsClosingQuoteDelimiter(text[quoteIndex + 1]);

    private static bool IsClosingQuoteDelimiter(char c) =>
        char.IsWhiteSpace(c) ||
        c is '.' or ',' or ';' or ':' or '!' or '?' or ')' or ']' or '}' or '"' or '`' or '>';

    private static bool IsDisallowedPathChar(char c) =>
        c is '\r' or '\n' or '\t' or '"' or '<' or '>' or '|';

    private static int FindSingleQuotedPathClose(
        string text,
        int pathStart,
        int initialScanIndex,
        char expectedSeparator,
        string[] orderedRoots)
    {
        var index = Math.Max(initialScanIndex, AdvancePastKnownRoot(text, pathStart, orderedRoots));
        while (index < text.Length)
        {
            var c = text[index];
            if (IsDisallowedPathChar(c)) return -1;
            if (c != '\'')
            {
                index++;
                continue;
            }

            if (!IsQuotedPathClosingBoundary(text, index))
            {
                index++;
                continue;
            }

            var continuedQuote = ContinuePastInternalApostrophe(text, index, expectedSeparator);
            if (continuedQuote >= 0)
            {
                index = continuedQuote;
                continue;
            }

            return index;
        }

        return -1;
    }

    private static int AdvancePastKnownRoot(
        string text,
        int pathStart,
        string[] orderedRoots)
    {
        var bestAdvance = pathStart;
        foreach (var root in orderedRoots)
        {
            var rootLength = GetMatchableRootLength(root);
            var advance = pathStart + rootLength;
            if (advance > bestAdvance && MatchesRootAt(text, pathStart, root, rootLength))
                bestAdvance = advance;
        }
        return bestAdvance;
    }

    private static int GetMatchableRootLength(string root)
    {
        var minLength = IsDrivePathStart(root, 0) ? 3
            : root.StartsWith(@"\\", StringComparison.Ordinal) ? 2
            : 1;
        var length = root.Length;
        while (length > minLength && root[length - 1] is '\\' or '/')
            length--;
        return length;
    }

    private static bool MatchesRootAt(
        string text,
        int pathStart,
        string root,
        int rootLength)
    {
        if (rootLength == 0 || pathStart + rootLength > text.Length) return false;
        for (var i = 0; i < rootLength; i++)
        {
            var actual = text[pathStart + i];
            var expected = root[i];
            if (actual == expected) continue;
            if ((actual is '\\' or '/') && (expected is '\\' or '/')) continue;
            if (char.ToUpperInvariant(actual) == char.ToUpperInvariant(expected)) continue;
            return false;
        }
        if (root[rootLength - 1] is '\\' or '/') return true;
        var after = pathStart + rootLength;
        return after < text.Length && text[after] is '\\' or '/' or '\'';
    }

    // Keep scanning past apostrophes followed by whitespace or punctuation inside a path
    // (such as "Players' Choice\mw3.exe" or "v1'.txt") without crossing into another quoted token.
    private static int ContinuePastInternalApostrophe(
        string text,
        int quoteIndex,
        char expectedSeparator)
    {
        if (quoteIndex + 1 >= text.Length) return -1;

        var after = text[quoteIndex + 1];
        if (after is ' ' or '\t' or '.' or ',' or ';' or '!' or '?' or ')' or ']')
        {
            var candidate = FindContinuationClosingQuote(
                text,
                quoteIndex + 1,
                expectedSeparator,
                requirePathSeparator: true,
                allowWhitespace: true);
            if (candidate >= 0) return candidate;
        }

        if (after is '.' or ',' &&
            quoteIndex + 2 < text.Length &&
            !char.IsWhiteSpace(text[quoteIndex + 2]) &&
            text[quoteIndex + 2] is not (
                '\'' or '=' or ':' or ')' or ']' or '}' or '"' or '`' or '>'))
        {
            var candidate = FindContinuationClosingQuote(
                text,
                quoteIndex + 2,
                expectedSeparator,
                requirePathSeparator: false,
                allowWhitespace: false);
            if (candidate >= 0) return candidate;
        }

        if (after == ' ')
        {
            var componentEnd = ScanSingleTrailingWordQuote(text, quoteIndex + 2);
            if (componentEnd >= 0) return componentEnd;
        }

        return -1;
    }

    private static int FindContinuationClosingQuote(
        string text,
        int start,
        char expectedSeparator,
        bool requirePathSeparator,
        bool allowWhitespace)
    {
        var sawSeparator = false;
        var forwardSlashCount = 0;
        var lastForwardSlash = -1;
        for (var i = start; i < text.Length; i++)
        {
            var c = text[i];
            if (IsDisallowedPathChar(c) || c == ':') return -1;
            if (!allowWhitespace && char.IsWhiteSpace(c)) return -1;
            if (c == expectedSeparator || c == '\\')
            {
                sawSeparator = true;
            }
            else if (c == '/')
            {
                forwardSlashCount++;
                lastForwardSlash = i;
            }
            if (c != '\'') continue;

            if (IsQuotedPathClosingBoundary(text, i))
            {
                if (!requirePathSeparator || sawSeparator)
                    return i;
                return IsMixedForwardSlashContinuation(
                    text, lastForwardSlash, i, forwardSlashCount) ? i : -1;
            }

            // An opening quote after a delimiter starts a separate quoted token,
            // not a continuation.
            if (IsQuotedPathOpeningBoundary(text, i))
                return -1;
        }
        return -1;
    }

    private static bool IsMixedForwardSlashContinuation(
        string text,
        int lastSlash,
        int end,
        int slashCount)
    {
        if (slashCount <= 0 || lastSlash + 1 >= end)
            return false;
        if (HasFileExtension(text, lastSlash + 1, end))
            return true;
        if (slashCount < 2)
            return false;
        for (var i = lastSlash + 1; i < end; i++)
        {
            if (char.IsWhiteSpace(text[i]))
                return false;
        }
        return true;
    }

    private static bool HasFileExtension(string text, int segmentStart, int segmentEnd)
    {
        var lastDot = text.LastIndexOf('.', segmentEnd - 1, segmentEnd - segmentStart);
        if (lastDot <= segmentStart || lastDot >= segmentEnd - 1)
            return false;
        var extLength = segmentEnd - lastDot - 1;
        if (extLength > 8)
            return false;
        var hasLetter = false;
        for (var i = lastDot + 1; i < segmentEnd; i++)
        {
            var c = text[i];
            if (!char.IsAsciiLetterOrDigit(c))
                return false;
            if (char.IsAsciiLetter(c))
                hasLetter = true;
        }
        return hasLetter;
    }

    private static int ScanSingleTrailingWordQuote(string text, int start)
    {
        if (start >= text.Length) return -1;
        var length = 0;
        for (var i = start; i < text.Length; i++)
        {
            var c = text[i];
            if (IsDisallowedPathChar(c) || char.IsWhiteSpace(c)) return -1;
            if (c is '/' or '\\' or ':' or '=' or '(' or '[' or '{' or
                ',' or ';' or '!' or '?' or '"' or '`')
                return -1;
            if (c == '\'')
            {
                if (!IsQuotedPathClosingBoundary(text, i))
                {
                    length++;
                    continue;
                }
                return length > 0 ? i : -1;
            }
            length++;
        }
        return -1;
    }

    public static void Export(string destination, LauncherSettings settings, IEnumerable<PackManifest> packs,
        string? launchLog, string applicationRoot, HardwareInventoryData? hardwareInventory = null,
        string? runtimeVersion = null, int? exitCode = null)
    {
        // No profiles, settings files, saves, archives, media, dumps or recursive directory walks.
        var roots = new[] { applicationRoot, GameRunner.FindRepositoryRoot(applicationRoot) ?? "", settings.GamePath,
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), LauncherPaths.DataRoot };
        var failureSummary = Redact(FailureSummary(launchLog, exitCode), roots);
        if (failureSummary.Length > 2000) failureSummary = failureSummary[..2000];
        var report = new
        {
            format_version = 1,
            created_utc = DateTimeOffset.UtcNow,
            launcher_version = LauncherVersionString(),
            runtime_version = runtimeVersion ?? "unknown",
            mode = settings.EngineMode,
            exit_code = exitCode,
            os = OperatingSystemDescription(),
            architecture = RuntimeInformation.ProcessArchitecture.ToString(),
            dotnet_runtime = RuntimeInformation.FrameworkDescription,
            hardware = hardwareInventory ?? HardwareInventory.Capture(),
            failure_summary = failureSummary,
            settings = ReportSettings(settings),
            packs = packs.Select(pack => new { pack.Id, pack.Version, pack.SchemaVersion, pack.IsEnabled, pack.Priority }).ToArray(),
            note = "Review this local report before sharing. It includes selected settings, pack metadata, a limited hardware inventory and redacted log tails."
        };
        var sessionLogs = ReadSessionLogs(launchLog, roots);
        var temporary = destination + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var zip = ZipFile.Open(temporary, ZipArchiveMode.Create))
            {
                void AddRaw(string name, string redactedContent)
                {
                    using var writer = new StreamWriter(zip.CreateEntry(name, CompressionLevel.Optimal).Open(), Encoding.UTF8);
                    writer.Write(redactedContent);
                }
                AddRaw("report.json", Redact(JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }), roots));
                foreach (var (wireKey, zipName, _) in SessionLogMappings)
                {
                    if (sessionLogs.TryGetValue(wireKey, out var content) && !string.IsNullOrEmpty(content))
                        AddRaw(zipName, content);
                }
            }
            File.Move(temporary, destination, overwrite: true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
}
