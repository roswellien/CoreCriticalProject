using System.IO;
using System.Security.Cryptography;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

public sealed record AssetPackRelease(string Id, string GameId, string Version,
    string MinimumRuntimeVersion, ReleaseArtifact Archive, string[] InstalledManifestSha256s);

public sealed record AssetPackCatalogDocument(int SchemaVersion, string Type, string Channel,
    long Sequence, DateTimeOffset IssuedUtc, DateTimeOffset ExpiresUtc, AssetPackRelease[] Packs);

public sealed record VerifiedAssetPackCatalog(AssetPackCatalogDocument Document, string PayloadSha256);

public sealed record InstalledAssetPack(string Id, string GameId, string Version, string ManifestSha256);

/// <summary>Authenticates and plans asset pack updates independently of core runtime releases.</summary>
public static class AssetPackUpdateCatalog
{
    public const int MaximumMetadataBytes = ReleaseCatalog.MaximumMetadataBytes;
    public const long MaximumArchiveBytes = PackStorage.MaxExpandedBytes;

    public static VerifiedAssetPackCatalog Verify(byte[] envelope, RuntimeUpdateTrust trust,
        OnlineUpdateConfiguration config, DateTimeOffset now, long highestSequence = 0,
        string? previousHash = null)
    {
        config.Validate();
        if (envelope == null || envelope.Length is < 1 or > MaximumMetadataBytes)
            throw new InvalidDataException("Asset pack catalog envelope is invalid or too large.");

        using var doc = JsonDocument.Parse(envelope);
        var root = doc.RootElement;
        if (!root.TryGetProperty("key_id", out var keyIdProp) ||
            !trust.PublicKeys.TryGetValue(keyIdProp.GetString() ?? "", out var pem))
            throw new InvalidDataException("Untrusted asset pack catalog signing key.");

        if (!root.TryGetProperty("payload", out var payloadProp) ||
            !root.TryGetProperty("signature", out var signatureProp))
            throw new InvalidDataException("Invalid asset pack catalog envelope structure.");

        var payload = Convert.FromBase64String(payloadProp.GetString() ?? "");
        var signature = Convert.FromBase64String(signatureProp.GetString() ?? "");

        using var rsa = RSA.Create();
        rsa.ImportFromPem(pem);
        if (rsa.KeySize < 3072 || !rsa.VerifyData(payload, signature, HashAlgorithmName.SHA256, RSASignaturePadding.Pss))
            throw new InvalidDataException("Asset pack catalog signature verification failed.");

        var catalog = JsonSerializer.Deserialize<AssetPackCatalogDocument>(payload, RuntimeUpdates.Json)
            ?? throw new InvalidDataException("Empty asset pack catalog.");

        if (catalog.SchemaVersion != 1 || catalog.Type != "corecritical-asset-pack-catalog-v1" ||
            catalog.Channel != config.Channel || catalog.Sequence < 1)
            throw new InvalidDataException("Unsupported asset pack catalog or different update channel.");

        var validLifetime = catalog.ExpiresUtc > catalog.IssuedUtc &&
            catalog.ExpiresUtc - catalog.IssuedUtc <= TimeSpan.FromDays(31);
        var validAtNow = catalog.IssuedUtc <= now.AddMinutes(5) && catalog.ExpiresUtc > now;
        if (!validLifetime || !validAtNow)
            throw new InvalidDataException("Asset pack catalog has expired or the system clock needs checking.");

        var hash = Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant();
        if (catalog.Sequence < highestSequence ||
            (catalog.Sequence == highestSequence && !string.Equals(previousHash, hash, StringComparison.Ordinal)))
            throw new InvalidDataException("An older or conflicting asset pack catalog was received. Retry the update check.");

        if (catalog.Packs == null || catalog.Packs.Length > 128 ||
            catalog.Packs.Any(p => p == null) ||
            catalog.Packs.Select(p => (p.GameId, p.Id)).Distinct().Count() != catalog.Packs.Length)
            throw new InvalidDataException("Invalid or duplicate asset pack entries.");

        foreach (var pack in catalog.Packs)
        {
            ValidatePack(pack, config);
        }

        return new(catalog, hash);
    }

