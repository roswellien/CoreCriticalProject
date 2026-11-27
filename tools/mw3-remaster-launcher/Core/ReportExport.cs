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
        string? runtimeVersion = null, int? exitCode = null, IReadOnlyDictionary<string, object>? header = null)
    {
        // No profiles, settings files, saves, archives, media, dumps or recursive directory walks.
        var roots = PlaytestDiagnostics.ReportRoots(settings, applicationRoot);
        var failureSummary = PlaytestDiagnostics.Redact(PlaytestDiagnostics.FailureSummary(launchLog, exitCode), roots);
        if (failureSummary.Length > 2000) failureSummary = failureSummary[..2000];
        var report = PlaytestDiagnostics.StartPayload(header);
        report["created_utc"] = DateTimeOffset.UtcNow;
        report["launcher_version"] = PlaytestDiagnostics.LauncherVersionString();
        report["runtime_version"] = runtimeVersion ?? "unknown";
        report["mode"] = settings.EngineMode;
        report["exit_code"] = exitCode;
        report["os"] = PlaytestDiagnostics.OperatingSystemDescription();
        report["architecture"] = RuntimeInformation.ProcessArchitecture.ToString();
        report["dotnet_runtime"] = RuntimeInformation.FrameworkDescription;
        report["hardware"] = hardwareInventory ?? HardwareInventory.Capture();
        report["failure_summary"] = failureSummary;
        report["settings"] = PlaytestDiagnostics.ReportSettings(settings);
        report["packs"] = packs.Select(pack => new { pack.Id, pack.Version, pack.SchemaVersion, pack.IsEnabled, pack.Priority }).ToArray();
        report["note"] = "Review this local report before sharing. It includes selected settings, pack metadata, a limited hardware inventory, a setup header and the whole redacted game and launcher logs, unless a log was cut to fit the 19 MB export.";
        var reportJson = PlaytestDiagnostics.Redact(
            JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }), roots);
        var logs = ReadWholeSessionLogs(launchLog, roots);
        WriteZipWithinLimit(destination, reportJson, logs);
    }

    /// <summary>Each mapped session log, whole and redacted, keyed by its zip entry name.</summary>
    private static List<(string ZipName, string Text)> ReadWholeSessionLogs(string? launchLog, string[] roots)
    {
        var logs = new List<(string ZipName, string Text)>();
        var folder = PlaytestDiagnostics.SessionFolder(launchLog);
        if (launchLog == null || folder == null) return logs;

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
    /// Writes the zip; while it is over the limit, cuts logs to their first 1 MB, the cut marker
    /// and a shorter end, then writes it again. The first zip's compression ratio estimates how
    /// far to cut, so each rewrite is usually the last. The largest log's end halves until the
    /// estimate fits; a log is never dropped whole. If the attempts run out, every log over
    /// 1 MB keeps only a short end, which always fits (seven logs of about 1 MB each).
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
                var zipBytes = new FileInfo(temporary).Length;
                if (zipBytes <= MaxExportZipBytes || logs.Count == 0) break;
                if (attempt >= MaxCutAttempts)
                {
                    CutEveryLargeLog(logs, originals, tailChars);
                    WriteZip(temporary, reportJson, logs);
                    break;
                }

                // Aim 10% under the limit, at this zip's bytes per character.
                var bytesPerChar = (double)zipBytes / Math.Max(1, TotalChars(reportJson, logs));
                var targetChars = (long)(MaxExportZipBytes * 0.9 / bytesPerChar);
                while (TotalChars(reportJson, logs) > targetChars && HalveLargestTail(logs, originals, tailChars)) { }
            }
            File.Move(temporary, destination, overwrite: true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    private static long TotalChars(string reportJson, List<(string ZipName, string Text)> logs) =>
        reportJson.Length + logs.Sum(log => (long)log.Text.Length);

    /// <summary>Halves the kept end of the largest log that can still be cut; false when none can.</summary>
    private static bool HalveLargestTail(List<(string ZipName, string Text)> logs,
        Dictionary<string, string> originals, Dictionary<string, int> tailChars)
    {
        var candidates = logs
            .Select((log, index) => (log.ZipName, log.Text.Length, Index: index))
            .Where(log => originals[log.ZipName].Length > KeptLogHeadChars &&
                (!tailChars.TryGetValue(log.ZipName, out var kept) || kept > 0))
            .OrderByDescending(log => log.Length)
            .ToList();
        if (candidates.Count == 0) return false;
        var largest = candidates[0];
        var original = originals[largest.ZipName];
        var remaining = original.Length - KeptLogHeadChars;
        var previousTail = tailChars.TryGetValue(largest.ZipName, out var tail) ? tail : remaining;
        var nextTail = previousTail / 2;
        tailChars[largest.ZipName] = nextTail;
        logs[largest.Index] = (largest.ZipName, CutLog(original, nextTail));
        return true;
    }

    private const int LastResortTailChars = 64 * 1024;

    private static void CutEveryLargeLog(List<(string ZipName, string Text)> logs, Dictionary<string, string> originals,
        Dictionary<string, int> tailChars)
    {
        for (var index = 0; index < logs.Count; index++)
        {
            var name = logs[index].ZipName;
            var original = originals[name];
            if (original.Length <= KeptLogHeadChars) continue;
            // Never longer than a tail the halving already chose.
            var tail = tailChars.TryGetValue(name, out var kept) ? Math.Min(kept, LastResortTailChars) : LastResortTailChars;
            logs[index] = (name, CutLog(original, tail));
        }
    }

    /// <summary>The log's first 1 MB and its last <paramref name="tailChars"/>, each on a line boundary.</summary>
    public static string CutLog(string text, int tailChars)
    {
        if (text.Length <= KeptLogHeadChars) return text;
        var head = text[..KeptLogHeadChars];
        var lastHeadNewline = head.LastIndexOf('\n');
        if (lastHeadNewline >= 0) head = head[..(lastHeadNewline + 1)];
        // From the head's own end, so a tail reaching back that far starts on a whole line.
        var tail = UploadLogCuts.SliceTailOnLineBoundary(text[head.Length..], tailChars);
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
