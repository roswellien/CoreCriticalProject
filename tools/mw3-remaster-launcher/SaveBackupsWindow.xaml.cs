using System.Diagnostics;
using System.IO;
using System.Windows;
using Microsoft.Win32;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public partial class SaveBackupsWindow : Window
{
    private readonly SaveBackups _saves;
    public SaveBackupsWindow(string game, string? registry)
    {
        InitializeComponent();
        _saves = new SaveBackups(game, LauncherPaths.DataRoot, registry);
        Refresh();
    }
    private void Refresh() => Backups.ItemsSource = _saves.List().Select(p => new FileInfo(p)).ToArray();
    private void CreateBackup(object sender, RoutedEventArgs e)
    {
        try { var path = _saves.Create("Manual playtest backup"); Refresh(); Status.Text = "Backup saved: " + Path.GetFileName(path); }
        catch (Exception error) { Status.Text = error.Message; }
    }
    private void Restore(string path)
    {
        if (MessageBox.Show(this, "Restore this backup? Matching pilot, campaign and configuration files will be replaced. A safety backup of current saves is created first.",
            "Restore saves", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes) return;
        try { _saves.Restore(path); Refresh(); Status.Text = "Saves restored. Start the game and choose Load Game. Your previous saves have a safety backup."; }
        catch (Exception error) { Status.Text = error.Message; }
    }
    private void RestoreSelected(object sender, RoutedEventArgs e)
    {
        if (Backups.SelectedItem is FileInfo file) Restore(file.FullName);
        else Status.Text = "Select a backup first.";
    }
    private void LoadBackup(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Title = "Load save backup", Filter = "MW3 save backups (*.mw3save.zip)|*.mw3save.zip" };
        if (dialog.ShowDialog(this) == true) Restore(dialog.FileName);
    }
    private void OpenFolder(object sender, RoutedEventArgs e)
    {
        try { Process.Start(new ProcessStartInfo(_saves.DirectoryPath) { UseShellExecute = true }); }
        catch (Exception error) { Status.Text = error.Message; }
    }
}
