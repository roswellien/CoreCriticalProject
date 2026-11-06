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
                .SetEquals(value.EnumerateObject().Select(p => p.Name).Where(name => name != "normals" && name != "emission")) ||
            value.GetProperty("schema_version").ValueKind != JsonValueKind.Number ||
            !value.GetProperty("schema_version").TryGetInt32(out var version) || version != 1)
            throw new InvalidDataException("Invalid owned visual alternative.");
        var batchCounts = new Dictionary<string, uint>();
        var emissionMeshes = new Dictionary<string, OwnedEmission.Mesh>();
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
                {
                    var mesh = new OwnedEmission.Mesh();
                    batchCounts[lod.Name] = ReadMesh(reader, mesh);
                    emissionMeshes[lod.Name] = mesh;
                }
                if (role == "textures")
                {
                    var batches = reader.ReadUInt32(); var count = reader.ReadUInt32();
                    if (batches is < 1 or > 256 || batches != batchCounts[lod.Name] || count is < 1 or > 64)
                        throw new InvalidDataException("Invalid owned texture counts.");
                    var indices = new uint[batches];
                    for (var i = 0; i < batches; ++i)
                    {
                        indices[i] = reader.ReadUInt32();
                        if (indices[i] >= count) throw new InvalidDataException("Invalid material binding.");
                    }
                    var materials = new List<(string Name, uint Width, uint Height, ulong Hash)>();
                    for (var i = 0; i < count; ++i)
                    {
                        var material = ReadName(reader);
                        var width = reader.ReadUInt32(); var height = reader.ReadUInt32(); reader.ReadUInt64();
                        if (width is < 1 or > 4096 || height is < 1 or > 4096)
                            throw new InvalidDataException("Invalid texture dimensions.");
                        var size = checked((int)(width * height * 2)); var pixels = reader.ReadBytes(size);
                        if (pixels.Length != size) throw new InvalidDataException("Truncated owned texture.");
                        var identity = ChassisAppearances.PixelHash(pixels);
                        colors.Add(new(width, height, 1, identity));
                        materials.Add((material, width, height, identity));
                    }
                    if (reader.BaseStream.Position != reader.BaseStream.Length)
                        throw new InvalidDataException("Trailing owned texture data.");
                    for (var i = 0; i < batches; ++i)
                    {
                        var binding = emissionMeshes[lod.Name].Batches[i];
                        var material = materials[(int)indices[i]];
                        binding.Material = material.Name; binding.Width = material.Width;
                        binding.Height = material.Height; binding.ColorHash = material.Hash;
                    }
                }
            }
        }
        if (value.TryGetProperty("emission", out var emission))
        {
            if (emission.ValueKind != JsonValueKind.Object ||
                !new HashSet<string>(new[] { "close", "distance" }).SetEquals(emission.EnumerateObject().Select(p => p.Name)))
                throw new InvalidDataException("Owned emission requires both LODs.");
            foreach (var lod in emission.EnumerateObject())
            {
                if (lod.Value.ValueKind != JsonValueKind.String || string.IsNullOrEmpty(lod.Value.GetString()))
                    throw new InvalidDataException("Invalid owned emission path.");
                OwnedEmission.Read(verify(lod.Value.GetString()!, OwnedEmission.Format), emissionMeshes[lod.Name]);
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
    internal static string ReadName(BinaryReader reader, bool empty = false)
    {
        var data = reader.ReadBytes(32);
        if (data.Length != 32) throw new InvalidDataException("Truncated owned name."); var end = Array.IndexOf(data, (byte)0);
        if (end < 0 || (!empty && end == 0) || data.Skip(end).Any(b => b != 0) ||
            data.Take(end).Any(b => !((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') ||
                (b >= '0' && b <= '9') || b == '_' || b == '.' || b == '-')))
            throw new InvalidDataException("Invalid owned mesh name.");
        return System.Text.Encoding.ASCII.GetString(data, 0, end);
    }
    private static void ValidateArmRest(List<(string Name, string Control, int Parent)> bones)
    {
        var controls = new Dictionary<string, int>();
        var parents = new int[bones.Count];
        var arms = new HashSet<string>(new[] { "larm", "rarm", "lhand", "rhand" });
        for (var i = 0; i < bones.Count; ++i)
        {
            var bone = bones[i];
            if (bone.Control != "" && !controls.TryAdd(bone.Control, i))
                throw new InvalidDataException("Duplicate arm policy control.");
            var parent = bone.Parent;
            while (parent >= 0 && bones[parent].Control == "") parent = bones[parent].Parent;
            parents[i] = parent;
            if (bone.Control != "" && !arms.Contains(bone.Control) && parent >= 0 && arms.Contains(bones[parent].Control))
                throw new InvalidDataException("Unsupported bound arm descendant.");
        }
        foreach (var (control, name, parent) in new[] {
            ("larm", "Upperarm_Left", "torso"), ("rarm", "Upperarm_Right", "torso"),
            ("lhand", "Forearm_Left", "larm"), ("rhand", "Forearm_Right", "rarm") })
        {
            if (!controls.TryGetValue(control, out var index) || bones[index].Name != name ||
                parents[index] < 0 || bones[parents[index]].Control != parent)
                throw new InvalidDataException("Authored arm parent mismatch.");
        }
    }

    private static uint ReadMesh(BinaryReader reader, OwnedEmission.Mesh emissionMesh)
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
            if (batches is < 1 or > 256 || bones is < 1 or > 256 || refs is < 1 or > 128 || flags > 3)
                throw new InvalidDataException("Invalid owned rig counts.");
            emissionMesh.Fold(batches);
            for (var i = 0; i < 5; ++i)
            {
                var value = reader.ReadDouble();
                if (!double.IsFinite(value) || (i == 0 && (value < 0 || value > 10)))
                    throw new InvalidDataException("Invalid owned gait metadata.");
            }
            var names = new HashSet<string>(); var controls = new HashSet<string>();
            var rigBones = new List<(string Name, string Control, int Parent)>();
            for (var i = 0; i < bones; ++i)
            {
                var name = Name();
                if (!names.Add(name)) throw new InvalidDataException("Duplicate owned bone.");
                var control = Name(true); if (control != "") controls.Add(control);
                var parent = reader.ReadInt32();
                if (parent < -1 || parent >= i) throw new InvalidDataException("Invalid owned bone parent.");
                Matrix();
                rigBones.Add((name, control, parent));
            }
            if (flags == 3) ValidateArmRest(rigBones);
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
                var binding = new OwnedEmission.Batch { Owner = Name() };
                Name(); var bone = reader.ReadUInt32(); var size = reader.ReadUInt32(); reader.ReadUInt32();
                binding.Rigid = bone != uint.MaxValue;
                if ((bone != uint.MaxValue && bone >= bones) || size is < 1 or > 65535 || size % 3 != 0)
                    throw new InvalidDataException("Invalid owned visual batch.");
                emissionMesh.Fold(size);
                for (var vertex = 0; vertex < size; ++vertex)
                {
                    float normalLength = 0;
                    for (var field = 0; field < 8; ++field)
                    {
                        var value = reader.ReadSingle();
                        if (!float.IsFinite(value)) throw new InvalidDataException("Nonfinite owned vertex.");
                        if (field >= 3 && field <= 5) normalLength += value * value;
                        emissionMesh.Fold(BitConverter.SingleToUInt32Bits(value));
                        if (field < 3)
                        {
                            binding.Low[field] = Math.Min(binding.Low[field], value);
                            binding.High[field] = Math.Max(binding.High[field], value);
                        }
                    }
                    if (normalLength < .5f) throw new InvalidDataException("Invalid owned vertex normal.");
                }
                if (bone == uint.MaxValue)
                    for (var vertex = 0; vertex < size; ++vertex)
                        if (reader.ReadUInt32() >= bones) throw new InvalidDataException("Invalid owned vertex bone.");
                emissionMesh.Batches.Add(binding);
            }
            if (reader.BaseStream.Position != reader.BaseStream.Length)
                throw new InvalidDataException("Trailing owned mesh data.");
            return batches;
        }
        catch (EndOfStreamException error) { throw new InvalidDataException("Truncated owned mesh.", error); }
    }

}
