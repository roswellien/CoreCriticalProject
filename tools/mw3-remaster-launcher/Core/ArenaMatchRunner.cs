using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Parsed outcome of one completed AI Arena match.</summary>
public sealed record ArenaMatchOutcome(
    bool Succeeded,
    int ExitCode,
    int ResolvedSeed,
    string? Winner,
    string? TimeText,
    int LostA,
    int LostB,
    string? ErrorMessage,
    string RunFolder,
    string SetupJsonPath,
    string ExpectedLogPath,
    string CommandLine)
{
    public string WinnerDisplayLabel => Winner switch
    {
        "A" => "Side A wins",
        "B" => "Side B wins",
        "draw" => "Draw",
        _ => "No result"
    };

    public string SummaryLine => Succeeded
        ? $"{WinnerDisplayLabel} — Time {TimeText}, Lost: Side A {LostA}, Side B {LostB} (seed {ResolvedSeed})"
        : (ErrorMessage ?? $"Match failed (exit {ExitCode}).");
}

/// <summary>
/// Prepares per-run AI Arena folders, builds <c>mw3 --arena</c> arguments, launches matches
/// through <see cref="NativeGameRunner"/>, and parses match outcomes from stdout or the match log.
/// </summary>
public static class ArenaMatchRunner
{
    private static readonly Regex StdoutResultPattern = new(
        @"(?:^|\b)arena:\s*winner\s+(?<winner>A|B|draw),\s*time\s+(?<time>\d+:\d{2}),\s*lost\s+A\s+(?<lostA>\d+)\s+B\s+(?<lostB>\d+)\b",
        RegexOptions.CultureInvariant);

    private static readonly Regex LauncherElapsedSuffix = new(
        @"\s+\[launcher elapsed \d+ ms\]\s*$",
        RegexOptions.CultureInvariant);

    /// <summary>Default parent folder for arena match runs: <c>&lt;dataRoot&gt;/arena/runs</c>.</summary>
    public static string DefaultLogsRoot(string dataRoot) =>
        Path.Combine(Path.GetFullPath(dataRoot), "arena", "runs");

    /// <summary>
    /// Build the extra command-line arguments appended to the planned MW3-RE launch for an arena match.
    /// </summary>
    public static IReadOnlyList<string> BuildArguments(string setupJsonPath, int resolvedSeed, int frameMs, bool hidden)
    {
        if (string.IsNullOrWhiteSpace(setupJsonPath))
            throw new ArgumentException("A setup.json path is required.", nameof(setupJsonPath));
        if (resolvedSeed < ArenaSetup.MinSeed)
            throw new ArgumentOutOfRangeException(nameof(resolvedSeed), "Arena seed must be between 0 and 2147483647.");
        if (frameMs <= 0)
            throw new ArgumentOutOfRangeException(nameof(frameMs), "Arena frame_ms must be positive.");

        var arguments = new List<string>(8)
        {
            "--arena",
            setupJsonPath,
            "--seed",
            resolvedSeed.ToString(),
            "--frame-ms",
            frameMs.ToString()
        };
        if (hidden)
            arguments.Add("--hidden");
        arguments.Add("-nofmv");
        return arguments;
    }

    /// <summary>
    /// Build the extra command-line arguments appended to the planned MW3-RE launch for a 3D replay.
    /// </summary>
    public static IReadOnlyList<string> BuildReplay3dArguments(string matchLogPath)
    {
        if (string.IsNullOrWhiteSpace(matchLogPath))
            throw new ArgumentException("A match log path is required.", nameof(matchLogPath));
        return new[] { "--replay3d", matchLogPath };
    }

    /// <summary>
    /// Format the graphics summary shown in the AI Arena window for watched vs. hidden runs.
    /// </summary>
    public static string FormatGraphicsSummary(LauncherSettings settings, IEnumerable<string> activeModDirs, bool hidden)
    {
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(activeModDirs);

        if (hidden)
            return "Hidden matches draw nothing; graphics settings don't apply.";

        var drawDistance = NativeGameRunner.PreviewDrawDistance(settings.DrawDistance, out _);
        var (models, environments) = NativeGameRunner.SelectPreviewPacks(activeModDirs);
        return $"Graphics: your current Play settings ({settings.Width}x{settings.Height}, scenery {drawDistance}, {models.Count} model pack(s), {environments.Count} map pack(s)).";
    }

