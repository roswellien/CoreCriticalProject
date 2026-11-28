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
    private const string GameOptions = "GameOptions";
    private const uint DefaultGameOptions = 0x49; // options.h: camera 1, heat and joystick.
    private const uint JumpJetsBit = 0x80;
    private const string RestoreFile = "launcher-controls.restore.json";

    private sealed class RestoreState
    {
        public int Version { get; set; } = 3;
        public string[] DefaultMap { get; set; } = [];
        public string[] ActiveConfig { get; set; } = [];
        public string[] LastAppliedDefaultMap { get; set; } = [];
        public string[] LastAppliedActiveConfig { get; set; } = [];
        public bool HasOriginalGameOptions { get; set; }
        public uint? OriginalGameOptions { get; set; }
        public uint? LastAppliedGameOptions { get; set; }
        public PendingApplication? Pending { get; set; }
    }

    // The restore file and registry replace are separate writes. Keep both the previous and
    // the intended projections until the settings write has completed.
    private sealed class PendingApplication
    {
        public string[] DefaultMap { get; set; } = [];
        public string[] ActiveConfig { get; set; } = [];
        public bool WritesGameOptions { get; set; }
        public bool KeepsGameOptionsOverride { get; set; }
        public uint? GameOptions { get; set; }
    }

    public static string? ExportControllerProfile(string dataRoot, string profileDirectory, ControllerProfile profile)
    {
        if (!profile.Enabled) return null;
        var path = ControllerProfilePath(profileDirectory);
        ControlProfiles.AtomicWrite(path, ControllerProfiles.Export(profile,
            ControllerCalibration.Load(dataRoot, profile.DeviceKey)));
        return path;
    }

    public static string ControllerProfilePath(string profileDirectory) =>
        Path.Combine(profileDirectory, "mw3-controller.txt");

    public static IReadOnlyList<string> ControllerArguments(ControllerProfile profile, string? path)
    {
        if (!profile.Enabled) return Array.Empty<string>();
        if (string.IsNullOrWhiteSpace(path)) throw new InvalidOperationException("Enabled controller profile has no exported file.");
        return ["--cc-controller", path];
    }

    internal static ControlProfile? LoadSelectedProfile(string dataRoot)
    {
        var controls = new ControlProfiles(dataRoot).LoadForLaunch();
        return controls.Profiles.SingleOrDefault(profile => profile.Id == controls.ActiveId);
    }

    public static string? PrepareLaunch(string dataRoot, string writeDirectory, string gameDirectory,
        LauncherSettings settings, Action<string> log) =>
        PrepareLaunch(dataRoot, writeDirectory, gameDirectory, settings, LoadSelectedProfile(dataRoot),
            new ControllerProfiles(dataRoot).Load(), log);

    internal static string? PrepareLaunch(string dataRoot, string writeDirectory, string gameDirectory,
        LauncherSettings settings, ControlProfile? profile, ControllerProfile controllerProfile, Action<string> log)
    {
        var settingsPath = Path.Combine(writeDirectory, "settings.reg");
        var restorePath = Path.Combine(writeDirectory, RestoreFile);
        var settingsText = File.Exists(settingsPath) ? ReadSettings(settingsPath) : "";
        var lines = SplitLines(settingsText);
        var settingsEol = DetectLineEnding(settingsText);
        var restore = File.Exists(restorePath) ? ReadRestore(restorePath) : null;
        var jumpJets = profile?.Mw2JumpJets;
        var currentOptions = jumpJets.HasValue || restore?.HasOriginalGameOptions == true
            ? ReadGameOptions(lines) : null;
        if (restore != null)
        {
            RecoverPendingApplication(lines, currentOptions, restore);
            var controlsEdited = ReconcilePlayerEdits(lines, restore);
            var optionsEdited = ReconcileGameOptions(currentOptions, restore);
            if (controlsEdited || optionsEdited)
                log("MW3-RE controls changed since the launcher applied its layout; preserved the latest in-game controls for restore.");
        }

        if (profile == null && !controllerProfile.Enabled)
        {
            if (restore != null)
            {
                var updated = ApplyValues(lines, restore.DefaultMap, restore.ActiveConfig);
                if (restore.HasOriginalGameOptions) SetGameOptions(updated, restore.OriginalGameOptions);
                // Reconciled baselines must survive a failure while replacing settings.reg.
                SaveRestore(restorePath, restore);
                WriteSettings(settingsPath, updated, settingsEol);
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
            // Controller projection clears legacy joystick slots on a private copy.
            var selected = profile == null ? Mw3DefaultControls.Create() : ControlProfiles.Clone(profile, profile.Name);
            restore ??= new RestoreState
            {
                DefaultMap = FindValue(lines, DefaultMap),
                ActiveConfig = FindValue(lines, ActiveConfig)
            };

            var activePreset = ReadActivePreset(writeDirectory, gameDirectory, restore.ActiveConfig);
            if (activePreset == null || !ReadAxisRows(activePreset).Any())
                activePreset = ReadDefaultPreset(writeDirectory, gameDirectory);
            if (activePreset == null || !ReadAxisRows(activePreset).Any()) activePreset = DefaultAxesPreset();
            var controllerPreset = ControllerPreset(selected, controllerProfile);
            if (controllerProfile.Enabled)
            {
                _ = ExportControllerProfile(dataRoot, writeDirectory, controllerProfile);
                log("Applied the full saved controller profile through MW3-RE's native controller input path.");
            }
            var preset = ControlProfiles.Preset(selected, controllerPreset ?? activePreset);
            var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(preset)))[..20];
            var relative = @"keys\CC-" + hash + ".zrd";
            var target = Path.Combine(writeDirectory, "keys", "CC-" + hash + ".zrd");
            ControlProfiles.AtomicWrite(target, preset);

            var pending = new PendingApplication
            {
                DefaultMap = FormatMap(selected),
                ActiveConfig = FormatActiveConfig(relative),
                WritesGameOptions = jumpJets.HasValue || restore.HasOriginalGameOptions,
                KeepsGameOptionsOverride = jumpJets.HasValue,
                GameOptions = restore.OriginalGameOptions
            };
            if (jumpJets.HasValue)
            {
                if (!restore.HasOriginalGameOptions)
                {
                    restore.HasOriginalGameOptions = true;
                    restore.OriginalGameOptions = currentOptions;
                }
                var options = currentOptions ?? DefaultGameOptions;
                pending.GameOptions = jumpJets.Value ? options | JumpJetsBit : options & ~JumpJetsBit;
            }
            var updated = ApplyValues(lines, pending.DefaultMap, pending.ActiveConfig);
            if (pending.WritesGameOptions) SetGameOptions(updated, pending.GameOptions);
            restore.Pending = pending;
            SaveRestore(restorePath, restore);
            WriteSettings(settingsPath, updated, settingsEol);
            CompleteApplication(restore, pending);
            SaveRestore(restorePath, restore);
            log("Applied launcher key and mouse bindings to MW3-RE's per-profile controls files.");
        }

        var inputPath = ExportInputBindings(writeDirectory, profile, out var bindingCount);
        var jumpJetsState = jumpJets.HasValue ? (jumpJets.Value ? "enabled" : "disabled") : "use game setting";
        log($"Applied {bindingCount} extended MW3-RE input binding(s). MW2JJets: {jumpJetsState}.");
        PrepareJoystickSelection(writeDirectory, settings, log);
        return inputPath;
    }

    private static string? ExportInputBindings(string writeDirectory, ControlProfile? profile, out int count)
    {
        var path = Path.GetFullPath(Path.Combine(writeDirectory, "mw3-input.txt"));
        count = 0;
        if (profile == null || !ControlProfiles.UsesExtendedInputBindings(profile))
        {
            PackStorage.EnsureNoLinks(path);
            PackStorage.EnsureNoLinks(path + ".previous");
            if (File.Exists(path)) File.Delete(path);
            if (File.Exists(path + ".previous")) File.Delete(path + ".previous");
            return null;
        }

        var text = new StringBuilder("CC_MW3_INPUT_V1\n");
        foreach (var action in ControlProfiles.Actions.OrderBy(action => action.Command))
        {
            var binding = profile.Bindings[action.Name];
            if (binding.Mouse > 3)
            {
                text.Append(CultureInfo.InvariantCulture, $"MOUSE {action.Command} {binding.Mouse}\n");
                count++;
            }
            var combos = (binding.Combos ?? []).Select(combo => new
            {
                combo.Suppress,
                Count = combo.Inputs.Count,
                Inputs = ControlProfiles.CanonicalCombo(combo)
            }).OrderBy(combo => combo.Inputs, StringComparer.Ordinal);
            foreach (var combo in combos)
            {
                var suppress = combo.Suppress ? 1 : 0;
                text.Append(CultureInfo.InvariantCulture, $"COMBO {action.Command} {suppress} {combo.Count} {combo.Inputs}\n");
                count++;
            }
        }
        ControlProfiles.AtomicWrite(path, text.ToString());
        return path;
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

    private static string? ControllerPreset(ControlProfile selected, ControllerProfile controller)
    {
        if (!controller.Enabled) return null;
        foreach (var action in ControlProfiles.Actions) selected.Bindings[action.Name].Joystick = 0;

        var axisByControl = new[] { 0, 2, 3, 1 }; // throttle, twist, pitch, turn
        var names = new[] { "Throttle", "Twist", "Pitch", "LR" };
        var sourceNames = new[] { "X", "Y", "Rx", "Ry" };
        var axes = new StringBuilder("(\n  KEYS ()\n  AXES (\n");
        for (var i = 0; i < axisByControl.Length; i++)
        {
            var controllerAxis = controller.Axes[axisByControl[i]];
            if (controllerAxis < 0) continue;
            if (controllerAxis >= sourceNames.Length)
                throw new InvalidDataException("Validated controller profile contains an unsupported stick axis.");
            var source = sourceNames[controllerAxis];
            // SDL input applies calibration, deadzone, response and inversion. This
            // legacy .zrd row only routes the selected source and applies sensitivity.
            var sensitivity = controller.Scale[axisByControl[i]];
            const double deadzone = 0;
            // AxisBinding::value is slope * source + intercept. Throttle maps
            // the normalized stick range to the game's 1-to-0 throttle range.
            var slope = (i == 0 ? 0.5f : 1.0f) * sensitivity;
            var intercept = i == 0 ? 0.5f : 0.0f;
            axes.Append("    (").Append(names[i]).Append(" joystick(").Append(source).Append(") slope(")
                .Append(slope.ToString("R", CultureInfo.InvariantCulture)).Append(") intercept(")
                .Append(intercept.ToString("R", CultureInfo.InvariantCulture)).Append(") deadzone(")
                .Append(deadzone.ToString("R", CultureInfo.InvariantCulture)).AppendLine("))");
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
            var legacyMouse = binding.Mouse <= 3 ? binding.Mouse : 0;
            uint packed = (uint)(binding.Primary | (binding.Secondary << 11) |
                (binding.Joystick << 22) | (legacyMouse << 26));
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

    private static int FindGameOptionsRow(List<string> lines)
    {
        var inSection = false;
        var index = -1;
        for (var i = 0; i < lines.Count; i++)
        {
            var row = lines[i].Trim();
            if (row.StartsWith('['))
                inSection = row.Equals(RegistrySection, StringComparison.OrdinalIgnoreCase);
            if (!inSection || !row.Split('=', 2)[0].TrimEnd().Equals(
                    "\"GameOptions\"", StringComparison.OrdinalIgnoreCase)) continue;
            if (index >= 0) throw new InvalidDataException("Duplicate HKCU GameOptions in MW3-RE settings.reg.");
            index = i;
        }
        return index;
    }

    private static uint? ReadGameOptions(List<string> lines)
    {
        var index = FindGameOptionsRow(lines);
        if (index < 0) return null;
        var parts = lines[index].Split('=', 2);
        var value = parts.Length == 2 ? parts[1].Trim() : "";
        const string prefix = "dword:";
        if (!value.StartsWith(prefix, StringComparison.OrdinalIgnoreCase) || value.Length != prefix.Length + 8 ||
            !uint.TryParse(value.AsSpan(prefix.Length), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture, out var options))
            throw new InvalidDataException("HKCU GameOptions in MW3-RE settings.reg must be a DWORD.");
        return options;
    }

    private static void SetGameOptions(List<string> lines, uint? value)
    {
        var index = FindGameOptionsRow(lines);
        if (!value.HasValue)
        {
            if (index >= 0) lines.RemoveAt(index);
            return;
        }
        var row = FormattableString.Invariant($"\"{GameOptions}\"=dword:{value.Value:x8}");
        if (index >= 0) lines[index] = row;
        else lines.Insert(lines.FindIndex(line => line.Equals(RegistrySection, StringComparison.OrdinalIgnoreCase)) + 1, row);
    }

    private static void SaveRestore(string path, RestoreState restore) =>
        ControlProfiles.AtomicWrite(path, JsonSerializer.Serialize(restore));

    private static void CompleteApplication(RestoreState restore, PendingApplication pending)
    {
        restore.LastAppliedDefaultMap = pending.DefaultMap;
        restore.LastAppliedActiveConfig = pending.ActiveConfig;
        CompleteGameOptions(restore, pending);
        restore.Pending = null;
    }

    private static void CompleteGameOptions(RestoreState restore, PendingApplication pending)
    {
        if (!pending.WritesGameOptions) return;
        restore.HasOriginalGameOptions = pending.KeepsGameOptionsOverride;
        restore.LastAppliedGameOptions = pending.KeepsGameOptionsOverride ? pending.GameOptions : null;
        if (!pending.KeepsGameOptionsOverride) restore.OriginalGameOptions = null;
    }

    private static void RecoverPendingApplication(List<string> lines, uint? currentOptions, RestoreState restore)
    {
        var pending = restore.Pending;
        if (pending == null) return;
        // An atomic settings replace may have completed before the final restore write.
        // A value matching the intended projection is still launcher-owned.
        if (EquivalentValue(FindValue(lines, DefaultMap), pending.DefaultMap))
            restore.LastAppliedDefaultMap = pending.DefaultMap;
        if (EquivalentValue(FindValue(lines, ActiveConfig), pending.ActiveConfig))
            restore.LastAppliedActiveConfig = pending.ActiveConfig;
        if (pending.WritesGameOptions && currentOptions == pending.GameOptions)
            CompleteGameOptions(restore, pending);
        restore.Pending = null;
    }

    private static bool ReconcileGameOptions(uint? current, RestoreState restore)
    {
        if (restore.OriginalGameOptions is not uint original || current is not uint live ||
            restore.LastAppliedGameOptions == live) return false;
        // If the player changed other options, retain the original jump-jet bit.
        // A different jump-jet bit from the applied bit is itself a live edit.
        var reconciled = live;
        if (restore.LastAppliedGameOptions is uint applied && ((live ^ applied) & JumpJetsBit) == 0)
            reconciled = (live & ~JumpJetsBit) | (original & JumpJetsBit);
        restore.OriginalGameOptions = reconciled;
        return reconciled != original;
    }

    private static RestoreState ReadRestore(string path)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 65536) throw new InvalidDataException("Native controls restore data is too large.");
        var state = JsonSerializer.Deserialize<RestoreState>(File.ReadAllText(path))
            ?? throw new InvalidDataException("Native controls restore data is empty.");
        if (state.Version is < 1 or > 3 || !ValidRestoreRows(state.DefaultMap, 64) ||
            !ValidRestoreRows(state.ActiveConfig, 16) || !ValidRestoreRows(state.LastAppliedDefaultMap, 64) ||
            !ValidRestoreRows(state.LastAppliedActiveConfig, 16))
            throw new InvalidDataException("Native controls restore data is invalid.");
        if (state.Version < 3)
        {
            state.Version = 3;
            state.HasOriginalGameOptions = false;
            state.OriginalGameOptions = null;
            state.LastAppliedGameOptions = null;
            state.Pending = null;
        }
        var pending = state.Pending;
        if ((!state.HasOriginalGameOptions && (state.OriginalGameOptions.HasValue || state.LastAppliedGameOptions.HasValue)) ||
            (pending != null && (!ValidRestoreRows(pending.DefaultMap, 64) ||
                !ValidRestoreRows(pending.ActiveConfig, 16) ||
                (pending.WritesGameOptions && !state.HasOriginalGameOptions) ||
                (pending.KeepsGameOptionsOverride && (!pending.WritesGameOptions || !pending.GameOptions.HasValue)))))
            throw new InvalidDataException("Native controls GameOptions restore data is invalid.");
        return state;
    }

    private static bool ValidRestoreRows(string[]? rows, int limit) =>
        rows != null && rows.Length <= limit &&
        rows.All(row => row != null && row.Length <= 8192 && !row.StartsWith('['));

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
        // Each value is the player's own only if it differs from what the launcher applied; an unchanged
        // value still holds the launcher's layout, so its pre-launcher baseline must stay as it was.
        var mapEditedInGame = !EquivalentValue(currentMap, restore.LastAppliedDefaultMap);
        var configEditedInGame = !EquivalentValue(currentConfig, restore.LastAppliedActiveConfig);
        if (mapEditedInGame) restore.DefaultMap = currentMap;
        if (configEditedInGame) restore.ActiveConfig = currentConfig;
        return mapEditedInGame || configEditedInGame;
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
