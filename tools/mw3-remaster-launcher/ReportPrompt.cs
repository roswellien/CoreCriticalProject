using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>
/// The wording of the question asked before a playtest report is sent, and of its result.
/// <see cref="AlwaysAsk"/> asks even when automatic reports are on. <see cref="NotSentMessage"/>
/// opens the message shown when sending fails.
/// </summary>
public sealed record ReportPrompt(string Title, string Summary, bool AlwaysAsk, string SentTitle,
    string NotSentTitle, string NotSentMessage)
{
    /// <summary>The dialog shows at most this much of a problem line; the report keeps it all.</summary>
    public const int MaxShownProblemChars = 300;

    /// <summary>After a crash or failed exit: sent without asking when automatic reports are on.</summary>
    public static ReportPrompt ForCrash(LauncherSettings settings, int exitCode, string? launchLog)
    {
        var summary = PlaytestDiagnostics.FailureSummary(launchLog, exitCode);
        var engineTitle = settings.EngineMode == "d7vk" ? "Original Game (D7VK)" : "MW3-RE";
        var exitStatus = PlaytestDiagnostics.FormatExitCode(exitCode);
        var dialogSummary = summary == PlaytestDiagnostics.GenericFailureSummary
            ? $"{summary} Exit code: {exitStatus}."
            : summary;
        return new ReportPrompt($"{engineTitle} stopped (exit {exitStatus})", dialogSummary,
            AlwaysAsk: false, "Crash report sent", "Crash report not sent",
            "The crash report could not be sent.");
    }

    /// <summary>
    /// After a clean exit with problems during play (<paramref name="playProblems"/>, from
    /// GameProblemsLog.PlayProblems). Nothing is sent without Yes, even with automatic reports
    /// on, because the player saw no failure. The dialog names the first counted problem.
    /// </summary>
    public static ReportPrompt ForProblems(IReadOnlyList<string> playProblems)
    {
        var firstLine = playProblems.Count > 0 ? playProblems[0] : "";
        var first = GameProblemsLog.Parse(firstLine)?.Text ?? firstLine;
        if (first.Length > MaxShownProblemChars) first = first[..MaxShownProblemChars] + "...";
        var problems = playProblems.Count == 1 ? "1 problem" : $"{playProblems.Count} problems";
        return new ReportPrompt("MW3-RE reported problems",
            $"The game closed normally but logged {problems} during play, the first: {first}",
            AlwaysAsk: true, "Problem report sent", "Problem report not sent",
            "The problem report could not be sent.");
    }
}
