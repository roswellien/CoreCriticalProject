using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// Thrown when a saved <c>*.ccarena.json</c> file or an in-memory <see cref="ArenaSetup"/>
/// violates schema, range, or catalog constraints. Includes the exact field path.
/// </summary>
public sealed class ArenaSetupException : Exception
{
    public string FieldPath { get; }

    public ArenaSetupException(string fieldPath, string description)
        : base($"{fieldPath}: {description}")
    {
        FieldPath = fieldPath;
    }
}

/// <summary>Identifies an AI record in the game's mission files (<c>world</c>, <c>mission</c>, <c>record</c>).</summary>
public sealed record ArenaPresetRef(string World, string Mission, string Record);

/// <summary>A single bot on Side A or Side B: chassis ID, stock loadout index, and AI pilot preset.</summary>
public sealed record ArenaBotSetup(string Mech, int Loadout, ArenaPresetRef Preset);

/// <summary>
/// The launcher's AI Arena match configuration. Validates both structural bounds and
/// catalog membership, and projects the runtime <c>setup.json</c> consumed by <c>mw3 --arena</c>.
/// </summary>
public sealed class ArenaSetup
{
    public const string ExpectedFormat = "core-critical-arena-setup";
    public const int ExpectedVersion = 1;
    public const int RequiredSideCount = 2;
    public const int MinBotsPerSide = 1;
    public const int MaxBotsPerSide = 8;
    public const int MinMinutes = 1;
    public const int MaxMinutes = 600;
    public const int MinLoadoutIndex = 0;
    public const int MaxLoadoutIndex = 15;
    public const int MinSeed = 0;
    public const int MaxSeed = int.MaxValue;
    public const int FixedFrameMs = 33;

    public string Map { get; set; } = "c1mp1";
    public int Minutes { get; set; } = 5;
    public List<List<ArenaBotSetup>> Sides { get; set; } = new() { new(), new() };
    public int Seed { get; set; } = 1234567;
    public bool RandomSeed { get; set; }
    public int FrameMs { get; set; } = FixedFrameMs;
    public bool Hidden { get; set; }
    public string? TimeOfDay { get; set; }

    /// <summary>Create a deep copy so UI edits during a match cannot mutate the running setup.</summary>
    public ArenaSetup Clone()
    {
        return new ArenaSetup
        {
            Map = Map,
            Minutes = Minutes,
            Sides = Sides.Select(side => side.Select(bot => new ArenaBotSetup(
                bot.Mech,
                bot.Loadout,
                new ArenaPresetRef(bot.Preset.World, bot.Preset.Mission, bot.Preset.Record))).ToList()).ToList(),
            Seed = Seed,
            RandomSeed = RandomSeed,
            FrameMs = FrameMs,
            Hidden = Hidden,
            TimeOfDay = TimeOfDay
        };
    }

    /// <summary>
    /// Pick the seed for one match run. When <see cref="RandomSeed"/> is true, draw a fresh
    /// seed across <c>0..2147483647</c> inclusive without mutating <see cref="Seed"/> or <see cref="RandomSeed"/>.
    /// </summary>
    public int ResolveSeedForRun()
    {
        if (!RandomSeed)
        {
            if (Seed < MinSeed)
                throw new ArenaSetupException("seed", "must be between 0 and 2147483647");
            return Seed;
        }

        // RandomNumberGenerator.GetInt32 has an exclusive int upper bound and cannot reach
        // int.MaxValue, so draw 4 cryptographic bytes and mask off the sign bit to cover
        // the full 0..2147483647 inclusive range that mw3 --seed accepts.
        Span<byte> bytes = stackalloc byte[sizeof(int)];
        RandomNumberGenerator.Fill(bytes);
        return BitConverter.ToInt32(bytes) & MaxSeed;
    }

