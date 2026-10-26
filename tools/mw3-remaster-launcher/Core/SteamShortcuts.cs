using System.Buffers.Binary;
using System.IO;
using System.Text;

namespace MW3RemasterLauncher.Core;

/// <summary>Bounded binary KeyValues editing. Unknown supported scalar fields retain their exact bytes.</summary>
public static class SteamShortcuts
{
    public const int MaximumBytes = 16 * 1024 * 1024;
    private static readonly UTF8Encoding Utf8 = new(false, true);
    public sealed class Field(byte type, string name, byte[] value, List<Field>? children = null)
    {
        public byte Type = type;
        public string Name = name;
        public byte[] Value = value;
        public List<Field>? Children = children;
    }
    public sealed record Update(byte[] Bytes, uint AppId, bool Changed);

    public static List<Field> Parse(byte[] bytes)
    {
        if (bytes.Length > MaximumBytes) throw new InvalidDataException("Steam shortcut file is too large.");
        using var input = new MemoryStream(bytes, false);
        var count = 0;
        byte[] String()
        {
            using var output = new MemoryStream();
            int next;
            while ((next = input.ReadByte()) > 0)
            {
                if (output.Length >= 256 * 1024) throw new InvalidDataException("Steam shortcut string is too long.");
                output.WriteByte((byte)next);
            }
            if (next != 0) throw new InvalidDataException("Truncated Steam shortcut string.");
            var value = output.ToArray();
            _ = Utf8.GetString(value);
            return value;
        }
        List<Field> Object(int depth)
        {
            if (depth > 32) throw new InvalidDataException("Steam shortcuts are nested too deeply.");
            var fields = new List<Field>();
            while (true)
            {
                var type = input.ReadByte();
                if (type == 8) return fields;
                if (type < 0 || ++count > 200000) throw new InvalidDataException("Truncated or excessive Steam shortcut records.");
                var name = Utf8.GetString(String());
                if (type == 0) fields.Add(new(0, name, [], Object(depth + 1)));
                else if (type == 1) fields.Add(new(1, name, String()));
                else
                {
                    var size = type switch { 2 or 3 or 4 or 6 => 4, 7 or 10 => 8, _ =>
                        throw new InvalidDataException("Unsupported Steam shortcut field type. Existing shortcuts were kept.") };
                    var value = new byte[size];
                    try { input.ReadExactly(value); }
                    catch (EndOfStreamException error) { throw new InvalidDataException("Truncated Steam shortcut value.", error); }
                    fields.Add(new((byte)type, name, value));
                }
            }
        }
        var result = Object(0);
        if (input.Position != input.Length || result.Count != 1 || result[0].Type != 0 || result[0].Name != "shortcuts")
            throw new InvalidDataException("Invalid Steam shortcut root. Existing shortcuts were kept.");
        if (result[0].Children!.Any(f => f.Type != 0 || !uint.TryParse(f.Name, out _)))
            throw new InvalidDataException("Invalid Steam shortcut entry table.");
        return result;
    }

    public static byte[] Serialize(List<Field> fields)
    {
        using var output = new MemoryStream();
        void String(string value) { output.Write(Utf8.GetBytes(value)); output.WriteByte(0); }
        void Object(List<Field> rows)
        {
            foreach (var row in rows)
            {
                output.WriteByte(row.Type); String(row.Name);
                if (row.Type == 0) Object(row.Children!);
                else { output.Write(row.Value); if (row.Type == 1) output.WriteByte(0); }
            }
            output.WriteByte(8);
        }
        Object(fields);
        if (output.Length > MaximumBytes) throw new InvalidDataException("Updated Steam shortcut file is too large.");
        return output.ToArray();
    }

