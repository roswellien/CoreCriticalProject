using System.Diagnostics;
using System.IO;

namespace MW3RemasterLauncher.Core;

internal static class Mw3ReAlphaRunner
{
    internal static ProcessStartInfo CreateStartInfo(string launcherDirectory, string profileDirectory,
        string gameDirectory, string readyFile, LauncherSettings settings,
        IEnumerable<PackManifest> packs, out List<string> unsupportedPacks)
    {
        var executable = Path.GetFullPath(Path.Combine(launcherDirectory, "MW3-RE-Alpha", "mw3.exe"));
        if (!File.Exists(executable))
            throw new FileNotFoundException("Install the Core Critical MW3-RE Alpha Runtime next to this launcher.", executable);

        Directory.CreateDirectory(profileDirectory);
        var startInfo = new ProcessStartInfo
        {
            FileName = executable,
            WorkingDirectory = Path.GetDirectoryName(executable)!,
            UseShellExecute = false,
            ArgumentList =
            {
                "--install", Path.GetFullPath(gameDirectory),
                "--write-dir", Path.GetFullPath(profileDirectory),
                "--ready-file", Path.GetFullPath(readyFile),
                "--cc-vulkan-wsi"
            }
        };
        switch (settings.WindowMode)
        {
            case "windowed":
                if (settings.Width is < 640 or > 7680 || settings.Height is < 480 or > 4320)
                    throw new InvalidOperationException("Choose a supported display resolution.");
                startInfo.ArgumentList.Add("--window");
                startInfo.ArgumentList.Add(FormattableString.Invariant($"{settings.Width}x{settings.Height}"));
                break;
            case "fullscreen_windowed":
                startInfo.ArgumentList.Add("--borderless");
                break;
            default:
                throw new InvalidOperationException("Choose Windowed or Fullscreen Windowed for MW3-RE Alpha.");
        }
        unsupportedPacks = new List<string>();
        foreach (var pack in packs)
        {
            if (!pack.IsEnabled || pack.GameId != GameCatalog.Mw3) continue;
            if (pack.SchemaVersion != 2 || pack.NativePayload?.Profile != "prepared-environment-v1")
            {
                unsupportedPacks.Add(pack.Name);
                continue;
            }
            startInfo.ArgumentList.Add("--cc-environment-pack");
            startInfo.ArgumentList.Add(PackStorage.CanonicalPackRoot(pack.DirectoryPath));
        }
        return startInfo;
    }
}
