using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

namespace MW3RemasterLauncher.Core;

public sealed record ControllerDevice(uint Instance, string Name, string Key, bool HasSerial, bool CanBind = true)
{
    public override string ToString() => Name + (HasSerial ? "" : " (connection-specific calibration)");
}
public sealed record ControllerState(short[] Axes, bool[] Buttons);

/// <summary>Input-only SDL session, owned by the setup window on its UI thread. No global key injection.</summary>
public sealed class ControllerInput : IDisposable
{
    private const string Library = "SDL3.dll";
    private bool initialized;
    private readonly Dictionary<uint, nint> handles = new();
    private readonly int thread = Environment.CurrentManagedThreadId;
    private static readonly object LoadLock = new();
    private static bool loaded;
    public ControllerInput()
    {
        lock (LoadLock)
        {
            if (!loaded)
            {
                string path = Path.Combine(AppContext.BaseDirectory, Library);
                if (!File.Exists(path)) throw new InvalidOperationException("Controller support files are missing. Rebuild with the pinned SDL3 runtime.");
                PackStorage.EnsureNoLinks(path);
                var library = NativeLibrary.Load(path);
                NativeLibrary.SetDllImportResolver(typeof(ControllerInput).Assembly, (name, _, _) => name == Library ? library : 0);
                loaded = true; // Retained for the assembly lifetime, never resolve from the working directory.
            }
        }
        // The build verifies upstream bytes before distribution signing changes the PE certificate.
        if (SDL_GetVersion() != 3004018) throw new InvalidDataException("Controller runtime version does not match this launcher.");
        if (!SDL_InitSubSystem(0x2000)) throw new InvalidOperationException("Controller input could not start: " + Text(SDL_GetError()));
        initialized = true;
        // This window polls directly. Disable queues to avoid an unconsumed event backlog.
        SDL_SetGamepadEventsEnabled(false); SDL_SetJoystickEventsEnabled(false);
    }
    private void RequireThread()
    {
        if (Environment.CurrentManagedThreadId != thread) throw new InvalidOperationException("Controller session must stay on its owning thread.");
        ObjectDisposedException.ThrowIf(!initialized, this);
    }
    private static string Text(nint p) => Marshal.PtrToStringUTF8(p) ?? "";
    public IReadOnlyList<ControllerDevice> Scan()
    {
        RequireThread(); SDL_UpdateGamepads();
        nint ids = SDL_GetGamepads(out int count);
        if (ids == 0) throw new InvalidOperationException("Cannot enumerate controllers: " + Text(SDL_GetError()));
        try
        {
            if (count is < 0 or > 128) throw new InvalidDataException("Unexpected number of controllers.");
            var devices = new List<ControllerDevice>();
            var present = new HashSet<uint>();
            for (int i = 0; i < count; i++)
            {
                uint id = unchecked((uint)Marshal.ReadInt32(ids, i * 4)); present.Add(id);
                if (!handles.TryGetValue(id, out nint pad))
                {
                    pad = SDL_OpenGamepad(id);
                    if (pad == 0) throw new InvalidOperationException("Cannot open controller: " + Text(SDL_GetError()));
                    handles.Add(id, pad);
                }
                string serial = Text(SDL_GetGamepadSerial(pad));
                // A GUID alone identifies a class, not a physical unit. Never share calibration silently.
                var guid = SDL_GetGamepadGUIDForID(id);
                string identity = Convert.ToHexString(guid.Data) + ":" + (serial.Length > 0 ? serial : Text(SDL_GetGamepadPath(pad)));
                if (serial.Length == 0 && string.IsNullOrEmpty(Text(SDL_GetGamepadPath(pad)))) identity += ":session:" + id;
                string key = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(identity)));
                devices.Add(new(id, Text(SDL_GetGamepadName(pad)), key, serial.Length > 0, serial.Length > 0 || Text(SDL_GetGamepadPath(pad)).Length > 0));
            }
            foreach (uint removed in handles.Keys.Except(present).ToArray()) { SDL_CloseGamepad(handles[removed]); handles.Remove(removed); }
            // Identical serial/path identities are ambiguous: require a connection-specific calibration.
            return devices.Select(d => devices.Count(x => x.Key == d.Key) > 1 ? d with {
                Key = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(d.Key + ":" + d.Instance))), HasSerial = false, CanBind = false
            } : d).ToArray();
        }
        finally { SDL_free(ids); }
    }
    public ControllerState? Read(uint instance)
    {
        RequireThread(); SDL_UpdateGamepads();
        if (!handles.TryGetValue(instance, out nint pad) || !SDL_GamepadConnected(pad)) return null;
        return new(Enumerable.Range(0, 6).Select(i => SDL_GetGamepadAxis(pad, i)).ToArray(),
            Enumerable.Range(0, 26).Select(i => SDL_GetGamepadButton(pad, i)).ToArray());
    }
    public void Dispose()
    {
        if (!initialized) return;
        RequireThread();
        foreach (var pad in handles.Values) SDL_CloseGamepad(pad);
        handles.Clear(); SDL_QuitSubSystem(0x2000); initialized = false;
    }
    [StructLayout(LayoutKind.Sequential)] private struct GuidBytes { [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)] public byte[] Data; }
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern int SDL_GetVersion();
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] [return: MarshalAs(UnmanagedType.I1)] private static extern bool SDL_InitSubSystem(uint flags);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern void SDL_QuitSubSystem(uint flags);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern nint SDL_GetError();
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern nint SDL_GetGamepads(out int count);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern nint SDL_OpenGamepad(uint instance);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern void SDL_CloseGamepad(nint pad);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern void SDL_UpdateGamepads();
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern void SDL_SetGamepadEventsEnabled([MarshalAs(UnmanagedType.I1)] bool enabled);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern void SDL_SetJoystickEventsEnabled([MarshalAs(UnmanagedType.I1)] bool enabled);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern nint SDL_GetGamepadName(nint pad);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern nint SDL_GetGamepadSerial(nint pad);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern nint SDL_GetGamepadPath(nint pad);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern GuidBytes SDL_GetGamepadGUIDForID(uint instance);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] [return: MarshalAs(UnmanagedType.I1)] private static extern bool SDL_GamepadConnected(nint pad);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern short SDL_GetGamepadAxis(nint pad, int axis);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] [return: MarshalAs(UnmanagedType.I1)] private static extern bool SDL_GetGamepadButton(nint pad, int button);
    [DllImport(Library, CallingConvention = CallingConvention.Cdecl)] private static extern void SDL_free(nint memory);
}
