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
        private bool _nativeSessionActive;
        private readonly SettingsManager _settingsMgr;
        private readonly PackManager _packMgr;
        private readonly GameRunner _gameRunner;
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

        public MainWindow()
        {
            InitializeComponent();

            _basePath = AppDomain.CurrentDomain.BaseDirectory;
            _settingsMgr = new SettingsManager(_basePath);
            _packMgr = new PackManager(LauncherPaths.DataRoot);
            _gameRunner = new GameRunner(_basePath);
            _d7vkRunner = new D7VkRunner(_basePath);

            Loaded += MainWindow_Loaded;
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            TxtLauncherBuild.Text = "Launcher " + typeof(GameRunner).Assembly.GetName().Version;
            if (_settingsMgr.LoadWarning != null)
                MessageBox.Show(_settingsMgr.LoadWarning, "Settings recovered", MessageBoxButton.OK, MessageBoxImage.Warning);
            InitializeGamePath();
            _packMgr.RefreshPacks(_settingsMgr.Current.PackSelectionInitialized || _settingsMgr.Current.ActivePacks.Count > 0
                ? _settingsMgr.Current.ActivePacks : null);
            _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
            _settingsMgr.Current.PackSelectionInitialized = true;
            _settingsMgr.Current.EnvironmentPackSelectionInitialized |= _packMgr.Packs.Any(p => p.NativePayload?.Profile == "prepared-environment-v1");
            _settingsMgr.Save();
            ListPacks.ItemsSource = _packMgr.Packs;
            if (_packMgr.DiscoveryErrors.Count > 0)
                MessageBox.Show(string.Join("\n", _packMgr.DiscoveryErrors), "Some installed packs could not be loaded", MessageBoxButton.OK, MessageBoxImage.Warning);

            LoadSettingsIntoUi();
            UpdateSummaryDisplay();
            _isInitializing = false;
            if (Environment.GetCommandLineArgs().Contains("--setup-game", StringComparer.OrdinalIgnoreCase) ||
                string.IsNullOrWhiteSpace(_settingsMgr.Current.GamePath))
                ShowGameSetup();
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
            var res = GameValidator.Validate(_settingsMgr.Current.GamePath);
            if (res.IsValid)
            {
                TxtGameDetected.Text = $"MW3 Ready ({res.DetectedVersion})";
                TxtGameDetected.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                TxtValidationDetails.Text = res.StatusMessage;
                TxtValidationDetails.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                TxtStatusReady.Text = "● GAME STATUS: READY";
                TxtStatusReady.Foreground = (System.Windows.Media.Brush)FindResource("BrushAmber");
                BorderGameMissingAlert.Visibility = Visibility.Collapsed;
                BtnLaunchGame.Content = _settingsMgr.Current.EngineMode == "d7vk" ? "▶  LAUNCH ORIGINAL (D7VK)" : "▶  LAUNCH REMASTER";
                BtnLaunchGame.IsEnabled = true;
                try
                {
                    if (NativeRuntimeLayout.IsInstalledApplication(_basePath) || RuntimeUpdates.SelectedRoot(_basePath) != null)
                        NativeRuntimeLayout.FindInstalled(_basePath);
                }
                catch (Exception error)
                {
                    TxtStatusReady.Text = "● GAME STATUS: SETUP INCOMPLETE";
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

        private void BtnGameUpdates_Click(object sender, RoutedEventArgs e)
        {
            if (_nativeSessionActive)
            {
                MessageBox.Show(this, "Close the game before changing versions.", "Game updates");
                return;
            }
            try { new UpdatesWindow(_basePath, _settingsMgr.Current.GamePath) { Owner = this }.ShowDialog(); }
            catch (Exception error) { MessageBox.Show(this, error.Message, "Game updates"); }
            ValidateGamePath();
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

            // Remaster options
            SelectComboByTag(ComboWindowMode, string.IsNullOrEmpty(s.WindowMode) ? "fullscreen_windowed" : s.WindowMode, 0);
            var resTag = $"{s.Width}x{s.Height}";
            SelectComboByTag(ComboResolution, resTag, 2);
            SelectComboByTag(ComboAA, s.AntiAliasing, 0);
            SelectComboByTag(ComboAF, s.AnisotropicFiltering.ToString(), 0);
            SelectComboByTag(ComboDrawDist, s.DrawDistance.ToString(), 2);
            SelectComboByTag(ComboFog, s.FogDistance.ToString(), 0);
            ChkCdAudio.IsChecked = s.LocalCdAudio;
            ChkInstantReplay.IsChecked = s.InstantReplay;

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
            TxtEnvironmentMigration.Visibility = !s.EnvironmentPackSelectionInitialized &&
                GameRunner.FindRepositoryRoot(_basePath) != null && !Directory.Exists(Path.Combine(_basePath, "Runtime"))
                ? Visibility.Visible : Visibility.Collapsed;
            bool isD7Vk = s.EngineMode == "d7vk";

            if (TxtHeaderMode != null)
            {
                TxtHeaderMode.Text = isD7Vk ? "ORIGINAL (D7VK VULKAN)" : "NATIVE REMASTER";
            }
            if (TxtHeroBadge != null)
            {
                TxtHeroBadge.Text = isD7Vk ? "ORIGINAL MECH3.EXE + D7VK VULKAN" : "NATIVE VULKAN RECOMPILATION";
            }
            if (TxtHeroTitle != null)
            {
                TxtHeroTitle.Text = isD7Vk ? "MechWarrior 3 (Original Engine)" : "MechWarrior 3 Remastered";
            }
            if (TxtHeroDesc != null)
            {
                TxtHeroDesc.Text = isD7Vk
                    ? "Original 1999 game executable running through isolated DirectDraw Vulkan wrapper with widescreen FOV injection, MSAA, and 30 FPS physics lock."
                    : "Original game logic with Vulkan rendering, 1440p and ultrawide output, modern lighting, and registered model replacements.";
            }
            if (BtnLaunchGame != null && BtnLaunchGame.IsEnabled)
            {
                BtnLaunchGame.Content = isD7Vk ? "▶  LAUNCH ORIGINAL (D7VK)" : "▶  LAUNCH REMASTER";
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
                TxtSummaryDrawDist.Text = $"{s.DrawDistance}m ({(s.DrawDistance >= 2400 ? "Epic Distance" : "Standard")})";

                var activeCount = _packMgr.Packs.Count(p => p.IsEnabled);
                TxtSummaryPacks.Text = $"{activeCount} of {_packMgr.Packs.Count} Packs Active";
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

            if (ComboWindowMode != null && ComboWindowMode.SelectedItem is ComboBoxItem modeItem && modeItem.Tag is string modeStr)
            {
                s.WindowMode = modeStr;
                s.Fullscreen = (modeStr != "windowed");
            }

            if (ComboResolution != null && ComboResolution.SelectedItem is ComboBoxItem resItem && resItem.Tag is string resStr)
            {
                var parts = resStr.Split('x');
                if (parts.Length == 2 && int.TryParse(parts[0], out var w) && int.TryParse(parts[1], out var h))
                {
                    s.Width = w;
                    s.Height = h;
                }
            }

            if (ComboAA.SelectedItem is ComboBoxItem aaItem && aaItem.Tag is string aaStr)
            {
                s.AntiAliasing = aaStr;
            }

            if (ComboAF.SelectedItem is ComboBoxItem afItem && int.TryParse(afItem.Tag?.ToString(), out var af))
            {
                s.AnisotropicFiltering = af;
            }

            if (ComboDrawDist.SelectedItem is ComboBoxItem distItem && int.TryParse(distItem.Tag?.ToString(), out var dist))
            {
                s.DrawDistance = dist;
            }

            if (ComboFog.SelectedItem is ComboBoxItem fogItem && int.TryParse(fogItem.Tag?.ToString(), out var fog))
            {
                s.FogDistance = fog;
            }

            s.LocalCdAudio = ChkCdAudio.IsChecked == true;
            s.InstantReplay = ChkInstantReplay.IsChecked == true;

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
                            throw new InvalidOperationException("Close the Remaster game before removing content packs.");
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
            if (!BtnInstallPack.IsEnabled) throw new InvalidOperationException("A content installation is already running.");
            if (Process.GetProcessesByName("entry_commandline").Length > 0)
                throw new InvalidOperationException("Close the Remaster game before installing content packs.");
            BtnInstallPack.IsEnabled = false;
            BtnLaunchGame.IsEnabled = false;
            ListPacks.IsEnabled = false;
            var caption = BtnInstallPack.Content;
            BtnInstallPack.Content = "Verifying and installing...";
            try
            {
                var pack = await _packMgr.InstallPackAsync(file);
                // Persist each successful import even if a later pack fails or the batch is interrupted.
                _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
                _settingsMgr.Current.PackSelectionInitialized = true;
                if (pack.NativePayload?.Profile == "prepared-environment-v1")
                    _settingsMgr.Current.EnvironmentPackSelectionInitialized = true;
                _settingsMgr.Save();
                UpdateSummaryDisplay();
                return pack;
            }
            finally
            {
                BtnInstallPack.Content = caption;
                BtnInstallPack.IsEnabled = true;
                ListPacks.IsEnabled = true;
                ValidateGamePath();
            }
        }

        private async void BtnInstallPack_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Select Asset Pack (.mw3pack or .zip)",
                Filter = "MechWarrior 3 Asset Packs (*.mw3pack;*.zip)|*.mw3pack;*.zip|All Files (*.*)|*.*",
                Multiselect = true
            };

            if (dlg.ShowDialog() == true)
            {
                foreach (var file in dlg.FileNames)
                {
                    try
                    {
                        var installed = await InstallPackWithProgressAsync(file);
                        MessageBox.Show($"Successfully installed pack '{installed.Name}'!", "Pack Installed", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Failed to install '{Path.GetFileName(file)}':\n{ex.Message}", "Error Installing Pack", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }

                _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
                _settingsMgr.Save();
                UpdateSummaryDisplay();
            }
        }

        private void BtnRollbackPack_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is PackManifest pack)
            {
                try
                {
                    if (Process.GetProcessesByName("entry_commandline").Length > 0)
                        throw new InvalidOperationException("Close the Remaster game before changing installed versions.");
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
            var modsDir = _packMgr.ModsRoot;
            if (!Directory.Exists(modsDir)) Directory.CreateDirectory(modsDir);
            Process.Start(new ProcessStartInfo("explorer.exe", modsDir));
        }

        private void Window_DragOver(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
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
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                var files = (string[])e.Data.GetData(DataFormats.FileDrop);
                int installedCount = 0;
                foreach (var file in files)
                {
                    // Check if player dropped Mech3.exe or a folder containing Mech3.exe
                    if (Path.GetFileName(file).Equals("Mech3.exe", StringComparison.OrdinalIgnoreCase) ||
                        (Directory.Exists(file) && GameValidator.FindExecutableInDirectory(file) != null))
                    {
                        var dir = Directory.Exists(file) ? file : (Path.GetDirectoryName(file) ?? file);
                        _settingsMgr.Current.GamePath = dir;
                        _settingsMgr.Save();
                        TxtGamePath.Text = dir;
                        ValidateGamePath();
                        MessageBox.Show($"MechWarrior 3 location set to:\n{dir}\n\nStatus: {_settingsMgr.Current.GamePath}", "Game Folder Updated", MessageBoxButton.OK, MessageBoxImage.Information);
                        return;
                    }

                    var ext = Path.GetExtension(file).ToLowerInvariant();
                    if (ext == ".mw3pack" || ext == ".zip")
                    {
                        try
                        {
                            await InstallPackWithProgressAsync(file);
                            installedCount++;
                        }
                        catch (Exception ex)
                        {
                            MessageBox.Show($"Failed to install '{Path.GetFileName(file)}':\n{ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                        }
                    }
                }

                if (installedCount > 0)
                {
                    _settingsMgr.Current.ActivePacks = _packMgr.GetActivePackIds();
                    _settingsMgr.Save();
                    UpdateSummaryDisplay();
                    MessageBox.Show($"Successfully installed {installedCount} asset pack(s) via Drag & Drop!", "Packs Installed", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
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
            if (_nativeSessionActive) return;
            var setup = new GameSetupWindow(_settingsMgr.Current.GamePath) { Owner = this };
            if (setup.ShowDialog() != true || setup.GameDirectory == null) return;
            _settingsMgr.Current.GamePath = setup.GameDirectory;
            _settingsMgr.Save();
            TxtGamePath.Text = setup.GameDirectory;
            TxtMediaStatus.Text = "Original MW3 1.2 files verified.";
            ValidateGamePath();
            foreach (var file in setup.SelectedPacks)
            {
                TxtMediaStatus.Text = "Installing " + Path.GetFileName(file) + "…";
                try { await InstallPackWithProgressAsync(file); }
                catch (Exception ex)
                {
                    TxtMediaStatus.Text = "Original files verified. A pack needs attention; completed imports were saved.";
                    MessageBox.Show($"Could not install {Path.GetFileName(file)}:\n{ex.Message}\n\nYour verified game and completed pack imports are preserved. Retry through Mods & Packs → Install Pack.",
                        "Pack installation", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }
            if (setup.SelectedPacks.Length > 0) TxtMediaStatus.Text = "Original files verified and selected packs installed.";
        }

        private void BtnAddToSteam_Click(object sender, RoutedEventArgs e)
        {
            var launcherExe = Process.GetCurrentProcess().MainModule?.FileName ?? Path.Combine(_basePath, "MW3RemasterLauncher.exe");
            var artworkDir = Path.Combine(_basePath, "Assets", "Plates");

            bool ok = SteamHelper.AddToSteam(launcherExe, artworkDir);
            if (ok)
            {
                _settingsMgr.Current.HasAddedToSteam = true;
                _settingsMgr.Save();
                MessageBox.Show("MechWarrior 3 Remastered was successfully added to your Steam library!\n\nPlease restart Steam if it is currently running to see the game and artwork.",
                    "Steam Integration", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                MessageBox.Show("Could not automatically locate your Steam installation or user profile.\nPlease ensure Steam is installed on this PC.",
                    "Steam Integration", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void BtnLaunchGame_Click(object sender, RoutedEventArgs e)
        {
            var s = _settingsMgr.Current;

            if (s.EngineMode == "d7vk")
            {
                var val = _d7vkRunner.Validate();
                if (!val.IsValid)
                {
                    MessageBox.Show($"Cannot launch Original Game with D7VK:\n\n{val.StatusMessage}\n\n" +
                                    "Please ensure Python 3 is installed and the D7VK wrapper components exist in local/work-ahead/mw3-d7vk-wrapper.",
                                    "D7VK Wrapper Launch Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                try
                {
                    BtnLaunchGame.IsEnabled = false;
                    BtnLaunchGame.Content = "●  GAME RUNNING (D7VK)...";
                    TxtStatusReady.Text = "● GAME STATUS: ORIGINAL MECH3 (D7VK) RUNNING";

                    if (_packMgr.Packs.Any(p => p.IsEnabled && p.SchemaVersion == 2))
                        throw new InvalidOperationException("Prepared native mech packs require the Remaster engine. Disable them before launching D7VK.");
                    var proc = _d7vkRunner.LaunchGame(s, log =>
                    {
                        System.Diagnostics.Debug.WriteLine(log);
                    });

                    proc.EnableRaisingEvents = true;
                    proc.Exited += (sObj, args) =>
                    {
                        Dispatcher.Invoke(() =>
                        {
                            BtnLaunchGame.IsEnabled = true;
                            BtnLaunchGame.Content = "▶  LAUNCH ORIGINAL (D7VK)";
                            TxtStatusReady.Text = "● GAME STATUS: READY";
                        });
                    };
                }
                catch (Exception ex)
                {
                    BtnLaunchGame.IsEnabled = true;
                    BtnLaunchGame.Content = "▶  LAUNCH ORIGINAL (D7VK)";
                    MessageBox.Show($"Failed to launch Original Game (D7VK Wrapper):\n\n{ex.Message}", "Launch Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            else
            {
                var validation = GameValidator.Validate(_settingsMgr.Current.GamePath);
                if (!validation.IsValid)
                {
                    BtnBrowseGamePath_Click(sender, e);
                    return;
                }

                try
                {
                    var activeDirs = _packMgr.GetActivePackDirectories();
                    SettingControl_Changed(sender, e);
                    _nativeSessionActive = true;
                    BtnLaunchGame.IsEnabled = false;
                    BtnInstallPack.IsEnabled = false;
                    ListPacks.IsEnabled = false;
                    BtnLaunchGame.Content = "●  PREPARING REMASTER...";
                    TxtStatusReady.Text = "● GAME STATUS: PREPARING ASSETS";
                    TxtStartupProgress.Text = "Checking content…";
                    var proc = _gameRunner.LaunchGame(_settingsMgr.Current, activeDirs, line =>
                    {
                        if (line.StartsWith("Startup: ", StringComparison.Ordinal))
                            Dispatcher.BeginInvoke(new Action(() =>
                            {
                                if (!_nativeSessionActive) return;
                                TxtStartupProgress.Text = line[9..].Replace(
                                    " First startup can take several minutes depending on your PC and storage speed.", "",
                                    StringComparison.Ordinal);
                                BtnLaunchGame.Content = "●  PREPARING REMASTER...";
                            }));
                        if (line.StartsWith("Native Remaster PID "))
                            Dispatcher.BeginInvoke(new Action(() =>
                            {
                                if (!_nativeSessionActive) return;
                                BtnLaunchGame.Content = "●  GAME RUNNING (REMASTER)...";
                                TxtStatusReady.Text = "● GAME STATUS: REMASTER HOST RUNNING";
                                TxtStartupProgress.Text = "The game process has started.";
                            }));
                    });
                    if (proc == null) throw new InvalidOperationException("The game launch did not start.");
                    _ = ObserveNativeCompletionAsync(proc);
                }
                catch (Exception ex)
                {
                    ResetNativeLaunchControls();
                    TxtStatusReady.Text = "⚠ LAUNCH FAILED — OPEN LOGS FOR DETAILS";
                    MessageBox.Show($"Failed to launch MechWarrior 3 Remaster:\n\n{ex.Message}\n\nUse Open Logs or Export Report under Settings & Steam.", "Launch Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void ResetNativeLaunchControls()
        {
            _nativeSessionActive = false;
            BtnLaunchGame.IsEnabled = true;
            BtnInstallPack.IsEnabled = true;
            ListPacks.IsEnabled = true;
            BtnLaunchGame.Content = "▶  LAUNCH REMASTER";
        }

        private async System.Threading.Tasks.Task ObserveNativeCompletionAsync(Process process)
        {
            try
            {
                var exit = await GameRunner.WaitForCompletionAsync(process);
                ResetNativeLaunchControls();
                TxtStatusReady.Text = exit == 0 ? "● GAME STATUS: READY" : "⚠ LAUNCH OR GAME FAILED";
                if (exit != 0)
                    MessageBox.Show(PlaytestDiagnostics.FailureSummary(_gameRunner.LastLogPath) +
                        "\n\nUse Open Logs or Export Report under Settings & Steam.",
                        "Remaster stopped (exit " + exit + ")", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            catch (Exception ex)
            {
                ResetNativeLaunchControls();
                TxtStatusReady.Text = "⚠ COULD NOT READ GAME EXIT STATUS";
                MessageBox.Show(ex.Message, "Game session details", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally { process.Dispose(); }
        }

        private void BtnOpenLogs_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var log = _gameRunner.LastLogPath ?? LauncherPaths.LatestLaunchLog();
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
                    registry = Path.Combine(LauncherPaths.DataRoot, "native-settings", "mw3-registry.txt");
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

        private void BtnExportReport_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new SaveFileDialog
            {
                Title = "Save playtest troubleshooting report", Filter = "Troubleshooting report (*.zip)|*.zip",
                FileName = "MW3-Playtest-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".zip"
            };
            if (dialog.ShowDialog() != true) return;
            try
            {
                PlaytestDiagnostics.Export(dialog.FileName, _settingsMgr.Current, _packMgr.Packs,
                    _gameRunner.LastLogPath ?? LauncherPaths.LatestLaunchLog(), _basePath);
                MessageBox.Show("Report saved. It contains build/system details, selected settings, pack metadata and redacted recent log tails. Review it before sharing.",
                    "Playtest report saved", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex) { MessageBox.Show(ex.Message, "Cannot export report", MessageBoxButton.OK, MessageBoxImage.Error); }
        }

        private void BtnOpenScreenshots_Click(object sender, RoutedEventArgs e)
        {
            OpenSubFolder("local/screenshots");
        }

        private void BtnOpenReplays_Click(object sender, RoutedEventArgs e)
        {
            OpenSubFolder("local/replays");
        }

        private void BtnOpenVideos_Click(object sender, RoutedEventArgs e)
        {
            OpenSubFolder("local/videos");
        }

        private void OpenSubFolder(string relative)
        {
            var rootDir = Path.GetFullPath(Path.Combine(_basePath, @"..\.."));
            var target = Path.Combine(rootDir, relative);
            if (!Directory.Exists(target)) Directory.CreateDirectory(target);
            Process.Start(new ProcessStartInfo("explorer.exe", target));
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
