using System.Buffers.Binary;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace MW3RemasterLauncher.Core;

public sealed record ControlAction(string Name, int Command)
{
    public string Label => System.Globalization.CultureInfo.CurrentCulture.TextInfo.ToTitleCase(Name[4..]
        .Replace("THROTTLE_DN", "Throttle down").Replace("JJ_", "Jump jets ").Replace("CYCLE_CAM", "Cycle camera")
        .Replace("VMODE_TOGGLE", "Toggle view mode").Replace("TOGGLE_TMODE", "Toggle torso mode").Replace("WEPGRP", "Weapon group").Replace("WEP", "Weapon").Replace('_', ' ').ToLowerInvariant());
    public string Group => Name.Contains("TARGET") ? "Targeting" :
        Name.Contains("CAM") || Name.Contains("LOOK") || Name.Contains("ZOOM") || Name.Contains("VMODE") ? "Camera & view" :
        Name.Contains("THROTTLE") || Name.Contains("TURN") || Name.Contains("TWIST") || Name.Contains("PITCH") ||
        Name.Contains("CENTER") || Name.Contains("TMODE") || Name.Contains("JJ_") || Name.Contains("CROUCH") || Name.Contains("GETUP") ? "Movement & aiming" :
        Name.Contains("WEP") || Name.Contains("WEAPON") || Name.Contains("TRIGGER") || Name.Contains("FIRE") || Name.Contains("ALPHA") ? "Weapons" : "Systems & commands";
}
public enum ControlComboInputKind { Key, Mouse }

public sealed record ControlComboInput(
    [property: JsonRequired] ControlComboInputKind Kind,
    [property: JsonRequired] int Code);

public sealed class ControlCombo
{
    public List<ControlComboInput> Inputs { get; set; } = [];
    public bool Suppress { get; set; } = true;
}

public sealed class ControlBinding
{
    public int Primary { get; set; }
    public int Secondary { get; set; }
    public int Mouse { get; set; }
    public int Joystick { get; set; } // Preserved; editing controllers is a later feature.
    public List<ControlCombo>? Combos { get; set; }
}
public sealed class ControlProfile
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "My controls";
    public string Description { get; set; } = "";
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Mw2JumpJets { get; set; }
    public Dictionary<string, ControlBinding> Bindings { get; set; } = new();
}
public sealed class ControlDocument
{
    public int Version { get; set; } = 1;
    public string GameId { get; set; } = GameCatalog.Mw3;
    public string? ActiveId { get; set; }
    public List<ControlProfile> Profiles { get; set; } = new();
}

/// <summary>MW3 command metadata, declarative default bindings and authored profiles.</summary>
public sealed class ControlProfiles
{
    public static IReadOnlyList<ControlAction> Actions { get; } = LoadActions();
    private const int ProfileSizeLimit = 1024 * 1024;
    private const int MaxCombosPerAction = 8;
    private const int MaxCombosPerProfile = 64;
    private static readonly JsonSerializerOptions Json = CreateJsonOptions();

