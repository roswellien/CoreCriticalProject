using System.IO;
using MW3RemasterLauncher.Core;
using System.Text.Json.Nodes;

if(args.Length==3 && args[0]=="--check-update-notification") { UpdateNotificationUiChecks.Run(args[1],args[2]); return; }

if(args.Length==1 && args[0]=="--steam-only") { SteamShortcutChecks.Run(); return; }
if(args.Length==4 && args[0]=="--add-steam-shortcut")
{
    var result=SteamHelper.AddToSteam(args[1],args[2]);
    File.WriteAllText(args[3],System.Text.Json.JsonSerializer.Serialize(result));
    Console.WriteLine("Steam shortcut verified and installed for the selected local profile.");return;
}

if(args.Length==1 && args[0]=="--online-updates-only") { OnlineUpdateChecks.Run(); await UpdateDownloadChecks.Run(); return; }
if(args.Length==1 && args[0]=="--playtest-support-only")
{
    PlaytestSupportChecks.Run();
    await CrashReportServiceChecks.RunAsync();
    return;
}

if(args.Length==1 && args[0]=="--chassis-only") { ChassisPackChecks.Run(); return; }
if(args.Length==3 && args[0]=="--install-chassis-pack") { ChassisPackChecks.Install(args[1],args[2]); return; }

if(args.Length==1 && args[0]=="--skins-only") { SkinPackChecks.Run(); return; }
if(args.Length==3 && args[0]=="--install-skin-pack") { SkinPackChecks.Install(args[1],args[2]); return; }

if(args.Length==3&&args[0]=="--check-loading-indicator")
{
    LoadingIndicatorUiChecks.Run(args[1],args[2]);return;
}

if(args.Length==2&&args[0]=="--check-headlight-controls") { GraphicsSetupUiChecks.RunHeadlights(args[1]);return; }

if(args.Length==3&&args[0]=="--check-graphics-setup")
{
    GraphicsSetupUiChecks.Run(args[1],args[2]);return;
}

if (args.Length is 5 or 6 && args[0] == "--prepare-presentation-profile")
{
    if (args[2] is not ("on" or "off")) throw new ArgumentException("Lighting must be on or off");
    var output = Path.GetFullPath(args[4]);
    Directory.CreateDirectory(Path.GetDirectoryName(output)!);
    var graphicsProfile = GameRunner.CreateLaunchProfile(File.ReadAllText(args[1]),
        new LauncherSettings { Width = 3440, Height = 1440, DynamicLighting = args[2] == "on" });
    var contentRoots = args.Length == 6
        ? System.Text.Json.JsonSerializer.Deserialize<string[]>(File.ReadAllText(args[5]))!
        : Array.Empty<string>();
    GameRunner.ApplyContentSelection(graphicsProfile, contentRoots, true,
        Path.GetDirectoryName(output)!, Path.GetFullPath(args[3]));
    File.WriteAllText(output, GameRunner.SerializeLaunchProfile(graphicsProfile));
    Console.WriteLine("Explicit launcher content and graphics profile prepared.");
    return;
}

if (args.Length == 2 && args[0] == "--verify-media-tools")
{
    GameInstallation.VerifyExtractor(Path.GetFullPath(args[1]));
    Console.WriteLine("Published media extractor matches the pinned executable, including certificate-only signing changes.");
    return;
}

if (args.Length == 4 && args[0] == "--prepare-installed-renderer")
{
    var path = Path.GetFullPath(args[3]);
    var rendererProfile = JsonNode.Parse(File.ReadAllText(path))!.AsObject();
    PlayerRegistry.PrepareInstalledRenderer(rendererProfile, Path.GetFullPath(args[1]), Path.GetFullPath(args[2]));
    File.WriteAllText(path, GameRunner.SerializeLaunchProfile(rendererProfile)); return;
}

