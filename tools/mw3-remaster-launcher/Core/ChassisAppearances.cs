using System.Buffers.Binary;
using System.IO;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>Validate texture-only alternatives without changing chassis identity.</summary>
public static class ChassisAppearances
{
    public const string Capability = "mech-appearances";
    private const long MaxPageBytes = 128L * 1024 * 1024;
    private const long MaxCatalogBytes = 512L * 1024 * 1024;
    internal readonly record struct ColorKey(uint Width, uint Height, uint Format, ulong Hash);

    private static void Fields(JsonElement value, params string[] names)
    {
        if (value.ValueKind != JsonValueKind.Object ||
            !names.ToHashSet().SetEquals(value.EnumerateObject().Select(p => p.Name)))
            throw new InvalidDataException("Unknown or missing appearance field.");
    }

    private static string PathValue(JsonElement value)
    {
        if (value.ValueKind != JsonValueKind.String || string.IsNullOrEmpty(value.GetString()))
            throw new InvalidDataException("Invalid appearance resource path.");
        return value.GetString()!;
    }

    internal static ulong PixelHash(ReadOnlySpan<byte> data)
    {
        ulong hash = 0xCBF29CE484222325;
        foreach (var value in data) hash = unchecked((hash ^ value) * 0x100000001B3);
        return hash;
    }

    public static void Read(JsonElement appearances, JsonElement baselineTextures,
        NativePackPayload payload, Func<string, string?, string> verify)
    {
        if (!payload.RequiredCapabilities.TryGetValue(Capability, out var version) || version != 1)
            throw new InvalidDataException("Chassis appearances require version 1.");
        if (appearances.ValueKind != JsonValueKind.Object ||
            !appearances.EnumerateObject().Any() ||
            appearances.EnumerateObject().Any(p => p.Name != "upgraded" && p.Name != "new"))
            throw new InvalidDataException("Invalid chassis appearance fields.");
        if (appearances.TryGetProperty("new", out var owned))
        {
            if (!payload.RequiredFormats.Contains("BWMESH4") || !payload.RequiredFormats.Contains("BWTEX1"))
                throw new InvalidDataException("Undeclared owned visual formats.");
            OwnedChassisVisuals.Read(owned, verify);
            if (owned.TryGetProperty("emission", out _) && !payload.RequiredFormats.Contains(OwnedEmission.Format))
                throw new InvalidDataException("Undeclared owned emission format.");
            if (owned.TryGetProperty("normals", out var normalPages) && normalPages.ValueKind == JsonValueKind.Array && normalPages.GetArrayLength() > 0 && !payload.RequiredFormats.Contains("BWSNR2"))
                throw new InvalidDataException("Undeclared owned normal format.");
        }
        if (!appearances.TryGetProperty("upgraded", out _)) return;
        var upgraded = appearances.GetProperty("upgraded");
        Fields(upgraded, "textures", "normals");
        var textures = upgraded.GetProperty("textures");
        if (textures.ValueKind != JsonValueKind.Object ||
            textures.EnumerateObject().Count() is < 1 or > 512)
            throw new InvalidDataException("Invalid appearance texture set.");
        var keys = new HashSet<ColorKey>();
        foreach (var texture in textures.EnumerateObject())
        {
            if (!baselineTextures.TryGetProperty(texture.Name, out _))
                throw new InvalidDataException("Appearance names an unknown texture.");
            var path = verify(PathValue(texture.Value), null);
            if (new FileInfo(path).Length is < 16 or > 16 * 1024 * 1024)
                throw new InvalidDataException("Appearance texture exceeds legacy bounds.");
            var data = File.ReadAllBytes(path);
            var flags = BinaryPrimitives.ReadUInt32LittleEndian(data);
            var width = BinaryPrimitives.ReadUInt16LittleEndian(data.AsSpan(4));
            var height = BinaryPrimitives.ReadUInt16LittleEndian(data.AsSpan(6));
            if (flags is not (3 or 5 or 11) || width is < 1 or > 4096 || height is < 1 or > 4096 ||
                BinaryPrimitives.ReadUInt64LittleEndian(data.AsSpan(8)) != 0 ||
                data.Length != 16L + width * height * (flags == 11 ? 3L : 2L))
                throw new InvalidDataException("Unsupported appearance RGB565 texture.");
            if (flags == 5) keys.Add(new(width, height, 1, PixelHash(data.AsSpan(16))));
        }
        var pages = upgraded.GetProperty("normals");
        if (pages.ValueKind != JsonValueKind.Array || pages.GetArrayLength() > 16)
            throw new InvalidDataException("Invalid appearance normal page list.");
        if (pages.GetArrayLength() > 0 && !payload.RequiredFormats.Contains("BWSNR2"))
            throw new InvalidDataException("Undeclared appearance normal format.");
        var paths = new HashSet<string>(StringComparer.Ordinal);
        var bindings = new HashSet<ColorKey>();
        long total = 0;
        foreach (var page in pages.EnumerateArray())
        {
            var name = PathValue(page);
            if (!paths.Add(name)) throw new InvalidDataException("Duplicate appearance normal page.");
            var path = verify(name, "BWSNR2");
            var size = new FileInfo(path).Length;
            total += size;
            if (size is < 1 or > MaxPageBytes || total > MaxCatalogBytes)
                throw new InvalidDataException("Appearance normal catalog exceeds budget.");
            try { ReadNormals(File.ReadAllBytes(path), keys, bindings); }
            catch (EndOfStreamException error) { throw new InvalidDataException("Truncated appearance normal page.", error); }
        }
    }

