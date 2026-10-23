using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Input;

namespace MW3RemasterLauncher.Core;

public static class ControlKeys
{
    [DllImport("user32.dll")] private static extern uint MapVirtualKey(uint code, uint type);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetKeyNameText(int parameter, StringBuilder text, int size);
    public static int Capture(Key key, ModifierKeys modifiers, int? physicalScan = null)
    {
        if (key is Key.LeftShift or Key.RightShift or Key.LeftCtrl or Key.RightCtrl or Key.LeftAlt or Key.RightAlt or
            Key.LWin or Key.RWin or Key.None or Key.System || (modifiers & ModifierKeys.Windows) != 0)
            throw new InvalidOperationException("Press a regular key, optionally with Shift, Ctrl or Alt.");
        if (key is Key.F9 or Key.F10 or Key.F11) throw new InvalidOperationException("F9–F11 are used for screenshots, replay and photo mode. Choose another key.");
        if (((modifiers & ModifierKeys.Alt) != 0 && key is Key.F4 or Key.Tab or Key.Escape or Key.Space) ||
            ((modifiers & ModifierKeys.Control) != 0 && key == Key.Escape) ||
            ((modifiers & (ModifierKeys.Control | ModifierKeys.Alt)) == (ModifierKeys.Control | ModifierKeys.Alt) && key == Key.Delete))
            throw new InvalidOperationException("That shortcut is reserved by Windows. Choose another key.");
        var mapped = MapVirtualKey((uint)KeyInterop.VirtualKeyFromKey(key), 4);
        if ((!physicalScan.HasValue && mapped == 0) || key == Key.Pause || (mapped & 0xff00) == 0xe100) throw new InvalidOperationException("This key is not supported by MW3's binding format.");
        int scan = (int)(mapped & 255);
        // Some Windows layouts return the base scan for navigation VKs even in EX mode.
        if ((mapped & 0xff00) == 0xe000 || key is Key.Up or Key.Down or Key.Left or Key.Right or Key.Insert or Key.Delete or
            Key.Home or Key.End or Key.PageUp or Key.PageDown or Key.Divide or Key.Snapshot or Key.Apps) scan |= 0x80;
        if (physicalScan.HasValue)
        {
            if (physicalScan.Value is <= 0 or > 255) throw new InvalidOperationException("This physical key is not supported by MW3.");
            scan = physicalScan.Value;
        }
        // MW3 stores Alt/Ctrl/Shift in bits 8/9/10, independently of DI scan codes.
        return scan | ((modifiers & ModifierKeys.Shift) != 0 ? 0x400 : 0) |
            ((modifiers & ModifierKeys.Control) != 0 ? 0x200 : 0) | ((modifiers & ModifierKeys.Alt) != 0 ? 0x100 : 0);
    }
    public static string Label(int value)
    {
        if (value == 0) return "Unassigned";
        var scan = value & 255;
        var text = new StringBuilder(80);
        GetKeyNameText(((scan & 127) << 16) | ((scan & 128) != 0 ? 1 << 24 : 0), text, text.Capacity);
        return ((value & 0x200) != 0 ? "Ctrl + " : "") + ((value & 0x100) != 0 ? "Alt + " : "") +
            ((value & 0x400) != 0 ? "Shift + " : "") + (text.Length > 0 ? text.ToString() : $"Scan 0x{scan:X2}");
    }
}
