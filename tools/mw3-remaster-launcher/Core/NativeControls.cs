using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>Projects launcher controls into one MW3-RE write profile.</summary>
public static class NativeControls
{
    private const string RegistrySection =
        "[HKEY_CURRENT_USER\\SOFTWARE\\MicroProse\\MechWarrior 3\\1.0]";
    private const string DefaultMap = "DefaultCmdMap";
    private const string ActiveConfig = "ActiveCtlCfg";
    private const string RestoreFile = "launcher-controls.restore.json";

    private sealed class RestoreState
    {
        public int Version { get; set; } = 1;
        public string[] DefaultMap { get; set; } = [];
        public string[] ActiveConfig { get; set; } = [];
    }

    public static void PrepareLaunch(string dataRoot, string writeDirectory, string gameDirectory,
        LauncherSettings settings, Action<string> log)
    {
        var controls = new ControlProfiles(dataRoot).LoadForLaunch();
        var controllerProfile = new ControllerProfiles(dataRoot).Load();
        var settingsPath = Path.Combine(writeDirectory, "settings.reg");
        var restorePath = Path.Combine(writeDirectory, RestoreFile);
        var settingsText = File.Exists(settingsPath) ? ReadSettings(settingsPath) : "";
        var lines = SplitLines(settingsText);
        var hasRestore = File.Exists(restorePath);
        var restore = hasRestore ? ReadRestore(restorePath) : null;

        if (controls.ActiveId == null && !controllerProfile.Enabled)
        {
            if (restore != null)
            {
                WriteSettings(settingsPath, ApplyValues(lines, restore.DefaultMap, restore.ActiveConfig));
                File.Delete(restorePath);
                log("Restored MW3-RE's saved controls from before the launcher layout was applied.");
            }
            else
            {
                log("No launcher key layout is selected; MW3-RE will use its saved controls.");
            }
        }
        else
        {
            var selected = controls.ActiveId == null
                ? Mw3DefaultControls.Create()
                : controls.Profiles.Single(profile => profile.Id == controls.ActiveId);
            if (restore == null)
            {
                restore = new RestoreState
                {
                    DefaultMap = FindValue(lines, DefaultMap),
                    ActiveConfig = FindValue(lines, ActiveConfig)
                };
                ControlProfiles.AtomicWrite(restorePath, JsonSerializer.Serialize(restore));
            }

            var controllerPreset = ControllerPreset(dataRoot, selected, controllerProfile, log);
            var preset = controllerPreset == null
                ? ControlProfiles.Preset(selected, ReadActivePreset(writeDirectory, gameDirectory, restore.ActiveConfig))
                : ControlProfiles.Preset(selected, controllerPreset);
            var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(preset)))[..20];
            var relative = @"keys\CC-" + hash + ".zrd";
            var target = Path.Combine(writeDirectory, "keys", "CC-" + hash + ".zrd");
            ControlProfiles.AtomicWrite(target, preset);
            var updated = ApplyValues(lines, FormatMap(selected), FormatActiveConfig(relative));
            WriteSettings(settingsPath, updated);
            log("Applied launcher key and mouse bindings to MW3-RE's per-profile controls files.");
        }

        PrepareJoystickSelection(writeDirectory, settings, log);
    }

    private static void PrepareJoystickSelection(string writeDirectory, LauncherSettings settings, Action<string> log)
    {
        var path = Path.Combine(writeDirectory, "mw3.cfg");
        var rows = File.Exists(path) ? ReadSettings(path).Split('\n').ToList() : [];
        rows.RemoveAll(row => row.TrimEnd('\r').StartsWith("joystick=", StringComparison.OrdinalIgnoreCase));
        var automatic = !settings.DirectInputJoystickNone &&
            string.IsNullOrWhiteSpace(settings.DirectInputJoystickProductName);
        if (!automatic)
        {
            var value = settings.DirectInputJoystickNone ? "none" : settings.DirectInputJoystickProductName.Trim();
            if (value.Any(char.IsControl) || value.Contains('\n') || value.Contains('\r'))
                throw new InvalidDataException("The selected joystick product name contains invalid characters.");
            rows.Add("joystick=" + value);
        }
        WriteSettings(path, rows);
        if (automatic)
            log("Joystick selection is automatic; MW3-RE will choose its best ranked attached device.");
        else if (settings.DirectInputJoystickNone)
            log("Disabled joystick selection for this MW3-RE profile.");
        else
            log("Selected joystick by its DirectInput product name in this MW3-RE profile; duplicate product names select the first match.");
    }

    private static string? ControllerPreset(string dataRoot, ControlProfile selected, ControllerProfile controller,
        Action<string> log)
    {
        if (!controller.Enabled) return null;
        log("MW3-RE applies the controller layout's first 15 button mappings and four stick assignments. " +
            "Trigger mappings, buttons 16 through 26, calibration response curves and calibrated center/range " +
            "are not representable by the original game control file.");
        log("The saved SDL controller identity cannot be matched exactly by MW3-RE; confirm the selected " +
            "DirectInput product name resolves to the same device.");
        var calibration = ControllerCalibration.Load(dataRoot, controller.DeviceKey);
        for (var button = 0; button < 15; button++)
        {
            var command = controller.Buttons[button];
            if (command == 0) continue;
            var action = ControlProfiles.Actions.FirstOrDefault(item => item.Command == command);
            if (action == null) continue;
            selected.Bindings[action.Name].Joystick = button + 1;
        }

        var unsupportedButtons = controller.Buttons.Skip(15).Count(command => command != 0);
        if (unsupportedButtons > 0)
            log($"Controller layout has {unsupportedButtons} assigned buttons beyond MW3's 15-button control-file limit; those bindings are not applied.");
        if (controller.Triggers.Any(command => command != 0))
            log("Controller trigger-to-action bindings are not applied: MW3-RE's original control file has no trigger threshold mapping.");

        var axisByControl = new[] { 0, 2, 3, 1 }; // throttle, twist, pitch, turn
        var names = new[] { "Throttle", "Twist", "Pitch", "LR" };
        var sourceNames = new[] { "X", "Y", "Rx", "Ry" };
        var axes = new StringBuilder("(\n  KEYS ()\n  AXES (\n");
        for (var i = 0; i < axisByControl.Length; i++)
        {
            var controllerAxis = controller.Axes[axisByControl[i]];
            if (controllerAxis < 0) continue;
            var source = sourceNames[controllerAxis];
            var sourceIndex = controllerAxis switch { 0 => 0, 1 => 1, 2 => 3, _ => 4 };
            var axis = calibration.Axes[sourceIndex];
            var sensitivity = controller.Scale[axisByControl[i]] * (axis.Inverted ? -1 : 1);
            var deadzone = axis.Deadzone;
            axes.Append("    (").Append(names[i]).Append(" joystick(").Append(source).Append(") slope(")
                .Append(sensitivity.ToString("R", CultureInfo.InvariantCulture)).Append(") intercept(0) deadzone(")
                .Append(deadzone.ToString("R", CultureInfo.InvariantCulture)).AppendLine("))");
            if (axis.Response != 1 || axis.Center != 0 || axis.Minimum != -32768 || axis.Maximum != 32767)
                log($"Controller calibration for {source} uses response/center/range values that MW3's original axis format cannot represent; only deadzone and inversion are applied.");
        }
        axes.Append("  )\n)\n");
        return axes.ToString();
    }

    private static string[] FormatMap(ControlProfile profile)
    {
        var bytes = new byte[167 * sizeof(uint)];
        foreach (var action in ControlProfiles.Actions)
        {
            var binding = profile.Bindings[action.Name];
            uint packed = (uint)(binding.Primary | (binding.Secondary << 11) |
                (binding.Joystick << 22) | (binding.Mouse << 26));
            System.Buffers.Binary.BinaryPrimitives.WriteUInt32LittleEndian(bytes.AsSpan(action.Command * 4, 4), packed);
        }
        return ["\"DefaultCmdMap\"=" + FormatHex(bytes)];
    }

    private static string[] FormatActiveConfig(string relativePath)
    {
        var bytes = new byte[260];
        Encoding.ASCII.GetBytes(relativePath).CopyTo(bytes, 0);
        return ["\"ActiveCtlCfg\"=" + FormatHex(bytes)];
    }

    private static string FormatHex(byte[] bytes)
    {
        var result = new StringBuilder("hex:");
        for (var i = 0; i < bytes.Length; i++)
        {
            if (i > 0) result.Append(',');
            if (i > 0 && i % 24 == 0) result.Append("\\\n  ");
            result.Append(bytes[i].ToString("x2"));
        }
        return result.ToString();
    }

    private static string[] FindValue(List<string> lines, string name)
    {
        var section = false;
        for (var i = 0; i < lines.Count; i++)
        {
            var row = lines[i];
            if (row.StartsWith('[')) section = row.Equals(RegistrySection, StringComparison.OrdinalIgnoreCase);
            if (!section || !StartsValue(row, name)) continue;
            var value = new List<string> { row };
            while (value[^1].TrimEnd('\r').EndsWith('\\') && i + 1 < lines.Count) value.Add(lines[++i]);
            return value.ToArray();
        }
        return [];
    }

    private static string? ReadActivePreset(string writeDirectory, string gameDirectory, string[] activeValue)
    {
        if (activeValue.Length == 0) return null;
        var encoded = string.Join("", activeValue).Split("hex:", 2, StringSplitOptions.None);
        if (encoded.Length != 2) return null;
        var hex = new string(encoded[1].Where(Uri.IsHexDigit).ToArray());
        if (hex.Length < 2 || hex.Length % 2 != 0) return null;
        var data = Convert.FromHexString(hex);
        var end = Array.IndexOf(data, (byte)0);
        if (end < 0) end = data.Length;
        var name = Encoding.ASCII.GetString(data, 0, end)
            .Replace('\\', Path.DirectorySeparatorChar).Replace('/', Path.DirectorySeparatorChar);
        if (string.IsNullOrWhiteSpace(name) || Path.IsPathRooted(name) || name.Split(Path.DirectorySeparatorChar).Any(part => part == ".."))
            return null;
        foreach (var directory in new[] { writeDirectory, gameDirectory })
        {
            var path = Path.GetFullPath(name, directory);
            if (!File.Exists(path)) continue;
            PackStorage.EnsureNoLinks(path);
            if (new FileInfo(path).Length > 512 * 1024) throw new InvalidDataException("Original controls preset is too large.");
            return File.ReadAllText(path);
        }
        return null;
    }

    private static List<string> ApplyValues(List<string> source, string[] map, string[] active)
    {
        var lines = RemoveValue(source, DefaultMap);
        lines = RemoveValue(lines, ActiveConfig);
        var sectionIndex = lines.FindIndex(row => row.Equals(RegistrySection, StringComparison.OrdinalIgnoreCase));
        if (sectionIndex < 0)
        {
            if (lines.Count > 0 && lines[^1].Length != 0) lines.Add("");
            lines.Add(RegistrySection);
            sectionIndex = lines.Count - 1;
        }
        var insertAt = sectionIndex + 1;
        if (map.Length > 0) lines.InsertRange(insertAt, map);
        insertAt += map.Length;
        if (active.Length > 0) lines.InsertRange(insertAt, active);
        return lines;
    }

    private static List<string> RemoveValue(List<string> source, string name)
    {
        var lines = new List<string>();
        var section = false;
        for (var i = 0; i < source.Count; i++)
        {
            var row = source[i];
            if (row.StartsWith('[')) section = row.Equals(RegistrySection, StringComparison.OrdinalIgnoreCase);
            if (section && StartsValue(row, name))
            {
                while (row.TrimEnd('\r').EndsWith('\\') && i + 1 < source.Count) row = source[++i];
                continue;
            }
            lines.Add(row);
        }
        return lines;
    }

    private static bool StartsValue(string row, string name) =>
        row.StartsWith("\"" + name + "\"=", StringComparison.OrdinalIgnoreCase);

    private static RestoreState ReadRestore(string path)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 16384) throw new InvalidDataException("Native controls restore data is too large.");
        var state = JsonSerializer.Deserialize<RestoreState>(File.ReadAllText(path))
            ?? throw new InvalidDataException("Native controls restore data is empty.");
        if (state.Version != 1 || state.DefaultMap.Length > 64 || state.ActiveConfig.Length > 16 ||
            state.DefaultMap.Concat(state.ActiveConfig).Any(row => row.Length > 1024 || row.StartsWith('[')))
            throw new InvalidDataException("Native controls restore data is invalid.");
        return state;
    }

    private static string ReadSettings(string path)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 1024 * 1024) throw new InvalidDataException("MW3-RE settings file is too large.");
        return File.ReadAllText(path);
    }

    private static List<string> SplitLines(string text) => text.Length == 0 ? [] : text.Split('\n').ToList();

    private static void WriteSettings(string path, List<string> lines) =>
        ControlProfiles.AtomicWrite(path, string.Join('\n', lines).TrimEnd('\n') + "\n");
}
