using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// Starts the labelled MW3-RE Native preview with the player's saved settings.
/// </summary>
/// <remarks>
/// Owner decision 2026-11-15: the preview ships beside the default Remaster Play. It is not the
/// trusted B2/C activation route. The runtime folder is integrity-checked by
/// <see cref="Mw3ReRuntimeContract.ReadStructure"/> (every pinned file is hashed), and the Python
/// planner shipped with the launcher remains the only producer of game arguments.
/// </remarks>
public sealed class NativePreviewRunner
{
    /// <summary>Installed folder name, next to the launcher executable.</summary>
    public const string RuntimeFolder = "NativePreview";
    public const string PlannerFolder = "Planner";
    public const string ProfileId = "native-preview";
    /// <summary>The largest scenery distance the preview runtime accepts in this release.</summary>
    public const int MaxDrawDistance = 1600;

    private readonly string _basePath;
    private readonly string _dataRoot;

    public NativePreviewRunner(string basePath, string? dataRoot = null)
    {
        _basePath = basePath;
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
    }

    public string? LastLogPath { get; private set; }

    /// <summary>The installed preview runtime folder, or null when this install has none.</summary>
    public string? FindRuntimeRoot()
    {
        var root = Path.Combine(_basePath, RuntimeFolder);
        return File.Exists(Path.Combine(root, "runtime.json")) ? root : null;
    }

    /// <summary>
    /// The preview supports 800, 1200 and 1600. Larger saved choices (made for the Remaster
    /// engine) use 1600, and the caller is told so; smaller unknown values are refused.
    /// </summary>
    public static int PreviewDrawDistance(int savedDrawDistance, out bool reduced)
    {
        reduced = savedDrawDistance > MaxDrawDistance;
        if (reduced) return MaxDrawDistance;
        if (savedDrawDistance is not (800 or 1200 or 1600))
            throw new InvalidOperationException("Choose a scenery distance of 800, 1200 or 1600 for the Native preview.");
        return savedDrawDistance;
    }

    /// <summary>Split the enabled packs into the two kinds the preview runtime reads.</summary>
    public static (List<string> Models, List<string> Environments) SelectPreviewPacks(IEnumerable<string> activeModDirs)
    {
        var models = new List<string>();
        var environments = new List<string>();
        foreach (var directory in activeModDirs)
        {
            var root = Path.GetFullPath(PackStorage.CanonicalPackRoot(directory));
            var manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
            // Music, interface and cinematic packs belong to the Remaster engine's own content steps.
            if (manifest.SchemaVersion != 2) continue;
            if (manifest.NativePayload?.Profile == "prepared-native-v1") models.Add(root);
            else if (manifest.NativePayload?.Profile == "prepared-environment-v1") environments.Add(root);
        }
        return (models, environments);
    }

    /// <summary>Map the saved antialiasing text to the planner's typed choice.</summary>
    public static Mw3ReAntialiasing PreviewAntialiasing(string saved) => saved switch
    {
        "off" => Mw3ReAntialiasing.Off,
        "fxaa" => Mw3ReAntialiasing.Fxaa,
        "2" => Mw3ReAntialiasing.Two,
        "4" => Mw3ReAntialiasing.Four,
        "8" => Mw3ReAntialiasing.Eight,
        _ => throw new InvalidOperationException("Unknown antialiasing setting: " + saved)
    };