if (args.Length == 4 && args[0] == "--prepare-controller-launch")
{
    var path = Path.GetFullPath(args[3]);
    var launch = JsonNode.Parse(File.ReadAllText(path))!.AsObject();
    new ControllerProfiles(Path.GetFullPath(args[1])).PrepareLaunch(launch, Path.GetFullPath(args[2]));
    File.WriteAllText(path, GameRunner.SerializeLaunchProfile(launch)); return;
}

if (args.Length == 1 && args[0] == "--runtime-layout-only")
{
    NativeRuntimeLayoutChecks.Run();
    return;
}
if (args.Length == 1 && args[0] == "--content-only")
{
    ChassisPackChecks.Run();
    SkinPackChecks.Run();
    PackStorageChecks.Run();
    EnvironmentPackChecks.Run();
    MusicPackChecks.Run();
    ArtworkCinematicChecks.Run();
    return;
}
if (args.Length == 1 && args[0] == "--artwork-only")
{
    ArtworkCinematicChecks.Run();
    return;
}
if (args.Length == 1 && args[0] == "--controllers-only")
{
    ControllerChecks.Run(); ControllerChecks.Sdl(); return;
}
if (args.Length == 1 && args[0] == "--joystick-only")
{
    JoystickSelectionChecks.Run(); return;
}
if (args.Length == 2 && args[0] == "--preview-controller")
{
    var thread = new Thread(() =>
    {
        var app = new MW3RemasterLauncher.App(false); app.InitializeComponent();
        app.Run(new MW3RemasterLauncher.ControllerWindow(Path.GetFullPath(args[1])));
    });
    thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join(); return;
}

if (args.Length == 1 && args[0] == "--controls-only")
{
    ControlProfileChecks.Run(); return;
}
if (args.Length == 3 && args[0] == "--preview-controls")
{
    var root = Path.GetFullPath(args[1]);
    var thread = new Thread(() =>
    {
        var app = new MW3RemasterLauncher.App(false); app.InitializeComponent();
        app.Run(new MW3RemasterLauncher.ControlsWindow(root, Path.GetFullPath(args[2])) { Title = "Controls — isolated UI trial" });
    });
    thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join(); return;
}
if (args.Length == 4 && args[0] == "--prepare-controls-profile")
{
    var store = new ControlProfiles(Path.GetFullPath(args[1]));
    var doc = store.Load();
    var preset = ControlProfiles.ImportRegistry(File.ReadAllText(Path.GetFullPath(args[2])), args[3]);
    doc.Profiles.Add(preset); doc.ActiveId = preset.Id; store.Save(doc); return;
}
if (args.Length == 4 && args[0] == "--prepare-controls-launch")
{
    LauncherUpdates.RequireGamesClosed();
    var profilePath = Path.GetFullPath(args[3]);
    var controlsLaunch = JsonNode.Parse(File.ReadAllText(profilePath))!.AsObject();
    new ControlProfiles(Path.GetFullPath(args[1])).PrepareLaunch(controlsLaunch, Path.GetFullPath(args[1]), Path.GetFullPath(args[2]));
    File.WriteAllText(profilePath, GameRunner.SerializeLaunchProfile(controlsLaunch)); return;
}

