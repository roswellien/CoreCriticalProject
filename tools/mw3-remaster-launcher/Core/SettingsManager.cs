using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Windows;

namespace MW3RemasterLauncher.Core
{
    public class LauncherSettings
    {
        public string GamePath { get; set; } = string.Empty;
        public int Width { get; set; } = 1920;
        public int Height { get; set; } = 1080;
        public string WindowMode { get; set; } = "fullscreen_windowed"; // "fullscreen", "fullscreen_windowed", "windowed"
        public bool Fullscreen { get; set; } = true;
        public string AntiAliasing { get; set; } = "fxaa"; // "off", "fxaa", "2", "4", "8"
        public int AnisotropicFiltering { get; set; } = 16; // 1, 2, 4, 8, 16
        public int DrawDistance { get; set; } = 1600; // 800, 1200, 1600, 2400, 3200
        public int FogDistance { get; set; } = 1100; // 0, 1100
        public bool LocalCdAudio { get; set; } = true;
        public string MusicTrack2 { get; set; } = string.Empty;
        public string MusicTrack3 { get; set; } = string.Empty;
        public int CdAudioVolume { get; set; } = 80;
        public bool InstantReplay { get; set; } = false;
        public bool PerformanceMonitor { get; set; } = false;
        // Off until the RX 9070 benchmark shows the same gain as the RTX 5070 (issue #252).
        public bool RenderThread { get; set; } = false;
        public bool Headlights { get; set; } = false;
        public bool DynamicLighting { get; set; } = false;
        public bool Shadows { get; set; } = false;
        public string DirectInputJoystickInstanceGuid { get; set; } = string.Empty;
        public string DirectInputJoystickProductName { get; set; } = string.Empty;
        public bool DirectInputJoystickNone { get; set; }
        public bool InitialSetupCompleted { get; set; } = false;
        public bool AutomaticUpdateChecks { get; set; } = false;
        public bool AutomaticCrashReports { get; set; } = false;
        public int ReplayVideoSettingsVersion { get; set; } = 0;
        public List<string> ActivePacks { get; set; } = new();
        public string ModularContentProfile { get; set; } = string.Empty;
        public string ModularContentTool { get; set; } = string.Empty;
        public string ModularContentStore { get; set; } = string.Empty;
        public string ModularRuntimeExecutable { get; set; } = string.Empty;
        public bool PackSelectionInitialized { get; set; } = false;
        public bool EnvironmentPackSelectionInitialized { get; set; } = false;
        public bool HasAddedToSteam { get; set; } = false;

        // Engine & D7VK options
        public string EngineMode { get; set; } = "remaster"; // "remaster" or "d7vk"
        public string D7VkResolution { get; set; } = "1920x1080 (1080p Widescreen 16:9)";
        public string D7VkAntiAliasing { get; set; } = "Off"; // "Off", "2x MSAA", "4x MSAA", "8x MSAA"
        public string D7VkAnisotropicFiltering { get; set; } = "16x"; // "Game default", "2x", "4x", "8x", "16x"
        public bool D7VkAiTextures { get; set; } = true;
    }

    public class SettingsManager
    {
        private readonly string _settingsPath;
        public string SettingsPath => _settingsPath;
        public string? LoadWarning { get; private set; }
        public LauncherSettings Current { get; private set; }

        public SettingsManager(string basePath, string? dataRoot = null)
        {
            var userDir = dataRoot ?? LauncherPaths.DataRoot;
            Directory.CreateDirectory(userDir);
            _settingsPath = Path.Combine(userDir, "settings.json");
            var legacy = Path.Combine(basePath, "user", "settings.json");
            if (!File.Exists(_settingsPath) && File.Exists(legacy))
            {
                // Copy once. Upgrades must never replace a newer per-user choice.
                File.Copy(legacy, _settingsPath, overwrite: false);
            }
            Current = Load();
        }

        public LauncherSettings Load()
        {
            LoadWarning = null;
            if (File.Exists(_settingsPath))
            {
                try
                {
                    var raw = File.ReadAllText(_settingsPath);
                    var settings = JsonSerializer.Deserialize<LauncherSettings>(raw)
                        ?? throw new JsonException("Settings are empty.");
                    settings.ActivePacks ??= new List<string>();
                    // Existing users have already configured their launcher.
                    // Newly saved first-run settings contain the explicit false
                    // marker, so cancelling setup does not count as completing it.
                    using var saved = JsonDocument.Parse(raw);
                    if (!saved.RootElement.TryGetProperty(nameof(LauncherSettings.InitialSetupCompleted), out _))
                        settings.InitialSetupCompleted = true;
                    if (settings.ReplayVideoSettingsVersion < 1) settings.InstantReplay = false;
                    return settings;
                }
                catch (JsonException ex)
                {
                    // Keep the exact rejected bytes before allowing defaults to save.
                    var backup = _settingsPath + ".unreadable-" + Guid.NewGuid().ToString("N");
                    File.Copy(_settingsPath, backup);
                    LoadWarning = "Saved settings could not be read. Defaults were loaded; the original file is preserved at " + backup + ". " + ex.Message;
                }
            }

            var defaultSettings = new LauncherSettings();
            try
            {
                // Auto-detect primary screen resolution
                defaultSettings.Width = (int)SystemParameters.PrimaryScreenWidth;
                defaultSettings.Height = (int)SystemParameters.PrimaryScreenHeight;
            }
            catch
            {
                defaultSettings.Width = 1920;
                defaultSettings.Height = 1080;
            }

            return defaultSettings;
        }

        public void Save()
        {
            Current.ReplayVideoSettingsVersion = 1;
            var temporary = _settingsPath + "." + Guid.NewGuid().ToString("N") + ".tmp";
            try
            {
                var json = JsonSerializer.Serialize(Current, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(temporary, json);
                if (File.Exists(_settingsPath)) File.Replace(temporary, _settingsPath, _settingsPath + ".previous");
                else File.Move(temporary, _settingsPath);
            }
            catch (Exception ex) when (ex is IOException || ex is UnauthorizedAccessException)
            {
                throw new IOException("Your launcher settings could not be saved to " + _settingsPath + ". " + ex.Message, ex);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
    }
}
