using System.IO;

namespace MW3RemasterLauncher.Core;

/// <summary>Writable launcher state shared by installed versions, outside application files.</summary>
public static class LauncherPaths
{
    public static string DataRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MW3Remaster");
    public static string SessionsRoot => Path.Combine(DataRoot, "sessions");

    public static string? LatestLaunchLog(string? dataRoot = null)
    {
        var sessions = Path.Combine(dataRoot ?? DataRoot, "sessions");
        if (!Directory.Exists(sessions)) return null;
        PackStorage.EnsureNoLinks(sessions);
        foreach (var directory in Directory.GetDirectories(sessions).OrderByDescending(Directory.GetLastWriteTimeUtc))
        {
            PackStorage.EnsureNoLinks(directory);
            var log = Path.Combine(directory, "launcher.log");
            if (File.Exists(log)) return log;
        }
        return null;
    }
}
