using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Mesh-bound presentation anchors, independent of gameplay sockets.</summary>
internal static class WeaponVisualAttachments
{
    internal sealed class Mesh
    {
        internal readonly Dictionary<string, string> Controls = [];
        internal readonly Dictionary<string, (float[] Low, float[] High)> Bounds = [];
        internal ulong Identity;
    }

    private static void Fields(JsonElement value, params string[] names)
    {
        if (value.ValueKind != JsonValueKind.Object ||
            !names.ToHashSet().SetEquals(value.EnumerateObject().Select(p => p.Name)))
            throw new InvalidDataException("Invalid weapon visual fields.");
    }

    internal static void Read(JsonElement value, Dictionary<string, Mesh> meshes)
    {
        Fields(value, "schema_version", "close", "distance");
        if (value.GetProperty("schema_version").ValueKind != JsonValueKind.Number ||
            !value.GetProperty("schema_version").TryGetInt32(out var version) || version != 1)
            throw new InvalidDataException("Unsupported weapon visual schema.");
        List<(string, string)>? previous = null;
        foreach (var lod in new[] { "close", "distance" })
        {
            var table = value.GetProperty(lod);
            Fields(table, "mesh_identity", "records");
            var hash = table.GetProperty("mesh_identity");
            if (hash.ValueKind != JsonValueKind.String ||
                !Regex.IsMatch(hash.GetString()!, "\\A[0-9a-f]{16}\\z") ||
                !ulong.TryParse(hash.GetString(), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var identity) ||
                identity != meshes[lod].Identity)
                throw new InvalidDataException("Weapon visual mesh identity mismatch.");
            var records = table.GetProperty("records");
            if (records.ValueKind != JsonValueKind.Array || records.GetArrayLength() is < 1 or > 64)
                throw new InvalidDataException("Invalid weapon visual count.");
            var keys = new List<(string, string)>();
            foreach (var row in records.EnumerateArray())
            {
                Fields(row, "source_control", "weapon", "bone", "position");
                string Name(string field)
                {
                    var name = row.GetProperty(field);
                    if (name.ValueKind != JsonValueKind.String ||
                        !Regex.IsMatch(name.GetString()!, "\\A[A-Za-z0-9_.-]{1,31}\\z"))
                        throw new InvalidDataException("Invalid weapon visual name.");
                    return name.GetString()!;
                }
                var control = Name("source_control"); var weapon = Name("weapon"); var bone = Name("bone");
                if ((control != "lhand" && control != "rhand") ||
                    bone != (control == "lhand" ? "Forearm_Left" : "Forearm_Right") ||
                    !meshes[lod].Controls.TryGetValue(bone, out var bound) || bound != control ||
                    !meshes[lod].Bounds.TryGetValue(bone, out var bounds) || keys.Contains((control, weapon)))
                    throw new InvalidDataException("Invalid or ambiguous weapon visual binding.");
                keys.Add((control, weapon));
                var position = row.GetProperty("position");
                if (position.ValueKind != JsonValueKind.Array || position.GetArrayLength() != 3)
                    throw new InvalidDataException("Invalid weapon visual position.");
                for (var axis = 0; axis < 3; ++axis)
                {
                    if (position[axis].ValueKind != JsonValueKind.Number ||
                        !position[axis].TryGetDouble(out var coordinate) || !double.IsFinite(coordinate) ||
                        coordinate < bounds.Low[axis] - .1 || coordinate > bounds.High[axis] + .1)
                        throw new InvalidDataException("Weapon visual muzzle outside rigid donor geometry.");
                }
            }
            if (previous != null && !previous.SequenceEqual(keys))
                throw new InvalidDataException("Weapon visual LOD keys mismatch.");
            previous = keys;
        }
    }
}
