using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Host actions are separate from the original 167-command control profiles.</summary>
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record HeadlightBinding
{
    public int Version { get; init; } = 1;
    public int Key { get; init; }
    public int Button { get; init; } = -1;
    public void Validate()
    {
        var scan = Key & 255;
        if (Version != 1 || Key is < 0 or > 0x7ff || (Key != 0 && scan == 0) ||
            scan is 0x43 or 0x44 or 0x57 || Button is < -1 or > 25)
            throw new InvalidDataException("Unsupported headlight binding.");
    }
}

public sealed class HeadlightBindings(string dataRoot)
{
    private string Store => Path.Combine(dataRoot, "controls", "mw3-headlights-v1.json");
    public HeadlightBinding Load()
    {
        if (!File.Exists(Store)) return new();
        if (new FileInfo(Store).Length > 4096) throw new InvalidDataException("Headlight binding is too large.");
        var binding = JsonSerializer.Deserialize<HeadlightBinding>(File.ReadAllText(Store))
            ?? throw new InvalidDataException("Empty headlight binding.");
        binding.Validate();
        return binding;
    }
    public void Save(HeadlightBinding binding)
    {
        binding.Validate();
        ControlProfiles.AtomicWrite(Store, JsonSerializer.Serialize(binding, new JsonSerializerOptions { WriteIndented = true }));
    }
    public void PrepareLaunch(JsonObject launch, string session, bool enabled)
    {
        var native = launch["native"]!.AsObject();
        native["runtime_environment"] ??= new JsonObject();
        var environment = native["runtime_environment"]!.AsObject();
        environment["MW34_HEADLIGHT_BINDINGS"] = "";
        if (!enabled) return;
        var binding = Load();
        var path = Path.Combine(session, "mw3-headlights.txt");
        ControlProfiles.AtomicWrite(path, "CC_MW3_HEADLIGHTS_V1\n" +
            binding.Key.ToString(CultureInfo.InvariantCulture) + " " +
            binding.Button.ToString(CultureInfo.InvariantCulture) + "\n");
        environment["MW34_HEADLIGHT_BINDINGS"] = PackStorage.CanonicalFilePath(path);
    }
}
