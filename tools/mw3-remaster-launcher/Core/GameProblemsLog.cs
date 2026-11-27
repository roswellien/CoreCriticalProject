using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// Reads the line formats the game prints for reports: its periodic "mw3: health" lines in
/// mw3.log, and its problems log. Keeping every reader of those formats here keeps the
/// game-format contract in one file.
/// </summary>
/// <remarks>
/// The problems log (native/mw3-problems.log in a session) holds one problem per line, in the
/// format the game must print: <c>[&lt;seconds since launch&gt;] &lt;W|E&gt; &lt;text&gt;</c>, for
/// example <c>[12.5] E texture upload failed</c>. W is a warning, E an error. Lines in any
/// other shape are ignored.
/// </remarks>
public static class GameProblemsLog
{
    public const string HealthMarker = "mw3: health";

    /// <summary>One parsed problems-log line.</summary>
    public sealed record Problem(double SecondsSinceLaunch, char Level, string Text, string Line);

    private static readonly Regex ProblemLine = new(
        @"\A\[(?<seconds>[0-9]{1,9}(?:\.[0-9]{1,6})?)\] (?<level>[WE]) (?<text>.+)\z",
        RegexOptions.CultureInvariant);

    /// <summary>The line parsed, or null when it isn't in the problems-log format.</summary>
    public static Problem? Parse(string line)
    {
        var trimmed = line.Trim();
        var match = ProblemLine.Match(trimmed);
        if (!match.Success) return null;
        var seconds = double.Parse(match.Groups["seconds"].Value, CultureInfo.InvariantCulture);
        var text = match.Groups["text"].Value.Trim();
        if (text.Length == 0) return null;
        return new Problem(seconds, match.Groups["level"].Value[0], text, trimmed);
    }

    /// <summary>
    /// The W and E lines of the session's problems log stamped at or after the first frame.
    /// None without a first frame, a file or such a line, so startup noise never prompts.
    /// </summary>
    public static IReadOnlyList<string> PlayProblems(string sessionDirectory, long? firstFrameMilliseconds)
    {
        if (firstFrameMilliseconds is not { } firstFrame) return Array.Empty<string>();
        var firstFrameSeconds = firstFrame / 1000.0;
        return ReadProblems(sessionDirectory)
            .Where(problem => problem.SecondsSinceLaunch >= firstFrameSeconds)
            .Select(problem => problem.Line)
            .ToList();
    }

    /// <summary>
    /// The text of the problems log's first E line, else its first W line, without the stamp
    /// and level; null when there is none. Reports after a clean exit are grouped by it.
    /// </summary>
    public static string? FirstProblemSummary(string sessionDirectory)
    {
        var problems = ReadProblems(sessionDirectory);
        var first = problems.FirstOrDefault(problem => problem.Level == 'E') ??
            problems.FirstOrDefault(problem => problem.Level == 'W');
        return first?.Text;
    }

    private static List<Problem> ReadProblems(string sessionDirectory)
    {
        var path = Path.Combine(sessionDirectory, "native", PlaytestDiagnostics.NativeProblemsFileName);
        string text;
        try { text = PlaytestDiagnostics.ReadWholeLog(path); }
        catch { return new List<Problem>(); }
        var problems = new List<Problem>();
        foreach (var line in text.Split('\n'))
        {
            var problem = Parse(line);
            if (problem != null) problems.Add(problem);
        }
        return problems;
    }

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
