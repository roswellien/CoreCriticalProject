using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;

namespace MW3RemasterLauncher.Core
{
    public class D7VkValidationResult
    {
        public bool IsValid { get; set; }
        public string StatusMessage { get; set; } = string.Empty;
        public string? PythonPath { get; set; }
        public string? WrapperScriptPath { get; set; }
        public string? GameExePath { get; set; }
    }

    public class D7VkRunner
    {
        private readonly string _basePath;

        public D7VkRunner(string basePath)
        {
            _basePath = basePath;
        }

        public static string? FindPythonExecutable()
        {
            // 1. Check common PATH command
            var candidateNames = new[] { "python.exe", "py.exe" };
            var pathEnv = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
            var paths = pathEnv.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries);

            foreach (var p in paths)
            {
                foreach (var name in candidateNames)
                {
                    try
                    {
                        var full = Path.Combine(p.Trim(), name);
                        if (File.Exists(full))
                        {
                            return full;
                        }
                    }
                    catch { }
                }
            }

            // 2. Check well-known installation paths
            var wellKnown = new[]
            {
                @"C:\Python314\python.exe",
                @"C:\Python313\python.exe",
                @"C:\Python312\python.exe",
                @"C:\Python311\python.exe",
                @"C:\Python310\python.exe",
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Python\Python314\python.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Python\Python313\python.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Python\Python312\python.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Python\Python311\python.exe")
            };

            foreach (var candidate in wellKnown)
            {
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }

            return null;
        }

        public D7VkValidationResult Validate()
        {
            var res = new D7VkValidationResult();
            var rootDir = GameRunner.FindRepositoryRoot(_basePath);
            if (string.IsNullOrEmpty(rootDir))
            {
                var candidate = Path.GetFullPath(Path.Combine(_basePath, @"..\..\..\.."));
                if (File.Exists(Path.Combine(candidate, "mw3_launcher.py")))
                {
                    rootDir = candidate;
                }
            }

            if (string.IsNullOrEmpty(rootDir))
            {
                res.IsValid = false;
                res.StatusMessage = "Repository root directory could not be located.";
                return res;
            }

            var scriptPath = Path.Combine(rootDir, "mw3_launcher.py");
            if (!File.Exists(scriptPath))
            {
                res.IsValid = false;
                res.StatusMessage = "D7VK launcher script (mw3_launcher.py) not found.";
                return res;
            }
            res.WrapperScriptPath = scriptPath;

            var gameExe = Path.Combine(rootDir, @"local\work-ahead\mw3-d7vk-wrapper\game\Mech3.exe");
            if (!File.Exists(gameExe))
            {
                res.IsValid = false;
                res.StatusMessage = "Admitted original Mech3.exe not found in D7VK wrapper profile.";
                return res;
            }
            res.GameExePath = gameExe;

            var ddraw = Path.Combine(rootDir, @"local\work-ahead\mw3-d7vk-wrapper\game\ddraw.dll");
            if (!File.Exists(ddraw))
            {
                res.IsValid = false;
                res.StatusMessage = "D7VK ddraw.dll wrapper binary missing.";
                return res;
            }

            var python = FindPythonExecutable();
            if (string.IsNullOrEmpty(python))
            {
                res.IsValid = false;
                res.StatusMessage = "Python 3 environment not detected (required for D7VK launcher runner).";
                return res;
            }
            res.PythonPath = python;

            res.IsValid = true;
            res.StatusMessage = "Original Mech3 (D7VK Vulkan Wrapper) Ready";
            return res;
        }

        public Process LaunchGame(LauncherSettings settings, Action<string>? logCallback = null)
        {
            var val = Validate();
            if (!val.IsValid)
            {
                throw new InvalidOperationException($"Cannot launch D7VK wrapper: {val.StatusMessage}");
            }

            // Check if game or wrapper is already running
            var runningMech = Process.GetProcessesByName("Mech3");
            if (runningMech.Length > 0)
            {
                throw new InvalidOperationException("Mech3.exe is already running.");
            }

            var rootDir = Path.GetDirectoryName(val.WrapperScriptPath)!;

            // Sync settings into launcher-settings.json in wrapper directory
            try
            {
                var settingsJsonPath = Path.Combine(rootDir, @"local\work-ahead\mw3-d7vk-wrapper\launcher-settings.json");
                var dict = new Dictionary<string, object>
                {
                    ["resolution"] = settings.D7VkResolution,
                    ["aa"] = settings.D7VkAntiAliasing,
                    ["af"] = settings.D7VkAnisotropicFiltering,
                    ["ai_textures"] = settings.D7VkAiTextures
                };
                var json = JsonSerializer.Serialize(dict, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(settingsJsonPath, json);
            }
            catch { }

            var textureArg = settings.D7VkAiTextures ? "ai" : "original";
            var arguments = $"\"{val.WrapperScriptPath}\" --no-gui " +
                            $"--resolution \"{settings.D7VkResolution}\" " +
                            $"--aa \"{settings.D7VkAntiAliasing}\" " +
                            $"--af \"{settings.D7VkAnisotropicFiltering}\" " +
                            $"--textures {textureArg}";

            var psi = new ProcessStartInfo
            {
                FileName = val.PythonPath!,
                Arguments = arguments,
                WorkingDirectory = rootDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            logCallback?.Invoke($"Launching Original Mech3 with D7VK: {settings.D7VkResolution}, AA: {settings.D7VkAntiAliasing}, AF: {settings.D7VkAnisotropicFiltering}, Textures: {textureArg}...");

            var proc = new Process { StartInfo = psi };

            proc.OutputDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    logCallback?.Invoke($"[D7VK] {e.Data}");
                }
            };
            proc.ErrorDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    logCallback?.Invoke($"[D7VK ERR] {e.Data}");
                }
            };

            proc.Start();
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();

            return proc;
        }
    }
}
