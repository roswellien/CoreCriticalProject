using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public partial class MainWindow
{
    private DispatcherTimer? _assetUpdateTimer;
    private CancellationTokenSource? _assetUpdateCancellation;
    private Task? _assetUpdateCheck;
    private bool _assetUpdateWindowOpen;

    private void InitializeAssetPackUpdates()
    {
        if (!AssetPackUpdateService.IsConfigured(_basePath)) return;
        AssetPackUpdateControls.Visibility = Visibility.Visible;
        ChkAutomaticAssetPackChecks.IsChecked = _settingsMgr.Current.AutomaticAssetPackChecks;
        ApplyAssetPackUpdatePreference();
    }

    private void AutomaticAssetPackChecks_Changed(object sender, RoutedEventArgs e)
    {
        if (_isInitializing || _settingsMgr.Current.AutomaticAssetPackChecks ==
            (ChkAutomaticAssetPackChecks.IsChecked == true)) return;
        _settingsMgr.Current.AutomaticAssetPackChecks = ChkAutomaticAssetPackChecks.IsChecked == true;
        _settingsMgr.Save();
        ApplyAssetPackUpdatePreference();
    }

    private void ApplyAssetPackUpdatePreference()
    {
        if (!_settingsMgr.Current.AutomaticAssetPackChecks)
        {
            _assetUpdateTimer?.Stop();
            _assetUpdateCancellation?.Cancel();
            TxtAssetUpdateAvailability.Text = "";
            return;
        }
        if (_assetUpdateTimer == null)
        {
            _assetUpdateTimer = new DispatcherTimer { Interval = TimeSpan.FromMinutes(30) };
            _assetUpdateTimer.Tick += async (_, _) => await RefreshAssetPackUpdatesAsync();
        }
        _assetUpdateTimer.Start();
        _ = RefreshAssetPackUpdatesAsync();
    }

    private async Task RefreshAssetPackUpdatesAsync()
    {
        if (_updateNotificationsClosed || !_settingsMgr.Current.AutomaticAssetPackChecks ||
            _assetUpdateWindowOpen || _assetUpdateCancellation != null || _onlineUpdatesOpen ||
            _assetInstallActive || _nativeSessionActive || _launchPreparing) return;
        _assetUpdateCheck = ReadAssetPackUpdateNoticeAsync();
        try { await _assetUpdateCheck; }
        finally { _assetUpdateCheck = null; }
    }

    private async Task ReadAssetPackUpdateNoticeAsync()
    {
        using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        _assetUpdateCancellation = cancellation;
        try
        {
            var updates = await Task.Run(async () =>
            {
                using var service = new AssetPackUpdateService(_basePath, _dataRoot, _packMgr);
                return await service.CheckAsync(cancellation.Token);
            }, cancellation.Token);
            if (_updateNotificationsClosed || cancellation.IsCancellationRequested ||
                !_settingsMgr.Current.AutomaticAssetPackChecks || _assetUpdateWindowOpen) return;
            TxtAssetUpdateAvailability.Text = updates.Count switch
            {
                0 => "",
                1 => "1 installed pack has an update.",
                _ => $"{updates.Count} installed packs have updates."
            };
        }
        catch (OperationCanceledException) { }
        catch (Exception error)
        {
            Debug.WriteLine("Background asset pack update check: " + error.Message);
        }
        finally
        {
            _assetUpdateCancellation = null;
        }
    }

    private async void CheckAssetPackUpdates_Click(object sender, RoutedEventArgs e)
    {
        if (_assetUpdateWindowOpen || _nativeSessionActive || _assetInstallActive || _launchPreparing ||
            (CmbPackGame.SelectedItem as GameDefinition)?.Id != GameCatalog.Mw3) return;
        _assetUpdateWindowOpen = true;
        BtnCheckAssetPackUpdates.IsEnabled = false;
        _assetUpdateCancellation?.Cancel();
        try
        {
            if (_assetUpdateCheck != null) await _assetUpdateCheck;
            if (_updateNotificationsClosed) return;
            using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(30));
            using var service = new AssetPackUpdateService(_basePath, _dataRoot, _packMgr);
            var updates = await Task.Run(() => service.CheckAsync(cancellation.Token), cancellation.Token);
            if (_updateNotificationsClosed || _nativeSessionActive || _launchPreparing ||
                (CmbPackGame.SelectedItem as GameDefinition)?.Id != GameCatalog.Mw3) return;
            if (updates.Count == 0)
            {
                TxtAssetUpdateAvailability.Text = "";
                MessageBox.Show(this, "No compatible updates were found for your installed asset packs.",
                    "Asset pack updates");
                return;
            }
            ShowAssetPackUpdates(service, updates);
        }
        catch (Exception error)
        {
            if (!_updateNotificationsClosed) MessageBox.Show(this, error.Message, "Asset pack updates");
        }
        finally
        {
            BtnCheckAssetPackUpdates.IsEnabled = true;
            _assetUpdateWindowOpen = false;
        }
    }

    private void ShowAssetPackUpdates(AssetPackUpdateService service, IReadOnlyList<AssetPackRelease> updates)
    {
        var window = new Window
        {
            Owner = this, Title = "Asset pack updates", Width = 500, SizeToContent = SizeToContent.Height,
            WindowStartupLocation = WindowStartupLocation.CenterOwner, ResizeMode = ResizeMode.NoResize
        };
        var content = new StackPanel { Margin = new Thickness(18) };
        var options = updates.Select(release =>
        {
            var installed = _packMgr.Packs.FirstOrDefault(pack => pack.Id == release.Id);
            return new AssetPackUpdateChoice(release, $"{installed?.Name ?? release.Id} · {release.Version}");
        }).ToArray();
        var selector = new ComboBox { ItemsSource = options, DisplayMemberPath = "Label", SelectedIndex = 0 };
        var status = new TextBlock
        {
            Text = "Download through the private playtest site, then choose the downloaded pack to install.",
            TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 10, 0, 8)
        };
        var actions = new StackPanel { Orientation = Orientation.Horizontal };
        var download = new Button { Content = "Open private download", Margin = new Thickness(0, 0, 10, 0) };
        var install = new Button { Content = "Install downloaded update…" };
        content.Children.Add(selector);
        content.Children.Add(status);
        content.Children.Add(actions);
        actions.Children.Add(download);
        actions.Children.Add(install);
        window.Content = content;
        window.Closing += (_, e) => { if (_assetInstallActive) e.Cancel = true; };

        download.Click += (_, _) =>
        {
            if (selector.SelectedItem is not AssetPackUpdateChoice choice) return;
            try
            {
                Process.Start(new ProcessStartInfo(choice.Release.Archive.Url) { UseShellExecute = true });
            }
            catch (Exception error) { status.Text = error.Message; }
        };

        install.Click += async (_, _) =>
        {
            if (selector.SelectedItem is not AssetPackUpdateChoice choice || _assetInstallActive) return;
            var picker = new OpenFileDialog { Filter = "MechWarrior 3 packs (*.mw3pack)|*.mw3pack" };
            if (picker.ShowDialog(window) != true) return;
            _assetInstallActive = true;
            selector.IsEnabled = download.IsEnabled = install.IsEnabled = false;
            status.Text = "Checking the downloaded archive…";
            try
            {
                var order = _settingsMgr.Current.ActivePacks.ToList();
                var progress = new Progress<PackInstallProgress>(value =>
                    status.Text = value.TotalBytes > 0 ? $"{value.Stage} · {value.Percent:F0}%" : value.Stage);
                var pack = await Task.Run(() => service.InstallDownloaded(choice.Release.Id, picker.FileName, progress));
                _packMgr.RefreshPacks(order);
                RefreshPackLibrary();
                UpdateSummaryDisplay();
                TxtAssetUpdateAvailability.Text = "";
                status.Text = $"Updated {pack.Name} to {pack.Version}.";
                selector.ItemsSource = options.Where(item => item.Release.Id != choice.Release.Id).ToArray();
                selector.SelectedIndex = 0;
            }
            catch (Exception error) { status.Text = error.Message; }
            finally
            {
                _assetInstallActive = false;
                _assetInstallSequence++;
                selector.IsEnabled = download.IsEnabled = install.IsEnabled = selector.SelectedIndex >= 0;
                ValidateGamePath();
            }
        };
        window.ShowDialog();
    }

    private sealed record AssetPackUpdateChoice(AssetPackRelease Release, string Label);

    private void StopAssetPackUpdateChecks()
    {
        _assetUpdateTimer?.Stop();
        _assetUpdateCancellation?.Cancel();
    }
}
