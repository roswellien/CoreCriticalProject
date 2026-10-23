using System.Buffers.Binary;
using System.Security.Cryptography;

namespace MW3RemasterLauncher.Core;

/// <summary>Match an exact unsigned PE after certificate attachment; does not establish certificate trust.</summary>
public static class PinnedPeImage
{
    public static bool MatchesSignedImage(byte[] image, int unsignedBytes, string unsignedSha256)
    {
        if (unsignedBytes < 256 || image.Length <= unsignedBytes || image.Length > unsignedBytes + 1024 * 1024)
            return false;
        var pe = BinaryPrimitives.ReadInt32LittleEndian(image.AsSpan(60, 4));
        if (image[0] != 'M' || image[1] != 'Z' || pe < 64 || pe > unsignedBytes - 168 ||
            BinaryPrimitives.ReadUInt32LittleEndian(image.AsSpan(pe, 4)) != 0x4550)
            return false;
        var optional = pe + 24;
        var magic = BinaryPrimitives.ReadUInt16LittleEndian(image.AsSpan(optional, 2));
        var directories = magic == 0x20b ? 112 : magic == 0x10b ? 96 : 0;
        if (directories == 0) return false;
        var security = optional + directories + 32;
        if (security > unsignedBytes - 8) return false;
        var certificateOffset = BinaryPrimitives.ReadUInt32LittleEndian(image.AsSpan(security, 4));
        var certificateBytes = BinaryPrimitives.ReadUInt32LittleEndian(image.AsSpan(security + 4, 4));
        if ((unsignedBytes & 7) != 0 || certificateOffset != unsignedBytes || certificateBytes < 8 ||
            (long)certificateOffset + certificateBytes != image.Length)
            return false;
        // Only well-formed, aligned WIN_CERTIFICATE records may follow the pinned image.
        for (var cursor = unsignedBytes; cursor < image.Length;)
        {
            if (image.Length - cursor < 8) return false;
            var size = BinaryPrimitives.ReadUInt32LittleEndian(image.AsSpan(cursor, 4));
            if (size < 8 || size > image.Length - cursor ||
                BinaryPrimitives.ReadUInt16LittleEndian(image.AsSpan(cursor + 4, 2)) != 0x200 ||
                BinaryPrimitives.ReadUInt16LittleEndian(image.AsSpan(cursor + 6, 2)) != 2)
                return false;
            var next = cursor + ((long)size + 7 & ~7L);
            if (next > image.Length) return false;
            cursor = (int)next;
        }
        var original = image.AsSpan(0, unsignedBytes).ToArray();
        original.AsSpan(optional + 64, 4).Clear(); // PE checksum changes on signing.
        original.AsSpan(security, 8).Clear(); // Original pinned image has no certificate table.
        return Convert.ToHexString(SHA256.HashData(original)).Equals(unsignedSha256, StringComparison.OrdinalIgnoreCase);
    }
}