    /// <summary>Validate all structural, type, and numeric range invariants on this instance.</summary>
    public void Validate()
    {
        if (string.IsNullOrWhiteSpace(Map))
            throw new ArenaSetupException("arena.map", "must be a non-empty map id");
        if (Minutes < MinMinutes || Minutes > MaxMinutes)
            throw new ArenaSetupException("arena.minutes", $"must be between {MinMinutes} and {MaxMinutes}");
        if (Sides == null || Sides.Count != RequiredSideCount)
            throw new ArenaSetupException("arena.sides", "must contain exactly 2 sides");

        for (var sideIndex = 0; sideIndex < RequiredSideCount; sideIndex++)
        {
            var side = Sides[sideIndex];
            var sidePath = $"arena.sides[{sideIndex}]";
            if (side == null || side.Count < MinBotsPerSide || side.Count > MaxBotsPerSide)
                throw new ArenaSetupException(sidePath, $"must contain {MinBotsPerSide} to {MaxBotsPerSide} bots");

            for (var botIndex = 0; botIndex < side.Count; botIndex++)
            {
                var bot = side[botIndex];
                var botPath = $"{sidePath}[{botIndex}]";
                if (bot == null)
                    throw new ArenaSetupException(botPath, "must be a bot object");
                if (string.IsNullOrWhiteSpace(bot.Mech))
                    throw new ArenaSetupException($"{botPath}.mech", "must be a non-empty mech id");
                if (bot.Loadout < MinLoadoutIndex || bot.Loadout > MaxLoadoutIndex)
                    throw new ArenaSetupException($"{botPath}.loadout", $"must be between {MinLoadoutIndex} and {MaxLoadoutIndex}");
                if (bot.Preset == null)
                    throw new ArenaSetupException($"{botPath}.preset", "must be a preset object");
                if (string.IsNullOrWhiteSpace(bot.Preset.World))
                    throw new ArenaSetupException($"{botPath}.preset.world", "must be a non-empty world id");
                if (string.IsNullOrWhiteSpace(bot.Preset.Mission))
                    throw new ArenaSetupException($"{botPath}.preset.mission", "must be a non-empty mission reader id");
                if (string.IsNullOrWhiteSpace(bot.Preset.Record))
                    throw new ArenaSetupException($"{botPath}.preset.record", "must be a non-empty AI record name");
            }
        }

        if (Seed < MinSeed)
            throw new ArenaSetupException("seed", $"must be between {MinSeed} and {MaxSeed}");
        if (FrameMs != FixedFrameMs)
            throw new ArenaSetupException("frame_ms", $"must be {FixedFrameMs}");
        if (TimeOfDay != null && string.IsNullOrWhiteSpace(TimeOfDay))
            throw new ArenaSetupException("time_of_day", "must be null or a non-empty time-of-day option");
    }

    /// <summary>
    /// Validate this setup against the game build's <see cref="ArenaCatalog"/>. Throws
    /// <see cref="ArenaSetupException"/> naming the exact offending field path.
    /// </summary>
    public void ValidateAgainst(ArenaCatalog catalog)
    {
        ArgumentNullException.ThrowIfNull(catalog);

        // #507: send time_of_day to the runtime and relax this guard once it supports it.
        if (TimeOfDay != null)
        {
            throw new ArenaSetupException("time_of_day", "this game runtime cannot set time of day yet");
        }

        Validate();

        var knownMaps = new HashSet<string>(catalog.Maps.Select(map => map.Id), StringComparer.Ordinal);
        if (!knownMaps.Contains(Map))
            throw new ArenaSetupException("arena.map", $"unknown map \"{Map}\"");

        var mechsById = catalog.Mechs.ToDictionary(mech => mech.Id, StringComparer.Ordinal);
        var knownPresets = new HashSet<(string World, string Mission, string Record)>(
            catalog.Presets.Select(preset => (preset.World, preset.Mission, preset.Record)));

        for (var sideIndex = 0; sideIndex < Sides.Count; sideIndex++)
        {
            var side = Sides[sideIndex];
            for (var botIndex = 0; botIndex < side.Count; botIndex++)
            {
                var bot = side[botIndex];
                var botPath = $"arena.sides[{sideIndex}][{botIndex}]";
                if (!mechsById.TryGetValue(bot.Mech, out var catalogMech))
                    throw new ArenaSetupException($"{botPath}.mech", $"unknown mech \"{bot.Mech}\"");

                if (!catalogMech.Loadouts.Any(loadout => loadout.Index == bot.Loadout))
                {
                    throw new ArenaSetupException(
                        $"{botPath}.loadout",
                        $"{bot.Loadout} is not a stock loadout of {bot.Mech}");
                }

                var presetKey = (bot.Preset.World, bot.Preset.Mission, bot.Preset.Record);
                if (!knownPresets.Contains(presetKey))
                {
                    throw new ArenaSetupException(
                        $"{botPath}.preset",
                        $"unknown pilot preset \"{bot.Preset.World} {bot.Preset.Mission} {bot.Preset.Record}\"");
                }
            }
        }
    }

    /// <summary>
    /// Serialize only the runtime setup fields that <c>mw3 --arena</c> accepts:
    /// <c>map</c>, <c>minutes</c>, <c>out</c>, and <c>sides</c> (with explicit <c>loadout</c>).
    /// Launcher-only fields (<c>seed</c>, <c>random_seed</c>, <c>frame_ms</c>, <c>hidden</c>, <c>time_of_day</c>)
    /// are never emitted into the runtime file.
    /// </summary>
    public string ToRuntimeSetupJson(string outFolder)
    {
        if (string.IsNullOrWhiteSpace(outFolder))
            throw new ArgumentException("The match log output folder is required.", nameof(outFolder));
        Validate();

        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true }))
        {
            writer.WriteStartObject();
            writer.WriteString("map", Map);
            writer.WriteNumber("minutes", Minutes);
            writer.WriteString("out", outFolder);
            writer.WritePropertyName("sides");
            writer.WriteStartArray();
            foreach (var side in Sides)
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
        }
        return Encoding.UTF8.GetString(stream.ToArray());
    }
}
