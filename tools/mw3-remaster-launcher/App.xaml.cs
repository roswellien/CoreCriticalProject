using System;
using System.IO;
using System.Linq;
using System.Windows;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher
{
    public partial class App : Application
    {
        private readonly bool _showMainWindow;
        public App() : this(true) { }
        public App(bool showMainWindow) { _showMainWindow = showMainWindow; }
        protected override async void OnStartup(StartupEventArgs e)
        {
            if (e.Args.Length == 2 && e.Args[0] == "--apply-ccupdate")
            {
                ShutdownMode = ShutdownMode.OnExplicitShutdown;
                base.OnStartup(e);
                try { await LauncherUpdates.ApplyJobAsync(e.Args[1]); Shutdown(0); }
                catch (Exception error)
                {
                    MessageBox.Show(error.Message, "Core Critical update failed", MessageBoxButton.OK, MessageBoxImage.Error);
                    Shutdown(1);
                }
                return;
            }
            base.OnStartup(e);

            DispatcherUnhandledException += (s, args) =>
            {
                MessageBox.Show($"Launcher Error:\n\n{args.Exception.Message}\n\nStack:\n{args.Exception.StackTrace}",
                    "Launcher Error", MessageBoxButton.OK, MessageBoxImage.Error);
                args.Handled = true;
            };

            var argsList = e.Args;
            if (argsList.Contains("--add-steam", StringComparer.OrdinalIgnoreCase))
            {
                var basePath = AppDomain.CurrentDomain.BaseDirectory;
                var launcherExe = Path.Combine(basePath, "Core Critical Launcher.exe");
                var artworkDir = Path.Combine(basePath, "Assets", "Plates");
                var success = true;
                try { SteamHelper.AddToSteam(launcherExe, artworkDir); }
                catch (Exception error)
                {
                    success = false;
                    try
                    {
                        Directory.CreateDirectory(LauncherPaths.DataRoot);
                        File.WriteAllText(Path.Combine(LauncherPaths.DataRoot, "steam-integration.log"), error.Message);
                    }
                    catch (IOException) { }
                    catch (UnauthorizedAccessException) { }
                    if (!argsList.Contains("--silent", StringComparer.OrdinalIgnoreCase))
                        MessageBox.Show(error.Message, "Steam integration", MessageBoxButton.OK, MessageBoxImage.Warning);
                }

                if (argsList.Contains("--silent", StringComparer.OrdinalIgnoreCase))
                {
                    Shutdown(success ? 0 : 1);
                    return;
                }
            }
            if (_showMainWindow) new MainWindow().Show();
        }
    }
}
