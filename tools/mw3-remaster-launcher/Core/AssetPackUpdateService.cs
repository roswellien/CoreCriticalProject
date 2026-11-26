using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>Checks signed asset metadata and installs an explicitly acquired private pack.</summary>
public sealed class AssetPackUpdateService : IDisposable
{
    public const string ConfigurationFile = "asset-pack-updates.json";
    private readonly string _application;
    private readonly string _dataRoot;
    private readonly string _modsRoot;
    private readonly string _game;
    private readonly OnlineUpdateConfiguration _config;
    private readonly RuntimeUpdateTrust _trust;
    private readonly OnlineUpdateDownloader _downloader;
    private readonly string _watermark;
    private VerifiedAssetPackCatalog? _catalog;

    private sealed record CatalogWatermark(long Sequence, string Sha256);

    public AssetPackUpdateService(string application, string dataRoot, PackManager manager,
        HttpMessageHandler? handler = null)
    {
        _application = application;
        _dataRoot = dataRoot;
        _modsRoot = manager.ModsRoot;
        _game = manager.GameId;
        _config = OnlineUpdateConfiguration.Read(application, ConfigurationFile);
        _trust = RuntimeUpdates.ReadTrust(application);
        _downloader = new OnlineUpdateDownloader(application, _config, dataRoot, handler: handler);
        _watermark = PackStorage.Resolve(_downloader.Store, "asset-packs/" + _config.Channel + "/watermark.json");
    }

    public static bool IsConfigured(string application) =>
        File.Exists(Path.Combine(application, ConfigurationFile));

    public async Task<IReadOnlyList<AssetPackRelease>> CheckAsync(CancellationToken cancellation = default)
    {
        _catalog = null;
        var envelope = await _downloader.FetchCatalogAsync(cancellation);
        var directory = Path.GetDirectoryName(_watermark)!;
        PackStorage.EnsureNoLinks(directory);
        Directory.CreateDirectory(directory);
        using (PackStorage.Lock(directory))
        {
            var seen = ReadWatermark();
            var verified = AssetPackUpdateCatalog.Verify(envelope, _trust, _config,
                DateTimeOffset.UtcNow, seen?.Sequence ?? 0, seen?.Sha256);
            if (seen == null || seen.Sequence != verified.Document.Sequence)
            {
                WriteWatermark(new(verified.Document.Sequence, verified.PayloadSha256));
            }
            _catalog = verified;
        }

        var runtime = CompatibleRuntimeVersion();
        if (runtime == null) return Array.Empty<AssetPackRelease>();
        return AssetPackUpdateCatalog.Plan(_catalog, ReadInstalled(), _game, runtime);
    }

    public PackManifest InstallDownloaded(string id, string archive,
        IProgress<PackInstallProgress>? progress = null)
    {
        var catalog = _catalog ?? throw new InvalidOperationException("Check for asset pack updates first.");
        if (catalog.Document.ExpiresUtc <= DateTimeOffset.UtcNow)
        {
            throw new InvalidDataException("The asset pack catalog expired. Check for updates again.");
        }

        using var gameGate = GameUpdateGate.Acquire(_dataRoot);
        var runtime = CompatibleRuntimeVersion()
            ?? throw new InvalidDataException("The selected runtime does not support managed asset pack updates.");
        var release = AssetPackUpdateCatalog.Plan(catalog, ReadInstalled(), _game, runtime)
            .SingleOrDefault(item => item.Id == id)
            ?? throw new InvalidDataException("This asset pack update is no longer applicable.");
        using (PackStorage.Lock(Path.GetDirectoryName(_watermark)!))
        {
            var latest = ReadWatermark();
            if (latest == null || latest.Sequence != catalog.Document.Sequence ||
                latest.Sha256 != catalog.PayloadSha256)
            {
                throw new InvalidDataException("The asset pack catalog changed. Check for updates again.");
            }
            var root = RuntimeUpdates.SelectedRoot(_application, _dataRoot) ?? Path.Combine(_application, "Runtime");
            var profile = PackStorage.Resolve(root, "profile.json");
            var native = JsonNode.Parse(LauncherUpdates.ReadMetadata(profile))?["native"] as JsonObject
                ?? throw new InvalidDataException("The selected runtime does not advertise asset pack support.");
            return PackStorage.Install(_modsRoot, archive, _game, progress,
                new(release.Id, release.Version, release.InstalledManifestSha256s, release.Archive, native));
        }
    }

    private Version? CompatibleRuntimeVersion()
    {
        var version = OnlineUpdateService.InstalledRuntimeVersion(_application, _dataRoot);
        return Version.TryParse(version, out var numeric) && numeric.Build >= 0 ? numeric : null;
    }

    private List<InstalledAssetPack> ReadInstalled()
    {
        var snapshot = new List<InstalledAssetPack>();
        using var storageLock = PackStorage.Lock(_modsRoot);
        foreach (var directory in Directory.EnumerateDirectories(_modsRoot))
        {
            var id = Path.GetFileName(directory);
            if (id.StartsWith('.')) continue;
            try
            {
                var path = PackStorage.Resolve(_modsRoot, PackStorage.ValidateId(id) + "/pack.json");
                var manifest = PackStorage.ReadManifest(path);
                if (manifest.Id == id && manifest.GameId == _game && manifest.SchemaVersion == 2)
                {
                    using var stream = File.OpenRead(path);
                    var hash = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
                    snapshot.Add(new(manifest.Id, manifest.GameId, manifest.Version, hash));
                }
            }
            catch (Exception error) when (error is IOException or InvalidDataException or JsonException or UnauthorizedAccessException)
            {
                // Manual packs with missing or invalid metadata are ineligible.
            }
        }
        return snapshot;
    }

    private CatalogWatermark? ReadWatermark()
    {
        PackStorage.EnsureNoLinks(_watermark);
        if (!File.Exists(_watermark)) return null;
        if (new FileInfo(_watermark).Length > 4096) throw new InvalidDataException("Invalid asset catalog history.");
        var value = JsonSerializer.Deserialize<CatalogWatermark>(File.ReadAllBytes(_watermark), RuntimeUpdates.Json);
        if (value == null || value.Sequence < 1 || value.Sha256 == null ||
            value.Sha256.Length != 64 || !value.Sha256.All(Uri.IsHexDigit))
        {
            throw new InvalidDataException("Invalid asset catalog history.");
        }
        return value;
    }

    private void WriteWatermark(CatalogWatermark value)
    {
        var temp = _watermark + "." + Guid.NewGuid().ToString("N");
        try
        {
            using (var stream = new FileStream(temp, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                JsonSerializer.Serialize(stream, value, RuntimeUpdates.Json);
                stream.Flush(flushToDisk: true);
            }
            File.Move(temp, _watermark, overwrite: true);
        }
        finally
        {
            if (File.Exists(temp)) File.Delete(temp);
        }
    }

    public void Dispose() => _downloader.Dispose();
}
