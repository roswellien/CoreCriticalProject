using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>
/// The wording of the question asked before a playtest report is sent, and of its result.
/// <see cref="AlwaysAsk"/> asks even when automatic reports are on.
/// </summary>
internal sealed record ReportPrompt(string Title, string Summary, bool AlwaysAsk, string SentTitle, string NotSentTitle)
{
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
            AlwaysAsk: false, "Crash report sent", "Crash report not sent");
    }

    /// <summary>
    /// After a clean exit with problems during play. Nothing is sent without Yes, even with
    /// automatic reports on, because the player saw no failure.
    /// </summary>
    public static ReportPrompt ForProblems(int problemCount, string? launchLog)
    {
        var first = PlaytestDiagnostics.FailureSummary(launchLog, 0);
        var problems = problemCount == 1 ? "1 problem" : $"{problemCount} problems";
        return new ReportPrompt("MW3-RE reported problems",
            $"The game closed normally but logged {problems} during play, the first: {first}",
            AlwaysAsk: true, "Problem report sent", "Problem report not sent");
    }
}
