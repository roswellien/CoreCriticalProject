using System.IO;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using MW3RemasterLauncher;
using MW3RemasterLauncher.Core;

static class LoadingIndicatorUiChecks
{
    public static void Run(string root, string game)
    {
        Directory.CreateDirectory(root);
        var settings = new SettingsManager(root, root);
        settings.Current.GamePath = game;
        settings.Current.InitialSetupCompleted = true;
        settings.Save();
        Exception failure = null!;
        var thread = new Thread(() =>
        {
            var app = new App(false); app.InitializeComponent();
            var window = new MainWindow(root) { ShowActivated = false, ShowInTaskbar = false, Left = -10000, Top = 100 };
            window.Loaded += (_, _) => window.Dispatcher.BeginInvoke(new Action(() =>
            {
                try
                {
                    var mark = (CoreCriticalLoadingMark)window.FindName("LaunchActivity");
                    var sections = new[] { "LightTopRight", "LightBottomRight", "LightBottomLeft", "LightTopLeft" }
                        .Select(n => (System.Windows.Shapes.Path)mark.FindName(n)).ToArray();
                    var expected = "Core Critical " + typeof(GameRunner).Assembly.GetName().Version!.ToString(3);
                    if (((TextBlock)window.FindName("TxtHeaderBuild")).Text != expected) throw new Exception("Launcher header version is stale");
                    if (mark.IsActive || sections.Any(p => p.HasAnimatedProperties)) throw new Exception("Idle mark is animated");
                    var setBusy = typeof(MainWindow).GetMethod("SetLaunchPreparing", BindingFlags.Instance | BindingFlags.NonPublic)!;
                    setBusy.Invoke(window, new object[] { true });
                    ((TextBlock)window.FindName("TxtStatusReady")).Text = "GAME STATUS: PREPARING ASSETS";
                    var cycle = (Storyboard)typeof(CoreCriticalLoadingMark).GetField("_cycle", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(mark)!;
                    if (SystemParameters.ClientAreaAnimation)
                    {
                        cycle.Pause(mark);
                        for (var i = 0; i < 4; ++i)
                        {
                            cycle.SeekAlignedToLastTick(mark, TimeSpan.FromSeconds(i * .7 + .28), TimeSeekOrigin.BeginTime);
                            window.UpdateLayout();
                            if (sections[i].Opacity < .95 || sections.Where((_, j) => j != i).Any(p => p.Opacity > .05))
                                throw new Exception("Loading backlight does not progress clockwise one section at a time");
                            Capture(window, System.IO.Path.Combine(root, $"loading-phase-{i}.png"));
                        }
                    }
                    else if (sections.Any(p => p.HasAnimatedProperties || p.Opacity <= 0))
                        throw new Exception("Reduced-motion activity feedback is missing");
                    window.WindowState = WindowState.Minimized;
                    if (sections.Any(p => p.HasAnimatedProperties)) throw new Exception("Minimized window kept animating");
                    window.WindowState = WindowState.Normal;
                    typeof(MainWindow).GetMethod("ResetNativeLaunchControls", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(window, null);
                    if (mark.IsActive || sections.Any(p => p.HasAnimatedProperties || p.Opacity != 0))
                        throw new Exception("Completion/failure cleanup left a loading animation running");
                    setBusy.Invoke(window, new object[] { true });
                    window.Close();
                    if (sections.Any(p => p.HasAnimatedProperties)) throw new Exception("Closed window retained its animation clocks");
                }
                catch (Exception error) { failure = error; window.Close(); }
                finally { app.Shutdown(); }
            }));
            app.Run(window);
        });
        thread.SetApartmentState(ApartmentState.STA); thread.Start(); thread.Join();
        if (failure != null) throw failure;
        Console.WriteLine("Actual WPF loading mark: clockwise pulses, version, idle/cleanup, minimize and close checks passed.");
    }
    private static void Capture(Window window, string path)
    {
        var image = new RenderTargetBitmap((int)window.ActualWidth, (int)window.ActualHeight, 96, 96, PixelFormats.Pbgra32);
        image.Render(window); var png = new PngBitmapEncoder(); png.Frames.Add(BitmapFrame.Create(image));
        using var output = File.Create(path); png.Save(output);
    }
}
