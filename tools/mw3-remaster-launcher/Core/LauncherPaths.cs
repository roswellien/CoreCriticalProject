using System.IO;

namespace MW3RemasterLauncher.Core;

/// <summary>Writable launcher state shared by installed versions, outside application files.</summary>
public static class LauncherPaths
{
    public static string DataRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MW3Remaster");
    public static string SessionsRoot => Path.Combine(DataRoot, "sessions");
    /// <summary>
    /// Benchmark replays and results. Kept beside, not inside, DataRoot: the benchmark treats the
    /// launcher's settings and packs as read-only inputs and refuses to write under them.
    /// </summary>
    public static string BenchmarkRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Core Critical Benchmark");

    public const string GameFolderName = "MechWarrior 3";

    /// <summary>Visible game library, independent of hidden per-user launcher state.</summary>
    public static string SuggestedGameDirectory(string? applicationDirectory = null)
    {
        var application = new DirectoryInfo(Path.GetFullPath(applicationDirectory ?? AppContext.BaseDirectory));
        // Follow the library when Setup's standard Launcher folder is installed
        // on another drive. Do not suggest game writes into an arbitrary app's
        // parent (for example Program Files) or into a development build tree.
        if (application.Name.Equals("Launcher", StringComparison.OrdinalIgnoreCase) &&
            application.Parent is { } library && library.Name.Equals("Core Critical", StringComparison.OrdinalIgnoreCase))
            return Path.Combine(library.FullName, GameFolderName);
        var systemDrive = Path.GetPathRoot(Environment.SystemDirectory)
            ?? throw new InvalidOperationException("Cannot locate the Windows system drive.");
        return Path.Combine(systemDrive, "Games", "Core Critical", GameFolderName);
    }

    public static string? LatestLaunchLog(string? dataRoot = null)
    {
        var sessions = Path.Combine(dataRoot ?? DataRoot, "sessions");
        if (!Directory.Exists(sessions)) return null;
        PackStorage.EnsureNoLinks(sessions);
        foreach (var directory in Directory.GetDirectories(sessions).OrderByDescending(Directory.GetLastWriteTimeUtc))
        {
            PackStorage.EnsureNoLinks(directory);
            // Older sessions use launcher.log/native-preview.log; MW3-RE sessions use mw3-re.log.
            foreach (var name in new[] { "mw3-re.log", "launcher.log", "native-preview.log" })
            {
                var log = Path.Combine(directory, name);
                if (File.Exists(log)) return log;
            }
        }
        return null;
    }
}
