using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Import-time metadata checks; the coordinator validates embedded ZRD lookups.</summary>
public static class LegacyChassisSkins
{
    public const string Capability = "legacy-mech-skins";

    public static int Validate(JsonElement descriptor, NativePackPayload payload)
    {
        if (!descriptor.TryGetProperty("schema_version", out var schema) ||
            schema.ValueKind != JsonValueKind.Number || !schema.TryGetInt32(out var version) ||
            version is not (1 or 2))
            throw new InvalidDataException("Unsupported legacy chassis descriptor version.");
        if (version == 1) return version;
        if (!payload.RequiredCapabilities.TryGetValue(Capability, out var required) || required != 1)
            throw new InvalidDataException("Legacy skins require legacy-mech-skins version 1.");
        if (!descriptor.TryGetProperty("skins", out var skins) ||
            skins.ValueKind != JsonValueKind.Array || skins.GetArrayLength() is < 1 or > 8)
            throw new InvalidDataException("Legacy skins require 1–8 ordered records.");

        var ids = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var suffixes = new HashSet<string>(StringComparer.Ordinal);
        var fields = new HashSet<string> { "id", "message", "suffix" };
        var index = 0;
        foreach (var row in skins.EnumerateArray())
        {
            if (row.ValueKind != JsonValueKind.Object ||
                !fields.SetEquals(row.EnumerateObject().Select(p => p.Name)) ||
                row.EnumerateObject().Any(p => p.Value.ValueKind != JsonValueKind.String))
                throw new InvalidDataException("Invalid legacy skin metadata fields.");
            var id = row.GetProperty("id").GetString()!;
            var suffix = row.GetProperty("suffix").GetString()!;
            var message = index == 0 ? "MSG_SKIN_PRIMARY" : "MSG_SKIN_VARIANT" + (char)('A' + index);
            var validSuffix = index == 0 ? suffix.Length == 0 : Regex.IsMatch(suffix, @"\A_[a-z0-9]{1,8}\z");
            if (!Regex.IsMatch(id, @"\A[a-z0-9][a-z0-9._-]{0,63}\z") || !ids.Add(id) ||
                row.GetProperty("message").GetString() != message || !validSuffix || !suffixes.Add(suffix))
                throw new InvalidDataException("Invalid, duplicate or out-of-order legacy skin metadata.");
            index++;
        }
        return version;
    }
}
