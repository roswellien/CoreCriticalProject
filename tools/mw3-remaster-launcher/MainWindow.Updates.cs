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

    private void CrashReportDisclosure_Click(object sender, RoutedEventArgs e)
    {
        const string disclosure =
            "Crash reports include:\n\n" +
            "Hardware: processor manufacturer and model, physical and logical core counts, installed memory total, and each memory module's capacity, type and configured speed. For graphics adapters, reports include the adapter name, dedicated video memory (VRAM), shared system memory and Windows-reported driver version and date.\n\n" +
            "System and session: report ID and UTC timestamp, Windows version, process architecture, .NET runtime, launcher and game runtime versions, engine mode, exit code, and a short failure summary.\n\n" +
            "Settings and packs: selected graphics settings and pack IDs, versions, schema versions, enabled status and priorities.\n\n" +
            "Logs: up to the last 64 KiB each from the launcher log, native standard error and native standard output, when those files exist. Local and network file paths are redacted.\n\n" +
            "The hardware inventory does not request memory serial numbers or device identifiers. Reports do not include saves, original game media, screenshots or memory dumps. Recent log text may contain diagnostic identifiers already written by the launcher or native host. Some hardware values may be unavailable or incomplete if Windows or a driver does not report them.";
        MessageBox.Show(this, disclosure, "Crash report contents", MessageBoxButton.OK, MessageBoxImage.Information);
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
