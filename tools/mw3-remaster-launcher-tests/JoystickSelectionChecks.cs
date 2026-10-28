using System.IO;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

internal static class JoystickSelectionChecks
{
    public static void Run()
    {
        var attached = new[]
        {
            new DirectInputJoystick("{11111111-1111-1111-1111-111111111111}", "Flight stick", "Flight stick"),
            new DirectInputJoystick("{22222222-2222-2222-2222-222222222222}", "Flight stick", "Flight stick 2"),
            new DirectInputJoystick("{33333333-3333-3333-3333-333333333333}", "Gamepad", "Gamepad")
        };

        Check(DirectInputJoystickSelection.Resolve(new LauncherSettings(), attached) == attached[0],
            "The default choice must retain Windows' first-attached-device behavior.");
        Check(DirectInputJoystickSelection.Resolve(new LauncherSettings
        {
            DirectInputJoystickInstanceGuid = attached[1].InstanceGuid,
            DirectInputJoystickProductName = attached[1].ProductName
        }, attached) == attached[1], "An exact instance GUID must beat a duplicate product name.");
        Check(DirectInputJoystickSelection.Resolve(new LauncherSettings
        {
            DirectInputJoystickInstanceGuid = "{44444444-4444-4444-4444-444444444444}",
            DirectInputJoystickProductName = "Flight stick"
        }, attached) == attached[0], "Product name must be used when the saved GUID is unavailable.");
        Check(DirectInputJoystickSelection.Resolve(new LauncherSettings { DirectInputJoystickNone = true }, attached) == null,
            "None must not resolve to an attached joystick.");
        Check(DirectInputJoystickSelection.Resolve(new LauncherSettings
        {
            DirectInputJoystickInstanceGuid = attached[2].InstanceGuid,
            DirectInputJoystickProductName = attached[2].ProductName
        }, attached.Take(2).ToArray()) == null, "A missing saved device must not select an unrelated joystick.");

        var automatic = GameRunner.CreateLaunchProfile(
            """{"graphics":{},"native":{"runtime_environment":{"MW34_DI_JOYSTICK_GUID":"stale"}}}""",
            new LauncherSettings());
        var automaticEnvironment = automatic["native"]!["runtime_environment"]!;
        Check(automaticEnvironment["MW34_DI_JOYSTICK_MODE"]!.GetValue<string>() == "default" &&
            automaticEnvironment["MW34_DI_JOYSTICK_GUID"]!.GetValue<string>() == string.Empty &&
            automaticEnvironment["MW34_DI_JOYSTICK_NAME"]!.GetValue<string>() == string.Empty,
            "The default choice must clear stale selection bindings.");

        var profile = GameRunner.CreateLaunchProfile(
            """{"graphics":{},"native":{"runtime_environment":{"MW34_DI_JOYSTICK_GUID":"stale"}}}""",
            new LauncherSettings
            {
                DirectInputJoystickInstanceGuid = attached[1].InstanceGuid,
                DirectInputJoystickProductName = attached[1].ProductName
            });
        var environment = profile["native"]!["runtime_environment"]!;
        Check(environment["MW34_DI_JOYSTICK_MODE"]!.GetValue<string>() == "device" &&
            environment["MW34_DI_JOYSTICK_GUID"]!.GetValue<string>() == attached[1].InstanceGuid &&
            environment["MW34_DI_JOYSTICK_NAME"]!.GetValue<string>() == attached[1].ProductName,
            "The selected DirectInput identity was not applied to the launch profile.");

        DirectInputJoystickSelection.ApplyRuntimeEnvironment(environment.AsObject(),
            new LauncherSettings { DirectInputJoystickNone = true });
        Check(environment["MW34_DI_JOYSTICK_MODE"]!.GetValue<string>() == "none" &&
            environment["MW34_DI_JOYSTICK_GUID"]!.GetValue<string>() == string.Empty &&
            environment["MW34_DI_JOYSTICK_NAME"]!.GetValue<string>() == string.Empty,
            "None did not clear the selected identity in the launch environment.");

        var root = Path.Combine(Path.GetTempPath(), "cc-joystick-settings-" + Guid.NewGuid().ToString("N"));
        try
        {
            var settings = new SettingsManager(root, root);
            settings.Current.DirectInputJoystickInstanceGuid = attached[1].InstanceGuid;
            settings.Current.DirectInputJoystickProductName = attached[1].ProductName;
            settings.Save();
            var saved = new SettingsManager(root, root).Current;
            Check(saved.DirectInputJoystickInstanceGuid == attached[1].InstanceGuid &&
                saved.DirectInputJoystickProductName == attached[1].ProductName,
                "The selected joystick identity was not persisted.");

            settings.Current.DirectInputJoystickNone = true;
            settings.Save();
            Check(new SettingsManager(root, root).Current.DirectInputJoystickNone,
                "The explicit None choice was not persisted.");
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, true);
            }
        }

        Console.WriteLine("DirectInput joystick launcher-selection checks passed.");
    }

    private static void Check(bool value, string message)
    {
        if (!value)
        {
            throw new Exception(message);
        }
    }
}
