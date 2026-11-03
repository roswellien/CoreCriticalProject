using System.IO;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Resource-reader contracts advertised by the selected runtime, never by a content pack.</summary>
public static class RuntimeContentCapabilities
{
    private static readonly Dictionary<string, string> Profiles = new(StringComparer.Ordinal) {
        ["prepared-ui-v1"] = "ui-artwork",
        ["prepared-cinematic-v1"] = "cinematic-replacements",
        ["prepared-native-v1"] = "prepared-mechs",
        ["prepared-environment-v1"] = "environment-resources",
        ["prepared-music-v1"] = "soundtrack",
        [SkinPack.Profile] = "additional-mech-skins",
        [ChassisPack.Profile] = "additional-mech-chassis"
    };
    private static readonly JsonObject Legacy = LoadLegacy();
    private static JsonObject LoadLegacy()
    {
        using var input = typeof(RuntimeContentCapabilities).Assembly.GetManifestResourceStream(
            "MW3RemasterLauncher.Core.legacy_content_capabilities.json")!;
        using var reader = new StreamReader(input);
        return JsonNode.Parse(reader.ReadToEnd())!["hosts"]!.AsObject();
    }

    public static void ValidateRequirements(NativePackPayload payload)
    {
        if (payload.RequiredCapabilities == null || payload.RequiredCapabilities.Count > 32)
            throw new InvalidDataException("Invalid content capability requirements.");
        foreach (var (name, version) in payload.RequiredCapabilities)
            if ((!Profiles.ContainsValue(name) && name != "mech-headlights" &&
                 name != LegacyChassisSkins.Capability && name != "surface-materials") || version < 1)
                throw new InvalidDataException("Unsupported content capability requirement: " + name);
    }

    public static JsonObject Advertised(JsonObject native)
    {
        JsonNode? declarations;
        // An explicit empty table means no capabilities. Never fill missing
        // entries from history when the runtime provides its own declaration.
        if (native.ContainsKey("content_capabilities")) declarations = native["content_capabilities"];
        else
        {
            var identity = native["executable_sha256"]?.GetValue<string>()?.ToLowerInvariant();
            declarations = identity == null ? null : Legacy[identity];
            if (declarations == null) return new JsonObject();
        }
        if (declarations is not JsonObject table || table.Count > 64)
            throw new InvalidDataException("Invalid runtime content capabilities.");
        foreach (var (name, versions) in table)
        {
            if (versions is not JsonArray list || list.Count is < 1 or > 16 ||
                list.Any(v => v is not JsonValue value || !value.TryGetValue<int>(out var number) || number < 1) ||
                list.Select(v => v!.GetValue<int>()).Distinct().Count() != list.Count)
                throw new InvalidDataException("Invalid runtime capability versions: " + name);
        }
        return (JsonObject)table.DeepClone();
    }

    public static void Require(JsonObject native, NativePackPayload payload, string packId)
    {
        ValidateRequirements(payload);
        if (!Profiles.TryGetValue(payload.Profile, out var capability))
            throw new InvalidDataException("Unsupported content profile: " + payload.Profile);
        var available = Advertised(native);
        void Need(string name, int version)
        {
            if (available[name] is not JsonArray versions || !versions.Any(v => v!.GetValue<int>() == version))
                throw new InvalidDataException($"Pack '{packId}' requires {name} version {version}. Update the game runtime or choose a compatible pack.");
        }
        Need(capability, 1); // Existing v1 profiles imply v1; no manifest rewrite is required.
        foreach (var (name, version) in payload.RequiredCapabilities) Need(name, version);
    }
}
