using System.IO;
using System.Text;

namespace MW3RemasterLauncher.Core;

/// <summary>Import validation for explicitly authored replacement emission.</summary>
internal static class OwnedEmission
{
    internal const string Format = "BWMEM1";
    internal const string Capability = "owned-chassis-emission";
    internal sealed class Batch
    {
        internal string Owner = "", Material = "";
        internal uint Width, Height;
        internal ulong ColorHash;
        internal bool Rigid = true;
        internal readonly float[] Low = [float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity];
        internal readonly float[] High = [float.NegativeInfinity, float.NegativeInfinity, float.NegativeInfinity];
    }
    internal sealed class Mesh
    {
        internal ulong Hash = 0xCBF29CE484222325;
        internal readonly List<Batch> Batches = [];
        internal void Fold(uint word)
        {
            for (var shift = 0; shift < 32; shift += 8)
                Hash = unchecked((Hash ^ (byte)(word >> shift)) * 0x100000001B3);
        }
    }

    internal static void Read(string path, Mesh mesh)
    {
        if (new FileInfo(path).Length is < 20 or > 1024 * 1024)
            throw new InvalidDataException("Invalid owned emission size.");
        using var reader = new BinaryReader(File.OpenRead(path));
        string Name() => OwnedChassisVisuals.ReadName(reader);
        float Scalar(float low, float high)
        {
            var value = reader.ReadSingle();
            if (!float.IsFinite(value) || value < low || value > high)
                throw new InvalidDataException("Invalid emission floating point value.");
            return value;
        }
        if (!reader.ReadBytes(8).SequenceEqual(Encoding.ASCII.GetBytes("BWMEM1\0\0")))
            throw new InvalidDataException("Unsupported owned emission format.");
        var count = reader.ReadUInt32();
        if (count is < 1 or > 64 || reader.ReadUInt64() != mesh.Hash)
            throw new InvalidDataException("Emission mesh identity/count mismatch.");
        var ids = new HashSet<string>(); var batches = new HashSet<uint>();
        for (var index = 0; index < count; ++index)
        {
            var id = Name(); var batchIndex = reader.ReadUInt32();
            var owner = Name(); var material = Name();
            var width = reader.ReadUInt32(); var height = reader.ReadUInt32();
            var hash = reader.ReadUInt64();
            if (!ids.Add(id) || !batches.Add(batchIndex) || batchIndex >= mesh.Batches.Count)
                throw new InvalidDataException("Duplicate or invalid emission binding.");
            var batch = mesh.Batches[(int)batchIndex];
            if (!batch.Rigid) throw new InvalidDataException("Emission version 1 requires a rigid batch.");
            if (owner != batch.Owner || material != batch.Material || width != batch.Width ||
                height != batch.Height || hash != batch.ColorHash)
                throw new InvalidDataException("Emission material identity mismatch.");
            Scalar(0, 2);
            var regions = reader.ReadUInt32(); var anchors = reader.ReadUInt32();
            if (regions is < 1 or > 32 || anchors > 8)
                throw new InvalidDataException("Invalid emission region/anchor count.");
            for (var region = 0; region < regions; ++region)
            {
                var u0 = Scalar(0, 1); var v0 = Scalar(0, 1);
                var u1 = Scalar(0, 1); var v1 = Scalar(0, 1);
                if (u0 >= u1 || v0 >= v1)
                    throw new InvalidDataException("Empty emission UV rectangle.");
            }
            var anchorIds = new HashSet<string>();
            for (var anchor = 0; anchor < anchors; ++anchor)
            {
                if (!anchorIds.Add(Name())) throw new InvalidDataException("Duplicate emission anchor.");
                for (var axis = 0; axis < 3; ++axis)
                {
                    var position = Scalar(-1e6f, 1e6f);
                    if (position < batch.Low[axis] - 4 || position > batch.High[axis] + 4)
                        throw new InvalidDataException("Out-of-bounds emission anchor.");
                }
                for (var axis = 0; axis < 3; ++axis) Scalar(0, 1);
                Scalar(0, 4); Scalar(0, 2);
            }
        }
        if (reader.BaseStream.Position != reader.BaseStream.Length)
            throw new InvalidDataException("Trailing owned emission bytes.");
    }
}
