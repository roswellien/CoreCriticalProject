using System;
using System.IO;
using System.Security.Cryptography;
using Microsoft.Win32;

namespace MW3RemasterLauncher.Core
{
    /// <summary>Launcher discovery details and a user-facing status for a selected directory.</summary>
    public class ValidationResult
    {
        public bool IsValid { get; set; }
        public string GameDirectory { get; set; } = string.Empty;
        public string ExecutablePath { get; set; } = string.Empty;
        public string ExecutableSha256 { get; set; } = string.Empty;
        public string DetectedVersion { get; set; } = "Unknown";
        public string StatusMessage { get; set; } = string.Empty;
    }

    /// <summary>Find a local Mech3.exe and collect launcher discovery metadata.</summary>
    /// <remarks>
    /// This legacy validator currently accepts unknown executable hashes. IsValid and
    /// the displayed version therefore do not establish supported-image admission;
    /// the strict native analysis/runtime contracts must check the selected image.
    /// </remarks>
    public static class GameValidator
    {
        public const string SHA256_V1_2_COMMUNITY = "09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a";

        /// <summary>Find the expected executable basename without searching arbitrary subtrees.</summary>
        public static string? FindExecutableInDirectory(string dir)
        {
            if (!Directory.Exists(dir)) return null;

            // Direct check (case-insensitive)
            var candidates = new[] { "Mech3.exe", "mech3.exe", "MECH3.EXE" };
            foreach (var name in candidates)
            {
                var full = Path.Combine(dir, name);
                if (File.Exists(full)) return full;
            }

            // Check files in folder
            try
            {
                foreach (var file in Directory.GetFiles(dir, "*.exe"))
                {
                    if (Path.GetFileName(file).Equals("Mech3.exe", StringComparison.OrdinalIgnoreCase))
                    {
                        return file;
                    }
                }
            }
            catch { }

            return null;
        }

        /// <summary>Try repository-relative and conventional installed-game locations.</summary>
        public static string? AutoDetectGameDirectory()
        {
            // 1. Walk up from BaseDirectory looking for MW3 or Mech3.exe
            try
            {
                var cur = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);
                while (cur != null)
                {
                    if (FindExecutableInDirectory(cur.FullName) != null)
                    {
                        return cur.FullName;
                    }
                    var mw3Sub = Path.Combine(cur.FullName, "MW3");
                    if (FindExecutableInDirectory(mw3Sub) != null)
                    {
                        return mw3Sub;
                    }
                    cur = cur.Parent;
                }
            }
            catch { }

            // 2. Check Registry keys
            string[] registryPaths = new[]
            {
                @"SOFTWARE\WOW6432Node\MicroProse\MechWarrior 3",
                @"SOFTWARE\MicroProse\MechWarrior 3",
                @"SOFTWARE\WOW6432Node\Microsoft\Microsoft Games\MechWarrior 3",
                @"SOFTWARE\Microsoft\Microsoft Games\MechWarrior 3"
            };

            foreach (var keyPath in registryPaths)
            {
                try
                {
                    using var key = Registry.LocalMachine.OpenSubKey(keyPath);
                    if (key != null)
                    {
                        var installPath = key.GetValue("InstallDir") as string ??
                                          key.GetValue("Path") as string ??
                                          key.GetValue("") as string;
                        if (!string.IsNullOrWhiteSpace(installPath) && FindExecutableInDirectory(installPath) != null)
                        {
                            return installPath;
                        }
                    }
                }
                catch { }
            }

            // 3. Common drive paths
            string[] commonPaths = new[]
            {
                @"C:\Games\MW3",
                @"C:\Games\MechWarrior 3",
                @"C:\Program Files (x86)\MicroProse\MechWarrior 3",
                @"C:\Program Files\MicroProse\MechWarrior 3",
                @"D:\Games\MW3",
                @"D:\Games\MechWarrior 3",
                @"E:\Games\MW3",
                @"E:\Games\MechWarrior 3"
            };

            foreach (var p in commonPaths)
            {
                if (FindExecutableInDirectory(p) != null)
                {
                    return p;
                }
            }

            return null;
        }

        /// <summary>Collect the selected folder/executable identity for launcher feedback.</summary>
        /// <remarks>Unknown hashes currently remain valid here; see the class-level admission limit.</remarks>
        public static ValidationResult Validate(string? path)
        {
            var res = new ValidationResult();

            if (string.IsNullOrWhiteSpace(path))
            {
                res.IsValid = false;
                res.StatusMessage = "No game location specified. Please select your MechWarrior 3 folder or Mech3.exe.";
                return res;
            }

            // If user selected the executable file directly instead of folder
            string targetDir = path;
            if (File.Exists(path))
            {
                targetDir = Path.GetDirectoryName(path) ?? path;
            }

            if (!Directory.Exists(targetDir))
            {
                res.IsValid = false;
                res.StatusMessage = $"Folder does not exist: {targetDir}";
                return res;
            }

            res.GameDirectory = targetDir;
            var exePath = FindExecutableInDirectory(targetDir);

            if (exePath == null)
            {
                res.IsValid = false;
                res.StatusMessage = $"Mech3.exe was not found in: {targetDir}";
                return res;
            }

            res.ExecutablePath = exePath;

            try
            {
                using var stream = File.OpenRead(exePath);
                using var sha = SHA256.Create();
                var hash = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
                res.ExecutableSha256 = hash;

                if (hash == SHA256_V1_2_COMMUNITY.ToLowerInvariant())
                {
                    res.DetectedVersion = "MechWarrior 3 v1.2 (Community Clean/1.2)";
                }
                else
                {
                    res.DetectedVersion = "MechWarrior 3 Retail / Custom";
                }

                // Check for supporting game archives
                var zfsCount = Directory.GetFiles(targetDir, "*.zfs").Length;
                res.IsValid = true;
                res.StatusMessage = zfsCount > 0
                    ? $"Verified: {res.DetectedVersion} ({zfsCount} game archives detected)."
                    : $"Verified: {res.DetectedVersion}.";
            }
            catch (Exception ex)
            {
                res.IsValid = false;
                res.StatusMessage = $"Error validating executable: {ex.Message}";
            }

            return res;
        }
    }
}
