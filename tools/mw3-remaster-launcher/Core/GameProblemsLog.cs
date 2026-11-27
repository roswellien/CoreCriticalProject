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

    private static readonly Regex Stamp = new(
        @"\A\[[0-9]{1,9}(?:\.[0-9]{1,6})?\] [IWE] ", RegexOptions.CultureInvariant);

    /// <summary>
    /// The line without the game's leading time and level stamp (<c>[12.345] I </c>), which the game
    /// puts on every mw3.log line; lines without one come back unchanged.
    /// </summary>
    public static string WithoutStamp(string line) => Stamp.Replace(line, "", 1);

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

    private const string FirstFrameMarker = "mw3: first frame shown ";
    private static readonly Regex StampedLine = new(
        @"\A\[(?<seconds>[0-9]{1,9}(?:\.[0-9]{1,6})?)\] [IWE] (?<text>.*)\z", RegexOptions.CultureInvariant);

    /// <summary>
    /// The W and E lines of the session's problems log stamped at or after the first frame.
    /// The first frame is the game's own "first frame shown" line in that log, on the same clock as
    /// the problems; a game too old to write it falls back to <paramref name="launcherFirstFrameMilliseconds"/>,
    /// when the launcher noticed the ready file. None without a first frame, a file or such a line,
    /// so startup noise never prompts.
    /// </summary>
    public static IReadOnlyList<string> PlayProblems(string sessionDirectory, long? launcherFirstFrameMilliseconds)
    {
        var log = ReadProblems(sessionDirectory);
        var cutoff = log.FirstFrameSeconds ?? launcherFirstFrameMilliseconds / 1000.0;
        if (cutoff is not { } firstFrameSeconds) return Array.Empty<string>();
        return log.Problems
            .Where(problem => problem.SecondsSinceLaunch >= firstFrameSeconds)
            .Select(problem => problem.Line)
            .ToList();
    }

    /// <summary>
    /// The text of the first E line, else the first W line, from play (after the game's first frame,
    /// as the prompt counts them), without the stamp and level; with none from play, the same from
    /// the whole log; null when there is none. Reports after a clean exit are titled and grouped by it.
    /// </summary>
    public static string? FirstProblemSummary(string sessionDirectory)
    {
        var log = ReadProblems(sessionDirectory);
        var fromPlay = log.FirstFrameSeconds is { } firstFrame
            ? log.Problems.Where(problem => problem.SecondsSinceLaunch >= firstFrame).ToList()
            : log.Problems;
        var problems = fromPlay.Count > 0 ? fromPlay : log.Problems;
        var first = problems.FirstOrDefault(problem => problem.Level == 'E') ??
            problems.FirstOrDefault(problem => problem.Level == 'W');
        return first?.Text;
    }

    private sealed record ProblemsLog(List<Problem> Problems, double? FirstFrameSeconds);

    private static ProblemsLog ReadProblems(string sessionDirectory)
    {
        var path = Path.Combine(sessionDirectory, "native", PlaytestDiagnostics.NativeProblemsFileName);
        string text;
        try { text = PlaytestDiagnostics.ReadWholeLog(path); }
        catch { return new ProblemsLog(new List<Problem>(), null); }
        var problems = new List<Problem>();
        double? firstFrame = null;
        foreach (var line in text.Split('\n'))
        {
            var problem = Parse(line);
            if (problem != null) problems.Add(problem);
            if (firstFrame == null && StampedLine.Match(line.Trim()) is { Success: true } stamped &&
                stamped.Groups["text"].Value.StartsWith(FirstFrameMarker, StringComparison.Ordinal))
                firstFrame = double.Parse(stamped.Groups["seconds"].Value, CultureInfo.InvariantCulture);
        }
        return new ProblemsLog(problems, firstFrame);
    }

    /// <summary>
    /// The last <paramref name="count"/> lines of the log text that contain "mw3: health",
    /// oldest first.
    /// </summary>
    public static IReadOnlyList<string> LastHealthLines(string text, int count)
    {
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
