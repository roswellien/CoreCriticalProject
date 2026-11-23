using System.Text.Json.Nodes;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Exact package pins for the MW3-RE runtime. Resolution stays in native code.</summary>
public sealed class ModProfilesWindow : Window
{
    private readonly LauncherSettings settings;
    private readonly ModProfiles profiles;
    private readonly TextBox tool = new(), runtime = new(), store = new(), name = new();
    private readonly ComboBox choices = new();
    private readonly ListBox packages = new() { SelectionMode = SelectionMode.Multiple, DisplayMemberPath = "Label" };
    private readonly ComboBox hud = new() { DisplayMemberPath = "Label" };
    private readonly ListBox appearances = new() { SelectionMode = SelectionMode.Multiple, DisplayMemberPath = "Label", Height = 100 };
    private bool visualChoicesLoaded;
    private readonly TextBox report = new() { IsReadOnly = true, TextWrapping = TextWrapping.Wrap,
        VerticalScrollBarVisibility = ScrollBarVisibility.Auto, MinHeight = 90 };
    private readonly StackPanel controls = new();
    private JsonObject profile = new() { ["schema_version"] = 1, ["id"] = "default", ["packages"] = new JsonArray() };
    private sealed record PackagePin(string Label, JsonObject Pin);
    private List<PackagePin> installedPins = new();
    private sealed record VisualChoice(string Id, string Label);

