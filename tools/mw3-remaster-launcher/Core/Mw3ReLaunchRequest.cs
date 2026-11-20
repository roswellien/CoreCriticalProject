using System.IO;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

public enum Mw3ReRenderer { VulkanWsi }
public enum Mw3ReAntialiasing { Off, One, Fxaa, Two, Four, Eight }
public enum Mw3ReWindowMode { Windowed, Fullscreen, Borderless }
public enum Mw3ReLighting { Off, Flat, Normal }
public enum Mw3ReFlareStyle { Modern, Original }

/// <summary>Explicit native planning inputs, not a conversion of saved launcher settings.</summary>
public sealed record Mw3RePlanningOptions
{
    public Mw3ReRenderer Renderer { get; init; } = Mw3ReRenderer.VulkanWsi;
    public int Width { get; init; } = 1280;
    public int Height { get; init; } = 720;
    public Mw3ReAntialiasing Antialiasing { get; init; } = Mw3ReAntialiasing.Fxaa;
    public int AnisotropicFiltering { get; init; } = 16;
    public Mw3ReWindowMode WindowMode { get; init; } = Mw3ReWindowMode.Windowed;
    public bool RenderThread { get; init; } = true;
    public Mw3ReLighting Lighting { get; init; } = Mw3ReLighting.Off;
    public Mw3ReFlareStyle FlareStyle { get; init; } = Mw3ReFlareStyle.Modern;
    public bool Pom { get; init; } = false;
    public string? PomQuality { get; init; } = null;
    public IReadOnlyList<string> Assets { get; init; } = Array.Empty<string>();
    /// <summary>Native preview choices; when set, the request uses wire schema 4.</summary>
    public Mw3RePreviewOptions? Preview { get; init; }
}

