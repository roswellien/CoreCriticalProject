using System;
using System.IO;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Keep the native game's writable registry outside verified runtime versions.</summary>
public static class PlayerRegistry
{
    private const long MaximumBytes = 8 * 1024 * 1024;

    public static string PrepareInstalledRenderer(JsonObject profile, string dataRoot, string gameDirectory)
    {
        // Retail 1.2 reads HKLM InstallOptions at 0x59803d, and masks its low
        // byte when initializing HWCardFlag at 0x40c47e. A copied data install
        // has no original installer registry. Bit 4 is Hardware_Texture_8.
        GameInstallation.VerifyHardwareRendererFiles(gameDirectory);
        var target = Bind(profile, dataRoot);
        var text = File.ReadAllText(target);
        var configured = ConfigureHardwareRenderer(text);
        if (configured != text) ControlProfiles.AtomicWrite(target, configured);
        return target;
    }

    public static string ConfigureHardwareRenderer(string text)
    {
        const string userKey = @"hkcu\software\microprose\mechwarrior 3\1.0";
        const string installKey = @"hklm\software\microprose\mechwarrior 3\1.0";
        var values = new[] {
            (Key: installKey, Name: "installoptions", Hex: "04000000"),
            (Key: userKey, Name: "hwcardflag", Hex: "01000000"),
            (Key: userKey, Name: "hwcarddev", Hex: "00000000")
        };
        var rows = text.Split('\n').Select(r => r.TrimEnd('\r')).Where(r => r.Length > 0)
            .Where(r => !values.Any(v => r.StartsWith("V " + v.Key + "\t" + v.Name + "\t", StringComparison.OrdinalIgnoreCase)))
            .ToList();
        foreach (var key in new[] { installKey, userKey })
            if (!rows.Any(r => r.Equals("K " + key, StringComparison.OrdinalIgnoreCase))) rows.Add("K " + key);
        // The modern native backend exposes one Vulkan-backed hardware device.
        // Only its installation/device selection is launcher-owned; game defaults,
        // pilot state and controls remain owned by the translated game/player.
        rows.AddRange(values.Select(v => "V " + v.Key + "\t" + v.Name + "\t4\t" + v.Hex));
        return string.Join('\n', rows) + "\n";
    }

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
                    // Translated game code owns gameplay defaults. Installed
                    // renderer component selection is supplied separately.
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
