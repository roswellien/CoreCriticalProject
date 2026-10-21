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
        public int DrawDistance { get; set; } = 2400; // 800, 1200, 1600, 2400, 3200
        public int FogDistance { get; set; } = 1100; // 0, 1100
        public bool LocalCdAudio { get; set; } = true;
        public int CdAudioVolume { get; set; } = 80;
        public bool InstantReplay { get; set; } = false;
        public int ReplayVideoSettingsVersion { get; set; } = 0;
        public List<string> ActivePacks { get; set; } = new();
        public bool PackSelectionInitialized { get; set; } = false;
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
        public LauncherSettings Current { get; private set; }

        public SettingsManager(string basePath)
        {
            var userDir = Path.Combine(basePath, "user");
            if (!Directory.Exists(userDir))
            {
                Directory.CreateDirectory(userDir);
            }
            _settingsPath = Path.Combine(userDir, "settings.json");
            Current = Load();
        }

        public LauncherSettings Load()
        {
            if (File.Exists(_settingsPath))
            {
                try
                {
                    var json = File.ReadAllText(_settingsPath);
                    var settings = JsonSerializer.Deserialize<LauncherSettings>(json);
                    if (settings != null)
                    {
                        // Earlier launchers enabled capture by default without informed opt-in.
                        if (settings.ReplayVideoSettingsVersion < 1)
                            settings.InstantReplay = false;
                        return settings;
                    }
                }
                catch
                {
                    // Fall back to defaults
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
            try
            {
                Current.ReplayVideoSettingsVersion = 1;
                var options = new JsonSerializerOptions { WriteIndented = true };
                var json = JsonSerializer.Serialize(Current, options);
                File.WriteAllText(_settingsPath, json);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to save settings: {ex.Message}");
            }
        }
    }
}