    /// <summary>Plan and start one preview session; the caller owns the returned process.</summary>
    public Process Launch(LauncherSettings settings, IEnumerable<string> activeModDirs, Action<string>? log = null)
    {
        var session = Path.Combine(_dataRoot, "sessions", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(session);
        LastLogPath = Path.Combine(session, "native-preview.log");
        File.WriteAllText(LastLogPath, "Native preview, launcher " +
            typeof(NativePreviewRunner).Assembly.GetName().Version + Environment.NewLine);
        void Log(string line)
        {
            lock (session) File.AppendAllText(LastLogPath!, line + Environment.NewLine);
            log?.Invoke(line);
        }

        // Same exclusion as the Remaster Play: no update or pack change while the game runs.
        var gate = GameUpdateGate.Acquire(_dataRoot);
        try
        {
            var process = Start(settings, activeModDirs, Log);
            process.EnableRaisingEvents = true;
            process.Exited += (_, _) => gate.Dispose();
            if (process.HasExited) gate.Dispose();
            return process;
        }
        catch (Exception error)
        {
            gate.Dispose();
            Log("ERROR: " + error.Message);
            throw;
        }
    }

    private Process Start(LauncherSettings settings, IEnumerable<string> activeModDirs, Action<string> log)
    {
        var validation = GameValidator.Validate(settings.GamePath);
        if (!validation.IsValid) throw new InvalidOperationException("Cannot launch game: " + validation.StatusMessage);
        var root = FindRuntimeRoot() ?? throw new FileNotFoundException("This installation has no Native preview runtime.");
        var contract = Mw3ReRuntimeContract.ReadStructure(root);
        var planner = Path.Combine(_basePath, PlannerFolder, "mw3_re_launch.py");
        if (!File.Exists(planner)) throw new FileNotFoundException("The Native preview planner is missing.", planner);
        var python = NativeRuntimeLayout.FindInstalled(_basePath, _dataRoot)?.Python
            ?? D7VkRunner.FindPythonExecutable(requirePython311: true)
            ?? throw new FileNotFoundException("The Native preview needs Python 3.11 or newer.");

        var drawDistance = PreviewDrawDistance(settings.DrawDistance, out var reduced);
        if (reduced) log($"Scenery distance {settings.DrawDistance} is not in this preview; using {drawDistance}.");
        var (models, environments) = SelectPreviewPacks(activeModDirs);
        var options = new Mw3RePlanningOptions
        {
            Width = settings.Width,
            Height = settings.Height,
            Antialiasing = PreviewAntialiasing(settings.AntiAliasing),
            AnisotropicFiltering = settings.AnisotropicFiltering,
            // The preview runtime presents in a window only; the planner refuses other modes.
            WindowMode = Mw3ReWindowMode.Windowed,
            RenderThread = settings.RenderThread,
            Lighting = Mw3ReLighting.Normal,
            Pom = true,
            Preview = new Mw3RePreviewOptions
            {
                DrawDistance = drawDistance,
                ModelPacks = models,
                EnvironmentPacks = environments
            }
        };
        var request = Mw3ReLaunchRequest.Create(contract, options, validation.GameDirectory, _dataRoot, ProfileId);
        var plan = RunPlanner(python, planner, request);
        if (!plan.RootElement.GetProperty("ok").GetBoolean())
        {
            var reasons = plan.RootElement.GetProperty("reasons").EnumerateArray().Select(item => item.GetString());
            throw new InvalidOperationException("The Native preview cannot start: " + string.Join("; ", reasons));
        }
        if (plan.RootElement.TryGetProperty("skipped_packs", out var skipped))
            foreach (var item in skipped.EnumerateArray())
                log("Pack left out: " + item.GetProperty("root").GetString() + " (" + item.GetProperty("reason").GetString() + ")");

        var argv = plan.RootElement.GetProperty("argv").EnumerateArray().Select(item => item.GetString()!).ToList();
        var writeDirectory = Path.Combine(_dataRoot, "mw3-re", "profiles", ProfileId);
        Directory.CreateDirectory(writeDirectory);
        var start = new ProcessStartInfo(argv[0])
        {
            WorkingDirectory = plan.RootElement.GetProperty("working_directory").GetString()!,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };
        foreach (var argument in argv.Skip(1)) start.ArgumentList.Add(argument);
        log($"Starting MW3-RE Native preview: {settings.Width}x{settings.Height}, scenery {drawDistance}, " +
            $"{models.Count} model pack(s), {environments.Count} map pack(s).");
        var process = new Process { StartInfo = start };
        process.OutputDataReceived += (_, line) => { if (line.Data != null) log(line.Data); };
        process.ErrorDataReceived += (_, line) => { if (line.Data != null) log(line.Data); };
        if (!process.Start()) throw new InvalidOperationException("MW3-RE did not start.");
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();
        log("MW3-RE PID " + process.Id);
        return process;
    }

    /// <summary>Run the shipped planner in isolated mode and parse its one JSON result.</summary>
    private static JsonDocument RunPlanner(string python, string planner, string request)
    {
        // -I ignores the user's Python environment and the current directory, so only the shipped
        // planner module is imported.
        const string Script = "import sys, json; sys.path.insert(0, sys.argv[1]); import mw3_re_launch; " +
                              "print(json.dumps(mw3_re_launch.plan_json(sys.stdin.read())))";
        var start = new ProcessStartInfo(python)
        {
            UseShellExecute = false,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };
        foreach (var argument in new[] { "-I", "-c", Script, Path.GetDirectoryName(planner)! })
            start.ArgumentList.Add(argument);
        using var process = Process.Start(start) ?? throw new InvalidOperationException("The planner did not start.");
        process.StandardInput.Write(request);
        process.StandardInput.Close();
        var errors = process.StandardError.ReadToEndAsync();
        var output = process.StandardOutput.ReadToEnd();
        if (!process.WaitForExit(30000))
        {
            process.Kill(entireProcessTree: true);
            throw new TimeoutException("The Native preview planner did not finish.");
        }
        if (process.ExitCode != 0)
        {
            // The planner reports invalid choices as a ValueError on its last error line.
            var last = errors.Result.Split('\n', StringSplitOptions.RemoveEmptyEntries).LastOrDefault()?.Trim();
            throw new InvalidOperationException("The Native preview settings were refused: " + (last ?? "planner error"));
        }
        return JsonDocument.Parse(output);
    }
}