    internal static void ReadNormals(byte[] data, HashSet<ColorKey> colors, HashSet<ColorKey> bindings)
    {
        using var stream = new MemoryStream(data);
        using var reader = new BinaryReader(stream);
        byte[] Bytes(int count)
        {
            var bytes = reader.ReadBytes(count);
            if (bytes.Length != count) throw new EndOfStreamException();
            return bytes;
        }
        string Name()
        {
            var bytes = Bytes(32);
            if (bytes[0] == 0 || bytes[31] != 0 || bytes.TakeWhile(b => b != 0).Any(b => b > 127))
                throw new InvalidDataException("Invalid normal material name.");
            return Encoding.ASCII.GetString(bytes, 0, Array.IndexOf(bytes, (byte)0));
        }
        if (!Bytes(8).SequenceEqual("BWSNR2\0\0"u8.ToArray()))
            throw new InvalidDataException("Unsupported appearance normal page.");
        var count = reader.ReadUInt32();
        if (count is < 1 or > 256) throw new InvalidDataException("Invalid normal binding count.");
        var materials = new List<string>();
        for (var index = 0; index < count; index++)
        {
            var key = new ColorKey(reader.ReadUInt32(), reader.ReadUInt32(), reader.ReadUInt32(), reader.ReadUInt64());
            if (!colors.Contains(key) || !bindings.Add(key))
                throw new InvalidDataException("Foreign or duplicate appearance normal key.");
            materials.Add(Name());
        }
        if (!Bytes(8).SequenceEqual("BWNRM2\0\0"u8.ToArray()) || reader.ReadUInt32() != count)
            throw new InvalidDataException("Invalid normal image payload.");
        var imageCount = reader.ReadUInt32();
        if (imageCount > 64) throw new InvalidDataException("Invalid normal image count.");
        var indices = Enumerable.Range(0, (int)count).Select(_ => reader.ReadUInt32()).ToArray();
        var images = new List<string>();
        long total = 0;
        for (var index = 0; index < imageCount; index++)
        {
            var name = Name();
            var width = reader.ReadUInt32();
            var height = reader.ReadUInt32();
            var hash = reader.ReadUInt64();
            if (width is < 1 or > 4096 || height is < 1 or > 4096 || images.Contains(name))
                throw new InvalidDataException("Invalid normal image.");
            var size = checked((int)(width * height * 4));
            total += size;
            if (total > 256L * 1024 * 1024 || size > stream.Length - stream.Position)
                throw new InvalidDataException("Truncated or excessive normal image.");
            if (PixelHash(Bytes(size)) != hash) throw new InvalidDataException("Normal image hash mismatch.");
            images.Add(name);
        }
        for (var index = 0; index < count; index++)
            if (indices[index] != uint.MaxValue &&
                (indices[index] >= images.Count || images[(int)indices[index]] != materials[index]))
                throw new InvalidDataException("Normal material binding mismatch.");
        if (stream.Position != stream.Length) throw new InvalidDataException("Trailing appearance normal data.");
    }
}
