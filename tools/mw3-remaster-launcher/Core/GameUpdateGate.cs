using System.IO;

namespace MW3RemasterLauncher.Core;

/// <summary>One per-user gate spans launch preparation/session or installation. Acquire before product locks.</summary>
public static class GameUpdateGate
{
    public static FileStream Acquire(string? dataRoot = null)
    {
        var directory = Path.Combine(dataRoot ?? LauncherPaths.DataRoot, "coordination");
        PackStorage.EnsureNoLinks(directory);
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, "game-update.gate");
        PackStorage.EnsureNoLinks(path);
        try { return new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None); }
        catch (IOException error)
        {
            throw new InvalidOperationException("A game is starting/running or another update is installing. Close the game or wait for the update, then retry.", error);
        }
    }
}
