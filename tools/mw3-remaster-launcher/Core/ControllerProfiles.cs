using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

public sealed class ControllerProfile
{
    public int Version { get; set; } = 1;
    public string GameId { get; set; } = GameCatalog.Mw3;
    public bool Enabled { get; set; }
    public string DeviceKey { get; set; } = "";
    public int[] Buttons { get; set; } = [12, 6, 70, 97, 63, 0, 81, 7, 27, 43, 42, 44, 45, 46, 47, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    public int[] Triggers { get; set; } = [20, 61];
    // Source axes for throttle, steering, torso yaw and pitch. -1 means unbound.
    public int[] Axes { get; set; } = [1, 0, 2, 3];
    public double[] Scale { get; set; } = [-1, 1, 1, 1];
    public double TriggerThreshold { get; set; } = .25;
    public void Validate()
    {
        if (Version != 1 || GameId != GameCatalog.Mw3 || DeviceKey == null ||
            (DeviceKey.Length != 0 && (DeviceKey.Length != 64 || DeviceKey.Any(c => !Uri.IsHexDigit(c)))) ||
            (Enabled && DeviceKey.Length == 0) || Buttons?.Length != 26 || Triggers?.Length != 2 || Axes?.Length != 4 || Scale?.Length != 4 ||
            !double.IsFinite(TriggerThreshold) || TriggerThreshold is < .05 or > .95)
            throw new InvalidDataException("Unsupported MW3 controller layout.");
        var commands = ControlProfiles.Actions.Select(a => a.Command).Append(0).ToHashSet();
        if (Buttons.Concat(Triggers).Any(a => !commands.Contains(a)) || Axes.Any(a => a is < -1 or > 3) ||
            Scale.Any(s => !double.IsFinite(s) || Math.Abs(s) is < .1 or > 2))
            throw new InvalidDataException("Invalid controller action or stick assignment.");
    }
}

public sealed class ControllerProfiles(string dataRoot)
{
    private string Store => Path.Combine(dataRoot, "controls", GameCatalog.Mw3, "controller.json");
    public ControllerProfile Load()
    {
        PackStorage.EnsureNoLinks(Store);
        if (!File.Exists(Store)) return new();
        if (new FileInfo(Store).Length > 16384) throw new InvalidDataException("Controller layout is too large.");
        var data = JsonSerializer.Deserialize<ControllerProfile>(File.ReadAllText(Store)) ?? throw new InvalidDataException("Empty controller layout.");
        data.Validate(); return data;
    }
    public void Save(ControllerProfile profile)
    {
        profile.Validate();
        ControlProfiles.AtomicWrite(Store, JsonSerializer.Serialize(profile, new JsonSerializerOptions { WriteIndented = true }));
    }
    public static string Export(ControllerProfile profile, ControllerCalibration calibration)
    {
        profile.Validate(); calibration.Validate();
        if (profile.DeviceKey != calibration.DeviceKey) throw new InvalidDataException("Layout/calibration controller identity mismatch.");
        string N(double value) => value.ToString("R", CultureInfo.InvariantCulture);
        var result = new StringBuilder("CC_MW3_CONTROLLER_V1\n").AppendLine(profile.DeviceKey);
        foreach (var axis in calibration.Axes)
            result.AppendLine(string.Join(' ', N(axis.Minimum), N(axis.Center), N(axis.Maximum), N(axis.Deadzone), N(axis.Response), axis.Inverted ? "1" : "0"));
        result.AppendLine(string.Join(' ', profile.Buttons)).AppendLine(string.Join(' ', profile.Triggers));
        result.AppendLine(string.Join(' ', profile.Axes)).AppendLine(string.Join(' ', profile.Scale.Select(N))).AppendLine(N(profile.TriggerThreshold));
        return result.ToString();
    }
    public void PrepareLaunch(JsonObject launch, string session)
    {
        var profile = Load();
        var native = launch["native"]!.AsObject();
        var env = native["runtime_environment"]?.AsObject() ?? new JsonObject(); native["runtime_environment"] = env;
        // Explicit empty bindings also clear inherited development-shell settings in the child.
        env["MW34_CONTROLLER_CONFIG"] = ""; env["MW34_CONTROLLER_SDL"] = "";
        if (!profile.Enabled) return;
        if (native["controller_input_version"]?.GetValue<int>() != 1)
            throw new InvalidOperationException("This MW3 runtime needs the controller input update. Disable controller gameplay or install a compatible runtime update.");
        string sdl = Path.Combine(AppContext.BaseDirectory, "SDL3.dll");
        if (!File.Exists(sdl)) throw new FileNotFoundException("The controller runtime is missing.", sdl);
        PackStorage.EnsureNoLinks(sdl);
        string path = Path.Combine(session, "mw3-controller.txt");
        ControlProfiles.AtomicWrite(path, Export(profile, ControllerCalibration.Load(dataRoot, profile.DeviceKey)));
        env["MW34_CONTROLLER_CONFIG"] = PackStorage.CanonicalFilePath(path);
        env["MW34_CONTROLLER_SDL"] = PackStorage.CanonicalFilePath(sdl);
    }
}
