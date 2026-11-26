using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Media;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>
/// Modal AI Arena setup and match-runner dialog. Uses the game's own <c>--arena-catalog</c>
/// lists, validates saved <c>*.ccarena.json</c> files, runs matches through <see cref="NativeGameRunner"/>,
/// and launches 3D replays of completed match logs.
/// </summary>
public partial class ArenaWindow : Window
{
    public sealed record TimeOfDayChoice(string? Value, string Label);

    /// <summary>
    /// View-model for a single bot row in Side A or Side B. Changing <see cref="SelectedMech"/>
    /// refreshes <see cref="AvailableLoadouts"/> so only stock loadouts for that chassis can be picked.
    /// </summary>
    public sealed class BotRowViewModel : INotifyPropertyChanged
    {
        private ArenaCatalogMech? _selectedMech;
        private ArenaCatalogLoadout? _selectedLoadout;
        private ArenaCatalogPreset? _selectedPreset;
        private bool _canRemove = true;

        public IReadOnlyList<ArenaCatalogMech> AvailableMechs { get; }
        public ObservableCollection<ArenaCatalogLoadout> AvailableLoadouts { get; } = new();
        public IReadOnlyList<ArenaCatalogPreset> AvailablePresets { get; }

        public event PropertyChangedEventHandler? PropertyChanged;

        public BotRowViewModel(
            IReadOnlyList<ArenaCatalogMech> mechs,
            IReadOnlyList<ArenaCatalogPreset> presets,
            ArenaCatalogMech? initialMech,
            int initialLoadoutIndex,
            ArenaCatalogPreset? initialPreset)
        {
            AvailableMechs = mechs;
            AvailablePresets = presets;

            _selectedMech = initialMech ?? mechs.FirstOrDefault();
            RebuildLoadouts(initialLoadoutIndex);
            _selectedPreset = initialPreset ?? presets.FirstOrDefault();
        }

        public ArenaCatalogMech? SelectedMech
        {
            get => _selectedMech;
            set
            {
                if (ReferenceEquals(_selectedMech, value))
                    return;
                _selectedMech = value;
                OnPropertyChanged(nameof(SelectedMech));
                RebuildLoadouts(0);
            }
        }

        public ArenaCatalogLoadout? SelectedLoadout
        {
            get => _selectedLoadout;
            set
            {
                if (ReferenceEquals(_selectedLoadout, value))
                    return;
                _selectedLoadout = value;
                OnPropertyChanged(nameof(SelectedLoadout));
            }
        }

        public ArenaCatalogPreset? SelectedPreset
        {
            get => _selectedPreset;
            set
            {
                if (ReferenceEquals(_selectedPreset, value))
                    return;
                _selectedPreset = value;
                OnPropertyChanged(nameof(SelectedPreset));
            }
        }

        public bool CanRemove
        {
            get => _canRemove;
            set
            {
                if (_canRemove == value)
                    return;
                _canRemove = value;
                OnPropertyChanged(nameof(CanRemove));
            }
        }

        private void RebuildLoadouts(int preferredIndex)
        {
            AvailableLoadouts.Clear();
            if (_selectedMech != null)
            {
                foreach (var loadout in _selectedMech.Loadouts)
                {
                    AvailableLoadouts.Add(loadout);
                }
            }

            SelectedLoadout = AvailableLoadouts.FirstOrDefault(item => item.Index == preferredIndex)
                ?? AvailableLoadouts.FirstOrDefault();
        }

        private void OnPropertyChanged(string propertyName) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    private readonly LauncherSettings _settings;
    private readonly IReadOnlyList<string> _activeModDirs;
    private readonly string _dataRoot;
    private readonly NativeGameRunner _runner;
    private readonly ObservableCollection<BotRowViewModel> _sideARows = new();
    private readonly ObservableCollection<BotRowViewModel> _sideBRows = new();

    private ArenaCatalog? _catalog;
    private bool _matchOrReplayActive;
    private string? _lastRunFolder;
    private string? _lastMatchLogPath;
    private string? _lastCommandLine;

    public ArenaWindow(
        LauncherSettings settings,
        IReadOnlyList<string> activeModDirs,
        string dataRoot,
        NativeGameRunner runner)
    {
        _settings = settings ?? throw new ArgumentNullException(nameof(settings));
        _activeModDirs = activeModDirs ?? throw new ArgumentNullException(nameof(activeModDirs));
        _dataRoot = dataRoot ?? throw new ArgumentNullException(nameof(dataRoot));
        _runner = runner ?? throw new ArgumentNullException(nameof(runner));

        InitializeComponent();

        ItemsSideA.ItemsSource = _sideARows;
        ItemsSideB.ItemsSource = _sideBRows;
        TxtLogsFolder.Text = ArenaMatchRunner.DefaultLogsRoot(_dataRoot);

        UpdateGraphicsSummary();
        Loaded += ArenaWindow_Loaded;
    }

