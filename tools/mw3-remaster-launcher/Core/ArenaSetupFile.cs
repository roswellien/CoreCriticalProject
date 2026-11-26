using System.IO;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// Strict reader and writer for the launcher's <c>*.ccarena.json</c> setup files.
/// Rejects unknown keys, duplicate keys, wrong types, and out-of-range values with
/// an <see cref="ArenaSetupException"/> naming the exact JSON field path.
/// </summary>
public static class ArenaSetupFile
{
    private static readonly HashSet<string> AllowedRootKeys = new(StringComparer.Ordinal)
    {
        "format", "version", "arena", "seed", "random_seed", "frame_ms", "hidden", "time_of_day"
    };

    private static readonly string[] RequiredRootKeys =
    {
        "format", "version", "arena", "seed", "random_seed", "frame_ms", "hidden"
    };

    private static readonly HashSet<string> AllowedArenaKeys = new(StringComparer.Ordinal)
    {
        "map", "minutes", "sides"
    };

    private static readonly string[] RequiredArenaKeys =
    {
        "map", "minutes", "sides"
    };

    private static readonly HashSet<string> AllowedBotKeys = new(StringComparer.Ordinal)
    {
        "mech", "loadout", "preset"
    };

    private static readonly string[] RequiredBotKeys =
    {
        "mech", "preset"
    };

    private static readonly HashSet<string> AllowedPresetKeys = new(StringComparer.Ordinal)
    {
        "world", "mission", "record"
    };

    private static readonly string[] RequiredPresetKeys =
    {
        "world", "mission", "record"
    };

    /// <summary>Load and strictly validate a <c>*.ccarena.json</c> file from disk.</summary>
    public static ArenaSetup Load(string filePath)
    {
        if (!File.Exists(filePath))
            throw new FileNotFoundException("Arena setup file was not found.", filePath);
        return Parse(File.ReadAllText(filePath, Encoding.UTF8));
    }

    /// <summary>Save an <see cref="ArenaSetup"/> to disk as indented <c>*.ccarena.json</c>.</summary>
    public static void Save(string filePath, ArenaSetup setup)
    {
        ArgumentNullException.ThrowIfNull(setup);
        var json = ToJson(setup);
        var directory = Path.GetDirectoryName(Path.GetFullPath(filePath));
        if (!string.IsNullOrEmpty(directory))
            Directory.CreateDirectory(directory);
        File.WriteAllText(filePath, json, new UTF8Encoding(false));
    }

