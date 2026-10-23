using System.IO;

namespace MW3RemasterLauncher.Core;

/// <summary>Use the installer's signed source tools after original-data setup.</summary>
public static class BundledPreparation
{
    public static bool IsAvailable(string application) =>
        !NativeRuntimeLayout.HasPrecompiledRuntime(application) &&
        File.Exists(Path.Combine(application, "Preparation", "initial.mw3update"));

    public static async Task PrepareAsync(string application, string game, IProgress<string>? progress = null,
        CancellationToken cancellation = default, string? dataRoot = null)
    {
        var updatePath = PackStorage.Resolve(application, "Preparation/initial.mw3update");
        PackStorage.EnsureNoLinks(updatePath);
        if (new FileInfo(updatePath).Length > 2 * 1024 * 1024)
            throw new InvalidDataException("Bundled preparation metadata is too large.");
        var updates = new RuntimeUpdates(application, RuntimeUpdates.ReadTrust(application), dataRoot);
        var update = updates.Verify(File.ReadAllBytes(updatePath));
        var state = updates.State();
        if (state.HighestSequence >= update.Manifest.Sequence && state.Active != null)
        {
            NativeRuntimeLayout.FindInstalled(application, dataRoot);
            progress?.Report("The installed native game version is ready.");
            return;
        }
        await updates.PrepareAsync(update, game, PackStorage.Resolve(application, "Preparation/initial.zip"), progress, cancellation);
    }
}
