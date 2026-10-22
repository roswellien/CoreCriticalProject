using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Manual update checks and explicit installation; no background execution of downloaded code.</summary>
public sealed class UpdatesWindow : Window
{
    private readonly string _application;
    private readonly string _game;
    private readonly TextBlock _status = new() { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 14, 0, 14) };
    private readonly Button _check = new() { Content = "Check for updates", Padding = new Thickness(12, 7, 12, 7) };
    private readonly Button _import = new() { Content = "Import signed update…", Padding = new Thickness(12, 7, 12, 7) };
    private readonly Button _install = new() { Content = "Prepare and install", IsEnabled = false, Padding = new Thickness(12, 7, 12, 7) };
    private readonly Button _rollback = new() { Content = "Use previous version", Padding = new Thickness(12, 7, 12, 7) };
    private readonly Button _cancel = new() { Content = "Cancel preparation", IsEnabled = false, Padding = new Thickness(12, 7, 12, 7) };
    private VerifiedRuntimeUpdate? _candidate;
    private string? _localPackage;
    private RuntimeUpdates? _updates;
    private CancellationTokenSource? _operation;
    private bool _busy;

    public UpdatesWindow(string application, string game)
    {
        _application = application;
        _game = game;
        Title = "Game updates";
        Width = 650; Height = 440; MinWidth = 580; MinHeight = 400;
        Background = new SolidColorBrush(Color.FromRgb(23, 29, 27)); Foreground = Brushes.WhiteSmoke;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var panel = new StackPanel { Margin = new Thickness(24) };
        panel.Children.Add(new TextBlock { Text = "Game updates", FontSize = 24 });
        panel.Children.Add(new TextBlock { Text = "Prepare new versions using your original game files. Your settings and packs stay in place, and the previous game version is retained.", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 12, 0, 12) });
        var top = new WrapPanel(); top.Children.Add(_check); top.Children.Add(_import); panel.Children.Add(top);
        panel.Children.Add(_status);
        var bottom = new WrapPanel(); bottom.Children.Add(_install); bottom.Children.Add(_rollback); bottom.Children.Add(_cancel); panel.Children.Add(bottom);
        Content = panel;
        _check.Click += async (_, _) => await Run(async () =>
        {
            _candidate = null; _localPackage = null;
            _updates = new RuntimeUpdates(_application, RuntimeUpdates.ReadTrust(_application));
            _candidate = await _updates.CheckAsync(_operation!.Token);
            DescribeCandidate();
        });
        _import.Click += (_, _) => Import();
        _install.Click += async (_, _) => await Run(async () =>
        {
            if (_updates == null || _candidate == null) return;
            var progress = new Progress<string>(message => _status.Text = message);
            await Task.Run(() => _updates.PrepareAsync(_candidate, _game, _localPackage, progress, _operation!.Token));
            _candidate = null;
            _status.Text = "Update ready. Close this window and launch the game. You can return here to use the previous version.";
        });
        _rollback.Click += async (_, _) => await Run(() =>
        {
            // Returning to an already installed version does not require a network feed or signing key.
            new RuntimeUpdates(_application, new("", new())).Rollback();
            _status.Text = "Previous game version selected. Settings and packs were preserved.";
            return Task.CompletedTask;
        });
        _cancel.Click += (_, _) => _operation?.Cancel();
        Closing += (_, e) =>
        {
            if (!_busy) return;
            e.Cancel = true;
            _operation?.Cancel();
            _status.Text = "Stopping preparation. The current version remains selected…";
        };
        var state = new RuntimeUpdates(application, new("", new())).State();
        _rollback.IsEnabled = state.Active != null;
        _status.Text = "Selected game version: " + (state.Active ?? "current installation") + ". Check for an update or import a signed update file.";
    }

    private void DescribeCandidate()
    {
        var manifest = _candidate!.Manifest;
        var sequence = _updates!.State().HighestSequence;
        _status.Text = manifest.Sequence <= sequence
            ? "This update is already installed or older than a previously installed update."
            : $"Version {manifest.Version} is available ({manifest.PackageBytes / (1024.0 * 1024):F1} MB). Preparing it will use your verified original game files.";
        if (manifest.Sequence <= sequence) _candidate = null;
    }

    private void Import()
    {
        var dialog = new OpenFileDialog { Title = "Select signed update metadata", Filter = "Signed update (*.mw3update)|*.mw3update" };
        if (dialog.ShowDialog(this) != true) return;
        _candidate = null;
        try
        {
            _updates = new RuntimeUpdates(_application, RuntimeUpdates.ReadTrust(_application));
            if (new FileInfo(dialog.FileName).Length > 2 * 1024 * 1024) throw new InvalidDataException("Update metadata is too large.");
            _candidate = _updates.Verify(File.ReadAllBytes(dialog.FileName));
            _localPackage = Path.ChangeExtension(dialog.FileName, ".zip");
            if (!File.Exists(_localPackage)) _localPackage = null;
            DescribeCandidate();
        }
        catch (Exception error) { _status.Text = error.Message; }
        _install.IsEnabled = _candidate != null;
    }

    private async Task Run(Func<Task> action)
    {
        if (_busy) return;
        _busy = true;
        _operation = new CancellationTokenSource();
        _check.IsEnabled = _import.IsEnabled = _install.IsEnabled = _rollback.IsEnabled = false;
        _cancel.IsEnabled = true;
        try { await action(); }
        catch (OperationCanceledException) { _status.Text = "Update cancelled. Your current version was kept."; }
        catch (Exception error) { _status.Text = "Update could not complete: " + error.Message; }
        finally
        {
            _operation.Dispose(); _operation = null; _busy = false;
            _check.IsEnabled = _import.IsEnabled = true;
            _rollback.IsEnabled = new RuntimeUpdates(_application, new("", new())).State().Active != null;
            _install.IsEnabled = _candidate != null;
            _cancel.IsEnabled = false;
        }
    }
}
