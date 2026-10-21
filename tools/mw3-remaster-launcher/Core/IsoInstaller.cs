using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;

namespace MW3RemasterLauncher.Core
{
    /// <summary>Mount local user-supplied media and copy recognized files into a destination.</summary>
    /// <remarks>
    /// This helper does not build a native host or establish a complete standalone install.
    /// PowerShell filename interpolation and incomplete-media success remain review findings
    /// C03/C11; they are intentionally not changed by the readability-only pass.
    /// </remarks>
    public class IsoInstaller
    {
        /// <summary>Mount the selected media, attempt recognized-file copying and dismount afterward.</summary>
        /// <remarks>Progress is a fraction from zero to one; completion is not native-install validation.</remarks>
        public static async Task<bool> InstallFromIsoAsync(string isoPath, string destDir, Action<string, double>? onProgress = null)
        {
            if (!File.Exists(isoPath))
            {
                throw new FileNotFoundException("Specified ISO image was not found.", isoPath);
            }

            Directory.CreateDirectory(destDir);

            onProgress?.Invoke("Mounting ISO image in background...", 0.1);

            // Mount ISO using PowerShell
            string mountCmd = $"$img = Mount-DiskImage -ImagePath '{isoPath}' -PassThru; ($img | Get-Volume).DriveLetter";
            var startInfo = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-NoProfile -ExecutionPolicy Bypass -Command \"{mountCmd}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            string driveLetter = string.Empty;
            using (var proc = Process.Start(startInfo))
            {
                if (proc != null)
                {
                    driveLetter = (await proc.StandardOutput.ReadToEndAsync()).Trim();
                    await proc.WaitForExitAsync();
                }
            }

            if (string.IsNullOrEmpty(driveLetter))
            {
                throw new InvalidOperationException("Failed to mount ISO image or retrieve drive letter.");
            }

            string sourceDrive = $"{driveLetter}:\\";
            onProgress?.Invoke($"ISO mounted at {sourceDrive}. Copying game media...", 0.25);

            try
            {
                await CopyGameMediaAsync(sourceDrive, destDir, onProgress);
                return true;
            }
            finally
            {
                onProgress?.Invoke("Dismounting ISO image...", 0.95);
                string dismountCmd = $"Dismount-DiskImage -ImagePath '{isoPath}'";
                var dismountInfo = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = $"-NoProfile -ExecutionPolicy Bypass -Command \"{dismountCmd}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using var proc = Process.Start(dismountInfo);
                if (proc != null) await proc.WaitForExitAsync();
            }
        }

        /// <summary>Copy the currently recognized media layout on a background worker.</summary>
        /// <remarks>Progress callbacks may run off the UI thread and must be marshalled by callers.</remarks>
        public static async Task CopyGameMediaAsync(string sourceRoot, string destDir, Action<string, double>? onProgress = null)
        {
            await Task.Run(() =>
            {
                Directory.CreateDirectory(destDir);

                // 1. Copy MW3CD.TXT if exists
                string cdTxt = Path.Combine(sourceRoot, "MW3CD.TXT");
                if (File.Exists(cdTxt))
                {
                    onProgress?.Invoke("Copying disc identification marker (MW3CD.TXT)...", 0.3);
                    File.Copy(cdTxt, Path.Combine(destDir, "MW3CD.TXT"), true);
                }

                // 2. Copy VIDEO folder if exists
                string srcVideo = Path.Combine(sourceRoot, "VIDEO");
                if (!Directory.Exists(srcVideo)) srcVideo = Path.Combine(sourceRoot, "video");

                if (Directory.Exists(srcVideo))
                {
                    string dstVideo = Path.Combine(destDir, "VIDEO");
                    Directory.CreateDirectory(dstVideo);

                    var videoFiles = Directory.GetFiles(srcVideo);
                    for (int i = 0; i < videoFiles.Length; i++)
                    {
                        var vf = videoFiles[i];
                        var fname = Path.GetFileName(vf);
                        double pct = 0.3 + (0.5 * (i + 1) / (double)videoFiles.Length);
                        onProgress?.Invoke($"Copying cinematics: {fname}...", pct);
                        File.Copy(vf, Path.Combine(dstVideo, fname), true);
                    }
                }

                // 3. If Mech3.exe does not exist in destination, copy all core files
                string dstExe = Path.Combine(destDir, "Mech3.exe");
                if (!File.Exists(dstExe))
                {
                    onProgress?.Invoke("Copying core game binaries...", 0.85);
                    foreach (var f in Directory.GetFiles(sourceRoot))
                    {
                        var name = Path.GetFileName(f);
                        if (!name.StartsWith("AUTORUN", StringComparison.OrdinalIgnoreCase) &&
                            !name.StartsWith("SETUP", StringComparison.OrdinalIgnoreCase) &&
                            !name.StartsWith("_", StringComparison.OrdinalIgnoreCase))
                        {
                            File.Copy(f, Path.Combine(destDir, name), true);
                        }
                    }

                    // Copy zbd directory if exists on disc
                    string srcZbd = Path.Combine(sourceRoot, "zbd");
                    if (Directory.Exists(srcZbd))
                    {
                        string dstZbd = Path.Combine(destDir, "zbd");
                        Directory.CreateDirectory(dstZbd);
                        foreach (var zf in Directory.GetFiles(srcZbd))
                        {
                            File.Copy(zf, Path.Combine(dstZbd, Path.GetFileName(zf)), true);
                        }
                    }
                }

                onProgress?.Invoke("Installation complete! Game is now 100% standalone.", 1.0);
            });
        }
    }
}
