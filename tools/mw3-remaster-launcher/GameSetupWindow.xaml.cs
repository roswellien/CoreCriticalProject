using System.IO;
using System.Windows;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Shared setup flow for post-install launch and the launcher's Set Up Game action.</summary>
public partial class GameSetupWindow : Window
{
    public string? GameDirectory { get; private set; }
    public string[] SelectedPacks { get; private set; } = Array.Empty<string>();
    private bool _busy;
    private CancellationTokenSource? _nativePreparation;
    private string? _verifiedDirectory;

    public GameSetupWindow(string? existingPath)
    {
        InitializeComponent();
        ExistingPath.Text = existingPath ?? GameValidator.AutoDetectGameDirectory() ?? "";
        DestinationPath.Text = Path.Combine(LauncherPaths.DataRoot, "OriginalGame");
        if (BundledPreparation.IsAvailable(AppContext.BaseDirectory))
            PreparationNote.Text = "After verifying your files, setup prepares the native game. First-time preparation can take a while. You can cancel and resume it.";
        Closing += (_, e) =>
        {
            if (!_busy) return;
            e.Cancel = true;
            _nativePreparation?.Cancel();
        };
    }

    private void SourceChanged(object sender, RoutedEventArgs e)
    {
        if (MediaPanel == null) return;
        var fromMedia = MediaChoice.IsChecked == true;
        ExistingPanel.Visibility = fromMedia ? Visibility.Collapsed : Visibility.Visible;
        MediaPanel.Visibility = fromMedia ? Visibility.Visible : Visibility.Collapsed;
        ContinueButton.Content = fromMedia ? "Install and verify" : "Verify and use folder";
    }

    private void BrowseExisting(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFolderDialog { Title = "Select your original MW3 installation" };
        if (dialog.ShowDialog(this) == true) ExistingPath.Text = dialog.FolderName;
    }
    private void BrowseIso(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Title = "Select your MW3 ISO", Filter = "ISO image|*.iso" };
        if (dialog.ShowDialog(this) == true) IsoPath.Text = dialog.FileName;
    }
    private void BrowsePatch(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Title = "Select your English 1.2 patch", Filter = "MW3 patch|mw3v12.exe|Executable|*.exe" };
        if (dialog.ShowDialog(this) == true) PatchPath.Text = dialog.FileName;
    }
    private void BrowseDestination(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFolderDialog { Title = "Choose the parent folder for a new MW3-Original folder" };
        if (dialog.ShowDialog(this) == true) DestinationPath.Text = Path.Combine(dialog.FolderName, "MW3-Original");
    }
    private void CancelSetup(object sender, RoutedEventArgs e)
    {
        if (_busy && _nativePreparation != null)
        {
            _nativePreparation.Cancel();
            CancelButton.IsEnabled = false;
            Status.Text = "Stopping preparation. Your original files will be kept…";
            return;
        }
        DialogResult = false;
    }

    private void BrowsePacks(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Title = "Choose optional content packs", Filter = "MW3 packs|*.mw3pack;*.zip", Multiselect = true };
        if (dialog.ShowDialog(this) != true) return;
        SelectedPacks = dialog.FileNames;
        PackSelection.Text = string.Join(Environment.NewLine, SelectedPacks.Select(Path.GetFileName));
    }

    private void ClearPacks(object sender, RoutedEventArgs e)
    {
        SelectedPacks = Array.Empty<string>();
        PackSelection.Text = "No optional packs selected.";
    }

    private async void ContinueSetup(object sender, RoutedEventArgs e)
    {
        var fromMedia = MediaChoice.IsChecked == true;
        var directory = fromMedia ? DestinationPath.Text.Trim() : ExistingPath.Text.Trim();
        var iso = IsoPath.Text.Trim();
        var patch = PatchPath.Text.Trim();
        if (string.IsNullOrWhiteSpace(directory)) { Status.Text = "Select a game-data folder."; return; }
        if (fromMedia && (!File.Exists(iso) || !File.Exists(patch)))
        { Status.Text = "Select both your ISO image and your 1.2 patch file."; return; }
        _busy = true;
        ExistingPanel.IsEnabled = MediaPanel.IsEnabled = false;
        PackPanel.IsEnabled = false;
        ExistingChoice.IsEnabled = MediaChoice.IsEnabled = false;
        ContinueButton.IsEnabled = CancelButton.IsEnabled = false;
        Progress.Visibility = Visibility.Visible;
        try
        {
            void Report(string text, double fraction) => Dispatcher.Invoke(() => {
                Status.Text = text; Progress.Value = fraction * 100;
            });
            if (fromMedia && _verifiedDirectory != Path.GetFullPath(directory))
                await GameInstallation.InstallIsoAsync(iso, patch, directory,
                    Path.Combine(AppContext.BaseDirectory, "Tools", "Unshield"), Report);
            else
            {
                await GameInstallation.VerifyExistingAsync(directory, Report);
                if (NativeRuntimeLayout.IsInstalledApplication(AppContext.BaseDirectory) &&
                    GameInstallation.FindSupportFiles(directory, LauncherPaths.DataRoot) == null)
                {
                    var supportIso = new OpenFileDialog {
                        Title = "Select your MW3 ISO to import required support files (your installation stays unchanged)",
                        Filter = "ISO image|*.iso"
                    };
                    if (supportIso.ShowDialog(this) != true)
                        throw new InvalidOperationException("Original files verified. Select your ISO to finish importing the required support files.");
                    await GameInstallation.ImportProviderIsoAsync(supportIso.FileName, LauncherPaths.DataRoot,
                        Path.Combine(AppContext.BaseDirectory, "Tools", "Unshield"), Report);
                }
            }
            if (GameInstallation.FindSupportFiles(directory, LauncherPaths.DataRoot) != null)
                await Task.Run(() => GameInstallation.PrepareSupportFiles(directory, LauncherPaths.DataRoot));
            _verifiedDirectory = Path.GetFullPath(directory);
            if (BundledPreparation.IsAvailable(AppContext.BaseDirectory))
            {
                _nativePreparation = new CancellationTokenSource();
                CancelButton.Content = "Cancel preparation";
                CancelButton.IsEnabled = true;
                Progress.IsIndeterminate = true;
                var progress = new Progress<string>(message => Status.Text = message);
                await Task.Run(() => BundledPreparation.PrepareAsync(AppContext.BaseDirectory, directory, progress,
                    _nativePreparation.Token));
            }
            GameDirectory = Path.GetFullPath(directory);
            _busy = false;
            DialogResult = true;
        }
        catch (OperationCanceledException) { Status.Text = "Preparation stopped. Continue to resume it; your original files were kept."; }
        catch (Exception error) { Status.Text = error.Message; }
        finally
        {
            _busy = false;
            _nativePreparation?.Dispose();
            _nativePreparation = null;
            ExistingPanel.IsEnabled = MediaPanel.IsEnabled = true;
            PackPanel.IsEnabled = true;
            ExistingChoice.IsEnabled = MediaChoice.IsEnabled = true;
            ContinueButton.IsEnabled = CancelButton.IsEnabled = true;
            CancelButton.Content = "Later";
            Progress.IsIndeterminate = false;
            Progress.Visibility = Visibility.Collapsed;
        }
    }
}
