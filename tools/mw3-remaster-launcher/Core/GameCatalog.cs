using System.IO;

namespace MW3RemasterLauncher.Core;

public sealed record GameDefinition(string Id, string Name, string FileStem, bool Playable)
{
    public string UpdateExtension => "." + FileStem + "update";
    public string PackExtension => "." + FileStem + "pack";
    public string DisplayName => Name + (Playable ? "" : " — planned");
}

/// <summary>Stable product identities. Registering a title does not implement its runtime.</summary>
public static class GameCatalog
{
    public const string LauncherId = "corecritical";
    public const string LauncherUpdateExtension = ".ccupdate";
    public const string Mw3 = "mw3";
    public static IReadOnlyList<GameDefinition> Games { get; } = Array.AsReadOnly(new[] {
        new GameDefinition(Mw3, "MechWarrior 3", "mw3", true),
        new GameDefinition("mw3pm", "MechWarrior 3: Pirate’s Moon", "mw3pm", false),
        new GameDefinition("mw4", "MechWarrior 4: Vengeance", "mw4", false),
        new GameDefinition("mw4bk", "MechWarrior 4: Black Knight", "mw4bk", false),
        new GameDefinition("mw4mercs", "MechWarrior 4: Mercenaries", "mw4mercs", false)
    });

    public static GameDefinition Get(string id) => Games.FirstOrDefault(g => g.Id == id)
        ?? throw new InvalidDataException("Unknown game identity: " + id);

    public static void RequirePackTarget(string gameId, string expected, string? archive = null)
    {
        var game = Get(gameId);
        if (game.Id != Get(expected).Id) throw new InvalidDataException("This pack belongs to " + game.Name + ". Select that game's library.");
        if (archive == null) return;
        var extension = Path.GetExtension(archive);
        if (!extension.Equals(game.PackExtension, StringComparison.OrdinalIgnoreCase) &&
            !extension.Equals(".zip", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The pack filename must use " + game.PackExtension + " and match its game_id.");
    }

    // Retain existing MW3 installations; every additional title has a separate store.
    public static string PackBase(string dataRoot, string gameId) => Get(gameId).Id == Mw3
        ? dataRoot : Path.Combine(dataRoot, "games", gameId);
}