    private static JsonSerializerOptions CreateJsonOptions()
    {
        var resolver = new DefaultJsonTypeInfoResolver();
        resolver.Modifiers.Add(type =>
        {
            if (type.Type != typeof(ControlBinding)) return;
            var combos = type.Properties.Single(property => property.Name == nameof(ControlBinding.Combos));
            combos.ShouldSerialize = (_, value) => value is List<ControlCombo> { Count: > 0 };
        });
        var options = new JsonSerializerOptions { WriteIndented = true, TypeInfoResolver = resolver };
        options.Converters.Add(new JsonStringEnumConverter<ControlComboInputKind>(allowIntegerValues: false));
        return options;
    }
    private const string RegistryKey = @"hkcu\software\microprose\mechwarrior 3\1.0";
    private readonly string directory;
    private string Store => Path.Combine(directory, "profiles.json");
    private string StatePath => Path.Combine(directory, "restore.json");
    public ControlProfiles(string dataRoot, string gameId = GameCatalog.Mw3)
    {
        if (GameCatalog.Get(gameId).Id != GameCatalog.Mw3) throw new NotSupportedException("Controls for this game are not available yet.");
        directory = Path.GetFullPath(Path.Combine(dataRoot, "controls", gameId));
    }
    private static IReadOnlyList<ControlAction> LoadActions()
    {
        using var stream = typeof(ControlProfiles).Assembly.GetManifestResourceStream("MW3RemasterLauncher.Core.Mw3ControlActions.json")!;
        return JsonSerializer.Deserialize<List<ControlAction>>(stream)!.AsReadOnly();
    }
    private static string ReadBounded(string path, int limit = 256 * 1024)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > limit) throw new InvalidDataException("Controls file is too large: " + path);
        return File.ReadAllText(path);
    }
    private static T Read<T>(string path, int limit = 256 * 1024) =>
        JsonSerializer.Deserialize<T>(ReadBounded(path, limit), Json)
        ?? throw new InvalidDataException("Controls file is empty: " + path);
    public ControlDocument Load()
    {
        var doc = ReadLaunchDocument();
        var changed = MigrateLegacyMw5(doc);
        // Seed optional layouts without replacing edits or changing the active selection.
        foreach (var preset in new[] { ControlPresets.Mw5(), Mw3DefaultControls.Create() })
        {
            if (doc.Profiles.Count >= 24 || doc.Profiles.Any(profile => profile.Id == preset.Id)) continue;
            doc.Profiles.Add(preset);
            if (WithinSizeLimit(doc)) changed = true;
            else doc.Profiles.RemoveAt(doc.Profiles.Count - 1);
        }
        if (changed) Save(doc);
        return doc;
    }

    /// <summary>Read and migrate the selected layout in memory without writing user controls.</summary>
    public ControlDocument LoadForLaunch()
    {
        var doc = ReadLaunchDocument();
        MigrateLegacyMw5(doc);
        return doc;
    }

    private ControlDocument ReadLaunchDocument()
    {
        var doc = File.Exists(Store) ? Read<ControlDocument>(Store, ProfileSizeLimit) : new ControlDocument();
        Validate(doc);
        return doc;
    }

    private static bool MigrateLegacyMw5(ControlDocument doc)
    {
        var index = doc.Profiles.FindIndex(profile => profile.Id == ControlPresets.Mw5Id);
        if (index < 0 || !ControlPresets.IsUnmodifiedLegacyMw5(doc.Profiles[index])) return false;
        var previous = doc.Profiles[index];
        doc.Profiles[index] = ControlPresets.Mw5();
        if (WithinSizeLimit(doc)) return true;
        doc.Profiles[index] = previous;
        return false;
    }

    private static bool WithinSizeLimit(ControlDocument doc) =>
        Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(doc, Json)) <= ProfileSizeLimit;

    public void Save(ControlDocument doc)
    {
        Validate(doc);
        var text = JsonSerializer.Serialize(doc, Json);
        if (Encoding.UTF8.GetByteCount(text) > ProfileSizeLimit)
            throw new InvalidDataException("The layout library is full. Keep fewer saved layouts.");
        AtomicWrite(Store, text);
    }

    public static void Validate(ControlDocument doc)
    {
        if (doc.Version != 1 || doc.GameId != GameCatalog.Mw3 || doc.Profiles == null || doc.Profiles.Count > 24)
            throw new InvalidDataException("Unsupported controls profile document.");
        if (doc.Profiles.Any(p => p == null) || doc.Profiles.Select(p => p.Id).Distinct().Count() != doc.Profiles.Count)
            throw new InvalidDataException("Duplicate controls profile identity.");
        foreach (var p in doc.Profiles)
        {
            if (!Guid.TryParseExact(p.Id, "N", out _) || string.IsNullOrWhiteSpace(p.Name) || p.Name.Length > 64 || p.Name.Any(char.IsControl) ||
                p.Description == null || p.Description.Length > 2048 ||
                p.Bindings == null || p.Bindings.Count != Actions.Count || Actions.Any(a => !p.Bindings.ContainsKey(a.Name)))
                throw new InvalidDataException("Invalid or incomplete controls profile.");
            var extendedMouse = new HashSet<int>();
            var combos = new HashSet<string>(StringComparer.Ordinal);
            foreach (var binding in p.Bindings.Values)
            {
                if (binding == null || binding.Primary is < 0 or > 0x7ff || binding.Secondary is < 0 or > 0x7ff ||
                    binding.Mouse is < 0 or > 7 || binding.Joystick is < 0 or > 15 ||
                    (binding.Primary != 0 && (binding.Primary & 255) == 0) ||
                    (binding.Secondary != 0 && (binding.Secondary & 255) == 0))
                    throw new InvalidDataException("Invalid control binding.");
                // Retail command maps can contain shared Mouse 1–3 assignments.
                if (binding.Mouse > 3 && !extendedMouse.Add(binding.Mouse))
                    throw new InvalidDataException("An extended mouse input is assigned to more than one action.");
                if (binding.Combos is not { Count: > 0 } actionCombos) continue;
                if (actionCombos.Count > MaxCombosPerAction || combos.Count + actionCombos.Count > MaxCombosPerProfile)
                    throw new InvalidDataException("A controls layout may have up to eight combos per action and 64 total.");
                foreach (var combo in actionCombos)
                {
                    ValidateCombo(combo);
                    if (!combos.Add(CanonicalCombo(combo)))
                        throw new InvalidDataException("A controls layout cannot contain duplicate combos.");
                }
            }
        }
        if (doc.ActiveId != null && !doc.Profiles.Any(p => p.Id == doc.ActiveId))
            throw new InvalidDataException("The selected controls profile is missing.");
    }

    public static void ValidateCombo(ControlCombo combo)
    {
        if (combo?.Inputs == null || combo.Inputs.Count is < 2 or > 3 ||
            combo.Inputs.Any(input => input == null || !IsPhysicalInput(input)) ||
            combo.Inputs.Distinct().Count() != combo.Inputs.Count)
            throw new InvalidDataException("A combo must contain two or three distinct supported physical inputs.");
        if (combo.Inputs.Count(input => input.Kind == ControlComboInputKind.Mouse && input.Code is 6 or 7) == 2)
            throw new InvalidDataException("A combo cannot contain both wheel directions.");
    }

    private static bool IsPhysicalInput(ControlComboInput input) => input.Kind switch
    {
        ControlComboInputKind.Key => input.Code is >= 1 and <= 0xff && !ControlKeys.IsReservedScan(input.Code),
        ControlComboInputKind.Mouse => input.Code is >= 1 and <= 7,
        _ => false
    };

    internal static IEnumerable<ControlComboInput> OrderedInputs(ControlCombo combo) =>
        combo.Inputs.OrderBy(input => input.Kind).ThenBy(input => input.Code);

    public static string CanonicalCombo(ControlCombo combo) =>
        string.Join(' ', OrderedInputs(combo).Select(input => input.Kind == ControlComboInputKind.Key
            ? FormattableString.Invariant($"K:0x{input.Code:x2}")
            : FormattableString.Invariant($"M:{input.Code}")));

    public static bool UsesExtendedInputBindings(ControlProfile profile) =>
        profile.Bindings.Values.Any(binding => binding.Mouse > 3 || binding.Combos is { Count: > 0 });

    public static ControlProfile Clone(ControlProfile source, string name) => new()
    {
        Name = name,
        Description = source.Description,
        Mw2JumpJets = source.Mw2JumpJets,
        Bindings = source.Bindings.ToDictionary(pair => pair.Key, pair => new ControlBinding
        {
            Primary = pair.Value.Primary,
            Secondary = pair.Value.Secondary,
            Mouse = pair.Value.Mouse,
            Joystick = pair.Value.Joystick,
            Combos = pair.Value.Combos?.Select(combo => new ControlCombo
            {
                Suppress = combo.Suppress,
                Inputs = combo.Inputs.Select(input => input with { }).ToList()
            }).ToList()
        })
    };

    public static IReadOnlyList<string> Conflicts(ControlProfile profile)
    {
        var bindings = Actions.SelectMany(action => ConflictInputs(profile.Bindings[action.Name])
            .Select(input => (input.Identity, input.Label, Action: action.Label)));
        return bindings.GroupBy(binding => binding.Identity, StringComparer.Ordinal)
            .Where(group => group.Count() > 1)
            .Select(group => $"{group.First().Label}: " + string.Join(", ", group.Select(binding => binding.Action)))
            .ToArray();
    }

    private static IEnumerable<(string Identity, string Label)> ConflictInputs(ControlBinding binding)
    {
        foreach (var key in new[] { binding.Primary, binding.Secondary }.Where(key => key != 0).Distinct())
            yield return ($"key:{key}", ControlKeys.Label(key));
        if (binding.Mouse > 0)
            yield return ($"mouse:{binding.Mouse}", ControlKeys.MouseLabel(binding.Mouse));
        foreach (var combo in binding.Combos ?? [])
            yield return ("combo:" + CanonicalCombo(combo), string.Join(" + ", OrderedInputs(combo).Select(input =>
                input.Kind == ControlComboInputKind.Key ? ControlKeys.Label(input.Code) : ControlKeys.MouseLabel(input.Code))));
    }

    private static bool IsControlRow(string row)
    {
        var f = row.Split('\t');
        return f.Length == 4 && f[0].Equals("V " + RegistryKey, StringComparison.OrdinalIgnoreCase) &&
            (f[1].Equals("defaultcmdmap", StringComparison.OrdinalIgnoreCase) || f[1].Equals("activectlcfg", StringComparison.OrdinalIgnoreCase));
    }
    private static string[] ControlRows(string text) => text.Split('\n').Select(x => x.TrimEnd('\r')).Where(IsControlRow).ToArray();
    public static ControlProfile ImportRegistry(string text, string name = "My controls")
    {
        var maps = ControlRows(text).Where(r => r.Split('\t')[1].Equals("defaultcmdmap", StringComparison.OrdinalIgnoreCase)).ToArray();
        if (maps.Length != 1) throw new InvalidDataException("No saved MW3 bindings were found. Start the game once, then quit normally before copying your controls.");
        var f = maps[0].Split('\t');
        var bytes = Convert.FromHexString(f[3]);
        if (f[2] != "3" || bytes.Length != 167 * 4) throw new InvalidDataException("Unrecognized MW3 command map; existing controls were preserved.");
        var p = new ControlProfile { Name = name };
        foreach (var a in Actions)
        {
            var word = BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(a.Command * 4, 4));
            p.Bindings.Add(a.Name, new() { Primary = (int)(word & 0x7ff), Secondary = (int)((word >> 11) & 0x7ff),
                Joystick = (int)((word >> 22) & 15), Mouse = (int)((word >> 26) & 3) });
        }
        Validate(new() { Profiles = new() { p } }); return p;
    }
    public ControlProfile ImportCurrent(IEnumerable<string> candidates)
    {
        foreach (var path in candidates.Where(p => !string.IsNullOrWhiteSpace(p)).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            if (!File.Exists(path)) continue;
            var text = ReadBounded(path, 8 * 1024 * 1024);
            if (ControlRows(text).Any(r => r.Split('\t')[1].Equals("defaultcmdmap", StringComparison.OrdinalIgnoreCase))) return ImportRegistry(text);
        }
        throw new InvalidDataException("Start MW3 once and quit normally so its current bindings can be copied. Your existing controls have not been changed.");
    }
    public ControlProfile ImportOriginal(IEnumerable<string> candidates)
    {
        if (File.Exists(StatePath))
        {
            var state = ReadState();
            if (state.Applied) return ImportRegistry(string.Join('\n', state.OriginalRows));
        }
        return ImportCurrent(candidates);
    }
    public static string Preset(ControlProfile p, string? originalPreset = null)
    {
        Validate(new() { Profiles = new() { p } });
        var s = new StringBuilder("KEYS (\n");
        foreach (var a in Actions)
        {
            var b = p.Bindings[a.Name];
            // Emit zero fields too: clearing a key must not retain a prior game's binding.
            var legacyMouse = b.Mouse <= 3 ? b.Mouse : 0;
            s.AppendLine($"  ({a.Name} keya(0x{b.Primary:x}) keyb(0x{b.Secondary:x}) joybtn(0x{b.Joystick:x}) mousebtn(0x{legacyMouse:x}))");
        }
        var keys = s.Append(")").ToString();
        if (originalPreset == null) return "(\n" + keys + "\n)\n";
        // Preserve the user's AXES and any other original configuration sections.
        // Only the KEYS section is replaced; unsupported/binary templates fail visibly.
        if (originalPreset.Contains('\ufffd') || originalPreset.Any(c => char.IsControl(c) && c is not ('\r' or '\n' or '\t')))
            throw new InvalidDataException("The original controls preset is not a supported text preset. Keep the game's own controls selected.");
        var tokens = System.Text.RegularExpressions.Regex.Matches(originalPreset,
            @"//[^\r\n]*|;[^\r\n]*|#[^\r\n]*|""(?:\\.|[^""\\])*""|[A-Za-z_][A-Za-z_0-9]*|[()]",
            System.Text.RegularExpressions.RegexOptions.CultureInvariant, TimeSpan.FromSeconds(1))
            .Cast<System.Text.RegularExpressions.Match>().Where(t => !t.Value.StartsWith("//") && !t.Value.StartsWith(';') && !t.Value.StartsWith('#') && !t.Value.StartsWith('"')).ToArray();
        var starts = tokens.Select((t, i) => (t, i)).Where(x => x.t.Value.Equals("KEYS", StringComparison.OrdinalIgnoreCase)).ToArray();
        if (starts.Length != 1 || starts[0].i + 1 >= tokens.Length || tokens[starts[0].i + 1].Value != "(")
            throw new InvalidDataException("The original preset's KEYS section could not be safely replaced.");
        int depth = 0;
        for (var n = starts[0].i + 1; n < tokens.Length; n++)
        {
            if (tokens[n].Value == "(") depth++;
            if (tokens[n].Value == ")" && --depth == 0)
                return originalPreset[..starts[0].t.Index] + keys + originalPreset[(tokens[n].Index + tokens[n].Length)..];
        }
        throw new InvalidDataException("The original controls preset is incomplete.");
    }
    private static string? OriginalPreset(string[] rows, string gameDirectory)
    {
        var active = rows.FirstOrDefault(r => r.Split('\t')[1].Equals("activectlcfg", StringComparison.OrdinalIgnoreCase));
        if (active == null) return null;
        var data = Convert.FromHexString(active.Split('\t')[3]);
        var end = Array.IndexOf(data, (byte)0); if (end < 0) end = data.Length;
        var name = Encoding.Latin1.GetString(data, 0, end);
        if (name.Length == 0 || name.Equals("DefaultCtlConfig", StringComparison.OrdinalIgnoreCase)) return null;
        var path = Path.GetFullPath(name, gameDirectory);
        if (!File.Exists(path)) throw new InvalidDataException("The original controls preset is missing: " + name + ". Restore it before applying a launcher layout.");
        return ReadBounded(path, 512 * 1024);
    }
    private sealed class RestoreState
    {
        public int Version { get; set; } = 1;
        public bool Applied { get; set; }
        public string[] OriginalRows { get; set; } = Array.Empty<string>();
    }
    private RestoreState ReadState()
    {
        var s = Read<RestoreState>(StatePath);
        if (s.Version != 1 || s.OriginalRows == null || s.OriginalRows.Length > 2 || s.OriginalRows.Any(r => !IsControlRow(r)) ||
            s.OriginalRows.Select(r => r.Split('\t')[1].ToLowerInvariant()).Distinct().Count() != s.OriginalRows.Length)
            throw new InvalidDataException("The original-controls backup is invalid. Restore it before applying another layout.");
        ImportRegistry(string.Join('\n', s.OriginalRows)); return s;
    }
    private static string ReplaceControls(string text, IEnumerable<string> rows) =>
        string.Join('\n', text.Split('\n').Select(r => r.TrimEnd('\r')).Where(r => !IsControlRow(r) && r.Length > 0).Concat(rows)) + "\n";
    public void PrepareLaunch(JsonObject profile, string dataRoot, string gameDirectory)
    {
        var doc = LoadForLaunch();
        var selected = doc.Profiles.SingleOrDefault(p => p.Id == doc.ActiveId);
        if (selected != null && UsesExtendedInputBindings(selected))
            throw new InvalidDataException("Extended mouse and combo controls require MW3-RE. Choose a compatible layout for D7VK.");
        if (selected == null && !File.Exists(StatePath)) return; // Existing installations are untouched by default.
        var state = File.Exists(StatePath) ? ReadState() : new RestoreState();
        if (selected == null && !state.Applied) return;
        // Bind a per-user copy in development too. Never modify the published registry seed.
        var registry = PlayerRegistry.Bind(profile, dataRoot);
        var text = ReadBounded(registry, 8 * 1024 * 1024);
        if (selected == null)
        {
            AtomicWrite(registry, ReplaceControls(text, state.OriginalRows));
            state.Applied = false; AtomicWrite(StatePath, JsonSerializer.Serialize(state, Json)); return;
        }
        ImportRegistry(text); // Reject unknown/missing formats before touching game settings.
        var content = Preset(selected, OriginalPreset(state.Applied ? state.OriginalRows : ControlRows(text), gameDirectory));
        var hash = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(content)))[..20];
        var relative = @"keys\CC-" + hash + ".zrd";
        var target = Path.Combine(gameDirectory, relative);
        AtomicWrite(target, content);
        if (!state.Applied)
        {
            state.OriginalRows = ControlRows(text);
            state.Applied = true;
            // Persist recovery information before changing the active configuration.
            AtomicWrite(StatePath, JsonSerializer.Serialize(state, Json));
        }
        var active = Convert.ToHexString(Encoding.ASCII.GetBytes(relative + '\0').Concat(new byte[260 - relative.Length - 1]).ToArray()).ToLowerInvariant();
        var rows = ControlRows(text).Where(r => !r.Split('\t')[1].Equals("activectlcfg", StringComparison.OrdinalIgnoreCase))
            .Append("V " + RegistryKey + "\tactivectlcfg\t3\t" + active);
        AtomicWrite(registry, ReplaceControls(text, rows));
    }
    internal static void AtomicWrite(string path, string text)
    {
        PackStorage.EnsureNoLinks(path);
        PackStorage.EnsureNoLinks(path + ".previous");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temporary = path + ".writing-" + Guid.NewGuid().ToString("N");
        try
        {
            using (var f = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                var bytes = new UTF8Encoding(false).GetBytes(text); f.Write(bytes); f.Flush(true);
            }
            if (File.Exists(path)) File.Replace(temporary, path, path + ".previous"); else File.Move(temporary, path);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
}
