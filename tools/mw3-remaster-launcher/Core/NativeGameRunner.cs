using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// Starts MW3-RE Native with the player's saved settings.
/// </summary>
/// <remarks>
/// Owner decision 2026-11-15: MW3-RE Native is the launcher's default runtime. It is not the
/// trusted B2/C activation route. The runtime folder is integrity-checked by
/// <see cref="Mw3ReRuntimeContract.ReadStructure"/> (every pinned file is hashed), and the Python
/// planner shipped with the launcher remains the only producer of game arguments.
/// </remarks>
public sealed class NativeGameRunner
{
    /// <summary>Installed folder name, next to the launcher executable.</summary>
    public const string RuntimeFolder = "NativePreview";
    public const string PlannerFolder = "Planner";
    public const string ProfileId = "native-preview";
    /// <summary>The largest scenery distance the native runtime accepts in this release.</summary>
    public const int MaxDrawDistance = 1600;

    private readonly string _basePath;
    private readonly string _dataRoot;

    public NativeGameRunner(string basePath, string? dataRoot = null)
    {
        _basePath = basePath;
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
    }

    public string? LastLogPath { get; private set; }

    public static Mw3ReWindowMode WindowModeForSettings(string savedWindowMode) => savedWindowMode switch
    {
        "windowed" => Mw3ReWindowMode.Windowed,
        "fullscreen" => Mw3ReWindowMode.Fullscreen,
        "fullscreen_windowed" => Mw3ReWindowMode.Borderless,
        _ => throw new InvalidOperationException("Choose a supported window mode.")
    };

    /// <summary>The installed MW3-RE runtime folder, or null when this install has none.</summary>
    public string? FindRuntimeRoot()
    {
        var root = Path.Combine(_basePath, RuntimeFolder);
        return File.Exists(Path.Combine(root, "runtime.json")) ? root : null;
    }

    /// <summary>
    /// MW3-RE supports 800, 1200 and 1600. Larger saved choices (made for the old runtime
    /// engine) use 1600, and the caller is told so; smaller unknown values are refused.
    /// </summary>
    public static int PreviewDrawDistance(int savedDrawDistance, out bool reduced)
    {
        reduced = savedDrawDistance > MaxDrawDistance;
        if (reduced) return MaxDrawDistance;
        if (savedDrawDistance is not (800 or 1200 or 1600))
            throw new InvalidOperationException("Choose a scenery distance of 800, 1200 or 1600 for MW3-RE.");
        return savedDrawDistance;
    }

