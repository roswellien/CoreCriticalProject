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
        public int Version { get; set; } = 2;
        public string[] DefaultMap { get; set; } = [];
        public string[] ActiveConfig { get; set; } = [];
        public string[] LastAppliedDefaultMap { get; set; } = [];
        public string[] LastAppliedActiveConfig { get; set; } = [];
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
        var settingsEol = DetectLineEnding(settingsText);
        var hasRestore = File.Exists(restorePath);
        var restore = hasRestore ? ReadRestore(restorePath) : null;
        if (restore != null && ReconcilePlayerEdits(lines, restore))
        {
            ControlProfiles.AtomicWrite(restorePath, JsonSerializer.Serialize(restore));
            log("MW3-RE controls changed since the launcher applied its layout; preserved the latest in-game controls for restore.");
        }

        if (controls.ActiveId == null && !controllerProfile.Enabled)
        {
            if (restore != null)
            {
                WriteSettings(settingsPath, ApplyValues(lines, restore.DefaultMap, restore.ActiveConfig), settingsEol);
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
            }
            ControlProfiles.AtomicWrite(restorePath, JsonSerializer.Serialize(restore));

            var activePreset = ReadActivePreset(writeDirectory, gameDirectory, restore.ActiveConfig);
            if (activePreset == null || !ReadAxisRows(activePreset).Any())
                activePreset = ReadDefaultPreset(writeDirectory, gameDirectory);
            if (activePreset == null || !ReadAxisRows(activePreset).Any()) activePreset = DefaultAxesPreset();
            var controllerPreset = ControllerPreset(dataRoot, selected, controllerProfile, log);
            var preset = controllerPreset == null
                ? ControlProfiles.Preset(selected, activePreset)
                : ControlProfiles.Preset(selected, MergeControllerAxes(activePreset, controllerPreset));
            var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(preset)))[..20];
            var relative = @"keys\CC-" + hash + ".zrd";
            var target = Path.Combine(writeDirectory, "keys", "CC-" + hash + ".zrd");
            ControlProfiles.AtomicWrite(target, preset);
            var appliedMap = FormatMap(selected);
            var appliedConfig = FormatActiveConfig(relative);
            var updated = ApplyValues(lines, appliedMap, appliedConfig);
            WriteSettings(settingsPath, updated, settingsEol);
            restore.LastAppliedDefaultMap = appliedMap;
            restore.LastAppliedActiveConfig = appliedConfig;
            ControlProfiles.AtomicWrite(restorePath, JsonSerializer.Serialize(restore));
            log("Applied launcher key and mouse bindings to MW3-RE's per-profile controls files.");
        }

        PrepareJoystickSelection(writeDirectory, settings, log);
    }

    private static void PrepareJoystickSelection(string writeDirectory, LauncherSettings settings, Action<string> log)
    {
        var path = Path.Combine(writeDirectory, "mw3.cfg");
        var text = File.Exists(path) ? ReadSettings(path) : "";
        var rows = SplitLines(text);
        var lineEnding = DetectLineEnding(text);
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
        WriteSettings(path, rows, lineEnding);
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
        foreach (var action in ControlProfiles.Actions) selected.Bindings[action.Name].Joystick = 0;
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
            if (controllerAxis >= sourceNames.Length)
            {
                log($"Controller axis index {controllerAxis} for {names[i]} is unsupported by MW3's four-axis control file and was not applied.");
                continue;
            }
            var source = sourceNames[controllerAxis];
            var sourceIndex = controllerAxis switch { 0 => 0, 1 => 1, 2 => 3, _ => 4 };
            var axis = calibration.Axes[sourceIndex];
            var sensitivity = controller.Scale[axisByControl[i]] * (axis.Inverted ? -1 : 1);
            var deadzone = axis.Deadzone;
            // AxisBinding::value is slope * source + intercept. Throttle maps
            // the normalized stick range to the game's 1-to-0 throttle range.
            var slope = (i == 0 ? 0.5f : 1.0f) * sensitivity;
            var intercept = i == 0 ? 0.5f : 0.0f;
            axes.Append("    (").Append(names[i]).Append(" joystick(").Append(source).Append(") slope(")
                .Append(slope.ToString("R", CultureInfo.InvariantCulture)).Append(") intercept(")
                .Append(intercept.ToString("R", CultureInfo.InvariantCulture)).Append(") deadzone(")
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
            if (action.Command < 0 || action.Command >= 167)
                throw new InvalidDataException($"MW3 control command id {action.Command} is outside DefaultCmdMap.");
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

    private static string? ReadDefaultPreset(string writeDirectory, string gameDirectory)
    {
        foreach (var directory in new[] { writeDirectory, gameDirectory })
        {
            // The controls screen reads and writes keys\DefaultCtlConfig.zrd.
            // The write directory shadows the install's read-only copy.
            var path = Path.Combine(directory, "keys", "DefaultCtlConfig.zrd");
            if (!File.Exists(path)) continue;
            PackStorage.EnsureNoLinks(path);
            if (new FileInfo(path).Length > 512 * 1024) throw new InvalidDataException("Original controls preset is too large.");
            return File.ReadAllText(path);
        }
        return null;
    }

    // AxisTable's constructor values in controls_cfg.h: the rebuild uses these
    // same four mappings when no DefaultCtlConfig file exists yet.
    private static string DefaultAxesPreset() => "(\n  KEYS ()\n  AXES (\n" +
        "    (Throttle joystick(Z) slope(-0.5) intercept(0.5) deadzone(0.05))\n" +
        "    (Twist joystick(Rz) slope(-1) intercept(0) deadzone(0))\n" +
        "    (Pitch joystick(Y) slope(1) intercept(0) deadzone(0))\n" +
        "    (LR joystick(X) slope(-1) intercept(0) deadzone(0))\n  )\n)\n";

    private static string MergeControllerAxes(string activePreset, string controllerPreset)
    {
        var axes = ReadAxisRows(activePreset).ToDictionary(AxisName, StringComparer.Ordinal);
        foreach (var row in ReadAxisRows(controllerPreset)) axes[AxisName(row)] = row;
        var names = new[] { "Throttle", "Twist", "Pitch", "LR" };
        return "(\n  KEYS ()\n  AXES (\n" +
            string.Join("\n", names.Where(axes.ContainsKey).Select(name => "    " + axes[name])) +
            "\n  )\n)\n";
    }

    private static IEnumerable<string> ReadAxisRows(string preset)
    {
        var nameAt = preset.IndexOf("AXES", StringComparison.OrdinalIgnoreCase);
        if (nameAt < 0) yield break;
        var openAt = preset.IndexOf('(', nameAt + 4);
        if (openAt < 0) yield break;
        var depth = 1;
        var entryStart = -1;
        for (var i = openAt + 1; i < preset.Length; i++)
        {
            if (preset[i] == '(')
            {
                if (depth == 1) entryStart = i;
                depth++;
                continue;
            }
            if (preset[i] != ')') continue;
            depth--;
            if (depth == 1 && entryStart >= 0)
            {
                var row = preset[entryStart..(i + 1)].Trim();
                if (AxisName(row) is "Throttle" or "Twist" or "Pitch" or "LR") yield return row;
                entryStart = -1;
            }
            if (depth == 0) yield break;
        }
    }

    private static string AxisName(string row)
    {
        var value = row.TrimStart('(', ' ', '\t');
        var end = value.IndexOfAny([' ', '\t', ')']);
        return end < 0 ? "" : value[..end];
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
        if (new FileInfo(path).Length > 32768) throw new InvalidDataException("Native controls restore data is too large.");
        var state = JsonSerializer.Deserialize<RestoreState>(File.ReadAllText(path))
            ?? throw new InvalidDataException("Native controls restore data is empty.");
        if (state.Version is < 1 or > 2 || state.DefaultMap == null || state.ActiveConfig == null ||
            state.LastAppliedDefaultMap == null || state.LastAppliedActiveConfig == null ||
            state.DefaultMap.Length > 64 || state.ActiveConfig.Length > 16 ||
            state.LastAppliedDefaultMap.Length > 64 || state.LastAppliedActiveConfig.Length > 16 ||
            state.DefaultMap.Concat(state.ActiveConfig).Concat(state.LastAppliedDefaultMap).Concat(state.LastAppliedActiveConfig)
                .Any(row => row == null || row.Length > 8192 || row.StartsWith('[')))
            throw new InvalidDataException("Native controls restore data is invalid.");
        if (state.Version == 1) state.Version = 2;
        return state;
    }

    private static string ReadSettings(string path)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 1024 * 1024) throw new InvalidDataException("MW3-RE settings file is too large.");
        return File.ReadAllText(path);
    }

    private static List<string> SplitLines(string text) => text.Length == 0 ? [] : text.Split('\n').Select(row => row.TrimEnd('\r')).ToList();

    private static string DetectLineEnding(string text) => text.Contains("\r\n", StringComparison.Ordinal) ? "\r\n" : "\n";

    private static void WriteSettings(string path, List<string> lines, string lineEnding) =>
        ControlProfiles.AtomicWrite(path, string.Join(lineEnding, lines.Select(row =>
            row.Replace("\r\n", "\n", StringComparison.Ordinal).Replace("\n", lineEnding, StringComparison.Ordinal)))
            .TrimEnd('\r', '\n') + lineEnding);

    private static bool ReconcilePlayerEdits(List<string> lines, RestoreState restore)
    {
        if (restore.LastAppliedDefaultMap.Length == 0 && restore.LastAppliedActiveConfig.Length == 0) return false;
        var currentMap = FindValue(lines, DefaultMap);
        var currentConfig = FindValue(lines, ActiveConfig);
        if (EquivalentValue(currentMap, restore.LastAppliedDefaultMap) &&
            EquivalentValue(currentConfig, restore.LastAppliedActiveConfig)) return false;
        restore.DefaultMap = currentMap;
        restore.ActiveConfig = currentConfig;
        return true;
    }

    private static bool EquivalentValue(string[] left, string[] right) => NormalizeValue(left) == NormalizeValue(right);

    private static string NormalizeValue(string[] rows)
    {
        var normalized = new StringBuilder();
        foreach (var row in rows)
            foreach (var character in row)
                if (!char.IsWhiteSpace(character) && character != '\\') normalized.Append(char.ToLowerInvariant(character));
        return normalized.ToString();
    }
}
