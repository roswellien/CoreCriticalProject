using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace MW3RemasterLauncher.Core;

/// <summary>Windows Authenticode policy, including certificate chain and timestamp handling.</summary>
internal static class WindowsPublisherTrust
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct FileInfo { public uint Size; public IntPtr Path; public IntPtr File; public IntPtr Subject; }
    [StructLayout(LayoutKind.Sequential)]
    private struct TrustData
    {
        public uint Size; public IntPtr Policy; public IntPtr Sip; public uint Ui; public uint Revocation;
        public uint Choice; public IntPtr File; public uint Action; public IntPtr State;
        public IntPtr Url; public uint Flags; public uint Context; public IntPtr Signature;
    }
    [DllImport("wintrust.dll", ExactSpelling = true)]
    private static extern int WinVerifyTrust(IntPtr window, ref Guid action, ref TrustData data);

    public static void Verify(string path)
    {
        var name = Marshal.StringToCoTaskMemUni(path);
        var filePointer = Marshal.AllocHGlobal(Marshal.SizeOf<FileInfo>());
        var data = new TrustData { Size = (uint)Marshal.SizeOf<TrustData>(), Ui = 2, Choice = 1, File = filePointer, Action = 1 };
        var action = new Guid("00AAC56B-CD44-11d0-8CC2-00C04FC295EE");
        try
        {
            Marshal.StructureToPtr(new FileInfo { Size = (uint)Marshal.SizeOf<FileInfo>(), Path = name }, filePointer, false);
            var result = WinVerifyTrust(new IntPtr(-1), ref action, ref data);
            if (result != 0) throw new InvalidDataException("The launcher installer needs a valid Windows publisher signature (" + new Win32Exception(result).Message + ").");
        }
        finally
        {
            data.Action = 2;
            WinVerifyTrust(new IntPtr(-1), ref action, ref data);
            Marshal.FreeHGlobal(filePointer); Marshal.FreeCoTaskMem(name);
        }
    }
}