// Maintainer repair: use the same bounded/transactional importer as the UI.
// Run in the player's Windows context when MSIX AppData redirection differs.
if (args.Length == 4 && args[0] == "--refresh-installed-mech-pack")
{
    LauncherUpdates.RequireGamesClosed();
    var dataRoot = Path.GetFullPath(args[1]);
    var archive = Path.GetFullPath(args[2]);
    string id;
    using (var zip = System.IO.Compression.ZipFile.OpenRead(archive))
    {
        var entry = zip.GetEntry("pack.json") ?? throw new InvalidDataException("Missing pack manifest.");
        if (entry.Length > PackStorage.MaxJsonBytes) throw new InvalidDataException("Pack manifest too large.");
        using var reader = new StreamReader(entry.Open());
        id = JsonNode.Parse(reader.ReadToEnd())!["id"]!.GetValue<string>();
    }
    if (id is not ("com.mw3remaster.updated-mw3-mechs" or "com.mw3remaster.mw5-mechs"))
        throw new InvalidDataException("This repair only refreshes existing MW3 mech collections.");
    var mods = Path.Combine(dataRoot, "mods");
    var before = Path.Combine(mods, id, "pack.json");
    if (!File.Exists(before)) throw new InvalidDataException("The target mech collection is not already installed.");
    PackStorage.EnsureNoLinks(before);
    var beforeHash = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(before)));
    var installed = PackStorage.Install(mods, archive);
    var registry = JsonNode.Parse(File.ReadAllText(Path.Combine(installed.DirectoryPath, "models", "models.json")))!;
    var bindings = registry["models"]!.AsArray().Sum(model => model!["environment"]!.AsObject().Count(pair => pair.Key.Contains("_SKIN_")));
    File.WriteAllText(args[3], System.Text.Json.JsonSerializer.Serialize(new {
        installed.Id, installed.Version, installed.DirectoryPath, alternate_bindings = bindings,
        before_manifest_sha256 = beforeHash,
        rollback = Path.Combine(mods, ".rollback-" + installed.Id),
        settings_modified = false, native_started = false
    }));
    Console.WriteLine($"Refreshed {installed.Id}: {bindings} alternate texture bindings; previous pack retained.");
    return;
}

if (args.Length >= 2 && args[0] == "--preview-corecritical")
{
    var root = Path.GetFullPath(args[1]);
    var fixtureSettings = new SettingsManager(root, root);
    fixtureSettings.Current.InitialSetupCompleted = true;
    fixtureSettings.Current.GamePath = args.Length >= 3 ? Path.GetFullPath(args[2]) : root; fixtureSettings.Save();
    var thread = new Thread(() =>
    {
        var application = new MW3RemasterLauncher.App(false); application.InitializeComponent();
        var window = new MW3RemasterLauncher.MainWindow(root) { Title = "Core Critical — UI trial" };
        window.Loaded += (_, _) => ((System.Windows.Controls.RadioButton)window.FindName("TabMods")).IsChecked = true;
        if (args.Length > 3)
        {
            window.Loaded += async (_, _) =>
            {
                var samples = new List<object>();
                var timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
                timer.Tick += (_, _) =>
                {
                    if (samples.Count >= 1000) return;
                    var bar = (System.Windows.Controls.ProgressBar)window.FindName("ProgressAssetInstall");
                    samples.Add(new {
                        status = ((System.Windows.Controls.TextBlock)window.FindName("TxtStatusReady")).Text,
                        detail = ((System.Windows.Controls.TextBlock)window.FindName("TxtAssetInstallProgress")).Text,
                        percent = bar.Value,
                        visible = bar.IsVisible,
                        launch_enabled = ((System.Windows.Controls.Button)window.FindName("BtnLaunchGame")).IsEnabled
                    });
                };
                timer.Start();
                try
                {
                    var method = typeof(MW3RemasterLauncher.MainWindow).GetMethod("InstallPacksAsync",
                        System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)!;
                    await (Task<int>)method.Invoke(window, new object[] { args.Skip(3).ToArray() })!;
                }
                finally
                {
                    timer.Stop();
                    File.WriteAllText(Path.Combine(root, "asset-install-ui-samples.json"),
                        System.Text.Json.JsonSerializer.Serialize(samples));
                }
            };
        }
        application.Run(window);
    });
    thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join();
    return;
}

if (args.Length == 6 && args[0] == "--check-precompiled-update")
{
    var updates = new RuntimeUpdates(args[1], RuntimeUpdates.ReadTrust(args[1]), args[3]);
    if (updates.State().Active != null) throw new InvalidOperationException("Use an isolated update store.");
    var update = updates.Verify(File.ReadAllBytes(args[4]));
    await updates.PrepareAsync(update, args[2], args[5], new Progress<string>(Console.WriteLine));
    var selected = RuntimeUpdates.SelectedRoot(args[1], args[3])
        ?? throw new InvalidDataException("Precompiled update was not activated.");
    RuntimeUpdates.ValidateGeneratedRuntime(selected);
    updates.Rollback();
    if (updates.State().Active != null || updates.State().HighestSequence != update.Manifest.Sequence)
        throw new InvalidDataException("Precompiled rollback or sequence retention failed.");
    Console.WriteLine("Signed precompiled update verified, installed, activated, validated and rolled back.");
    return;
}

