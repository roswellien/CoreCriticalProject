using System.IO;

namespace MW3RemasterLauncher.Core;

public sealed record InstalledUpdateProduct(string ProductId, string NumericVersion, long HighestSequence);
public sealed record PlannedOnlineUpdate(OnlineRelease Release, string? BlockedReason);

/// <summary>Orders separate product transactions without weakening their individual installers.</summary>
public static class OnlineUpdatePlanner
{
    public static IReadOnlyList<PlannedOnlineUpdate> Plan(VerifiedReleaseCatalog catalog,
        Version launcherVersion, IReadOnlyList<InstalledUpdateProduct> installed)
    {
        var result = new List<PlannedOnlineUpdate>();
        var launcher = catalog.Document.Releases.SingleOrDefault(r => r.ProductId == GameCatalog.LauncherId);
        var launcherState = installed.SingleOrDefault(p => p.ProductId == GameCatalog.LauncherId);
        var launcherEligible = launcher != null && Version.Parse(launcher.NumericVersion) > launcherVersion &&
            Version.Parse(launcher.MinimumLauncherVersion) <= launcherVersion &&
            launcher.Sequence > (launcherState?.HighestSequence ?? 0);
        if (launcherEligible) result.Add(new(launcher!, null));
        foreach (var release in catalog.Document.Releases.Where(r => r.ProductId != GameCatalog.LauncherId))
        {
            var current = installed.SingleOrDefault(p => p.ProductId == release.ProductId);
            if (current == null || release.Sequence <= current.HighestSequence) continue;
            if (!Version.TryParse(current.NumericVersion, out var currentVersion))
                throw new InvalidDataException("Cannot establish the selected runtime version. Repair its installation before updating.");
            if (Version.Parse(release.NumericVersion) <= currentVersion) continue;
            var minimum = Version.Parse(release.MinimumLauncherVersion);
            foreach (var dependency in release.Dependencies)
                if (Version.Parse(dependency.MinimumVersion) > minimum) minimum = Version.Parse(dependency.MinimumVersion);
            var blocked = minimum <= launcherVersion || (launcherEligible && Version.Parse(launcher!.NumericVersion) >= minimum)
                ? null : "Update Core Critical through the current full installer before installing this game update.";
            result.Add(new(release, blocked));
        }
        return result;
    }
}