    private async void ArenaWindow_Loaded(object sender, RoutedEventArgs e)
    {
        await LoadCatalogAsync();
    }

    private async Task LoadCatalogAsync()
    {
        SetEditingEnabled(false);
        BtnStartMatch.IsEnabled = false;
        SetStatus("Loading AI Arena catalog from MW3-RE…", isError: false);

        try
        {
            var catalog = await Task.Run(() => ArenaCatalog.EnsureCatalogAsync(_runner, _settings.GamePath, _dataRoot));
            if (catalog.Maps.Count == 0 || catalog.Mechs.Count == 0 || catalog.Presets.Count == 0)
            {
                throw new InvalidDataException("The game's arena catalog is missing maps, mechs or pilot presets.");
            }

            _catalog = catalog;
            PopulateCatalogControls(catalog);
            SetEditingEnabled(true);
            BtnStartMatch.IsEnabled = true;
            SetStatus($"Ready — {catalog.Maps.Count} arena maps, {catalog.Mechs.Count} mechs, {catalog.Presets.Count} pilot presets.", isError: false);
        }
        catch (Exception error)
        {
            _catalog = null;
            SetEditingEnabled(false);
            BtnStartMatch.IsEnabled = false;
            SetStatus("Arena catalog unavailable: " + error.Message, isError: true);
        }
    }

    private void PopulateCatalogControls(ArenaCatalog catalog)
    {
        ComboMap.ItemsSource = catalog.Maps;
        ComboMap.SelectedItem = catalog.Maps.FirstOrDefault(map => map.Id == "c1mp1") ?? catalog.Maps[0];

        var timeChoices = new List<TimeOfDayChoice> { new(null, "Map default") };
        foreach (var option in catalog.TimeOfDayOptions)
        {
            timeChoices.Add(new TimeOfDayChoice(option, option));
        }
        ComboTimeOfDay.ItemsSource = timeChoices;
        ComboTimeOfDay.SelectedIndex = 0;

        var hasTimeOfDay = catalog.TimeOfDayOptions.Count > 0;
        ComboTimeOfDay.IsEnabled = hasTimeOfDay;
        ComboTimeOfDay.ToolTip = hasTimeOfDay ? null : "Needs a newer game runtime";
        TxtTimeOfDayHint.Visibility = hasTimeOfDay ? Visibility.Collapsed : Visibility.Visible;

        _sideARows.Clear();
        _sideBRows.Clear();

        var defaultMechA = catalog.FindMech("madcat") ?? catalog.Mechs[0];
        var defaultMechB = catalog.FindMech("thor") ?? defaultMechA;
        var defaultPreset = catalog.Presets.FirstOrDefault(p =>
            p.World == "c1" && p.Mission == "ia1" && p.Record == "Enemy_01") ?? catalog.Presets[0];

        _sideARows.Add(CreateBotRow(catalog, defaultMechA, 0, defaultPreset));
        _sideBRows.Add(CreateBotRow(catalog, defaultMechB, 0, defaultPreset));
        UpdateSideCountsAndButtons();
    }

    private BotRowViewModel CreateBotRow(
        ArenaCatalog catalog,
        ArenaCatalogMech? mech,
        int loadoutIndex,
        ArenaCatalogPreset? preset)
    {
        return new BotRowViewModel(
            catalog.Mechs,
            catalog.Presets,
            mech,
            loadoutIndex,
            preset);
    }

    private void UpdateSideCountsAndButtons()
    {
        TxtCountSideA.Text = $"({_sideARows.Count} / {ArenaSetup.MaxBotsPerSide})";
        TxtCountSideB.Text = $"({_sideBRows.Count} / {ArenaSetup.MaxBotsPerSide})";

        var canEdit = !_matchOrReplayActive && _catalog != null;
        BtnAddSideA.IsEnabled = canEdit && _sideARows.Count < ArenaSetup.MaxBotsPerSide;
        BtnAddSideB.IsEnabled = canEdit && _sideBRows.Count < ArenaSetup.MaxBotsPerSide;

        var canRemoveA = _sideARows.Count > ArenaSetup.MinBotsPerSide;
        foreach (var row in _sideARows)
            row.CanRemove = canRemoveA;

        var canRemoveB = _sideBRows.Count > ArenaSetup.MinBotsPerSide;
        foreach (var row in _sideBRows)
            row.CanRemove = canRemoveB;
    }

