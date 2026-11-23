using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public sealed class HeadlightBindingsWindow : Window
{
    public HeadlightBindingsWindow(string dataRoot)
    {
        Title = "Headlight controls"; Width = 480; Height = 520;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        Background = TryFindResource("BrushGround") as System.Windows.Media.Brush
            ?? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x14, 0x17, 0x17));
        Foreground = TryFindResource("BrushInk") as System.Windows.Media.Brush
            ?? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0xEE, 0xE6, 0xDC));
        var store = new HeadlightBindings(dataRoot);
        var binding = store.Load();
        bool capturingKey = false;
        bool capturingMouse = false;
        bool syncingMouse = false;
        int nativeVirtualKey = 0;
        int? nativeScan = null;

        ControlsWindow.HookPhysicalKeys(this, (vk, scan) => { nativeVirtualKey = vk; nativeScan = scan; });

        var panel = new StackPanel { Margin = new Thickness(24) };
        Content = panel;
        panel.Children.Add(new TextBlock { Text = "Toggle all headlights on your mech. Requires Headlights and Dynamic Lighting in Display, and a mech equipped with lights. Applies on the next launch.", TextWrapping = TextWrapping.Wrap });
        var key = new Button { Content = ControlKeys.Label(binding.Key), Margin = new Thickness(0, 16, 0, 8) };
        System.Windows.Automation.AutomationProperties.SetName(key, "Headlight keyboard binding");
        var mouseButton = new Button { Content = ControlKeys.MouseLabel(binding.Mouse), Margin = new Thickness(0, 0, 0, 8) };
        System.Windows.Automation.AutomationProperties.SetName(mouseButton, "Headlight mouse binding");
        key.Click += (_, _) =>
        {
            capturingMouse = false; // keyboard and mouse capture are mutually exclusive
            mouseButton.Content = ControlKeys.MouseLabel(binding.Mouse);
            capturingKey = true;
            key.Content = "Press a key (Esc cancels)…";
        };
        panel.Children.Add(key);
        var clear = new Button { Content = "Clear keyboard binding" };
        clear.Click += (_, _) => { capturingKey = false; binding = binding with { Key = 0 }; key.Content = "Unassigned"; };
        panel.Children.Add(clear);
        panel.Children.Add(new TextBlock { Text = "Controller button (uses your enabled controller layout):", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 16, 0, 8) });
        var button = new ComboBox { ItemsSource = new[] { "Unassigned" }.Concat(ControllerWindow.ButtonNames).ToArray(), SelectedIndex = binding.Button + 1 };
        System.Windows.Automation.AutomationProperties.SetName(button, "Headlight controller button");
        panel.Children.Add(button);
        panel.Children.Add(new TextBlock { Text = "Mouse button / wheel:", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 16, 0, 8) });
        mouseButton.Click += (_, _) =>
        {
            // Click fires on MouseUp, after PreviewMouseDown, so the arming click is never captured.
            capturingKey = false; // keyboard and mouse capture are mutually exclusive
            key.Content = ControlKeys.Label(binding.Key);
            capturingMouse = true;
            mouseButton.Content = "Click mouse button or scroll wheel (Esc cancels)…";
            Focus();
        };
        panel.Children.Add(mouseButton);
        var mouseCombo = new ComboBox { ItemsSource = Enumerable.Range(0, 8).Select(ControlKeys.MouseLabel).ToArray(), SelectedIndex = binding.Mouse, Margin = new Thickness(0, 0, 0, 8) };
        System.Windows.Automation.AutomationProperties.SetName(mouseCombo, "Headlight mouse choice");
        mouseCombo.SelectionChanged += (_, _) =>
        {
            if (syncingMouse || mouseCombo.SelectedIndex < 0) return;
            capturingMouse = false;
            binding = binding with { Mouse = mouseCombo.SelectedIndex };
            mouseButton.Content = ControlKeys.MouseLabel(binding.Mouse);
        };
        panel.Children.Add(mouseCombo);
        var clearMouse = new Button { Content = "Clear mouse binding" };
        System.Windows.Automation.AutomationProperties.SetName(clearMouse, "Clear mouse binding");
        clearMouse.Click += (_, _) =>
        {
            capturingMouse = false;
            binding = binding with { Mouse = 0 };
            syncingMouse = true;
            mouseCombo.SelectedIndex = 0;
            syncingMouse = false;
            mouseButton.Content = "Unassigned";
        };
        panel.Children.Add(clearMouse);
        var status = new TextBlock { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 8, 0, 8) };
        System.Windows.Automation.AutomationProperties.SetName(status, "Headlight status");
        panel.Children.Add(status);
        PreviewKeyDown += (_, e) =>
        {
            if (capturingKey)
            {
                e.Handled = true;
                var pressed = e.Key == Key.System ? e.SystemKey : e.Key;
                if (pressed == Key.Escape) { capturingKey = false; key.Content = ControlKeys.Label(binding.Key); return; }
                try
                {
                    var physicalScan = nativeVirtualKey == KeyInterop.VirtualKeyFromKey(pressed) ? nativeScan : null;
                    binding = binding with { Key = ControlKeys.Capture(pressed, Keyboard.Modifiers, physicalScan) };
                    key.Content = ControlKeys.Label(binding.Key);
                    capturingKey = false;
                    status.Text = "";
                }
                catch (Exception ex) { status.Text = ex.Message; }
            }
            else if (capturingMouse && (e.Key == Key.Escape || (e.Key == Key.System && e.SystemKey == Key.Escape)))
            {
                e.Handled = true;
                capturingMouse = false;
                mouseButton.Content = ControlKeys.MouseLabel(binding.Mouse);
            }
        };
        PreviewMouseDown += (_, e) =>
        {
            if (capturingMouse)
            {
                if (e.ChangedButton == MouseButton.Left &&
                    ControlsWindow.TryCancelInteractiveLeftClick(e.OriginalSource as DependencyObject, mouseButton, null,
                        () => { capturingMouse = false; mouseButton.Content = ControlKeys.MouseLabel(binding.Mouse); },
                        out var cancelHandled))
                {
                    if (cancelHandled) e.Handled = true;
                    return;
                }
                int mouse = e.ChangedButton switch
                {
                    MouseButton.Left => 1,
                    MouseButton.Right => 2,
                    MouseButton.Middle => 3,
                    MouseButton.XButton1 => 4,
                    MouseButton.XButton2 => 5,
                    _ => 0
                };
                if (mouse > 0)
                {
                    e.Handled = true;
                    binding = binding with { Mouse = mouse };
                    syncingMouse = true;
                    mouseCombo.SelectedIndex = mouse;
                    syncingMouse = false;
                    mouseButton.Content = ControlKeys.MouseLabel(mouse);
                    capturingMouse = false;
                    status.Text = "";
                }
            }
            else if (capturingKey)
            {
                capturingKey = false;
                key.Content = ControlKeys.Label(binding.Key);
            }
        };
        PreviewMouseWheel += (_, e) =>
        {
            if (capturingMouse && e.Delta != 0)
            {
                e.Handled = true;
                int mouse = e.Delta > 0 ? 6 : 7;
                binding = binding with { Mouse = mouse };
                syncingMouse = true;
                mouseCombo.SelectedIndex = mouse;
                syncingMouse = false;
                mouseButton.Content = ControlKeys.MouseLabel(mouse);
                capturingMouse = false;
                status.Text = "";
            }
        };
        Deactivated += (_, _) =>
        {
            if (capturingKey)
            {
                capturingKey = false;
                key.Content = ControlKeys.Label(binding.Key);
            }
            if (capturingMouse)
            {
                capturingMouse = false;
                mouseButton.Content = ControlKeys.MouseLabel(binding.Mouse);
            }
        };
        var save = new Button { Content = "Save" };
        System.Windows.Automation.AutomationProperties.SetName(save, "Save");
        save.Click += (_, _) =>
        {
            try
            {
                store.Save(binding with { Button = button.SelectedIndex - 1, Mouse = mouseCombo.SelectedIndex });
                DialogResult = true;
            }
            catch (Exception ex) { status.Text = ex.Message; }
        };
        panel.Children.Add(save);
    }
}
