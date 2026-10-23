using System.IO;
using System.Runtime.InteropServices;
using MW3RemasterLauncher.Core;

internal static class ControllerChecks
{
    private static void Check(bool value, string message) { if (!value) throw new Exception(message); }
    private static void Reject(Action action)
    {
        try { action(); } catch (InvalidDataException) { return; }
        throw new Exception("Invalid calibration was accepted.");
    }
    public static void Run()
    {
        var axis = new AxisCalibration();
        Check(axis.Adjust(0, false) == 0 && axis.Adjust(2000, false) == 0, "Stick deadzone failed.");
        Check(axis.Adjust(short.MinValue, false) == -1 && axis.Adjust(short.MaxValue, false) == 1, "Stick endpoints failed.");
        axis.Inverted = true; Check(axis.Adjust(short.MaxValue, false) == -1, "Stick inversion failed.");
        var trigger = new AxisCalibration { Minimum = 0 };
        Check(trigger.Adjust(0, true) == 0 && trigger.Adjust(short.MaxValue, true) == 1, "Trigger range failed.");
        axis.Deadzone = double.NaN; Reject(() => axis.Adjust(0, false));
        string key = new('A', 64);
        var capture = new CalibrationCapture();
        for (int i = 0; i < 40; i++) capture.Rest([100, -100, 150, -150, 0, 0]);
        capture.Range([-32000, -32000, -32000, -32000, 0, 0]);
        capture.Range([32000, 32000, 32000, 32000, 32767, 32767]);
        var measured = capture.Finish(key);
        Check(measured.Axes[0].Center == 100 && measured.Axes[0].Adjust(100, false) == 0, "Rest center failed.");
        var incomplete = new CalibrationCapture();
        for (int i = 0; i < 40; i++) incomplete.Rest([0, 0, 0, 0, 0, 0]);
        incomplete.Range([0, 0, 0, 0, 0, 0]); Reject(() => incomplete.Finish(key));
        var held = new CalibrationCapture();
        for (int i = 0; i < 40; i++) held.Rest([20000, 0, 0, 0, 0, 0]);
        held.Range([-32768, -32768, -32768, -32768, 0, 0]); held.Range([32767, 32767, 32767, 32767, 32767, 32767]);
        Reject(() => held.Finish(key));
        var root = Path.Combine(Path.GetTempPath(), "cc-controller-check-" + Guid.NewGuid().ToString("N"));
        try
        {
            measured.Save(root);
            Check(ControllerCalibration.Load(root, key).Axes[0].Center == 100, "Calibration did not persist.");
            Check(ControllerCalibration.Load(root, new('B', 64)).Axes[0].Center == 0, "Calibration leaked between devices.");
            string file = Path.Combine(root, "controls", "devices", key + ".json");
            File.WriteAllText(file, "{}"); Reject(() => ControllerCalibration.Load(root, key));
            Check(File.ReadAllText(file) == "{}", "Corrupt calibration was overwritten.");
            measured.Save(root);
            var layouts = new ControllerProfiles(root);
            var layout = new ControllerProfile { DeviceKey = key, Enabled = true };
            layouts.Save(layout); Check(layouts.Load().Enabled, "Controller layout did not persist.");
            layout.GameId = "mw4"; Reject(()=>layouts.Save(layout)); layout.GameId = "mw3";
            layout.Buttons[0] = 166; Reject(()=>layouts.Save(layout)); layout.Buttons[0] = 12;
            var launch = System.Text.Json.Nodes.JsonNode.Parse("{\"native\":{\"runtime_environment\":{}}}")!.AsObject();
            try { layouts.PrepareLaunch(launch, root); throw new Exception("Old native host accepted controller setup."); }
            catch (InvalidOperationException) { }
            launch["native"]!["controller_input_version"] = 1;
            layouts.PrepareLaunch(launch, root);
            string exported = File.ReadAllText(Path.Combine(root,"mw3-controller.txt"));
            Check(exported.StartsWith("CC_MW3_CONTROLLER_V1\n"+key), "Native controller config identity missing.");
            Check(exported.Contains("0.12"), "Native numeric format is not invariant.");
            Check(File.ReadAllText(launch["native"]!["runtime_environment"]!["MW34_CONTROLLER_CONFIG"]!.GetValue<string>())==exported,"External native child cannot read the exported physical config path.");
            layout.Enabled = false; layouts.Save(layout); layouts.PrepareLaunch(launch, root);
            Check(launch["native"]!["runtime_environment"]!["MW34_CONTROLLER_CONFIG"]!.GetValue<string>() == "", "Disabled controller leaked into launch.");
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, true); }
        Console.WriteLine("Controller calibration checks passed.");
    }

    // Real SDL input API with authored virtual input, not a physical hardware claim.
    public static void Sdl()
    {
        using var input = new ControllerInput();
        Console.WriteLine($"Physical/mapped devices present before virtual test: {input.Scan().Count}");
        nint lib = NativeLibrary.Load(Path.Combine(AppContext.BaseDirectory, "SDL3.dll"));
        T Export<T>(string name) where T : Delegate => Marshal.GetDelegateForFunctionPointer<T>(NativeLibrary.GetExport(lib, name));
        var attach = Export<Attach>("SDL_AttachVirtualJoystick"); var detach = Export<Detach>("SDL_DetachVirtualJoystick");
        var open = Export<Open>("SDL_OpenJoystick"); var close = Export<Close>("SDL_CloseJoystick");
        var setAxis = Export<SetAxis>("SDL_SetJoystickVirtualAxis"); var setButton = Export<SetButton>("SDL_SetJoystickVirtualButton");
        var name = Marshal.StringToCoTaskMemUTF8("Core Critical authored test pad");
        uint id = 0; nint joystick = 0;
        try
        {
            var desc = new VirtualDescription { Version = 136, Type = 1, Axes = 6, Buttons = 26, ButtonMask = (1u << 26) - 1, AxisMask = 63, Name = name };
            id = attach(ref desc); Check(id != 0, "SDL virtual attach failed.");
            joystick = open(id); Check(joystick != 0, "SDL virtual joystick open failed.");
            var devices = input.Scan(); var pad = devices.Single(d => d.Instance == id);
            Check(pad.Key.Length == 64 && !pad.HasSerial, "Virtual device identity incorrect.");
            Check(setAxis(joystick, 0, 16000) && setAxis(joystick, 4, short.MinValue) && setAxis(joystick, 5, short.MaxValue) && setButton(joystick, 0, true), "SDL virtual write failed.");
            var state = input.Read(id)!;
            Check(state.Axes[0] == 16000 && state.Axes[4] == 0 && state.Axes[5] == 32767 && state.Buttons[0], "SDL state normalization failed.");
            Check(setButton(joystick, 0, false), "SDL button release failed.");
            Check(!input.Read(id)!.Buttons[0], "SDL button remained held.");
            close(joystick); joystick = 0; Check(detach(id), "SDL detach failed.");
            Check(input.Read(id) == null && input.Scan().All(d => d.Instance != id), "Disconnected controller was not released."); id = 0;
            Console.WriteLine("SDL authored virtual attach, axes, triggers, buttons, release and disconnect checks passed.");
        }
        finally
        {
            if (joystick != 0) close(joystick);
            if (id != 0) detach(id);
            Marshal.FreeCoTaskMem(name); NativeLibrary.Free(lib);
        }
    }
    [StructLayout(LayoutKind.Explicit, Size = 136)] private struct VirtualDescription
    {
        [FieldOffset(0)] public uint Version;
        [FieldOffset(4)] public ushort Type;
        [FieldOffset(12)] public ushort Axes;
        [FieldOffset(14)] public ushort Buttons;
        [FieldOffset(28)] public uint ButtonMask;
        [FieldOffset(32)] public uint AxisMask;
        [FieldOffset(40)] public nint Name;
    }
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate uint Attach(ref VirtualDescription desc);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] [return: MarshalAs(UnmanagedType.I1)] private delegate bool Detach(uint id);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate nint Open(uint id);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate void Close(nint joystick);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] [return: MarshalAs(UnmanagedType.I1)] private delegate bool SetAxis(nint joystick, int axis, short value);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] [return: MarshalAs(UnmanagedType.I1)] private delegate bool SetButton(nint joystick, int button, [MarshalAs(UnmanagedType.I1)] bool down);
}
