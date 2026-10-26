using System.IO;
using System.Security.Cryptography;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

public sealed record ReleaseArtifact(string Url, string Filename, long Bytes, string Sha256);
public sealed record ReleaseDependency(string ProductId, string MinimumVersion);
public sealed record OnlineRelease(string ProductId, string? GameId, string Version, string DisplayVersion,
    string NumericVersion, long Sequence, string Status, string Os, string Architecture,
    string MinimumLauncherVersion, string Contract, ReleaseArtifact Metadata, ReleaseArtifact Payload,
    string ReleaseNotes, string? NotesUrl, ReleaseDependency[] Dependencies);
public sealed record ReleaseCatalogDocument(int SchemaVersion, string Type, string Channel, long Sequence,
    DateTimeOffset IssuedUtc, DateTimeOffset ExpiresUtc, OnlineRelease[] Releases);
public sealed record VerifiedReleaseCatalog(ReleaseCatalogDocument Document, string PayloadSha256, byte[] Envelope);

/// <summary>Authenticates discovery independently of the existing signed installation protocols.</summary>
public static class ReleaseCatalog
{
    public const int MaximumMetadataBytes = 2 * 1024 * 1024;
    public const long MaximumPayloadBytes = 512L * 1024 * 1024;

    public static VerifiedReleaseCatalog Verify(byte[] envelope, RuntimeUpdateTrust trust,
        OnlineUpdateConfiguration config, DateTimeOffset now, long highestSequence = 0, string? previousHash = null)
    {
        config.Validate();
        if (envelope.Length > MaximumMetadataBytes) throw new InvalidDataException("Release catalog is too large.");
        using var doc = JsonDocument.Parse(envelope);
        var root = doc.RootElement;
        if (!trust.PublicKeys.TryGetValue(root.GetProperty("key_id").GetString() ?? "", out var pem))
            throw new InvalidDataException("Untrusted release catalog signing key.");
        var payload = Convert.FromBase64String(root.GetProperty("payload").GetString() ?? "");
        using var rsa = RSA.Create();
        rsa.ImportFromPem(pem);
        if (rsa.KeySize < 3072 || !rsa.VerifyData(payload,
            Convert.FromBase64String(root.GetProperty("signature").GetString() ?? ""),
            HashAlgorithmName.SHA256, RSASignaturePadding.Pss))
            throw new InvalidDataException("Release catalog signature verification failed.");
        var catalog = JsonSerializer.Deserialize<ReleaseCatalogDocument>(payload, RuntimeUpdates.Json)
            ?? throw new InvalidDataException("Empty release catalog.");
        if (catalog.SchemaVersion != 1 || catalog.Type != "corecritical-release-catalog-v1" ||
            catalog.Channel != config.Channel || catalog.Sequence < 1)
            throw new InvalidDataException("Unsupported release catalog or different update channel.");
        if (catalog.IssuedUtc > now.AddMinutes(5) || catalog.ExpiresUtc <= now ||
            catalog.ExpiresUtc <= catalog.IssuedUtc || catalog.ExpiresUtc - catalog.IssuedUtc > TimeSpan.FromDays(31))
            throw new InvalidDataException("Release catalog has expired or the system clock needs checking. Your installed games remain available.");
        var hash = Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant();
        if (catalog.Sequence < highestSequence ||
            (catalog.Sequence == highestSequence && !string.Equals(previousHash, hash, StringComparison.Ordinal)))
            throw new InvalidDataException("An older or conflicting release catalog was received. Retry the update check.");
        if (catalog.Releases == null || catalog.Releases.Length > 32 ||
            catalog.Releases.Select(r => r.ProductId).Distinct(StringComparer.Ordinal).Count() != catalog.Releases.Length)
            throw new InvalidDataException("Invalid or duplicate release products.");
        foreach (var release in catalog.Releases) Validate(release, config);
        return new(catalog, hash, envelope.ToArray());
    }

