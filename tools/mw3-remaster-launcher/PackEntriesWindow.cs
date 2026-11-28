using System.Windows;
using System.Windows.Controls;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Edits the same entry ticks as the game's MODS screen, without saving a separate selection.</summary>
public sealed class PackEntriesWindow : Window
{
    private readonly PackManager manager;
    private readonly PackManifest pack;
    private readonly StackPanel entries = new();
    private readonly TextBlock status = new() { TextWrapping = TextWrapping.Wrap };

    public PackEntriesWindow(PackManager manager, PackManifest pack)
    {
        this.manager = manager;
        this.pack = pack;
        Title = pack.Name + " - Gameplay entries";
        Width = 480; Height = 460; MinWidth = 360; MinHeight = 280;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var panel = new DockPanel { Margin = new Thickness(20) };
        var help = new TextBlock
        {
            Text = "Choose where this pack's gameplay is on. These are the same ticks shown on the game's MODS screen. Close the game before changing them.",
            TextWrapping = TextWrapping.Wrap,
            Margin = new Thickness(0, 0, 0, 14)
        };
        DockPanel.SetDock(help, Dock.Top); panel.Children.Add(help);
        var footer = new StackPanel { Margin = new Thickness(0, 12, 0, 0) };
        footer.Children.Add(status);
        var refresh = new Button { Content = "Refresh entries", Margin = new Thickness(0, 10, 0, 0) };
        refresh.Click += (_, _) => RefreshEntries();
        footer.Children.Add(refresh);
        DockPanel.SetDock(footer, Dock.Bottom); panel.Children.Add(footer);
        panel.Children.Add(new ScrollViewer { Content = entries, VerticalScrollBarVisibility = ScrollBarVisibility.Auto });
        Content = panel;
        Activated += (_, _) => RefreshEntries();
    }

    private void RefreshEntries()
    {
        entries.Children.Clear();
        try
        {
            foreach (var tick in manager.ReadEntryTicks(pack))
            {
                var checkbox = new CheckBox
                {
                    Content = tick.Entry.Name,
                    ToolTip = tick.Entry.Id,
                    IsChecked = tick.IsTicked,
                    Margin = new Thickness(0, 6, 0, 6)
                };
                checkbox.Click += (_, _) =>
                {
                    try
                    {
                        manager.EntryTicks.SetTick(pack, tick.Entry, checkbox.IsChecked == true);
                        RefreshEntries();
                        status.Text = "Saved. The game's MODS screen uses these ticks.\n" + status.Text;
                    }
                    catch (Exception error)
                    {
                        RefreshEntries();
                        status.Text = error.Message + "\n" + status.Text;
                    }
                };
                entries.Children.Add(checkbox);
            }
            status.Text = "Other players need the same gameplay pack to join a multiplayer game.";
            if (manager.EntryWarnings.Count > 0)
                status.Text += "\n\n" + string.Join("\n", manager.EntryWarnings);
        }
        catch (Exception error) { status.Text = "Cannot read gameplay ticks: " + error.Message; }
    }
}
