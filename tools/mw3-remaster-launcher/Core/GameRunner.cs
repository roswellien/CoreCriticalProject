using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core
{
    public class GameRunner
    {
        private readonly string _basePath;
        public string? LastLogPath { get; private set; }

        public GameRunner(string basePath)
        {
            _basePath = basePath;
        }

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

        public Process? LaunchGame(LauncherSettings settings, List<string> activeModDirs, Action<string>? logCallback = null)
        {
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

            var rootDir = FindRepositoryRoot(_basePath);
            if (string.IsNullOrEmpty(rootDir))
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

            var psScript = Path.Combine(rootDir, @"tools\remaster-launcher\play_native.ps1");
            var profileJson = Path.Combine(rootDir, @"local\remaster\launcher.json");

            if (!File.Exists(psScript) || !File.Exists(profileJson))
            {
                throw new FileNotFoundException($"Could not locate Remaster host launcher scripts in: {rootDir}");
            }

            // Each launch owns its settings snapshot; never rewrite the published host profile.
            var profile = CreateLaunchProfile(File.ReadAllText(profileJson), settings);
            var runDir = Path.Combine(rootDir, "local", "remaster", "launcher-runs", Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(runDir);
            var launchProfile = Path.Combine(runDir, "profile.json");
            File.WriteAllText(launchProfile, profile.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
            var logPath = Path.Combine(runDir, "launcher.log");
            LastLogPath = logPath;
            var python = D7VkRunner.FindPythonExecutable(requirePillow: true)
                ?? throw new FileNotFoundException("Native asset preparation needs Python 3.11 or newer with a working Pillow image library. No compatible runtime could be loaded.");
            var startInfo = new ProcessStartInfo
            {
                FileName = python,
                WorkingDirectory = rootDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            foreach (var argument in new[] { "-u", Path.Combine(rootDir, @"tools\remaster-launcher\play_remaster.py"),
                "--backend", "native", "--profile", launchProfile, "--game-exe", validation.ExecutablePath,
                "--instant-replay", settings.InstantReplay ? "1" : "0",
                "--asset-output", Path.Combine(rootDir, "local", "remaster", "prepared-launcher") })
                startInfo.ArgumentList.Add(argument);
            bool modelsEnabled = activeModDirs.Exists(dir =>
                File.Exists(Path.Combine(dir, "pack.json")) &&
                JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "pack.json")))?["id"]?.GetValue<string>() == "com.mw3remaster.upgraded-mechs");
            if (!modelsEnabled) startInfo.ArgumentList.Add("--original-models");

            var logLock = new object();
            void Log(string? line)
            {
                if (line == null) return;
                lock (logLock) File.AppendAllText(logPath, line + Environment.NewLine);
                logCallback?.Invoke(line);
            }
            Log($"Preparing native Remaster: {settings.Width}x{settings.Height}, models {(modelsEnabled ? "updated" : "original")}. Logs: {logPath}");
            Log($"Asset preparation runtime: {python}");
            var process = new Process { StartInfo = startInfo };
            process.OutputDataReceived += (_, e) => Log(e.Data);
            process.ErrorDataReceived += (_, e) => Log(e.Data);
            if (!process.Start()) throw new InvalidOperationException("The native launcher did not start.");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            return process;
        }

        public static JsonObject CreateLaunchProfile(string publishedJson, LauncherSettings settings)
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
            return profile;
        }
    }
}
