using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Threading;
using MW3RemasterLauncher.Core;

internal static class ArenaSetupChecks
{
    private const string SampleCatalogJson = """
        {
          "version": 1,
          "maps": [
            { "id": "c1mp1", "name": "Canyon" },
            { "id": "c2mp2", "name": "Desert" }
          ],
          "mechs": [
            {
              "id": "madcat",
              "name": "Mad Cat",
              "tons": 75,
              "loadouts": [
                { "index": 0, "name": "Primary", "armor": 240 }
              ]
            },
            {
              "id": "thor",
              "name": "Thor",
              "tons": 70,
              "loadouts": [
                { "index": 0, "name": "Primary", "armor": 208 },
                { "index": 1, "name": "Alternate A", "armor": 208 }
              ]
            }
          ],
          "presets": [
            {
              "world": "c1",
              "mission": "ia1",
              "record": "Enemy_01",
              "mech": "madcat",
              "numbers": { "attack_m": 600 }
            },
            {
              "world": "c2",
              "mission": "m1",
              "record": "Boss_02",
              "mech": "thor",
              "numbers": { "attack_m": 800 }
            }
          ]
        }
        """;

    private const string SampleValidSetupJson = """
        {
          "format": "core-critical-arena-setup",
          "version": 1,
          "arena": {
            "map": "c1mp1",
            "minutes": 5,
            "sides": [
              [
                {
                  "mech": "madcat",
                  "loadout": 0,
                  "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" }
                }
              ],
              [
                {
                  "mech": "thor",
                  "loadout": 1,
                  "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" }
                }
              ]
            ]
          },
          "seed": 1234567,
          "random_seed": false,
          "frame_ms": 33,
          "hidden": false,
          "time_of_day": null
        }
        """;

