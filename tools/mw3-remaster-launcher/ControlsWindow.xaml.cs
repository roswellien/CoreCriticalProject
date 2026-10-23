using System.ComponentModel;
using System.IO;
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Data;
using System.Windows.Interop;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public partial class ControlsWindow : Window
{
    private readonly ControlProfiles store;
    private readonly string dataRoot, gamePath;
    private ControlDocument document = new();
    private ControlProfile? working;
    private string? savedId;
    private bool initializing = true, dirty, loadFailed;
    private (string Action, bool Secondary)? capture;
    private int nativeVirtualKey, nativeScan;
    public sealed record BindingRow(string Action, string Label, string Group, string Primary, string Secondary, string Mouse);
    public ControlsWindow(string dataRoot, string gamePath)
    {
        this.dataRoot = dataRoot; this.gamePath = gamePath; store = new(dataRoot);
        InitializeComponent();
        SourceInitialized += (_, _) => ((HwndSource)PresentationSource.FromVisual(this)).AddHook(RecordNativeKey);
        try { document = store.Load(); }
        catch (Exception ex) { loadFailed = true; Editor.IsEnabled = false; Status.Text = "Controls could not be loaded. The saved file is preserved. " + ex.Message; }
        Game.ItemsSource = GameCatalog.Games; Game.SelectedIndex = 0;
        Profiles.ItemsSource = document.Profiles;
        UpdateActive(); initializing = false;
        Profiles.SelectedItem = document.Profiles.FirstOrDefault(p => p.Id == document.ActiveId) ?? document.Profiles.FirstOrDefault();
        Closing += (_, _) => capture = null;
    }
    private IntPtr RecordNativeKey(IntPtr window, int message, IntPtr key, IntPtr parameters, ref bool handled)
    {
        if (message is 0x100 or 0x104) // WM_KEYDOWN / WM_SYSKEYDOWN, scoped to this editor window.
        {
            nativeVirtualKey = (int)key;
            nativeScan = ((int)((long)parameters >> 16) & 255) | ((((long)parameters >> 24) & 1) != 0 ? 128 : 0);
        }
        return IntPtr.Zero;
    }
    private bool DiscardChanges() => !dirty || MessageBox.Show(this, "Discard the unsaved changes to this layout?", "Unsaved controls", MessageBoxButton.YesNo) == MessageBoxResult.Yes;
    private void OpenControllerSetup(object sender, RoutedEventArgs e)
    {
        capture = null;
        new ControllerWindow(dataRoot) { Owner = this }.ShowDialog();
    }
    private static void RequireClosedForImport()
    {
        foreach (var name in new[] { "entry_commandline", "Mech3", "MW3RemasterNative" })
        {
            var games = System.Diagnostics.Process.GetProcessesByName(name);
            try { if (games.Length > 0) throw new InvalidOperationException("Close MechWarrior 3 before copying or resetting its controls. You can still edit saved layouts."); }
            finally { foreach (var game in games) game.Dispose(); }
        }
    }
    private void CancelCaptureOnClick(object sender, MouseButtonEventArgs e)
    {
        if (capture != null) { capture = null; Status.Text = "Key assignment canceled."; }
    }
    private void ProfileChanged(object sender, SelectionChangedEventArgs e)
    {
        if (initializing) return;
        if (!DiscardChanges())
        {
            initializing = true; Profiles.SelectedItem = document.Profiles.FirstOrDefault(p => p.Id == savedId); initializing = false; return;
        }
        if (Profiles.SelectedItem is ControlProfile p) Edit(p, p.Id);
    }
    private void Edit(ControlProfile p, string? id)
    {
        capture = null; working = ControlProfiles.Clone(p, p.Name); working.Id = id ?? p.Id; savedId = id;
        ProfileEditor.IsEnabled = true; SaveButton.IsEnabled = UseButton.IsEnabled = true;
        initializing = true; ProfileName.Text = p.Name; Search.Text = ""; initializing = false;
        dirty = id == null; RefreshRows();
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
    private void RefreshRows()
    {
        if (working == null) return;
        var selected = (Bindings.SelectedItem as BindingRow)?.Action;
        var filter = Search.Text.Trim();
        var rows = ControlProfiles.Actions.Select(a => {
            var b = working.Bindings[a.Name];
            return new BindingRow(a.Name, a.Label, a.Group, ControlKeys.Label(b.Primary), ControlKeys.Label(b.Secondary), MouseLabel(b.Mouse));
        }).Where(r => filter.Length == 0 || (r.Label + " " + r.Group).Contains(filter, StringComparison.CurrentCultureIgnoreCase)).OrderBy(r => r.Group).ThenBy(r => r.Label).ToArray();
        var view = new ListCollectionView(rows);
        view.GroupDescriptions.Add(new PropertyGroupDescription(nameof(BindingRow.Group)));
        Bindings.ItemsSource = view; Bindings.SelectedItem = rows.FirstOrDefault(r => r.Action == selected);
        var conflicts = ControlProfiles.Conflicts(working);
        ConflictSummary.Text = conflicts.Count == 0 ? "F9–F11 are reserved for capture, replay and photo mode. Joystick bindings are retained; axis settings are not edited here." :
            $"{conflicts.Count} existing shared key(s). New assignments cannot add conflicts. " + string.Join(" • ", conflicts.Take(2));
    }
    private static string MouseLabel(int value) => value switch { 1 => "Left", 2 => "Right", 3 => "Middle", _ => "Unassigned" };
    private void NameChanged(object sender, TextChangedEventArgs e) { if (!initializing && working != null) { working.Name = ProfileName.Text; dirty = true; } }
    private void FilterChanged(object sender, TextChangedEventArgs e) { if (!initializing) RefreshRows(); }
    private void BindingChanged(object sender, SelectionChangedEventArgs e) { capture = null; BindingButtons.IsEnabled = Bindings.SelectedItem is BindingRow; }
    private void ResetOriginal(object sender, RoutedEventArgs e)
    {
        if (working == null) { Status.Text = "Select a saved layout or copy your current controls first."; return; }
        try
        {
            RequireClosedForImport();
            var original = store.ImportOriginal(RegistryCandidates());
            if (MessageBox.Show(this, "Reset this layout's bindings to your original game controls? Save afterward to keep the reset.", "Reset layout", MessageBoxButton.YesNo) != MessageBoxResult.Yes) return;
            working.Bindings = original.Bindings; dirty = true; RefreshRows(); Status.Text = "Original bindings copied into this layout. Save to keep the reset.";
        }
        catch (Exception ex) { Status.Text = ex.Message; }
    }
    private void BeginCapture(bool secondary)
    {
        if (Bindings.SelectedItem is not BindingRow row) return;
        capture = (row.Action, secondary); Status.Text = $"Press the {(secondary ? "secondary" : "primary")} key for {row.Label}. Escape cancels; use Clear to remove a binding.";
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
        dirty = true; capture = null; RefreshRows(); Status.Text = "Binding changed. Save the layout to keep it.";
    }
    private void CaptureKey(object sender, KeyEventArgs e)
    {
        if (capture == null || e.IsRepeat) return;
        e.Handled = true;
        if (e.Key == Key.Escape) { capture = null; Status.Text = "Key assignment canceled."; return; }
        var key = e.Key == Key.System ? e.SystemKey : e.Key;
        if (key is Key.LeftShift or Key.RightShift or Key.LeftCtrl or Key.RightCtrl or Key.LeftAlt or Key.RightAlt) return;
        try { ChangeKey(capture.Value.Secondary, ControlKeys.Capture(key, Keyboard.Modifiers,
            nativeVirtualKey == KeyInterop.VirtualKeyFromKey(key) ? nativeScan : null)); }
        catch (Exception ex) { Status.Text = ex.Message; }
    }
    private void SetMouse(object sender, RoutedEventArgs e)
    {
        capture = null;
        if (working == null || Bindings.SelectedItem is not BindingRow row) return;
        var menu = new ContextMenu();
        for (var n = 0; n <= 3; n++)
        {
            int value = n;
            var item = new MenuItem { Header = MouseLabel(value) };
            item.Click += (_, _) => {
                if (value != 0 && working.Bindings.Any(b => b.Key != row.Action && b.Value.Mouse == value))
                { Status.Text = "That mouse button is assigned to another action. Clear it there first."; return; }
                working.Bindings[row.Action].Mouse = value; dirty = true; RefreshRows(); Status.Text = "Mouse binding changed. Save the layout to keep it.";
            };
            menu.Items.Add(item);
        }
        menu.PlacementTarget = (Button)sender; menu.IsOpen = true;
    }
    private bool Persist(bool use)
    {
        if (working == null) return false;
        capture = null;
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
        SaveButton.IsEnabled = UseButton.IsEnabled = supported && !loadFailed && working != null;
        if (!supported) { capture = null; ActiveSummary.Text = "Controls not available yet"; Status.Text = "Controls for this game will be available when its runtime is supported. MW3 layouts remain separate."; }
        else if (!initializing && !loadFailed) { UpdateActive(); Status.Text = "Select or copy a MW3 layout. In-game edits are not saved into a launcher layout automatically."; }
    }
    private void OnClosing(object? sender, CancelEventArgs e) { if (!DiscardChanges()) e.Cancel = true; }
    private void CloseWindow(object sender, RoutedEventArgs e) => Close();
}