    private static Field? Find(Field entry, string name) => entry.Children!.SingleOrDefault(f => f.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
    private static string Text(Field entry, string name) => Find(entry, name) is { Type: 1 } field ? Utf8.GetString(field.Value) : "";
    private static void Set(Field entry, string name, byte type, byte[] value)
    {
        var field = Find(entry, name);
        if (field == null) entry.Children!.Add(new(type, name, value));
        else { field.Type = type; field.Value = value; field.Children = null; }
    }
    private static void Text(Field entry, string name, string value) => Set(entry, name, 1, Utf8.GetBytes(value));
    private static void Integer(Field entry, string name, uint value)
    {
        var bytes = new byte[4]; BinaryPrimitives.WriteUInt32LittleEndian(bytes, value); Set(entry, name, 2, bytes);
    }
    private static string Exe(Field entry)
    {
        var value = Text(entry, "Exe").Trim().Trim('"');
        try { return Path.GetFullPath(value); } catch { return ""; }
    }
    private static bool KnownName(string value) => new[] { "Core Critical Launcher", "Core Critical", "MechWarrior 3 Remastered", "MW3 Remaster", "MW3RemasterLauncher" }
        .Contains(value, StringComparer.OrdinalIgnoreCase);
    private static bool KnownExe(string value) => new[] { "Core Critical Launcher.exe", "MW3RemasterLauncher.exe" }
        .Contains(Path.GetFileName(value), StringComparer.OrdinalIgnoreCase);

    public static Update Upsert(byte[]? existing, string executable, string icon)
    {
        executable = Path.GetFullPath(executable);
        var root = existing == null ? new List<Field> { new(0, "shortcuts", [], new()) } : Parse(existing);
        var rows = root[0].Children!;
        bool Owned(Field row)
        {
            var target = Exe(row);
            return target.Equals(executable, StringComparison.OrdinalIgnoreCase) ||
                (KnownName(Text(row, "AppName")) && KnownExe(target) &&
                 (string.Equals(Path.GetDirectoryName(target), Path.GetDirectoryName(executable), StringComparison.OrdinalIgnoreCase) || !File.Exists(target)));
        }
        var matches = rows.Where(Owned).ToArray();
        var entry = matches.FirstOrDefault(r => Exe(r).Equals(executable, StringComparison.OrdinalIgnoreCase)) ?? matches.FirstOrDefault();
        var added = entry == null;
        entry ??= new(0, "", [], new());
        foreach (var duplicate in matches.Where(r => r != entry)) rows.Remove(duplicate);
        var name = !added && !string.IsNullOrWhiteSpace(Text(entry, "AppName")) && !KnownName(Text(entry, "AppName"))
            ? Text(entry, "AppName") : "Core Critical Launcher";
        var appId = Find(entry, "appid") is { Type: 2 } id ? BinaryPrimitives.ReadUInt32LittleEndian(id.Value) : 0;
        if ((appId & 0x80000000) == 0) appId = SteamHelper.CalculateShortcutAppId('"' + executable + '"', name);
        if (rows.Any(r => r != entry && Find(r, "appid") is { Type: 2 } other && BinaryPrimitives.ReadUInt32LittleEndian(other.Value) == appId))
            throw new InvalidDataException("Steam shortcut ID conflicts with another game. Existing shortcuts were kept.");
        Text(entry, "AppName", name); Text(entry, "Exe", '"' + executable + '"');
        Text(entry, "StartDir", '"' + Path.GetDirectoryName(executable)! + '"'); Text(entry, "icon", icon);
        Integer(entry, "appid", appId);
        if (added)
        {
            Text(entry, "ShortcutPath", ""); Text(entry, "LaunchOptions", "");
            foreach (var field in new[] { "IsHidden", "OpenVR", "Devkit", "DevkitOverrideAppID", "LastPlayTime" }) Integer(entry, field, 0);
            Integer(entry, "AllowDesktopConfig", 1); Integer(entry, "AllowOverlay", 1); Text(entry, "DevkitGameID", "");
            entry.Children!.Add(new(0, "tags", [], new() { new(1, "0", Utf8.GetBytes("MechWarrior")) }));
            rows.Add(entry);
        }
        // Old builds wrote every appended entry as "0". Reindex the table without changing other entries' fields.
        for (var index = 0; index < rows.Count; index++) rows[index].Name = index.ToString(System.Globalization.CultureInfo.InvariantCulture);
        var bytes = Serialize(root);
        _ = Parse(bytes);
        return new(bytes, appId, existing == null || !bytes.SequenceEqual(existing));
    }
}
