using System.IO;
using System.Security.Cryptography;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

public sealed record PendingOnlineUpdates(int SchemaVersion, string Application, string Channel,
    string CatalogEnvelope, string[] Products, string? LauncherJob);

/// <summary>Coordinates discovery/downloads and separate launcher/runtime transactions, including restart continuation.</summary>
public sealed class OnlineUpdateService : IDisposable
{
    private sealed record CatalogWatermark(long Sequence, string Hash);
    private readonly string _application;
    private readonly string _game;
    private readonly string _dataRoot;
    private readonly OnlineUpdateConfiguration _config;
    private readonly RuntimeUpdateTrust _trust;
    private readonly OnlineUpdateDownloader _downloader;
    private readonly string _workflow;
    public VerifiedReleaseCatalog? Catalog { get; private set; }
    public IReadOnlyList<PlannedOnlineUpdate> Available { get; private set; } = Array.Empty<PlannedOnlineUpdate>();
    public string Channel => _config.Channel;
    public string PendingFile => Path.Combine(_workflow, "pending.json");

    public OnlineUpdateService(string application, string game, string? dataRoot = null)
    {
        _application = Path.TrimEndingDirectorySeparator(Path.GetFullPath(application));
        _game = game;
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
        _config = OnlineUpdateConfiguration.Read(_application);
        _trust = RuntimeUpdates.ReadTrust(_application);
        _downloader = new(_application, _config, _dataRoot);
        _workflow = Path.Combine(_downloader.Store, _config.Channel);
        PackStorage.EnsureNoLinks(_workflow);
        Directory.CreateDirectory(_workflow);
    }

