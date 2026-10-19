using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;

namespace MW3RemasterLauncher.Core
{
    public class GameRunner
    {
        private readonly string _basePath;

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

            // Sync user settings into local/remaster/launcher.json so graphics settings take effect immediately
            try
            {
                var jsonText = File.ReadAllText(profileJson);
                using var doc = JsonDocument.Parse(jsonText);
                var rootDict = JsonSerializer.Deserialize<Dictionary<string, object>>(jsonText) ?? new();

                if (rootDict.TryGetValue("graphics", out var graphicsObj))
                {
                    var gfxDict = JsonSerializer.Deserialize<Dictionary<string, object>>(graphicsObj.ToString() ?? "{}") ?? new();
                    gfxDict["width"] = settings.Width;
                    gfxDict["height"] = settings.Height;
                    gfxDict["aa"] = settings.AntiAliasing;
                    gfxDict["af"] = settings.AnisotropicFiltering;
                    gfxDict["draw_distance"] = settings.DrawDistance;
                    gfxDict["fog_distance"] = settings.FogDistance;
                    gfxDict["window_mode"] = settings.WindowMode;
                    rootDict["graphics"] = gfxDict;

                    var updatedJson = JsonSerializer.Serialize(rootDict, new JsonSerializerOptions { WriteIndented = true });
                    File.WriteAllText(profileJson, updatedJson);
                }
            }
            catch { }

            var startInfo = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-NoProfile -ExecutionPolicy Bypass -File \"{psScript}\" -Profile \"{profileJson}\" -InstantReplay {(settings.InstantReplay ? "1" : "0")}",
                WorkingDirectory = rootDir,
                UseShellExecute = false,
                RedirectStandardOutput = false,
                RedirectStandardError = false,
                CreateNoWindow = true
            };

            // Set environment variables
            startInfo.EnvironmentVariables["MW34_GAME_EXE"] = validation.ExecutablePath;
            startInfo.EnvironmentVariables["MW34_WINDOW_MODE"] = settings.WindowMode;
            startInfo.EnvironmentVariables["MW34_REMASTER_DRAW_DISTANCE"] = settings.DrawDistance.ToString();
            startInfo.EnvironmentVariables["MW34_REMASTER_FOG_DISTANCE"] = settings.FogDistance.ToString();
            startInfo.EnvironmentVariables["MW34_WIDTH"] = settings.Width.ToString();
            startInfo.EnvironmentVariables["MW34_HEIGHT"] = settings.Height.ToString();
            startInfo.EnvironmentVariables["MW34_AA"] = settings.AntiAliasing;
            startInfo.EnvironmentVariables["MW34_AF"] = settings.AnisotropicFiltering.ToString();
            startInfo.EnvironmentVariables["MW34_INSTANT_REPLAY"] = settings.InstantReplay ? "1" : "0";

            if (activeModDirs.Count > 0)
            {
                startInfo.EnvironmentVariables["MW34_ACTIVE_MODS"] = string.Join(";", activeModDirs);
            }

            logCallback?.Invoke($"Launching Remaster host: {settings.Width}x{settings.Height}, Draw Distance {settings.DrawDistance}m, Game: {validation.ExecutablePath}...");

            var process = Process.Start(startInfo);
            return process;
        }
    }
}