    public static void Run()
    {
        var tempRoot = Path.Combine(Path.GetTempPath(), "MW3ArenaChecks-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempRoot);
        try
        {
            CheckCatalogParsing(tempRoot);
            var catalog = ArenaCatalog.ParseJson(SampleCatalogJson);
            CheckRuntimeJsonAndRoundTrip(tempRoot, catalog);
            CheckOptionalLoadoutAndTimeOfDay(catalog);
            CheckSparseLoadoutIndices();
            CheckRejectionFieldPaths(catalog);
            CheckRandomSeedAndDirectoryPrep(tempRoot);
            CheckArgumentsAndGraphicsSummary(tempRoot);
            CheckOutcomeParsingAndExitHandling(tempRoot);
            CheckRuntimeLogTimestampAndStdoutResult(tempRoot);
            CheckCatalogProcessWaitHelper();
            Console.WriteLine("AI Arena catalog, setup schema, field-path validation, argument builder and result parser checks passed.");
        }
        finally
        {
            if (Directory.Exists(tempRoot))
                Directory.Delete(tempRoot, recursive: true);
        }
    }

    private static void Check(bool condition, string message)
    {
        if (!condition)
            throw new Exception(message);
    }

    private static void ExpectFieldFailure(Action action, string expectedFieldPath, string? expectedSubstring = null)
    {
        try
        {
            action();
        }
        catch (ArenaSetupException error)
        {
            Check(
                string.Equals(error.FieldPath, expectedFieldPath, StringComparison.Ordinal) &&
                error.Message.StartsWith(expectedFieldPath + ":", StringComparison.Ordinal),
                $"Expected field path '{expectedFieldPath}' but got '{error.FieldPath}' ({error.Message}).");
            if (expectedSubstring != null)
            {
                Check(
                    error.Message.Contains(expectedSubstring, StringComparison.OrdinalIgnoreCase),
                    $"Expected '{expectedSubstring}' in error message '{error.Message}'.");
            }
            return;
        }
        throw new Exception($"Expected ArenaSetupException on field '{expectedFieldPath}', but no ArenaSetupException was thrown.");
    }

    private static void CheckCatalogParsing(string tempRoot)
    {
        var catalogFile = Path.Combine(tempRoot, "catalog.json");
        File.WriteAllText(catalogFile, SampleCatalogJson);
        var catalog = ArenaCatalog.LoadFromFile(catalogFile);
        Check(catalog.Maps.Count == 2 && catalog.Maps[0].Id == "c1mp1" && catalog.Maps[0].Name == "Canyon",
            "Catalog maps did not parse as expected.");
        Check(catalog.Mechs.Count == 2 && catalog.FindMech("thor")!.Loadouts.Count == 2,
            "Catalog mechs and loadouts did not parse as expected.");
        Check(catalog.Presets.Count == 2 && catalog.Presets[0].DisplayLabel == "c1 ia1 Enemy_01",
            "Catalog presets did not parse as expected.");
        Check(catalog.TimeOfDayOptions.Count == 0,
            "Catalog without times_of_day should have an empty TimeOfDayOptions list.");

        var withTimesJson = SampleCatalogJson[..SampleCatalogJson.LastIndexOf('}')] +
            ", \"times_of_day\": [\"day\", \"night\"]}";
        var withTimes = ArenaCatalog.ParseJson(withTimesJson);
        Check(withTimes.TimeOfDayOptions.SequenceEqual(new[] { "day", "night" }),
            "Catalog optional times_of_day array was not preserved.");

        try
        {
            ArenaCatalog.ParseJson(SampleCatalogJson.Replace("\"version\": 1", "\"version\": 2"));
            throw new Exception("Catalog version 2 was accepted.");
        }
        catch (InvalidDataException) { }

        // Reject duplicate map IDs
        try
        {
            var duplicateMapJson = SampleCatalogJson.Replace("\"c2mp2\"", "\"c1mp1\"");
            ArenaCatalog.ParseJson(duplicateMapJson);
            throw new Exception("Catalog with duplicate map ID was accepted.");
        }
        catch (InvalidDataException error)
        {
            Check(error.Message.Contains("c1mp1", StringComparison.OrdinalIgnoreCase) &&
                  error.Message.Contains("twice", StringComparison.OrdinalIgnoreCase),
                "Duplicate map exception did not name map: " + error.Message);
        }

        // Reject duplicate mech IDs
        try
        {
            var duplicateMechJson = SampleCatalogJson.Replace("\"id\": \"madcat\"", "\"id\": \"thor\"");
            ArenaCatalog.ParseJson(duplicateMechJson);
            throw new Exception("Catalog with duplicate mech ID was accepted.");
        }
        catch (InvalidDataException error)
        {
            Check(error.Message.Contains("thor", StringComparison.OrdinalIgnoreCase) &&
                  error.Message.Contains("twice", StringComparison.OrdinalIgnoreCase),
                "Duplicate mech exception did not name mech: " + error.Message);
        }

        // Reject duplicate explicit loadout index within mech
        try
        {
            var duplicateLoadoutJson = SampleCatalogJson.Replace("\"index\": 1", "\"index\": 0");
            ArenaCatalog.ParseJson(duplicateLoadoutJson);
            throw new Exception("Catalog with duplicate explicit loadout index was accepted.");
        }
        catch (InvalidDataException error)
        {
            Check(error.Message.Contains("0") && error.Message.Contains("twice", StringComparison.OrdinalIgnoreCase),
                "Duplicate explicit loadout index exception did not name index: " + error.Message);
        }

        // Reject implicit/explicit loadout index collision
        try
        {
            var collisionLoadoutJson = SampleCatalogJson
                .Replace("\"index\": 0, ", "")
                .Replace("\"index\": 1", "\"index\": 0");
            ArenaCatalog.ParseJson(collisionLoadoutJson);
            throw new Exception("Catalog with implicit/explicit loadout index collision was accepted.");
        }
        catch (InvalidDataException error)
        {
            Check(error.Message.Contains("0") && error.Message.Contains("twice", StringComparison.OrdinalIgnoreCase),
                "Implicit/explicit loadout collision exception did not name index: " + error.Message);
        }
    }

    private static void CheckRuntimeJsonAndRoundTrip(string tempRoot, ArenaCatalog catalog)
    {
        var setup = ArenaSetupFile.Parse(SampleValidSetupJson);
        setup.ValidateAgainst(catalog);

        var savedPath = Path.Combine(tempRoot, "saved.ccarena.json");
        ArenaSetupFile.Save(savedPath, setup);
        var reloaded = ArenaSetupFile.Load(savedPath);
        reloaded.ValidateAgainst(catalog);

        Check(reloaded.Map == "c1mp1" && reloaded.Minutes == 5 && reloaded.Seed == 1234567 &&
            !reloaded.RandomSeed && reloaded.FrameMs == 33 && !reloaded.Hidden && reloaded.TimeOfDay == null,
            "Saved and reloaded setup scalar fields changed.");
        Check(reloaded.Sides.Count == 2 &&
            reloaded.Sides[0][0].Mech == "madcat" && reloaded.Sides[0][0].Loadout == 0 &&
            reloaded.Sides[1][0].Mech == "thor" && reloaded.Sides[1][0].Loadout == 1,
            "Saved and reloaded setup sides changed.");

        using (var wrapperDoc = JsonDocument.Parse(File.ReadAllText(savedPath)))
        {
            var wrapperKeys = wrapperDoc.RootElement.EnumerateObject().Select(p => p.Name).ToArray();
            Check(wrapperKeys.SequenceEqual(new[]
            {
                "format", "version", "arena", "seed", "random_seed", "frame_ms", "hidden", "time_of_day"
            }), "Saved *.ccarena.json root keys did not match the exact schema.");
        }

        var outFolder = Path.Combine(tempRoot, "run-out");
        var runtimeJson = reloaded.ToRuntimeSetupJson(outFolder);
        using var runtimeDoc = JsonDocument.Parse(runtimeJson);
        var root = runtimeDoc.RootElement;
        var rootKeys = root.EnumerateObject().Select(p => p.Name).ToArray();
        Check(rootKeys.SequenceEqual(new[] { "map", "minutes", "out", "sides" }),
            "Runtime setup.json root keys must be exactly map, minutes, out, sides.");
        Check(!root.TryGetProperty("time_of_day", out _) &&
            !root.TryGetProperty("seed", out _) &&
            !root.TryGetProperty("random_seed", out _) &&
            !root.TryGetProperty("frame_ms", out _) &&
            !root.TryGetProperty("hidden", out _),
            "Runtime setup.json leaked launcher-only fields.");
        Check(root.GetProperty("out").GetString() == outFolder,
            "Runtime setup.json out path did not match.");

        foreach (var side in root.GetProperty("sides").EnumerateArray())
        {
            foreach (var bot in side.EnumerateArray())
            {
                var botKeys = bot.EnumerateObject().Select(p => p.Name).ToArray();
                Check(botKeys.SequenceEqual(new[] { "mech", "loadout", "preset" }),
                    "Runtime setup.json bot keys must be exactly mech, loadout, preset.");
                var presetKeys = bot.GetProperty("preset").EnumerateObject().Select(p => p.Name).ToArray();
                Check(presetKeys.SequenceEqual(new[] { "world", "mission", "record" }),
                    "Runtime setup.json preset keys must be exactly world, mission, record.");
            }
        }
    }

    private static void CheckOptionalLoadoutAndTimeOfDay(ArenaCatalog catalogWithoutTime)
    {
        // Omitted bot.loadout defaults to 0 and omitted time_of_day defaults to null.
        const string omittedOptionals = """
            {
              "format": "core-critical-arena-setup",
              "version": 1,
              "arena": {
                "map": "c1mp1",
                "minutes": 10,
                "sides": [
                  [ { "mech": "madcat", "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } } ],
                  [ { "mech": "thor", "preset": { "world": "c2", "mission": "m1", "record": "Boss_02" } } ]
                ]
              },
              "seed": 0,
              "random_seed": true,
              "frame_ms": 33,
              "hidden": true
            }
            """;

        var parsed = ArenaSetupFile.Parse(omittedOptionals);
        parsed.ValidateAgainst(catalogWithoutTime);
        Check(parsed.Sides[0][0].Loadout == 0 && parsed.Sides[1][0].Loadout == 0 && parsed.TimeOfDay == null,
            "Omitted loadout or time_of_day did not default to 0 and null.");

        // And ToRuntimeSetupJson must still emit explicit loadout: 0.
        using var runtimeDoc = JsonDocument.Parse(parsed.ToRuntimeSetupJson("D:/arena-out"));
        Check(runtimeDoc.RootElement.GetProperty("sides")[0][0].GetProperty("loadout").GetInt32() == 0,
            "Runtime setup JSON omitted explicit loadout 0.");

        var catalogWithTime = new ArenaCatalog(
            catalogWithoutTime.Maps,
            catalogWithoutTime.Mechs,
            catalogWithoutTime.Presets,
            new[] { "day", "night" });

        // Reject ANY non-null time_of_day even when listed in catalog
        foreach (var timeOfDay in new[] { "night", "", " " })
        {
            parsed.TimeOfDay = timeOfDay;
            ExpectFieldFailure(
                () => parsed.ValidateAgainst(catalogWithTime),
                "time_of_day",
                "this game runtime cannot set time of day yet");
        }

        parsed.TimeOfDay = "night";
        using var runtimeWithTimeDoc = JsonDocument.Parse(parsed.ToRuntimeSetupJson("D:/arena-out"));
        Check(!runtimeWithTimeDoc.RootElement.TryGetProperty("time_of_day", out _),
            "Runtime setup JSON must never include time_of_day.");
    }

    private static void CheckRejectionFieldPaths(ArenaCatalog catalog)
    {
        // Unknown keys at every level
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"hidden\": false,", "\"hidden\": false, \"extra_top\": 1,")),
            "extra_top");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"minutes\": 5,", "\"minutes\": 5, \"extra_arena\": 1,")),
            "arena.extra_arena");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"loadout\": 0,", "\"loadout\": 0, \"extra_bot\": true,")),
            "arena.sides[0][0].extra_bot");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"record\": \"Enemy_01\"", "\"record\": \"Enemy_01\", \"extra_preset\": \"x\"")),
            "arena.sides[0][0].preset.extra_preset");

        // Duplicate key
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"minutes\": 5,", "\"minutes\": 5, \"minutes\": 5,")),
            "arena.minutes");

        // Wrong format, version, and types
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"core-critical-arena-setup\"", "\"other-format\"")),
            "format");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"version\": 1", "\"version\": 2")),
            "version");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"version\": 1", "\"version\": \"1\"")),
            "version");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"random_seed\": false", "\"random_seed\": 0")),
            "random_seed");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"hidden\": false", "\"hidden\": \"false\"")),
            "hidden");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"frame_ms\": 33", "\"frame_ms\": 16")),
            "frame_ms");

        // Minutes bounds (1..600)
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"minutes\": 5", "\"minutes\": 0")),
            "arena.minutes");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"minutes\": 5", "\"minutes\": 601")),
            "arena.minutes");

        // Sides bounds (2 sides, 1..8 bots each)
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse("""
                {
                  "format": "core-critical-arena-setup",
                  "version": 1,
                  "arena": {
                    "map": "c1mp1",
                    "minutes": 5,
                    "sides": [
                      [],
                      [ { "mech": "thor", "loadout": 0, "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } } ]
                    ]
                  },
                  "seed": 1,
                  "random_seed": false,
                  "frame_ms": 33,
                  "hidden": false
                }
                """),
            "arena.sides[0]");

        var nineBots = string.Join(",", Enumerable.Repeat(
            """{ "mech": "madcat", "loadout": 0, "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } }""",
            9));
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse($$"""
                {
                  "format": "core-critical-arena-setup",
                  "version": 1,
                  "arena": {
                    "map": "c1mp1",
                    "minutes": 5,
                    "sides": [
                      [ { "mech": "madcat", "loadout": 0, "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } } ],
                      [ {{nineBots}} ]
                    ]
                  },
                  "seed": 1,
                  "random_seed": false,
                  "frame_ms": 33,
                  "hidden": false
                }
                """),
            "arena.sides[1]");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse("""
                {
                  "format": "core-critical-arena-setup",
                  "version": 1,
                  "arena": {
                    "map": "c1mp1",
                    "minutes": 5,
                    "sides": [
                      [ { "mech": "madcat", "loadout": 0, "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } } ],
                      [ { "mech": "madcat", "loadout": 0, "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } } ],
                      [ { "mech": "madcat", "loadout": 0, "preset": { "world": "c1", "mission": "ia1", "record": "Enemy_01" } } ]
                    ]
                  },
                  "seed": 1,
                  "random_seed": false,
                  "frame_ms": 33,
                  "hidden": false
                }
                """),
            "arena.sides");

        // Seed bounds (0..2147483647)
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"seed\": 1234567", "\"seed\": -1")),
            "seed");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"seed\": 1234567", "\"seed\": 2147483648")),
            "seed");

        // Loadout bounds (0..15 in file, < catalog count in ValidateAgainst)
        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"loadout\": 0", "\"loadout\": -1")),
            "arena.sides[0][0].loadout");

        ExpectFieldFailure(
            () => ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"loadout\": 0", "\"loadout\": 16")),
            "arena.sides[0][0].loadout");

        ExpectFieldFailure(
            () =>
            {
                var badLoadout = ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"loadout\": 0", "\"loadout\": 1"));
                badLoadout.ValidateAgainst(catalog);
            },
            "arena.sides[0][0].loadout");

        // Catalog membership: unknown map, mech, preset, and unsupported time_of_day
        ExpectFieldFailure(
            () =>
            {
                var badMap = ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"c1mp1\"", "\"c9mp9\""));
                badMap.ValidateAgainst(catalog);
            },
            "arena.map");

        ExpectFieldFailure(
            () =>
            {
                var badMech = ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"thor\"", "\" shadowcat_missing \""));
                badMech.ValidateAgainst(catalog);
            },
            "arena.sides[1][0].mech");

        ExpectFieldFailure(
            () =>
            {
                var badPreset = ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"Enemy_01\"", "\"Missing_Record\""));
                badPreset.ValidateAgainst(catalog);
            },
            "arena.sides[0][0].preset");

        ExpectFieldFailure(
            () =>
            {
                var badTime = ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"time_of_day\": null", "\"time_of_day\": \"dusk\""));
                badTime.ValidateAgainst(catalog);
            },
            "time_of_day",
            "this game runtime cannot set time of day yet");

        // Empty string TimeOfDay rejected by ValidateAgainst before Validate()
        ExpectFieldFailure(
            () =>
            {
                var emptyTime = ArenaSetupFile.Parse(SampleValidSetupJson);
                emptyTime.TimeOfDay = "";
                emptyTime.ValidateAgainst(catalog);
            },
            "time_of_day",
            "this game runtime cannot set time of day yet");

        var catalogWithTime = new ArenaCatalog(
            catalog.Maps,
            catalog.Mechs,
            catalog.Presets,
            new[] { "day", "night" });

        ExpectFieldFailure(
            () =>
            {
                var unknownTime = ArenaSetupFile.Parse(SampleValidSetupJson.Replace("\"time_of_day\": null", "\"time_of_day\": \"day\""));
                unknownTime.ValidateAgainst(catalogWithTime);
            },
            "time_of_day",
            "this game runtime cannot set time of day yet");
    }

    private static void CheckRandomSeedAndDirectoryPrep(string tempRoot)
    {
        var setup = ArenaSetupFile.Parse(SampleValidSetupJson);
        setup.RandomSeed = true;
        setup.Seed = 424242;

        var drawnSeeds = new HashSet<int>();
        for (var i = 0; i < 32; i++)
        {
            var resolved = setup.ResolveSeedForRun();
            Check(resolved >= 0 && resolved <= int.MaxValue, "Resolved random seed was outside 0..int.MaxValue.");
            drawnSeeds.Add(resolved);
        }
        Check(drawnSeeds.Count > 1, "Random seed resolution did not vary across runs.");
        Check(setup.RandomSeed && setup.Seed == 424242,
            "Resolving a random seed mutated the saved setup's Seed or RandomSeed.");

        var savedJson = ArenaSetupFile.ToJson(setup);
        var roundTripped = ArenaSetupFile.Parse(savedJson);
        Check(roundTripped.RandomSeed && roundTripped.Seed == 424242,
            "Saved setup did not retain random_seed: true and the fixed seed.");

        var fixedTime = new DateTime(2026, 11, 25, 19, 45, 00);
        var logsRoot = Path.Combine(tempRoot, "runs");
        var firstRun = ArenaMatchRunner.PrepareRunDirectory(logsRoot, setup, 111, fixedTime);
        var secondRun = ArenaMatchRunner.PrepareRunDirectory(logsRoot, setup, 222, fixedTime);
        Check(firstRun.RunFolder != secondRun.RunFolder &&
            Directory.Exists(firstRun.RunFolder) &&
            Directory.Exists(secondRun.RunFolder) &&
            File.Exists(firstRun.SetupJsonPath) &&
            File.Exists(secondRun.SetupJsonPath) &&
            firstRun.ExpectedLogPath == Path.Combine(firstRun.RunFolder, "match-111.jsonl") &&
            secondRun.ExpectedLogPath == Path.Combine(secondRun.RunFolder, "match-222.jsonl"),
            "PrepareRunDirectory did not disambiguate same-second run folders or write setup.json.");
    }

    private static void CheckArgumentsAndGraphicsSummary(string tempRoot)
    {
        var watchedArgs = ArenaMatchRunner.BuildArguments(@"D:\runs\setup.json", 77, 33, hidden: false);
        Check(watchedArgs.SequenceEqual(new[]
        {
            "--arena", @"D:\runs\setup.json", "--seed", "77", "--frame-ms", "33", "-nofmv"
        }), "Watched match argument array did not match expected flags.");

        var hiddenArgs = ArenaMatchRunner.BuildArguments(@"D:\runs\setup.json", 77, 33, hidden: true);
        Check(hiddenArgs.SequenceEqual(new[]
        {
            "--arena", @"D:\runs\setup.json", "--seed", "77", "--frame-ms", "33", "--hidden", "-nofmv"
        }), "Hidden match argument array did not match expected flags.");

        var replayArgs = ArenaMatchRunner.BuildReplay3dArguments(@"D:\runs\match-77.jsonl");
        Check(replayArgs.SequenceEqual(new[] { "--replay3d", @"D:\runs\match-77.jsonl" }),
            "3D replay argument array did not match expected flags.");

        var quoted = ArenaMatchRunner.FormatCommandLine(new[]
        {
            @"C:\Games\Core Critical\mw3.exe",
            "--install",
            @"D:\Games\MechWarrior 3",
            "--arena",
            @"C:\Users\Jane Doe\setup.json"
        });
        Check(quoted == "\"C:\\Games\\Core Critical\\mw3.exe\" --install \"D:\\Games\\MechWarrior 3\" --arena \"C:\\Users\\Jane Doe\\setup.json\"",
            "Command line quoting did not quote paths with spaces properly: " + quoted);

        var settings = new LauncherSettings
        {
            Width = 2560,
            Height = 1440,
            DrawDistance = 2400
        };
        var watchedSummary = ArenaMatchRunner.FormatGraphicsSummary(settings, Array.Empty<string>(), hidden: false);
        Check(watchedSummary == "Graphics: your current Play settings (2560x1440, scenery 2400, 0 model pack(s), 0 map pack(s)).",
            "Watched graphics summary did not match expected text: " + watchedSummary);

        var hiddenSummary = ArenaMatchRunner.FormatGraphicsSummary(settings, Array.Empty<string>(), hidden: true);
        Check(hiddenSummary == "Hidden matches draw nothing; graphics settings don't apply.",
            "Hidden graphics summary did not match exact required string: " + hiddenSummary);
    }

    private static void CheckOutcomeParsingAndExitHandling(string tempRoot)
    {
        var runFolder = Path.Combine(tempRoot, "outcome-run");
        Directory.CreateDirectory(runFolder);
        var setupPath = Path.Combine(runFolder, "setup.json");
        var logPath = Path.Combine(runFolder, "match-99.jsonl");

        // Stdout result parsing for Side A, Side B, and draw (including launcher elapsed suffix)
        var outcomeA = ArenaMatchRunner.EvaluateOutcome(
            0, 99,
            new[] { "arena: winner A, time 1:22, lost A 0 B 2 [launcher elapsed 4312 ms]" },
            runFolder, setupPath, logPath, "mw3.exe --arena setup.json");
        Check(outcomeA.Succeeded && outcomeA.Winner == "A" && outcomeA.TimeText == "1:22" &&
            outcomeA.LostA == 0 && outcomeA.LostB == 2 && outcomeA.WinnerDisplayLabel == "Side A wins",
            "Stdout winner A outcome did not parse properly.");

        var outcomeB = ArenaMatchRunner.EvaluateOutcome(
            0, 99,
            new[] { "arena: winner B, time 12:05, lost A 4 B 1" },
            runFolder, setupPath, logPath, "mw3.exe --arena setup.json");
        Check(outcomeB.Succeeded && outcomeB.Winner == "B" && outcomeB.TimeText == "12:05" &&
            outcomeB.LostA == 4 && outcomeB.LostB == 1 && outcomeB.WinnerDisplayLabel == "Side B wins",
            "Stdout winner B outcome did not parse properly.");

        var outcomeDraw = ArenaMatchRunner.EvaluateOutcome(
            0, 99,
            new[] { "arena: winner draw, time 5:00, lost A 2 B 2" },
            runFolder, setupPath, logPath, "mw3.exe --arena setup.json");
        Check(outcomeDraw.Succeeded && outcomeDraw.Winner == "draw" && outcomeDraw.TimeText == "5:00" &&
            outcomeDraw.LostA == 2 && outcomeDraw.LostB == 2 && outcomeDraw.WinnerDisplayLabel == "Draw",
            "Stdout draw outcome did not parse properly.");

        // Exit 0 with no stdout line falls back to streaming the match-<seed>.jsonl end line
        File.WriteAllText(logPath,
            "{\"type\":\"start\",\"version\":2,\"map\":\"c1mp1\"}\n" +
            "{\"type\":\"state\",\"t\":0.1,\"mechs\":[]}\n" +
            "{\"type\":\"end\",\"winner\":\"B\",\"t\":87.4,\"lost\":[1,0]}\n");

        var outcomeFromLog = ArenaMatchRunner.EvaluateOutcome(
            0, 99, Array.Empty<string>(), runFolder, setupPath, logPath, "mw3.exe --arena setup.json");
        Check(outcomeFromLog.Succeeded && outcomeFromLog.Winner == "B" && outcomeFromLog.TimeText == "1:27" &&
            outcomeFromLog.LostA == 1 && outcomeFromLog.LostB == 0,
            "Match log 'end' fallback did not parse properly.");

        // Nonzero exit codes must NEVER accept a log end line as success
        var exit2Outcome = ArenaMatchRunner.EvaluateOutcome(
            2, 99,
            new[] { "mw3: --arena setup.json: map: unknown map \"c9mp9\" [launcher elapsed 45 ms]" },
            runFolder, setupPath, logPath, "mw3.exe --arena setup.json");
        Check(!exit2Outcome.Succeeded &&
            exit2Outcome.ErrorMessage != null &&
            exit2Outcome.ErrorMessage.StartsWith("Setup refused:", StringComparison.Ordinal) &&
            exit2Outcome.ErrorMessage.Contains("unknown map \"c9mp9\"", StringComparison.Ordinal),
            "Exit 2 did not report 'Setup refused: <detail>': " + exit2Outcome.ErrorMessage);

        var exit1Outcome = ArenaMatchRunner.EvaluateOutcome(
            1, 99,
            new[] { "mw3: arena: a side has no bot that could be made; the match cannot start" },
            runFolder, setupPath, logPath, "mw3.exe --arena setup.json");
        Check(!exit1Outcome.Succeeded &&
            exit1Outcome.ErrorMessage != null &&
            exit1Outcome.ErrorMessage.StartsWith("Match could not start:", StringComparison.Ordinal) &&
            exit1Outcome.ErrorMessage.Contains("a side has no bot that could be made", StringComparison.Ordinal),
            "Exit 1 did not report 'Match could not start: <detail>': " + exit1Outcome.ErrorMessage);

        // Exit 0 with neither stdout result nor log end line fails clearly
        var missingLogPath = Path.Combine(runFolder, "match-missing.jsonl");
        var exit0Missing = ArenaMatchRunner.EvaluateOutcome(
            0, 100, Array.Empty<string>(), runFolder, setupPath, missingLogPath, "mw3.exe --arena setup.json");
        Check(!exit0Missing.Succeeded &&
            exit0Missing.ErrorMessage != null &&
            exit0Missing.ErrorMessage.Contains("without a result", StringComparison.OrdinalIgnoreCase),
            "Exit 0 without a result did not fail with an explanation.");
    }

    private static void CheckSparseLoadoutIndices()
    {
        var sparseCatalogJson = """
            {
              "version": 1,
              "maps": [ { "id": "c1mp1", "name": "Canyon" } ],
              "mechs": [
                {
                  "id": "madcat",
                  "name": "Mad Cat",
                  "loadouts": [
                    { "index": 0, "name": "Stock" },
                    { "index": 5, "name": "Sparse High Index" }
                  ]
                }
              ],
              "presets": [
                { "world": "c1", "mission": "ia1", "record": "Enemy_01", "mech": "madcat" }
              ]
            }
            """;
        var sparseCatalog = ArenaCatalog.ParseJson(sparseCatalogJson);

        var validSparse = ArenaSetupFile.Parse(SampleValidSetupJson);
        validSparse.Sides[1][0] = validSparse.Sides[1][0] with { Mech = "madcat", Loadout = 5 };
        // High index 5 exists on madcat and must be accepted
        validSparse.ValidateAgainst(sparseCatalog);

        var missingLower = validSparse.Clone();
        missingLower.Sides[1][0] = missingLower.Sides[1][0] with { Loadout = 1 };
        // Lower index 1 does not exist on madcat and must be rejected with exact field path
        ExpectFieldFailure(
            () => missingLower.ValidateAgainst(sparseCatalog),
            "arena.sides[1][0].loadout",
            "is not a stock loadout of madcat");
    }

    private static void CheckRuntimeLogTimestampAndStdoutResult(string tempRoot)
    {
        var testLogPath = Path.Combine(tempRoot, "test_mw3.log");
        var launchStartUtc = new DateTime(2026, 11, 26, 12, 0, 0, DateTimeKind.Utc);

        File.WriteAllText(testLogPath, "arena: winner A, time 1:15, lost A 0 B 2\n");
        File.SetLastWriteTimeUtc(testLogPath, launchStartUtc.AddMinutes(-1));
        var staleLines = ArenaMatchRunner.TryReadFreshRuntimeLogLines(testLogPath, launchStartUtc);
        Check(staleLines.Count == 0, "Runtime log older than launch must be ignored.");

        // The runtime replaces the old log, so every line in a fresh file belongs to this run.
        var freshLines = new[]
        {
            "arena: winner A, time 1:00, lost A 0 B 2",
            "ordinary log line",
            "arena: winner B, time 3:20, lost A 2 B 0"
        };
        File.WriteAllLines(testLogPath, freshLines);
        File.SetLastWriteTimeUtc(testLogPath, launchStartUtc.AddMinutes(1));
        var runtimeLines = ArenaMatchRunner.TryReadFreshRuntimeLogLines(testLogPath, launchStartUtc);
        Check(runtimeLines.SequenceEqual(freshLines), "Fresh runtime log must be read in full.");
        var foundLast = ArenaMatchRunner.TryParseStdoutResult(
            runtimeLines, out var lastWinner, out var lastTime, out var lastLostA, out var lastLostB);
        Check(foundLast && lastWinner == "B" && lastTime == "3:20" && lastLostA == 2 && lastLostB == 0,
            "Fresh runtime log must use the LAST matching result.");

        File.SetLastWriteTimeUtc(testLogPath, launchStartUtc);
        var sameTimeLines = ArenaMatchRunner.TryReadFreshRuntimeLogLines(testLogPath, launchStartUtc);
        Check(sameTimeLines.SequenceEqual(freshLines), "Runtime log written at launch time must be accepted.");
    }

    private static void CheckCatalogProcessWaitHelper()
    {
        // 1. Timeout kills process tree and throws TimeoutException
        {
            var startInfo = new ProcessStartInfo("cmd.exe", "/c ping -n 30 127.0.0.1 >nul")
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            using var process = Process.Start(startInfo)!;
            var timedOut = false;
            try
            {
                ArenaCatalog.WaitForCatalogProcessAsync(process, TimeSpan.FromMilliseconds(400)).GetAwaiter().GetResult();
            }
            catch (TimeoutException error)
            {
                timedOut = true;
                Check(error.Message == "Generating the arena catalog took longer than 2 minutes",
                    "Timeout exception message did not match expected text: " + error.Message);
            }
            Check(timedOut, "WaitForCatalogProcessAsync did not time out as expected.");
            Check(process.HasExited, "Process was not killed on timeout.");
        }

        // 2. Cancellation kills process tree and propagates OperationCanceledException
        {
            var startInfo = new ProcessStartInfo("cmd.exe", "/c ping -n 30 127.0.0.1 >nul")
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            using var process = Process.Start(startInfo)!;
            using var cancellationSource = new CancellationTokenSource(TimeSpan.FromMilliseconds(300));
            var cancelled = false;
            try
            {
                ArenaCatalog.WaitForCatalogProcessAsync(process, TimeSpan.FromSeconds(30), cancellationSource.Token).GetAwaiter().GetResult();
            }
            catch (OperationCanceledException)
            {
                cancelled = true;
            }
            Check(cancelled, "WaitForCatalogProcessAsync did not propagate caller cancellation.");
            Check(process.HasExited, "Process was not killed on cancellation.");
        }
    }

    /// <summary>
    /// Manual end-to-end run for #503: the same catalog, validation and native launch path the
    /// AI Arena window uses, with the player's saved settings and active packs. Needs a game
    /// install and a launcher folder that holds the bundled runtime.
    /// </summary>
    public static async Task RunManualMatch(string setupPath, string launcherDirectory)
    {
        var dataRoot = LauncherPaths.DataRoot;
        var settings = new SettingsManager(launcherDirectory, dataRoot).Current;
        // Same pack selection the main window makes at startup; without RefreshPacks the
        // manager has no packs loaded and the match would run with stock models.
        var packManager = new PackManager(dataRoot);
        packManager.RefreshPacks(settings.PackSelectionInitialized || settings.ActivePacks.Count > 0
            ? settings.ActivePacks : null);
        var activeDirectories = packManager.GetActivePackDirectories();
        var runner = new NativeGameRunner(launcherDirectory, dataRoot);
        var catalog = await ArenaCatalog.EnsureCatalogAsync(runner, settings.GamePath, dataRoot);
        var setup = ArenaSetupFile.Load(setupPath);
        setup.ValidateAgainst(catalog);
        var seed = setup.ResolveSeedForRun();
        var outcome = await ArenaMatchRunner.RunMatchAsync(runner, settings, activeDirectories, setup, seed,
            ArenaMatchRunner.DefaultLogsRoot(dataRoot), dataRoot);
        Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(outcome,
            new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
    }
}
