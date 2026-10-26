using System;
using System.Diagnostics;
using System.Text.RegularExpressions;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Microsoft.Win32;

namespace MW3RemasterLauncher.Core
{
    public sealed record SteamIntegrationResult(string Profile, uint AppId, string? Backup, bool Changed, string? ArtworkWarning);

    /// <summary>Locate Steam and write local non-Steam shortcut/artwork records.</summary>
    /// <remarks>
    /// This is an opt-in filesystem integration, not a Steam Web API or network client.
    /// Steam must be closed before changing its local shortcut table.
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


        public static void RequireSteamClosed()
        {
            var processes = Process.GetProcessesByName("steam");
            try
            {
                if (processes.Length != 0)
                    throw new InvalidOperationException("Exit Steam completely using Steam → Exit, then click Add to Steam again. Start Steam afterwards to load the shortcut.");
            }
            finally { foreach (var process in processes) process.Dispose(); }
        }

        public static string SelectProfile(string steamPath, uint activeUser = 0)
        {
            var userdata = Path.Combine(steamPath, "userdata");
            PackStorage.EnsureNoLinks(userdata);
            if (!Directory.Exists(userdata)) throw new DirectoryNotFoundException("Sign in to Steam once before adding the launcher.");
            var profiles = Directory.GetDirectories(userdata).Where(p => uint.TryParse(Path.GetFileName(p), out var id) && id != 0 &&
                Directory.Exists(Path.Combine(p, "config"))).ToArray();
            var active = profiles.SingleOrDefault(p => Path.GetFileName(p) == activeUser.ToString());
            if (active != null) return active;
            if (profiles.Length == 1) return profiles[0];
            var login = Path.Combine(steamPath, "config", "loginusers.vdf");
            if (File.Exists(login))
            {
                PackStorage.EnsureNoLinks(login);
                if (new FileInfo(login).Length > 2 * 1024 * 1024) throw new InvalidDataException("Steam login profile file is too large.");
                const string quoted = "\"(?:\\\\.|[^\"\\\\])*\"";
                var accounts = Regex.Matches(File.ReadAllText(login), "\"(?<id>[0-9]{17})\"\\s*\\{(?<fields>(?:\\s*" + quoted + "\\s*" + quoted + "\\s*)*)\\}",
                    RegexOptions.CultureInvariant, TimeSpan.FromSeconds(1));
                var recent = new List<string>();
                foreach (Match account in accounts)
                {
                    var pairs = Regex.Matches(account.Groups["fields"].Value, "(?<key>" + quoted + ")\\s*(?<value>" + quoted + ")",
                        RegexOptions.CultureInvariant, TimeSpan.FromSeconds(1));
                    if (!pairs.Any(pair => pair.Groups["key"].Value.Equals("\"MostRecent\"", StringComparison.OrdinalIgnoreCase) && pair.Groups["value"].Value == "\"1\"")) continue;
                    var id = (uint)(ulong.Parse(account.Groups["id"].Value) & uint.MaxValue);
                    recent.AddRange(profiles.Where(p => Path.GetFileName(p) == id.ToString()));
                }
                if (recent.Count == 1) return recent[0];
            }
            throw new InvalidOperationException(profiles.Length == 0 ? "No Steam user profile is available. Sign in to Steam once, exit it, and retry." :
                "Several Steam profiles are available. Sign in to the desired account, exit Steam, then retry so the shortcut is added to the right library.");
        }

        public static SteamIntegrationResult AddToSteam(string launcherExePath, string artworkSourceDir)
        {
            RequireSteamClosed();
            var steam = GetSteamPath() ?? throw new DirectoryNotFoundException("Steam was not found. Install and sign in to Steam first.");
            using var key = Registry.CurrentUser.OpenSubKey(@"Software\Valve\Steam\ActiveProcess");
            var active = key?.GetValue("ActiveUser") is int value ? unchecked((uint)value) : 0;
            return InstallForProfile(SelectProfile(steam, active), launcherExePath, artworkSourceDir);
        }

        /// <summary>Selected-profile write path; also permits isolated integration fixtures.</summary>
        public static SteamIntegrationResult InstallForProfile(string profile, string executable, string artwork)
        {
            RequireSteamClosed();
            executable = Path.GetFullPath(executable);
            if (!File.Exists(executable) || !executable.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
                throw new FileNotFoundException("The Core Critical launcher executable is missing. Repair the launcher installation first.");
            var config = Path.Combine(Path.GetFullPath(profile), "config");
            PackStorage.EnsureNoLinks(config); Directory.CreateDirectory(config);
            var path = Path.Combine(config, "shortcuts.vdf");
            var lockPath = Path.Combine(config, ".corecritical-shortcut-lock");
            PackStorage.EnsureNoLinks(path); PackStorage.EnsureNoLinks(lockPath);
            using var writerLock = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            byte[]? before = null;
            if (File.Exists(path))
            {
                if (new FileInfo(path).Length > SteamShortcuts.MaximumBytes) throw new InvalidDataException("Steam shortcut file is too large.");
                before = File.ReadAllBytes(path);
            }
            var icon = Path.Combine(Path.GetDirectoryName(executable)!, "Assets", "app-icon.ico");
            var updated = SteamShortcuts.Upsert(before, executable, File.Exists(icon) ? icon : executable);
            string? backup = null;
            if (updated.Changed)
            {
                var temporary = Path.Combine(config, ".corecritical-shortcuts-" + Guid.NewGuid().ToString("N"));
                try
                {
                    using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                    { output.Write(updated.Bytes); output.Flush(true); }
                    RequireSteamClosed();
                    if (before == null)
                    {
                        if (File.Exists(path)) throw new IOException("Steam shortcuts changed while adding the launcher. Exit Steam and retry.");
                        File.Move(temporary, path);
                    }
                    else
                    {
                        if (!File.ReadAllBytes(path).SequenceEqual(before)) throw new IOException("Steam shortcuts changed while adding the launcher. Exit Steam and retry.");
                        backup = path + ".corecritical-backup-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N")[..8];
                        File.Replace(temporary, path, backup);
                    }
                    if (!File.ReadAllBytes(path).SequenceEqual(updated.Bytes)) throw new IOException("Steam shortcut write did not verify.");
                }
                finally { if (File.Exists(temporary)) File.Delete(temporary); }
            }
            string? warning = null;
            try
            {
                var grid = Path.Combine(config, "grid"); PackStorage.EnsureNoLinks(grid); Directory.CreateDirectory(grid);
                foreach (var (source, suffix) in new[] { ("hero-art.png", "_hero.png"), ("hero-art.png", ".png"), ("hero-art.png", "p.png"), ("brand-mark.png", "_logo.png") })
                {
                    var from = Path.Combine(artwork, source); var to = Path.Combine(grid, updated.AppId + suffix);
                    PackStorage.EnsureNoLinks(to);
                    if (File.Exists(from) && !File.Exists(to)) File.Copy(from, to);
                    else if (!File.Exists(from)) warning = "The shortcut is ready, but bundled artwork was not available.";
                }
            }
            catch (IOException) { warning = "The shortcut is ready, but some Steam artwork could not be copied."; }
            catch (UnauthorizedAccessException) { warning = "The shortcut is ready, but access to Steam artwork was denied."; }
            return new(Path.GetFullPath(profile), updated.AppId, backup, updated.Changed, warning);
        }
    }
}