if (args.Length == 2 && args[0] == "--verify-bundled-preparation")
{
    var updates = new RuntimeUpdates(args[1], RuntimeUpdates.ReadTrust(args[1]));
    var update = updates.Verify(File.ReadAllBytes(Path.Combine(args[1], "Preparation", "initial.mw3update")));
    using var archive = File.OpenRead(Path.Combine(args[1], "Preparation", "initial.zip"));
    if (archive.Length != update.Manifest.PackageBytes ||
        !Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(archive)).Equals(update.Manifest.PackageSha256, StringComparison.OrdinalIgnoreCase))
        throw new InvalidDataException("Bundled source archive differs from signed metadata.");
    Console.WriteLine("Bundled source preparation signature and v2 input contract verified: " + update.Manifest.Version);
    return;
}
if (args.Length == 4 && args[0] == "--prepare-bundled")
{
    await BundledPreparation.PrepareAsync(args[1], args[2], new Progress<string>(Console.WriteLine), dataRoot: args[3]);
    Console.WriteLine("Bundled source preparation and runtime activation passed.");
    return;
}

if (args.Length == 2 && args[0] == "--validate-runtime")
{
    RuntimeUpdates.ValidateGeneratedRuntime(args[1]);
    Console.WriteLine("Prepared runtime passed the launcher's complete file and startup validation.");
    return;
}

if (args.Length >= 6 && args[0] == "--game")
{
    await RuntimeUpdateChecks.GenerateFixture(args);
    return;
}

