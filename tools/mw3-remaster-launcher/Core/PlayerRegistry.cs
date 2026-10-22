using System;
using System.IO;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Keep the native game's writable registry outside verified runtime versions.</summary>
public static class PlayerRegistry
{
    private const long MaximumBytes = 8 * 1024 * 1024;

    public static string Bind(JsonObject profile, string dataRoot)
    {
        var environment = profile["native"]!["runtime_environment"]!.AsObject();
        var target = PackStorage.Resolve(dataRoot, "native-settings/mw3-registry.txt");
        PackStorage.EnsureNoLinks(target);
        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
        if (!File.Exists(target))
        {
            var source = environment["MW34_REG_OVERLAY"]?.GetValue<string>();
            var temporary = target + ".preparing-" + Guid.NewGuid().ToString("N");
            try
            {
                using (var destination = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                {
                    if (!string.IsNullOrEmpty(source))
                    {
                        if (!Path.IsPathFullyQualified(source))
                            throw new InvalidDataException("The previous native settings path is unresolved.");
                        PackStorage.EnsureNoLinks(source);
                        using var input = File.OpenRead(source);
                        var buffer = new byte[8192];
                        long total = 0;
                        int count;
                        while ((count = input.Read(buffer)) != 0)
                        {
                            if ((total += count) > MaximumBytes)
                                throw new InvalidDataException("The previous native settings file is too large.");
                            destination.Write(buffer, 0, count);
                        }
                    }
                    // New installations start empty. Translated game code creates
                    // its actual defaults; no captured configuration is supplied.
                    destination.Flush(true);
                }
                try { File.Move(temporary, target); }
                catch (IOException) when (File.Exists(target))
                {
                    // Another launcher completed first; preserve its player state.
                    PackStorage.EnsureNoLinks(target);
                }
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
        if (new FileInfo(target).Length > MaximumBytes)
            throw new InvalidDataException("The native player settings file is too large.");
        environment["MW34_REG_OVERLAY"] = target;
        return target;
    }
}
