using System.IO;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>Import structure for visual alternatives retaining an owned legacy controller.</summary>
public static class OwnedChassisVisuals
{
    public const string Capability = "owned-chassis-visuals";

    public static void Read(JsonElement value, Func<string, string?, string> verify)
    {
        try { ReadCore(value, verify); }
        catch (EndOfStreamException error) { throw new InvalidDataException("Truncated owned visual resource.", error); }
    }

    private static void ReadCore(JsonElement value, Func<string, string?, string> verify)
    {
        if (value.ValueKind != JsonValueKind.Object ||
            !new HashSet<string>(new[] { "schema_version", "meshes", "textures" })
                .SetEquals(value.EnumerateObject().Select(p => p.Name).Where(name => name != "normals")) ||
            value.GetProperty("schema_version").ValueKind != JsonValueKind.Number ||
            !value.GetProperty("schema_version").TryGetInt32(out var version) || version != 1)
            throw new InvalidDataException("Invalid owned visual alternative.");
        var batchCounts = new Dictionary<string, uint>();
        var colors = new HashSet<ChassisAppearances.ColorKey>();
        foreach (var role in new[] { "meshes", "textures" })
        {
            var table = value.GetProperty(role);
            if (table.ValueKind != JsonValueKind.Object ||
                !new HashSet<string>(new[] { "close", "distance" })
                    .SetEquals(table.EnumerateObject().Select(p => p.Name)))
                throw new InvalidDataException("Owned visuals require both LODs.");
            foreach (var lod in table.EnumerateObject())
            {
                if (lod.Value.ValueKind != JsonValueKind.String)
                    throw new InvalidDataException("Invalid owned visual path.");
                var format = role == "meshes" ? "BWMESH4" : "BWTEX1";
                var path = verify(lod.Value.GetString() ?? "", format);
                if (new FileInfo(path).Length is < 16 or > 256 * 1024 * 1024)
                    throw new InvalidDataException("Invalid owned visual resource size.");
                using var reader = new BinaryReader(File.OpenRead(path));
                var expected = System.Text.Encoding.ASCII.GetBytes(format.PadRight(8, '\0'));
                if (!reader.ReadBytes(8).SequenceEqual(expected))
                    throw new InvalidDataException("Mislabeled owned visual resource.");
                if (role == "meshes")
                    batchCounts[lod.Name] = ReadMesh(reader);
                if (role == "textures")
                {
                    var batches = reader.ReadUInt32(); var count = reader.ReadUInt32();
                    if (batches is < 1 or > 256 || batches != batchCounts[lod.Name] || count is < 1 or > 64)
                        throw new InvalidDataException("Invalid owned texture counts.");
                    for (var i = 0; i < batches; ++i)
                        if (reader.ReadUInt32() >= count) throw new InvalidDataException("Invalid material binding.");
                    for (var i = 0; i < count; ++i)
                    {
                        ReadName(reader);
                        var width = reader.ReadUInt32(); var height = reader.ReadUInt32(); reader.ReadUInt64();
                        if (width is < 1 or > 4096 || height is < 1 or > 4096)
                            throw new InvalidDataException("Invalid texture dimensions.");
                        var size = checked((int)(width * height * 2)); var pixels = reader.ReadBytes(size);
                        if (pixels.Length != size) throw new InvalidDataException("Truncated owned texture.");
                        colors.Add(new(width, height, 1, ChassisAppearances.PixelHash(pixels)));
                    }
                    if (reader.BaseStream.Position != reader.BaseStream.Length)
                        throw new InvalidDataException("Trailing owned texture data.");
                }
            }
        }
        if (value.TryGetProperty("normals", out var pages))
        {
            if (pages.ValueKind != JsonValueKind.Array || pages.GetArrayLength() > 16)
                throw new InvalidDataException("Invalid owned normal page list.");
            var paths = new HashSet<string>();
            var bindings = new HashSet<ChassisAppearances.ColorKey>();
            long total = 0;
            foreach (var page in pages.EnumerateArray())
            {
                if (page.ValueKind != JsonValueKind.String || !paths.Add(page.GetString() ?? ""))
                    throw new InvalidDataException("Invalid or duplicate owned normal path.");
                var path = verify(page.GetString() ?? "", "BWSNR2");
                var size = new FileInfo(path).Length; total += size;
                if (size is < 1 or > 128 * 1024 * 1024 || total > 512L * 1024 * 1024)
                    throw new InvalidDataException("Owned normal budget exceeded.");
                try { ChassisAppearances.ReadNormals(File.ReadAllBytes(path), colors, bindings); }
                catch (EndOfStreamException error) { throw new InvalidDataException("Truncated owned normal page.", error); }
            }
        }
        // The coordinator derives suppression rosters from the pinned legacy models,
        // checks ancestry and parses the complete visual payload before preparing banks.
    }
    private static string ReadName(BinaryReader reader, bool empty = false)
    {
        var data = reader.ReadBytes(32);
        if (data.Length != 32) throw new InvalidDataException("Truncated owned name."); var end = Array.IndexOf(data, (byte)0);
        if (end < 0 || (!empty && end == 0) || data.Skip(end).Any(b => b != 0) ||
            data.Take(end).Any(b => !((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') ||
                (b >= '0' && b <= '9') || b == '_' || b == '.' || b == '-')))
            throw new InvalidDataException("Invalid owned mesh name.");
        return System.Text.Encoding.ASCII.GetString(data, 0, end);
    }
    private static uint ReadMesh(BinaryReader reader)
    {
        string Name(bool empty = false) => ReadName(reader, empty);
        void Matrix()
        {
            var values = new double[16];
            for (var i = 0; i < 16; ++i)
            {
                values[i] = reader.ReadDouble();
                if (!double.IsFinite(values[i])) throw new InvalidDataException("Nonfinite owned rest matrix.");
            }
            var determinant = values[0] * (values[5] * values[10] - values[6] * values[9])
                - values[1] * (values[4] * values[10] - values[6] * values[8])
                + values[2] * (values[4] * values[9] - values[5] * values[8]);
            if (Math.Abs(determinant) < 1e-12)
                throw new InvalidDataException("Singular owned rest matrix.");
            if (values[12] != 0 || values[13] != 0 || values[14] != 0 || values[15] != 1)
                throw new InvalidDataException("Nonaffine owned rest matrix.");
        }
        try
        {
            var batches = reader.ReadUInt32(); var bones = reader.ReadUInt32();
            var refs = reader.ReadUInt32(); var flags = reader.ReadUInt32();
            if (batches is < 1 or > 256 || bones is < 1 or > 256 || refs is < 1 or > 128 || flags > 1)
                throw new InvalidDataException("Invalid owned rig counts.");
            for (var i = 0; i < 5; ++i)
            {
                var value = reader.ReadDouble();
                if (!double.IsFinite(value) || (i == 0 && (value < 0 || value > 10)))
                    throw new InvalidDataException("Invalid owned gait metadata.");
            }
            var names = new HashSet<string>(); var controls = new HashSet<string>();
            for (var i = 0; i < bones; ++i)
            {
                if (!names.Add(Name())) throw new InvalidDataException("Duplicate owned bone.");
                var control = Name(true); if (control != "") controls.Add(control);
                var parent = reader.ReadInt32();
                if (parent < -1 || parent >= i) throw new InvalidDataException("Invalid owned bone parent.");
                Matrix();
            }
            var references = new HashSet<string>();
            for (var i = 0; i < refs; ++i)
            {
                if (!references.Add(Name())) throw new InvalidDataException("Duplicate owned reference.");
                Matrix();
            }
            if (!controls.IsSubsetOf(references)) throw new InvalidDataException("Foreign owned control.");
            if (!new HashSet<string>(new[] { "hip", "torso", "larm", "rarm", "lhand", "rhand", "lthigh", "rthigh", "lcalf", "rcalf", "lfoot", "rfoot" }).IsSubsetOf(references) ||
                !new HashSet<string>(new[] { "Pelvis", "Torso_Twist", "Upperarm_Left", "Upperarm_Right", "Forearm_Left", "Forearm_Right", "Thigh_Left", "Thigh_Right", "Calf_Left", "Calf_Right", "Foot0_Left", "Foot0_Right" }).IsSubsetOf(names))
                throw new InvalidDataException("Missing required owned retarget joint.");
            for (var batch = 0; batch < batches; ++batch)
            {
                Name(); Name(); var bone = reader.ReadUInt32(); var size = reader.ReadUInt32(); reader.ReadUInt32();
                if ((bone != uint.MaxValue && bone >= bones) || size is < 1 or > 65535 || size % 3 != 0)
                    throw new InvalidDataException("Invalid owned visual batch.");
                for (var vertex = 0; vertex < size; ++vertex)
                {
                    float normalLength = 0;
                    for (var field = 0; field < 8; ++field)
                    {
                        var value = reader.ReadSingle();
                        if (!float.IsFinite(value)) throw new InvalidDataException("Nonfinite owned vertex.");
                        if (field >= 3 && field <= 5) normalLength += value * value;
                    }
                    if (normalLength < .5f) throw new InvalidDataException("Invalid owned vertex normal.");
                }
                if (bone == uint.MaxValue)
                    for (var vertex = 0; vertex < size; ++vertex)
                        if (reader.ReadUInt32() >= bones) throw new InvalidDataException("Invalid owned vertex bone.");
            }
            if (reader.BaseStream.Position != reader.BaseStream.Length)
                throw new InvalidDataException("Trailing owned mesh data.");
            return batches;
        }
        catch (EndOfStreamException error) { throw new InvalidDataException("Truncated owned mesh.", error); }
    }

}
