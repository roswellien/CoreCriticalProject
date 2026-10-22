using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Optional bonus movies; no commands, shell associations or pack code.</summary>
public sealed class CinematicWindow : Window
{
    public CinematicWindow(IReadOnlyList<CinematicPack.Clip> clips)
    {
        Title = "Installed cinematics"; Width = 960; Height = 680;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        var panel = new DockPanel { Margin = new Thickness(12) };
        var choices = new ComboBox { ItemsSource = clips, DisplayMemberPath = "Title", Margin = new Thickness(0, 0, 0, 10) };
        DockPanel.SetDock(choices, Dock.Top); panel.Children.Add(choices);
        var controls = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 10, 0, 0) };
        DockPanel.SetDock(controls, Dock.Bottom); panel.Children.Add(controls);
        var media = new MediaElement { LoadedBehavior = MediaState.Manual, UnloadedBehavior = MediaState.Close,
            Stretch = Stretch.Uniform, ScrubbingEnabled = true };
        foreach (var label in new[] { "Play", "Pause", "Restart", "Close" })
        {
            var button = new Button { Content = label, Padding = new Thickness(16, 6, 16, 6), Margin = new Thickness(0, 0, 10, 0) };
            button.Click += (_, _) => { if (label == "Close") Close(); else if (label == "Pause") media.Pause(); else { if (label == "Restart") media.Position = TimeSpan.Zero; media.Play(); } };
            controls.Children.Add(button);
        }
        media.MediaFailed += (_, e) => { media.Close(); MessageBox.Show(this, "Windows could not play this movie. Ask the pack creator for an H.264/AAC MP4 compatible with Windows.\n\n" + e.ErrorException.Message, "Movie playback failed"); };
        choices.SelectionChanged += (_, _) => { media.Close(); media.Source = new Uri(((CinematicPack.Clip)choices.SelectedItem).Source); media.Play(); };
        Closed += (_, _) => media.Close();
        panel.Children.Add(media); Content = panel; choices.SelectedIndex = 0;
    }
}
