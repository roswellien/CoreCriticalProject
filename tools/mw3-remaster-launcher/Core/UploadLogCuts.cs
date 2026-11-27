namespace MW3RemasterLauncher.Core;

/// <summary>
/// How each log is cut to fit the 256 KB crash upload: which part of it survives depends on
/// where that log keeps the lines that explain a failure.
/// </summary>
internal static class UploadLogCuts
{
    private const int HealthLinesInUpload = 20;
    private const string HealthLinesHeading = "Last health lines:\n";

    /// <summary>
    /// The game log for the upload, led by the last health lines from the whole session log,
    /// since the head-and-tail cut can drop the ones from the middle of a long session.
    /// </summary>
    public static string WithLastHealthLines(string runLogPath, string runLogText, int maxChars, string[] roots)
    {
        var healthLines = GameProblemsLog.LastHealthLines(runLogPath, HealthLinesInUpload);
        var healthBlock = healthLines.Count == 0
            ? ""
            : PlaytestDiagnostics.Redact(HealthLinesHeading + string.Join("\n", healthLines) + "\n", roots);
        if (healthBlock.Length >= maxChars / 2) healthBlock = "";
        var room = maxChars - healthBlock.Length;
        var log = runLogText.Length > room ? CutHeadAndTail(runLogText, room) : runLogText;
        return healthBlock + log;
    }

    /// <summary>
    /// The problems log and game log keep their start and end, so the first error that started
    /// the trouble survives; the crash record keeps its start; other logs keep their end.
    /// </summary>
    public static string CutLog(string wireKey, string text, int maxChars) => wireKey switch
    {
        "native_crash" => text[..Math.Min(text.Length, maxChars)],
        "native_run" or "native_problems" => CutHeadAndTail(text, maxChars),
        _ => SliceTailOnLineBoundary(text, maxChars)
    };

    /// <summary>The text's start (up to 12 KB, on a line boundary), "...", and as much of its end as fits.</summary>
    public static string CutHeadAndTail(string text, int maxChars)
    {
        const string marker = "...\n";
        if (text.Length <= maxChars) return text;
        if (maxChars <= marker.Length) return SliceTailOnLineBoundary(text, maxChars);
        var headBudget = Math.Min(12 * 1024, maxChars / 4);
        var head = text[..headBudget];
        var lastHeadNewline = head.LastIndexOf('\n');
        head = lastHeadNewline >= 0 ? head[..(lastHeadNewline + 1)] : "";
        var tail = SliceTailOnLineBoundary(text[head.Length..], maxChars - head.Length - marker.Length);
        return head + marker + tail;
    }

    /// <summary>At most the last <paramref name="maxChars"/>, starting after a line break when one is in reach.</summary>
    public static string SliceTailOnLineBoundary(string text, int maxChars)
    {
        if (text.Length <= maxChars) return text;
        var sliced = text[^maxChars..];
        var newline = sliced.IndexOf('\n');
        return newline >= 0 && newline + 1 < sliced.Length ? sliced[(newline + 1)..] : sliced;
    }
}
