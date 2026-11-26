using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>One figure set for a benchmark scene or the whole suite.</summary>
public sealed record BenchmarkFigures(string Name, double AverageFps, double LowOnePercentFps, double P95Ms, double P99Ms);

/// <summary>What the settings page shows after a finished benchmark.</summary>
public sealed record BenchmarkReport(
    IReadOnlyList<BenchmarkFigures> Scenes,
    BenchmarkFigures Overall,
    BenchmarkFigures? Previous,
    string? PreviousFinished,
    string? Gpu,
    IReadOnlyList<string> ReferenceMismatchScenes,
    string? OutputDirectory);

/// <summary>One line the coordinator printed for the launcher.</summary>
public sealed record BenchmarkEvent(string Kind, string? Stage, string? Scene, string? ErrorKind, string? Message,
    BenchmarkReport? Report);

/// <summary>
/// Runs the bundled four-scene arena benchmark (tools/benchmark/player.py) with the planner's
/// Python. The coordinator reads the saved launcher settings and active packs itself through the
/// Play planner, so the benchmark uses exactly what Play would launch.
/// </summary>
public sealed class BenchmarkRunner
{
    public const string BenchmarkFolder = "Benchmark";
    public const string EventPrefix = "BENCHMARK-EVENT ";

    private readonly string _basePath;
    private readonly NativeGameRunner _nativeRunner;
    private readonly string _workRoot;

    public BenchmarkRunner(string basePath, NativeGameRunner nativeRunner, string? workRoot = null)
    {
        _basePath = basePath;
        _nativeRunner = nativeRunner;
        _workRoot = workRoot ?? LauncherPaths.BenchmarkRoot;
    }

    /// <summary>The coordinator script, or null when this install does not ship the benchmark.</summary>
    public string? FindCoordinator()
    {
        var script = Path.Combine(_basePath, BenchmarkFolder, "player.py");
        return File.Exists(script) ? script : null;
    }

    /// <summary>Arguments after the Python executable. -I keeps the user's Python setup out.</summary>
    public static IReadOnlyList<string> BuildArguments(string coordinator, string runtimeRoot, string plannerDirectory,
        string workRoot) =>
        new[] { "-I", "-B", coordinator, "--runtime", runtimeRoot, "--planner-dir", plannerDirectory, "--work-root", workRoot };

    public async Task<BenchmarkEvent> RunAsync(Action<BenchmarkEvent> progress, CancellationToken cancellation)
    {
        var coordinator = FindCoordinator() ?? throw new FileNotFoundException(
            "This launcher does not include the benchmark. Update Core Critical.");
        var runtimeRoot = _nativeRunner.RequireBundledMw3Re();
        var python = _nativeRunner.FindPlannerPython();
        var planner = Path.Combine(_basePath, NativeGameRunner.PlannerFolder);
        var start = new ProcessStartInfo(python)
        {
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };
        foreach (var argument in BuildArguments(coordinator, runtimeRoot, planner, _workRoot))
            start.ArgumentList.Add(argument);
        start.Environment["PYTHONIOENCODING"] = "utf-8";

        using var process = Process.Start(start) ?? throw new InvalidOperationException("The benchmark did not start.");
        BenchmarkEvent? final = null;
        var errorTail = new Queue<string>();
        var errorReader = Task.Run(async () =>
        {
            while (await process.StandardError.ReadLineAsync() is { } line)
            {
                lock (errorTail)
                {
                    errorTail.Enqueue(line);
                    if (errorTail.Count > 5) errorTail.Dequeue();
                }
            }
        });
        using (cancellation.Register(() => { try { process.Kill(entireProcessTree: true); } catch (InvalidOperationException) { } }))
        {
            while (await process.StandardOutput.ReadLineAsync() is { } line)
            {
                if (ParseEvent(line) is not { } item) continue;
                if (item.Kind is "result" or "error") final = item;
                else progress(item);
            }
            await process.WaitForExitAsync(CancellationToken.None);
            await errorReader;
        }
        cancellation.ThrowIfCancellationRequested();
        if (final != null) return final;
        string tail;
        lock (errorTail) tail = string.Join(" ", errorTail);
        return new BenchmarkEvent("error", null, null, "failed",
            $"The benchmark stopped with status {process.ExitCode}. {tail}".Trim(), null);
    }