    private static void Validate(OnlineRelease r, OnlineUpdateConfiguration config)
    {
        var launcher = r.ProductId == GameCatalog.LauncherId;
        var game = launcher ? null : GameCatalog.Get(r.ProductId);
        if ((launcher ? r.GameId != null : r.GameId != game!.Id) || r.Status != "promoted" ||
            r.Os != "windows" || r.Architecture != "x64" || r.Sequence < 1 ||
            !Version.TryParse(r.NumericVersion, out var version) || version.Build < 0 ||
            r.Version != r.NumericVersion || !Version.TryParse(r.MinimumLauncherVersion, out var minimum) || minimum.Build < 0 ||
            string.IsNullOrWhiteSpace(r.DisplayVersion) || r.DisplayVersion.Length > 128)
            throw new InvalidDataException("Release target, version or publication status is unsupported.");
        if (r.Contract != (launcher ? "launcher-inno-v1" : "mw3-local-runtime-v1") || (!launcher && game!.Id != GameCatalog.Mw3))
            throw new InvalidDataException("This product does not have a supported online update installer.");
        Artifact(r.Metadata, r.Version + (launcher ? GameCatalog.LauncherUpdateExtension : game!.UpdateExtension), MaximumMetadataBytes, config);
        Artifact(r.Payload, r.Version + ".zip", MaximumPayloadBytes, config);
        if (r.ReleaseNotes == null || r.ReleaseNotes.Length > 16384 || r.Dependencies == null ||
            r.Dependencies.Length > 8 || r.Dependencies.Select(d => d.ProductId).Distinct().Count() != r.Dependencies.Length)
            throw new InvalidDataException("Invalid release notes or dependencies.");
        if (r.NotesUrl != null) config.Destination(r.NotesUrl);
        foreach (var dependency in r.Dependencies)
            if (launcher || dependency.ProductId != GameCatalog.LauncherId ||
                !Version.TryParse(dependency.MinimumVersion, out var required) || required.Build < 0)
                throw new InvalidDataException("Unsupported update dependency.");
    }

    private static void Artifact(ReleaseArtifact? artifact, string filename, long maximum, OnlineUpdateConfiguration config)
    {
        if (artifact == null || artifact.Filename != filename || artifact.Bytes is < 1 || artifact.Bytes > maximum ||
            artifact.Sha256 == null || artifact.Sha256.Length != 64 || !artifact.Sha256.All(Uri.IsHexDigit))
            throw new InvalidDataException("Invalid update artifact name, size or SHA-256.");
        var address = config.Destination(artifact.Url);
        if (Uri.UnescapeDataString(address.Segments.Last()) != filename)
            throw new InvalidDataException("Update URL must retain the exact release filename.");
    }

    public static void VerifyArtifact(string file, ReleaseArtifact artifact) =>
        RuntimeUpdates.VerifyFile(file, new(artifact.Bytes, artifact.Sha256));

    public static VerifiedLauncherUpdate VerifyLauncherPackage(OnlineRelease release, byte[] metadata, LauncherUpdates updates)
    {
        MetadataPin(release, metadata);
        var result = updates.Verify(metadata);
        var m = result.Manifest;
        Match(release, m.ProductId, null, m.Version, m.Sequence, m.MinimumLauncherVersion,
            m.UpdateType, m.PackageBytes, m.PackageSha256);
        return result;
    }

    public static VerifiedRuntimeUpdate VerifyRuntimePackage(OnlineRelease release, byte[] metadata, RuntimeUpdates updates)
    {
        MetadataPin(release, metadata);
        // The normal runtime verifier still enforces the currently running launcher minimum.
        var result = updates.Verify(metadata);
        var m = result.Manifest;
        Match(release, m.GameId, m.GameId, m.Version, m.Sequence, m.MinimumLauncherVersion,
            m.PreparationContract, m.PackageBytes, m.PackageSha256);
        return result;
    }

    private static void MetadataPin(OnlineRelease release, byte[] bytes)
    {
        if (bytes.Length != release.Metadata.Bytes ||
            !Convert.ToHexString(SHA256.HashData(bytes)).Equals(release.Metadata.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Downloaded update metadata does not match the signed catalog.");
    }

    private static void Match(OnlineRelease r, string product, string? game, string version, long sequence,
        string minimum, string contract, long bytes, string hash)
    {
        if (r.ProductId != product || r.GameId != game || r.NumericVersion != version || r.Sequence != sequence ||
            r.MinimumLauncherVersion != minimum || r.Contract != contract || r.Payload.Bytes != bytes ||
            !r.Payload.Sha256.Equals(hash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The signed update package disagrees with its release catalog entry.");
    }
}
