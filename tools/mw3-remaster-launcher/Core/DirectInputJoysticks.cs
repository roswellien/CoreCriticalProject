using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

public sealed record DirectInputJoystick(string InstanceGuid, string ProductName, string InstanceName)
{
    public string DisplayName
    {
        get
        {
            if (string.IsNullOrWhiteSpace(ProductName))
            {
                return InstanceName;
            }

            if (string.Equals(ProductName, InstanceName, StringComparison.Ordinal))
            {
                return ProductName;
            }

            return $"{ProductName} — {InstanceName}";
        }
    }
}

public static class DirectInputJoystickCatalog
{
    private const uint DirectInputVersion = 0x0800;
    private const uint AttachedOnly = 0x00000001;
    private const uint JoystickDeviceType = 4;
    private static readonly Guid InterfaceId = new("BF798031-483A-4DA2-AA99-5D64ED369700");

    public static List<DirectInputJoystick> EnumerateAttached()
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("DirectInput joystick enumeration requires Windows.");
        }

        var instance = Marshal.GetHINSTANCE(typeof(DirectInputJoystickCatalog).Module);
        var interfaceId = InterfaceId;
        Marshal.ThrowExceptionForHR(DirectInput8Create(instance, DirectInputVersion, ref interfaceId,
            out var directInput, IntPtr.Zero));
        try
        {
            if (Marshal.SizeOf<DirectInputDeviceInstance>() != 1100)
            {
                throw new InvalidOperationException("The DirectInput joystick instance layout is unsupported.");
            }

            var devices = new List<DirectInputJoystick>();
            Exception? callbackError = null;
            EnumDevicesCallback callback = (ref DirectInputDeviceInstance device, IntPtr _) =>
            {
                try
                {
                    if ((device.DeviceType & 0xff) == JoystickDeviceType)
                    {
                        devices.Add(new DirectInputJoystick(device.InstanceGuid.ToString("B"),
                            device.ProductName ?? string.Empty, device.InstanceName ?? string.Empty));
                    }

                    return true;
                }
                catch (Exception error)
                {
                    callbackError = error;
                    return false;
                }
            };

            var result = directInput.EnumDevices(JoystickDeviceType, callback, IntPtr.Zero, AttachedOnly);
            if (callbackError != null)
            {
                throw new InvalidOperationException("DirectInput joystick enumeration failed.", callbackError);
            }

            Marshal.ThrowExceptionForHR(result);
            return devices;
        }
        finally
        {
            Marshal.ReleaseComObject(directInput);
        }
    }

    [ComImport]
    [Guid("BF798031-483A-4DA2-AA99-5D64ED369700")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IDirectInput8W
    {
        [PreserveSig]
        int CreateDevice(ref Guid instanceGuid, out IntPtr device, IntPtr outerUnknown);

        [PreserveSig]
        int EnumDevices(uint deviceType, EnumDevicesCallback callback, IntPtr context, uint flags);
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DirectInputDeviceInstance
    {
        public uint Size;
        public Guid InstanceGuid;
        public Guid ProductGuid;
        public uint DeviceType;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string? InstanceName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string? ProductName;
        public Guid ForceFeedbackDriver;
        public ushort UsagePage;
        public ushort Usage;
    }

    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private delegate bool EnumDevicesCallback(ref DirectInputDeviceInstance device, IntPtr context);

    [DllImport("dinput8.dll", ExactSpelling = true, PreserveSig = true)]
    private static extern int DirectInput8Create(IntPtr instance, uint version, ref Guid interfaceId,
        [MarshalAs(UnmanagedType.Interface)] out IDirectInput8W directInput, IntPtr outerUnknown);
}

public static class DirectInputJoystickSelection
{
    public static DirectInputJoystick? Resolve(LauncherSettings settings,
        IReadOnlyList<DirectInputJoystick> attached)
    {
        if (settings.DirectInputJoystickNone)
        {
            return null;
        }

        var instanceGuid = settings.DirectInputJoystickInstanceGuid?.Trim() ?? string.Empty;
        var productName = settings.DirectInputJoystickProductName?.Trim() ?? string.Empty;
        if (instanceGuid.Length == 0 && productName.Length == 0)
        {
            return attached.FirstOrDefault();
        }

        if (Guid.TryParse(instanceGuid, out var selectedGuid))
        {
            var exact = attached.FirstOrDefault(device =>
                Guid.TryParse(device.InstanceGuid, out var deviceGuid) && deviceGuid == selectedGuid);
            if (exact != null)
            {
                return exact;
            }
        }

        return productName.Length == 0
            ? null
            : attached.FirstOrDefault(device =>
                string.Equals(device.ProductName, productName, StringComparison.Ordinal));
    }

    public static void ApplyRuntimeEnvironment(JsonObject environment, LauncherSettings settings)
    {
        var instanceGuid = settings.DirectInputJoystickInstanceGuid?.Trim() ?? string.Empty;
        var productName = settings.DirectInputJoystickProductName?.Trim() ?? string.Empty;
        if (instanceGuid.Length > 0 && !Guid.TryParse(instanceGuid, out _))
        {
            throw new InvalidDataException("The saved DirectInput joystick GUID is invalid.");
        }

        if (productName.Length > 260)
        {
            throw new InvalidDataException("The saved DirectInput joystick product name is too long.");
        }

        string mode;
        if (settings.DirectInputJoystickNone)
        {
            mode = "none";
        }
        else if (instanceGuid.Length == 0 && productName.Length == 0)
        {
            mode = "default";
        }
        else
        {
            mode = "device";
        }

        environment["MW34_DI_JOYSTICK_MODE"] = mode;
        var runtimeGuid = string.Empty;
        if (mode == "device" && Guid.TryParse(instanceGuid, out var guid))
        {
            runtimeGuid = guid.ToString("B");
        }

        environment["MW34_DI_JOYSTICK_GUID"] = runtimeGuid;
        environment["MW34_DI_JOYSTICK_NAME"] = mode == "device" ? productName : string.Empty;
    }
}
