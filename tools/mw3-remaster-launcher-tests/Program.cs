using System.IO;
using MW3RemasterLauncher.Core;
using System.Text.Json.Nodes;

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
PackStorageChecks.Run();
EnvironmentPackChecks.Run();
MusicPackChecks.Run();
ArtworkCinematicChecks.Run();
PlaytestSupportChecks.Run();
GameInstallationChecks.Run();
OriginalSupportChecks.Run();
PlayerRegistryChecks.Run();
SaveBackupChecks.Run();
NativeRuntimeLayoutChecks.Run();
await RuntimeUpdateChecks.Run();

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
GameRunner.ApplyEnvironmentSelection(profile, new JsonArray(), false, false);
if (profile["native"]!["prepared_environment_pack_roots"] != null)
    throw new Exception("Development upgrade discarded its existing environment bindings.");
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
packs.RefreshPacks(null); Check(packs.GetActivePackIds().Count == 1, "First-run default lost");
packs.RefreshPacks(new()); Check(packs.GetActivePackIds().Count == 0, "Empty saved selection re-enabled models");
packs.RefreshPacks(new() { "com.mw3remaster.upgraded-mechs" }); Check(packs.GetActivePackDirectories().Count == 1, "Model pack selection lost");
Directory.Delete(folder, true);
if (args.Length > 0) Check(published == File.ReadAllText(Path.Combine(args[0], "local/remaster/launcher.json")), "Published profile was modified");
if (args.Length > 1) File.WriteAllText(args[1], GameRunner.CreateLaunchProfile(published, new LauncherSettings { Width = 3440, Height = 1440 }).ToJsonString());
Console.WriteLine("Launcher profile and pack-selection checks passed.");
