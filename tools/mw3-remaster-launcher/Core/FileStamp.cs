using System.IO;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// A file's identity before launch (whether it existed, its times and length), so the
/// launcher can tell a file this session wrote from one left over by an earlier run.
/// </summary>
public sealed record FileStamp(string Path, bool Existed, DateTime CreationTimeUtc,
    DateTime LastWriteTimeUtc, long Length)
{
    /// <summary>The file's stamp now; a missing file or one reached through a link counts as absent.</summary>
    public static FileStamp Capture(string path)
    {
        try
        {
            if (File.Exists(path) && !PlaytestDiagnostics.HasLinkInChain(path))
            {
                var info = new FileInfo(path);
                return new FileStamp(path, true, info.CreationTimeUtc, info.LastWriteTimeUtc, info.Length);
            }
        }
        catch { }
        return new FileStamp(path, false, DateTime.MinValue, DateTime.MinValue, 0);
    }

    /// <summary>True when the file exists now and wasn't there, or differs from this stamp.</summary>
    public bool ChangedSince()
    {
        var now = Capture(Path);
        if (!now.Existed) return false;
        return !Existed ||
            now.LastWriteTimeUtc != LastWriteTimeUtc ||
            now.CreationTimeUtc != CreationTimeUtc ||
            now.Length != Length;
    }
}
