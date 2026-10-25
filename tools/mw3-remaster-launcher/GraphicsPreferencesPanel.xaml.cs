using System.Windows;
using System.Windows.Controls;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>The same choices and validation in first-run setup and Display.</summary>
public partial class GraphicsPreferencesPanel : UserControl
{
    public event RoutedEventHandler? Changed;
    private bool _loading;
    public GraphicsPreferencesPanel() => InitializeComponent();

    public void Load(LauncherSettings settings)
    {
        _loading = true;
        try
        {
            Select(ComboWindowMode, settings.WindowMode);
            var resolution = $"{settings.Width}x{settings.Height}";
            if (!ComboResolution.Items.OfType<ComboBoxItem>().Any(x => x.Tag?.ToString() == resolution))
                ComboResolution.Items.Add(new ComboBoxItem { Content = resolution + " (saved display resolution)", Tag = resolution });
            Select(ComboResolution, resolution);
            Select(ComboAA, settings.AntiAliasing == "1" ? "off" : settings.AntiAliasing);
            Select(ComboAF, settings.AnisotropicFiltering.ToString());
            Select(ComboDrawDist, settings.DrawDistance.ToString());
            Select(ComboFog, settings.FogDistance.ToString());
            ChkDynamicLighting.IsChecked = settings.DynamicLighting;
            ChkShadows.IsChecked = settings.Shadows;
            ChkShadows.IsEnabled = settings.DynamicLighting;
        }
        finally { _loading = false; }
    }

    public GraphicsPreferences Read()
    {
        var parts = Value(ComboResolution).Split('x');
        if (parts.Length != 2 || !int.TryParse(parts[0], out var width) || !int.TryParse(parts[1], out var height))
            throw new InvalidOperationException("Choose a display resolution.");
        var result = new GraphicsPreferences(width, height, Value(ComboWindowMode), Value(ComboAA),
            int.Parse(Value(ComboAF)), int.Parse(Value(ComboDrawDist)), int.Parse(Value(ComboFog)),
            ChkDynamicLighting.IsChecked == true, ChkShadows.IsChecked == true);
        result.Validate();
        return result;
    }

    private static string Value(ComboBox combo) => (combo.SelectedItem as ComboBoxItem)?.Tag?.ToString()
        ?? throw new InvalidOperationException("Choose all display and graphics settings.");
    private static void Select(ComboBox combo, string value) => combo.SelectedItem =
        combo.Items.OfType<ComboBoxItem>().FirstOrDefault(x => x.Tag?.ToString() == value);
    private void ControlChanged(object sender, RoutedEventArgs e)
    {
        if (ChkShadows != null && ChkDynamicLighting != null)
            ChkShadows.IsEnabled = ChkDynamicLighting.IsChecked == true;
        if (!_loading) Changed?.Invoke(this, new RoutedEventArgs());
    }
}