if (args.Length == 4 && args[0] == "--prepare-support")
{
    try
    {
        var inputs = GameInstallation.PrepareSupportFiles(args[1], args[2]);
        File.WriteAllText(args[3], System.Text.Json.JsonSerializer.Serialize(inputs));
        Console.WriteLine("Original support images prepared from verified user files.");
    }
    catch (Exception error) when (error is IOException or InvalidDataException)
    { Console.Error.WriteLine(error.Message); Environment.ExitCode = 2; }
    return;
}
if (args.Length == 2 && args[0] == "--watch-cinematic-pack")
{
    var clips = CinematicPack.Library(new[] { args[1] });
    var uiThread = new Thread(() => new System.Windows.Application().Run(new MW3RemasterLauncher.CinematicWindow(clips)));
    uiThread.SetApartmentState(ApartmentState.STA); uiThread.Start(); uiThread.Join();
    return;
}
if (args.Length == 4 && args[0] == "--import-support-iso")
{
    await GameInstallation.ImportProviderIsoAsync(args[1], args[2], args[3]);
    Console.WriteLine("Original support file imported into the user cache.");
    return;
}
if ((args.Length == 4 && args[0] == "--launch-installed-trial") ||
    (args.Length == 5 && args[0] == "--launch-installed-content"))
{
    var layout = NativeRuntimeLayout.FindInstalled(args[1]) ?? throw new Exception("No installed runtime.");
    var runner = new GameRunner(args[1], args[3]);
    var trialSettings = new LauncherSettings { GamePath = args[2], LocalCdAudio = false };
    var trialPacks = new List<string>();
    if (args.Length == 5)
    {
        var input = JsonNode.Parse(File.ReadAllText(args[4]))!;
        trialSettings.LocalCdAudio = true;
        trialSettings.MusicTrack2 = input["music_track_2"]!.GetValue<string>();
        trialSettings.MusicTrack3 = input["music_track_3"]!.GetValue<string>();
        trialPacks = input["packs"]!.AsArray().Select(p => p!.GetValue<string>()).ToList();
    }
    using var process = runner.LaunchGame(trialSettings, trialPacks, Console.WriteLine)
        ?? throw new Exception("Installed coordinator did not start.");
    var exit = await GameRunner.WaitForCompletionAsync(process);
    Console.WriteLine("Installed trial exit: " + exit + "; log: " + runner.LastLogPath);
    Environment.ExitCode = exit;
    return;
}
if (args.Length >= 4 && args[0] == "--write-installed-profile")
{
    var layout = NativeRuntimeLayout.FindInstalled(args[1]) ?? throw new Exception("No installed runtime.");
    var text = NativeRuntimeLayout.ResolveProfile(File.ReadAllText(layout.Profile), layout.Root, args[2]);
    var trial = GameRunner.CreateLaunchProfile(text, new LauncherSettings { LocalCdAudio = false });
    if (trial["native"]!["original_support_versions"] != null)
        GameInstallation.BindSupportFiles(trial, args[2], Path.GetDirectoryName(Path.GetFullPath(args[3]))!);
    if (args.Length > 4) MusicPack.Apply(trial, args.Skip(4), true);
    UiPack.Apply(trial, args.Skip(4));
    CinematicPack.Apply(trial, args.Skip(4), Path.GetDirectoryName(Path.GetFullPath(args[3]))!, args[2]);
    File.WriteAllText(args[3], GameRunner.SerializeLaunchProfile(trial));
    Console.WriteLine("Installed trial profile resolved without repository discovery: " + args[3]);
    return;
}
if (args.Length == 2 && args[0] == "--verify-original")
{
    await GameInstallation.VerifyExistingAsync(args[1]);
    Console.WriteLine("Complete supported original-data closure verified.");
    return;
}
if (args.Length == 5 && (args[0] == "--install-original-source" || args[0] == "--install-original-iso"))
{
    if (args[0] == "--install-original-iso")
        await GameInstallation.InstallIsoAsync(args[1], args[2], args[3], args[4]);
    else
        await GameInstallation.InstallDirectoryAsync(args[1], args[2], args[3], args[4]);
    Console.WriteLine("Original-data installation verified: " + args[3]);
    return;
}
if (args.Length == 3 && args[0] == "--export-current-report")
{
    var currentSettings = new SettingsManager(args[1]);
    var currentPacks = new PackManager(LauncherPaths.DataRoot);
    currentPacks.RefreshPacks(currentSettings.Current.ActivePacks);
    PlaytestDiagnostics.Export(args[2], currentSettings.Current, currentPacks.Packs,
        LauncherPaths.LatestLaunchLog(), args[1]);
    Console.WriteLine("Local support export passed: " + args[2]);
    return;
}

if (args.Length > 0 && args[0] == "--install-packs")
{
    var manager = new PackManager(args[1]);
    foreach (var archive in args.Skip(2))
    {
        var pack = manager.InstallPack(archive);
        Console.WriteLine("Installed " + pack.Id + " at " + pack.DirectoryPath);
    }
    return;
}
var profilesOnly = args.Length == 2 && args[0] == "--profile-only";
if (profilesOnly) args = new[] { args[1] };
if (args.Length > 0 && args[0].StartsWith("--", StringComparison.Ordinal) && args[0] != "--check-native-runtime")
    throw new ArgumentException("Unknown check command or incorrect argument count: " + args[0]);
if (!profilesOnly)
{
PackStorageChecks.Run();
UniversalLauncherChecks.Run();
SteamShortcutChecks.Run();
OnlineUpdateChecks.Run();
await UpdateDownloadChecks.Run();
EnvironmentPackChecks.Run();
MusicPackChecks.Run();
GraphicsPreferencesChecks.Run();
ArtworkCinematicChecks.Run();
PlaytestSupportChecks.Run();
GameInstallationChecks.Run();
GameValidatorChecks.Run();
OriginalSupportChecks.Run();
PlayerRegistryChecks.Run();
ControlProfileChecks.Run();
ControllerChecks.Run();
JoystickSelectionChecks.Run();
SaveBackupChecks.Run();
NativeRuntimeLayoutChecks.Run();
await RuntimeUpdateChecks.Run();
}

