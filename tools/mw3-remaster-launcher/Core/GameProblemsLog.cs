namespace MW3RemasterLauncher.Core;

/// <summary>
/// Reads the line formats the game prints for reports: its periodic "mw3: health" lines in
/// mw3.log, and its problems log. Keeping every reader of those formats here keeps the
/// game-format contract in one file.
/// </summary>
public static class GameProblemsLog
{
    public const string HealthMarker = "mw3: health";

    /// <summary>
    /// The last <paramref name="count"/> lines of the whole log that contain "mw3: health",
    /// oldest first; none when the file is missing or unreadable.
    /// </summary>
    public static IReadOnlyList<string> LastHealthLines(string path, int count)
    {
        string text;
        try { text = PlaytestDiagnostics.ReadWholeLog(path); }
        catch { return Array.Empty<string>(); }

        var lastLines = new Queue<string>();
        foreach (var line in text.Split('\n'))
        {
            if (!line.Contains(HealthMarker, StringComparison.Ordinal)) continue;
            lastLines.Enqueue(line.TrimEnd('\r'));
            if (lastLines.Count > count) lastLines.Dequeue();
        }
        return lastLines.ToArray();
    }
}
