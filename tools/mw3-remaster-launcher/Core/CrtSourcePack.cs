using System.IO;
using System.Security.Cryptography;

namespace MW3RemasterLauncher.Core;

/// <summary>Reproduce the admitted startup source-page pack directly from the player's CRT image.</summary>
public static class CrtSourcePack
{
    public const string Hash = "fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80";

    public static byte[] Build(byte[] provider)
    {
        if (!Convert.ToHexString(SHA256.HashData(provider)).Equals("2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Unsupported original startup provider.");
        // Addresses and lengths reproduce the source-only prepare_native/derive_registry
        // contract. Every payload byte comes from the admitted user image or 0xCC padding.
        var pe = BitConverter.ToInt32(provider, 0x3c); var optional = pe + 24;
        var sectionCount = BitConverter.ToUInt16(provider, pe + 6);
        var table = optional + BitConverter.ToUInt16(provider, pe + 20);
        var imageBase = BitConverter.ToUInt32(provider, optional + 28);
        byte[] Slice(uint address, int bytes)
        {
            if (address < imageBase) throw new InvalidDataException("Startup source address below image base.");
            var rva = address - imageBase;
            for (var i = 0; i < sectionCount; i++)
            {
                var row = table + i * 40;
                var va = BitConverter.ToUInt32(provider, row + 12); var size = BitConverter.ToUInt32(provider, row + 16);
                var raw = BitConverter.ToUInt32(provider, row + 20);
                if (rva < va || (ulong)rva - va + (uint)bytes > size) continue;
                var offset = (ulong)raw + rva - va;
                if (offset + (uint)bytes > (ulong)provider.Length) throw new InvalidDataException("Startup source slice is unbacked.");
                return provider.AsSpan((int)offset, bytes).ToArray();
            }
            throw new InvalidDataException("Startup source slice outside original sections.");
        }
        var pages = new SortedDictionary<uint, (uint Permissions, byte[] Bytes)>();
        void Copy(uint address, int bytes, uint permissions)
        {
            var data = Slice(address, bytes);
            for (var i = 0; i < data.Length; i++)
            {
                var at = address + (uint)i; var page = at & ~4095U;
                if (!pages.TryGetValue(page, out var entry))
                    pages[page] = entry = (permissions, Enumerable.Repeat((byte)0xcc, 4096).ToArray());
                if (entry.Permissions != permissions) throw new InvalidDataException("Startup source page permissions overlap.");
                entry.Bytes[at & 4095] = data[i];
            }
        }
        foreach (var (address, bytes) in new (uint, int)[] {
            (0x78004254,141), (0x7802c070,62), (0x780042e1,303), (0x7801129b,125), (0x78004227,45) })
            Copy(address, bytes, 5);
        Copy(0x7802e000, 4096, 1); Copy(0x78037000, 4096, 3);
        foreach (var address in new uint[] { 0x78030018, 0x78030010, 0x7802ffc8 }) Copy(address, 8, 1);
        using var output = new MemoryStream();
        using (var writer = new BinaryWriter(output, System.Text.Encoding.UTF8, true))
        {
            writer.Write("MW4FDIP1"u8); writer.Write(pages.Count);
            foreach (var (address, entry) in pages) { writer.Write(address); writer.Write(entry.Permissions); writer.Write(entry.Bytes); }
        }
        var result = output.ToArray();
        if (result.Length != 28740 || !Convert.ToHexString(SHA256.HashData(result)).Equals(Hash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Generated startup source pack failed its runtime identity check.");
        return result;
    }
}
