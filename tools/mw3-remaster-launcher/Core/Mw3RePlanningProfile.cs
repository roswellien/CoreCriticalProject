using System.IO;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>Read pinned packaged planning choices without loading or changing saved launcher settings.</summary>
public static class Mw3RePlanningProfile
{
    public static Mw3RePlanningOptions Read(Mw3ReRuntimeContract contract)
    {
        ArgumentNullException.ThrowIfNull(contract);
        var snapshot = contract.ReadPinnedPlanningProfile();
        try
        {
            using var document = JsonDocument.Parse(snapshot, new JsonDocumentOptions { MaxDepth = 64 });
            var profile = document.RootElement;
            PackStorage.ValidateUniqueProperties(profile);
            RequireFields(profile, "schema_version", "engine", "purpose", "options");
            if (Integer(profile.GetProperty("schema_version")) != 1 ||
                Text(profile.GetProperty("engine")) != "mw3-re" ||
                Text(profile.GetProperty("purpose")) != "planning-defaults")
                throw InvalidProfile();

            var options = profile.GetProperty("options");
            RequireFields(options, "renderer", "width", "height", "aa", "af",
                "window_mode", "render_thread", "lighting");
            // Preserve known saved choices; only the existing planner qualifies bounds and argv.
            return new Mw3RePlanningOptions
            {
                Renderer = Text(options.GetProperty("renderer")) switch
                {
                    "vulkan-wsi" => Mw3ReRenderer.VulkanWsi,
                    _ => throw InvalidProfile()
                },
                Width = Integer(options.GetProperty("width")),
                Height = Integer(options.GetProperty("height")),
                Antialiasing = Text(options.GetProperty("aa")) switch
                {
                    "off" => Mw3ReAntialiasing.Off,
                    "1" => Mw3ReAntialiasing.One,
                    "fxaa" => Mw3ReAntialiasing.Fxaa,
                    "2" => Mw3ReAntialiasing.Two,
                    "4" => Mw3ReAntialiasing.Four,
                    "8" => Mw3ReAntialiasing.Eight,
                    _ => throw InvalidProfile()
                },
                AnisotropicFiltering = Integer(options.GetProperty("af")),
                WindowMode = Text(options.GetProperty("window_mode")) switch
                {
                    "windowed" => Mw3ReWindowMode.Windowed,
                    "fullscreen" => Mw3ReWindowMode.Fullscreen,
                    "borderless" => Mw3ReWindowMode.Borderless,
                    _ => throw InvalidProfile()
                },
                RenderThread = options.GetProperty("render_thread").ValueKind switch
                {
                    JsonValueKind.True => true,
                    JsonValueKind.False => false,
                    _ => throw InvalidProfile()
                },
                Lighting = Text(options.GetProperty("lighting")) switch
                {
                    "off" => Mw3ReLighting.Off,
                    "flat" => Mw3ReLighting.Flat,
                    "normal" => Mw3ReLighting.Normal,
                    _ => throw InvalidProfile()
                },
                Assets = Array.Empty<string>()
            };
        }
        catch (JsonException)
        {
            // Parser diagnostics can contain packaged text; keep them out of outward errors.
            throw InvalidProfile();
        }
    }

    private static void RequireFields(JsonElement value, params string[] fields)
    {
        if (value.ValueKind != JsonValueKind.Object ||
            value.EnumerateObject().Count() != fields.Length ||
            fields.Any(field => !value.TryGetProperty(field, out _)))
            throw InvalidProfile();
    }

    private static int Integer(JsonElement value) =>
        value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out var number)
            ? number : throw InvalidProfile();

    private static string Text(JsonElement value) =>
        value.ValueKind == JsonValueKind.String ? value.GetString()! : throw InvalidProfile();

    private static InvalidDataException InvalidProfile() => new("Invalid native planning profile.");
}