if (args.Length > 0 && args[0] == "--check-native-runtime")
{
    // Caller can disable user packages to reproduce an interpreter that exists
    // but cannot import Pillow. Selection must continue to a working runtime.
    if (args.Length > 1 && D7VkRunner.CanPrepareNativeAssets(args[1]))
        throw new Exception("The negative-control interpreter unexpectedly has Pillow.");
    var runtime = D7VkRunner.FindPythonExecutable(requirePillow: true);
    if (runtime == null || !D7VkRunner.CanPrepareNativeAssets(runtime))
        throw new Exception("No usable native asset runtime selected.");
    Console.WriteLine("Native dependency selection passed: " + runtime);
    return;
}

var published = args.Length > 0 ? File.ReadAllText(Path.Combine(args[0], "local/remaster/launcher.json"))
    : """{"graphics":{"width":3440,"height":1440},"native":{"executable_sha256":"authored-test-identity"}}""";
var settings = new LauncherSettings { Width = 3440, Height = 1440, WindowMode = "fullscreen_windowed" };
var profile = GameRunner.CreateLaunchProfile(published, settings);
Check(profile["native"]!["runtime_environment"]!["MW34_SEH_LOG"]!.GetValue<string>() == "1",
    "Remote native memory-fault diagnostics were not enabled");
GameRunner.ApplyEnvironmentSelection(profile, new JsonArray(), false, false);
if (profile["native"]!["prepared_environment_pack_roots"]!.AsArray().Count != 0)
    throw new Exception("Empty development selection inherited optional environment bindings.");
GameRunner.ApplyEnvironmentSelection(profile, new JsonArray(), true, false);
if (profile["native"]!["prepared_environment_pack_roots"]!.AsArray().Count != 0)
    throw new Exception("Fresh installed selection inherited development content.");
GameRunner.ApplyEnvironmentSelection(profile, new JsonArray(), false, true);
if (profile["native"]!["prepared_environment_pack_roots"] == null)
    throw new Exception("Disabling all environment packs restored legacy content.");
GameRunner.ApplyEnvironmentSelection(profile, new JsonArray("authored-environment-pack"), false, false);
if (profile["native"]!["prepared_environment_pack_roots"]![0]!.GetValue<string>() != "authored-environment-pack")
    throw new Exception("First environment pack was not selected.");
profile["native"]!["prepared_pack_roots"] = new JsonArray(Path.Combine(Path.GetTempPath(), "authored pack root"));
var serializedProfile = GameRunner.SerializeLaunchProfile(profile);
if (JsonNode.Parse(serializedProfile)!["native"]!["prepared_pack_roots"]![0]!.GetValue<string>() != Path.Combine(Path.GetTempPath(), "authored pack root"))
    throw new Exception("Serialized installed-pack root changed");
void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
Check(profile["native"]!["runtime_environment"]!["MW34_PERF_OVERLAY"]!.GetValue<string>() == "0", "Monitor must default off");
Check(!new LauncherSettings().RenderThread, "New installations must default to the render thread off");
Check(profile["native"]!["runtime_environment"]!["MW34_RENDER_THREAD"]!.GetValue<string>() == "0", "Render thread must default off");
Check(!new LauncherSettings().DynamicLighting, "New installations must default to stock lighting");
Check(!profile["native"]!["presentation"]!["dynamic_lighting"]!.GetValue<bool>(), "Stock lighting choice missing");
settings.DynamicLighting = true;
settings.Shadows = true;
Check(GameRunner.CreateLaunchProfile(serializedProfile, settings)["native"]!["presentation"]!["dynamic_lighting"]!.GetValue<bool>(), "Lighting on choice lost");
Check(GameRunner.CreateLaunchProfile(serializedProfile, settings)["native"]!["presentation"]!["shadows"]!.GetValue<bool>(), "Shadow on choice lost");
settings.DynamicLighting = false;
Check(!GameRunner.CreateLaunchProfile(serializedProfile, settings)["native"]!["presentation"]!["dynamic_lighting"]!.GetValue<bool>(), "Lighting off choice lost");
Check(GameRunner.CreateLaunchProfile(serializedProfile, settings)["native"]!["presentation"]!["shadows"]!.GetValue<bool>(), "Lighting off erased saved shadow choice");
settings.Headlights=true;settings.DynamicLighting=true;
try {GameRunner.CreateLaunchProfile(serializedProfile,settings);throw new Exception("Old runtime accepted enabled headlights");}
catch(InvalidOperationException){}
var headlightProfile=JsonNode.Parse(serializedProfile)!.AsObject();
headlightProfile["native"]!["stock_presentation_versions"]=new JsonArray(1,2);
var withHeadlights=GameRunner.CreateLaunchProfile(headlightProfile.ToJsonString(),settings);
Check(withHeadlights["native"]!["presentation"]!["schema_version"]!.GetValue<int>()==2 &&
    withHeadlights["native"]!["presentation"]!["headlights"]!.GetValue<bool>(),"Headlight policy v2 missing");
