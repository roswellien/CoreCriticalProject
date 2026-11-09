using System.Diagnostics;
using System.IO;

namespace MW3RemasterLauncher.Core;

internal static class Mw3ReAlphaRunner
{
    internal static ProcessStartInfo CreateStartInfo(string launcherDirectory, string profileDirectory,
        string gameDirectory, string readyFile)
    {
        var executable = Path.GetFullPath(Path.Combine(launcherDirectory, "MW3-RE-Alpha", "mw3.exe"));
        if (!File.Exists(executable))
            throw new FileNotFoundException("Install the Core Critical MW3-RE Alpha Runtime next to this launcher.", executable);

        Directory.CreateDirectory(profileDirectory);
        return new ProcessStartInfo
        {
            FileName = executable,
            WorkingDirectory = Path.GetDirectoryName(executable)!,
            UseShellExecute = false,
            ArgumentList =
            {
                "--install", Path.GetFullPath(gameDirectory),
                "--write-dir", Path.GetFullPath(profileDirectory),
                "--ready-file", Path.GetFullPath(readyFile),
                "--cc-vulkan-wsi", "--windowed"
            }
        };
    }
}
