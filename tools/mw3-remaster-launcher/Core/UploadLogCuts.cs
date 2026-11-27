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
    /// The game log for the upload: its start and end, led by the last health lines of the
    /// whole session log that the cut dropped (a long session's middle). Both come from one
    /// read of the redacted whole log.
    /// </summary>
    public static string WithLastHealthLines(string redactedRunLog, int maxChars)
    {
        var healthLines = GameProblemsLog.LastHealthLines(redactedRunLog, HealthLinesInUpload);
        var fullBlockLength = HealthLinesHeading.Length + healthLines.Sum(line => line.Length + 1);
        var blockFits = healthLines.Count > 0 && fullBlockLength < maxChars / 2;
        var room = blockFits ? maxChars - fullBlockLength : maxChars;
        var kept = CutHeadAndTail(redactedRunLog, room);
        if (!blockFits) return kept;

        var droppedLines = healthLines.Where(line => !kept.Contains(line, StringComparison.Ordinal)).ToList();
        if (droppedLines.Count == 0) return kept;
        return HealthLinesHeading + string.Join("\n", droppedLines) + "\n" + kept;
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