/// <summary>
/// Player choices for the labelled Native preview launch (wire schema 4). The Python planner
/// reads the pack folders and turns them into game arguments; C# only passes typed values.
/// </summary>
public sealed record Mw3RePreviewOptions
{
    /// <summary>
    /// Scenery/view distance: 800 is original; 1200, 1600, 2400 and 3200 extend it.
    /// </summary>
    public int DrawDistance { get; init; } = 800;
    public string? Hud { get; init; } = "core-critical";
    public bool? HudText { get; init; } = true;
    public string Geometry { get; init; } = "partial";
    public IReadOnlyList<string> ModelPacks { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> SkinPacks { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> EnvironmentPacks { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> UiPacks { get; init; } = Array.Empty<string>();
    public bool DynamicLighting { get; init; }
    public bool Shadows { get; init; }
    public bool Headlights { get; init; }
    public bool WaterDetail { get; init; } = true;
    public bool CloudDetail { get; init; } = true;
    public string? HeadlightBindings { get; init; }
    public string? StockEffectCatalog { get; init; }
    public string? StockHeadlightCatalog { get; init; }
}

/// <summary>Project an integrity snapshot into wire data; only Python translates it into argv.</summary>
public static class Mw3ReLaunchRequest
{
    public static string Create(Mw3ReRuntimeContract contract, Mw3RePlanningOptions options,
        string gameDirectory, string dataRoot, string profileId, string? indeoCodec = null)
    {
        ArgumentNullException.ThrowIfNull(contract);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(gameDirectory);
        ArgumentNullException.ThrowIfNull(dataRoot);
        ArgumentNullException.ThrowIfNull(options.Assets);
        var id = PackStorage.ValidateId(profileId);
        var renderer = options.Renderer switch
        {
            Mw3ReRenderer.VulkanWsi => "vulkan-wsi",
            _ => throw new InvalidDataException("Unknown native renderer.")
        };
        var antialiasing = options.Antialiasing switch
        {
            Mw3ReAntialiasing.Off => "off", Mw3ReAntialiasing.One => "1",
            Mw3ReAntialiasing.Fxaa => "fxaa", Mw3ReAntialiasing.Two => "2",
            Mw3ReAntialiasing.Four => "4", Mw3ReAntialiasing.Eight => "8",
            _ => throw new InvalidDataException("Unknown native antialiasing.")
        };
        var windowMode = options.WindowMode switch
        {
            Mw3ReWindowMode.Windowed => "windowed", Mw3ReWindowMode.Fullscreen => "fullscreen",
            Mw3ReWindowMode.Borderless => "borderless",
            _ => throw new InvalidDataException("Unknown native window mode.")
        };
        var lighting = options.Lighting switch
        {
            Mw3ReLighting.Off => "off", Mw3ReLighting.Flat => "flat", Mw3ReLighting.Normal => "normal",
            _ => throw new InvalidDataException("Unknown native lighting.")
        };
        var flareStyle = options.FlareStyle switch
        {
            Mw3ReFlareStyle.Modern => "modern",
            Mw3ReFlareStyle.Original => "original",
            _ => throw new InvalidDataException("Unknown native flare style.")
        };
        // The preview ships its planner with the launcher, so it has no pinned planner roles to check;
        // the planner still refuses POM without normal lighting.
        if (options.Preview != null)
            return CreatePreview(contract, options, gameDirectory, dataRoot, id, renderer, antialiasing,
                windowMode, lighting, flareStyle, indeoCodec);
        // This pinned combined runtime/planner claim is observational, not trusted execution admission.
        if (options.Pom && (options.Lighting != Mw3ReLighting.Normal ||
            !contract.Capabilities.TryGetValue("pom", out var versions) || !versions.Contains(1) ||
            !contract.Roles.ContainsKey("coordinator") || !contract.Roles.ContainsKey("python")))
            throw new InvalidDataException("Native POM planning requires normal lighting and compatible pinned runtime/planner roles.");
        // Do not create directories or repair input paths; the sole planner validates their lexical contract.
        var request = new JsonObject
        {
            ["schema_version"] = options.Pom ? 3 : 2, ["engine"] = "mw3-re", ["runtime_root"] = contract.Root,
            ["executable"] = contract.Executable, ["game_dir"] = gameDirectory,
            ["indeo_codec"] = indeoCodec,
            ["write_dir"] = Path.Combine(dataRoot, "mw3-re", "profiles", id), ["renderer"] = renderer,
            ["width"] = options.Width, ["height"] = options.Height, ["aa"] = antialiasing,
            ["af"] = options.AnisotropicFiltering, ["window_mode"] = windowMode,
            ["render_thread"] = options.RenderThread, ["lighting"] = lighting,
            ["flare_style"] = flareStyle,
            ["assets"] = new JsonArray(options.Assets.Select(asset => (JsonNode?)JsonValue.Create(asset)).ToArray())
        };
        var visuals = BuildVisuals(options);
        if (visuals != null) request["visuals"] = visuals;
        return GameRunner.SerializeLaunchProfile(request);
    }

    private static string CreatePreview(Mw3ReRuntimeContract contract, Mw3RePlanningOptions options,
        string gameDirectory, string dataRoot, string id, string renderer, string antialiasing,
        string windowMode, string lighting, string flareStyle, string? indeoCodec)
    {
        var preview = options.Preview!;
        ArgumentNullException.ThrowIfNull(preview.ModelPacks);
        ArgumentNullException.ThrowIfNull(preview.EnvironmentPacks);
        ArgumentNullException.ThrowIfNull(preview.UiPacks);
        ArgumentNullException.ThrowIfNull(preview.SkinPacks);
        var request = new JsonObject
        {
            ["schema_version"] = 4, ["engine"] = "mw3-re", ["runtime_root"] = contract.Root,
            ["executable"] = contract.Executable, ["game_dir"] = gameDirectory,
            ["indeo_codec"] = indeoCodec,
            ["write_dir"] = Path.Combine(dataRoot, "mw3-re", "profiles", id), ["renderer"] = renderer,
            ["width"] = options.Width, ["height"] = options.Height, ["aa"] = antialiasing,
            ["af"] = options.AnisotropicFiltering, ["window_mode"] = windowMode,
            ["render_thread"] = options.RenderThread, ["lighting"] = lighting,
            ["flare_style"] = flareStyle,
            ["assets"] = new JsonArray(options.Assets.Select(asset => (JsonNode?)JsonValue.Create(asset)).ToArray()),
            ["preview"] = new JsonObject
            {
                ["draw_distance"] = preview.DrawDistance, ["hud"] = preview.Hud,
                ["hud_text"] = preview.HudText, ["geometry"] = preview.Geometry,
                ["model_packs"] = Paths(preview.ModelPacks),
                ["skin_packs"] = Paths(preview.SkinPacks),
                ["environment_packs"] = Paths(preview.EnvironmentPacks),
                ["ui_packs"] = Paths(preview.UiPacks),
                ["dynamic_lighting"] = preview.DynamicLighting,
                ["shadows"] = preview.Shadows,
                ["headlights"] = preview.Headlights,
                ["water_detail"] = preview.WaterDetail,
                ["cloud_detail"] = preview.CloudDetail,
                ["headlight_bindings"] = preview.HeadlightBindings,
                ["stock_effect_catalog"] = preview.StockEffectCatalog,
                ["stock_headlight_catalog"] = preview.StockHeadlightCatalog
            }
        };
        var visuals = BuildVisuals(options);
        if (visuals != null) request["visuals"] = visuals;
        return GameRunner.SerializeLaunchProfile(request);
    }

    private static JsonObject? BuildVisuals(Mw3RePlanningOptions options)
    {
        if (options.PomQuality is not null)
        {
            if (options.PomQuality is not ("off" or "low" or "high"))
                throw new InvalidDataException("Unknown native POM quality.");
            if (options.PomQuality == "off")
                return null;
            return new JsonObject { ["pom"] = true, ["pom_quality"] = options.PomQuality };
        }
        return options.Pom ? new JsonObject { ["pom"] = true } : null;
    }

    private static JsonArray Paths(IEnumerable<string> paths) =>
        new(paths.Select(path => (JsonNode?)JsonValue.Create(path)).ToArray());
}
