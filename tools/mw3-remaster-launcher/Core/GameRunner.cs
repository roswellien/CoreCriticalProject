using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization.Metadata;

namespace MW3RemasterLauncher.Core
{
    /// <summary>Translate native-launcher settings into one isolated launch session.</summary>
    /// <remarks>
    /// The published host profile is read-only. Each call writes a profile/log below
    /// the per-user sessions directory and delegates asset preparation to play_remaster.py.
    /// Host admission and gameplay acceptance belong to the native pipeline, not this UI adapter.
    /// </remarks>
    public class GameRunner
    {
        private readonly string _basePath;
        private readonly string _dataRoot;
        public string? LastLogPath { get; private set; }

        public GameRunner(string basePath, string? dataRoot = null)
        {
            _basePath = basePath;
            _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
        }

        /// <summary>Walk ancestors for the private native profile and launch script together.</summary>
        public static string? FindRepositoryRoot(string startDir)
        {
            try
            {
                var cur = new DirectoryInfo(startDir);
                while (cur != null)
                {
                    if (File.Exists(Path.Combine(cur.FullName, @"local\remaster\launcher.json")) &&
                        File.Exists(Path.Combine(cur.FullName, @"tools\remaster-launcher\play_native.ps1")))
                    {
                        return cur.FullName;
                    }
                    cur = cur.Parent;
                }
            }
            catch { }

            return null;
        }