    /// <summary>
    /// Create a unique timestamped run folder (<c>&lt;logsRoot&gt;/&lt;yyyyMMdd-HHmmss&gt;</c>, with
    /// a numeric suffix if another run started in the same second) and write <c>setup.json</c>.
    /// </summary>
    public static (string RunFolder, string SetupJsonPath, string ExpectedLogPath) PrepareRunDirectory(
        string logsRoot,
        ArenaSetup setup,
        int resolvedSeed,
        DateTime? timestamp = null)
    {
        if (string.IsNullOrWhiteSpace(logsRoot))
            throw new ArgumentException("A logs root folder is required.", nameof(logsRoot));
        ArgumentNullException.ThrowIfNull(setup);
        setup.Validate();

        var root = Path.GetFullPath(logsRoot);
        Directory.CreateDirectory(root);

        var stamp = (timestamp ?? DateTime.Now).ToString("yyyyMMdd-HHmmss");
        var runFolder = Path.Combine(root, stamp);
        var suffix = 2;
        while (Directory.Exists(runFolder) || File.Exists(runFolder))
        {
            runFolder = Path.Combine(root, $"{stamp}-{suffix}");
            suffix++;
        }

        Directory.CreateDirectory(runFolder);
        var setupJsonPath = Path.Combine(runFolder, "setup.json");
        var expectedLogPath = Path.Combine(runFolder, $"match-{resolvedSeed}.jsonl");
        File.WriteAllText(setupJsonPath, setup.ToRuntimeSetupJson(runFolder), new UTF8Encoding(false));
        return (runFolder, setupJsonPath, expectedLogPath);
    }

    /// <summary>
    /// Format a <see cref="ProcessStartInfo"/> executable and argument list as a pasteable Windows command line.
    /// </summary>
    public static string FormatCommandLine(ProcessStartInfo startInfo)
    {
        ArgumentNullException.ThrowIfNull(startInfo);
        var tokens = new List<string>(1 + startInfo.ArgumentList.Count) { startInfo.FileName };
        tokens.AddRange(startInfo.ArgumentList);
        return FormatCommandLine(tokens);
    }

    /// <summary>
    /// Quote an executable and argument list using standard Windows command-line escaping rules.
    /// </summary>
    public static string FormatCommandLine(IEnumerable<string> arguments)
    {
        ArgumentNullException.ThrowIfNull(arguments);
        return string.Join(" ", arguments.Select(QuoteWindowsArgument));
    }

    /// <summary>Quote a single argument for a Windows command line.</summary>
    public static string QuoteWindowsArgument(string argument)
    {
        if (argument == null)
            return "\"\"";
        if (argument.Length > 0 && !argument.Any(c => char.IsWhiteSpace(c) || c is '"' or '\''))
            return argument;

        var builder = new StringBuilder(argument.Length + 8);
        builder.Append('"');
        var backslashes = 0;
        foreach (var ch in argument)
        {
            if (ch == '\\')
            {
                backslashes++;
            }
            else if (ch == '"')
            {
                builder.Append('\\', backslashes * 2 + 1);
                builder.Append('"');
                backslashes = 0;
            }
            else
            {
                if (backslashes > 0)
                {
                    builder.Append('\\', backslashes);
                    backslashes = 0;
                }
                builder.Append(ch);
            }
        }

        if (backslashes > 0)
            builder.Append('\\', backslashes * 2);
        builder.Append('"');
        return builder.ToString();
    }

