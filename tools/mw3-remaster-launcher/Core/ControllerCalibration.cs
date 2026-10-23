using System.IO;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

// Shared device calibration; game-specific actions belong in a separate profile.
public sealed class AxisCalibration
{
    public double Minimum { get; set; } = -32768;
    public double Center { get; set; }
    public double Maximum { get; set; } = 32767;
    public double Deadzone { get; set; } = .12;
    public double Response { get; set; } = 1;
    public bool Inverted { get; set; }

    public void Validate(bool trigger)
    {
        if (!double.IsFinite(Minimum) || !double.IsFinite(Center) || !double.IsFinite(Maximum) ||
            !double.IsFinite(Deadzone) || !double.IsFinite(Response) || Minimum < -32768 || Maximum > 32767 ||
            Deadzone is < 0 or > .45 || Response is < .25 or > 4 ||
            (trigger ? Center < 0 || Maximum - Center < 8192 : Center - Minimum < 8192 || Maximum - Center < 8192))
            throw new InvalidDataException("Calibration range is incomplete. Move both sticks fully and press each trigger fully.");
    }

    public double Adjust(short raw, bool trigger)
    {
        Validate(trigger);
        double value = trigger ? Math.Clamp((raw - Center) / (Maximum - Center), 0, 1) :
            Math.Clamp((raw - Center) / (raw >= Center ? Maximum - Center : Center - Minimum), -1, 1);
        value = Math.CopySign(Math.Pow(Math.Max(0, Math.Abs(value) - Deadzone) / (1 - Deadzone), Response), value);
        return Inverted ? (trigger ? 1 - value : -value) : value;
    }
}

public sealed class ControllerCalibration
{
    public int Version { get; set; } = 1;
    public string DeviceKey { get; set; } = "";
    public AxisCalibration[] Axes { get; set; } = Enumerable.Range(0, 6).Select(i =>
        new AxisCalibration { Minimum = i >= 4 ? 0 : -32768 }).ToArray();
    public void Validate()
    {
        if (Version != 1 || DeviceKey.Length != 64 || DeviceKey.Any(c => !Uri.IsHexDigit(c)) || Axes?.Length != 6)
            throw new InvalidDataException("Unsupported controller calibration file.");
        for (int i = 0; i < 6; i++) (Axes[i] ?? throw new InvalidDataException("Missing axis calibration.")).Validate(i >= 4);
    }
    private static string PathFor(string root, string key)
    {
        if (key.Length != 64 || key.Any(c => !Uri.IsHexDigit(c))) throw new InvalidDataException("Invalid controller identity.");
        return Path.Combine(root, "controls", "devices", key + ".json");
    }
    public static ControllerCalibration Load(string root, string key)
    {
        string path = PathFor(root, key);
        PackStorage.EnsureNoLinks(path);
        if (!File.Exists(path)) return new() { DeviceKey = key };
        if (new FileInfo(path).Length > 16384) throw new InvalidDataException("Controller calibration file is too large.");
        var data = JsonSerializer.Deserialize<ControllerCalibration>(File.ReadAllText(path)) ?? throw new InvalidDataException("Empty calibration file.");
        data.Validate();
        if (data.DeviceKey != key) throw new InvalidDataException("Calibration belongs to a different controller.");
        return data;
    }
    public void Save(string root)
    {
        Validate();
        ControlProfiles.AtomicWrite(PathFor(root, DeviceKey), JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true }));
    }
}

/// <summary>Two explicit phases avoid mistaking a held stick for the resting center.</summary>
public sealed class CalibrationCapture
{
    private readonly List<short[]> rest = new();
    private readonly short[] minimum = Enumerable.Repeat(short.MaxValue, 6).ToArray();
    private readonly short[] maximum = Enumerable.Repeat(short.MinValue, 6).ToArray();
    public void Rest(short[] axes)
    {
        if (axes.Length != 6) throw new ArgumentException("Six gamepad axes required.");
        if (rest.Count < 180) rest.Add((short[])axes.Clone());
    }
    public void Range(short[] axes)
    {
        if (axes.Length != 6) throw new ArgumentException("Six gamepad axes required.");
        for (int i = 0; i < 6; i++) { minimum[i] = Math.Min(minimum[i], axes[i]); maximum[i] = Math.Max(maximum[i], axes[i]); }
    }
    public ControllerCalibration Finish(string key)
    {
        if (rest.Count < 30) throw new InvalidDataException("Keep the controller at rest for at least one second.");
        var result = new ControllerCalibration { DeviceKey = key };
        for (int i = 0; i < 6; i++)
        {
            var values = rest.Select(s => (int)s[i]).Order().ToArray();
            int center = values[values.Length / 2];
            if (values[^1] - values[0] > 1800 || (i < 4 && Math.Abs(center) > 8192) || (i >= 4 && center > 4096))
                throw new InvalidDataException("Controller moved during the rest step. Release sticks and triggers, then start again.");
            result.Axes[i] = new() { Minimum = minimum[i], Maximum = maximum[i], Center = center };
        }
        result.Validate(); return result;
    }
}