        /// <summary>Prepare arguments and start the native launch coordinator.</summary>
        /// <returns>The started coordinator process; the caller owns its lifetime.</returns>
        /// <remarks>
        /// Output callbacks run on process-reader threads; UI callers must marshal updates.
        /// Enabled prepared-native packs are verified and composed by the native coordinator.
        /// Starting the coordinator does not mean the game has finished preparing or loading.
        /// </remarks>
        public Process? LaunchGame(LauncherSettings settings, List<string> activeModDirs, Action<string>? logCallback = null)
        {
            var session = Path.Combine(_dataRoot, "sessions", Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(session);
            LastLogPath = Path.Combine(session, "launcher.log");
            File.WriteAllText(LastLogPath, "Launcher " + typeof(GameRunner).Assembly.GetName().Version + Environment.NewLine);
            try { return LaunchGameCore(settings, activeModDirs, session, logCallback); }
            catch (Exception ex)
            {
                File.AppendAllText(LastLogPath, "ERROR: " + ex.Message + Environment.NewLine);
                throw;
            }
        }

        private Process LaunchGameCore(LauncherSettings settings, List<string> activeModDirs, string runDir, Action<string>? logCallback)
        {
            // MSIX AppData redirection can expose a different pack to a child
            // outside this process's context. Pass physical manifest roots.
            activeModDirs = activeModDirs.Select(PackStorage.CanonicalPackRoot).ToList();
            // Verify game path
            var validation = GameValidator.Validate(settings.GamePath);
            if (!validation.IsValid)
            {
                throw new InvalidOperationException($"Cannot launch game: {validation.StatusMessage}");
            }

            // Check if game is already running
            var running = Process.GetProcessesByName("entry_commandline");
            if (running.Length > 0)
            {
                throw new InvalidOperationException("A MechWarrior 3 Remaster session is already running.");
            }

            var installed = NativeRuntimeLayout.FindInstalled(_basePath, _dataRoot);
            var rootDir = installed?.Root ?? FindRepositoryRoot(_basePath);
            if (installed == null && string.IsNullOrEmpty(rootDir))
            {
                // Fallback check
                var candidate = Path.GetFullPath(Path.Combine(_basePath, @"..\..\..\.."));
                if (File.Exists(Path.Combine(candidate, @"local\remaster\launcher.json")))
                {
                    rootDir = candidate;
                }
            }

            if (string.IsNullOrEmpty(rootDir))
            {
                throw new FileNotFoundException("Could not locate repository root directory (missing local\\remaster\\launcher.json).");
            }

            var psScript = installed == null ? Path.Combine(rootDir, @"tools\remaster-launcher\play_native.ps1")
                : Path.Combine(Path.GetDirectoryName(installed.Coordinator)!, "play_native.ps1");
            var profileJson = installed?.Profile ?? Path.Combine(rootDir, @"local\remaster\launcher.json");

            if (!File.Exists(psScript) || !File.Exists(profileJson))
            {
                throw new FileNotFoundException($"Could not locate Remaster host launcher scripts in: {rootDir}");
            }

            // Each launch owns its settings snapshot; never rewrite the published host profile.
            var profileText = File.ReadAllText(profileJson);
            if (installed != null) profileText = NativeRuntimeLayout.ResolveProfile(profileText, installed.Root, validation.GameDirectory);
            var profile = CreateLaunchProfile(profileText, settings,
                Path.Combine(_dataRoot, "cache", "pipeline-warmup-v1"));
            profile["native"]!["content_capabilities"] = RuntimeContentCapabilities.Advertised(profile["native"]!.AsObject());
            NativeRuntimeLayout.ValidateLaunchExecutable(Path.GetFullPath(profile["native"]!["executable"]!.GetValue<string>(), rootDir));
            if (installed != null)
            {
                var provider = GameInstallation.FindProvider(validation.GameDirectory, _dataRoot)
                    ?? throw new FileNotFoundException("Original support files are missing. Run Set Up Game and select your ISO when prompted.");
                profile["native"]!["launch_inputs"]!["crt_provider"] = provider;
                if (profile["native"]!["original_support_versions"] != null)
                    GameInstallation.BindSupportFiles(profile, validation.GameDirectory, _dataRoot);
                PlayerRegistry.PrepareInstalledRenderer(profile, _dataRoot, validation.GameDirectory);
            }
            if (installed == null && profile["native"]!["music_decoder"] == null)
            {
                var musicConfig = Path.Combine(rootDir, "local", "remaster", "music.json");
                if (File.Exists(musicConfig))
                {
                    var name = JsonNode.Parse(File.ReadAllText(musicConfig))?["decoder"]?.GetValue<string>();
                    if (name != null) profile["native"]!["music_decoder"] = Path.GetFullPath(Path.Combine(rootDir, name));
                }
            }
            MusicPack.Apply(profile, activeModDirs, settings.LocalCdAudio);
            UiPack.Apply(profile, activeModDirs);
            CinematicPack.Apply(profile, activeModDirs, runDir, validation.GameDirectory);
            // Empty is deliberate: disable all optional replacements without loading the development registry.
            var roots = new JsonArray();
            var environmentRoots = new JsonArray();
            foreach (var directory in activeModDirs)
            {
                var manifest = PackStorage.ReadManifest(Path.Combine(directory, "pack.json"));
                if (manifest.NativePayload?.Profile is MusicPack.Profile or UiPack.Profile or CinematicPack.Profile) continue;
                if (manifest.SchemaVersion == 2 && manifest.NativePayload?.Profile == "prepared-environment-v1")
                    environmentRoots.Add(Path.GetFullPath(directory));
                else if (manifest.SchemaVersion == 2) roots.Add(Path.GetFullPath(directory));
                else if (manifest.Provides?.Mechs?.Count > 0)
                    throw new InvalidDataException("This mech pack needs conversion to prepared-native-v1: " + manifest.Name);
            }
            profile["native"]!["prepared_pack_roots"] = roots;
            ApplyEnvironmentSelection(profile, environmentRoots, installed != null, settings.EnvironmentPackSelectionInitialized);
            profile["native"]!["launch_session_directory"] = Path.GetFullPath(runDir);
            new ControlProfiles(_dataRoot).PrepareLaunch(profile, _dataRoot, validation.GameDirectory);
            new ControllerProfiles(_dataRoot).PrepareLaunch(profile, runDir);
            var launchProfile = Path.Combine(runDir, "profile.json");
            File.WriteAllText(launchProfile, SerializeLaunchProfile(profile));
            var logPath = Path.Combine(runDir, "launcher.log");
            var python = installed?.Python ?? D7VkRunner.FindPythonExecutable(requirePython311: true)
                ?? throw new FileNotFoundException("The native launch coordinator needs Python 3.11 or newer. No compatible runtime could be loaded.");
            var startInfo = new ProcessStartInfo
            {
                FileName = python,
                WorkingDirectory = rootDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            foreach (var argument in new[] { "-u", installed?.Coordinator ?? Path.Combine(rootDir, @"tools\remaster-launcher\play_remaster.py"),
                "--backend", "native", "--profile", launchProfile, "--game-exe", validation.ExecutablePath,
                "--instant-replay", settings.InstantReplay ? "1" : "0",
                "--asset-output", Path.Combine(_dataRoot, "cache", "prepared") })
                startInfo.ArgumentList.Add(argument);
            // Redirected Python output otherwise uses the Windows ANSI code page,
            // while the launcher's reader expects UTF-8 startup status messages.
            startInfo.Environment["PYTHONIOENCODING"] = "utf-8";
            if (installed != null)
            {
                startInfo.ArgumentList.Add("--runtime-root");
                startInfo.ArgumentList.Add(installed.Root);
                startInfo.Environment.Remove("PYTHONHOME");
                startInfo.Environment.Remove("PYTHONPATH");
                startInfo.Environment["PYTHONNOUSERSITE"] = "1";
                startInfo.Environment["PYTHONDONTWRITEBYTECODE"] = "1";
            }
            var logLock = new object();
            void Log(string? line)
            {
                if (line == null) return;
                lock (logLock) File.AppendAllText(logPath, line + Environment.NewLine);
                logCallback?.Invoke(line);
            }
            Log($"Preparing native Remaster: {settings.Width}x{settings.Height}, prepared mech packs {roots.Count}. Logs: {logPath}");
            Log($"Asset preparation runtime: {python}");
            var process = new Process { StartInfo = startInfo };
            process.OutputDataReceived += (_, e) => Log(e.Data);
            process.ErrorDataReceived += (_, e) => Log(e.Data);
            if (!process.Start()) throw new InvalidOperationException("The native launcher did not start.");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            return process;
        }

        public static async System.Threading.Tasks.Task<int> WaitForCompletionAsync(Process process)
        {
            await process.WaitForExitAsync();
            process.WaitForExit(); // Drain redirected output callbacks before reading their log.
            return process.ExitCode;
        }

        /// <summary>Keep an existing development setup until its first environment-pack selection.</summary>
        public static void ApplyEnvironmentSelection(JsonObject profile, JsonArray roots, bool installed, bool initialized)
        {
            // Installed players always use explicit pack choices. Only the existing
            // development upgrade may retain its published environment bindings.
            if (installed || initialized || roots.Count > 0)
                profile["native"]!["prepared_environment_pack_roots"] = roots;
            else
                profile["native"]!.AsObject().Remove("prepared_environment_pack_roots");
        }

        /// <summary>Serialize parsed and newly authored nodes with an explicit reflection resolver.</summary>
        public static string SerializeLaunchProfile(JsonObject profile)
        {
            // JsonArray.Add(string) creates a node requiring type metadata. Parsed
            // JSON alone does not exercise that path, so set the resolver explicitly.
            return profile.ToJsonString(new JsonSerializerOptions
            {
                WriteIndented = true,
                TypeInfoResolver = new DefaultJsonTypeInfoResolver()
            });
        }

        /// <summary>Build a private settings snapshot while retaining published host identity.</summary>
        /// <remarks>
        /// AA "off" maps to one raster sample; "fxaa" remains a named mode.
        /// This validates UI choices; the coordinator separately checks host capabilities.
        /// </remarks>
        public static JsonObject CreateLaunchProfile(string publishedJson, LauncherSettings settings,
            string? pipelineWarmupDirectory = null)
        {
            var profile = JsonNode.Parse(publishedJson)?.AsObject()
                ?? throw new InvalidOperationException("Native profile is empty.");
            var graphics = profile["graphics"]?.AsObject()
                ?? throw new InvalidOperationException("Native profile has no graphics settings.");
            if (settings.Width < 640 || settings.Height < 480 || settings.Width > 7680 || settings.Height > 4320)
                throw new InvalidOperationException("Requested resolution is outside the renderer's output limits.");
            if (settings.AntiAliasing != "fxaa" && settings.AntiAliasing != "off" && settings.AntiAliasing != "1" && settings.AntiAliasing != "2" && settings.AntiAliasing != "4")
                throw new InvalidOperationException("Unknown anti-aliasing setting.");
            if (settings.WindowMode != "fullscreen_windowed" && settings.WindowMode != "fullscreen" && settings.WindowMode != "windowed")
                throw new InvalidOperationException("Unknown display window mode.");
            graphics["width"] = settings.Width;
            graphics["height"] = settings.Height;
            graphics["aa"] = settings.AntiAliasing == "fxaa" ? JsonValue.Create("fxaa") : JsonValue.Create(settings.AntiAliasing == "off" ? 1 : int.Parse(settings.AntiAliasing));
            graphics["af"] = settings.AnisotropicFiltering;
            graphics["draw_distance"] = settings.DrawDistance;
            graphics["fog_distance"] = settings.FogDistance;
            graphics["window_mode"] = settings.WindowMode;
            profile["native"]!["local_cd_audio"] = settings.LocalCdAudio;
            if (settings.PerformanceMonitor && profile["native"]!["performance_monitor_version"]?.GetValue<int>() != 1)
                throw new InvalidOperationException("This runtime needs the performance monitor update. Install it through Game Updates, or turn off the monitor to use this version.");
            // An explicit saved choice overrides both old profiles and inherited diagnostics.
            profile["native"]!["runtime_environment"] ??= new JsonObject();
            profile["native"]!["runtime_environment"]!["MW34_PERF_OVERLAY"] = settings.PerformanceMonitor ? "1" : "0";
            // Emit the existing native register/return-chain diagnostics only
            // when a guest memory fault occurs, including on remote playtest PCs.
            profile["native"]!["runtime_environment"]!["MW34_SEH_LOG"] = "1";
            if (pipelineWarmupDirectory != null)
            {
                if (!Path.IsPathFullyQualified(pipelineWarmupDirectory))
                    throw new InvalidOperationException("Pipeline warmup cache needs an absolute user-data path.");
                profile["native"]!["runtime_environment"]!["MW34_PIPELINE_WARMUP_DIR"] = pipelineWarmupDirectory;
                profile["native"]!["runtime_environment"]!["MW34_PIPELINE_WARMUP"] = "1";
                profile["native"]!["runtime_environment"]!["MW34_NORMAL_PREWARM"] = "1";
            }
            return profile;
        }
    }
}
