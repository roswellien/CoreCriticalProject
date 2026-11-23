using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>
/// Modal editor for the key/mouse chord combos of a single action in a <see cref="ControlProfile"/>.
/// The profile is only modified when OK is clicked; Cancel leaves it untouched.
/// </summary>
public sealed class ComboEditorWindow : Window
{
    private const int MaxCombosPerAction = 8;
    private const int MaxCombosPerProfile = 64;

    private readonly ControlProfile profile;
    private readonly string actionName;
    private readonly List<ControlCombo> staged;
    private readonly List<ControlComboInput> chord = [];
    private bool armingInput;
    private int nativeVirtualKey, nativeScan;

    public ListBox CombosList { get; }
    public Button AddComboButton { get; }
    public Button RemoveSelectedButton { get; }
    public Button TogglePassThroughButton { get; }
    public Button ClearIngredientsButton { get; }
    public Button CaptureInputButton { get; }
    public Button OkButton { get; }
    public Button CancelButton { get; }
    public CheckBox SuppressCheckBox { get; }
    public TextBlock ChordText { get; }
    public TextBlock StatusText { get; }

    public ComboEditorWindow(ControlProfile profile, string actionName)
    {
        this.profile = profile;
        this.actionName = actionName;
        var actionLabel = ControlProfiles.Actions.FirstOrDefault(a => a.Name == actionName)?.Label ?? actionName;
        Title = "Combos — " + actionLabel;
        Width = 620; Height = 560; MinWidth = 520; MinHeight = 460;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        Background = TryFindResource("BrushGround") as System.Windows.Media.Brush
            ?? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x14, 0x17, 0x17));
        Foreground = TryFindResource("BrushInk") as System.Windows.Media.Brush
            ?? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0xEE, 0xE6, 0xDC));
        if (TryFindResource("FontBody") is System.Windows.Media.FontFamily bodyFont) FontFamily = bodyFont;
        FontSize = 14;

        staged = (profile.Bindings.TryGetValue(actionName, out var binding) && binding.Combos != null
            ? binding.Combos
            : []).Select(c => new ControlCombo { Inputs = new List<ControlComboInput>(c.Inputs), Suppress = c.Suppress }).ToList();

        ControlsWindow.HookPhysicalKeys(this, (vk, scan) => { nativeVirtualKey = vk; nativeScan = scan; });

        var panel = new StackPanel { Margin = new Thickness(20) };
        Content = panel;
        panel.Children.Add(new TextBlock
        {
            Text = "Combos trigger " + actionLabel + " when every key/button in the chord is held together (for wheel combos, hold the other inputs and scroll). " +
                   "Build a chord of 2–3 inputs, then Add combo. OK applies the list to the layout; Cancel discards it.",
            TextWrapping = TextWrapping.Wrap
        });

        CombosList = new ListBox
        {
            Height = 150,
            Margin = new Thickness(0, 12, 0, 8),
            DisplayMemberPath = nameof(ComboEntry.Summary),
            Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x18, 0x1D, 0x1D)),
            Foreground = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0xEE, 0xE6, 0xDC)),
            BorderBrush = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(0x37, 0x3B, 0x3A))
        };
        System.Windows.Automation.AutomationProperties.SetName(CombosList, "Combos");

        // Suppress-by-default applies only to NEW combos staged from the current chord; it never
        // rewrites an already-added combo. Use "Toggle pass-through" on the selected combo instead.
        SuppressCheckBox = new CheckBox
        {
            Content = "Suppress constituent single bindings while new combo is held",
            IsChecked = true,
            Margin = new Thickness(0, 4, 0, 12),
            Foreground = Foreground
        };
        System.Windows.Automation.AutomationProperties.SetName(SuppressCheckBox, "Suppress constituent single bindings while new combo is held");

        StatusText = new TextBlock { TextWrapping = TextWrapping.Wrap, Foreground = System.Windows.Media.Brushes.OrangeRed, Margin = new Thickness(0, 0, 0, 8), MinHeight = 20 };
        System.Windows.Automation.AutomationProperties.SetName(StatusText, "Combo status");

        panel.Children.Add(CombosList);

        void StyleSecondary(Button button)
        {
            if (TryFindResource("SecondaryButton") is Style style) button.Style = style;
        }
        var listButtons = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 12) };
        AddComboButton = new Button { Content = "Add combo" };
        System.Windows.Automation.AutomationProperties.SetName(AddComboButton, "Add combo");
        AddComboButton.Click += AddCombo;
        StyleSecondary(AddComboButton);
        RemoveSelectedButton = new Button { Content = "Remove selected", Margin = new Thickness(8, 0, 0, 0) };
        System.Windows.Automation.AutomationProperties.SetName(RemoveSelectedButton, "Remove selected");
        RemoveSelectedButton.Click += RemoveSelected;
        StyleSecondary(RemoveSelectedButton);
        TogglePassThroughButton = new Button { Content = "Toggle pass-through", Margin = new Thickness(8, 0, 0, 0) };
        System.Windows.Automation.AutomationProperties.SetName(TogglePassThroughButton, "Toggle pass-through");
        TogglePassThroughButton.Click += TogglePassThrough;
        StyleSecondary(TogglePassThroughButton);
        listButtons.Children.Add(AddComboButton);
        listButtons.Children.Add(RemoveSelectedButton);
        listButtons.Children.Add(TogglePassThroughButton);
        panel.Children.Add(listButtons);

        ChordText = new TextBlock { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 8) };
        panel.Children.Add(ChordText);

        var chordButtons = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 8) };
        CaptureInputButton = new Button { Content = "Capture input…" };
        System.Windows.Automation.AutomationProperties.SetName(CaptureInputButton, "Capture input");
        StyleSecondary(CaptureInputButton);
        CaptureInputButton.Click += (_, _) =>
        {
            // Click fires on MouseUp, after this window's PreviewMouseDown, so the arming click is never captured.
            armingInput = true;
            CaptureInputButton.Content = "Capturing… (Esc cancels)";
            StatusText.Text = "Press a key, click a mouse button or scroll the wheel to add it to the chord.";
        };
        ClearIngredientsButton = new Button { Content = "Clear ingredients", Margin = new Thickness(8, 0, 0, 0) };
        System.Windows.Automation.AutomationProperties.SetName(ClearIngredientsButton, "Clear ingredients");
        StyleSecondary(ClearIngredientsButton);
        ClearIngredientsButton.Click += (_, _) => { chord.Clear(); armingInput = false; SuppressCheckBox.IsChecked = true; RefreshChord(); StatusText.Text = ""; };
        chordButtons.Children.Add(CaptureInputButton);
        chordButtons.Children.Add(ClearIngredientsButton);
        panel.Children.Add(chordButtons);

        panel.Children.Add(SuppressCheckBox);
        panel.Children.Add(StatusText);

        var footer = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        OkButton = new Button { Content = "OK", Margin = new Thickness(0, 0, 8, 0), Padding = new Thickness(18, 6, 18, 6) };
        System.Windows.Automation.AutomationProperties.SetName(OkButton, "OK");
        StyleSecondary(OkButton);
        OkButton.Click += OkClick;
        CancelButton = new Button { Content = "Cancel", Padding = new Thickness(18, 6, 18, 6) };
        System.Windows.Automation.AutomationProperties.SetName(CancelButton, "Cancel");
        StyleSecondary(CancelButton);
        CancelButton.Click += (_, _) => { DialogResult = false; };
        footer.Children.Add(OkButton);
        footer.Children.Add(CancelButton);
        panel.Children.Add(footer);

        PreviewKeyDown += OnPreviewKeyDown;
        PreviewMouseDown += OnPreviewMouseDown;
        PreviewMouseWheel += OnPreviewMouseWheel;
        Deactivated += (_, _) =>
        {
            if (armingInput)
            {
                armingInput = false;
                RefreshChord();
                StatusText.Text = "Input capture canceled; the chord was kept.";
            }
        };

        RefreshCombos();
        RefreshChord();
    }

    private sealed record ComboEntry(ControlCombo Combo, string Summary);

    internal static string FormatCombo(ControlCombo combo)
    {
        var parts = combo.Inputs.Select(i => i.Kind == ControlComboInputKind.Key
            ? ControlKeys.Label(i.Code)
            : ControlKeys.MouseLabel(i.Code));
        return string.Join(" + ", parts) + (combo.Suppress ? "" : " (pass-through)");
    }
    private static string Summarize(ControlCombo combo) => FormatCombo(combo);

    private void RefreshCombos()
    {
        var selected = (CombosList.SelectedItem as ComboEntry)?.Combo;
        CombosList.ItemsSource = staged.Select(c => new ComboEntry(c, Summarize(c))).ToArray();
        CombosList.SelectedItem = CombosList.Items.Cast<ComboEntry>().FirstOrDefault(e => e.Combo == selected);
    }

    private void RefreshChord()
    {
        ChordText.Text = chord.Count == 0
            ? "Chord: (empty — capture inputs to build one)"
            : "Chord: " + string.Join(" + ", chord.Select(i => i.Kind == ControlComboInputKind.Key
                ? ControlKeys.Label(i.Code)
                : ControlKeys.MouseLabel(i.Code)));
        // 1-input chords are not allowed, so adding is only possible with 2–3 ingredients.
        AddComboButton.IsEnabled = chord.Count is >= 2 and <= 3;
        if (armingInput) CaptureInputButton.Content = "Capturing… (Esc cancels)";
        else CaptureInputButton.Content = "Capture input…";
    }

    private void AddIngredient(ControlComboInput input)
    {
        armingInput = false;
        if (chord.Count >= 3)
        {
            StatusText.Text = "A combo can hold at most 3 inputs. Add the combo or clear the ingredients.";
            RefreshChord();
            return;
        }
        if (chord.Any(i => i.Kind == input.Kind && i.Code == input.Code))
        {
            StatusText.Text = "That input is already in the chord.";
            RefreshChord();
            return;
        }
        if (input.Kind == ControlComboInputKind.Mouse && input.Code is 6 or 7)
        {
            var opposite = input.Code == 6 ? 7 : 6;
            if (chord.Any(i => i.Kind == ControlComboInputKind.Mouse && i.Code == opposite))
            {
                StatusText.Text = "Wheel Up and Wheel Down cannot be in the same combo.";
                RefreshChord();
                return;
            }
        }
        chord.Add(input);
        StatusText.Text = "";
        RefreshChord();
    }

    private void OnPreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (!armingInput || e.IsRepeat) return;
        var key = e.Key == Key.System ? e.SystemKey : e.Key;
        e.Handled = true;
        if (key == Key.Escape)
        {
            armingInput = false;
            StatusText.Text = "Input capture canceled; the chord was kept.";
            RefreshChord();
            return;
        }
        try
        {
            var code = ControlKeys.CapturePhysical(key,
                nativeVirtualKey == KeyInterop.VirtualKeyFromKey(key) ? nativeScan : null);
            AddIngredient(new ControlComboInput(ControlComboInputKind.Key, code));
        }
        catch (Exception ex)
        {
            armingInput = false;
            StatusText.Text = ex.Message;
            RefreshChord();
        }
    }

    private void OnPreviewMouseDown(object sender, MouseButtonEventArgs e)
    {
        if (!armingInput) return;
        if (e.ChangedButton == MouseButton.Left &&
            ControlsWindow.TryCancelInteractiveLeftClick(e.OriginalSource as DependencyObject, CaptureInputButton, null,
                () => { armingInput = false; RefreshChord(); StatusText.Text = "Input capture canceled; the chord was kept."; },
                out var cancelHandled))
        {
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
        if (value == 0) return;
        e.Handled = true;
        AddIngredient(new ControlComboInput(ControlComboInputKind.Mouse, value));
    }

    private void OnPreviewMouseWheel(object sender, MouseWheelEventArgs e)
    {
        if (!armingInput || e.Delta == 0) return;
        e.Handled = true;
        AddIngredient(new ControlComboInput(ControlComboInputKind.Mouse, e.Delta > 0 ? 6 : 7));
    }

    private string? ConflictFor(ControlCombo combo, ControlCombo? exclude)
    {
        var canonical = ControlProfiles.CanonicalCombo(combo);
        foreach (var existing in staged)
        {
            if (ReferenceEquals(existing, exclude)) continue;
            if (ControlProfiles.CanonicalCombo(existing) == canonical)
            {
                return "This combo already exists on this action.";
            }
        }
        foreach (var kv in profile.Bindings)
        {
            if (kv.Key == actionName) continue;
            foreach (var existing in kv.Value.Combos ?? [])
            {
                if (ControlProfiles.CanonicalCombo(existing) == canonical)
                {
                    var label = ControlProfiles.Actions.FirstOrDefault(a => a.Name == kv.Key)?.Label ?? kv.Key;
                    return "This combo conflicts with a combo on " + label + ".";
                }
            }
        }
        return null;
    }

    private int ProfileComboCount(int extraForThisAction) =>
        profile.Bindings.Sum(kv => kv.Key == actionName
            ? staged.Count + extraForThisAction
            : kv.Value.Combos?.Count ?? 0);

    private void AddCombo(object sender, RoutedEventArgs e)
    {
        if (chord.Count < 2 || chord.Count > 3)
        {
            StatusText.Text = "A combo needs 2–3 distinct inputs. 1-input chords are not allowed.";
            return;
        }
        if (staged.Count >= MaxCombosPerAction)
        {
            StatusText.Text = "This action already has " + MaxCombosPerAction + " combos, the maximum.";
            return;
        }
        if (ProfileComboCount(1) > MaxCombosPerProfile)
        {
            StatusText.Text = "This layout already has " + MaxCombosPerProfile + " combos, the maximum.";
            return;
        }
        var combo = new ControlCombo
        {
            Inputs = new List<ControlComboInput>(chord),
            Suppress = SuppressCheckBox.IsChecked == true
        };
        try { ControlProfiles.ValidateCombo(combo); }
        catch (Exception ex) { StatusText.Text = ex.Message; return; }
        var conflict = ConflictFor(combo, null);
        if (conflict != null) { StatusText.Text = conflict; return; }
        staged.Add(combo);
        chord.Clear();
        SuppressCheckBox.IsChecked = true; // every newly staged combo defaults to suppress
        RefreshCombos();
        RefreshChord();
        StatusText.Text = "Combo added. Click OK to apply it to the layout.";
    }

    private void RemoveSelected(object sender, RoutedEventArgs e)
    {
        if (CombosList.SelectedItem is not ComboEntry entry) { StatusText.Text = "Select a combo to remove."; return; }
        staged.Remove(entry.Combo);
        RefreshCombos();
        StatusText.Text = "Combo removed. Click OK to apply the change.";
    }

    private void TogglePassThrough(object sender, RoutedEventArgs e)
    {
        if (CombosList.SelectedItem is not ComboEntry entry) { StatusText.Text = "Select a combo to toggle pass-through."; return; }
        entry.Combo.Suppress = !entry.Combo.Suppress;
        RefreshCombos();
        StatusText.Text = entry.Combo.Suppress
            ? "Pass-through off: this combo suppresses its constituent single-input bindings while held."
            : "Pass-through on: this combo does not suppress its constituent single-input bindings (other active combos may still suppress them).";
    }

    private void OkClick(object sender, RoutedEventArgs e)
    {
        if (staged.Count > MaxCombosPerAction)
        {
            StatusText.Text = "This action can have at most " + MaxCombosPerAction + " combos.";
            return;
        }
        if (ProfileComboCount(0) > MaxCombosPerProfile)
        {
            StatusText.Text = "This layout can have at most " + MaxCombosPerProfile + " combos.";
            return;
        }
        foreach (var combo in staged)
        {
            try { ControlProfiles.ValidateCombo(combo); }
            catch (Exception ex) { StatusText.Text = ex.Message; return; }
            var conflict = ConflictFor(combo, combo);
            if (conflict != null) { StatusText.Text = conflict; return; }
        }
        if (!profile.Bindings.TryGetValue(actionName, out var binding)) return;
        binding.Combos = staged.Count > 0 ? new List<ControlCombo>(staged) : null;
        DialogResult = true;
    }
}
