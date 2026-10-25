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
    public GraphicsPreferences? SelectedGraphics { get; private set; }
    private bool _busy;
    private CancellationTokenSource? _nativePreparation;
    private string? _verifiedDirectory;
    private readonly string _dataRoot;
    private int _step;

    public GameSetupWindow(string? existingPath, LauncherSettings? settings = null, string? dataRoot = null)
    {
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
        InitializeComponent();
        SetupGraphics.Load(settings ?? new LauncherSettings());
        ExistingPath.Text = existingPath ?? GameValidator.AutoDetectGameDirectory() ?? "";
        DestinationPath.Text = Path.Combine(_dataRoot, "OriginalGame");
        ShowStep(0);
        if (NativeRuntimeLayout.HasPrecompiledRuntime(AppContext.BaseDirectory))
            PreparationNote.Text = "The native game is already installed. This step only installs or verifies your original game files; no game-code compilation is needed.";
        else if (BundledPreparation.IsAvailable(AppContext.BaseDirectory))
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
        if (ContinueButton != null && _step == 3) UpdateReview();
    }

    private void ShowStep(int step)
    {
        _step = step;
        GameFilesStep.Visibility = step == 0 ? Visibility.Visible : Visibility.Collapsed;
        GraphicsStep.Visibility = step == 1 ? Visibility.Visible : Visibility.Collapsed;
        PacksStep.Visibility = step == 2 ? Visibility.Visible : Visibility.Collapsed;
        ReviewStep.Visibility = step == 3 ? Visibility.Visible : Visibility.Collapsed;
        BackButton.Visibility = step == 0 ? Visibility.Collapsed : Visibility.Visible;
        StepProgress.Text = $"STEP {step + 1} OF 4 · " + new[] { "GAME FILES", "DISPLAY & GRAPHICS", "OPTIONAL PACKS", "REVIEW & INSTALL" }[step];
        ContinueButton.Content = new[] { "Next: Display & graphics", "Next: Optional packs", "Next: Review", "Start setup" }[step];
        Status.Text = "";
        if (step == 3) UpdateReview();
    }

    private void PreviousStep(object sender, RoutedEventArgs e)
    {
        if (!_busy && _step > 0) ShowStep(_step - 1);
    }

    private bool ValidateSource()
    {
        var fromMedia = MediaChoice.IsChecked == true;
        var directory = fromMedia ? DestinationPath.Text.Trim() : ExistingPath.Text.Trim();
        if (string.IsNullOrWhiteSpace(directory)) throw new InvalidOperationException("Select a game-data folder.");
        var fullPath = Path.GetFullPath(directory);
        if (fromMedia)
        {
            if (!File.Exists(IsoPath.Text.Trim()) || !File.Exists(PatchPath.Text.Trim()))
                throw new InvalidOperationException("Select both your ISO image and your 1.2 patch file.");
            if (_verifiedDirectory != fullPath && (Directory.Exists(fullPath) || File.Exists(fullPath)))
                throw new InvalidOperationException("Choose a new folder for the installed original files.");
        }
        else
        {
            var validation = GameValidator.Validate(fullPath);
            if (!validation.IsValid) throw new InvalidOperationException(validation.StatusMessage);
        }
        return true;
    }

    private void UpdateReview()
    {
        var g = SetupGraphics.Read();
        var fromMedia = MediaChoice.IsChecked == true;
        ReviewSource.Text = fromMedia
            ? $"Install from ISO: {IsoPath.Text.Trim()}\nEnglish 1.2 patch: {PatchPath.Text.Trim()}\nDestination: {DestinationPath.Text.Trim()}"
            : "Verify existing installation: " + ExistingPath.Text.Trim();
        var windowMode = g.WindowMode switch { "fullscreen_windowed" => "Borderless fullscreen", "fullscreen" => "Fullscreen exclusive", _ => "Windowed" };
        var aa = g.AntiAliasing switch { "off" or "1" => "Off", "fxaa" => "FXAA", _ => g.AntiAliasing + "x SSAA" };
        ReviewGraphics.Text = $"{g.Width} × {g.Height} · {windowMode}\nAA: {aa} · AF: {g.AnisotropicFiltering}x\nDraw distance: {g.DrawDistance}m · Fog: {(g.FogDistance == 0 ? "Original" : "1100m")}\nDynamic Lighting: {(g.DynamicLighting ? "On" : "Off")} · Shadows: {(g.Shadows && g.DynamicLighting ? "On" : "Off")}";
        ReviewPacks.Text = SelectedPacks.Length == 0 ? "None — start with stock content." : string.Join(Environment.NewLine, SelectedPacks.Select(Path.GetFileName));
        ContinueButton.Content = fromMedia ? "Install game" : "Verify and finish setup";
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
        if (_busy) return;
        if (_step < 3)
        {
            try
            {
                if (_step == 0) ValidateSource();
                if (_step == 1) SetupGraphics.Read();
                ShowStep(_step + 1);
            }
            catch (Exception error) { Status.Text = error.Message; }
            return;
        }
        try { ValidateSource(); }
        catch (Exception error) { ShowStep(0); Status.Text = error.Message; return; }
        GraphicsPreferences graphics;
        try { graphics = SetupGraphics.Read(); }
        catch (Exception error) { ShowStep(1); Status.Text = error.Message; return; }
        var fromMedia = MediaChoice.IsChecked == true;
        var directory = fromMedia ? DestinationPath.Text.Trim() : ExistingPath.Text.Trim();
        var iso = IsoPath.Text.Trim();
        var patch = PatchPath.Text.Trim();
        if (string.IsNullOrWhiteSpace(directory)) { ShowStep(0); Status.Text = "Select a game-data folder."; return; }
        if (fromMedia && (!File.Exists(iso) || !File.Exists(patch)))
        { Status.Text = "Select both your ISO image and your 1.2 patch file."; return; }
        _busy = true;
        ExistingPanel.IsEnabled = MediaPanel.IsEnabled = false;
        PackPanel.IsEnabled = false;
        SetupGraphics.IsEnabled = false;
        ExistingChoice.IsEnabled = MediaChoice.IsEnabled = false;
        ContinueButton.IsEnabled = CancelButton.IsEnabled = false;
        BackButton.IsEnabled = false;
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
                    GameInstallation.FindSupportFiles(directory, _dataRoot) == null)
                {
                    var supportIso = new OpenFileDialog {
                        Title = "Select your MW3 ISO to import required support files (your installation stays unchanged)",
                        Filter = "ISO image|*.iso"
                    };
                    if (supportIso.ShowDialog(this) != true)
                        throw new InvalidOperationException("Original files verified. Select your ISO to finish importing the required support files.");
                    await GameInstallation.ImportProviderIsoAsync(supportIso.FileName, _dataRoot,
                        Path.Combine(AppContext.BaseDirectory, "Tools", "Unshield"), Report);
                }
            }
            if (GameInstallation.FindSupportFiles(directory, _dataRoot) != null)
                await Task.Run(() => GameInstallation.PrepareSupportFiles(directory, _dataRoot));
            _verifiedDirectory = Path.GetFullPath(directory);
            if (NativeRuntimeLayout.HasPrecompiledRuntime(AppContext.BaseDirectory))
            {
                Status.Text = "Checking the installed native game…";
                await Task.Run(() => RuntimeUpdates.ValidateGeneratedRuntime(
                    Path.Combine(AppContext.BaseDirectory, "Runtime")));
            }
            else if (BundledPreparation.IsAvailable(AppContext.BaseDirectory))
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
            SelectedGraphics = graphics;
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
            SetupGraphics.IsEnabled = true;
            ExistingChoice.IsEnabled = MediaChoice.IsEnabled = true;
            ContinueButton.IsEnabled = CancelButton.IsEnabled = true;
            BackButton.IsEnabled = true;
            CancelButton.Content = "Cancel";
            Progress.IsIndeterminate = false;
            Progress.Visibility = Visibility.Collapsed;
        }
    }
}
