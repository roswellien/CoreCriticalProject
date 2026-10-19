using System;
using System.IO;
using System.Linq;
using System.Windows;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
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
                var launcherExe = Path.Combine(basePath, "MW3RemasterLauncher.exe");
                var artworkDir = Path.Combine(basePath, "Assets", "Plates");
                SteamHelper.AddToSteam(launcherExe, artworkDir);

                if (argsList.Contains("--silent", StringComparer.OrdinalIgnoreCase))
                {
                    Shutdown(0);
                    return;
                }
            }
        }
    }
}
