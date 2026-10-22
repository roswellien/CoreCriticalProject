using System.IO;
using MW3RemasterLauncher.Core;

static class OriginalSupportChecks
{
    public static void Run()
    {
        var source = new byte[1024];
        void U16(int offset, ushort value) => BitConverter.GetBytes(value).CopyTo(source, offset);
        void U32(int offset, uint value) => BitConverter.GetBytes(value).CopyTo(source, offset);
        U16(0, 0x5a4d); U32(0x3c, 0x80); U32(0x80, 0x4550);
        U16(0x84, 0x14c); U16(0x86, 1); U16(0x94, 224);
        const int optional = 0x98, section = optional + 224;
        U16(optional, 0x10b); U32(optional + 28, 0x10000000); U32(optional + 92, 16);
        U32(optional + 136, 0x1100); U32(optional + 140, 12);
        U32(section + 8, 0x200); U32(section + 12, 0x1000); U32(section + 16, 0x200); U32(section + 20, 0x200);
        U32(0x220, 0x10001234); U32(0x300, 0x1000); U32(0x304, 12); U16(0x308, 0x3020);
        var before = (byte[])source.Clone();
        var result = PeImageRelocator.Rebase(source, 0x11000000);
        if (!before.SequenceEqual(source) || BitConverter.ToUInt32(result, 0x220) != 0x11001234 ||
            BitConverter.ToUInt32(result, optional + 28) != 0x11000000)
            throw new Exception("PE relocation changed source or failed to relocate HIGHLOW/ImageBase.");
        void Reject(Action change)
        {
            source = (byte[])before.Clone(); change();
            try { PeImageRelocator.Rebase(source, 0x11000000); }
            catch (InvalidDataException) { return; }
            throw new Exception("Invalid original PE relocation input was accepted.");
        }
        Reject(() => U16(0x308, 0x5020)); // Unsupported relocation type.
        Reject(() => U32(0x304, 7));
        Reject(() => U32(0x304, 100));
        Reject(() => U16(0x308, 0x3fff)); // Target outside backed bytes.
        Reject(() => U32(optional + 136, 0xfffffff0));
        Reject(() => U16(optional, 0x20b));
        Reject(() => U32(0x3c, 0xffffffff));
        Reject(() => source = source[..100]);
        try { CrtSourcePack.Build(before); throw new Exception("An unknown startup provider was accepted."); }
        catch (InvalidDataException) { }
        Console.WriteLine("Original-provider relocation, source preservation and malformed-PE checks passed.");
    }
}