    /// <summary>Serialize an <see cref="ArenaSetup"/> to the launcher's wrapper JSON schema.</summary>
    public static string ToJson(ArenaSetup setup)
    {
        ArgumentNullException.ThrowIfNull(setup);
        setup.Validate();

        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true }))
        {
            writer.WriteStartObject();
            writer.WriteString("format", ArenaSetup.ExpectedFormat);
            writer.WriteNumber("version", ArenaSetup.ExpectedVersion);
            writer.WritePropertyName("arena");
            writer.WriteStartObject();
            writer.WriteString("map", setup.Map);
            writer.WriteNumber("minutes", setup.Minutes);
            writer.WritePropertyName("sides");
            writer.WriteStartArray();
            foreach (var side in setup.Sides)
            {
                writer.WriteStartArray();
                foreach (var bot in side)
                {
                    writer.WriteStartObject();
                    writer.WriteString("mech", bot.Mech);
                    writer.WriteNumber("loadout", bot.Loadout);
                    writer.WritePropertyName("preset");
                    writer.WriteStartObject();
                    writer.WriteString("world", bot.Preset.World);
                    writer.WriteString("mission", bot.Preset.Mission);
                    writer.WriteString("record", bot.Preset.Record);
                    writer.WriteEndObject();
                    writer.WriteEndObject();
                }
                writer.WriteEndArray();
            }
            writer.WriteEndArray();
            writer.WriteEndObject();
            writer.WriteNumber("seed", setup.Seed);
            writer.WriteBoolean("random_seed", setup.RandomSeed);
            writer.WriteNumber("frame_ms", setup.FrameMs);
            writer.WriteBoolean("hidden", setup.Hidden);
            if (setup.TimeOfDay == null)
                writer.WriteNull("time_of_day");
            else
                writer.WriteString("time_of_day", setup.TimeOfDay);
            writer.WriteEndObject();
        }
        return Encoding.UTF8.GetString(stream.ToArray());
    }

    /// <summary>Strictly parse a <c>*.ccarena.json</c> string into an <see cref="ArenaSetup"/>.</summary>
    public static ArenaSetup Parse(string jsonText)
    {
        if (string.IsNullOrWhiteSpace(jsonText))
            throw new ArenaSetupException("setup", "JSON text is empty");

        JsonDocument document;
        try
        {
            document = JsonDocument.Parse(jsonText, new JsonDocumentOptions { MaxDepth = 32 });
        }
        catch (JsonException error)
        {
            throw new ArenaSetupException("setup", "invalid JSON: " + error.Message);
        }

        using (document)
        {
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
                throw new ArenaSetupException("setup", "must be a JSON object");

            ValidateObjectProperties(root, "", AllowedRootKeys, RequiredRootKeys);

            var formatElement = root.GetProperty("format");
            if (formatElement.ValueKind != JsonValueKind.String ||
                !string.Equals(formatElement.GetString(), ArenaSetup.ExpectedFormat, StringComparison.Ordinal))
            {
                throw new ArenaSetupException("format", $"must be \"{ArenaSetup.ExpectedFormat}\"");
            }

            var version = ReadExactInt32(root.GetProperty("version"), "version");
            if (version != ArenaSetup.ExpectedVersion)
                throw new ArenaSetupException("version", $"unsupported version {version} (expected {ArenaSetup.ExpectedVersion})");

            var arenaElement = root.GetProperty("arena");
            if (arenaElement.ValueKind != JsonValueKind.Object)
                throw new ArenaSetupException("arena", "must be a JSON object");

            ValidateObjectProperties(arenaElement, "arena", AllowedArenaKeys, RequiredArenaKeys);

            var map = ReadNonEmptyString(arenaElement.GetProperty("map"), "arena.map");
            var minutes = ReadExactInt32(arenaElement.GetProperty("minutes"), "arena.minutes");
            if (minutes < ArenaSetup.MinMinutes || minutes > ArenaSetup.MaxMinutes)
                throw new ArenaSetupException("arena.minutes", $"must be between {ArenaSetup.MinMinutes} and {ArenaSetup.MaxMinutes}");

            var sidesElement = arenaElement.GetProperty("sides");
            if (sidesElement.ValueKind != JsonValueKind.Array || sidesElement.GetArrayLength() != ArenaSetup.RequiredSideCount)
                throw new ArenaSetupException("arena.sides", "must be an array of 2 sides");

            var sides = new List<List<ArenaBotSetup>>(ArenaSetup.RequiredSideCount);
            var sideIndex = 0;
            foreach (var sideElement in sidesElement.EnumerateArray())
            {
                var sidePath = $"arena.sides[{sideIndex}]";
                if (sideElement.ValueKind != JsonValueKind.Array)
                    throw new ArenaSetupException(sidePath, "must be an array of bots");
                var botCount = sideElement.GetArrayLength();
                if (botCount < ArenaSetup.MinBotsPerSide || botCount > ArenaSetup.MaxBotsPerSide)
                    throw new ArenaSetupException(sidePath, $"must contain {ArenaSetup.MinBotsPerSide} to {ArenaSetup.MaxBotsPerSide} bots");

                var bots = new List<ArenaBotSetup>(botCount);
                var botIndex = 0;
                foreach (var botElement in sideElement.EnumerateArray())
                {
                    var botPath = $"{sidePath}[{botIndex}]";
                    bots.Add(ParseBot(botElement, botPath));
                    botIndex++;
                }
                sides.Add(bots);
                sideIndex++;
            }

            var seed = ReadSeed(root.GetProperty("seed"), "seed");
            var randomSeed = ReadBoolean(root.GetProperty("random_seed"), "random_seed");
            var frameMs = ReadExactInt32(root.GetProperty("frame_ms"), "frame_ms");
            if (frameMs != ArenaSetup.FixedFrameMs)
                throw new ArenaSetupException("frame_ms", $"must be {ArenaSetup.FixedFrameMs}");
            var hidden = ReadBoolean(root.GetProperty("hidden"), "hidden");

            string? timeOfDay = null;
            if (root.TryGetProperty("time_of_day", out var timeElement) && timeElement.ValueKind != JsonValueKind.Null)
            {
                timeOfDay = ReadNonEmptyString(timeElement, "time_of_day");
            }

            var setup = new ArenaSetup
            {
                Map = map,
                Minutes = minutes,
                Sides = sides,
                Seed = seed,
                RandomSeed = randomSeed,
                FrameMs = frameMs,
                Hidden = hidden,
                TimeOfDay = timeOfDay
            };
            setup.Validate();
            return setup;
        }
    }

    private static ArenaBotSetup ParseBot(JsonElement botElement, string botPath)
    {
        if (botElement.ValueKind != JsonValueKind.Object)
            throw new ArenaSetupException(botPath, "must be a JSON object");

        ValidateObjectProperties(botElement, botPath, AllowedBotKeys, RequiredBotKeys);

        var mech = ReadNonEmptyString(botElement.GetProperty("mech"), $"{botPath}.mech");
        var loadout = 0;
        if (botElement.TryGetProperty("loadout", out var loadoutElement))
        {
            loadout = ReadExactInt32(loadoutElement, $"{botPath}.loadout");
            if (loadout < ArenaSetup.MinLoadoutIndex || loadout > ArenaSetup.MaxLoadoutIndex)
            {
                throw new ArenaSetupException(
                    $"{botPath}.loadout",
                    $"must be between {ArenaSetup.MinLoadoutIndex} and {ArenaSetup.MaxLoadoutIndex}");
            }
        }

        var presetPath = $"{botPath}.preset";
        var presetElement = botElement.GetProperty("preset");
        if (presetElement.ValueKind != JsonValueKind.Object)
            throw new ArenaSetupException(presetPath, "must be a JSON object");

        ValidateObjectProperties(presetElement, presetPath, AllowedPresetKeys, RequiredPresetKeys);

        var world = ReadNonEmptyString(presetElement.GetProperty("world"), $"{presetPath}.world");
        var mission = ReadNonEmptyString(presetElement.GetProperty("mission"), $"{presetPath}.mission");
        var record = ReadNonEmptyString(presetElement.GetProperty("record"), $"{presetPath}.record");

        return new ArenaBotSetup(mech, loadout, new ArenaPresetRef(world, mission, record));
    }

    private static void ValidateObjectProperties(
        JsonElement element,
        string objectPath,
        HashSet<string> allowedKeys,
        string[] requiredKeys)
    {
        var seenKeys = new HashSet<string>(StringComparer.Ordinal);
        foreach (var property in element.EnumerateObject())
        {
            var fieldPath = string.IsNullOrEmpty(objectPath) ? property.Name : $"{objectPath}.{property.Name}";
            if (!allowedKeys.Contains(property.Name))
                throw new ArenaSetupException(fieldPath, $"unknown field \"{property.Name}\"");
            if (!seenKeys.Add(property.Name))
                throw new ArenaSetupException(fieldPath, $"duplicate field \"{property.Name}\"");
        }

        foreach (var required in requiredKeys)
        {
            if (!seenKeys.Contains(required))
            {
                var fieldPath = string.IsNullOrEmpty(objectPath) ? required : $"{objectPath}.{required}";
                throw new ArenaSetupException(fieldPath, $"missing required field \"{required}\"");
            }
        }
    }

    private static string ReadNonEmptyString(JsonElement element, string fieldPath)
    {
        if (element.ValueKind != JsonValueKind.String)
            throw new ArenaSetupException(fieldPath, "must be a string");
        var value = element.GetString();
        if (string.IsNullOrWhiteSpace(value))
            throw new ArenaSetupException(fieldPath, "must not be empty");
        return value;
    }

    private static bool ReadBoolean(JsonElement element, string fieldPath)
    {
        return element.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            _ => throw new ArenaSetupException(fieldPath, "must be a boolean")
        };
    }

    private static int ReadExactInt32(JsonElement element, string fieldPath)
    {
        if (element.ValueKind != JsonValueKind.Number)
            throw new ArenaSetupException(fieldPath, "must be a whole number");
        var raw = element.GetRawText();
        if (raw.Contains('.') || raw.Contains('e') || raw.Contains('E'))
            throw new ArenaSetupException(fieldPath, "must be a whole number");
        if (!element.TryGetInt64(out var value) || value < int.MinValue || value > int.MaxValue)
            throw new ArenaSetupException(fieldPath, "is out of integer range");
        return (int)value;
    }

    private static int ReadSeed(JsonElement element, string fieldPath)
    {
        if (element.ValueKind != JsonValueKind.Number)
            throw new ArenaSetupException(fieldPath, "must be a whole number between 0 and 2147483647");
        var raw = element.GetRawText();
        if (raw.Contains('.') || raw.Contains('e') || raw.Contains('E'))
            throw new ArenaSetupException(fieldPath, "must be a whole number between 0 and 2147483647");
        if (!element.TryGetInt64(out var value) || value < ArenaSetup.MinSeed || value > ArenaSetup.MaxSeed)
            throw new ArenaSetupException(fieldPath, "must be between 0 and 2147483647");
        return (int)value;
    }
}
