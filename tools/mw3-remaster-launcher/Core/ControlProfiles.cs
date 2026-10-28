using System.Buffers.Binary;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

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
public sealed class ControlBinding
{
    public int Primary { get; set; }
    public int Secondary { get; set; }
    public int Mouse { get; set; }
    public int Joystick { get; set; } // Preserved; editing controllers is a later feature.
}
public sealed class ControlProfile
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "My controls";
    public string Description { get; set; } = "";
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
    private static readonly JsonSerializerOptions Json = new() { WriteIndented = true };
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
    private static T Read<T>(string path) => JsonSerializer.Deserialize<T>(ReadBounded(path))
        ?? throw new InvalidDataException("Controls file is empty: " + path);
    public ControlDocument Load()
    {
        var doc = File.Exists(Store) ? Read<ControlDocument>(Store) : new();
        Validate(doc);
        // Seed optional layouts, never replacing edits or the active selection.
        bool added = false;
        foreach (var preset in new[] { ControlPresets.Mw5(), Mw3DefaultControls.Create() })
        {
            var existing = doc.Profiles.FindIndex(p => p.Id == preset.Id);
            if (existing >= 0)
            {
                // Repair only the exact old factory layout. Renamed, rebound or
                // deliberately cleared user layouts retain every customization.
                var previous = doc.Profiles[existing];
                if (preset.Id == ControlPresets.Mw5Id && ControlPresets.IsUnmodifiedLegacyMw5(previous))
                {
                    doc.Profiles[existing] = preset;
                    if (Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(doc, Json)) <= 256 * 1024) added = true;
                    else doc.Profiles[existing] = previous;
                }
                continue;
            }
            if (doc.Profiles.Count >= 24) continue;
            doc.Profiles.Add(preset);
            if (Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(doc, Json)) <= 256 * 1024) added = true;
            else doc.Profiles.RemoveAt(doc.Profiles.Count - 1);
        }
        if (added) Save(doc);
        return doc;
    }
    public void Save(ControlDocument doc)
    {
        Validate(doc);
        var text = JsonSerializer.Serialize(doc, Json);
        if (Encoding.UTF8.GetByteCount(text) > 256 * 1024) throw new InvalidDataException("The layout library is full. Keep fewer saved layouts.");
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
            foreach (var b in p.Bindings.Values)
                if (b == null || b.Primary is < 0 or > 0x7ff || b.Secondary is < 0 or > 0x7ff ||
                    b.Mouse is < 0 or > 3 || b.Joystick is < 0 or > 15 ||
                    (b.Primary != 0 && (b.Primary & 255) == 0) || (b.Secondary != 0 && (b.Secondary & 255) == 0))
                    throw new InvalidDataException("Invalid control binding.");
        }
        if (doc.ActiveId != null && !doc.Profiles.Any(p => p.Id == doc.ActiveId)) throw new InvalidDataException("The selected controls profile is missing.");
    }
    public static ControlProfile Clone(ControlProfile source, string name) => new()
    {
        Name = name, Description = source.Description, Bindings = source.Bindings.ToDictionary(p => p.Key, p => new ControlBinding {
            Primary = p.Value.Primary, Secondary = p.Value.Secondary, Mouse = p.Value.Mouse, Joystick = p.Value.Joystick })
    };
    public static IReadOnlyList<string> Conflicts(ControlProfile p)
    {
        return p.Bindings.SelectMany(b => new[] { b.Value.Primary, b.Value.Secondary }.Where(k => k != 0).Distinct()
            .Select(k => (Key: k, Action: b.Key))).GroupBy(x => x.Key).Where(g => g.Count() > 1)
            .Select(g => $"{ControlKeys.Label(g.Key)}: " + string.Join(", ", g.Select(x => Actions.First(a => a.Name == x.Action).Label))).ToArray();
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
            s.AppendLine($"  ({a.Name} keya(0x{b.Primary:x}) keyb(0x{b.Secondary:x}) joybtn(0x{b.Joystick:x}) mousebtn(0x{b.Mouse:x}))");
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
        var doc = Load();
        if (doc.ActiveId == null && !File.Exists(StatePath)) return; // Existing installations are untouched by default.
        var state = File.Exists(StatePath) ? ReadState() : new RestoreState();
        if (doc.ActiveId == null && !state.Applied) return;
        // Bind a per-user copy in development too. Never modify the published registry seed.
        var registry = PlayerRegistry.Bind(profile, dataRoot);
        var text = ReadBounded(registry, 8 * 1024 * 1024);
        if (doc.ActiveId == null)
        {
            AtomicWrite(registry, ReplaceControls(text, state.OriginalRows));
            state.Applied = false; AtomicWrite(StatePath, JsonSerializer.Serialize(state, Json)); return;
        }
        var selected = doc.Profiles.Single(p => p.Id == doc.ActiveId);
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
