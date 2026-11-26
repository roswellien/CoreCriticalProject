using System.IO;
using MW3RemasterLauncher.Core;

/// <summary>Asset-free checks for the settings page's Run benchmark button.</summary>
internal static class BenchmarkRunnerChecks
{
    private static void Check(bool value, string message)
    {
        if (!value) throw new Exception("Benchmark: " + message);
    }

    public static void Run()
    {
        // Diagnostic output from the planner and the game is not an event.
        Check(BenchmarkRunner.ParseEvent("{\"Width\": 1920}") == null, "plain JSON output parsed as an event");
        Check(BenchmarkRunner.ParseEvent("mw3: benchmark invalid") == null, "game text parsed as an event");

        var progress = BenchmarkRunner.ParseEvent("BENCHMARK-EVENT {\"event\":\"progress\",\"stage\":\"generate\",\"scene\":\"c2mp2\"}")!;
        Check(progress.Kind == "progress" && progress.Scene == "c2mp2", "progress event fields");
        Check(BenchmarkRunner.DescribeProgress(progress).Contains("c2mp2"), "generation progress names the map");

        var focus = BenchmarkRunner.ParseEvent(
            "BENCHMARK-EVENT {\"event\":\"error\",\"kind\":\"focus_lost\",\"scene\":\"c3mp1\",\"message\":\"benchmark window lost focus\"}")!;
        var focusText = BenchmarkRunner.DescribeError(focus);
        Check(focusText.Contains("lost focus during c3mp1") && focusText.Contains("Keep the game window in front"),
            "focus loss message is not actionable: " + focusText);
        var unsupported = BenchmarkRunner.ParseEvent(
            "BENCHMARK-EVENT {\"event\":\"error\",\"kind\":\"unsupported\",\"message\":\"Update Core Critical.\"}")!;
        Check(BenchmarkRunner.DescribeError(unsupported) == "Update Core Critical.", "unsupported build message");

        const string Result = "BENCHMARK-EVENT {\"event\":\"result\",\"output\":\"C:/results/1\",\"report\":{" +
            "\"gpu\":\"Test GPU\",\"reference_mismatch_scenes\":[\"c4mp2\"]," +
            "\"scenes\":[{\"id\":\"c1mp1\",\"average_fps\":64.93,\"low_1_percent_fps\":41.2,\"p95_ms\":19.5,\"p99_ms\":24.25}]," +
            "\"overall\":{\"average_fps\":60,\"low_1_percent_fps\":40,\"p95_ms\":20,\"p99_ms\":25}," +
            "\"previous\":{\"finished\":\"2026-11-25T10:00:00Z\",\"overall\":{\"average_fps\":50,\"low_1_percent_fps\":35,\"p95_ms\":22,\"p99_ms\":28}}}}";
        var result = BenchmarkRunner.ParseEvent(Result)!;
        var report = result.Report!;
        Check(report.Scenes.Count == 1 && report.Scenes[0].Name == "c1mp1" && report.Scenes[0].P99Ms == 24.25, "scene figures");
        Check(report.Overall.AverageFps == 60 && report.Previous!.AverageFps == 50, "overall and previous figures");
        Check(report.OutputDirectory == "C:/results/1" && report.Gpu == "Test GPU", "report metadata");
        var table = BenchmarkRunner.FormatReport(report);
        Check(table.Contains("Avg FPS") && table.Contains("1% low") && table.Contains("p95 ms") && table.Contains("p99 ms"),
            "table header");
        Check(table.Contains("c1mp1          64.9      41.2     19.50     24.25"), "scene row layout:\n" + table);
        Check(table.Contains("Overall") && table.Contains("+20.0%"), "overall row or previous-run change:\n" + table);
        Check(table.Contains("c4mp2") && table.Contains("your own earlier runs"), "reference mismatch note");

        // The installed layout: bundled Python runs the coordinator isolated, with the planner folder.
        var arguments = BenchmarkRunner.BuildArguments("B/player.py", "NativePreview", "Planner", "W");
        Check(arguments[0] == "-I" && arguments.Contains("--planner-dir") && arguments[^1] == "W", "coordinator arguments");

        var root = Path.Combine(Path.GetTempPath(), "MW3 benchmark fixture " + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(root);
            var runner = new BenchmarkRunner(root, new NativeGameRunner(root, root), Path.Combine(root, "work"));
            Check(runner.FindCoordinator() == null, "missing coordinator was reported as present");
            Directory.CreateDirectory(Path.Combine(root, BenchmarkRunner.BenchmarkFolder));
            File.WriteAllText(Path.Combine(root, BenchmarkRunner.BenchmarkFolder, "player.py"), "");
            Check(runner.FindCoordinator() != null, "bundled coordinator not found");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
        Check(!LauncherPaths.BenchmarkRoot.StartsWith(LauncherPaths.DataRoot + Path.DirectorySeparatorChar,
            StringComparison.OrdinalIgnoreCase), "benchmark output must stay outside the read-only launcher data");
        Console.WriteLine("Benchmark runner checks passed.");
    }
}