    private void BtnAddSideA_Click(object sender, RoutedEventArgs e)
    {
        if (_catalog == null || _sideARows.Count >= ArenaSetup.MaxBotsPerSide)
            return;
        var template = _sideARows.LastOrDefault();
        _sideARows.Add(CreateBotRow(
            _catalog,
            template?.SelectedMech,
            template?.SelectedLoadout?.Index ?? 0,
            template?.SelectedPreset));
        UpdateSideCountsAndButtons();
    }

    private void BtnAddSideB_Click(object sender, RoutedEventArgs e)
    {
        if (_catalog == null || _sideBRows.Count >= ArenaSetup.MaxBotsPerSide)
            return;
        var template = _sideBRows.LastOrDefault();
        _sideBRows.Add(CreateBotRow(
            _catalog,
            template?.SelectedMech,
            template?.SelectedLoadout?.Index ?? 0,
            template?.SelectedPreset));
        UpdateSideCountsAndButtons();
    }

    private void BtnRemoveSideA_Click(object sender, RoutedEventArgs e)
    {
        if (_sideARows.Count <= ArenaSetup.MinBotsPerSide)
            return;
        if (sender is FrameworkElement { Tag: BotRowViewModel row })
        {
            _sideARows.Remove(row);
            UpdateSideCountsAndButtons();
        }
    }

    private void BtnRemoveSideB_Click(object sender, RoutedEventArgs e)
    {
        if (_sideBRows.Count <= ArenaSetup.MinBotsPerSide)
            return;
        if (sender is FrameworkElement { Tag: BotRowViewModel row })
        {
            _sideBRows.Remove(row);
            UpdateSideCountsAndButtons();
        }
    }

    private void ChkRandomSeed_Changed(object sender, RoutedEventArgs e)
    {
        if (TxtSeed == null)
            return;
        TxtSeed.IsEnabled = ChkRandomSeed.IsChecked != true;
    }

    private void ExecutionMode_Changed(object sender, RoutedEventArgs e)
    {
        UpdateGraphicsSummary();
    }

    private void UpdateGraphicsSummary()
    {
        if (TxtGraphicsSummary == null)
            return;
        var hidden = RadioRunHidden?.IsChecked == true;
        try
        {
            TxtGraphicsSummary.Text = ArenaMatchRunner.FormatGraphicsSummary(_settings, _activeModDirs, hidden);
        }
        catch (Exception error)
        {
            TxtGraphicsSummary.Text = "Graphics setting problem: " + error.Message;
        }
    }

    private void BtnBrowseLogsFolder_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFolderDialog
        {
            Title = "Choose where AI Arena match logs and setup files are written"
        };
        if (Directory.Exists(TxtLogsFolder.Text.Trim()))
            dialog.InitialDirectory = TxtLogsFolder.Text.Trim();
        if (dialog.ShowDialog(this) == true)
            TxtLogsFolder.Text = dialog.FolderName;
    }

    private void BtnDefaultLogsFolder_Click(object sender, RoutedEventArgs e)
    {
        TxtLogsFolder.Text = ArenaMatchRunner.DefaultLogsRoot(_dataRoot);
    }