settings.DynamicLighting=false;
var olderOff=GameRunner.CreateLaunchProfile(serializedProfile,settings);
Check(olderOff["native"]!["presentation"]!["schema_version"]!.GetValue<int>()==1,"Disabled lighting broke old runtime");
settings.Headlights=false;

settings.Shadows = false;
var pipelineCache = Path.Combine(Path.GetTempPath(), "authored pipeline warmup cache");
var cacheProfile = GameRunner.CreateLaunchProfile(serializedProfile, settings, pipelineCache);
Check(cacheProfile["native"]!["runtime_environment"]!["MW34_PIPELINE_WARMUP_DIR"]!.GetValue<string>() == pipelineCache, "Pipeline cache escaped user storage");
Check(cacheProfile["native"]!["runtime_environment"]!["MW34_PIPELINE_WARMUP"]!.GetValue<string>() == "1", "Pipeline warmup binding lost");
Check(cacheProfile["native"]!["runtime_environment"]!["MW34_NORMAL_PREWARM"]!.GetValue<string>() == "1", "Mission normal warmup binding lost");
try { GameRunner.CreateLaunchProfile(serializedProfile, settings, "relative-cache"); throw new Exception("Relative cache path accepted"); }
catch (InvalidOperationException) { }
settings.PerformanceMonitor = true;
var oldMonitorProfile = JsonNode.Parse(serializedProfile)!.AsObject();
oldMonitorProfile["native"]!.AsObject().Remove("performance_monitor_version");
try { GameRunner.CreateLaunchProfile(oldMonitorProfile.ToJsonString(), settings); throw new Exception("Old runtime advertised the new monitor"); }
catch (InvalidOperationException) { }
var monitorSource = JsonNode.Parse(serializedProfile)!;
monitorSource["native"]!["performance_monitor_version"] = 1;
var monitorProfile = GameRunner.CreateLaunchProfile(monitorSource.ToJsonString(), settings);
Check(monitorProfile["native"]!["runtime_environment"]!["MW34_PERF_OVERLAY"]!.GetValue<string>() == "1", "Monitor on choice lost");
settings.PerformanceMonitor = false;
Check(GameRunner.CreateLaunchProfile(monitorProfile.ToJsonString(), settings)["native"]!["runtime_environment"]!["MW34_PERF_OVERLAY"]!.GetValue<string>() == "0", "Stale profile re-enabled monitor");
settings.RenderThread = false;
var threadOffProfile = GameRunner.CreateLaunchProfile(serializedProfile, settings);
Check(threadOffProfile["native"]!["runtime_environment"]!["MW34_RENDER_THREAD"]!.GetValue<string>() == "0", "Render thread off choice lost");
settings.RenderThread = true;
Check(GameRunner.CreateLaunchProfile(threadOffProfile.ToJsonString(), settings)["native"]!["runtime_environment"]!["MW34_RENDER_THREAD"]!.GetValue<string>() == "1", "Stale profile kept the render thread off");
var monitorSettingsRoot = Path.Combine(Path.GetTempPath(), "MW3MonitorSettings-" + Guid.NewGuid().ToString("N"));
try {
    var monitorSettings = new SettingsManager(monitorSettingsRoot, monitorSettingsRoot);
    monitorSettings.Current.PerformanceMonitor = true;
    monitorSettings.Current.DynamicLighting = true;
    monitorSettings.Save();
    Check(new SettingsManager(monitorSettingsRoot, monitorSettingsRoot).Current.PerformanceMonitor, "Monitor setting did not persist");
    Check(new SettingsManager(monitorSettingsRoot, monitorSettingsRoot).Current.DynamicLighting, "Lighting setting did not persist");
    monitorSettings.Current.DynamicLighting = false;
    monitorSettings.Current.RenderThread = false;
    monitorSettings.Save();
    Check(!new SettingsManager(monitorSettingsRoot, monitorSettingsRoot).Current.DynamicLighting, "Lighting off setting did not persist");
    Check(!new SettingsManager(monitorSettingsRoot, monitorSettingsRoot).Current.RenderThread, "Render thread off setting did not persist");
} finally { if (Directory.Exists(monitorSettingsRoot)) Directory.Delete(monitorSettingsRoot, true); }
Check(profile["graphics"]!["width"]!.GetValue<int>() == 3440, "Lost requested width");
Check(profile["graphics"]!["window_mode"]!.GetValue<string>() == "fullscreen_windowed", "Borderless choice was not preserved");
Check(profile["native"]!["executable_sha256"]!.ToString() == JsonNode.Parse(published)!["native"]!["executable_sha256"]!.ToString(), "Changed host identity");
settings.Width = 1920; settings.WindowMode = "windowed"; settings.AntiAliasing = "off"; settings.LocalCdAudio = false;
profile = GameRunner.CreateLaunchProfile(published, settings);
Check(profile["graphics"]!["aa"]!.GetValue<int>() == 1, "AA off was not normalized");
Check(profile["graphics"]!["window_mode"]!.GetValue<string>() == "windowed", "Windowed mode lost");
Check(!profile["native"]!["local_cd_audio"]!.GetValue<bool>(), "Music toggle lost");
settings.Height = 1080; settings.AntiAliasing = "4";
profile = GameRunner.CreateLaunchProfile(published, settings);
Check(profile["graphics"]!["height"]!.GetValue<int>() == 1080, "1080p output was discarded");
Check(profile["graphics"]!["aa"]!.GetValue<int>() == 4, "SSAA choice was discarded");
settings.WindowMode = "fullscreen";
Check(GameRunner.CreateLaunchProfile(published, settings)["graphics"]!["window_mode"]!.GetValue<string>() == "fullscreen", "Exclusive choice was discarded");
settings.Width = 0;
try { GameRunner.CreateLaunchProfile(published, settings); throw new Exception("Invalid resolution accepted"); }
catch (InvalidOperationException) { }
var folder = Path.Combine(Path.GetTempPath(), "MW3LauncherChecks-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(Path.Combine(folder, "mods", "com.mw3remaster.upgraded-mechs"));
File.WriteAllText(Path.Combine(folder, "mods", "com.mw3remaster.upgraded-mechs", "pack.json"), "{\"id\":\"com.mw3remaster.upgraded-mechs\"}");
var packs = new PackManager(folder);
packs.RefreshPacks(null); Check(packs.GetActivePackIds().Count == 0, "First-run selection must be stock");
packs.RefreshPacks(new()); Check(packs.GetActivePackIds().Count == 0, "Empty saved selection re-enabled models");
packs.RefreshPacks(new() { "com.mw3remaster.upgraded-mechs" }); Check(packs.GetActivePackDirectories().Count == 1, "Model pack selection lost");
Directory.Delete(folder, true);
if (args.Length > 0) Check(published == File.ReadAllText(Path.Combine(args[0], "local/remaster/launcher.json")), "Published profile was modified");
if (args.Length > 1) File.WriteAllText(args[1], GameRunner.CreateLaunchProfile(published, new LauncherSettings { Width = 3440, Height = 1440 }).ToJsonString());
Console.WriteLine("Launcher profile and pack-selection checks passed.");
