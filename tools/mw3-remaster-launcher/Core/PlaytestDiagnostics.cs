using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Export a small local support bundle, using an explicit allowlist of metadata and log tails.</summary>
public static class PlaytestDiagnostics
{
    public const int MaxLogBytes = 64 * 1024;

    public static object CreateCrashReport(LauncherSettings settings, IEnumerable<PackManifest> packs,
        string? launchLog, string applicationRoot, string? runtimeVersion = null, int? exitCode = null,
        HardwareInventoryData? hardwareInventory = null)
    {
        var roots = new[] { applicationRoot, GameRunner.FindRepositoryRoot(applicationRoot) ?? "", settings.GamePath,
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), LauncherPaths.DataRoot };
        var logs = new Dictionary<string, string>();
        if (launchLog != null)
        {
            var folder = Path.GetDirectoryName(launchLog)!;
            foreach (var (name, path) in new[] { ("launcher", launchLog),
                ("native_stderr", Path.Combine(folder, "native", "stderr.txt")),
                ("native_stdout", Path.Combine(folder, "native", "stdout.txt")) })
                if (File.Exists(path)) logs[name] = Redact(ReadTail(path), roots);
        }
        var failureSummary = Redact(FailureSummary(launchLog), roots);
        if (failureSummary.Length > 2000) failureSummary = failureSummary[..2000];

        return new
        {
            format_version = 1,
            report_id = Guid.NewGuid().ToString("N"),
            created_utc = DateTimeOffset.UtcNow,
            launcher_version = typeof(GameRunner).Assembly.GetName().Version?.ToString(),
            runtime_version = runtimeVersion ?? "unknown",
            mode = settings.EngineMode,
            exit_code = exitCode,
            os = RuntimeInformation.OSDescription,
            architecture = RuntimeInformation.ProcessArchitecture.ToString(),
            dotnet_runtime = RuntimeInformation.FrameworkDescription,
            hardware = hardwareInventory ?? HardwareInventory.Capture(),
            failure_summary = failureSummary,
            settings = settings.EngineMode == "d7vk"
                ? (object)new { settings.D7VkResolution, settings.D7VkAntiAliasing,
                    settings.D7VkAnisotropicFiltering, settings.D7VkAiTextures }
                : new { settings.Width, settings.Height, settings.WindowMode, settings.AntiAliasing,
                    settings.AnisotropicFiltering, settings.DrawDistance, settings.FogDistance,
                    settings.LocalCdAudio, settings.InstantReplay, settings.PerformanceMonitor },
            packs = packs.Select(pack => new { pack.Id, pack.Version, pack.SchemaVersion, pack.IsEnabled, pack.Priority }).ToArray(),
            logs
        };
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

    public static string FailureSummary(string? launchLog)
    {
        if (launchLog == null) return "No launch details were recorded.";
        var directory = Path.GetDirectoryName(launchLog)!;
        foreach (var file in new[] { Path.Combine(directory, "native", "stderr.txt"), launchLog })
        {
            var lines = ReadTail(file).Split('\n', StringSplitOptions.RemoveEmptyEntries);
            var error = lines.LastOrDefault(line => line.StartsWith("ERROR:", StringComparison.Ordinal) ||
                line.StartsWith("[D7VK ERR]", StringComparison.Ordinal) ||
                line.Contains("loader-order entry fault:", StringComparison.Ordinal) ||
                line.Contains("Unhandled exception", StringComparison.OrdinalIgnoreCase) ||
                line.Contains("Fatal error", StringComparison.OrdinalIgnoreCase));
            if (error != null) return error.Trim();
        }
        return "The launch or game ended unexpectedly. Open Logs for details.";
    }

    public static string Redact(string text, params string[] privateRoots)
    {
        // Replace complete path tokens before substituting known roots, or a
        // replaced root prefix could leave the remainder of a path visible.
        text = Regex.Replace(text, @"\b[A-Za-z]:[\\/][^\r\n\t\""<>|]*", "<local-path>");
        text = Regex.Replace(text, @"\\\\[^\s\""<>|]+", "<network-path>");
        foreach (var root in privateRoots.Where(root => !string.IsNullOrWhiteSpace(root)).OrderByDescending(root => root.Length))
        {
            text = text.Replace(root, "<local-path>", StringComparison.OrdinalIgnoreCase);
            text = text.Replace(root.Replace('\\', '/'), "<local-path>", StringComparison.OrdinalIgnoreCase);
        }
        return text;
    }

    public static void Export(string destination, LauncherSettings settings, IEnumerable<PackManifest> packs,
        string? launchLog, string applicationRoot, HardwareInventoryData? hardwareInventory = null)
    {
        // No profiles, settings files, saves, archives, media, dumps or recursive directory walks.
        var report = new
        {
            format_version = 1,
            created_utc = DateTimeOffset.UtcNow,
            launcher_version = typeof(GameRunner).Assembly.GetName().Version?.ToString(),
            os = RuntimeInformation.OSDescription,
            architecture = RuntimeInformation.ProcessArchitecture.ToString(),
            dotnet_runtime = RuntimeInformation.FrameworkDescription,
            hardware = hardwareInventory ?? HardwareInventory.Capture(),
            settings = new { settings.EngineMode, settings.Width, settings.Height, settings.WindowMode,
                settings.AntiAliasing, settings.AnisotropicFiltering, settings.DrawDistance, settings.FogDistance,
                settings.LocalCdAudio, settings.InstantReplay, settings.PerformanceMonitor },
            packs = packs.Select(pack => new { pack.Id, pack.Version, pack.SchemaVersion, pack.IsEnabled, pack.Priority }).ToArray(),
            note = "Review this local report before sharing. It includes selected settings, pack metadata, a limited hardware inventory and redacted log tails."
        };
        var roots = new[] { applicationRoot, GameRunner.FindRepositoryRoot(applicationRoot) ?? "", settings.GamePath,
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), LauncherPaths.DataRoot };
        var temporary = destination + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var zip = ZipFile.Open(temporary, ZipArchiveMode.Create))
            {
                void Add(string name, string content)
                {
                    using var writer = new StreamWriter(zip.CreateEntry(name, CompressionLevel.Optimal).Open(), Encoding.UTF8);
                    writer.Write(Redact(content, roots));
                }
                Add("report.json", JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
                if (launchLog != null)
                {
                    var folder = Path.GetDirectoryName(launchLog)!;
                    foreach (var (name, path) in new[] { ("launcher.log", launchLog),
                        ("native-stderr.txt", Path.Combine(folder, "native", "stderr.txt")),
                        ("native-stdout.txt", Path.Combine(folder, "native", "stdout.txt")) })
                        if (File.Exists(path)) Add(name, ReadTail(path));
                }
            }
            File.Move(temporary, destination, overwrite: true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
}
