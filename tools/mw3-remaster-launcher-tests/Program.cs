using System.IO;
using MW3RemasterLauncher.Core;
using System.Text.Json.Nodes;

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
Directory.CreateDirectory(Path.Combine(folder, "mods", "models"));
File.WriteAllText(Path.Combine(folder, "mods", "models", "pack.json"), "{\"id\":\"com.mw3remaster.upgraded-mechs\"}");
var packs = new PackManager(folder);
packs.RefreshPacks(null); Check(packs.GetActivePackIds().Count == 1, "First-run default lost");
packs.RefreshPacks(new()); Check(packs.GetActivePackIds().Count == 0, "Empty saved selection re-enabled models");
packs.RefreshPacks(new() { "com.mw3remaster.upgraded-mechs" }); Check(packs.GetActivePackDirectories().Count == 1, "Model pack selection lost");
Directory.Delete(folder, true);
if (args.Length > 0) Check(published == File.ReadAllText(Path.Combine(args[0], "local/remaster/launcher.json")), "Published profile was modified");
if (args.Length > 1) File.WriteAllText(args[1], GameRunner.CreateLaunchProfile(published, new LauncherSettings { Width = 3440, Height = 1440 }).ToJsonString());
Console.WriteLine("Launcher profile and pack-selection checks passed.");