    private static void ValidatePack(AssetPackRelease pack, OnlineUpdateConfiguration config)
    {
        PackStorage.ValidateId(pack.Id);
        var game = GameCatalog.Get(pack.GameId);
        if (game.Id != pack.GameId)
            throw new InvalidDataException("Invalid game identity in asset pack catalog.");
        PackStorage.ParseOnlineVersion(pack.Version);
        PackStorage.ParseOnlineVersion(pack.MinimumRuntimeVersion);

        ValidateArchive(pack.Archive, game.PackExtension, config);

        if (pack.InstalledManifestSha256s == null || pack.InstalledManifestSha256s.Length is < 1 or > 32 ||
            pack.InstalledManifestSha256s.Distinct(StringComparer.OrdinalIgnoreCase).Count() != pack.InstalledManifestSha256s.Length)
            throw new InvalidDataException("Asset pack must define 1 to 32 distinct allowed predecessor manifest hashes.");

        foreach (var manifestHash in pack.InstalledManifestSha256s)
        {
            ValidateSha256(manifestHash, "Invalid predecessor manifest SHA-256.");
        }
    }

    private static void ValidateArchive(ReleaseArtifact? archive, string expectedExtension, OnlineUpdateConfiguration config)
    {
        if (archive == null || string.IsNullOrWhiteSpace(archive.Filename) ||
            archive.Bytes is < 1 || archive.Bytes > MaximumArchiveBytes)
            throw new InvalidDataException("Invalid asset pack archive size or filename.");

        if (archive.Filename.Contains('/') || archive.Filename.Contains('\\') ||
            !string.Equals(Path.GetExtension(archive.Filename), expectedExtension, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Asset pack archive filename must use " + expectedExtension + ".");

        PackStorage.ValidatePath(archive.Filename);
        ValidateSha256(archive.Sha256, "Invalid asset pack archive SHA-256.");

        var address = config.Destination(archive.Url);
        if (Uri.UnescapeDataString(address.Segments.Last()) != archive.Filename)
            throw new InvalidDataException("Update URL must retain the exact release filename.");
    }

    private static void ValidateSha256(string? hash, string errorMessage)
    {
        if (hash == null || hash.Length != 64 || !hash.All(Uri.IsHexDigit))
            throw new InvalidDataException(errorMessage);
    }

    public static IReadOnlyList<AssetPackRelease> Plan(VerifiedAssetPackCatalog catalog,
        IReadOnlyList<InstalledAssetPack> installed, string gameId, Version runtimeVersion)
    {
        var result = new List<AssetPackRelease>();
        foreach (var release in catalog.Document.Packs)
        {
            if (!string.Equals(release.GameId, gameId, StringComparison.Ordinal))
                continue;

            var current = installed.FirstOrDefault(p =>
                string.Equals(p.Id, release.Id, StringComparison.Ordinal) &&
                string.Equals(p.GameId, gameId, StringComparison.Ordinal));
            if (current == null)
                continue;

            Version currentVersion;
            try
            {
                currentVersion = PackStorage.ParseOnlineVersion(current.Version);
            }
            catch (InvalidDataException)
            {
                continue;
            }

            var releaseVersion = PackStorage.ParseOnlineVersion(release.Version);
            if (releaseVersion <= currentVersion)
                continue;

            if (string.IsNullOrWhiteSpace(current.ManifestSha256) ||
                !release.InstalledManifestSha256s.Contains(current.ManifestSha256, StringComparer.OrdinalIgnoreCase))
                continue;

            var minimumRuntime = PackStorage.ParseOnlineVersion(release.MinimumRuntimeVersion);
            if (new Version(runtimeVersion.Major, runtimeVersion.Minor, Math.Max(0, runtimeVersion.Build), Math.Max(0, runtimeVersion.Revision)) < minimumRuntime)
                continue;

            result.Add(release);
        }
        return result;
    }
}