    private ArenaSetup ReadSetupFromUi()
    {
        if (ComboMap.SelectedItem is not ArenaCatalogMap selectedMap)
            throw new ArenaSetupException("arena.map", "choose an arena map");

        if (!int.TryParse(TxtMinutes.Text.Trim(), out var minutes) ||
            minutes < ArenaSetup.MinMinutes || minutes > ArenaSetup.MaxMinutes)
        {
            throw new ArenaSetupException("arena.minutes", $"enter a whole number of minutes from {ArenaSetup.MinMinutes} to {ArenaSetup.MaxMinutes}");
        }

        if (!int.TryParse(TxtSeed.Text.Trim(), out var seed) || seed < ArenaSetup.MinSeed)
        {
            throw new ArenaSetupException("seed", $"enter a whole number from {ArenaSetup.MinSeed} to {ArenaSetup.MaxSeed}");
        }

        List<ArenaBotSetup> BuildSide(ObservableCollection<BotRowViewModel> rows, int sideIndex)
        {
            var bots = new List<ArenaBotSetup>(rows.Count);
            for (var i = 0; i < rows.Count; i++)
            {
                var row = rows[i];
                var path = $"arena.sides[{sideIndex}][{i}]";
                if (row.SelectedMech == null)
                    throw new ArenaSetupException($"{path}.mech", "choose a mech chassis");
                if (row.SelectedLoadout == null)
                    throw new ArenaSetupException($"{path}.loadout", "choose a stock loadout");
                if (row.SelectedPreset == null)
                    throw new ArenaSetupException($"{path}.preset", "choose a pilot preset");

                bots.Add(new ArenaBotSetup(
                    row.SelectedMech.Id,
                    row.SelectedLoadout.Index,
                    new ArenaPresetRef(row.SelectedPreset.World, row.SelectedPreset.Mission, row.SelectedPreset.Record)));
            }
            return bots;
        }

        var timeChoice = ComboTimeOfDay.SelectedItem as TimeOfDayChoice;
        var setup = new ArenaSetup
        {
            Map = selectedMap.Id,
            Minutes = minutes,
            Sides = new List<List<ArenaBotSetup>>
            {
                BuildSide(_sideARows, 0),
                BuildSide(_sideBRows, 1)
            },
            Seed = seed,
            RandomSeed = ChkRandomSeed.IsChecked == true,
            FrameMs = ArenaSetup.FixedFrameMs,
            Hidden = RadioRunHidden.IsChecked == true,
            TimeOfDay = timeChoice?.Value
        };

        if (_catalog != null)
            setup.ValidateAgainst(_catalog);
        else
            setup.Validate();

        return setup;
    }

    private void ApplySetupToUi(ArenaSetup setup)
    {
        if (_catalog == null)
            return;

        ComboMap.SelectedItem = _catalog.Maps.FirstOrDefault(map => map.Id == setup.Map);
        TxtMinutes.Text = setup.Minutes.ToString();
        TxtSeed.Text = setup.Seed.ToString();
        ChkRandomSeed.IsChecked = setup.RandomSeed;
        TxtSeed.IsEnabled = !setup.RandomSeed;
        RadioRunHidden.IsChecked = setup.Hidden;
        RadioWatchMatch.IsChecked = !setup.Hidden;

        if (ComboTimeOfDay.ItemsSource is IEnumerable<TimeOfDayChoice> choices)
        {
            ComboTimeOfDay.SelectedItem = choices.FirstOrDefault(c => c.Value == setup.TimeOfDay)
                ?? choices.FirstOrDefault();
        }

        void PopulateSide(ObservableCollection<BotRowViewModel> target, List<ArenaBotSetup> bots)
        {
            target.Clear();
            foreach (var bot in bots)
            {
                var mech = _catalog.FindMech(bot.Mech);
                var preset = _catalog.Presets.FirstOrDefault(p =>
                    p.World == bot.Preset.World &&
                    p.Mission == bot.Preset.Mission &&
                    p.Record == bot.Preset.Record);
                target.Add(CreateBotRow(_catalog, mech, bot.Loadout, preset));
            }
        }

        PopulateSide(_sideARows, setup.Sides[0]);
        PopulateSide(_sideBRows, setup.Sides[1]);
        UpdateSideCountsAndButtons();
        UpdateGraphicsSummary();
    }