    /// <summary>Split the enabled packs into the two kinds the native runtime reads.</summary>
    public static (List<string> Models, List<string> Environments) SelectPreviewPacks(IEnumerable<string> activeModDirs)
    {
        var models = new List<string>();
        var environments = new List<string>();
        foreach (var directory in activeModDirs)
        {
            var root = Path.GetFullPath(PackStorage.CanonicalPackRoot(directory));
            var manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
            // Music, interface and cinematic packs use separate launcher content steps.
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

    /// <summary>Plan and start one MW3-RE session; the caller owns the returned process.</summary>
    public Process Launch(LauncherSettings settings, IEnumerable<string> activeModDirs, Action<string>? log = null)
    {
        var session = Path.Combine(_dataRoot, "sessions", Guid.NewGuid().ToString("N"));
        // Guards the pending-log buffer shared by process reader threads and the launch thread.
        var logLock = new object();
        Directory.CreateDirectory(session);
        var logPath = Path.Combine(session, "mw3-re.log");
        var pendingLog = new List<string>();
        var logCreated = false;
        void Log(string line)
        {
            lock (logLock)
            {
                if (!logCreated) pendingLog.Add(line);
                else File.AppendAllText(logPath, line + Environment.NewLine);
            }
            // Lines arrive on process reader threads; a failing UI callback must not stop the
            // game's output from reaching the session log.
            try { log?.Invoke(line); }
            catch (Exception error) { Debug.WriteLine("Native log callback failed: " + error.Message); }
        }

        void PublishLog()
        {
            lock (logLock)
            {
                if (!logCreated)
                {
                    File.WriteAllText(logPath, "MW3-RE, launcher " +
                        typeof(NativeGameRunner).Assembly.GetName().Version + Environment.NewLine +
                        string.Join(Environment.NewLine, pendingLog) + Environment.NewLine);
                    pendingLog.Clear();
                    logCreated = true;
                }
                LastLogPath = logPath;
            }
        }

        // Keep updates and pack changes out of the active MW3-RE session.
        var gate = GameUpdateGate.Acquire(_dataRoot);
        try
        {
            var process = Start(settings, activeModDirs, Log);
            PublishLog();
            process.EnableRaisingEvents = true;
            process.Exited += (_, _) => gate.Dispose();
            if (process.HasExited) gate.Dispose();
            return process;
        }
        catch (Exception error)
        {
            gate.Dispose();
            Log("ERROR: " + error.Message);
            PublishLog();
            throw;
        }
    }

    private Process Start(LauncherSettings settings, IEnumerable<string> activeModDirs, Action<string> log)
    {
        var validation = GameValidator.Validate(settings.GamePath);
        if (!validation.IsValid) throw new InvalidOperationException("Cannot launch game: " + validation.StatusMessage);
        if (!string.IsNullOrWhiteSpace(settings.ModularContentProfile))
        {
            var profileProcess = ModProfiles.Launch(settings, validation.GameDirectory, _dataRoot, log);
            return profileProcess;
        }

        var root = FindRuntimeRoot() ?? throw new FileNotFoundException("This installation has no MW3-RE runtime.");
        var contract = Mw3ReRuntimeContract.ReadStructure(root);
        var controllerProfile = new ControllerProfiles(_dataRoot).Load();
        if (controllerProfile.Enabled && !contract.SupportsControllerProfiles)
            throw new InvalidOperationException("The installed MW3-RE runtime does not support controller profiles.");
        var planner = Path.Combine(_basePath, PlannerFolder, "mw3_re_launch.py");
        if (!File.Exists(planner)) throw new FileNotFoundException("The MW3-RE planner is missing.", planner);
        var python = NativeRuntimeLayout.FindInstalled(_basePath, _dataRoot)?.Python
            ?? D7VkRunner.FindPythonExecutable(requirePython311: true)
            ?? throw new FileNotFoundException("MW3-RE needs Python 3.11 or newer.");

        var drawDistance = PreviewDrawDistance(settings.DrawDistance, out var reduced);
        if (reduced) log($"Scenery distance {settings.DrawDistance} is not supported; using {drawDistance}.");
        var activePacks = activeModDirs.ToList();
        var (models, environments) = SelectPreviewPacks(activePacks);
        var writeDirectory = Path.Combine(_dataRoot, "mw3-re", "profiles", ProfileId);
        Directory.CreateDirectory(writeDirectory);
        NativeControls.PrepareLaunch(_dataRoot, writeDirectory, validation.GameDirectory, settings, log);
        var headlightBindings = new HeadlightBindings(_dataRoot)
            .WriteNativeBinding(writeDirectory, settings.DynamicLighting && settings.Headlights);
        var options = new Mw3RePlanningOptions
        {
            Width = settings.Width,
            Height = settings.Height,
            Antialiasing = PreviewAntialiasing(settings.AntiAliasing),
            AnisotropicFiltering = settings.AnisotropicFiltering,
            WindowMode = WindowModeForSettings(settings.WindowMode),
            RenderThread = settings.RenderThread,
            Lighting = Mw3ReLighting.Normal,
            Pom = true,
            Preview = new Mw3RePreviewOptions
            {
                DrawDistance = drawDistance,
                ModelPacks = models,
                EnvironmentPacks = environments,
                DynamicLighting = settings.DynamicLighting,
                Headlights = settings.Headlights && settings.DynamicLighting,
                HeadlightBindings = headlightBindings,
                StockEffectCatalog = contract.FindDeclaredFile("resources/stock-effect-lights.bin"),
                StockHeadlightCatalog = contract.FindDeclaredFile("resources/stock-headlights.bin")
            }
        };
        var request = Mw3ReLaunchRequest.Create(contract, options, validation.GameDirectory, _dataRoot, ProfileId);
        var plan = RunPlanner(python, planner, request);
        if (!plan.RootElement.GetProperty("ok").GetBoolean())
        {
            var reasons = plan.RootElement.GetProperty("reasons").EnumerateArray().Select(item => item.GetString());
            throw new InvalidOperationException("MW3-RE cannot start: " + string.Join("; ", reasons));
        }
        if (plan.RootElement.TryGetProperty("skipped_packs", out var skipped))
            foreach (var item in skipped.EnumerateArray())
            {
                var feature = item.TryGetProperty("feature", out var selectedFeature)
                    ? selectedFeature.GetString() + " left off; " : "Pack left out; ";
                log(feature + item.GetProperty("root").GetString() + " (" +
                    item.GetProperty("reason").GetString() + ")");
            }
        // Two enabled mech packs can both supply a chassis; the earlier pack in the list keeps it.
        if (plan.RootElement.TryGetProperty("overridden_models", out var overridden))
            foreach (var item in overridden.EnumerateArray())
                log("Mech " + item.GetProperty("chassis").GetString() + " from " + item.GetProperty("root").GetString() +
                    " left out; using the one from " + item.GetProperty("kept_from").GetString());

        var argv = plan.RootElement.GetProperty("argv").EnumerateArray().Select(item => item.GetString()!).ToList();
        if (controllerProfile.Enabled)
        {
            string controllerPath = NativeControls.ControllerProfilePath(writeDirectory);
            if (!File.Exists(controllerPath))
                throw new InvalidOperationException("The enabled controller profile was not exported for this session.");
            argv.AddRange(NativeControls.ControllerArguments(controllerProfile, controllerPath));
        }
        // Music is optional: a broken or locked soundtrack file must not stop the game from starting.
        try
        {
            MusicPack.StageForNative(activePacks, writeDirectory, log);
        }
        catch (Exception error) when (error is IOException or InvalidDataException or UnauthorizedAccessException or JsonException)
        {
            log("Music pack not used for this launch: " + error.Message);
        }
        var start = new ProcessStartInfo(argv[0])
        {
            WorkingDirectory = plan.RootElement.GetProperty("working_directory").GetString()!,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };
        foreach (var argument in argv.Skip(1)) start.ArgumentList.Add(argument);
        log($"Starting MW3-RE: {settings.Width}x{settings.Height}, scenery {drawDistance}, " +
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
        // Read both pipes asynchronously so the timeout below can still fire if the planner hangs;
        // a blocking read would keep the launch (and its update gate) waiting forever.
        var output = process.StandardOutput.ReadToEndAsync();
        var errors = process.StandardError.ReadToEndAsync();
        process.StandardInput.Write(request);
        process.StandardInput.Close();
        if (!process.WaitForExit(30000))
        {
            process.Kill(entireProcessTree: true);
            throw new TimeoutException("The MW3-RE planner did not finish.");
        }
        process.WaitForExit(); // Let the asynchronous readers reach end of stream.
        if (process.ExitCode != 0)
        {
            // The planner reports invalid choices as a ValueError on its last error line.
            var last = errors.Result.Split('\n', StringSplitOptions.RemoveEmptyEntries).LastOrDefault()?.Trim();
            throw new InvalidOperationException("The MW3-RE settings were refused: " + (last ?? "planner error"));
        }
        return JsonDocument.Parse(output.Result);
    }
}