    /// <summary>Parse one coordinator event line; other output is diagnostic text and returns null.</summary>
    public static BenchmarkEvent? ParseEvent(string line)
    {
        if (!line.StartsWith(EventPrefix, StringComparison.Ordinal)) return null;
        using var document = JsonDocument.Parse(line[EventPrefix.Length..]);
        var root = document.RootElement;
        var kind = root.GetProperty("event").GetString() ?? throw new InvalidDataException("Benchmark event lacks a kind");
        BenchmarkReport? report = null;
        if (kind == "result")
            report = ParseReport(root.GetProperty("report"), Text(root, "output"));
        return new BenchmarkEvent(kind, Text(root, "stage"), Text(root, "scene"), Text(root, "kind"),
            Text(root, "message"), report);
    }

    private static string? Text(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;

    private static BenchmarkFigures Figures(string name, JsonElement element) => new(name,
        element.GetProperty("average_fps").GetDouble(),
        element.GetProperty("low_1_percent_fps").GetDouble(),
        element.GetProperty("p95_ms").GetDouble(),
        element.GetProperty("p99_ms").GetDouble());

    private static BenchmarkReport ParseReport(JsonElement report, string? output)
    {
        var scenes = report.GetProperty("scenes").EnumerateArray()
            .Select(scene => Figures(scene.GetProperty("id").GetString()!, scene)).ToList();
        BenchmarkFigures? previous = null;
        string? previousFinished = null;
        if (report.TryGetProperty("previous", out var earlier) && earlier.ValueKind == JsonValueKind.Object)
        {
            previous = Figures("Previous", earlier.GetProperty("overall"));
            previousFinished = Text(earlier, "finished");
        }
        var mismatches = report.TryGetProperty("reference_mismatch_scenes", out var list)
            ? list.EnumerateArray().Select(item => item.GetString()!).ToList()
            : new List<string>();
        return new BenchmarkReport(scenes, Figures("Overall", report.GetProperty("overall")), previous,
            previousFinished, Text(report, "gpu"), mismatches, output);
    }

    /// <summary>Plain status text for a progress event.</summary>
    public static string DescribeProgress(BenchmarkEvent item) => item.Stage switch
    {
        "generate" => $"Preparing the {item.Scene} replay from your MechWarrior 3 install (first run only, a few minutes per map)...",
        "play" => "Running the four benchmark scenes. Keep the game window in front until it closes.",
        _ => item.Message ?? "Running the benchmark...",
    };

    /// <summary>A message the player can act on for a failed run.</summary>
    public static string DescribeError(BenchmarkEvent item) => item.ErrorKind switch
    {
        "focus_lost" =>
            $"The benchmark window lost focus{(item.Scene is { } scene ? $" during {scene}" : "")}, so the run was stopped " +
            "and not scored. Keep the game window in front and don't switch apps until the benchmark finishes, then run it again.",
        "unsupported" => item.Message ?? "This game build does not include the benchmark. Update Core Critical.",
        _ => "The benchmark failed: " + (item.Message ?? "unknown error"),
    };

    /// <summary>A fixed-width results table for the settings page.</summary>
    public static string FormatReport(BenchmarkReport report)
    {
        var culture = CultureInfo.InvariantCulture;
        var text = new StringBuilder();
        text.AppendLine(string.Format(culture, "{0,-9}{1,10}{2,10}{3,10}{4,10}", "Scene", "Avg FPS", "1% low", "p95 ms", "p99 ms"));
        void Row(BenchmarkFigures row) => text.AppendLine(string.Format(culture, "{0,-9}{1,10:F1}{2,10:F1}{3,10:F2}{4,10:F2}",
            row.Name, row.AverageFps, row.LowOnePercentFps, row.P95Ms, row.P99Ms));
        foreach (var scene in report.Scenes) Row(scene);
        Row(report.Overall);
        if (report.Previous is { } previous)
        {
            var change = (report.Overall.AverageFps - previous.AverageFps) / previous.AverageFps * 100;
            text.AppendLine();
            text.AppendLine(string.Format(culture, "Previous run with the same settings ({0}): {1:F1} average FPS ({2:+0.0;-0.0}%).",
                report.PreviousFinished ?? "earlier", previous.AverageFps, change));
        }
        if (report.ReferenceMismatchScenes.Count > 0)
        {
            text.AppendLine();
            text.AppendLine("Your replays for " + string.Join(", ", report.ReferenceMismatchScenes) +
                " differ from the reference build's, so compare these results only with your own earlier runs.");
        }
        return text.ToString().TrimEnd();
    }
}