    /// <summary>
    /// Try to parse the game's printed <c>arena: winner A|B|draw, time M:SS, lost A N B M</c> line
    /// from captured stdout/stderr lines. When multiple result lines are present, the last one wins.
    /// </summary>
    public static bool TryParseStdoutResult(
        IEnumerable<string> capturedLines,
        out string winner,
        out string timeText,
        out int lostA,
        out int lostB)
    {
        winner = "";
        timeText = "";
        lostA = 0;
        lostB = 0;
        if (capturedLines == null)
            return false;

        var foundMatch = false;
        foreach (var rawLine in capturedLines)
        {
            if (string.IsNullOrWhiteSpace(rawLine))
                continue;
            var cleaned = StripLauncherElapsed(rawLine);
            var match = StdoutResultPattern.Match(cleaned);
            if (!match.Success)
                continue;

            winner = match.Groups["winner"].Value;
            timeText = match.Groups["time"].Value;
            lostA = int.Parse(match.Groups["lostA"].Value);
            lostB = int.Parse(match.Groups["lostB"].Value);
            foundMatch = true;
        }

        return foundMatch;
    }

    /// <summary>
    /// Stream a <c>match-&lt;seed&gt;.jsonl</c> file line by line (without loading the entire
    /// multi-megabyte log into memory) to find the trailing <c>{"type":"end",...}</c> record.
    /// </summary>
    public static bool TryReadLogEndResult(
        string matchLogPath,
        out string winner,
        out string timeText,
        out int lostA,
        out int lostB)
    {
        winner = "";
        timeText = "";
        lostA = 0;
        lostB = 0;

        if (string.IsNullOrWhiteSpace(matchLogPath) || !File.Exists(matchLogPath))
            return false;

        try
        {
            using var stream = new FileStream(matchLogPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            using var reader = new StreamReader(stream, Encoding.UTF8);
            string? line;
            while ((line = reader.ReadLine()) != null)
            {
                if (!line.Contains("\"end\"", StringComparison.Ordinal))
                    continue;

                try
                {
                    using var doc = JsonDocument.Parse(line);
                    var root = doc.RootElement;
                    if (root.ValueKind != JsonValueKind.Object)
                        continue;
                    if (!root.TryGetProperty("type", out var typeProp) ||
                        typeProp.ValueKind != JsonValueKind.String ||
                        typeProp.GetString() != "end")
                    {
                        continue;
                    }

                    if (!root.TryGetProperty("winner", out var winnerProp) ||
                        winnerProp.ValueKind != JsonValueKind.String)
                    {
                        continue;
                    }

                    var parsedWinner = winnerProp.GetString() ?? "";
                    if (parsedWinner is not ("A" or "B" or "draw"))
                        continue;

                    if (!root.TryGetProperty("t", out var timeProp) ||
                        timeProp.ValueKind != JsonValueKind.Number ||
                        !timeProp.TryGetDouble(out var seconds) ||
                        seconds < 0)
                    {
                        continue;
                    }

                    if (!root.TryGetProperty("lost", out var lostProp) ||
                        lostProp.ValueKind != JsonValueKind.Array ||
                        lostProp.GetArrayLength() != 2)
                    {
                        continue;
                    }

                    var lostItems = lostProp.EnumerateArray().ToArray();
                    if (!lostItems[0].TryGetInt32(out var parsedLostA) ||
                        !lostItems[1].TryGetInt32(out var parsedLostB))
                    {
                        continue;
                    }

                    var wholeSeconds = Math.Max(0, (int)seconds);
                    winner = parsedWinner;
                    timeText = $"{wholeSeconds / 60}:{wholeSeconds % 60:D2}";
                    lostA = parsedLostA;
                    lostB = parsedLostB;
                }
                catch (JsonException)
                {
                    // Skip a truncated or malformed line and keep scanning.
                }
            }

            return !string.IsNullOrEmpty(winner);
        }
        catch (IOException)
        {
            return false;
        }
    }

    /// <summary>
    /// Evaluate a finished arena process from its exit code, captured stdout/stderr lines,
    /// optional <c>mw3.log</c> lines (when the Windows GUI subsystem redirects stdout/stderr
    /// to <c>mw3.log</c>), and the match log file.
    /// </summary>
    public static ArenaMatchOutcome EvaluateOutcome(
        int exitCode,
        int resolvedSeed,
        IEnumerable<string> capturedOutputLines,
        string runFolder,
        string setupJsonPath,
        string expectedLogPath,
        string commandLine,
        IEnumerable<string>? fallbackRuntimeLogLines = null)
    {
        var combinedLines = new List<string>();
        if (capturedOutputLines != null)
            combinedLines.AddRange(capturedOutputLines);
        if (fallbackRuntimeLogLines != null)
            combinedLines.AddRange(fallbackRuntimeLogLines);

        // Nonzero exit codes are always failures, even if a partial or stale log exists.
        if (exitCode == 2)
        {
            var detail = ExtractFailureDetail(combinedLines);
            var message = string.IsNullOrEmpty(detail)
                ? "Setup refused (exit 2)."
                : $"Setup refused: {detail}";
            return new ArenaMatchOutcome(
                false, exitCode, resolvedSeed, null, null, 0, 0, message,
                runFolder, setupJsonPath, expectedLogPath, commandLine);
        }

        if (exitCode == 1)
        {
            var detail = ExtractFailureDetail(combinedLines);
            var message = string.IsNullOrEmpty(detail)
                ? "Match could not start (exit 1)."
                : $"Match could not start: {detail}";
            return new ArenaMatchOutcome(
                false, exitCode, resolvedSeed, null, null, 0, 0, message,
                runFolder, setupJsonPath, expectedLogPath, commandLine);
        }

        if (exitCode != 0)
        {
            var detail = ExtractFailureDetail(combinedLines);
            var suffix = string.IsNullOrEmpty(detail) ? "" : ": " + detail;
            return new ArenaMatchOutcome(
                false, exitCode, resolvedSeed, null, null, 0, 0,
                $"Match exited with code {exitCode}{suffix}",
                runFolder, setupJsonPath, expectedLogPath, commandLine);
        }

        // Prefer the printed "arena: winner ..." line because the match log's "end" record
        // includes the 5-second post-decision aftermath in its timestamp t.
        if (TryParseStdoutResult(combinedLines, out var winner, out var timeText, out var lostA, out var lostB))
        {
            return new ArenaMatchOutcome(
                true, 0, resolvedSeed, winner, timeText, lostA, lostB, null,
                runFolder, setupJsonPath, expectedLogPath, commandLine);
        }

        if (TryReadLogEndResult(expectedLogPath, out winner, out timeText, out lostA, out lostB))
        {
            return new ArenaMatchOutcome(
                true, 0, resolvedSeed, winner, timeText, lostA, lostB, null,
                runFolder, setupJsonPath, expectedLogPath, commandLine);
        }

        return new ArenaMatchOutcome(
            false, 0, resolvedSeed, null, null, 0, 0,
            "Match exited without a result (the window was closed early or no result was recorded).",
            runFolder, setupJsonPath, expectedLogPath, commandLine);
    }

    /// <summary>
    /// Run one AI Arena match end to end through <see cref="NativeGameRunner"/> and await completion.
    /// </summary>
    public static async Task<ArenaMatchOutcome> RunMatchAsync(
        NativeGameRunner runner,
        LauncherSettings settings,
        IReadOnlyList<string> activeModDirs,
        ArenaSetup setupSnapshot,
        int resolvedSeed,
        string logsRoot,
        string dataRoot,
        Action<string>? onProgressLine = null,
        Action<Process, string>? onProcessStarted = null)
    {
        ArgumentNullException.ThrowIfNull(runner);
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(activeModDirs);
        ArgumentNullException.ThrowIfNull(setupSnapshot);

        var (runFolder, setupJsonPath, expectedLogPath) = PrepareRunDirectory(logsRoot, setupSnapshot, resolvedSeed);
        var extraArguments = BuildArguments(setupJsonPath, resolvedSeed, setupSnapshot.FrameMs, setupSnapshot.Hidden);
        var capturedLines = new List<string>();
        var captureLock = new object();

        var profileWriteDir = Path.Combine(Path.GetFullPath(dataRoot), "mw3-re", "profiles", NativeGameRunner.ProfileId);
        var runtimeLogPath = Path.Combine(profileWriteDir, "mw3.log");
        DateTime launchStartUtc = default;

        var process = await Task.Run(() =>
        {
            launchStartUtc = DateTime.UtcNow;
            return runner.Launch(
                settings,
                activeModDirs,
                line =>
                {
                    lock (captureLock)
                    {
                        capturedLines.Add(line);
                    }
                    onProgressLine?.Invoke(StripLauncherElapsed(line));
                },
                extraArguments);
        }).ConfigureAwait(false);

        using (process)
        {
            var commandLine = FormatCommandLine(process.StartInfo);
            onProcessStarted?.Invoke(process, commandLine);

            var exitCode = runner.LastSessionCompletion != null
                ? await runner.LastSessionCompletion.ConfigureAwait(false)
                : await GameRunner.WaitForCompletionAsync(process).ConfigureAwait(false);

            List<string> snapshotLines;
            lock (captureLock)
            {
                snapshotLines = capturedLines.ToList();
            }

            // When built as a Windows GUI executable without an attached console, mw3.exe
            // redirects stdout and stderr directly into <write-dir>/mw3.log (log_to_file).
            // The runtime reopens mw3.log without append on every start, so the whole file
            // belongs to this run only when its last write is at or after launch.
            var fallbackLines = TryReadFreshRuntimeLogLines(runtimeLogPath, launchStartUtc);
            return EvaluateOutcome(
                exitCode,
                resolvedSeed,
                snapshotLines,
                runFolder,
                setupJsonPath,
                expectedLogPath,
                commandLine,
                fallbackLines);
        }
    }

    /// <summary>
    /// Read the entire runtime log only when it was last written at or after
    /// <paramref name="launchStartUtc"/>; each runtime start truncates the previous log.
    /// </summary>
    public static IReadOnlyList<string> TryReadFreshRuntimeLogLines(string runtimeLogPath, DateTime launchStartUtc)
    {
        try
        {
            if (!File.Exists(runtimeLogPath) || File.GetLastWriteTimeUtc(runtimeLogPath) < launchStartUtc)
                return Array.Empty<string>();

            using var stream = new FileStream(runtimeLogPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            using var reader = new StreamReader(stream, Encoding.UTF8);
            var lines = new List<string>();
            string? line;
            while ((line = reader.ReadLine()) != null)
            {
                lines.Add(line);
            }
            return lines;
        }
        catch
        {
            return Array.Empty<string>();
        }
    }

    private static string ExtractFailureDetail(IEnumerable<string> rawLines)
    {
        var meaningfulLines = new List<string>();
        foreach (var raw in rawLines)
        {
            var line = StripLauncherElapsed(raw).Trim();
            if (string.IsNullOrEmpty(line))
                continue;
            if (IsRoutineStartupLine(line))
                continue;
            meaningfulLines.Add(line);
        }

        return string.Join(Environment.NewLine, meaningfulLines);
    }

    private static bool IsRoutineStartupLine(string line)
    {
        return line.StartsWith("Startup: ", StringComparison.Ordinal) ||
            line.StartsWith("Starting MW3-RE: ", StringComparison.Ordinal) ||
            line.StartsWith("MW3-RE PID ", StringComparison.Ordinal) ||
            line.StartsWith("Native progress: ", StringComparison.Ordinal) ||
            line.StartsWith("Native first frame: ", StringComparison.Ordinal) ||
            line.StartsWith("Native menu ready: ", StringComparison.Ordinal) ||
            line.StartsWith("Native readiness observation ended: ", StringComparison.Ordinal) ||
            line.StartsWith("mw3 (MechWarrior 3 rebuild) ", StringComparison.Ordinal) ||
            line.StartsWith("mw3: timing ", StringComparison.Ordinal) ||
            line.StartsWith("mw3: disk cache ", StringComparison.Ordinal) ||
            line.StartsWith("mw3: input bindings: ", StringComparison.Ordinal) ||
            line.StartsWith("mw3: install ", StringComparison.Ordinal) ||
            line.StartsWith("mw3: rand seeded with ", StringComparison.Ordinal) ||
            line.StartsWith("Environment packs ", StringComparison.Ordinal);
    }

    private static string StripLauncherElapsed(string line) =>
        LauncherElapsedSuffix.Replace(line ?? "", "");
}