    public ModProfilesWindow(LauncherSettings settings, string dataRoot)
    {
        this.settings = settings;
        profiles = new ModProfiles(dataRoot);
        Title = "MW3-RE mod profiles"; Width = 860; Height = 720;
        MinWidth = 620; MinHeight = 500; WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var panel = new DockPanel { Margin = new Thickness(16) };
        var heading = new TextBlock { Text = "Create a named collection of exact package versions. Dependencies and conflicts are checked before saving or playing. The selected native runtime keeps its own graphics and controls settings.", TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 10) };
        DockPanel.SetDock(heading, Dock.Top); panel.Children.Add(heading);
        DockPanel.SetDock(controls, Dock.Top); panel.Children.Add(controls);
        AddPath("Content tool", tool, settings.ModularContentTool, false);
        AddPath("MW3-RE runtime", runtime, settings.ModularRuntimeExecutable, false);
        AddPath("Package library", store, string.IsNullOrEmpty(settings.ModularContentStore)
            ? Path.Combine(dataRoot, "content-store") : settings.ModularContentStore, true);
        choices.ItemsSource = profiles.List();
        choices.SelectionChanged += (_, _) => LoadProfile();
        controls.Children.Add(choices);
        controls.Children.Add(new TextBlock { Text = "Profile name (lowercase ID)", Margin = new Thickness(0, 8, 0, 4) });
        name.Text = "default"; controls.Children.Add(name);
        var buttons = new WrapPanel { Margin = new Thickness(0, 10, 0, 10) };
        AddButton(buttons, "Refresh packages", RefreshPackages);
        AddButton(buttons, "Install package…", Install);
        AddButton(buttons, "Save profile", Save);
        AddButton(buttons, "Choose HUD & appearances", InspectVisualChoices);
        AddButton(buttons, "Use for Play", ActivateProfile);
        AddButton(buttons, "Use existing launcher mode", Clear);
        controls.Children.Add(buttons);
        DockPanel.SetDock(report, Dock.Bottom); panel.Children.Add(report);
        var visuals = new StackPanel();
        visuals.Children.Add(new TextBlock { Text = "HUD layout", Margin = new Thickness(0, 6, 0, 3) });
        visuals.Children.Add(hud);
        visuals.Children.Add(new TextBlock { Text = "Chassis appearances (select one per chassis and LOD)", Margin = new Thickness(0, 6, 0, 3) });
        visuals.Children.Add(appearances);
        DockPanel.SetDock(visuals, Dock.Bottom); panel.Children.Add(visuals);
        panel.Children.Add(packages); Content = panel;
        if (profiles.List().Contains(settings.ModularContentProfile)) choices.SelectedItem = settings.ModularContentProfile;
        if (!string.IsNullOrEmpty(tool.Text)) Loaded += async (_, _) => await Run(RefreshPackages);
    }

    private void AddPath(string label, TextBox input, string value, bool folder)
    {
        controls.Children.Add(new TextBlock { Text = label, Margin = new Thickness(0, 6, 0, 3) });
        var row = new DockPanel();
        var browse = new Button { Content = "Browse…", Margin = new Thickness(6, 0, 0, 0), Padding = new Thickness(10, 3, 10, 3) };
        browse.Click += (_, _) =>
        {
            if (folder)
            {
                var picker = new OpenFolderDialog();
                if (picker.ShowDialog(this) == true) input.Text = picker.FolderName;
            }
            else
            {
                var picker = new OpenFileDialog { Filter = "Executable|*.exe|All files|*.*" };
                if (picker.ShowDialog(this) == true) input.Text = picker.FileName;
            }
        };
        DockPanel.SetDock(browse, Dock.Right); row.Children.Add(browse);
        input.Text = value; row.Children.Add(input); controls.Children.Add(row);
    }
    private void AddButton(Panel row, string text, Func<Task> action)
    {
        var button = new Button { Content = text, Padding = new Thickness(10, 6, 10, 6), Margin = new Thickness(0, 0, 6, 4) };
        button.Click += async (_, _) => await Run(action); row.Children.Add(button);
    }
    private async Task Run(Func<Task> action)
    {
        controls.IsEnabled = packages.IsEnabled = hud.IsEnabled = appearances.IsEnabled = false;
        report.Text = "Checking content…";
        try { await action(); }
        catch (Exception error) { report.Text = error.Message; }
        finally { controls.IsEnabled = packages.IsEnabled = hud.IsEnabled = appearances.IsEnabled = true; }
    }
    private ContentToolClient Tool() => new(tool.Text);
    private void LoadProfile()
    {
        if (choices.SelectedItem is not string path) return;
        try
        {
            profile = JsonNode.Parse(File.ReadAllText(path))!.AsObject();
            name.Text = profile["id"]!.GetValue<string>();
            visualChoicesLoaded = false;
            hud.ItemsSource = null; appearances.ItemsSource = null;
            SelectPins();
        }
        catch (Exception error) { report.Text = error.Message; }
    }
    private void SelectPins()
    {
        var rows = new List<PackagePin>(installedPins);
        var pins = profile["packages"] as JsonArray ?? new JsonArray();
        foreach (var pin in ModProfiles.UnavailablePins(pins, installedPins.Select(row => row.Pin)))
            rows.Add(new PackagePin($"{pin["id"]}  {pin["version"]}  (saved pin; unavailable)", pin));
        packages.ItemsSource = rows;
        foreach (var candidate in rows)
            if (pins.Any(pin => ModProfiles.SamePin(pin, candidate.Pin))) packages.SelectedItems.Add(candidate);
    }
    private async Task RefreshPackages()
    {
        var result = await Tool().RunAsync(new[] { "list", "--store", Path.GetFullPath(store.Text) });
        var rows = result["packages"]?.AsArray() ?? throw new InvalidDataException("Content tool omitted its package inventory.");
        installedPins = rows.Select(row => new PackagePin($"{row!["id"]}  {row["version"]}  {row["sha256"]?.ToString()[..12]}",
            new JsonObject { ["id"] = row["id"]!.DeepClone(), ["version"] = row["version"]!.DeepClone(),
                ["sha256"] = row["sha256"]?.DeepClone() ?? row["digest"]?.DeepClone() })).ToList();
        SelectPins(); report.Text = "Select package versions, then save and use the profile.";
    }
    private async Task Install()
    {
        var picker = new OpenFileDialog { Filter = "MW3 content package|*.mw3pack|All files|*.*" };
        if (picker.ShowDialog(this) != true) return;
        await Tool().RunAsync(new[] { "install", picker.FileName, "--store", Path.GetFullPath(store.Text) });
        await RefreshPackages();
    }
    private JsonObject Snapshot()
    {
        profile["id"] = name.Text;
        profile["packages"] = new JsonArray(packages.SelectedItems.Cast<PackagePin>()
            .Select(row => (JsonNode)row.Pin.DeepClone()).ToArray());
        if (visualChoicesLoaded)
        {
            profile["selections"] ??= new JsonObject();
            var selected = profile["selections"]!.AsObject();
            if (hud.SelectedItem is VisualChoice choice && choice.Id.Length > 0) selected["hud"] = choice.Id;
            else selected.Remove("hud");
            selected["appearances"] = new JsonArray(appearances.SelectedItems.Cast<VisualChoice>()
                .Select(row => (JsonNode?)JsonValue.Create(row.Id)).ToArray());
        }
        return profile;
    }
    private async Task InspectVisualChoices()
    {
        var candidate = (JsonObject)Snapshot().DeepClone();
        candidate["selections"] ??= new JsonObject();
        candidate["selections"]!.AsObject().Remove("hud");
        candidate["selections"]!.AsObject().Remove("appearances");
        var result = await profiles.InspectAsync(candidate, Tool(), store.Text);
        var definitions = result["content"]?["definitions"]?.AsArray()
            ?? throw new InvalidDataException("Native inspector omitted its definitions.");
        var layouts = new List<VisualChoice> { new("", "Stock native HUD") };
        var models = new List<VisualChoice>();
        foreach (var definition in definitions)
        {
            var id = definition!["id"]!.GetValue<string>();
            if (definition["kind"]?.ToString() == "hud") layouts.Add(new(id, id));
            if (definition["kind"]?.ToString() == "appearance") models.Add(new(id, id));
        }
        hud.ItemsSource = layouts;
        hud.SelectedItem = layouts.FirstOrDefault(item => item.Id == profile["selections"]?["hud"]?.ToString()) ?? layouts[0];
        appearances.ItemsSource = models;
        if (profile["selections"]?["appearances"] is JsonArray enabled)
            foreach (var item in models.Where(item => enabled.Any(value => value?.ToString() == item.Id))) appearances.SelectedItems.Add(item);
        visualChoicesLoaded = true;
        report.Text = "Presentation choices come from the resolved native catalogue. Selection changes are checked when you save.";
    }
    private async Task<string> Persist()
    {
        Snapshot();
        return await profiles.SaveAsync(profile.ToJsonString(), Tool(), store.Text);
    }
    private async Task Save()
    {
        var path = await Persist(); choices.ItemsSource = profiles.List(); choices.SelectedItem = path;
        report.Text = "Saved exact package versions. Existing profile content and previous version are retained.";
    }
    private async Task ActivateProfile()
    {
        var path = await Persist();
        if (!File.Exists(runtime.Text)) throw new FileNotFoundException("Choose the MW3-RE runtime executable.");
        settings.ModularContentProfile = path; settings.ModularContentTool = Path.GetFullPath(tool.Text);
        settings.ModularRuntimeExecutable = Path.GetFullPath(runtime.Text); settings.ModularContentStore = Path.GetFullPath(store.Text);
        settings.EngineMode = "remaster";
        DialogResult = true;
    }
    private Task Clear() { settings.ModularContentProfile = ""; DialogResult = true; return Task.CompletedTask; }
}
