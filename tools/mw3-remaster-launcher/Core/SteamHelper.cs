using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Microsoft.Win32;

namespace MW3RemasterLauncher.Core
{
    /// <summary>Locate Steam and write local non-Steam shortcut/artwork records.</summary>
    /// <remarks>
    /// This is an opt-in filesystem integration, not a Steam Web API or network client.
    /// The legacy VDF writer's indexing/atomic-replacement limitations remain review items;
    /// documentation does not establish safe updates to every existing Steam profile.
    /// </remarks>
    public static class SteamHelper
    {
        /// <summary>Discover Steam's local installation path from Windows registry locations.</summary>
        public static string? GetSteamPath()
        {
            try
            {
                using var key = Registry.CurrentUser.OpenSubKey(@"Software\Valve\Steam");
                if (key != null)
                {
                    var path = key.GetValue("SteamPath") as string;
                    if (!string.IsNullOrEmpty(path) && Directory.Exists(path))
                    {
                        return path.Replace('/', Path.DirectorySeparatorChar);
                    }
                }
            }
            catch { }

            try
            {
                using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\WOW6432Node\Valve\Steam");
                if (key != null)
                {
                    var path = key.GetValue("InstallPath") as string;
                    if (!string.IsNullOrEmpty(path) && Directory.Exists(path))
                    {
                        return path;
                    }
                }
            }
            catch { }

            string defaultPath = @"C:\Program Files (x86)\Steam";
            return Directory.Exists(defaultPath) ? defaultPath : null;
        }

        /// <summary>Compute the non-Steam shortcut CRC identity, including supplied executable quotes.</summary>
        public static uint CalculateShortcutAppId(string exePath, string appName)
        {
            // Steam generates shortcut ID using CRC32 of target path + name
            var combined = exePath + appName;
            var bytes = Encoding.UTF8.GetBytes(combined);
            uint crc = ComputeCrc32(bytes);
            return crc | 0x80000000;
        }

        private static uint ComputeCrc32(byte[] bytes)
        {
            uint crc = 0xFFFFFFFF;
            for (int i = 0; i < bytes.Length; i++)
            {
                byte b = bytes[i];
                crc ^= b;
                for (int j = 0; j < 8; j++)
                {
                    if ((crc & 1) != 0)
                        crc = (crc >> 1) ^ 0xEDB88320;
                    else
                        crc >>= 1;
                }
            }
            return ~crc;
        }

        /// <summary>Attempt shortcut/artwork installation in discovered local userdata profiles.</summary>
        /// <returns>Whether at least one shortcut write reported success.</returns>
        /// <remarks>The result does not mean Steam has reloaded or displayed the shortcut.</remarks>
        public static bool AddToSteam(string launcherExePath, string artworkSourceDir)
        {
            var steamPath = GetSteamPath();
            if (string.IsNullOrEmpty(steamPath)) return false;

            var userDataDir = Path.Combine(steamPath, "userdata");
            if (!Directory.Exists(userDataDir)) return false;

            var userFolders = Directory.GetDirectories(userDataDir);
            if (userFolders.Length == 0) return false;

            const string appName = "Core Critical Launcher";
            var targetExe = $"\"{launcherExePath}\"";
            var startDir = $"\"{Path.GetDirectoryName(launcherExePath)}\"";
            uint appId = CalculateShortcutAppId(targetExe, appName);

            bool successAny = false;

            foreach (var userFolder in userFolders)
            {
                var configDir = Path.Combine(userFolder, "config");
                if (!Directory.Exists(configDir))
                {
                    Directory.CreateDirectory(configDir);
                }

                var shortcutsPath = Path.Combine(configDir, "shortcuts.vdf");
                if (WriteShortcutEntry(shortcutsPath, appName, targetExe, startDir, appId))
                {
                    successAny = true;
                }

                // Copy Grid artwork
                var gridDir = Path.Combine(configDir, "grid");
                if (!Directory.Exists(gridDir))
                {
                    Directory.CreateDirectory(gridDir);
                }

                InstallGridArtwork(gridDir, appId, artworkSourceDir);
            }

            return successAny;
        }

