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

    public static bool UsesBundledMw3Re(string applicationDirectory)
    {
        var marker = Path.Combine(applicationDirectory, "launcher-installation.json");
        if (File.Exists(marker))
        {
            using var document = JsonDocument.Parse(LauncherUpdates.ReadMetadata(marker));
            if (document.RootElement.TryGetProperty("native_runtime", out var runtime) &&
                runtime.GetString() == "mw3-re")
                return true;
        }

        return File.Exists(Path.Combine(applicationDirectory, RuntimeFolder, "runtime.json"));
    }

    public string RequireBundledMw3Re()
    {
        var root = FindRuntimeRoot() ?? throw new FileNotFoundException(
            "The bundled MW3-RE runtime is missing. Repair the Core Critical installation.");
        var planner = Path.Combine(_basePath, PlannerFolder, "mw3_re_launch.py");
        if (!File.Exists(planner))
            throw new FileNotFoundException("The MW3-RE planner is missing. Repair the Core Critical installation.", planner);
        return root;
    }

    public const string ProfileId = "native-preview";
    /// <summary>The largest scenery distance the native runtime accepts in this release.</summary>
    public const int MaxDrawDistance = 3200;

    private readonly string _basePath;
    private readonly string _dataRoot;

    public NativeGameRunner(string basePath, string? dataRoot = null)
    {
        _basePath = basePath;
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
    }

    public string? LastLogPath { get; private set; }
    public string? LastRuntimeVersion { get; private set; }

    /// <summary>
    /// Milliseconds from process start to the game's first frame in the latest launch, or
    /// null when it never drew one. Problems logged before it are startup noise.
    /// </summary>
    public long? LastFirstFrameMilliseconds { get; private set; }
    public Task<int>? LastSessionCompletion { get; private set; }

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

    public string FindPlannerPython()
    {
        var bundled = Path.Combine(_basePath, "Tools", "PlannerPython", "python.exe");
        if (File.Exists(bundled))
        {
            PackStorage.EnsureNoLinks(bundled);
            if (!D7VkRunner.CanPrepareNativeAssets(bundled, requirePillow: false))
                throw new InvalidDataException("The bundled planner Python is incomplete. Repair the Core Critical installation.");
            return bundled;
        }

        var runtimeDirectory = Path.Combine(_basePath, "Runtime");
        var legacyPython = File.Exists(Path.Combine(runtimeDirectory, "runtime.json"))
            ? NativeRuntimeLayout.ReadRoot(runtimeDirectory).Python
            : null;
        return legacyPython ?? D7VkRunner.FindPythonExecutable(requirePython311: true)
            ?? throw new FileNotFoundException("MW3-RE needs Python 3.11 or newer. Repair the Core Critical installation.");
    }

    /// <summary>
    /// MW3-RE supports 800, 1200, 1600, 2400 and 3200 without reducing saved choices.
    /// Unknown values are refused before launch.
    /// </summary>
    public static int PreviewDrawDistance(int savedDrawDistance, out bool reduced)
    {
        reduced = false;
        if (savedDrawDistance is not (800 or 1200 or 1600 or 2400 or 3200))
            throw new InvalidOperationException(
                "Choose a scenery distance of 800, 1200, 1600, 2400 or 3200 for MW3-RE.");
        return savedDrawDistance;
    }

    /// <summary>Split the enabled packs into the two kinds the native runtime reads.</summary>
    public static (List<string> Models, List<string> Environments) SelectPreviewPacks(IEnumerable<string> activeModDirs)
    {
        var models = new List<string>();
        var environments = new List<string>();
        foreach (var directory in activeModDirs)
        {
            string root;
            PackManifest manifest;
            try
            {
                root = Path.GetFullPath(PackStorage.CanonicalPackRoot(directory));
                manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or
                ArgumentException or NotSupportedException)
            {
                // An unreadable optional pack must not prevent the native session from starting.
                continue;
            }
            // UI packs are selected separately; music and cinematic packs use other content steps.
            if (manifest.SchemaVersion != 2) continue;
            if (manifest.NativePayload?.Profile == "prepared-native-v1") models.Add(root);
            else if (manifest.NativePayload?.Profile == "prepared-environment-v1") environments.Add(root);
        }
        return (models, environments);
    }

    /// <summary>Return enabled prepared UI packs for the native planner to validate and route.</summary>
    public static List<string> SelectUiPacks(IEnumerable<string> activeModDirs, Action<string>? log = null)
    {
        var result = new List<string>();
        foreach (var directory in activeModDirs)
        {
            try
            {
                var root = Path.GetFullPath(PackStorage.CanonicalPackRoot(directory));
                var manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
                if (manifest.SchemaVersion == 2 && manifest.NativePayload?.Profile == UiPack.Profile)
                    result.Add(root);
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException or
                JsonException or ArgumentException or NotSupportedException)
            {
                log?.Invoke("Pack left out; UI pack could not be read: " + directory +
                    " (" + error.Message + ")");
            }
        }
        return result;
    }

    /// <summary>The planner validates named skin packs against the selected native meshes.</summary>
    public static List<string> SelectSkinPacks(IEnumerable<string> activeModDirs, Action<string>? log = null)
    {
        var result = new List<string>();
        foreach (var directory in activeModDirs)
        {
            try
            {
                var root = Path.GetFullPath(PackStorage.CanonicalPackRoot(directory));
                var manifest = PackStorage.ReadManifest(Path.Combine(root, "pack.json"));
                if (manifest.SchemaVersion == 2 && manifest.NativePayload?.Profile == "prepared-skins-v1")
                    result.Add(root);
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException or
                JsonException or ArgumentException or NotSupportedException)
            {
                log?.Invoke("Pack left out; skin pack could not be read: " + directory +
                    " (" + error.Message + ")");
            }
        }
        return result;
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

    /// <summary>Project saved choices and prepared inputs; the planner applies shadow dependencies.</summary>
    public static Mw3RePlanningOptions PlanningOptionsForSettings(LauncherSettings settings,
        Mw3ReRuntimeContract contract, int drawDistance, IReadOnlyList<string> models,
        IReadOnlyList<string> environments, string? headlightBindings,
        IReadOnlyList<string>? uiPacks = null, IReadOnlyList<string>? skinPacks = null)
    {
        var selectedUiPacks = uiPacks ?? Array.Empty<string>();
        return new Mw3RePlanningOptions
        {
            Width = settings.Width,
            Height = settings.Height,
            Antialiasing = PreviewAntialiasing(settings.AntiAliasing),
            AnisotropicFiltering = settings.AnisotropicFiltering,
            WindowMode = WindowModeForSettings(settings.WindowMode),
            RenderThread = settings.RenderThread,
            Vsync = settings.Vsync,
            Lighting = Mw3ReLighting.Normal,
            FlareStyle = settings.FlareStyle switch
            {
                "modern" => Mw3ReFlareStyle.Modern,
                "original" => Mw3ReFlareStyle.Original,
                _ => throw new InvalidOperationException("Unknown lens flare style: " + settings.FlareStyle)
            },
            Pom = settings.PomQuality is "low" or "high",
            PomQuality = settings.PomQuality switch
            {
                "off" => null,
                "low" or "high" => settings.PomQuality,
                _ => throw new InvalidOperationException("Unknown parallax occlusion mapping quality: " + settings.PomQuality)
            },
            // The environment switch stays a support override for a saved "on".
            DiskCache = settings.LoadCache && Environment.GetEnvironmentVariable("MW3_DISK_CACHE") != "0",
            Preview = new Mw3RePreviewOptions
            {
                DrawDistance = drawDistance,
                ModelPacks = models,
                SkinPacks = skinPacks ?? Array.Empty<string>(),
                EnvironmentPacks = environments,
                UiPacks = selectedUiPacks,
                // The launcher has no HUD setting; UI artwork needs this HUD, otherwise the
                // runtime profile's saved cc_hud and cc_hud_text settings must apply.
                Hud = selectedUiPacks.Count > 0 ? "core-critical" : null,
                HudText = selectedUiPacks.Count > 0 ? true : null,
                DynamicLighting = settings.DynamicLighting,
                // Preserve the request so the planner can report why shadows were suppressed.
                Shadows = settings.Shadows,
                WaterDetail = settings.WaterDetail,
                CloudDetail = settings.CloudDetail,
                Headlights = settings.Headlights && settings.DynamicLighting,
                HeadlightBindings = headlightBindings,
                StockEffectCatalog = contract.FindDeclaredFile("resources/stock-effect-lights.bin"),
                StockHeadlightCatalog = contract.FindDeclaredFile("resources/stock-headlights.bin")
            }
        };
    }

    /// <summary>Plan and start one MW3-RE session; the caller owns the returned process.</summary>
    public Process Launch(LauncherSettings settings, IEnumerable<string> activeModDirs, Action<string>? log = null,
        IReadOnlyList<string>? extraArguments = null)
    {
        var session = Path.Combine(_dataRoot, "sessions", Guid.NewGuid().ToString("N"));
        // Guards the pending-log buffer shared by process reader threads and the launch thread.
        var logLock = new object();
        Directory.CreateDirectory(session);
        var logPath = Path.Combine(session, "mw3-re.log");
        var pendingLog = new List<string>();
        var logCreated = false;
        var launchClock = Stopwatch.StartNew();
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
                        PlaytestDiagnostics.LauncherVersionString(typeof(NativeGameRunner).Assembly) + Environment.NewLine +
                        string.Join(Environment.NewLine, pendingLog) + Environment.NewLine);
                    pendingLog.Clear();
                    logCreated = true;
                }
                LastLogPath = logPath;
            }
        }

        LastRuntimeVersion = null;
        LastFirstFrameMilliseconds = null;
        LastSessionCompletion = null;
        NativeSessionDiagnosticsBaseline? baseline = null;
        // Keep updates and pack changes out of the active MW3-RE session.
        var gate = GameUpdateGate.Acquire(_dataRoot);
        try
        {
            Log("Startup: Checking game files...");
            var process = Start(settings, activeModDirs, line =>
                Log($"{line} [launcher elapsed {launchClock.ElapsedMilliseconds} ms]"), session,
                capturedBaseline => baseline = capturedBaseline, extraArguments);
            PublishLog();
            async Task<int> ObserveSessionExitAsync()
            {
                try
                {
                    var exit = await GameRunner.WaitForCompletionAsync(process).ConfigureAwait(false);
                    // Copy the game's own log on every exit, not only crashes: a session that
                    // ran out of video memory can recover and exit cleanly, and Export Report
                    // reads this copy, so without it a clean exit exports no game log at all.
                    PlaytestDiagnostics.CollectNativeSessionArtifacts(baseline, session);
                    return exit;
                }
                finally
                {
                    gate.Dispose();
                }
            }

            LastSessionCompletion = ObserveSessionExitAsync();
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

    private Process Start(LauncherSettings settings, IEnumerable<string> activeModDirs, Action<string> log, string session,
        Action<NativeSessionDiagnosticsBaseline>? onBaseline, IReadOnlyList<string>? extraArguments)
    {
        var validation = GameValidator.Validate(settings.GamePath);
        if (!validation.IsValid) throw new InvalidOperationException("Cannot launch game: " + validation.StatusMessage);
        if (!string.IsNullOrWhiteSpace(settings.ModularContentProfile))
        {
            // Modular content profiles launch through ModProfiles.Launch, which builds its own
            // fixed argument list and cannot accept arena or replay flags.
            if (extraArguments is { Count: > 0 })
            {
                throw new InvalidOperationException(
                    "Turn off the MW3-RE modular content profile before running an AI Arena match or replay.");
            }
            LastRuntimeVersion = DescribeExternalRuntimeVersion(settings.ModularRuntimeExecutable);
            var profileProcess = ModProfiles.Launch(settings, validation.GameDirectory, _dataRoot, log,
                writeDir => onBaseline?.Invoke(PlaytestDiagnostics.CaptureNativeBaseline(writeDir)));
            return profileProcess;
        }

        log("Startup: Verifying native runtime...");
        var root = RequireBundledMw3Re();
        var contract = Mw3ReRuntimeContract.ReadStructure(root);
        LastRuntimeVersion = PlaytestDiagnostics.FormatRuntimeVersion(contract);
        var controllerProfile = new ControllerProfiles(_dataRoot).Load();
        if (controllerProfile.Enabled && !contract.SupportsControllerProfiles)
            throw new InvalidOperationException("The installed MW3-RE runtime does not support controller profiles.");
        var launchControls = ReadLaunchControls(contract, _dataRoot, settings);
        var planner = Path.Combine(_basePath, PlannerFolder, "mw3_re_launch.py");
        var python = FindPlannerPython();

        var drawDistance = PreviewDrawDistance(settings.DrawDistance, out _);
        var activePacks = activeModDirs.ToList();
        var (models, environments) = SelectPreviewPacks(activePacks);
        var uiPacks = SelectUiPacks(activePacks, log);
        var skinPacks = SelectSkinPacks(activePacks, log);
        var writeDirectory = Path.Combine(_dataRoot, "mw3-re", "profiles", ProfileId);
        log("Startup: Preparing controls...");
        var (inputBindings, headlightBindings) = PrepareLaunchControls(launchControls, _dataRoot,
            writeDirectory, validation.GameDirectory, settings, controllerProfile, log);
        var options = PlanningOptionsForSettings(settings, contract, drawDistance, models,
            environments, headlightBindings, uiPacks, skinPacks);
        var indeoCodec = GameInstallation.FindVerifiedIndeoCodec(validation.GameDirectory, _dataRoot);
        var request = Mw3ReLaunchRequest.Create(contract, options, validation.GameDirectory, _dataRoot,
            ProfileId, indeoCodec);
        log("Startup: Checking packs and planning native launch...");
        using var plan = RunPlanner(python, planner, request);
        log("Startup: Pack planning complete.");
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
        if (plan.RootElement.TryGetProperty("skipped_features", out var skippedFeatures))
            foreach (var item in skippedFeatures.EnumerateArray())
                log(item.GetProperty("feature").GetString() + " unavailable; " +
                    item.GetProperty("reason").GetString());
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
        if (inputBindings != null)
        {
            argv.Add("--cc-input");
            argv.Add(inputBindings);
        }
        // Music is optional: a broken or locked soundtrack file must not stop the game from starting.
        try
        {
            log("Startup: Preparing soundtrack...");
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
        ApplyCacheEnvironment(start, plan.RootElement);
        // The launcher can show the captured crash and offer a report after the process exits.
        start.Environment["MW3_LAUNCHER_WATCHES"] = "1";
        if (extraArguments is { Count: > 0 })
        {
            foreach (var extraArgument in extraArguments)
            {
                if (extraArgument == null)
                    throw new ArgumentException("Extra launch arguments cannot contain null entries.", nameof(extraArguments));
                argv.Add(extraArgument);
            }
        }
        var readyFile = Path.Combine(session, "native-ready");
        argv.AddRange(new[] { "--ready-file", readyFile });
        foreach (var argument in argv.Skip(1)) start.ArgumentList.Add(argument);
        log($"Starting MW3-RE: {settings.Width}x{settings.Height}, scenery {drawDistance}, " +
            $"{models.Count} model pack(s), {environments.Count} map pack(s).");
        var process = new Process { StartInfo = start };
        process.OutputDataReceived += (_, line) => { if (line.Data != null) log(line.Data); };
        process.ErrorDataReceived += (_, line) => { if (line.Data != null) log(line.Data); };
        Directory.CreateDirectory(writeDirectory);
        onBaseline?.Invoke(PlaytestDiagnostics.CaptureNativeBaseline(writeDirectory));
        if (!process.Start()) throw new InvalidOperationException("MW3-RE did not start.");
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();
        log("MW3-RE PID " + process.Id);
        _ = ObserveReadinessAsync(process, readyFile, log,
            milliseconds => LastFirstFrameMilliseconds = milliseconds);
        return process;
    }

    private static string DescribeExternalRuntimeVersion(string executablePath)
    {
        try
        {
            if (!string.IsNullOrWhiteSpace(executablePath))
            {
                var full = Path.GetFullPath(executablePath);
                if (File.Exists(full))
                {
                    var info = FileVersionInfo.GetVersionInfo(full);
                    var version = !string.IsNullOrWhiteSpace(info.ProductVersion) ? info.ProductVersion.Trim()
                        : !string.IsNullOrWhiteSpace(info.FileVersion) ? info.FileVersion.Trim() : null;
                    if (!string.IsNullOrEmpty(version))
                    {
                        var plus = version.IndexOf('+');
                        if (plus >= 0) version = version[..plus].Trim();
                        var label = $"external ({version})";
                        return label.Length <= 80 ? label : label[..80];
                    }
                }
            }
        }
        catch { }
        return "external";
    }

    /// <summary>Run the launch preflight and write-profile projection without starting a process.</summary>
    public static (string? InputBindingsPath, string? HeadlightBindingsPath) PrepareLaunchControls(
        Mw3ReRuntimeContract contract, string dataRoot, string writeDirectory, string gameDirectory,
        LauncherSettings settings, ControllerProfile controllerProfile, Action<string> log) =>
        PrepareLaunchControls(ReadLaunchControls(contract, dataRoot, settings), dataRoot, writeDirectory,
            gameDirectory, settings, controllerProfile, log);

    private static (ControlProfile? Profile, HeadlightBinding? Headlights) ReadLaunchControls(
        Mw3ReRuntimeContract contract, string dataRoot, LauncherSettings settings)
    {
        var profile = NativeControls.LoadSelectedProfile(dataRoot);
        var headlights = settings.DynamicLighting && settings.Headlights
            ? new HeadlightBindings(dataRoot).Load() : null;
        var needsExtendedInput = (profile != null && ControlProfiles.UsesExtendedInputBindings(profile)) ||
            headlights?.Mouse > 0;
        if (needsExtendedInput && !contract.SupportsInputBindings)
            throw new InvalidOperationException(
                "The installed MW3-RE runtime does not support extended input bindings. Update MW3-RE to use this controls layout or mouse headlight binding.");
        return (profile, headlights);
    }

    private static (string? InputBindingsPath, string? HeadlightBindingsPath) PrepareLaunchControls(
        (ControlProfile? Profile, HeadlightBinding? Headlights) bindings, string dataRoot,
        string writeDirectory, string gameDirectory, LauncherSettings settings,
        ControllerProfile controllerProfile, Action<string> log)
    {
        var inputPath = NativeControls.PrepareLaunch(dataRoot, writeDirectory, gameDirectory,
            settings, bindings.Profile, controllerProfile, log);
        var headlightPath = HeadlightBindings.WriteNativeBinding(writeDirectory, bindings.Headlights);
        return (inputPath, headlightPath);
    }

    /// <summary>Only the planner's typed cache switch may change the child environment.</summary>
    public static void ApplyCacheEnvironment(ProcessStartInfo start, JsonElement plan)
    {
        if (!plan.TryGetProperty("environment", out var environment)) return; // Older planner.
        if (environment.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("Invalid native cache environment.");
        foreach (var item in environment.EnumerateObject())
        {
            if (item.Name != "MW3_DISK_CACHE" || item.Value.ValueKind != JsonValueKind.String ||
                item.Value.GetString() is not ("0" or "1"))
                throw new InvalidDataException("Unsupported native cache environment.");
            start.Environment[item.Name] = item.Value.GetString();
        }
    }

    /// <summary>
    /// Follows the game's ready/status files (they work even when the GUI native host sends its
    /// stdout to its own log) until the main menu is on screen, logging timings and progress.
    /// </summary>
    public static async Task ObserveReadinessAsync(Process process, string readyFile, Action<string> log,
        Action<long>? onFirstFrame = null)
    {
        var clock = Stopwatch.StartNew();
        string lastStatus = "";
        bool shown = false, menu = false;
        try
        {
            while (!process.HasExited)
            {
                string status = "";
                try
                {
                    var path = readyFile + ".status";
                    if (File.Exists(path))
                    {
                        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                            FileShare.ReadWrite | FileShare.Delete);
                        if (stream.Length <= 4096) status = await new StreamReader(stream).ReadToEndAsync();
                    }
                }
                catch (IOException) { } // The atomic writer may be replacing the status.
                if (status != lastStatus)
                {
                    log(status.Length == 0 ? "Native progress: idle" : "Native progress: " + status);
                    lastStatus = status;
                }
                if (!shown && File.Exists(readyFile))
                {
                    shown = true;
                    var firstFrameMilliseconds = clock.ElapsedMilliseconds;
                    onFirstFrame?.Invoke(firstFrameMilliseconds);
                    log($"Native first frame: {firstFrameMilliseconds} ms after process start");
                }
                if (!menu && File.Exists(readyFile + ".menu"))
                {
                    menu = true;
                    log($"Native menu ready: {clock.ElapsedMilliseconds} ms after process start");
                    return;  // Startup is over; later mission loads show in the game itself.
                }
                await Task.Delay(100);
            }
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or
            InvalidOperationException or ObjectDisposedException)
        {
            log("Native readiness observation ended: " + error.Message);
        }
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
