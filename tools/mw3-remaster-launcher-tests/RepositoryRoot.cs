using System.IO;

/// <summary>The repository root, for checks that read files the repo keeps (scripts, shared fixtures).</summary>
internal static class RepositoryRoot
{
    public static string Find()
    {
        foreach (var anchor in new[] { AppContext.BaseDirectory, Environment.CurrentDirectory })
        {
            var dir = new DirectoryInfo(Path.GetFullPath(anchor));
            while (dir != null)
            {
                if (File.Exists(Path.Combine(dir.FullName, "tools", "mw3-remaster-launcher", "sign_native_preview.ps1")) &&
                    File.Exists(Path.Combine(dir.FullName, "tools", "mw3-remaster-launcher-tests", "LauncherChecks.csproj")))
                {
                    return dir.FullName;
                }
                dir = dir.Parent;
            }
        }
        throw new DirectoryNotFoundException("Could not locate repository root containing launcher signing scripts.");
    }
}
