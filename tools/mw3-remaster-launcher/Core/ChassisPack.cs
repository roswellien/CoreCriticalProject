using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>Additional, namespaced chassis with data-only definitions and visual payloads.</summary>
public static class ChassisPack
{
    public const string Profile = "additional-chassis-v1";
    public const string Registry = "chassis/chassis.json";
    public sealed record Chassis(string Id, string Name);
    private static readonly HashSet<string> Templates = new(StringComparer.Ordinal) {
        "annihilator", "avatar", "blackhawk", "bushwacker", "cauldron", "champion", "daishi",
        "firefly", "madcat", "orion", "owens", "puma", "shadowcat", "strider", "sunder",
        "supernova", "thor", "vulture"
    };

    private static void ValidateHeadlights(JsonElement row, NativePackPayload payload)
    {
        if (!row.TryGetProperty("headlights", out var lights)) return;
        if (lights.ValueKind != JsonValueKind.Array || lights.GetArrayLength() > 8)
            throw new InvalidDataException("Expected zero through eight headlights.");
        if (lights.GetArrayLength() > 0 &&
            (!payload.RequiredCapabilities.TryGetValue("mech-headlights", out var version) || version != 1 ||
             !payload.RequiredCapabilities.TryGetValue("additional-mech-chassis", out var chassisVersion) || chassisVersion < 2))
            throw new InvalidDataException("Headlights require mech-headlights version 1 and chassis version 2 or newer.");
        var ids = new HashSet<string>(StringComparer.Ordinal);
        var fields = new HashSet<string>(new[] { "id", "space", "attachment", "position", "direction", "color",
            "intensity", "range", "inner_angle", "outer_angle" });
        double Number(JsonElement value, double low, double high)
        {
            if (value.ValueKind != JsonValueKind.Number || !value.TryGetDouble(out var number) ||
                !double.IsFinite(number) || number < low || number > high)
                throw new InvalidDataException("Invalid headlight number.");
            return number;
        }
        foreach (var light in lights.EnumerateArray())
        {
            if (light.ValueKind != JsonValueKind.Object || !fields.SetEquals(light.EnumerateObject().Select(p => p.Name)))
                throw new InvalidDataException("Invalid headlight fields.");
            string Text(string field) => light.GetProperty(field).ValueKind == JsonValueKind.String
                ? light.GetProperty(field).GetString()! : "";
            var space = Text("space");
            if (!Regex.IsMatch(Text("id"), @"\A[a-z0-9_-]{1,31}\z") || !ids.Add(Text("id")) ||
                !Regex.IsMatch(Text("attachment"), @"\A[A-Za-z0-9_.-]{1,31}\z") ||
                (space != "guest_node" && space != "donor_bone") ||
                (space == "donor_bone" && row.TryGetProperty("legacy", out _)))
                throw new InvalidDataException("Invalid headlight identity or attachment.");
            double[] Vector(string field, double low, double high)
            {
                var value = light.GetProperty(field);
                if (value.ValueKind != JsonValueKind.Array || value.GetArrayLength() != 3)
                    throw new InvalidDataException("Invalid headlight vector.");
                return value.EnumerateArray().Select(v => Number(v, low, high)).ToArray();
            }
            Vector("position", -100, 100);
            Vector("color", 0, 1);
            var direction = Vector("direction", -1e30, 1e30);
            if (direction.All(v => v == 0)) throw new InvalidDataException("Headlight direction cannot be zero.");
            Number(light.GetProperty("intensity"), 0, 8);
            Number(light.GetProperty("range"), 1, 256);
            if ((float)Number(light.GetProperty("inner_angle"), 0, 89) >= (float)Number(light.GetProperty("outer_angle"), 0, 89))
                throw new InvalidDataException("Invalid headlight cone.");
        }
    }

