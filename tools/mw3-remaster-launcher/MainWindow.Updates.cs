using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Threading;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public partial class MainWindow
{
    private DispatcherTimer? _updateNotificationTimer;
    private CancellationTokenSource? _updateNotificationCancellation;
    private Task? _updateNotificationCheck;
    private bool _onlineUpdatesOpen;
    private bool _updateNotificationsClosed;

    private void StartUpdateNotifications()
    {
        if (_updateNotificationsClosed || !_settingsMgr.Current.AutomaticUpdateChecks ||
            !File.Exists(Path.Combine(_basePath, "online-updates.json"))) return;
        if (_updateNotificationTimer == null)
        {
            _updateNotificationTimer = new DispatcherTimer { Interval = TimeSpan.FromMinutes(30) };
            _updateNotificationTimer.Tick += async (_, _) => await RefreshUpdateNotificationAsync();
        }
        _updateNotificationTimer.Start();
        _ = RefreshUpdateNotificationAsync();
    }

    private void AutomaticUpdateChecks_Changed(object sender, RoutedEventArgs e)
    {
        if (_isInitializing) return;
        _settingsMgr.Current.AutomaticUpdateChecks = ChkAutomaticUpdateChecks.IsChecked == true;
        _settingsMgr.Save();
        ApplyUpdateNotificationPreference();
    }

    private void AutomaticCrashReports_Changed(object sender, RoutedEventArgs e)
    {
        if (_isInitializing) return;
        _settingsMgr.Current.AutomaticCrashReports = ChkAutomaticCrashReports.IsChecked == true;
        _settingsMgr.Save();
    }

    private void ApplyUpdateNotificationPreference()
    {
        if (_settingsMgr.Current.AutomaticUpdateChecks) StartUpdateNotifications();
        else
        {
            _updateNotificationTimer?.Stop();
            _updateNotificationCancellation?.Cancel();
            UpdateNotification.Visibility = Visibility.Collapsed;
        }
    }

    private async Task RefreshUpdateNotificationAsync()
    {
        if (_updateNotificationsClosed || !_settingsMgr.Current.AutomaticUpdateChecks || _onlineUpdatesOpen || _updateNotificationCheck != null ||
            _nativeSessionActive || _assetInstallActive || _launchPreparing) return;
        _updateNotificationCheck = CheckUpdateNotificationAsync();
        try { await _updateNotificationCheck; }
        finally { _updateNotificationCheck = null; }
    }

    private async Task CheckUpdateNotificationAsync()
    {
        using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        _updateNotificationCancellation = cancellation;
        // Snapshot UI-owned settings before doing signature/network/file checks off-thread.
        var game = _settingsMgr.Current.GamePath;
        try
        {
            var result = await Task.Run(async () =>
            {
                using var service = new OnlineUpdateService(_basePath, game, _dataRoot);
                await service.CheckAsync(cancellation.Token);
                return (Updates: service.Available.ToArray(), Pending: service.HasPending);
            }, cancellation.Token);
            if (_updateNotificationsClosed || !_settingsMgr.Current.AutomaticUpdateChecks || _onlineUpdatesOpen) return;
            ShowUpdateNotification(result.Updates, result.Pending);
        }
        catch (OperationCanceledException) { }
        catch (Exception error)
        {
            // Offline, invalid-feed and busy-workflow failures never block playing or
            // erase the last verified notice. The manual updater shows detailed errors.
            Debug.WriteLine("Background update check: " + error.Message);
        }
        finally { _updateNotificationCancellation = null; }
    }

    private void ShowUpdateNotification(IReadOnlyList<PlannedOnlineUpdate> updates, bool pending)
    {
        UpdateNotification.Visibility = updates.Count > 0 || pending ? Visibility.Visible : Visibility.Collapsed;
        TxtUpdateNotificationTitle.Text = updates.Count > 0 ? "Updates available" : "Resume your update";
        TxtUpdateNotificationDetails.Text = updates.Count > 0
            ? string.Join(" · ", updates.Select(update =>
                (update.Release.ProductId == GameCatalog.LauncherId ? "Core Critical" : GameCatalog.Get(update.Release.ProductId).Name + " runtime")
                + " " + update.Release.DisplayVersion))
            : "An unfinished update is saved. Open updates to continue.";
    }

    private async Task OpenOnlineUpdatesAsync()
    {
        if (_onlineUpdatesOpen || _updateNotificationsClosed) return;
        _onlineUpdatesOpen = true;
        try
        {
            // Release the background service's workflow lock before the manual updater
            // checks/downloads/installs. Cancellation alone does not release that lock.
            _updateNotificationCancellation?.Cancel();
            if (_updateNotificationCheck != null) await _updateNotificationCheck;
            if (_updateNotificationsClosed) return;
            new OnlineUpdatesWindow(_basePath, _settingsMgr.Current.GamePath) { Owner = this }.ShowDialog();
        }
        catch (Exception error) { MessageBox.Show(this, error.Message, "Core Critical updates"); }
        finally { _onlineUpdatesOpen = false; }
        if (!_updateNotificationsClosed)
        {
            ValidateGamePath();
            await RefreshUpdateNotificationAsync();
        }
    }

    protected override void OnClosed(EventArgs e)
    {
        _updateNotificationsClosed = true;
        _updateNotificationTimer?.Stop();
        _updateNotificationCancellation?.Cancel();
        base.OnClosed(e);
    }
}
