using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher
{
    public partial class MainWindow : Window
    {
        private async void WatchCinematics_Click(object sender, RoutedEventArgs e)
        {
            var button = (Button)sender;
            button.IsEnabled = false;
            try
            {
                var directories = _packMgr.GetActivePackDirectories();
                var clips = await System.Threading.Tasks.Task.Run(() => CinematicPack.Library(directories));
                if (clips.Count == 0)
                {
                    MessageBox.Show(this, "Install and enable a cinematic pack with library additions to watch them here. In-game movie replacements play at their original game triggers.", "Cinematics");
                    return;
                }
                new CinematicWindow(clips) { Owner = this }.ShowDialog();
            }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "Cannot open cinematics", MessageBoxButton.OK, MessageBoxImage.Error); }
            finally { button.IsEnabled = true; }
        }
        private readonly string _basePath;
        private void OpenModProfiles(object sender, RoutedEventArgs e)
        {
            if (_nativeSessionActive || _launchPreparing || _assetInstallActive) return;
            if (new ModProfilesWindow(_settingsMgr.Current, _dataRoot) { Owner = this }.ShowDialog() == true)
            {
                _settingsMgr.Save();
                LoadSettingsIntoUi();
                ValidateGamePath();
            }
        }
        private void OpenControls(object sender, RoutedEventArgs e)
        {
            new ControlsWindow(_dataRoot, _settingsMgr.Current.GamePath, _settingsMgr) { Owner = this }.ShowDialog();
            UpdateSummaryDisplay();
        }
        private bool _nativeSessionActive;
        private bool _assetInstallActive;
        private bool _launchPreparing;

        private void SetLaunchPreparing(bool preparing)
        {
            _launchPreparing = preparing;
            LaunchActivity.IsActive = preparing || _assetInstallActive;
        }
        private int _assetInstallSequence;
        private int _assetPackIndex;
        private int _assetPackCount;
        private readonly SettingsManager _settingsMgr;
        private readonly PackManager _packMgr;
        private readonly string _dataRoot;
        private PackManager? _libraryPackMgr;
        private readonly NativeGameRunner _nativeGameRunner;
        private readonly D7VkRunner _d7vkRunner;
        private bool _isInitializing = true;

        private static readonly Dictionary<string, string> D7VkResolutionHints = new()
        {
            ["1920x1080 (1080p Widescreen 16:9)"] = "Full HD 1080p widescreen with corrected 3D camera FOV (unstretched)",
            ["2560x1440 (1440p Widescreen 16:9)"] = "QHD 1440p widescreen with corrected 3D camera FOV (unstretched)",
            ["3440x1440 (Ultrawide 21:9)"] = "Ultrawide 21:9 with corrected 3D camera FOV (unstretched)",
            ["3840x2160 (4K Widescreen 16:9)"] = "4K UHD 2160p widescreen with corrected 3D camera FOV (unstretched)",
            ["1024x768 (Native 4:3)"] = "Native retail 4:3 presentation (pillarboxed on widescreen displays)",
            ["1440x1080 (1080p 4:3 Equivalent)"] = "1080p height in 4:3 proportions (pillarboxed on 16:9 displays)",
            ["1920x1440 (1440p 4:3 Equivalent)"] = "1440p height in 4:3 proportions (pillarboxed on 16:9 displays)",
            ["2880x2160 (4K 4:3 Equivalent)"] = "4K/2160p height in 4:3 proportions (pillarboxed on 16:9 displays)",
            ["800x600 (Legacy 4:3)"] = "Legacy 800x600 mode",
            ["640x480 (Legacy 4:3)"] = "Original default 640x480 mode"
        };

        public MainWindow() : this(null) { }

        public MainWindow(string? dataRoot)
        {
            _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
            InitializeComponent();

            _basePath = AppDomain.CurrentDomain.BaseDirectory;
            _settingsMgr = new SettingsManager(_basePath, _dataRoot);
            _packMgr = new PackManager(_dataRoot);
            CmbPackGame.ItemsSource = GameCatalog.Games;
            CmbPackGame.SelectedValue = GameCatalog.Mw3;
            _nativeGameRunner = new NativeGameRunner(_basePath, _dataRoot);
            _d7vkRunner = new D7VkRunner(_basePath, _dataRoot);

            Loaded += MainWindow_Loaded;
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            var launcherLabel = "Core Critical " + PlaytestDiagnostics.LauncherVersionString();
            TxtLauncherBuild.Text = TxtHeaderBuild.Text = launcherLabel;
            if (_settingsMgr.LoadWarning != null)
                MessageBox.Show(_settingsMgr.LoadWarning, "Settings recovered", MessageBoxButton.OK, MessageBoxImage.Warning);
            InitializeGamePath();
            _packMgr.RefreshPacks(_settingsMgr.Current.PackSelectionInitialized || _settingsMgr.Current.ActivePacks.Count > 0
                ? _settingsMgr.Current.ActivePacks : null);
            _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
            _settingsMgr.Current.PackSelectionInitialized = true;
            _settingsMgr.Current.EnvironmentPackSelectionInitialized |= _packMgr.Packs.Any(p => p.NativePayload?.Profile == "prepared-environment-v1");
            _settingsMgr.Save();
            RefreshPackLibrary();
            if (_packMgr.DiscoveryErrors.Count > 0)
                MessageBox.Show(string.Join("\n", _packMgr.DiscoveryErrors), "Some installed packs could not be loaded", MessageBoxButton.OK, MessageBoxImage.Warning);

            LoadSettingsIntoUi();
            UpdateSummaryDisplay();
            _isInitializing = false;
            if (Environment.GetCommandLineArgs().Contains("--setup-game", StringComparer.OrdinalIgnoreCase) ||
                string.IsNullOrWhiteSpace(_settingsMgr.Current.GamePath) || !_settingsMgr.Current.InitialSetupCompleted)
                ShowGameSetup();
            StartUpdateNotifications();
            InitializeAssetPackUpdates();
        }

        private void InitializeGamePath()
        {
            if (string.IsNullOrWhiteSpace(_settingsMgr.Current.GamePath) || !Directory.Exists(_settingsMgr.Current.GamePath))
            {
                var detected = GameValidator.AutoDetectGameDirectory();
                if (!string.IsNullOrEmpty(detected))
                {
                    _settingsMgr.Current.GamePath = detected;
                    _settingsMgr.Save();
                }
            }

            TxtGamePath.Text = _settingsMgr.Current.GamePath;
            ValidateGamePath();
        }

        private void ValidateGamePath()
        {
            LaunchActivity.IsActive = _launchPreparing || _assetInstallActive;
            if (_assetInstallActive)
            {
                TxtStatusReady.Text = "GAME STATUS: INSTALLING ASSETS (NOT READY)";
                TxtGameDetected.Text = "Installing assets (not ready)";
                BtnLaunchGame.IsEnabled = false;
                return;
            }
            var res = GameValidator.Validate(_settingsMgr.Current.GamePath);
            if (res.IsValid)
            {
                var originalVersion = FileVersionInfo.GetVersionInfo(res.ExecutablePath);
                TxtGameDetected.Text = originalVersion.FileMajorPart > 0
                    ? $"MechWarrior 3 {originalVersion.FileMajorPart}.{originalVersion.FileMinorPart}.{originalVersion.FileBuildPart}.{originalVersion.FilePrivatePart}"
                    : $"MW3 Ready ({res.DetectedVersion})";
                TxtGameDetected.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                TxtValidationDetails.Text = res.StatusMessage;
                TxtValidationDetails.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                TxtStatusReady.Text = "GAME STATUS: READY";
                TxtStatusReady.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                BorderGameMissingAlert.Visibility = Visibility.Collapsed;
                BtnLaunchGame.Content = _settingsMgr.Current.EngineMode == "d7vk"
                    ? "\u25B6  LAUNCH ORIGINAL (D7VK)" : PlayCaption();
                BtnLaunchGame.IsEnabled = true;
                try
                {
                    if (string.IsNullOrEmpty(_settingsMgr.Current.ModularContentProfile))
                    {
                        if (NativeGameRunner.UsesBundledMw3Re(_basePath))
                            _nativeGameRunner.RequireBundledMw3Re();
                        else if (NativeRuntimeLayout.IsInstalledApplication(_basePath) || RuntimeUpdates.SelectedRoot(_basePath) != null)
                            NativeRuntimeLayout.FindInstalled(_basePath);
                    }
                }
                catch (Exception error)
                {
                    TxtStatusReady.Text = "GAME STATUS: SETUP INCOMPLETE";
                    TxtValidationDetails.Text = error.Message;
                    BtnLaunchGame.Content = "GAME SETUP INCOMPLETE";
                    BtnLaunchGame.IsEnabled = false;
                }
            }
            else
            {
                TxtGameDetected.Text = "MW3 Path Required";
                TxtGameDetected.Foreground = System.Windows.Media.Brushes.LightCoral;
                TxtValidationDetails.Text = res.StatusMessage;
                TxtValidationDetails.Foreground = System.Windows.Media.Brushes.LightCoral;
                TxtStatusReady.Text = "⚠ GAME STATUS: ORIGINAL MECH3.EXE NOT FOUND";
                TxtStatusReady.Foreground = System.Windows.Media.Brushes.LightCoral;
                BorderGameMissingAlert.Visibility = Visibility.Visible;
                BtnLaunchGame.Content = "📁  SELECT GAME FOLDER...";
                BtnLaunchGame.IsEnabled = true;
            }
        }

        private async void BtnGameUpdates_Click(object sender, RoutedEventArgs e)
        {
            if (_assetInstallActive)
            {
                MessageBox.Show(this, "Close the game and wait for asset installation to finish before changing versions.", "Game updates");
                return;
            }
            await OpenOnlineUpdatesAsync();
        }

        private async void BtnLauncherUpdates_Click(object sender, RoutedEventArgs e)
        {
            if (_assetInstallActive) { MessageBox.Show(this, "Wait for asset installation to finish before updating Core Critical.", "Core Critical updates"); return; }
            await OpenOnlineUpdatesAsync();
        }

        private void PackGame_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_packMgr != null) RefreshPackLibrary();
        }

        private void RefreshPackLibrary()
        {
            var game = CmbPackGame.SelectedItem as GameDefinition ?? GameCatalog.Get(GameCatalog.Mw3);
            _libraryPackMgr = game.Id == GameCatalog.Mw3 ? _packMgr : new PackManager(_dataRoot, game.Id);
            if (game.Id != GameCatalog.Mw3) _libraryPackMgr.RefreshPacks();
            var view = System.Windows.Data.CollectionViewSource.GetDefaultView(_libraryPackMgr.Packs);
            view.GroupDescriptions.Clear();
            view.GroupDescriptions.Add(new System.Windows.Data.PropertyGroupDescription(nameof(PackManifest.Category)));
            ListPacks.ItemsSource = view;
            ListPacks.IsHitTestVisible = ListPacks.Focusable = game.Playable;
            BtnWatchCinematics.IsEnabled = game.Playable;
            AssetPackUpdateControls.Visibility = game.Id == GameCatalog.Mw3 &&
                AssetPackUpdateService.IsConfigured(_basePath) ? Visibility.Visible : Visibility.Collapsed;
            BtnInstallPack.IsEnabled = BtnInspectConflicts.IsEnabled = game.Playable && !_nativeSessionActive && !_assetInstallActive;
            TxtEnvironmentMigration.Visibility = Visibility.Collapsed;
            TxtPackEmpty.Text = game.Playable ? "No packs installed for MechWarrior 3. Choose Install New Pack to add one."
                : game.Name + " is coming later. Its packs will appear here when support is available.";
            TxtPackLibraryStatus.Text = game.Playable
                ? $"{game.Name} packs, grouped by type. Install {game.PackExtension} files or drag them into this window."
                : $"{game.Name} support is planned. Its {game.PackExtension} content and {game.UpdateExtension} updates will have their own library. Installation is not available yet.";
        }

        private void LoadSettingsIntoUi()
        {
            var s = _settingsMgr.Current;
            bool isD7Vk = s.EngineMode == "d7vk";

            // Engine Mode selection
            if (RadioEngineRemaster != null && RadioEngineD7vk != null)
            {
                RadioEngineRemaster.IsChecked = !isD7Vk;
                RadioEngineD7vk.IsChecked = isD7Vk;
            }
            if (RadioGfxRemaster != null && RadioGfxD7vk != null)
            {
                RadioGfxRemaster.IsChecked = !isD7Vk;
                RadioGfxD7vk.IsChecked = isD7Vk;
            }
            if (PanelRemasterGraphics != null && PanelD7vkGraphics != null)
            {
                PanelRemasterGraphics.Visibility = !isD7Vk ? Visibility.Visible : Visibility.Collapsed;
                PanelD7vkGraphics.Visibility = isD7Vk ? Visibility.Visible : Visibility.Collapsed;
            }

            // MW3-RE options
            DisplayGraphics.Load(s);
            ChkCdAudio.IsChecked = s.LocalCdAudio;
            ChkAutomaticUpdateChecks.IsChecked = s.AutomaticUpdateChecks;
            ChkAutomaticCrashReports.IsChecked = s.AutomaticCrashReports;
            ChkInstantReplay.IsChecked = s.InstantReplay;
            ChkPerformanceMonitor.IsChecked = s.PerformanceMonitor;
            ChkRenderThread.IsChecked = s.RenderThread;

            // D7VK options
            SelectComboByTag(ComboD7vkResolution, s.D7VkResolution, 0);
            SelectComboByTag(ComboD7vkAA, s.D7VkAntiAliasing, 0);
            SelectComboByTag(ComboD7vkAF, s.D7VkAnisotropicFiltering, 0);
            if (ChkD7vkAiTextures != null)
            {
                ChkD7vkAiTextures.IsChecked = s.D7VkAiTextures;
            }
            UpdateD7vkResolutionHint();
        }

        private void SelectComboByTag(ComboBox combo, string tag, int defaultIndex)
        {
            if (combo == null) return;
            foreach (ComboBoxItem item in combo.Items)
            {
                if (item.Tag != null && item.Tag.ToString() == tag)
                {
                    combo.SelectedItem = item;
                    return;
                }
            }
            if (combo.Items.Count > defaultIndex) combo.SelectedIndex = defaultIndex;
        }

        private void UpdateSummaryDisplay()
        {
            var s = _settingsMgr.Current;
            TxtEnvironmentMigration.Visibility = Visibility.Collapsed;
            bool isD7Vk = s.EngineMode == "d7vk";

            if (TxtHeaderMode != null)
            {
                TxtHeaderMode.Text = isD7Vk ? "ORIGINAL (D7VK VULKAN)" : "MW3-RE NATIVE";
            }
            if (TxtHeroBadge != null)
            {
                TxtHeroBadge.Text = isD7Vk ? "ORIGINAL MECH3.EXE + D7VK VULKAN" : "MW3-RE NATIVE";
            }
            if (TxtHeroTitle != null)
            {
                TxtHeroTitle.Text = isD7Vk ? "MechWarrior 3 (Original Engine)" : "MechWarrior 3 (MW3-RE)";
            }
            if (TxtHeroDesc != null)
            {
                TxtHeroDesc.Text = isD7Vk
                    ? "Original 1999 game executable running through isolated DirectDraw Vulkan wrapper with widescreen FOV injection, MSAA, and 30 FPS physics lock."
                    : "Native MW3-RE engine with Vulkan rendering, your enabled mech and map packs, and configurable scenery distance.";
            }
            if (BtnLaunchGame != null && BtnLaunchGame.IsEnabled)
            {
                BtnLaunchGame.Content = isD7Vk ? "▶  LAUNCH ORIGINAL (D7VK)" : PlayCaption();
            }

            if (PanelSummaryRemaster != null && PanelSummaryD7vk != null)
            {
                PanelSummaryRemaster.Visibility = !isD7Vk ? Visibility.Visible : Visibility.Collapsed;
                PanelSummaryD7vk.Visibility = isD7Vk ? Visibility.Visible : Visibility.Collapsed;
            }

            if (!isD7Vk)
            {
                string modeLabel = s.WindowMode switch
                {
                    "fullscreen" => "Exclusive Fullscreen",
                    "windowed" => "Windowed",
                    _ => "Fullscreen Windowed"
                };
                TxtSummaryResolution.Text = $"{s.Width}x{s.Height} ({modeLabel})";
                TxtSummaryAA.Text = $"{s.AntiAliasing.ToUpperInvariant()} AA, {s.AnisotropicFiltering}x AF";
                TxtSummaryDrawDist.Text = $"{s.DrawDistance}m scenery distance";

                var activeCount = _packMgr.Packs.Count(p => p.IsEnabled);
                TxtSummaryPacks.Text = $"{activeCount} of {_packMgr.Packs.Count} Packs Active";
                UpdateInputSummary(s);
            }
            else
            {
                if (TxtSummaryD7vkRes != null)
                {
                    TxtSummaryD7vkRes.Text = s.D7VkResolution;
                }
                if (TxtSummaryD7vkAA != null)
                {
                    TxtSummaryD7vkAA.Text = $"{s.D7VkAntiAliasing}, {s.D7VkAnisotropicFiltering} AF";
                }
                if (TxtSummaryD7vkTextures != null)
                {
                    TxtSummaryD7vkTextures.Text = s.D7VkAiTextures ? "39 AI-Upscaled Banks Loaded" : "Original 1999 Texture Banks";
                }
            }
        }

        private void UpdateInputSummary(LauncherSettings settings)
        {
            bool controllerLayoutEnabled = false;
            bool controllerLayoutKnown = false;
            try
            {
                controllerLayoutEnabled = new ControllerProfiles(_dataRoot).Load().Enabled;
                controllerLayoutKnown = true;
                TxtSummaryControllerLayout.Text = controllerLayoutEnabled ? "On" : "Off";
            }
            catch
            {
                TxtSummaryControllerLayout.Text = "Unavailable (check Controls)";
            }

            if (controllerLayoutEnabled)
            {
                TxtSummaryJoystick.Text = "Not used (SDL controller layout is on)";
                return;
            }

            try
            {
                var attached = DirectInputJoystickCatalog.EnumerateAttached();
                var selected = DirectInputJoystickSelection.Resolve(settings, attached);
                var hasSavedDevice = !string.IsNullOrWhiteSpace(settings.DirectInputJoystickInstanceGuid) ||
                    !string.IsNullOrWhiteSpace(settings.DirectInputJoystickProductName);
                TxtSummaryJoystick.Text = selected?.DisplayName ??
                    (hasSavedDevice && !settings.DirectInputJoystickNone
                        ? "None (saved joystick is not attached)"
                        : "None");
            }
            catch
            {
                TxtSummaryJoystick.Text = "Unavailable (device enumeration failed)";
            }

            if (!controllerLayoutKnown)
            {
                TxtSummaryJoystick.Text += " (controller-layout status unavailable)";
            }
        }

        private void Tab_Checked(object sender, RoutedEventArgs e)
        {
            if (ViewPlay == null || ViewGraphics == null || ViewMods == null || ViewPhotoReplay == null || ViewSettings == null) return;

            ViewPlay.Visibility = TabPlay.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
            ViewGraphics.Visibility = TabGraphics.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
            ViewMods.Visibility = TabMods.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
            ViewPhotoReplay.Visibility = TabPhotoReplay.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
            ViewSettings.Visibility = TabSettings.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        }

        private void EngineRadio_Checked(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;

            bool isD7Vk = RadioEngineD7vk.IsChecked == true;
            if (isD7Vk) _settingsMgr.Current.ModularContentProfile = "";
            _settingsMgr.Current.EngineMode = isD7Vk ? "d7vk" : "remaster";
            _settingsMgr.Save();

            if (RadioGfxRemaster != null && RadioGfxD7vk != null)
            {
                RadioGfxRemaster.IsChecked = !isD7Vk;
                RadioGfxD7vk.IsChecked = isD7Vk;
            }
            if (PanelRemasterGraphics != null && PanelD7vkGraphics != null)
            {
                PanelRemasterGraphics.Visibility = !isD7Vk ? Visibility.Visible : Visibility.Collapsed;
                PanelD7vkGraphics.Visibility = isD7Vk ? Visibility.Visible : Visibility.Collapsed;
            }

            UpdateSummaryDisplay();
        }

        private void GfxEngineRadio_Checked(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;

            bool isD7Vk = RadioGfxD7vk.IsChecked == true;
            if (isD7Vk) _settingsMgr.Current.ModularContentProfile = "";
            if (RadioEngineRemaster != null && RadioEngineD7vk != null)
            {
                RadioEngineRemaster.IsChecked = !isD7Vk;
                RadioEngineD7vk.IsChecked = isD7Vk;
            }
            if (PanelRemasterGraphics != null && PanelD7vkGraphics != null)
            {
                PanelRemasterGraphics.Visibility = !isD7Vk ? Visibility.Visible : Visibility.Collapsed;
                PanelD7vkGraphics.Visibility = isD7Vk ? Visibility.Visible : Visibility.Collapsed;
            }
            _settingsMgr.Current.EngineMode = isD7Vk ? "d7vk" : "remaster";
            _settingsMgr.Save();
            UpdateSummaryDisplay();
        }

        private void SettingControl_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;

            var s = _settingsMgr.Current;
            DisplayGraphics.Read().ApplyTo(s);

            s.LocalCdAudio = ChkCdAudio.IsChecked == true;
            s.InstantReplay = ChkInstantReplay.IsChecked == true;
            s.PerformanceMonitor = ChkPerformanceMonitor.IsChecked == true;
            s.RenderThread = ChkRenderThread.IsChecked == true;

            _settingsMgr.Save();
            UpdateSummaryDisplay();
        }

        private void D7vkSettingControl_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;

            var s = _settingsMgr.Current;
            if (ComboD7vkResolution?.SelectedItem is ComboBoxItem resItem && resItem.Tag is string resStr)
            {
                s.D7VkResolution = resStr;
                UpdateD7vkResolutionHint();
            }
            if (ComboD7vkAA?.SelectedItem is ComboBoxItem aaItem && aaItem.Tag is string aaStr)
            {
                s.D7VkAntiAliasing = aaStr;
            }
            if (ComboD7vkAF?.SelectedItem is ComboBoxItem afItem && afItem.Tag is string afStr)
            {
                s.D7VkAnisotropicFiltering = afStr;
            }
            if (ChkD7vkAiTextures != null)
            {
                s.D7VkAiTextures = ChkD7vkAiTextures.IsChecked == true;
            }

            _settingsMgr.Save();
            UpdateSummaryDisplay();
        }

        private void UpdateD7vkResolutionHint()
        {
            if (TxtD7vkResHint == null) return;
            var res = _settingsMgr.Current.D7VkResolution;
            if (D7VkResolutionHints.TryGetValue(res, out var hint))
            {
                TxtD7vkResHint.Text = hint;
            }
            else
            {
                TxtD7vkResHint.Text = "";
            }
        }

        private void PackCheckbox_Click(object sender, RoutedEventArgs e)
        {
            _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
            _settingsMgr.Save();
            UpdateSummaryDisplay();
        }

        private void BtnMoveUp_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is PackManifest pack)
            {
                _packMgr.MovePriority(pack, -1);
                _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
                _settingsMgr.Save();
            }
        }

        private void BtnMoveDown_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is PackManifest pack)
            {
                _packMgr.MovePriority(pack, 1);
                _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
                _settingsMgr.Save();
            }
        }

        private void BtnUninstallPack_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is PackManifest pack)
            {
                var prompt = MessageBox.Show($"Are you sure you want to uninstall and delete the pack '{pack.Name}'?",
                    "Uninstall Pack", MessageBoxButton.YesNo, MessageBoxImage.Question);
                if (prompt == MessageBoxResult.Yes)
                {
                    try
                    {
                        if (Process.GetProcessesByName("entry_commandline").Length > 0)
                            throw new InvalidOperationException("Close MW3-RE before removing content packs.");
                        _packMgr.UninstallPack(pack);
                    }
                    catch (Exception ex) { MessageBox.Show(ex.Message, "Cannot uninstall pack", MessageBoxButton.OK, MessageBoxImage.Error); return; }
                    _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
                    _settingsMgr.Save();
                    UpdateSummaryDisplay();
                }
            }
        }

        private async System.Threading.Tasks.Task<PackManifest> InstallPackWithProgressAsync(string file)
        {
            if (!_assetInstallActive) throw new InvalidOperationException("Asset installation needs an active batch.");
            var sequence = ++_assetInstallSequence;
            ProgressAssetInstall.Value = 0;
            ProgressAssetInstall.IsIndeterminate = true;
            TxtAssetInstallProgress.Text = $"Pack {_assetPackIndex} of {_assetPackCount}: {Path.GetFileName(file)} — Checking archive…";
            var progress = new Progress<PackInstallProgress>(value =>
            {
                if (!_assetInstallActive || sequence != _assetInstallSequence) return;
                ProgressAssetInstall.IsIndeterminate = value.TotalBytes == 0;
                ProgressAssetInstall.Value = value.Percent;
                var percent = value.TotalBytes > 0 ? $" ({value.Percent:F0}%)" : "";
                TxtAssetInstallProgress.Text = $"Pack {_assetPackIndex} of {_assetPackCount}: {Path.GetFileName(file)} — {value.Stage}{percent}";
            });
            var pack = await _packMgr.InstallPackAsync(file, progress);
            // Retain successful imports even if a later pack fails.
            _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
            _settingsMgr.Current.PackSelectionInitialized = true;
            if (pack.NativePayload?.Profile == "prepared-environment-v1")
                _settingsMgr.Current.EnvironmentPackSelectionInitialized = true;
            _settingsMgr.Save();
            UpdateSummaryDisplay();
            return pack;
        }

        private async System.Threading.Tasks.Task<int> InstallPacksAsync(string[] files)
        {
            if (files.Length == 0 || _assetInstallActive || _nativeSessionActive) return 0;
            if ((CmbPackGame.SelectedItem as GameDefinition)?.Id != GameCatalog.Mw3 ||
                Process.GetProcessesByName("entry_commandline").Length > 0)
            {
                MessageBox.Show(this, "Select the MechWarrior 3 library and close the game before installing packs.", "Cannot install assets");
                return 0;
            }
            _assetInstallActive = true;
            _assetPackCount = files.Length;
            _assetPackIndex = 0;
            var caption = BtnInstallPack.Content;
            BtnInstallPack.Content = "Installing assets…";
            BtnInstallPack.IsEnabled = BtnInspectConflicts.IsEnabled = false;
            CmbPackGame.IsEnabled = ListPacks.IsEnabled = false;
            AssetInstallProgressPanel.Visibility = Visibility.Visible;
            ValidateGamePath();
            var errors = new List<string>();
            int installed = 0;
            try
            {
                foreach (var file in files)
                {
                    _assetPackIndex++;
                    try
                    {
                        await InstallPackWithProgressAsync(file);
                        installed++;
                    }
                    catch (Exception error) { errors.Add(Path.GetFileName(file) + ": " + error.Message); }
                }
            }
            finally
            {
                _assetInstallActive = false;
                _assetInstallSequence++;
                AssetInstallProgressPanel.Visibility = Visibility.Collapsed;
                BtnInstallPack.Content = caption;
                CmbPackGame.IsEnabled = ListPacks.IsEnabled = true;
                RefreshPackLibrary();
                ValidateGamePath();
            }
            var message = $"Installed {installed} of {files.Length} asset pack(s).";
            if (errors.Count > 0) message += "\n\n" + string.Join("\n", errors);
            MessageBox.Show(this, message, errors.Count == 0 ? "Assets installed" : "Asset installation needs attention",
                MessageBoxButton.OK, errors.Count == 0 ? MessageBoxImage.Information : MessageBoxImage.Warning);
            return installed;
        }

        private async void BtnInstallPack_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Title = "Select Asset Packs",
                Filter = "MechWarrior 3 Asset Packs (*.mw3pack;*.zip)|*.mw3pack;*.zip|All Files (*.*)|*.*",
                Multiselect = true
            };
            if (dialog.ShowDialog(this) == true) await InstallPacksAsync(dialog.FileNames);
        }

        private void BtnRollbackPack_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is PackManifest pack)
            {
                try
                {
                    if (Process.GetProcessesByName("entry_commandline").Length > 0)
                        throw new InvalidOperationException("Close MW3-RE before changing installed versions.");
                    _packMgr.RollbackPack(pack);
                    UpdateSummaryDisplay();
                }
                catch (Exception ex) { MessageBox.Show(ex.Message, "Cannot restore previous pack", MessageBoxButton.OK, MessageBoxImage.Information); }
            }
        }

        private void BtnInspectConflicts_Click(object sender, RoutedEventArgs e)
        {
            List<PackConflict> conflicts;
            try { conflicts = _packMgr.InspectConflicts(); }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message, "Cannot inspect packs", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            if (conflicts.Count == 0)
            {
                MessageBox.Show("No file conflicts detected between active asset packs.", "Conflict Check", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                var msg = string.Join("\n", conflicts.Take(10).Select(c => $"• {c.RelativePath}\n   Winning: {c.WinningPackName} (overrides {c.OverriddenPackName})"));
                if (conflicts.Count > 10) msg += $"\n... and {conflicts.Count - 10} more conflicts.";
                MessageBox.Show($"Detected {conflicts.Count} overridden file(s) based on your current load order:\n\n{msg}", "Asset Overrides", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnOpenModsFolder_Click(object sender, RoutedEventArgs e)
        {
            var modsDir = (_libraryPackMgr ?? _packMgr).ModsRoot;
            if (!Directory.Exists(modsDir)) Directory.CreateDirectory(modsDir);
            Process.Start(new ProcessStartInfo("explorer.exe", modsDir));
        }

        private void Window_DragOver(object sender, DragEventArgs e)
        {
            if (!_assetInstallActive && !_nativeSessionActive && e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                e.Effects = DragDropEffects.Copy;
            }
            else
            {
                e.Effects = DragDropEffects.None;
            }
            e.Handled = true;
        }

        private async void Window_Drop(object sender, DragEventArgs e)
        {
            if (_assetInstallActive || _nativeSessionActive || !e.Data.GetDataPresent(DataFormats.FileDrop)) return;
            var files = (string[])e.Data.GetData(DataFormats.FileDrop);
            foreach (var file in files)
            {
                if (Path.GetFileName(file).Equals("Mech3.exe", StringComparison.OrdinalIgnoreCase) ||
                    (Directory.Exists(file) && GameValidator.FindExecutableInDirectory(file) != null))
                {
                    var directory = Directory.Exists(file) ? file : Path.GetDirectoryName(file)!;
                    _settingsMgr.Current.GamePath = directory;
                    _settingsMgr.Save();
                    TxtGamePath.Text = directory;
                    ValidateGamePath();
                    MessageBox.Show(this, "Game location set to: " + directory, "Game folder updated");
                    return;
                }
            }
            var archives = files.Where(file =>
                GameCatalog.Games.Any(game => string.Equals(Path.GetExtension(file), game.PackExtension, StringComparison.OrdinalIgnoreCase)) ||
                string.Equals(Path.GetExtension(file), ".zip", StringComparison.OrdinalIgnoreCase)).ToArray();
            await InstallPacksAsync(archives);
        }

        private void BtnBrowseGamePath_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Select MechWarrior 3 Folder or Executable (Mech3.exe)",
                Filter = "MechWarrior 3 Executable (Mech3.exe)|Mech3.exe;mech3.exe|All Executables (*.exe)|*.exe|All Files (*.*)|*.*",
                CheckFileExists = false
            };

            if (dlg.ShowDialog() == true)
            {
                string chosen = dlg.FileName;
                string dir = File.Exists(chosen) ? (Path.GetDirectoryName(chosen) ?? chosen) : chosen;
                _settingsMgr.Current.GamePath = dir;
                _settingsMgr.Save();
                TxtGamePath.Text = dir;
                ValidateGamePath();
            }
        }

        private void BtnImportMedia_Click(object sender, RoutedEventArgs e) => ShowGameSetup();

        private async void ShowGameSetup()
        {
            if (_nativeSessionActive || _assetInstallActive) return;
            var setup = new GameSetupWindow(_settingsMgr.Current.GamePath, _settingsMgr.Current, _dataRoot) { Owner = this };
            if (setup.ShowDialog() != true || setup.GameDirectory == null) return;
            _settingsMgr.Current.GamePath = setup.GameDirectory;
            setup.SelectedGraphics!.ApplyTo(_settingsMgr.Current);
            _settingsMgr.Current.AutomaticUpdateChecks = setup.AutomaticUpdateChecks;
            _settingsMgr.Current.InitialSetupCompleted = true;
            _settingsMgr.Save();
            _isInitializing = true;
            LoadSettingsIntoUi();
            _isInitializing = false;
            UpdateSummaryDisplay();
            TxtGamePath.Text = setup.GameDirectory;
            TxtMediaStatus.Text = "Original MW3 1.2 files verified.";
            ValidateGamePath();
            if (setup.SelectedPacks.Length > 0)
            {
                var installed = await InstallPacksAsync(setup.SelectedPacks);
                TxtMediaStatus.Text = $"Original files verified. Installed {installed} of {setup.SelectedPacks.Length} selected packs.";
            }
            ApplyUpdateNotificationPreference();
        }

        private void BtnAddToSteam_Click(object sender, RoutedEventArgs e)
        {
            var launcherExe = Path.Combine(_basePath, "Core Critical Launcher.exe");
            var artworkDir = Path.Combine(_basePath, "Assets", "Plates");

            try
            {
                var result = SteamHelper.AddToSteam(launcherExe, artworkDir);
                _settingsMgr.Current.HasAddedToSteam = true;
                _settingsMgr.Save();
                MessageBox.Show("Core Critical Launcher is ready in your Steam library. Start Steam to load it.\n\n" +
                    (result.ArtworkWarning ?? "Existing custom artwork was preserved; bundled artwork was added where missing."),
                    "Steam Integration", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception error)
            {
                MessageBox.Show("Core Critical could not be added to Steam: " + error.Message,
                    "Steam Integration", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        /// <summary>Play starts MW3-RE; a selected modular content profile launches that profile instead.</summary>
        private string PlayCaption() => string.IsNullOrEmpty(_settingsMgr.Current.ModularContentProfile)
            ? "▶  PLAY" : "▶  PLAY MW3-RE PROFILE";

        private sealed record CrashReportSessionContext(
            LauncherSettings Settings,
            PackManifest[] Packs,
            string? LaunchLog,
            string RuntimeVersion,
            int? ExitCode = null);

        private CrashReportSessionContext? _lastReportSession;

        /// <summary>
        /// Keeps the session's exit code for Export Report. Skipped when a newer launch has
        /// already replaced the session, so its report isn't given an old exit code.
        /// </summary>
        private void RecordSessionExit(CrashReportSessionContext context, int exitCode)
        {
            if (ReferenceEquals(_lastReportSession, context))
                _lastReportSession = context with { ExitCode = exitCode };
        }

        private static string ResolveD7VkRuntimeVersion(LauncherSettings settings)
        {
            try
            {
                var validation = GameValidator.Validate(settings.GamePath);
                if (!string.IsNullOrWhiteSpace(validation.DetectedVersion))
                    return validation.DetectedVersion;
                if (!string.IsNullOrWhiteSpace(validation.ExecutablePath) && File.Exists(validation.ExecutablePath))
                {
                    var versionInfo = FileVersionInfo.GetVersionInfo(validation.ExecutablePath);
                    if (versionInfo.FileMajorPart > 0)
                        return $"{versionInfo.FileMajorPart}.{versionInfo.FileMinorPart}.{versionInfo.FileBuildPart}.{versionInfo.FilePrivatePart}";
                }
            }
            catch { }
            return "unknown";
        }

        private async void BtnLaunchGame_Click(object sender, RoutedEventArgs e)
        {
            if (_assetInstallActive || _nativeSessionActive || _launchPreparing) return;
            var settings = System.Text.Json.JsonSerializer.Deserialize<LauncherSettings>(
                System.Text.Json.JsonSerializer.Serialize(_settingsMgr.Current))!;

            if (settings.EngineMode == "d7vk")
            {
                var settingsSnapshot = SnapshotCrashReportSettings(settings);
                var packsSnapshot = SnapshotCrashReportPacks(_packMgr.Packs);
                var runtimeVersion = ResolveD7VkRuntimeVersion(settingsSnapshot);
                try
                {
                    SetLaunchPreparing(true);
                    BtnLaunchGame.IsEnabled = false;
                    var validation = await System.Threading.Tasks.Task.Run(() => _d7vkRunner.Validate());
                    if (!validation.IsValid)
                    {
                        SetLaunchPreparing(false);
                        BtnLaunchGame.IsEnabled = true;
                        MessageBox.Show($"Cannot launch Original Game with D7VK:\n\n{validation.StatusMessage}\n\n" +
                                        "Please ensure Python 3 is installed and the D7VK wrapper components exist in local/work-ahead/mw3-d7vk-wrapper.",
                                        "D7VK Wrapper Launch Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                        return;
                    }

                    BtnLaunchGame.Content = "\u25CF  GAME RUNNING...";
                    TxtStatusReady.Text = "GAME STATUS: ORIGINAL MECH3 (D7VK) RUNNING";
                    if (_packMgr.Packs.Any(pack => pack.IsEnabled && pack.SchemaVersion == 2))
                        throw new InvalidOperationException("Prepared native mech packs require MW3-RE. Disable them before launching D7VK.");
                    var process = await System.Threading.Tasks.Task.Run(() =>
                        _d7vkRunner.LaunchGame(settings, line => Debug.WriteLine(line)));
                    SetLaunchPreparing(false);
                    var sessionContext = new CrashReportSessionContext(
                        settingsSnapshot, packsSnapshot, _d7vkRunner.LastLogPath, runtimeVersion);
                    _lastReportSession = sessionContext;
                    process.EnableRaisingEvents = true;
                    _ = ObserveD7VkCompletionAsync(process, sessionContext);
                }
                catch (Exception error)
                {
                    SetLaunchPreparing(false);
                    BtnLaunchGame.IsEnabled = true;
                    BtnLaunchGame.Content = "\u25B6  LAUNCH ORIGINAL (D7VK)";
                    MessageBox.Show($"Failed to launch Original Game (D7VK Wrapper):\n\n{error.Message}",
                        "Launch Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                return;
            }

            var gameValidation = GameValidator.Validate(settings.GamePath);
            if (!gameValidation.IsValid)
            {
                BtnBrowseGamePath_Click(sender, e);
                return;
            }

            try
            {
                SettingControl_Changed(sender, e);
                settings = System.Text.Json.JsonSerializer.Deserialize<LauncherSettings>(
                    System.Text.Json.JsonSerializer.Serialize(_settingsMgr.Current))!;
                var nativeSettingsSnapshot = SnapshotCrashReportSettings(settings);
                var nativePacksSnapshot = SnapshotCrashReportPacks(_packMgr.Packs);
                var activeDirectories = _packMgr.GetActivePackDirectories();
                _nativeSessionActive = true;
                SetLaunchPreparing(true);
                BtnLaunchGame.IsEnabled = false;
                BtnInstallPack.IsEnabled = false;
                ListPacks.IsEnabled = false;
                BtnLaunchGame.Content = "\u25CF  PREPARING MW3-RE...";
                TxtStatusReady.Text = "GAME STATUS: STARTING MW3-RE";
                TxtStartupProgress.Text = "Checking the MW3-RE runtime...";
                var process = await System.Threading.Tasks.Task.Run(() =>
                    _nativeGameRunner.Launch(settings, activeDirectories, line =>
                    {
                        if (line.StartsWith("Startup: ", StringComparison.Ordinal) ||
                            line.StartsWith("Native progress: ", StringComparison.Ordinal) ||
                            line.StartsWith("Scenery distance ", StringComparison.Ordinal) ||
                            line.StartsWith("Pack left out: ", StringComparison.Ordinal))
                            Dispatcher.BeginInvoke(new Action(() =>
                            {
                                if (!_nativeSessionActive) return;
                                const string native = "Native progress: ";
                                // "idle" only means the game's own loading finished; the first
                                // frame below ends the preparing state.
                                if (line == native + "idle") return;
                                TxtStartupProgress.Text = line.StartsWith(native, StringComparison.Ordinal)
                                    ? line.Substring(native.Length) : line;
                            }));
                        if (line.StartsWith("Native first frame: ", StringComparison.Ordinal))
                            Dispatcher.BeginInvoke(new Action(() =>
                            {
                                if (!_nativeSessionActive) return;
                                SetLaunchPreparing(false);
                                BtnLaunchGame.Content = "\u25CF  GAME RUNNING...";
                                TxtStatusReady.Text = "GAME STATUS: MW3-RE RUNNING";
                                TxtStartupProgress.Text = "The game is on screen.";
                            }));
                    }));
                var sessionContext = new CrashReportSessionContext(
                    nativeSettingsSnapshot, nativePacksSnapshot, _nativeGameRunner.LastLogPath,
                    _nativeGameRunner.LastRuntimeVersion ?? "unknown");
                _lastReportSession = sessionContext;
                _ = ObserveNativeGameCompletionAsync(process, _nativeGameRunner.LastSessionCompletion, sessionContext);
            }
            catch (Exception error)
            {
                ResetNativeLaunchControls();
                TxtStatusReady.Text = "\u26A0 LAUNCH FAILED - OPEN LOGS FOR DETAILS";
                MessageBox.Show($"Failed to launch MW3-RE:\n\n{error.Message}\n\nUse Open Logs or Export Report under Settings & Steam.",
                    "Launch Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async System.Threading.Tasks.Task ObserveNativeGameCompletionAsync(
            Process process, Task<int>? sessionCompletion, CrashReportSessionContext context)
        {
            try
            {
                var exit = sessionCompletion != null
                    ? await sessionCompletion
                    : await GameRunner.WaitForCompletionAsync(process);
                RecordSessionExit(context, exit);
                ResetNativeLaunchControls();
                TxtStatusReady.Text = exit == 0 ? "GAME STATUS: READY" : "\u26A0 MW3-RE ENDED WITH AN ERROR";
                if (exit != 0)
                    await HandleCrashReportAsync(exit, context);
            }
            catch (Exception error)
            {
                ResetNativeLaunchControls();
                TxtStatusReady.Text = "\u26A0 COULD NOT READ GAME EXIT STATUS";
                MessageBox.Show(error.Message, "Game session details", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally { process.Dispose(); }
        }

        private void ResetNativeLaunchControls()
        {
            _nativeSessionActive = false;
            SetLaunchPreparing(false);
            BtnLaunchGame.IsEnabled = true;
            BtnInstallPack.IsEnabled = true;
            ListPacks.IsEnabled = true;
            BtnLaunchGame.Content = PlayCaption();
        }

        private async Task ObserveD7VkCompletionAsync(Process process, CrashReportSessionContext context)
        {
            try
            {
                var exit = await GameRunner.WaitForCompletionAsync(process);
                RecordSessionExit(context, exit);
                BtnLaunchGame.IsEnabled = true;
                BtnLaunchGame.Content = "▶  LAUNCH ORIGINAL (D7VK)";
                TxtStatusReady.Text = exit == 0 ? "GAME STATUS: READY" : "⚠ ORIGINAL GAME OR WRAPPER FAILED";
                if (exit != 0) await HandleCrashReportAsync(exit, context);
            }
            catch (Exception error)
            {
                BtnLaunchGame.IsEnabled = true;
                BtnLaunchGame.Content = "▶  LAUNCH ORIGINAL (D7VK)";
                TxtStatusReady.Text = "⚠ COULD NOT READ GAME EXIT STATUS";
                MessageBox.Show(this, error.Message, "Game session details", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally { process.Dispose(); }
        }

        private async Task HandleCrashReportAsync(int exitCode, CrashReportSessionContext context)
        {
            var settingsSnapshot = context.Settings;
            var packsSnapshot = context.Packs;
            var launchLog = context.LaunchLog;
            var runtimeVersion = context.RuntimeVersion;
            var summary = PlaytestDiagnostics.FailureSummary(launchLog, exitCode);
            var engineTitle = settingsSnapshot.EngineMode == "d7vk" ? "Original Game (D7VK)" : "MW3-RE";
            var exitStatus = PlaytestDiagnostics.FormatExitCode(exitCode);
            var statusLabel = $"{engineTitle} stopped (exit {exitStatus})";
            var dialogSummary = summary == PlaytestDiagnostics.GenericFailureSummary
                ? $"{summary} Exit code: {exitStatus}."
                : summary;

            if (_settingsMgr.Current.AutomaticCrashReports)
            {
                MessageBox.Show(dialogSummary + "\n\nUse Open Logs or Export Report under Settings & Steam.",
                    statusLabel, MessageBoxButton.OK, MessageBoxImage.Error);
            }
            else
            {
                var choice = MessageBox.Show(this,
                    dialogSummary + "\n\nSend the redacted recent launcher and native logs, hardware inventory (CPU, installed memory, graphics adapters and drivers), launcher/runtime details, selected graphics settings and pack metadata to Core Critical for review? The inventory does not request serial numbers or device identifiers. Reports are stored in private review systems, including an admin-only archive retained until the maintainer deletes them. Saves, original media or memory dumps are not included.\n\nChoose No to keep all diagnostics on this PC. You can still use Export Report to review a local copy.",
                    statusLabel, MessageBoxButton.YesNo, MessageBoxImage.Warning, MessageBoxResult.No);
                if (choice != MessageBoxResult.Yes) return;
            }

            try
            {
                var hardwareInventory = await Task.Run(HardwareInventory.Capture);
                var report = PlaytestDiagnostics.CreateCrashReport(settingsSnapshot, packsSnapshot,
                    launchLog, _basePath, runtimeVersion, exitCode, hardwareInventory);
                var result = await new CrashReportService().SubmitAsync(report);
                var detail = result.ArchivedOnly
                    ? "The report was saved to the private admin archive. GitHub issue delivery was unavailable."
                    : result.Overflow
                        ? "Report sent, thanks. The report was added to the daily overflow queue."
                        : "Report sent, thanks.";
                MessageBox.Show(this, detail + "\nReport ID: " + result.ReportId,
                    "Crash report sent", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception error)
            {
                MessageBox.Show(this,
                    "The crash report could not be sent. Your logs remain on this PC. " + error.Message +
                    "\n\nUse Export Report under Settings & Steam to save a local copy.",
                    "Crash report not sent", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        /// <summary>The current MW3-RE or D7VK session log, else the latest on disk.</summary>
        private string? CurrentLaunchLog()
        {
            var logs = new[] { _nativeGameRunner.LastLogPath, _d7vkRunner.LastLogPath }
                .Where(path => path != null && File.Exists(path))
                .OrderByDescending(path => File.GetLastWriteTimeUtc(path!));
            return logs.FirstOrDefault() ?? LauncherPaths.LatestLaunchLog();
        }

        private void BtnOpenLogs_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var log = CurrentLaunchLog();
                var folder = log == null ? LauncherPaths.SessionsRoot : Path.GetDirectoryName(log)!;
                Directory.CreateDirectory(folder);
                Process.Start(new ProcessStartInfo { FileName = folder, UseShellExecute = true });
            }
            catch (Exception ex) { MessageBox.Show(ex.Message, "Cannot open logs", MessageBoxButton.OK, MessageBoxImage.Error); }
        }

        private void BtnSaveBackups_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (_nativeSessionActive) throw new InvalidOperationException("Close the current game session before managing saves.");
                string? registry = null;
                if (NativeRuntimeLayout.IsInstalledApplication(_basePath) || RuntimeUpdates.SelectedRoot(_basePath) != null)
                    registry = Path.Combine(_dataRoot, "native-settings", "mw3-registry.txt");
                else
                {
                    var root = GameRunner.FindRepositoryRoot(_basePath);
                    if (root != null)
                    {
                        var profile = System.Text.Json.Nodes.JsonNode.Parse(File.ReadAllText(Path.Combine(root, "local/remaster/launcher.json")));
                        var source = profile?["native"]?["runtime_environment"]?["MW34_REG_OVERLAY"]?.GetValue<string>();
                        if (!string.IsNullOrEmpty(source)) registry = Path.GetFullPath(Path.Combine(root, source));
                    }
                }
                new SaveBackupsWindow(_settingsMgr.Current.GamePath, registry) { Owner = this }.ShowDialog();
            }
            catch (Exception error) { MessageBox.Show(error.Message, "Save backups", MessageBoxButton.OK, MessageBoxImage.Information); }
        }

        private void BtnAiArena_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (_nativeSessionActive || _launchPreparing || _assetInstallActive)
                    throw new InvalidOperationException("Close the current game session before opening the AI Arena.");
                var activeDirectories = _packMgr.GetActivePackDirectories();
                new ArenaWindow(_settingsMgr.Current, activeDirectories, _dataRoot, _nativeGameRunner) { Owner = this }.ShowDialog();
            }
            catch (Exception error)
            {
                MessageBox.Show(this, error.Message, "AI Arena", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private System.Threading.CancellationTokenSource? _benchmarkCancellation;

        private async void BtnRunBenchmark_Click(object sender, RoutedEventArgs e)
        {
            if (_nativeSessionActive || _launchPreparing || _assetInstallActive)
            {
                MessageBox.Show(this, "Close the current game session before running the benchmark.", "Graphics benchmark",
                    MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }
            // Settings are saved as they change, and the benchmark reads that saved file through
            // the Play planner, so it uses the same graphics settings and packs Play would.
            _settingsMgr.Save();
            _nativeSessionActive = true; // Blocks Play, pack installs and update prompts meanwhile.
            BtnLaunchGame.IsEnabled = false;
            BtnRunBenchmark.IsEnabled = false;
            BtnCancelBenchmark.Visibility = Visibility.Visible;
            TxtBenchmarkResult.Visibility = Visibility.Collapsed;
            TxtBenchmarkStatus.Visibility = Visibility.Visible;
            TxtBenchmarkStatus.Foreground = (System.Windows.Media.Brush)FindResource("BrushMuted");
            TxtBenchmarkStatus.Text = "Starting the benchmark...";
            _benchmarkCancellation = new System.Threading.CancellationTokenSource();
            try
            {
                var runner = new BenchmarkRunner(_basePath, _nativeGameRunner);
                var outcome = await runner.RunAsync(
                    item => Dispatcher.Invoke(() => TxtBenchmarkStatus.Text = BenchmarkRunner.DescribeProgress(item)),
                    _benchmarkCancellation.Token);
                if (outcome.Report is { } report)
                {
                    TxtBenchmarkStatus.Text = report.Gpu is { } gpu ? $"Finished on {gpu}." : "Finished.";
                    TxtBenchmarkResult.Text = BenchmarkRunner.FormatReport(report);
                    TxtBenchmarkResult.Visibility = Visibility.Visible;
                }
                else
                {
                    TxtBenchmarkStatus.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                    TxtBenchmarkStatus.Text = BenchmarkRunner.DescribeError(outcome);
                }
            }
            catch (OperationCanceledException)
            {
                TxtBenchmarkStatus.Text = "Benchmark cancelled.";
            }
            catch (Exception error)
            {
                TxtBenchmarkStatus.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                TxtBenchmarkStatus.Text = "The benchmark could not run: " + error.Message;
            }
            finally
            {
                _benchmarkCancellation.Dispose();
                _benchmarkCancellation = null;
                BtnCancelBenchmark.Visibility = Visibility.Collapsed;
                BtnRunBenchmark.IsEnabled = true;
                ResetNativeLaunchControls();
            }
        }

        private void BtnCancelBenchmark_Click(object sender, RoutedEventArgs e) => _benchmarkCancellation?.Cancel();

        private async void BtnExportReport_Click(object sender, RoutedEventArgs e)
        {
            var launchLog = CurrentLaunchLog();
            var matchingSession = _lastReportSession is { LaunchLog: { } sessionLog } session &&
                string.Equals(sessionLog, launchLog, StringComparison.OrdinalIgnoreCase) ? session : null;
            var settingsSnapshot = matchingSession?.Settings ?? SnapshotCrashReportSettings(_settingsMgr.Current);
            var packsSnapshot = matchingSession?.Packs ?? SnapshotCrashReportPacks(_packMgr.Packs);
            var runtimeVersion = matchingSession?.RuntimeVersion;
            var dialog = new SaveFileDialog
            {
                Title = "Save playtest troubleshooting report", Filter = "Troubleshooting report (*.zip)|*.zip",
                FileName = "MW3-Playtest-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".zip"
            };
            if (dialog.ShowDialog() != true) return;
            try
            {
                var hardwareInventory = await System.Threading.Tasks.Task.Run(HardwareInventory.Capture);
                PlaytestDiagnostics.Export(dialog.FileName, settingsSnapshot, packsSnapshot,
                    launchLog, _basePath, hardwareInventory, runtimeVersion,
                    exitCode: matchingSession?.ExitCode);
                MessageBox.Show("Report saved. It contains build/system details, selected settings, pack metadata and redacted recent log tails. Review it before sharing.",
                    "Playtest report saved", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex) { MessageBox.Show(ex.Message, "Cannot export report", MessageBoxButton.OK, MessageBoxImage.Error); }
        }

        private static LauncherSettings SnapshotCrashReportSettings(LauncherSettings settings)
        {
            return new LauncherSettings
            {
                GamePath = settings.GamePath,
                EngineMode = settings.EngineMode,
                ModularContentProfile = settings.ModularContentProfile,
                ModularRuntimeExecutable = settings.ModularRuntimeExecutable,
                Width = settings.Width,
                Height = settings.Height,
                WindowMode = settings.WindowMode,
                AntiAliasing = settings.AntiAliasing,
                AnisotropicFiltering = settings.AnisotropicFiltering,
                DrawDistance = settings.DrawDistance,
                FlareStyle = settings.FlareStyle,
                FogDistance = settings.FogDistance,
                LocalCdAudio = settings.LocalCdAudio,
                InstantReplay = settings.InstantReplay,
                PerformanceMonitor = settings.PerformanceMonitor,
                RenderThread = settings.RenderThread,
                Vsync = settings.Vsync,
                D7VkResolution = settings.D7VkResolution,
                D7VkAntiAliasing = settings.D7VkAntiAliasing,
                D7VkAnisotropicFiltering = settings.D7VkAnisotropicFiltering,
                D7VkAiTextures = settings.D7VkAiTextures
            };
        }

        private static PackManifest[] SnapshotCrashReportPacks(IEnumerable<PackManifest> packs)
        {
            return packs.Select(pack => new PackManifest
            {
                Id = pack.Id,
                Version = pack.Version,
                SchemaVersion = pack.SchemaVersion,
                IsEnabled = pack.IsEnabled,
                Priority = pack.Priority
            }).ToArray();
        }

        private void BtnOpenScreenshots_Click(object sender, RoutedEventArgs e)
        {
            OpenSubFolder("screenshots");
        }

        private void BtnOpenReplays_Click(object sender, RoutedEventArgs e)
        {
            OpenSubFolder("replays");
        }

        private void BtnOpenVideos_Click(object sender, RoutedEventArgs e)
        {
            OpenSubFolder("videos");
        }

        private void OpenSubFolder(string folderName)
        {
            var validation = GameValidator.Validate(_settingsMgr.Current.GamePath);
            if (!validation.IsValid)
            {
                MessageBox.Show(this, validation.StatusMessage, "Game location required", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            try
            {
                var target = Path.Combine(Path.GetFullPath(validation.GameDirectory), folderName);
                Directory.CreateDirectory(target);
                Process.Start(new ProcessStartInfo("explorer.exe", target));
            }
            catch (Exception error)
            {
                MessageBox.Show(this, error.Message, "Cannot open capture folder", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void MainWindow_StateChanged(object? sender, EventArgs e)
        {
            if (WindowState == WindowState.Maximized)
            {
                BtnWinMaximize.Content = "\u29C9"; // Two overlapping squares (restore glyph)
                BtnWinMaximize.ToolTip = "Restore Down";
                RootBorder.Padding = new Thickness(7); // Account for WPF WindowChrome maximize overflow
            }
            else
            {
                BtnWinMaximize.Content = "\u25A1"; // Square (maximize glyph)
                BtnWinMaximize.ToolTip = "Maximize";
                RootBorder.Padding = new Thickness(0);
            }
        }

        private void BtnWinMinimize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void BtnWinMaximize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = (WindowState == WindowState.Maximized) ? WindowState.Normal : WindowState.Maximized;
        }

        private void BtnWinClose_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }
    }
}