        private static bool WriteShortcutEntry(string vdfPath, string appName, string targetExe, string startDir, uint appId)
        {
            try
            {
                // Simple binary append/replacement for Valve KeyValues format
                var memory = new MemoryStream();
                using (var writer = new BinaryWriter(memory, Encoding.UTF8, true))
                {
                    // \x00 = Subkey start
                    writer.Write((byte)0x00);
                    WriteString(writer, "0"); // Entry index

                    writer.Write((byte)0x02); // int32
                    WriteString(writer, "appid");
                    writer.Write((int)appId);

                    writer.Write((byte)0x01); // string
                    WriteString(writer, "AppName");
                    WriteString(writer, appName);

                    writer.Write((byte)0x01);
                    WriteString(writer, "Exe");
                    WriteString(writer, targetExe);

                    writer.Write((byte)0x01);
                    WriteString(writer, "StartDir");
                    WriteString(writer, startDir);

                    writer.Write((byte)0x01);
                    WriteString(writer, "icon");
                    WriteString(writer, targetExe);

                    writer.Write((byte)0x01);
                    WriteString(writer, "ShortcutPath");
                    WriteString(writer, "");

                    writer.Write((byte)0x01);
                    WriteString(writer, "LaunchOptions");
                    WriteString(writer, "");

                    writer.Write((byte)0x02);
                    WriteString(writer, "IsHidden");
                    writer.Write(0);

                    writer.Write((byte)0x02);
                    WriteString(writer, "AllowDesktopConfig");
                    writer.Write(1);

                    writer.Write((byte)0x02);
                    WriteString(writer, "AllowOverlay");
                    writer.Write(1);

                    writer.Write((byte)0x02);
                    WriteString(writer, "OpenVR");
                    writer.Write(0);

                    writer.Write((byte)0x02);
                    WriteString(writer, "Devkit");
                    writer.Write(0);

                    writer.Write((byte)0x01);
                    WriteString(writer, "DevkitGameID");
                    WriteString(writer, "");

                    writer.Write((byte)0x02);
                    WriteString(writer, "DevkitOverrideAppID");
                    writer.Write(0);

                    writer.Write((byte)0x02);
                    WriteString(writer, "LastPlayTime");
                    writer.Write(0);

                    writer.Write((byte)0x00);
                    WriteString(writer, "tags");
                    writer.Write((byte)0x01);
                    WriteString(writer, "0");
                    WriteString(writer, "MechWarrior");
                    writer.Write((byte)0x08); // End tags

                    writer.Write((byte)0x08); // End entry
                }

                var entryBytes = memory.ToArray();

                if (!File.Exists(vdfPath))
                {
                    // Create brand new shortcuts.vdf
                    using var fs = File.Create(vdfPath);
                    using var bw = new BinaryWriter(fs);
                    bw.Write((byte)0x00);
                    WriteString(bw, "shortcuts");
                    bw.Write(entryBytes);
                    bw.Write((byte)0x08); // End shortcuts
                    bw.Write((byte)0x08); // End file
                    return true;
                }

                // If file exists, check if appName already present
                var existing = File.ReadAllBytes(vdfPath);
                var existingStr = Encoding.UTF8.GetString(existing);
                if (existingStr.Contains(appName))
                {
                    // Already registered
                    return true;
                }

                // Insert entry before the final trailing 0x08 0x08 bytes
                if (existing.Length >= 2 && existing[^2] == 0x08 && existing[^1] == 0x08)
                {
                    var updated = new byte[existing.Length - 2 + entryBytes.Length + 2];
                    Buffer.BlockCopy(existing, 0, updated, 0, existing.Length - 2);
                    Buffer.BlockCopy(entryBytes, 0, updated, existing.Length - 2, entryBytes.Length);
                    updated[^2] = 0x08;
                    updated[^1] = 0x08;
                    File.WriteAllBytes(vdfPath, updated);
                    return true;
                }

                return false;
            }
            catch
            {
                return false;
            }
        }

        private static void WriteString(BinaryWriter writer, string text)
        {
            var bytes = Encoding.UTF8.GetBytes(text);
            writer.Write(bytes);
            writer.Write((byte)0x00); // null terminator
        }

        private static void InstallGridArtwork(string gridDir, uint appId, string artworkSourceDir)
        {
            try
            {
                var heroSrc = Path.Combine(artworkSourceDir, "hero-art.png");
                var markSrc = Path.Combine(artworkSourceDir, "brand-mark.png");

                // Steam capsule (portrait vertical)
                var pDst = Path.Combine(gridDir, $"{appId}p.png");
                // Steam hero banner (landscape)
                var heroDst = Path.Combine(gridDir, $"{appId}_hero.png");
                // Steam logo
                var logoDst = Path.Combine(gridDir, $"{appId}_logo.png");
                // Steam standard grid
                var gridDst = Path.Combine(gridDir, $"{appId}.png");

                if (File.Exists(heroSrc))
                {
                    File.Copy(heroSrc, heroDst, true);
                    File.Copy(heroSrc, gridDst, true);
                    File.Copy(heroSrc, pDst, true);
                }

                if (File.Exists(markSrc))
                {
                    File.Copy(markSrc, logoDst, true);
                }
            }
            catch { }
        }
    }
}