    public static List<Chassis> Read(string root, PackManifest manifest)
    {
        var formats = manifest.NativePayload?.RequiredFormats;
        var baselineFormats = formats?.Where(format => format != OwnedEmission.Format).ToList();
        if (formats != null && formats.Contains(OwnedEmission.Format) &&
            (formats.Count(format => format == OwnedEmission.Format) != 1 ||
             !new[] { "MW3LEGACY", "BWMESH4", "BWTEX1" }.All(formats.Contains)))
            throw new InvalidDataException("Invalid owned emission format declaration.");
        if (manifest.NativePayload?.Profile != Profile || manifest.NativePayload.Registry != Registry ||
            !(baselineFormats!.SequenceEqual(new[] { "BWMESH4", "BWTEX1" }) ||
              baselineFormats!.SequenceEqual(new[] { "BWMESH4", "BWTEX1", "MW3ICON1" }) ||
              baselineFormats!.SequenceEqual(new[] { "BWMESH4", "BWTEX1", "BWSFM1" }) ||
              baselineFormats!.SequenceEqual(new[] { "BWMESH4", "BWTEX1", "MW3ICON1", "BWSFM1" }) ||
              baselineFormats!.SequenceEqual(new[] { "MW3LEGACY" }) ||
              baselineFormats!.SequenceEqual(new[] { "MW3LEGACY", "BWSNR2" }) ||
              baselineFormats!.SequenceEqual(new[] { "MW3LEGACY", "BWMESH4", "BWTEX1" }) ||
              baselineFormats!.SequenceEqual(new[] { "MW3LEGACY", "BWMESH4", "BWTEX1", "BWSNR2" })) ||
            (manifest.NativePayload.RequiredFormats.Contains("BWSFM1") &&
             (!manifest.NativePayload.RequiredCapabilities.TryGetValue("surface-materials", out var surfaceVersion) || surfaceVersion != 1)) ||
            manifest.Dependencies?.Count > 0 || manifest.Conflicts?.Count > 0 ||
            manifest.Files == null || manifest.Files.Count is < 1 or > 1025 ||
            manifest.Files.Values.Sum(p => p.Bytes) > 4L * 1024 * 1024 * 1024)
            throw new InvalidDataException("Invalid additional chassis pack contract.");
        var used = new HashSet<string>(StringComparer.Ordinal) { Registry };
        string Verify(string name, string? format = null)
        {
            if (!manifest.Files.TryGetValue(name, out var pin) || pin.Format != format ||
                pin.Bytes is < 1 or > 256L * 1024 * 1024)
                throw new InvalidDataException("Undeclared or unsupported chassis resource: " + name);
            var path = PackStorage.Resolve(root, name);
            using var stream = File.OpenRead(path);
            if (stream.Length != pin.Bytes ||
                !Convert.ToHexString(SHA256.HashData(stream)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Chassis resource integrity failure: " + name);
            if (format != null)
            {
                stream.Position = 0;
                using var reader = new BinaryReader(stream);
                var expected = System.Text.Encoding.ASCII.GetBytes(format.PadRight(8, '\0'));
                if (!reader.ReadBytes(8).SequenceEqual(expected))
                    throw new InvalidDataException("Incorrect chassis payload format: " + name);
            }
            used.Add(name);
            return path;
        }
        var registryPath = Verify(Registry);
        if (new FileInfo(registryPath).Length > PackStorage.MaxJsonBytes)
            throw new InvalidDataException("Chassis registry exceeds size limit.");
        using var document = JsonDocument.Parse(File.ReadAllText(registryPath));
        PackStorage.ValidateUniqueProperties(document.RootElement);
        var registry = document.RootElement;
        if (registry.GetProperty("schema_version").GetInt32() != 2 ||
            registry.GetProperty("payload_profile").GetString() != Profile)
            throw new InvalidDataException("Unsupported chassis registry.");
        var rows = registry.GetProperty("chassis");
        if (rows.ValueKind != JsonValueKind.Array || rows.GetArrayLength() is < 1 or > 128)
            throw new InvalidDataException("Invalid chassis count.");
        var ids = new HashSet<string>(StringComparer.Ordinal);
        var result = new List<Chassis>();
        var fields = new HashSet<string>(new[] { "id", "name", "controller", "metadata_template", "definition", "meshes", "textures" });
        foreach (var row in rows.EnumerateArray())
        {
            ValidateHeadlights(row, manifest.NativePayload);
            if (manifest.NativePayload.RequiredFormats.Contains("MW3LEGACY"))
            {
                if (!manifest.NativePayload.RequiredCapabilities.TryGetValue("additional-mech-chassis", out var version) || version != 3 ||
                    !new HashSet<string>(new[] { "id", "name", "metadata_template", "legacy" }).SetEquals(row.EnumerateObject().Select(p => p.Name).Where(name => name != "appearances" && name != "headlights")))
                    throw new InvalidDataException("Legacy chassis resources require version 3 and exact fields.");
                var legacyId = row.GetProperty("id").GetString() ?? "";
                var legacyName = row.GetProperty("name").GetString() ?? "";
                if (!legacyId.StartsWith(manifest.Id + ":", StringComparison.Ordinal) ||
                    !Regex.IsMatch(legacyId, @"\A[a-z0-9][a-z0-9._-]{0,127}:[a-z0-9][a-z0-9._-]{0,63}\z") || !ids.Add(legacyId) ||
                    legacyName.Length is < 1 or > 64 || legacyName.Any(c => c < 32 || c > 126) ||
                    !Templates.Contains(row.GetProperty("metadata_template").GetString() ?? ""))
                    throw new InvalidDataException("Invalid legacy chassis identity or metadata template.");
                var resourcePath = Verify(row.GetProperty("legacy").GetString() ?? "");
                if (new FileInfo(resourcePath).Length > PackStorage.MaxJsonBytes)
                    throw new InvalidDataException("Legacy chassis descriptor exceeds size limit.");
                using var resourceDocument = JsonDocument.Parse(File.ReadAllText(resourcePath));
                var descriptor = resourceDocument.RootElement;
                PackStorage.ValidateUniqueProperties(descriptor);
                var descriptorFields = new HashSet<string>(new[] { "schema_version", "resource", "definition", "materials", "silhouette", "models", "motions", "animations", "textures" });
                if (LegacyChassisSkins.Validate(descriptor, manifest.NativePayload) == 2)
                    descriptorFields.Add("skins");
                if (!descriptorFields.SetEquals(descriptor.EnumerateObject().Select(p => p.Name)) ||
                    !Regex.IsMatch(descriptor.GetProperty("resource").GetString() ?? "", @"\A[a-z][a-z0-9_]{0,15}\z"))
                    throw new InvalidDataException("Invalid legacy chassis descriptor.");
                void VerifyResource(string path)
                {
                    var resolved = Verify(path);
                    if (new FileInfo(resolved).Length > 16 * 1024 * 1024)
                        throw new InvalidDataException("Legacy chassis resource exceeds size limit.");
                }
                foreach (var field in new[] { "definition", "materials", "silhouette" })
                    VerifyResource(descriptor.GetProperty(field).GetString() ?? "");
                foreach (var (role, limit) in new[] { ("models", 3), ("motions", 64), ("animations", 16), ("textures", 512) })
                {
                    var table = descriptor.GetProperty(role);
                    if (table.ValueKind != JsonValueKind.Object)
                        throw new InvalidDataException("Invalid legacy chassis resource table.");
                    var entries = table.EnumerateObject().ToArray();
                    if (entries.Length < 1 || entries.Length > limit ||
                        entries.Select(p => p.Name).Distinct(StringComparer.OrdinalIgnoreCase).Count() != entries.Length ||
                        (role == "models" && !new HashSet<string>(new[] { "close", "distance", "cockpit" }).SetEquals(entries.Select(p => p.Name))))
                        throw new InvalidDataException("Invalid legacy chassis resource count or LODs.");
                    foreach (var entry in entries)
                    {
                        if (!Regex.IsMatch(entry.Name, @"\A[a-zA-Z0-9_.-]{1,31}\z"))
                            throw new InvalidDataException("Invalid legacy chassis member name.");
                        VerifyResource(entry.Value.GetString() ?? "");
                    }
                }
                if (row.TryGetProperty("appearances", out var appearances))
                    ChassisAppearances.Read(appearances, descriptor.GetProperty("textures"), manifest.NativePayload, Verify);
                result.Add(new(legacyId, legacyName));
                continue;
            }
            var rowFields = row.EnumerateObject().Select(p => p.Name).ToHashSet();
            if (!fields.IsSubsetOf(rowFields) || rowFields.Except(fields).Any(p => p != "silhouette" && p != "base_skin_name" && p != "sockets" && p != "headlights" && p != "surface_materials"))
                throw new InvalidDataException("Unknown chassis registration field.");
            if (row.TryGetProperty("sockets", out var sockets))
            {
                if (!manifest.NativePayload.RequiredCapabilities.TryGetValue("additional-mech-chassis", out var required) || required < 2 ||
                    sockets.ValueKind != JsonValueKind.Array || sockets.GetArrayLength() is < 1 or > 64)
                    throw new InvalidDataException("Chassis sockets require version 2 and 1–64 bindings.");
                var nodes = new HashSet<string>(StringComparer.Ordinal);
                foreach (var socket in sockets.EnumerateArray())
                {
                    if (socket.ValueKind != JsonValueKind.Object ||
                        !new HashSet<string>(new[]{"node","bone","position"}).SetEquals(socket.EnumerateObject().Select(p=>p.Name)))
                        throw new InvalidDataException("Invalid chassis socket fields.");
                    var node=socket.GetProperty("node").GetString() ?? "";
                    var bone=socket.GetProperty("bone").GetString() ?? "";
                    var position=socket.GetProperty("position");
                    if (!Regex.IsMatch(node,@"\Afirepoint[0-9]{2}\z") || !nodes.Add(node) ||
                        !Regex.IsMatch(bone,@"\A[A-Za-z0-9_.-]{1,31}\z") || position.ValueKind!=JsonValueKind.Array ||
                        position.GetArrayLength()!=3 || position.EnumerateArray().Any(v=>v.ValueKind!=JsonValueKind.Number ||
                            !v.TryGetDouble(out var number) || !double.IsFinite(number) || Math.Abs(number)>100))
                        throw new InvalidDataException("Invalid or duplicate chassis socket.");
                }
            }
            if (row.TryGetProperty("base_skin_name", out var baseSkin))
            {
                var label = baseSkin.GetString() ?? "";
                if (label.Length is < 1 or > 64 || label.Any(c => c < 32 || c > 126) ||
                    !manifest.NativePayload.RequiredCapabilities.TryGetValue("additional-mech-chassis", out var required) || required < 2)
                    throw new InvalidDataException("Invalid base skin name or missing chassis version 2 requirement.");
            }
            var id = row.GetProperty("id").GetString() ?? "";
            var name = row.GetProperty("name").GetString() ?? "";
            var controller = row.GetProperty("controller").GetString() ?? "";
            if (!id.StartsWith(manifest.Id + ":", StringComparison.Ordinal) ||
                !Regex.IsMatch(id, @"\A[a-z0-9][a-z0-9._-]{0,127}:[a-z0-9][a-z0-9._-]{0,63}\z") || !ids.Add(id) ||
                name.Length is < 1 or > 64 || name.Any(c => c < 32 || c > 126) ||
                !Templates.Contains(controller) || !Templates.Contains(row.GetProperty("metadata_template").GetString() ?? ""))
                throw new InvalidDataException("Invalid chassis identity, name or controller.");
            var authored = Verify(row.GetProperty("definition").GetString() ?? "");
            if (new FileInfo(authored).Length > PackStorage.MaxJsonBytes)
                throw new InvalidDataException("Chassis definition exceeds size limit.");
            using (var definition = JsonDocument.Parse(File.ReadAllText(authored)))
            {
                var data = definition.RootElement;
                PackStorage.ValidateUniqueProperties(data);
                if (data.GetProperty("schema_version").GetInt32() != 1 ||
                    data.GetProperty("template").GetString() != controller ||
                    data.GetProperty("fields").ValueKind != JsonValueKind.Object ||
                    !new HashSet<string>(new[] { "schema_version", "template", "fields" }).SetEquals(data.EnumerateObject().Select(p => p.Name)))
                    throw new InvalidDataException("Unsupported authored chassis definition.");
            }
            foreach (var role in new[] { "meshes", "textures" })
            {
                var bindings = row.GetProperty(role);
                if (!new HashSet<string>(new[] { "close", "distance" }).SetEquals(bindings.EnumerateObject().Select(p => p.Name)))
                    throw new InvalidDataException("Chassis needs close and distance resources.");
                foreach (var lod in new[] { "close", "distance" })
                    Verify(bindings.GetProperty(lod).GetString() ?? "", role == "meshes" ? "BWMESH4" : "BWTEX1");
            }
            if (row.TryGetProperty("silhouette", out var silhouette))
            {
                if (!manifest.NativePayload.RequiredFormats.Contains("MW3ICON1") ||
                    !manifest.NativePayload.RequiredCapabilities.TryGetValue("additional-mech-chassis", out var version) || version < 2)
                    throw new InvalidDataException("Chassis silhouette requires additional-mech-chassis version 2.");
                var bytes = File.ReadAllBytes(Verify(silhouette.GetString() ?? "", "MW3ICON1"));
                if (bytes.Length != 2066 || BitConverter.ToUInt32(bytes, 8) != 41 ||
                    BitConverter.ToUInt32(bytes, 12) != 50 || !bytes.Skip(16).Any(b => b != 0))
                    throw new InvalidDataException("Chassis silhouette must be a nonempty 41x50 MW3ICON1 mask.");
            }
            if (row.TryGetProperty("surface_materials", out var surfaceMaterials))
            {
                if (!manifest.NativePayload.RequiredFormats.Contains("BWSFM1") ||
                    !manifest.NativePayload.RequiredCapabilities.TryGetValue("surface-materials", out var surfVer) || surfVer != 1 ||
                    surfaceMaterials.ValueKind != JsonValueKind.Object ||
                    !new HashSet<string>(new[] { "close", "distance" }).SetEquals(surfaceMaterials.EnumerateObject().Select(p => p.Name)))
                    throw new InvalidDataException("Chassis surface_materials require BWSFM1 and surface-materials version 1.");
                foreach (var lod in new[] { "close", "distance" })
                {
                    var surfPath = Verify(surfaceMaterials.GetProperty(lod).GetString() ?? "", "BWSFM1");
                    var surfLen = new FileInfo(surfPath).Length;
                    if (surfLen is < 36 or > 256L * 1024 * 1024)
                        throw new InvalidDataException("Chassis surface-material sidecar size is out of bounds.");
                    using var surfStream = File.OpenRead(surfPath);
                    using var surfReader = new BinaryReader(surfStream);
                    surfStream.Position = 8;
                    var version = surfReader.ReadUInt32();
                    var batches = surfReader.ReadUInt32();
                    var records = surfReader.ReadUInt32();
                    var images = surfReader.ReadUInt32();
                    if (version != 1 || batches is < 1 or > 4096 || records > 4096 || images > 512 ||
                        surfLen < 32L + batches * 4L)
                        throw new InvalidDataException("Invalid BWSFM1 header in chassis pack.");
                }
            }
            result.Add(new(id, name));
        }
        if (!used.SetEquals(manifest.Files.Keys) || !ids.SetEquals(manifest.Provides?.Mechs ?? new List<string>()))
            throw new InvalidDataException("Chassis manifest and resources disagree.");
        return result;
    }
}
