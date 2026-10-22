using System.Buffers.Binary;
using System.IO;

namespace MW3RemasterLauncher.Core;

/// <summary>Relocate admitted PE32 input data; never load or execute the input image.</summary>
public static class PeImageRelocator
{
    public static byte[] Rebase(byte[] source, uint newBase)
    {
        var image = (byte[])source.Clone();
        void Range(long offset, long count)
        {
            if (offset < 0 || count < 0 || offset > image.Length - count)
                throw new InvalidDataException("PE relocation range is outside the original image.");
        }
        ushort U16(int offset) { Range(offset, 2); return BinaryPrimitives.ReadUInt16LittleEndian(image.AsSpan(offset, 2)); }
        uint U32(int offset) { Range(offset, 4); return BinaryPrimitives.ReadUInt32LittleEndian(image.AsSpan(offset, 4)); }
        void Put(int offset, uint value) { Range(offset, 4); BinaryPrimitives.WriteUInt32LittleEndian(image.AsSpan(offset, 4), value); }
        if (U16(0) != 0x5a4d) throw new InvalidDataException("Original input is not an MZ image.");
        var peValue = U32(0x3c);
        if (peValue > int.MaxValue - 24) throw new InvalidDataException("Invalid PE header offset.");
        var pe = (int)peValue;
        if (U32(pe) != 0x4550 || U16(pe + 4) != 0x14c) throw new InvalidDataException("Original input must be a PE32 x86 image.");
        var sections = U16(pe + 6); var optionalSize = U16(pe + 20); var optional = pe + 24;
        Range(optional, optionalSize);
        if (U16(optional) != 0x10b || optionalSize < 144 || U32(optional + 92) < 6 || sections is < 1 or > 96)
            throw new InvalidDataException("PE32 relocation headers are incomplete.");
        var table = checked(optional + optionalSize); Range(table, sections * 40L);
        int Offset(uint address, uint count)
        {
            for (var i = 0; i < sections; i++)
            {
                var row = table + i * 40; var start = U32(row + 12); var rawSize = U32(row + 16); var raw = U32(row + 20);
                if (address < start || (ulong)address - start + count > rawSize) continue;
                var offset = (ulong)raw + address - start;
                if (offset > int.MaxValue) throw new InvalidDataException("PE section offset overflow.");
                Range((long)offset, count); return (int)offset;
            }
            throw new InvalidDataException("PE relocation points outside backed section data.");
        }
        var rva = U32(optional + 136); var size = U32(optional + 140);
        if (rva == 0 || size == 0) throw new InvalidDataException("Original image has no base relocation directory.");
        var position = Offset(rva, size); var end = checked(position + (int)size);
        var delta = unchecked(newBase - U32(optional + 28));
        while (position < end)
        {
            if (end - position < 8) throw new InvalidDataException("Truncated PE relocation block.");
            var page = U32(position); var block = U32(position + 4);
            if (page == 0 && block == 0 && image.AsSpan(position, end - position).IndexOfAnyExcept((byte)0) < 0) break;
            if (block < 8 || block % 2 != 0 || block > end - position)
                throw new InvalidDataException("Invalid PE relocation block size.");
            for (var index = 8; index < block; index += 2)
            {
                var entry = U16(position + index); var kind = entry >> 12;
                if (kind == 0) continue; // IMAGE_REL_BASED_ABSOLUTE padding.
                if (kind != 3) throw new InvalidDataException("Unsupported PE32 relocation type.");
                var address = (ulong)page + (uint)(entry & 0xfff);
                if (address > uint.MaxValue) throw new InvalidDataException("PE relocation address overflow.");
                var offset = Offset((uint)address, 4); Put(offset, unchecked(U32(offset) + delta));
            }
            position += (int)block;
        }
        Put(optional + 28, newBase);
        return image;
    }
}