    private FileStream Lock() => new(Path.Combine(_workflow, ".workflow-lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    private static T Read<T>(string path)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 3 * 1024 * 1024) throw new InvalidDataException("Saved update state is too large.");
        return JsonSerializer.Deserialize<T>(File.ReadAllBytes(path), RuntimeUpdates.Json) ?? throw new InvalidDataException("Empty saved update state.");
    }
    private static void Write<T>(string path, T value)
    {
        PackStorage.EnsureNoLinks(path);
        var temporary = path + "." + Guid.NewGuid().ToString("N");
        using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        { JsonSerializer.Serialize(output, value, RuntimeUpdates.Json); output.Flush(true); }
        File.Move(temporary, path, true);
    }

    public static string InstalledRuntimeVersion(string application, string? dataRoot = null, bool bundled = false)
    {
        var root = bundled ? Path.Combine(application, "Runtime") :
            RuntimeUpdates.SelectedRoot(application, dataRoot) ?? Path.Combine(application, "Runtime");
        var path = Path.Combine(root, "runtime.json");
        if (!File.Exists(path)) return "not installed";
        using var doc = JsonDocument.Parse(LauncherUpdates.ReadMetadata(path));
        return doc.RootElement.TryGetProperty("version", out var version) ? version.GetString() ?? "unknown" : "unknown";
    }

    private IReadOnlyList<InstalledUpdateProduct> Installed()
    {
        var launcher = new LauncherUpdates(_application, _trust, _dataRoot);
        var products = new List<InstalledUpdateProduct> { new(GameCatalog.LauncherId,
            typeof(OnlineUpdateService).Assembly.GetName().Version!.ToString(3), launcher.InstalledSequence) };
        if (GameValidator.Validate(_game).IsValid)
        {
            var runtime = InstalledRuntimeVersion(_application, _dataRoot);
            if (runtime == "not installed") runtime = "0.0.0";
            products.Add(new(GameCatalog.Mw3, runtime, new RuntimeUpdates(_application, _trust, _dataRoot).State().HighestSequence));
        }
        return products;
    }

    public async Task CheckAsync(CancellationToken cancellation = default)
    {
        using var operation = Lock();
        await CheckCoreAsync(cancellation);
    }

    private async Task CheckCoreAsync(CancellationToken cancellation)
    {
        Catalog = null; Available = Array.Empty<PlannedOnlineUpdate>();
        var path = Path.Combine(_workflow, "catalog-watermark.json");
        var watermark = File.Exists(path) ? Read<CatalogWatermark>(path) : new(0, "");
        var envelope = await _downloader.FetchCatalogAsync(cancellation);
        var catalog = ReleaseCatalog.Verify(envelope, _trust, _config, DateTimeOffset.UtcNow, watermark.Sequence, watermark.Hash);
        var plan = OnlineUpdatePlanner.Plan(catalog, typeof(OnlineUpdateService).Assembly.GetName().Version!, Installed());
        Write(path, new CatalogWatermark(catalog.Document.Sequence, catalog.PayloadSha256));
        Catalog = catalog; Available = plan;
    }

    public bool HasPending => File.Exists(PendingFile);

    private PendingOnlineUpdates Pending()
    {
        var plan = Read<PendingOnlineUpdates>(PendingFile);
        if (plan.SchemaVersion != 1 || plan.Application != _application || plan.Channel != _config.Channel ||
            plan.Products.Length is < 1 or > 6 || plan.Products.Distinct().Count() != plan.Products.Length)
            throw new InvalidDataException("Saved update plan belongs to a different installation or channel.");
        return plan;
    }

    private OnlineRelease[] RevalidatePending(PendingOnlineUpdates plan)
    {
        if (Catalog == null) throw new InvalidOperationException("Check for updates before continuing.");
        var saved = ReleaseCatalog.Verify(Convert.FromBase64String(plan.CatalogEnvelope), _trust, _config, DateTimeOffset.UtcNow);
        var releases = new List<OnlineRelease>();
        foreach (var product in plan.Products)
        {
            var old = saved.Document.Releases.Single(r => r.ProductId == product);
            var current = Catalog.Document.Releases.SingleOrDefault(r => r.ProductId == product);
            if (current == null || current.Sequence != old.Sequence || current.Metadata != old.Metadata || current.Payload != old.Payload)
                throw new InvalidDataException("This saved update is no longer the promoted release. Check for updates and select the current release.");
            releases.Add(current);
        }
        return releases.OrderBy(r => r.ProductId == GameCatalog.LauncherId ? 0 : 1).ToArray();
    }

    public async Task DownloadAsync(string[]? products, IProgress<UpdateTransferProgress>? progress, CancellationToken cancellation)
    {
        using var operation = Lock();
        await CheckCoreAsync(cancellation);
        PendingOnlineUpdates pending;
        if (products == null) pending = Pending();
        else
        {
            if (products.Length == 0 || products.Distinct().Count() != products.Length ||
                products.Any(id => !Available.Any(p => p.Release.ProductId == id && p.BlockedReason == null)))
                throw new InvalidDataException("Select an available compatible update first.");
            // Include a required launcher transaction if the user selected its dependent runtime.
            var selected = Available.Where(p => products.Contains(p.Release.ProductId)).ToList();
            if (selected.Any(p => Version.Parse(p.Release.MinimumLauncherVersion) > typeof(OnlineUpdateService).Assembly.GetName().Version))
            {
                var launcher = Available.SingleOrDefault(p => p.Release.ProductId == GameCatalog.LauncherId && p.BlockedReason == null)
                    ?? throw new InvalidDataException("Install the current full launcher installer first.");
                if (!selected.Contains(launcher)) selected.Insert(0, launcher);
            }
            pending = new(1, _application, Channel, Convert.ToBase64String(Catalog!.Envelope), selected.Select(p => p.Release.ProductId).ToArray(), null);
            Write(PendingFile, pending);
        }
        foreach (var release in RevalidatePending(pending))
        {
            await _downloader.DownloadAsync(release.ProductId, release.Sequence, release.Metadata, progress, cancellation);
            await _downloader.DownloadAsync(release.ProductId, release.Sequence, release.Payload, progress, cancellation);
        }
    }

    /// <returns>True only when a launcher helper started and the calling launcher must close.</returns>
    public async Task<bool> InstallAsync(IProgress<string>? progress, CancellationToken cancellation)
    {
        using var operation = Lock();
        await CheckCoreAsync(cancellation); // An offline/stale check cannot advance an interrupted transaction.
        var pending = Pending();
        var releases = RevalidatePending(pending);
        var currentVersion = typeof(OnlineUpdateService).Assembly.GetName().Version!;
        foreach (var release in releases)
        {
            if (release.ProductId == GameCatalog.LauncherId && currentVersion >= Version.Parse(release.NumericVersion))
            {
                if (pending.LauncherJob != null) VerifyHelperResult(pending.LauncherJob, release);
                continue;
            }
            if (release.ProductId != GameCatalog.LauncherId)
            {
                var runtimeState = new RuntimeUpdates(_application, _trust, _dataRoot).State();
                if (runtimeState.Active == release.Version && runtimeState.HighestSequence >= release.Sequence) continue;
            }
            // Cache hits are fully rehashed; missing artifacts can finish downloading before taking any install gate.
            var metadata = await _downloader.DownloadAsync(release.ProductId, release.Sequence, release.Metadata, cancellation: cancellation);
            var payload = await _downloader.DownloadAsync(release.ProductId, release.Sequence, release.Payload, cancellation: cancellation);
            if (release.ProductId == GameCatalog.LauncherId)
            {
                progress?.Report("Verifying launcher installer and preparing restart…");
                var updates = new LauncherUpdates(_application, _trust, _dataRoot);
                var candidate = ReleaseCatalog.VerifyLauncherPackage(release, LauncherUpdates.ReadMetadata(metadata), updates);
                var job = updates.Stage(candidate, payload);
                Write(PendingFile, pending with { LauncherJob = job });
                LauncherUpdates.StartHelper(job);
                return true;
            }
            else
            {
                LauncherUpdates.RequireGamesClosed();
                var updates = new RuntimeUpdates(_application, _trust, _dataRoot);
                var candidate = ReleaseCatalog.VerifyRuntimePackage(release, LauncherUpdates.ReadMetadata(metadata), updates);
                await updates.PrepareAsync(candidate, _game, payload, progress, cancellation);
            }
        }
        File.Delete(PendingFile);
        progress?.Report("Updates complete. Your selected runtime is ready to play.");
        return false;
    }

    private void VerifyHelperResult(string job, OnlineRelease release)
    {
        var store = new LauncherUpdates(_application, _trust, _dataRoot).Store;
        var stage = Path.GetDirectoryName(Path.GetFullPath(job))!;
        if (Path.GetDirectoryName(stage) != store || Path.GetFileName(job) != "job.json")
            throw new InvalidDataException("Saved launcher result is outside the owned update store.");
        var result = Path.Combine(stage, "result.txt");
        PackStorage.EnsureNoLinks(result);
        if (!File.Exists(result) || new FileInfo(result).Length > 4096 ||
            File.ReadAllText(result) != "Core Critical updated to " + release.NumericVersion)
            throw new InvalidDataException("The launcher helper did not confirm a successful update. Repair the launcher using the signed installer, then retry.");
        ReleaseCatalog.VerifyArtifact(Path.Combine(stage, "update.ccupdate"), release.Metadata);
    }

    public void Dispose() => _downloader.Dispose();
}
