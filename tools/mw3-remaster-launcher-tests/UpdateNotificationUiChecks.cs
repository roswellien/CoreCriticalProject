using System.IO;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using MW3RemasterLauncher;
using MW3RemasterLauncher.Core;

static class UpdateNotificationUiChecks
{
    public static void Run(string root, string game)
    {
        Directory.CreateDirectory(root);
        var settings = new SettingsManager(root, root);
        settings.Current.GamePath = game;
        settings.Current.InitialSetupCompleted = true;
        if (settings.Current.AutomaticUpdateChecks) throw new Exception("Automatic checking must default off");
        settings.Save();
        Exception failure = null!;
        var thread = new Thread(() =>
        {
            var app = new App(false); app.InitializeComponent();
            var window = new MainWindow(root) { ShowActivated = false, ShowInTaskbar = false, Left = -10000 };
            var flags = BindingFlags.Instance | BindingFlags.NonPublic;
            // Keep this presentation fixture offline; real signed-catalog planning is
            // covered by OnlineUpdateChecks and downloader fixtures.
            var manual = typeof(MainWindow).GetField("_onlineUpdatesOpen", flags)!;
            manual.SetValue(window, true);
            window.Loaded += (_, _) => window.Dispatcher.BeginInvoke(new Action(async () =>
            {
                try
                {
                    var banner = (Border)window.FindName("UpdateNotification");
                    var details = (TextBlock)window.FindName("TxtUpdateNotificationDetails");
                    var automatic = (CheckBox)window.FindName("ChkAutomaticUpdateChecks");
                    if (banner.Visibility != Visibility.Collapsed) throw new Exception("Unverified startup notification is visible");
                    if (automatic.IsChecked == true) throw new Exception("Existing user was silently opted in");
                    var refresh = typeof(MainWindow).GetMethod("RefreshUpdateNotificationAsync", flags)!;
                    var check = typeof(MainWindow).GetField("_updateNotificationCheck", flags)!;
                    manual.SetValue(window, false);
                    await (Task)refresh.Invoke(window, null)!;
                    if (check.GetValue(window) != null) throw new Exception("Opted-out startup starts background checking");
                    manual.SetValue(window, true);
                    var setup = new GameSetupWindow(game, new LauncherSettings(), root);
                    if (setup.AutomaticUpdateChecks) throw new Exception("Setup automatically opts users in");
                    ((CheckBox)setup.FindName("SetupAutomaticUpdateChecks")).IsChecked = true;
                    if (!setup.AutomaticUpdateChecks) throw new Exception("Setup loses the selected opt-in");
                    setup.Close();
                    automatic.IsChecked = true;
                    if (!new SettingsManager(root, root).Current.AutomaticUpdateChecks) throw new Exception("Opt-in was not persisted");
                    var show = typeof(MainWindow).GetMethod("ShowUpdateNotification", flags)!;
                    var artifact = new ReleaseArtifact("https://updates.example.test/1.0.99.zip", "1.0.99.zip", 1, new string('a', 64));
                    OnlineRelease Release(string product) => new(product, product == GameCatalog.LauncherId ? null : product,
                        "1.0.99", "1.0.99-preview", "1.0.99", 100, "promoted", "windows", "x64", "1.0.27",
                        "fixture", artifact, artifact, "fixture", null, Array.Empty<ReleaseDependency>());
                    var releases = new[] { new PlannedOnlineUpdate(Release(GameCatalog.LauncherId), null),
                        new PlannedOnlineUpdate(Release(GameCatalog.Mw3), null) };
                    show.Invoke(window, new object[] { releases, false });
                    if (banner.Visibility != Visibility.Visible || !details.Text.Contains("Core Critical 1.0.99-preview") ||
                        !details.Text.Contains("MechWarrior 3 runtime 1.0.99-preview")) throw new Exception("Product/version notification is missing");
                    window.Width = 960; window.Height = 640; window.UpdateLayout();
                    if (details.ActualWidth <= 0 || banner.ActualHeight > 120) throw new Exception("Notification does not fit the minimum window");
                    var image = new RenderTargetBitmap(960, 640, 96, 96, PixelFormats.Pbgra32); image.Render(window);
                    var png = new PngBitmapEncoder(); png.Frames.Add(BitmapFrame.Create(image));
                    using (var output = File.Create(Path.Combine(root, "update-notification.png"))) png.Save(output);
                    show.Invoke(window, new object[] { Array.Empty<PlannedOnlineUpdate>(), true });
                    if (banner.Visibility != Visibility.Visible || !details.Text.Contains("unfinished update")) throw new Exception("Resume notification is missing");
                    show.Invoke(window, new object[] { Array.Empty<PlannedOnlineUpdate>(), false });
                    if (banner.Visibility != Visibility.Collapsed) throw new Exception("Completed update left a stale banner");
                    await (Task)refresh.Invoke(window, null)!;
                    if (check.GetValue(window) != null) throw new Exception("Manual update window permits concurrent background check");
                    manual.SetValue(window, false);
                    typeof(MainWindow).GetField("_nativeSessionActive", flags)!.SetValue(window, true);
                    await (Task)refresh.Invoke(window, null)!;
                    if (check.GetValue(window) != null) throw new Exception("Background check ran during gameplay");
                    show.Invoke(window, new object[] { releases, false });
                    automatic.IsChecked = false;
                    if (new SettingsManager(root, root).Current.AutomaticUpdateChecks || banner.Visibility != Visibility.Collapsed)
                        throw new Exception("Opt-out was not persisted or left a banner visible");
                    var polling = typeof(MainWindow).GetField("_updateNotificationTimer", flags)!.GetValue(window) as DispatcherTimer;
                    if (polling?.IsEnabled == true) throw new Exception("Opt-out retained automatic polling");
                    window.Close();
                    var timer = typeof(MainWindow).GetField("_updateNotificationTimer", flags)!.GetValue(window) as DispatcherTimer;
                    if (timer?.IsEnabled == true) throw new Exception("Closed launcher retained update polling");
                }
                catch (Exception error) { failure = error; window.Close(); }
                finally { app.Shutdown(); }
            }));
            app.Run(window);
        });
        thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join();
        if (failure != null) throw failure;
        Console.WriteLine("Update notification UI: default-off setup/settings, persisted opt-in/out, versions/layout, pending/complete states, gameplay/manual gates and cleanup passed.");
    }
}
