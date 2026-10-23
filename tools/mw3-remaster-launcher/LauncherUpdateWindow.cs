using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public sealed class LauncherUpdateWindow : Window
{
    private readonly string _application;
    private readonly Button _import = new() { Content = "Choose .ccupdate…", Padding = new Thickness(14, 8, 14, 8) };
    private readonly Button _install = new() { Content = "Update Core Critical and restart", IsEnabled = false, Padding = new Thickness(14, 8, 14, 8), Margin = new Thickness(0, 20, 0, 0) };
    private readonly TextBlock _status = new() { Text = "Download the .ccupdate and matching ZIP into the same folder, then choose the update file.", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 16, 0, 0) };
    private LauncherUpdates? _updates;
    private VerifiedLauncherUpdate? _candidate;
    private string? _package;
    private bool _busy;

    public LauncherUpdateWindow(string application)
    {
        _application = application;
        Title = "Core Critical updates"; Width = 600; Height = 360; MinWidth = 520; MinHeight = 340;
        Background = new SolidColorBrush(Color.FromRgb(23, 29, 27)); Foreground = Brushes.WhiteSmoke;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var panel = new StackPanel { Margin = new Thickness(24) };
        panel.Children.Add(new TextBlock { Text = "Update Core Critical", FontSize = 24 });
        panel.Children.Add(new TextBlock { Text = "Launcher updates keep your games, packs, settings and saves in place. Close all games before continuing.", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 12, 0, 20) });
        panel.Children.Add(_import); panel.Children.Add(_status); panel.Children.Add(_install); Content = panel;
        _import.Click += (_, _) => Import();
        _install.Click += async (_, _) =>
        {
            if (_updates == null || _candidate == null || _package == null || _busy) return;
            if (MessageBox.Show(this, "Core Critical will close, install the verified launcher update, and reopen. Continue?", "Update Core Critical", MessageBoxButton.OKCancel) != MessageBoxResult.OK) return;
            _busy = true; _import.IsEnabled = _install.IsEnabled = false;
            _status.Text = "Verifying the installer and preparing restart…";
            try
            {
                var job = await Task.Run(() => _updates.Stage(_candidate, _package));
                LauncherUpdates.StartHelper(job);
                _busy = false;
                Application.Current.Shutdown();
            }
            catch (Exception error) { _status.Text = "Update could not start: " + error.Message; }
            finally { _busy = false; _import.IsEnabled = true; _install.IsEnabled = _candidate != null; }
        };
        Closing += (_, e) => { if (_busy) e.Cancel = true; };
    }

    private void Import()
    {
        var dialog = new OpenFileDialog { Title = "Select Core Critical update", Filter = "Core Critical updates (*.ccupdate)|*.ccupdate" };
        if (dialog.ShowDialog(this) != true) return;
        _candidate = null; _install.IsEnabled = false;
        try
        {
            _updates = new LauncherUpdates(_application, RuntimeUpdates.ReadTrust(_application));
            _candidate = _updates.Verify(LauncherUpdates.ReadMetadata(dialog.FileName));
            _package = Path.ChangeExtension(dialog.FileName, ".zip");
            if (!File.Exists(_package)) throw new FileNotFoundException("Place the matching ZIP beside this .ccupdate file.");
            _status.Text = $"Core Critical {_candidate.Manifest.Version} is ready to verify ({_candidate.Manifest.PackageBytes / 1048576.0:F1} MB). Your games will stay in place.";
            _install.IsEnabled = true;
        }
        catch (Exception error) { _candidate = null; _status.Text = error.Message; }
    }
}
