using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Manual discovery, explicit downloads/installations, and restart continuation for separate products.</summary>
public sealed class OnlineUpdatesWindow : Window
{
    private readonly string _application;
    private readonly string _game;
    private readonly StackPanel _releases = new();
    private readonly TextBlock _versions = new() { TextWrapping = TextWrapping.Wrap };
    private readonly TextBlock _status = new() { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 12, 0, 8) };
    private readonly ProgressBar _progress = new() { Minimum = 0, Maximum = 100, Height = 10, Margin = new Thickness(0, 0, 0, 14) };
    private readonly Button _check = Button("Check for updates");
    private readonly Button _download = Button("Download selected");
    private readonly Button _resume = Button("Resume downloads");
    private readonly Button _install = Button("Install downloaded updates");
    private readonly Button _cancel = Button("Pause / cancel");
    private readonly List<CheckBox> _choices = new();
    private OnlineUpdateService? _service;
    private CancellationTokenSource? _operation;

    private static Button Button(string text) => new() { Content = text, Padding = new Thickness(12, 7, 12, 7), Margin = new Thickness(0, 0, 8, 8) };

    public OnlineUpdatesWindow(string application, string game)
    {
        _application = application; _game = game;
        Title = "Core Critical Updates"; Width = 780; Height = 660; MinWidth = 630; MinHeight = 500;
        Background = new SolidColorBrush(Color.FromRgb(23, 29, 27)); Foreground = Brushes.WhiteSmoke;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var panel = new DockPanel { Margin = new Thickness(24) };
        var top = new StackPanel(); DockPanel.SetDock(top, Dock.Top); panel.Children.Add(top);
        top.Children.Add(new TextBlock { Text = "Updates", FontSize = 26 });
        top.Children.Add(_versions);
        top.Children.Add(new TextBlock { Text = "Choose when to download and install. Launcher and game versions update separately; optional packs stay in Mods & Packs.",
            TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 12, 0, 14) });
        var commands = new WrapPanel(); commands.Children.Add(_check); commands.Children.Add(_download); commands.Children.Add(_resume); top.Children.Add(commands);
        var bottom = new StackPanel(); DockPanel.SetDock(bottom, Dock.Bottom); panel.Children.Add(bottom);
        bottom.Children.Add(_status); bottom.Children.Add(_progress);
        var install = new WrapPanel(); install.Children.Add(_install); install.Children.Add(_cancel); bottom.Children.Add(install);
        var local = new WrapPanel();
        var launcherImport = Button("Import .ccupdate…");
        var runtimeImport = Button("Import .mw3update…");
        var rollback = Button("Use previous MW3 runtime");
        local.Children.Add(launcherImport); local.Children.Add(runtimeImport); local.Children.Add(rollback); bottom.Children.Add(local);
        panel.Children.Add(new ScrollViewer { Content = _releases, VerticalScrollBarVisibility = ScrollBarVisibility.Auto });
        Content = panel;
        _download.IsEnabled = _install.IsEnabled = _resume.IsEnabled = _cancel.IsEnabled = false;
        RefreshVersions();
        try
        {
            _service = new(application, game);
            _status.Text = _service.HasPending ? "An unfinished update is saved. Check for updates, then resume downloads or continue installation." : "Check for updates when you are ready.";
            _resume.IsEnabled = _install.IsEnabled = _service.HasPending;
        }
        catch (Exception error) { _status.Text = error.Message; }
        _check.Click += async (_, _) => await Run(async token =>
        {
            _service ??= new(_application, _game);
            await _service.CheckAsync(token); ShowReleases();
        });
        _download.Click += async (_, _) => await Download(_choices.Where(c => c.IsChecked == true).Select(c => (string)c.Tag).ToArray());
        _resume.Click += async (_, _) => await Download(null);
        _install.Click += async (_, _) => await Run(async token =>
        {
            if (_service == null) return;
            _status.Text = "Checking the saved update plan…"; _progress.IsIndeterminate = true;
            var progress = new Progress<string>(text => _status.Text = text);
            var restart = await Task.Run(() => _service.InstallAsync(progress, token), token);
            if (restart)
            {
                _status.Text = "Restarting Core Critical. The saved game update can continue after restart.";
                _operation = null;
                Application.Current.Shutdown();
            }
            else { RefreshVersions(); _releases.Children.Clear(); _choices.Clear(); }
        });
        _cancel.Click += (_, _) => _operation?.Cancel();
        launcherImport.Click += (_, _) => { if (_operation == null) new LauncherUpdateWindow(_application) { Owner = this }.ShowDialog(); };
        runtimeImport.Click += (_, _) => { if (_operation == null) new UpdatesWindow(_application, _game) { Owner = this }.ShowDialog(); RefreshVersions(); };
        rollback.Click += async (_, _) => await Run(token => Task.Run(() =>
        {
            new RuntimeUpdates(_application, new("", new())).Rollback();
            Dispatcher.Invoke(() => { RefreshVersions(); _status.Text = "Previous MW3 runtime selected. Your settings and packs were preserved."; });
        }, token));
        Closing += (_, e) => { if (_operation != null) { e.Cancel = true; _operation.Cancel(); } };
        Closed += (_, _) => _service?.Dispose();
    }

    private void RefreshVersions()
    {
        try
        {
            _versions.Text = "Core Critical " + typeof(OnlineUpdatesWindow).Assembly.GetName().Version!.ToString(3) +
                "   ·   Selected MW3 runtime: " + OnlineUpdateService.InstalledRuntimeVersion(_application) +
                "   ·   Bundled: " + OnlineUpdateService.InstalledRuntimeVersion(_application, bundled: true);
        }
        catch (Exception error) { _versions.Text = "Installed version could not be read: " + error.Message; }
    }

    private void ShowReleases()
    {
        _releases.Children.Clear(); _choices.Clear();
        foreach (var item in _service!.Available)
        {
            var release = item.Release;
            var label = release.ProductId == GameCatalog.LauncherId ? "Core Critical Launcher" : GameCatalog.Get(release.ProductId).Name;
            var choice = new CheckBox();
            choice.Content = $"{label} {release.DisplayVersion} ({release.Payload.Bytes / 1048576.0:F1} MB)";
            choice.Tag = release.ProductId; choice.IsChecked = item.BlockedReason == null; choice.IsEnabled = item.BlockedReason == null;
            choice.Margin = new Thickness(0, 14, 0, 5); choice.FontSize = 17;
            _choices.Add(choice); _releases.Children.Add(choice);
            _releases.Children.Add(new TextBlock { Text = item.BlockedReason ?? $"Channel: {_service.Channel}. Requires Core Critical {release.MinimumLauncherVersion}+.", TextWrapping = TextWrapping.Wrap });
            _releases.Children.Add(new TextBlock { Text = release.ReleaseNotes, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 6, 0, 10) });
        }
        _status.Text = _service.Available.Count == 0 ? "Up to date for channel " + _service.Channel + "." : "Updates available. Required launcher updates are installed before game updates.";
    }

    private async Task Download(string[]? products) => await Run(async token =>
    {
        if (_service == null) throw new InvalidOperationException("Check for updates first.");
        var progress = new Progress<UpdateTransferProgress>(p =>
        {
            _progress.IsIndeterminate = p.Phase == "Verifying";
            _progress.Value = p.Total == 0 ? 0 : 100.0 * p.Bytes / p.Total;
            _status.Text = $"{p.Phase}: {p.Bytes / 1048576.0:F1} / {p.Total / 1048576.0:F1} MB ({_progress.Value:F0}%)";
        });
        await Task.Run(() => _service.DownloadAsync(products, progress, token), token);
        _status.Text = "Downloads verified. Close all games, then choose Install downloaded updates. The launcher will restart if it needs an update.";
    });

    private async Task Run(Func<CancellationToken, Task> action)
    {
        if (_operation != null) return;
        using var operation = new CancellationTokenSource(); _operation = operation;
        _check.IsEnabled = _download.IsEnabled = _resume.IsEnabled = _install.IsEnabled = false;
        _cancel.IsEnabled = true;
        try { await action(operation.Token); }
        catch (OperationCanceledException) { _status.Text = "Paused. Verified downloads and partial transfers are saved; your selected game runtime was kept."; }
        catch (Exception error) { _status.Text = error.Message + " Your installed games remain available. Retry, or import a local signed update."; }
        finally
        {
            _operation = null; _progress.IsIndeterminate = false;
            _check.IsEnabled = true; _download.IsEnabled = _choices.Any(c => c.IsEnabled);
            _resume.IsEnabled = _install.IsEnabled = _service?.HasPending == true;
            _cancel.IsEnabled = false;
        }
    }
}
