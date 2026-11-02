using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public sealed class HeadlightBindingsWindow : Window
{
    public HeadlightBindingsWindow(string dataRoot)
    {
        Title = "Headlight controls"; Width = 480; Height = 400;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var store = new HeadlightBindings(dataRoot);
        var binding = store.Load();
        bool capturing = false;
        var panel = new StackPanel { Margin = new Thickness(24) };
        Content = panel;
        panel.Children.Add(new TextBlock { Text = "Toggle all headlights on your mech. Requires Headlights and Dynamic Lighting in Display, and a mech equipped with lights. Applies on the next launch.", TextWrapping = TextWrapping.Wrap });
        var key = new Button { Content = ControlKeys.Label(binding.Key), Margin = new Thickness(0, 16, 0, 8) };
        System.Windows.Automation.AutomationProperties.SetName(key, "Headlight keyboard binding");
        key.Click += (_, _) => { capturing = true; key.Content = "Press a key (Esc cancels)…"; };
        panel.Children.Add(key);
        var clear = new Button { Content = "Clear keyboard binding" };
        clear.Click += (_, _) => { capturing = false; binding = binding with { Key = 0 }; key.Content = "Unassigned"; };
        panel.Children.Add(clear);
        panel.Children.Add(new TextBlock { Text = "Controller button (uses your enabled controller layout):", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 16, 0, 8) });
        var button = new ComboBox { ItemsSource = new[] { "Unassigned" }.Concat(ControllerWindow.ButtonNames).ToArray(), SelectedIndex = binding.Button + 1 };
        System.Windows.Automation.AutomationProperties.SetName(button, "Headlight controller button");
        panel.Children.Add(button);
        var status = new TextBlock { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 8, 0, 8) };
        panel.Children.Add(status);
        PreviewKeyDown += (_, e) => {
            if (!capturing) return;
            e.Handled = true;
            var pressed = e.Key == Key.System ? e.SystemKey : e.Key;
            if (pressed == Key.Escape) { capturing = false; key.Content = ControlKeys.Label(binding.Key); return; }
            try {
                binding = binding with { Key = ControlKeys.Capture(pressed, Keyboard.Modifiers) };
                key.Content = ControlKeys.Label(binding.Key); capturing = false; status.Text = "";
            } catch (Exception ex) { status.Text = ex.Message; }
        };
        var save = new Button { Content = "Save" };
        save.Click += (_, _) => {
            try { store.Save(binding with { Button = button.SelectedIndex - 1 }); DialogResult = true; }
            catch (Exception ex) { status.Text = ex.Message; }
        };
        panel.Children.Add(save);
    }
}
