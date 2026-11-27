using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// Export Report: a local zip of report.json and the session's whole, redacted logs, for the
/// player to review and share by hand. Unlike the 256 KB crash upload, logs stay uncut unless
/// the zip would pass <see cref="MaxExportZipBytes"/>.
/// </summary>
public static class ReportExport
{
    /// <summary>Kept under common 20 MB attachment limits (Discord, email).</summary>
    public const long MaxExportZipBytes = 19 * 1024 * 1024;

    /// <summary>A cut log always keeps this much of its start, where startup and the first fault are.</summary>
    public const int KeptLogHeadChars = 1024 * 1024;

    public const string CutMarker = "... (cut to fit the 19 MB export) ...";

    private const int MaxCutAttempts = 8;

    public static void Export(string destination, LauncherSettings settings, IEnumerable<PackManifest> packs,
        string? launchLog, string applicationRoot, HardwareInventoryData? hardwareInventory = null,
        string? runtimeVersion = null, int? exitCode = null)
    {
        // No profiles, settings files, saves, archives, media, dumps or recursive directory walks.
        var roots = new[] { applicationRoot, GameRunner.FindRepositoryRoot(applicationRoot) ?? "", settings.GamePath,
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), LauncherPaths.DataRoot };
        var failureSummary = PlaytestDiagnostics.Redact(PlaytestDiagnostics.FailureSummary(launchLog, exitCode), roots);
        if (failureSummary.Length > 2000) failureSummary = failureSummary[..2000];
        var report = new
        {
            format_version = 1,
            created_utc = DateTimeOffset.UtcNow,
            launcher_version = PlaytestDiagnostics.LauncherVersionString(),
            runtime_version = runtimeVersion ?? "unknown",
            mode = settings.EngineMode,
            exit_code = exitCode,
            os = PlaytestDiagnostics.OperatingSystemDescription(),
            architecture = RuntimeInformation.ProcessArchitecture.ToString(),
            dotnet_runtime = RuntimeInformation.FrameworkDescription,
            hardware = hardwareInventory ?? HardwareInventory.Capture(),
            failure_summary = failureSummary,
            settings = PlaytestDiagnostics.ReportSettings(settings),
            packs = packs.Select(pack => new { pack.Id, pack.Version, pack.SchemaVersion, pack.IsEnabled, pack.Priority }).ToArray(),
            note = "Review this local report before sharing. It includes selected settings, pack metadata, a limited hardware inventory and the whole redacted game and launcher logs, unless a log was cut to fit the 19 MB export."
        };
        var reportJson = PlaytestDiagnostics.Redact(
            JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }), roots);
        var logs = ReadWholeSessionLogs(launchLog, roots);
        WriteZipWithinLimit(destination, reportJson, logs);
    }

    /// <summary>Each mapped session log, whole and redacted, keyed by its zip entry name.</summary>
    private static List<(string ZipName, string Text)> ReadWholeSessionLogs(string? launchLog, string[] roots)
    {
        var logs = new List<(string ZipName, string Text)>();
        if (launchLog == null) return logs;
        string? folder;
        try { folder = Path.GetDirectoryName(launchLog); }
        catch { return logs; }
        if (string.IsNullOrEmpty(folder)) return logs;

        foreach (var (_, zipName, relativePath, _) in PlaytestDiagnostics.SessionLogMappings)
        {
            string text;
            try
            {
                var path = PlaytestDiagnostics.SessionLogPath(launchLog, folder, relativePath);
                text = PlaytestDiagnostics.Redact(PlaytestDiagnostics.ReadWholeLog(path), roots);
            }
            catch { continue; }
            if (text.Length > 0) logs.Add((zipName, text));
        }
        return logs;
    }

    /// <summary>
    /// Writes the zip, and while it is over the limit cuts the largest log to its first 1 MB,
    /// the cut marker and a shorter end each time, then writes it again. The end starts at the
    /// log's remaining length and halves on each try, so a log is never dropped whole.
    /// </summary>
    private static void WriteZipWithinLimit(string destination, string reportJson, List<(string ZipName, string Text)> logs)
    {
        var originals = logs.ToDictionary(log => log.ZipName, log => log.Text);
        var tailChars = new Dictionary<string, int>();
        var temporary = destination + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            for (var attempt = 0; ; attempt++)
            {
                WriteZip(temporary, reportJson, logs);
                var fits = new FileInfo(temporary).Length <= MaxExportZipBytes;
                if (fits || attempt >= MaxCutAttempts || logs.Count == 0) break;

                var largest = logs
                    .Select((log, index) => (log.ZipName, log.Text.Length, Index: index))
                    .OrderByDescending(log => log.Length)
                    .First();
                var original = originals[largest.ZipName];
                var remaining = Math.Max(0, original.Length - KeptLogHeadChars);
                if (remaining == 0) break; // Every log is already down to its first 1 MB.
                var previousTail = tailChars.TryGetValue(largest.ZipName, out var tail) ? tail : remaining;
                tailChars[largest.ZipName] = previousTail / 2;
                logs[largest.Index] = (largest.ZipName, CutLog(original, previousTail / 2));
            }
            File.Move(temporary, destination, overwrite: true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    /// <summary>The log's first 1 MB and its last <paramref name="tailChars"/>, each on a line boundary.</summary>
    internal static string CutLog(string text, int tailChars)
    {
        if (text.Length <= KeptLogHeadChars) return text;
        var head = text[..KeptLogHeadChars];
        var lastHeadNewline = head.LastIndexOf('\n');
        if (lastHeadNewline >= 0) head = head[..(lastHeadNewline + 1)];
        var tail = PlaytestDiagnostics.SliceTailOnLineBoundary(text[KeptLogHeadChars..], tailChars);
        return head + CutMarker + "\n" + tail;
    }

    private static void WriteZip(string path, string reportJson, List<(string ZipName, string Text)> logs)
    {
        if (File.Exists(path)) File.Delete(path);
        using var zip = ZipFile.Open(path, ZipArchiveMode.Create);
        void AddEntry(string name, string content)
        {
            using var writer = new StreamWriter(zip.CreateEntry(name, CompressionLevel.Optimal).Open(), Encoding.UTF8);
            writer.Write(content);
        }
        AddEntry("report.json", reportJson);
        foreach (var (zipName, text) in logs) AddEntry(zipName, text);
    }
}
