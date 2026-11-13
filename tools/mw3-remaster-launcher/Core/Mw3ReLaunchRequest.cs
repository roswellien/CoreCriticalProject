using System.IO;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

public enum Mw3ReRenderer { VulkanWsi }
public enum Mw3ReAntialiasing { Off, One, Fxaa, Two, Four, Eight }
public enum Mw3ReWindowMode { Windowed, Fullscreen, Borderless }
public enum Mw3ReLighting { Off, Flat, Normal }

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
    public IReadOnlyList<string> Assets { get; init; } = Array.Empty<string>();
}

/// <summary>Project an integrity snapshot into wire data; only Python translates it into argv.</summary>
public static class Mw3ReLaunchRequest
{
    public static string Create(Mw3ReRuntimeContract contract, Mw3RePlanningOptions options,
        string gameDirectory, string dataRoot, string profileId)
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
        // Do not create directories or repair input paths; the sole planner validates their lexical contract.
        var request = new JsonObject
        {
            ["schema_version"] = 2, ["engine"] = "mw3-re", ["runtime_root"] = contract.Root,
            ["executable"] = contract.Executable, ["game_dir"] = gameDirectory,
            ["write_dir"] = Path.Combine(dataRoot, "mw3-re", "profiles", id), ["renderer"] = renderer,
            ["width"] = options.Width, ["height"] = options.Height, ["aa"] = antialiasing,
            ["af"] = options.AnisotropicFiltering, ["window_mode"] = windowMode,
            ["render_thread"] = options.RenderThread, ["lighting"] = lighting,
            ["assets"] = new JsonArray(options.Assets.Select(asset => (JsonNode?)JsonValue.Create(asset)).ToArray())
        };
        return GameRunner.SerializeLaunchProfile(request);
    }
}