    private void BtnLoadSetup_Click(object sender, RoutedEventArgs e)
    {
        if (_catalog == null || _matchOrReplayActive)
            return;

        var dialog = new OpenFileDialog
        {
            Title = "Load AI Arena setup",
            Filter = "Core Critical Arena setup (*.ccarena.json)|*.ccarena.json|JSON files (*.json)|*.json"
        };
        if (dialog.ShowDialog(this) != true)
            return;

        try
        {
            var loaded = ArenaSetupFile.Load(dialog.FileName);
            loaded.ValidateAgainst(_catalog);
            ApplySetupToUi(loaded);
            SetStatus("Loaded setup: " + Path.GetFileName(dialog.FileName), isError: false);
        }
        catch (Exception error)
        {
            MessageBox.Show(this, error.Message, "Cannot load AI Arena setup", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    private void BtnSaveSetup_Click(object sender, RoutedEventArgs e)
    {
        if (_catalog == null || _matchOrReplayActive)
            return;

        ArenaSetup setup;
        try
        {
            setup = ReadSetupFromUi();
        }
        catch (Exception error)
        {
            MessageBox.Show(this, error.Message, "Invalid AI Arena setup", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dialog = new SaveFileDialog
        {
            Title = "Save AI Arena setup",
            Filter = "Core Critical Arena setup (*.ccarena.json)|*.ccarena.json",
            FileName = $"{setup.Map}-{setup.Sides[0].Count}v{setup.Sides[1].Count}.ccarena.json",
            DefaultExt = ".ccarena.json"
        };
        if (dialog.ShowDialog(this) != true)
            return;

        try
        {
            ArenaSetupFile.Save(dialog.FileName, setup);
            SetStatus("Saved setup: " + Path.GetFileName(dialog.FileName), isError: false);
        }
        catch (Exception error)
        {
            MessageBox.Show(this, error.Message, "Cannot save AI Arena setup", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private async void BtnStartMatch_Click(object sender, RoutedEventArgs e)
    {
        if (_catalog == null || _matchOrReplayActive)
            return;

        ArenaSetup setupSnapshot;
        int resolvedSeed;
        string logsRoot;
        try
        {
            var currentSetup = ReadSetupFromUi();
            resolvedSeed = currentSetup.ResolveSeedForRun();
            setupSnapshot = currentSetup.Clone();
            logsRoot = TxtLogsFolder.Text.Trim();
            if (string.IsNullOrWhiteSpace(logsRoot))
                throw new InvalidOperationException("Choose a folder where match logs will be saved.");
        }
        catch (Exception error)
        {
            MessageBox.Show(this, error.Message, "Cannot start AI Arena match", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        ClearResultActions();
        _matchOrReplayActive = true;
        SetEditingEnabled(false);
        BtnStartMatch.IsEnabled = false;
        BtnStartMatch.Content = "●  MATCH RUNNING…";

        var modeWord = setupSnapshot.Hidden ? "hidden" : "watched";
        SetStatus($"Running {modeWord} match on {setupSnapshot.Map} (seed {resolvedSeed})…", isError: false);

        try
        {
            var outcome = await ArenaMatchRunner.RunMatchAsync(
                _runner,
                _settings,
                _activeModDirs,
                setupSnapshot,
                resolvedSeed,
                logsRoot,
                _dataRoot,
                onProgressLine: line =>
                {
                    if (line.StartsWith("Startup: ", StringComparison.Ordinal) ||
                        line.StartsWith("mw3: arena on ", StringComparison.Ordinal))
                    {
                        Dispatcher.BeginInvoke(() =>
                        {
                            if (_matchOrReplayActive)
                                SetStatus($"Running {modeWord} match (seed {resolvedSeed}) — {line}", isError: false);
                        });
                    }
                },
                onProcessStarted: (_, commandLine) =>
                {
                    Dispatcher.BeginInvoke(() =>
                    {
                        _lastCommandLine = commandLine;
                        BtnCopyCommand.IsEnabled = true;
                    });
                });

            _lastRunFolder = outcome.RunFolder;
            _lastMatchLogPath = outcome.ExpectedLogPath;
            _lastCommandLine = outcome.CommandLine;

            BtnOpenRunFolder.IsEnabled = Directory.Exists(outcome.RunFolder);
            BtnCopyCommand.IsEnabled = !string.IsNullOrWhiteSpace(outcome.CommandLine);
            BtnWatchReplay3d.IsEnabled = outcome.Succeeded && File.Exists(outcome.ExpectedLogPath);

            if (outcome.Succeeded)
            {
                SetStatus(outcome.WinnerDisplayLabel, isError: false);
                TxtResultDetail.Text = $"Time: {outcome.TimeText} · Mechs lost: Side A {outcome.LostA}, Side B {outcome.LostB} · Seed: {outcome.ResolvedSeed}";
                TxtResultDetail.Foreground = (Brush)FindResource("BrushInk");
                TxtResultDetail.Visibility = Visibility.Visible;
            }
            else
            {
                SetStatus($"Match failed (seed {outcome.ResolvedSeed})", isError: true);
                TxtResultDetail.Text = outcome.ErrorMessage ?? $"Exit code {outcome.ExitCode}";
                TxtResultDetail.Foreground = Brushes.LightCoral;
                TxtResultDetail.Visibility = Visibility.Visible;
            }

            TxtLogPath.Text = "Match log: " + outcome.ExpectedLogPath;
            TxtLogPath.Visibility = Visibility.Visible;
        }
        catch (Exception error)
        {
            SetStatus("Match could not start: " + error.Message, isError: true);
            TxtResultDetail.Text = error.Message;
            TxtResultDetail.Foreground = Brushes.LightCoral;
            TxtResultDetail.Visibility = Visibility.Visible;
        }
        finally
        {
            _matchOrReplayActive = false;
            SetEditingEnabled(_catalog != null);
            BtnStartMatch.Content = "▶  START MATCH";
            BtnStartMatch.IsEnabled = _catalog != null;
            UpdateSideCountsAndButtons();
        }
    }

    private void BtnOpenRunFolder_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_lastRunFolder) || !Directory.Exists(_lastRunFolder))
            return;
        try
        {
            Process.Start(new ProcessStartInfo { FileName = _lastRunFolder, UseShellExecute = true });
        }
        catch (Exception error)
        {
            MessageBox.Show(this, error.Message, "Cannot open folder", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private async void BtnWatchReplay3d_Click(object sender, RoutedEventArgs e)
    {
        if (_matchOrReplayActive || string.IsNullOrWhiteSpace(_lastMatchLogPath) || !File.Exists(_lastMatchLogPath))
            return;

        var logPath = _lastMatchLogPath;
        _matchOrReplayActive = true;
        SetEditingEnabled(false);
        BtnStartMatch.IsEnabled = false;
        BtnWatchReplay3d.IsEnabled = false;
        SetStatus("Starting 3D replay for " + Path.GetFileName(logPath) + "…", isError: false);

        try
        {
            var extraArgs = ArenaMatchRunner.BuildReplay3dArguments(logPath);
            using var process = await Task.Run(() => _runner.Launch(_settings, _activeModDirs, null, extraArgs));
            SetStatus("Watching 3D replay (" + Path.GetFileName(logPath) + ")…", isError: false);
            var exitCode = _runner.LastSessionCompletion != null
                ? await _runner.LastSessionCompletion
                : await GameRunner.WaitForCompletionAsync(process);

            if (exitCode != 0)
            {
                SetStatus($"3D replay exited with code {exitCode}.", isError: true);
            }
            else
            {
                SetStatus("3D replay finished.", isError: false);
            }
        }
        catch (Exception error)
        {
            SetStatus("Could not start 3D replay: " + error.Message, isError: true);
            MessageBox.Show(this, error.Message, "Cannot watch 3D replay", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            _matchOrReplayActive = false;
            SetEditingEnabled(_catalog != null);
            BtnStartMatch.IsEnabled = _catalog != null;
            BtnWatchReplay3d.IsEnabled = File.Exists(logPath);
            UpdateSideCountsAndButtons();
        }
    }

    private void BtnCopyCommand_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_lastCommandLine))
            return;
        try
        {
            Clipboard.SetText(_lastCommandLine);
            SetStatus("Copied full match command line to clipboard.", isError: false);
        }
        catch (Exception error)
        {
            MessageBox.Show(this, error.Message, "Cannot copy command", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void ClearResultActions()
    {
        _lastRunFolder = null;
        _lastMatchLogPath = null;
        _lastCommandLine = null;
        BtnOpenRunFolder.IsEnabled = false;
        BtnWatchReplay3d.IsEnabled = false;
        BtnCopyCommand.IsEnabled = false;
        TxtResultDetail.Text = "";
        TxtResultDetail.Visibility = Visibility.Collapsed;
        TxtLogPath.Text = "";
        TxtLogPath.Visibility = Visibility.Collapsed;
    }

    private void SetEditingEnabled(bool enabled)
    {
        PanelMatchHeader.IsEnabled = enabled;
        PanelSides.IsEnabled = enabled;
        PanelRunOptions.IsEnabled = enabled;
        BtnLoadSetup.IsEnabled = enabled;
        BtnSaveSetup.IsEnabled = enabled;
        BtnClose.IsEnabled = !_matchOrReplayActive;
    }

    private void SetStatus(string message, bool isError)
    {
        TxtStatus.Text = message;
        TxtStatus.Foreground = isError
            ? Brushes.LightCoral
            : (Brush)FindResource("BrushAmber");
    }

    private void BtnClose_Click(object sender, RoutedEventArgs e)
    {
        if (_matchOrReplayActive)
            return;
        Close();
    }

    private void ArenaWindow_Closing(object? sender, CancelEventArgs e)
    {
        // Prevent closing while a match or 3D replay process is active so output callbacks
        // and session gate disposal never race a disposed window or leave an orphaned session.
        if (_matchOrReplayActive)
        {
            e.Cancel = true;
            MessageBox.Show(
                this,
                "Wait for the active AI Arena match or replay to finish before closing this window.",
                "AI Arena match active",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }
    }
}
