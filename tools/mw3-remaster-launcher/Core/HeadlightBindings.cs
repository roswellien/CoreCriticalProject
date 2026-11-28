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
    public int Key { get; init; } = 0x26;
    public int Button { get; init; } = -1;
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public int Mouse { get; set; }
    public void Validate()
    {
        var scan = Key & 255;
        if (Version != 1 || Key is < 0 or > 0x7ff || (Key != 0 && scan == 0) ||
            scan is 0x43 or 0x44 or 0x57 || Button is < -1 or > 25 || Mouse is < 0 or > 7)
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
    public string? WriteNativeBinding(string session, bool enabled) =>
        WriteNativeBinding(session, enabled ? Load() : null);

    internal static string? WriteNativeBinding(string session, HeadlightBinding? binding)
    {
        if (binding == null) return null;
        binding.Validate();
        if (binding.Key == 0 && binding.Button < 0 && binding.Mouse == 0) return null;

        var text = binding.Mouse == 0
            ? FormattableString.Invariant($"CC_MW3_HEADLIGHTS_V1\n{binding.Key} {binding.Button}\n")
            : FormattableString.Invariant($"CC_MW3_HEADLIGHTS_V2\n{binding.Key} {binding.Button} {binding.Mouse}\n");
        var path = Path.Combine(session, "mw3-headlights.txt");
        ControlProfiles.AtomicWrite(path, text);
        return PackStorage.CanonicalFilePath(path);
    }

    public void PrepareLaunch(JsonObject launch, string session, bool enabled)
    {
        var binding = enabled ? Load() : null;
        if (binding?.Mouse > 0)
            throw new InvalidDataException("Mouse headlight bindings require MW3-RE. Choose a key or controller button for D7VK.");

        var path = WriteNativeBinding(session, binding);
        var native = launch["native"]!.AsObject();
        native["runtime_environment"] ??= new JsonObject();
        var environment = native["runtime_environment"]!.AsObject();
        environment["MW34_HEADLIGHT_BINDINGS"] = path ?? "";
    }
}
