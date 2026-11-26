using System.ComponentModel;
using System.IO;
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Data;
using System.Windows.Interop;
using System.Windows.Media;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public partial class ControlsWindow : Window
{
    private readonly ControlProfiles store;
    private readonly SettingsManager settingsManager;
    private readonly string dataRoot, gamePath;
    private bool initializingJoysticks = true;
    private bool? controllerLayoutEnabled;
    private ControlDocument document = new();
    private ControlProfile? working;
    private string? savedId;
    private bool initializing = true, dirty, loadFailed;
    private enum CaptureMode { None, KeyboardPrimary, KeyboardSecondary, MouseBinding }
    private CaptureMode captureMode = CaptureMode.None;
    private string? captureAction;
    private int nativeVirtualKey, nativeScan;
    private enum JoystickChoiceKind { Automatic, None, Device, Unavailable }
    private sealed record JoystickChoiceItem(string Label, string InstanceGuid, string ProductName,
        JoystickChoiceKind Kind);
    public sealed record BindingRow(string Action, string Label, string Group, string Primary, string Secondary, string Mouse, string Combos);
    public ControlsWindow(string dataRoot, string gamePath, SettingsManager? settingsManager = null)
    {
        this.dataRoot = dataRoot; this.gamePath = gamePath; store = new(dataRoot);
        this.settingsManager = settingsManager ?? new SettingsManager(dataRoot, dataRoot);
        InitializeComponent();
        HookPhysicalKeys(this, (vk, scan) => { nativeVirtualKey = vk; nativeScan = scan; });
        try { document = store.Load(); }
        catch (Exception ex) { loadFailed = true; Editor.IsEnabled = false; Status.Text = "Controls could not be loaded. The saved file is preserved. " + ex.Message; }
        LoadJoystickChoices();
        Game.ItemsSource = GameCatalog.Games; Game.SelectedIndex = 0;
        Profiles.ItemsSource = document.Profiles;
        UpdateActive(); initializing = false;
        Profiles.SelectedItem = document.Profiles.FirstOrDefault(p => p.Id == document.ActiveId) ?? document.Profiles.FirstOrDefault();
        Closing += (_, _) => CancelCapture();
        Deactivated += (_, _) => { if (captureMode != CaptureMode.None) { CancelCapture(); Status.Text = "Assignment canceled."; } };
        PreviewGotKeyboardFocus += (_, e) => { if (captureMode == CaptureMode.MouseBinding) { CancelCapture(); Status.Text = "Assignment canceled."; } };
    }
    private void CancelCapture()
    {
        captureMode = CaptureMode.None;
        captureAction = null;
    }
    private void OpenHeadlightBindings(object sender, RoutedEventArgs e)
    {
        CancelCapture();
        try { new HeadlightBindingsWindow(dataRoot) { Owner = this }.ShowDialog(); }
        catch (Exception ex) { Status.Text = "Headlight controls could not be loaded. " + ex.Message; }
    }
    private void LoadJoystickChoices()
    {
        initializingJoysticks = true;
        try
        {
            var settings = settingsManager.Current;
            var attached = DirectInputJoystickCatalog.EnumerateAttached();
            try
            {
                controllerLayoutEnabled = new ControllerProfiles(dataRoot).Load().Enabled;
            }
            catch
            {
                controllerLayoutEnabled = null;
            }

            var choices = new List<JoystickChoiceItem>
            {
                new("Windows default (first attached joystick)", "", "", JoystickChoiceKind.Automatic),
                new("None", "", "", JoystickChoiceKind.None)
            };
            foreach (var device in attached)
            {
                var label = device.DisplayName;
                if (attached.Count(other => other.DisplayName == label) > 1)
                {
                    label += " [" + device.InstanceGuid[^8..] + "]";
                }

                choices.Add(new JoystickChoiceItem(label, device.InstanceGuid, device.ProductName,
                    JoystickChoiceKind.Device));
            }

            var instanceGuid = settings.DirectInputJoystickInstanceGuid?.Trim() ?? string.Empty;
            var productName = settings.DirectInputJoystickProductName?.Trim() ?? string.Empty;
            JoystickChoiceItem selected;
            if (settings.DirectInputJoystickNone)
            {
                selected = choices[1];
            }
            else if (instanceGuid.Length == 0 && productName.Length == 0)
            {
                selected = choices[0];
            }
            else
            {
                var resolved = DirectInputJoystickSelection.Resolve(settings, attached);
                selected = resolved == null
                    ? new JoystickChoiceItem("Saved joystick is not attached — " + productName,
                        instanceGuid, productName, JoystickChoiceKind.Unavailable)
                    : choices.First(choice => choice.Kind == JoystickChoiceKind.Device &&
                        Guid.TryParse(choice.InstanceGuid, out var choiceGuid) &&
                        Guid.TryParse(resolved.InstanceGuid, out var resolvedGuid) && choiceGuid == resolvedGuid);
                if (resolved == null)
                {
                    choices.Add(selected);
                }
            }

            JoystickChoice.ItemsSource = choices;
            JoystickChoice.SelectedItem = selected;
            JoystickChoice.IsEnabled = true;
            JoystickStatus.Text = attached.Count == 0
                ? "No attached DirectInput joysticks were found. " + ControllerLayoutHint()
                : ControllerLayoutHint();
        }
        catch (Exception error)
        {
            JoystickChoice.ItemsSource = Array.Empty<JoystickChoiceItem>();
            JoystickChoice.IsEnabled = false;
            JoystickStatus.Text = "DirectInput devices could not be listed. The saved joystick choice was left unchanged. " +
                error.Message;
        }
        finally
        {
            initializingJoysticks = false;
        }
    }
    private void RefreshJoystickChoices(object sender, RoutedEventArgs e) => LoadJoystickChoices();
    private void JoystickChoiceChanged(object sender, SelectionChangedEventArgs e)
    {
        if (initializingJoysticks || JoystickChoice.SelectedItem is not JoystickChoiceItem choice ||
            choice.Kind == JoystickChoiceKind.Unavailable)
        {
            return;
        }

        var settings = settingsManager.Current;
        var previousGuid = settings.DirectInputJoystickInstanceGuid;
        var previousName = settings.DirectInputJoystickProductName;
        var previousNone = settings.DirectInputJoystickNone;
        settings.DirectInputJoystickNone = choice.Kind == JoystickChoiceKind.None;
        settings.DirectInputJoystickInstanceGuid = choice.Kind == JoystickChoiceKind.Device
            ? choice.InstanceGuid
            : string.Empty;
        settings.DirectInputJoystickProductName = choice.Kind == JoystickChoiceKind.Device
            ? choice.ProductName
            : string.Empty;
        try
        {
            settingsManager.Save();
            JoystickStatus.Text = "Joystick choice saved. " + ControllerLayoutHint();
        }
        catch (Exception error)
        {
            settings.DirectInputJoystickInstanceGuid = previousGuid;
            settings.DirectInputJoystickProductName = previousName;
            settings.DirectInputJoystickNone = previousNone;
            LoadJoystickChoices();
            JoystickStatus.Text = "Joystick choice was not saved. " + error.Message;
        }
    }
    internal static void HookPhysicalKeys(Window window, Action<int, int> onKey)
    {
        IntPtr handle = IntPtr.Zero;
        void Filter(ref MSG msg, ref bool handled)
        {
            if (msg.hwnd == handle && msg.message is 0x100 or 0x104)
            {
                var parameters = msg.lParam.ToInt64();
                var scan = ((int)(parameters >> 16) & 255) | (((parameters >> 24) & 1) != 0 ? 128 : 0);
                onKey((int)msg.wParam, scan);
            }
        }
        window.SourceInitialized += (_, _) =>
        {
            handle = ((HwndSource)PresentationSource.FromVisual(window)!).Handle;
            // ThreadFilterMessage fires before WPF dispatches PreviewKeyDown.
            ComponentDispatcher.ThreadFilterMessage += Filter;
        };
        window.Closed += (_, _) => ComponentDispatcher.ThreadFilterMessage -= Filter;
    }
    private bool DiscardChanges() => !dirty || MessageBox.Show(this, "Discard the unsaved changes to this layout?", "Unsaved controls", MessageBoxButton.YesNo) == MessageBoxResult.Yes;
    private void OpenControllerSetup(object sender, RoutedEventArgs e)
    {
        CancelCapture();
        new ControllerWindow(dataRoot) { Owner = this }.ShowDialog();
        LoadJoystickChoices();
    }
    private string ControllerLayoutHint() => controllerLayoutEnabled switch
    {
        true => "Controller setup is enabled and uses a separate SDL input path; this DirectInput choice is bypassed.",
        false => "This choice applies on the next native MW3 launch. Controller setup is a separate SDL input path.",
        _ => "Controller setup status is unavailable. This choice applies to DirectInput on the next launch."
    };
    private static void RequireClosedForImport()
    {
        foreach (var name in new[] { "entry_commandline", "Mech3", "MW3RemasterNative" })
        {
            var games = System.Diagnostics.Process.GetProcessesByName(name);
            try { if (games.Length > 0) throw new InvalidOperationException("Close MechWarrior 3 before copying or resetting its controls. You can still edit saved layouts."); }
            finally { foreach (var game in games) game.Dispose(); }
        }
    }
    internal static bool TryCancelInteractiveLeftClick(
        DependencyObject? source,
        ButtonBase? captureButton,
        Func<ButtonBase, bool>? isCaptureButtonPredicate,
        Action cancel,
        out bool handled)
    {
        handled = false;
        for (var current = source; current != null;)
        {
            if (current is ButtonBase btn)
            {
                handled = (captureButton != null && ReferenceEquals(btn, captureButton))
                    || (isCaptureButtonPredicate != null && isCaptureButtonPredicate(btn));
                cancel();
                return true;
            }
            if (current is DataGridRow or DataGridColumnHeader or ListBoxItem or ComboBox or ComboBoxItem or CheckBox or TextBoxBase or ScrollBar or MenuItem)
            {
                cancel();
                return true;
            }
            current = current is Visual or System.Windows.Media.Media3D.Visual3D
                ? VisualTreeHelper.GetParent(current)
                : LogicalTreeHelper.GetParent(current);
        }
        return false;
    }
    private void CancelCaptureOnClick(object sender, MouseButtonEventArgs e)
    {
        if (captureMode == CaptureMode.MouseBinding)
        {
            // The arming click on "Set mouse" already finished (Click fires on MouseUp, after this
            // PreviewMouseDown), so the next press anywhere is the mouse button to bind.
            if (e.ChangedButton == MouseButton.Left &&
                TryCancelInteractiveLeftClick(e.OriginalSource as DependencyObject, null,
                    btn => Equals(btn.Content, "Set mouse"),
                    () => { CancelCapture(); Status.Text = "Mouse assignment canceled."; },
                    out var cancelHandled))
            {
                // A left click on a button or other interactive control cancels the capture instead of
                // binding the click. Only the "Set mouse" button itself is marked handled so its Click
                // does not immediately re-arm the capture; every other control still gets the click.
                if (cancelHandled) e.Handled = true;
                return;
            }
            var value = e.ChangedButton switch
            {
                MouseButton.Left => 1,
                MouseButton.Right => 2,
                MouseButton.Middle => 3,
                MouseButton.XButton1 => 4,
                MouseButton.XButton2 => 5,
                _ => 0
            };
            if (value != 0)
            {
                e.Handled = true;
                ApplyMouse(value);
            }
            return;
        }
        if (captureMode != CaptureMode.None)
        {
            CancelCapture();
            Status.Text = "Key assignment canceled.";
        }
    }
    private void CaptureMouseWheel(object sender, MouseWheelEventArgs e)
    {
        if (captureMode != CaptureMode.MouseBinding || e.Delta == 0) return; // otherwise the grid scrolls normally
        e.Handled = true;
        ApplyMouse(e.Delta > 0 ? 6 : 7);
    }
    private void ProfileChanged(object sender, SelectionChangedEventArgs e)
    {
        if (initializing) return;
        CancelCapture();
        if (!DiscardChanges())
        {
            initializing = true; Profiles.SelectedItem = document.Profiles.FirstOrDefault(p => p.Id == savedId); initializing = false; return;
        }
        if (Profiles.SelectedItem is ControlProfile p) Edit(p, p.Id);
    }
    private void Edit(ControlProfile p, string? id)
    {
        CancelCapture(); working = ControlProfiles.Clone(p, p.Name); working.Id = id ?? p.Id; savedId = id;
        ProfileEditor.IsEnabled = true; SaveButton.IsEnabled = UseButton.IsEnabled = true;
        initializing = true; ProfileName.Text = p.Name; Search.Text = ""; Mw2JumpJets.IsChecked = working.Mw2JumpJets; initializing = false;
        dirty = id == null; RefreshRows();
        LayoutDescription.Text = p.Description;
        Status.Text = "Select an action to change its bindings. Saving does not change the active game session.";
    }
    private IEnumerable<string> RegistryCandidates()
    {
        yield return Path.Combine(dataRoot, "native-settings", "mw3-registry.txt");
        yield return Path.Combine(gamePath, "mw34-registry.txt");
        var root = GameRunner.FindRepositoryRoot(AppDomain.CurrentDomain.BaseDirectory);
        if (root != null)
        {
            var json = JsonNode.Parse(File.ReadAllText(Path.Combine(root, "local/remaster/launcher.json")));
            var source = json?["native"]?["runtime_environment"]?["MW34_REG_OVERLAY"]?.GetValue<string>();
            if (source != null) yield return Path.GetFullPath(source, root);
        }
    }
    private void ImportCurrent(object sender, RoutedEventArgs e)
    {
        if (!DiscardChanges()) return;
        try
        {
            // A running game can be rewriting its registry. Do not import a partial map.
            RequireClosedForImport();
            var p = store.ImportCurrent(RegistryCandidates());
            p.Name = document.Profiles.Count == 0 ? "My MW3 controls" : "MW3 layout " + (document.Profiles.Count + 1);
            initializing = true; Profiles.SelectedItem = null; initializing = false; Edit(p, null);
        }
        catch (Exception ex) { Status.Text = ex.Message; }
    }
    private static string FormatCombos(ControlBinding b)
    {
        var combos = b.Combos;
        if (combos == null || combos.Count == 0) return "None";
        if (combos.Count == 1) return ComboEditorWindow.FormatCombo(combos[0]);
        return combos.Count + " combos: " + string.Join(", ", combos.Select(ComboEditorWindow.FormatCombo));
    }
    private void RefreshRows()
    {
        if (working == null) return;
        var selected = (Bindings.SelectedItem as BindingRow)?.Action;
        var filter = Search.Text.Trim();
        var rows = ControlProfiles.Actions.Select(a => {
            var b = working.Bindings[a.Name];
            return new BindingRow(a.Name, a.Label, a.Group, ControlKeys.Label(b.Primary), ControlKeys.Label(b.Secondary), ControlKeys.MouseLabel(b.Mouse), FormatCombos(b));
        }).Where(r => filter.Length == 0 || (r.Label + " " + r.Group).Contains(filter, StringComparison.CurrentCultureIgnoreCase)).OrderBy(r => r.Group).ThenBy(r => r.Label).ToArray();
        var view = new ListCollectionView(rows);
        view.GroupDescriptions.Add(new PropertyGroupDescription(nameof(BindingRow.Group)));
        Bindings.ItemsSource = view; Bindings.SelectedItem = rows.FirstOrDefault(r => r.Action == selected);
        var conflicts = ControlProfiles.Conflicts(working);
        ConflictSummary.Text = conflicts.Count == 0 ? "F9–F11 are reserved for capture, replay and photo mode. Joystick bindings are retained; axis settings are not edited here." :
            $"{conflicts.Count} existing shared input(s). New assignments cannot add conflicts. " + string.Join(" • ", conflicts.Take(2));
    }
    private void NameChanged(object sender, TextChangedEventArgs e) { if (!initializing && working != null) { working.Name = ProfileName.Text; dirty = true; } }
    private void FilterChanged(object sender, TextChangedEventArgs e) { if (!initializing) RefreshRows(); }
    private void JumpJetsChanged(object sender, RoutedEventArgs e)
    {
        if (initializing || working == null) return;
        working.Mw2JumpJets = Mw2JumpJets.IsChecked;
        dirty = true;
        Status.Text = Mw2JumpJets.IsChecked switch
        {
            true => "MW2 Jump Jets selected for this layout. Save the layout to keep it.",
            false => "Classic MW3 jump jets selected for this layout. Save the layout to keep it.",
            _ => "Jump jets follow the game setting for this layout. Save the layout to keep it."
        };
    }
    private void BindingChanged(object sender, SelectionChangedEventArgs e) { CancelCapture(); BindingButtons.IsEnabled = Bindings.SelectedItem is BindingRow; }
    private void ResetOriginal(object sender, RoutedEventArgs e)
    {
        if (working == null) { Status.Text = "Select a saved layout or copy your current controls first."; return; }
        try
        {
            RequireClosedForImport();
            var original = store.ImportOriginal(RegistryCandidates());
            if (MessageBox.Show(this, "Reset this layout's bindings to your original game controls? Save afterward to keep the reset.", "Reset layout", MessageBoxButton.YesNo) != MessageBoxResult.Yes) return;
            working.Bindings = original.Bindings; working.Description = ""; LayoutDescription.Text = "";
            working.Mw2JumpJets = original.Mw2JumpJets;
            initializing = true; Mw2JumpJets.IsChecked = working.Mw2JumpJets; initializing = false;
            dirty = true; RefreshRows(); Status.Text = "Original bindings copied into this layout. Save to keep the reset.";
        }
        catch (Exception ex) { Status.Text = ex.Message; }
    }
    private void BeginCapture(bool secondary)
    {
        if (Bindings.SelectedItem is not BindingRow row) return;
        captureMode = secondary ? CaptureMode.KeyboardSecondary : CaptureMode.KeyboardPrimary;
        captureAction = row.Action;
        Status.Text = $"Press the {(secondary ? "secondary" : "primary")} key for {row.Label}. Escape cancels; use Clear to remove a binding.";
        Focus();
    }
    private void SetPrimary(object sender, RoutedEventArgs e) => BeginCapture(false);
    private void SetSecondary(object sender, RoutedEventArgs e) => BeginCapture(true);
    private void ClearPrimary(object sender, RoutedEventArgs e) => ChangeKey(false, 0);
    private void ClearSecondary(object sender, RoutedEventArgs e) => ChangeKey(true, 0);
    private void ChangeKey(bool secondary, int key)
    {
        if (working == null || Bindings.SelectedItem is not BindingRow row) return;
        var conflict = working.Bindings.FirstOrDefault(x => x.Key != row.Action && key != 0 && (x.Value.Primary == key || x.Value.Secondary == key));
        if (conflict.Key != null) throw new InvalidOperationException(ControlKeys.Label(key) + " is already assigned to " + ControlProfiles.Actions.First(a => a.Name == conflict.Key).Label + ". Clear that assignment first.");
        var b = working.Bindings[row.Action];
        if (key != 0 && (secondary ? b.Primary : b.Secondary) == key) throw new InvalidOperationException("That key is already assigned to this action.");
        if (secondary) b.Secondary = key; else b.Primary = key;
        dirty = true; CancelCapture(); RefreshRows(); Status.Text = "Binding changed. Save the layout to keep it.";
    }
    private void CaptureKey(object sender, KeyEventArgs e)
    {
        if (captureMode == CaptureMode.None) return;
        var key = e.Key == Key.System ? e.SystemKey : e.Key;
        if (captureMode == CaptureMode.MouseBinding)
        {
            // Checked before the IsRepeat guard so a held Tab still disarms mouse capture.
            if (key == Key.Escape) { e.Handled = true; CancelCapture(); Status.Text = "Assignment canceled."; }
            else if (key == Key.Tab) { CancelCapture(); Status.Text = "Assignment canceled."; }
            return;
        }
        if (e.IsRepeat) return;
        e.Handled = true; // swallow Alt+Tab and friends so the assignment is not interrupted
        if (key == Key.Escape) { CancelCapture(); Status.Text = "Assignment canceled."; return; }
        if (key is Key.LeftShift or Key.RightShift or Key.LeftCtrl or Key.RightCtrl or Key.LeftAlt or Key.RightAlt) return;
        try { ChangeKey(captureMode == CaptureMode.KeyboardSecondary, ControlKeys.Capture(key, Keyboard.Modifiers,
            nativeVirtualKey == KeyInterop.VirtualKeyFromKey(key) ? nativeScan : null)); }
        catch (Exception ex) { Status.Text = ex.Message; }
    }
    private void BeginMouseCapture(object sender, RoutedEventArgs e)
    {
        if (Bindings.SelectedItem is not BindingRow row) return;
        Focus(); // focus first so the focus call does not hit PreviewGotKeyboardFocus while the capture is armed
        captureMode = CaptureMode.MouseBinding; captureAction = row.Action;
        Status.Text = $"Click a mouse button or scroll the wheel for {row.Label}. Escape cancels.";
    }
    private bool TryAssignMouse(string actionName, int value)
    {
        if (working == null) return false;
        if (value != 0 && working.Bindings.Any(b => b.Key != actionName && b.Value.Mouse == value))
        {
            Status.Text = ControlKeys.MouseLabel(value) + " is already assigned to another action. Clear it there first; the binding was left unchanged.";
            return false;
        }
        working.Bindings[actionName].Mouse = value;
        dirty = true; RefreshRows();
        Status.Text = "Mouse binding changed. Save the layout to keep it.";
        return true;
    }
    private void ApplyMouse(int value)
    {
        if (working == null || captureAction == null) return;
        TryAssignMouse(captureAction, value);
        CancelCapture();
    }
    private void SetMouse(object sender, RoutedEventArgs e)
    {
        CancelCapture();
        if (working == null || Bindings.SelectedItem is not BindingRow row) return;
        var menu = new ContextMenu();
        for (var n = 0; n <= 7; n++)
        {
            int value = n;
            var item = new MenuItem { Header = ControlKeys.MouseLabel(value) };
            item.Click += (_, _) => TryAssignMouse(row.Action, value);
            menu.Items.Add(item);
        }
        menu.PlacementTarget = (Button)sender; menu.IsOpen = true;
    }
    private void ClearMouse(object sender, RoutedEventArgs e)
    {
        CancelCapture();
        if (working == null || Bindings.SelectedItem is not BindingRow row) return;
        working.Bindings[row.Action].Mouse = 0; dirty = true; RefreshRows();
        Status.Text = "Mouse binding cleared. Save the layout to keep it.";
    }
    private void EditCombos(object sender, RoutedEventArgs e)
    {
        if (working == null || Bindings.SelectedItem is not BindingRow row) return;
        CancelCapture();
        var editor = new ComboEditorWindow(working, row.Action) { Owner = this };
        var before = System.Text.Json.JsonSerializer.Serialize(working.Bindings[row.Action].Combos);
        if (editor.ShowDialog() == true && System.Text.Json.JsonSerializer.Serialize(working.Bindings[row.Action].Combos) != before)
        {
            dirty = true; RefreshRows();
            Status.Text = "Combos changed. Save the layout to keep them.";
        }
    }
    private bool Persist(bool use)
    {
        if (working == null) return false;
        CancelCapture();
        try
        {
            var next = System.Text.Json.JsonSerializer.Deserialize<ControlDocument>(System.Text.Json.JsonSerializer.Serialize(document))!;
            next.Profiles.RemoveAll(p => p.Id == working.Id);
            next.Profiles.Add(working);
            if (use) next.ActiveId = working.Id;
            store.Save(next); document = next; savedId = working.Id; dirty = false;
            initializing = true; Profiles.ItemsSource = document.Profiles; Profiles.SelectedItem = working; initializing = false;
            working = ControlProfiles.Clone(working, working.Name); working.Id = savedId;
            UpdateActive(); Status.Text = use ? "Saved. This layout will be applied on the next native MW3 launch." : "Layout saved. The active selection is unchanged."; return true;
        }
        catch (Exception ex) { Status.Text = "Layout was not saved. " + ex.Message; return false; }
    }
    private void SaveProfile(object sender, RoutedEventArgs e) => Persist(false);
    private void UseProfile(object sender, RoutedEventArgs e) => Persist(true);
    private void UseGameControls(object sender, RoutedEventArgs e)
    {
        try { var next = store.Load(); next.ActiveId = null; store.Save(next); document.ActiveId = null; UpdateActive(); Status.Text = "Your original game controls will be restored on the next native launch. Saved layouts are kept."; }
        catch (Exception ex) { Status.Text = ex.Message; }
    }
    private void UpdateActive() => ActiveSummary.Text = document.ActiveId == null ? "Active: game's own controls" : "Next launch: " + document.Profiles.Single(p => p.Id == document.ActiveId).Name;
    private void GameChanged(object sender, SelectionChangedEventArgs e)
    {
        if (Editor == null) return;
        var supported = (Game.SelectedItem as GameDefinition)?.Id == GameCatalog.Mw3;
        Editor.IsEnabled = supported && !loadFailed;
        JoystickSection.IsEnabled = supported;
        SaveButton.IsEnabled = UseButton.IsEnabled = supported && !loadFailed && working != null;
        if (!supported) { CancelCapture(); ActiveSummary.Text = "Controls not available yet"; Status.Text = "Controls for this game will be available when its runtime is supported. MW3 layouts remain separate."; }
        else if (!initializing && !loadFailed) { UpdateActive(); Status.Text = "Select or copy a MW3 layout. In-game edits are not saved into a launcher layout automatically."; }
    }
    private void OnClosing(object? sender, CancelEventArgs e)
    {
        CancelCapture();
        if (!DiscardChanges()) e.Cancel = true;
    }
    private void CloseWindow(object sender, RoutedEventArgs e) => Close();
}
