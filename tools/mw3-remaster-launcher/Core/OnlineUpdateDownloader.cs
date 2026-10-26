using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

public sealed record UpdateTransferProgress(string Phase, long Bytes, long Total);
public sealed class UpdateSignInRequiredException : IOException
{
    public UpdateSignInRequiredException() : base("Sign in to the playtest update service, then retry. Your installed games remain available.") { }
}

/// <summary>Authorization is supplied per approved request, never embedded in catalog or cache files.</summary>
public interface IUpdateDeliveryAuthorization
{
    Task AuthorizeAsync(HttpRequestMessage request, CancellationToken cancellation);
}

/// <summary>Bounded downloads outside installer locks. Ready files always pass complete size/hash verification.</summary>
public sealed class OnlineUpdateDownloader : IDisposable
{
    private sealed record ResumeIdentity(string Sha256, long Bytes, string Etag);
    private readonly OnlineUpdateConfiguration _config;
    private readonly HttpClient _client;
    private readonly IUpdateDeliveryAuthorization? _authorization;
    private readonly TimeSpan _inactivity;
    public string Store { get; }

    public OnlineUpdateDownloader(string application, OnlineUpdateConfiguration config, string? dataRoot = null,
        IUpdateDeliveryAuthorization? authorization = null, HttpMessageHandler? handler = null, TimeSpan? inactivityTimeout = null)
    {
        config.Validate();
        _config = config;
        _authorization = authorization;
        _inactivity = inactivityTimeout ?? TimeSpan.FromSeconds(30);
        _client = new HttpClient(handler ?? new HttpClientHandler { AllowAutoRedirect = false }) { Timeout = Timeout.InfiniteTimeSpan };
        var identity = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(
            Path.TrimEndingDirectorySeparator(Path.GetFullPath(application)).ToUpperInvariant())))[..24].ToLowerInvariant();
        Store = Path.Combine(dataRoot ?? LauncherPaths.DataRoot, "online-updates", identity);
    }

    public async Task<byte[]> FetchCatalogAsync(CancellationToken cancellation = default)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, _config.Destination(_config.CatalogUrl));
        request.Headers.CacheControl = new CacheControlHeaderValue { NoCache = true, NoStore = true };
        using var response = await SendAsync(request, cancellation);
        RequireDownload(response);
        if (response.Content.Headers.ContentLength > ReleaseCatalog.MaximumMetadataBytes)
            throw new InvalidDataException("Release catalog is too large.");
        using var output = new MemoryStream();
        await CopyAsync(await response.Content.ReadAsStreamAsync(cancellation), output, 0,
            ReleaseCatalog.MaximumMetadataBytes, null, cancellation);
        return output.ToArray();
    }

    public async Task<string> DownloadAsync(string product, long sequence, ReleaseArtifact artifact,
        IProgress<UpdateTransferProgress>? progress = null, CancellationToken cancellation = default)
    {
        PackStorage.ValidateId(product);
        if (sequence < 1 || artifact.Bytes < 1 || artifact.Bytes > ReleaseCatalog.MaximumPayloadBytes ||
            artifact.Sha256.Length != 64 || !artifact.Sha256.All(Uri.IsHexDigit) ||
            artifact.Filename != Path.GetFileName(artifact.Filename))
            throw new InvalidDataException("Invalid update download identity.");
        PackStorage.ValidatePath(artifact.Filename);
        var address = _config.Destination(artifact.Url);
        var directory = PackStorage.Resolve(Store, product + "/" + sequence + "/" + artifact.Sha256.ToLowerInvariant());
        PackStorage.EnsureNoLinks(directory);
        Directory.CreateDirectory(directory);
        using var downloadLock = new FileStream(Path.Combine(directory, ".download-lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        var ready = PackStorage.Resolve(directory, artifact.Filename);
        var partial = ready + ".partial";
        var identityFile = ready + ".resume.json";
        PackStorage.EnsureNoLinks(ready); PackStorage.EnsureNoLinks(partial); PackStorage.EnsureNoLinks(identityFile);
        if (File.Exists(ready))
        {
            ReleaseCatalog.VerifyArtifact(ready, artifact);
            progress?.Report(new("Ready", artifact.Bytes, artifact.Bytes));
            return ready;
        }
        for (var attempt = 0; attempt < 3; attempt++)
        {
            cancellation.ThrowIfCancellationRequested();
            try
            {
                var offset = File.Exists(partial) ? new FileInfo(partial).Length : 0;
                string? etag = null;
                if (File.Exists(identityFile) && new FileInfo(identityFile).Length <= 4096)
                {
                    var resume = JsonSerializer.Deserialize<ResumeIdentity>(File.ReadAllBytes(identityFile), RuntimeUpdates.Json);
                    if (resume?.Sha256 == artifact.Sha256 && resume.Bytes == artifact.Bytes &&
                        EntityTagHeaderValue.TryParse(resume.Etag, out var tag) && !tag.IsWeak) etag = tag.ToString();
                }
                if (offset > artifact.Bytes || etag == null) offset = 0;
                var remaining = artifact.Bytes - offset;
                if (new DriveInfo(Path.GetPathRoot(directory)!).AvailableFreeSpace < remaining + 32L * 1024 * 1024)
                    throw new InvalidDataException("Not enough free space to download this update. Free disk space and retry.");
                using var request = new HttpRequestMessage(HttpMethod.Get, address);
                if (offset > 0)
                {
                    request.Headers.Range = new RangeHeaderValue(offset, null);
                    request.Headers.IfRange = new RangeConditionHeaderValue(EntityTagHeaderValue.Parse(etag!));
                }
                using var response = await SendAsync(request, cancellation);
                if (response.StatusCode == HttpStatusCode.RequestedRangeNotSatisfiable)
                {
                    if (offset == artifact.Bytes)
                    {
                        ReleaseCatalog.VerifyArtifact(partial, artifact);
                        File.Move(partial, ready); return ready;
                    }
                    File.Delete(identityFile);
                    using (File.Create(partial)) { }
                    continue;
                }
                RequireDownload(response);
                if (response.StatusCode == HttpStatusCode.PartialContent)
                {
                    var range = response.Content.Headers.ContentRange;
                    if (offset == 0 || etag == null || response.Headers.ETag?.ToString() != etag ||
                        range == null || range.Unit != "bytes" || range.From != offset || range.Length != artifact.Bytes ||
                        range.To != artifact.Bytes - 1)
                        throw new InvalidDataException("The server returned an invalid resumed download. Retry with a fresh download.");
                }
                else if (response.StatusCode == HttpStatusCode.OK) offset = 0;
                else throw new InvalidDataException("Unsupported update download response.");
                if (response.Content.Headers.ContentLength is { } length && length != artifact.Bytes - offset)
                    throw new InvalidDataException("Update download length disagrees with its signed size.");
                var validator = response.Headers.ETag;
                if (validator is { IsWeak: false } && validator.ToString().Length <= 256)
                    File.WriteAllBytes(identityFile, JsonSerializer.SerializeToUtf8Bytes(new ResumeIdentity(artifact.Sha256, artifact.Bytes, validator.ToString()), RuntimeUpdates.Json));
                else File.Delete(identityFile);
                using (var output = new FileStream(partial, offset == 0 ? FileMode.Create : FileMode.Open, FileAccess.Write, FileShare.None, 81920, true))
                {
                    output.Position = offset;
                    progress?.Report(new("Downloading", offset, artifact.Bytes));
                    await CopyAsync(await response.Content.ReadAsStreamAsync(cancellation), output, offset, artifact.Bytes, progress, cancellation);
                    await output.FlushAsync(cancellation);
                    output.Flush(true);
                }
                if (new FileInfo(partial).Length != artifact.Bytes)
                    throw new IOException("Update download ended early. Retrying the transfer.");
                progress?.Report(new("Verifying", artifact.Bytes, artifact.Bytes));
                try { ReleaseCatalog.VerifyArtifact(partial, artifact); }
                catch (InvalidDataException) { File.Delete(identityFile); throw; }
                cancellation.ThrowIfCancellationRequested();
                File.Move(partial, ready);
                File.Delete(identityFile);
                progress?.Report(new("Ready", artifact.Bytes, artifact.Bytes));
                return ready;
            }
            catch (Exception error) when ((error is HttpRequestException || error is IOException && error is not (InvalidDataException or UpdateSignInRequiredException) ||
                error is OperationCanceledException && !cancellation.IsCancellationRequested) && attempt < 2)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(250 * (1 << attempt)), cancellation);
            }
            catch (OperationCanceledException error) when (!cancellation.IsCancellationRequested)
            {
                throw new IOException("The update connection stalled. Retry to resume the download.", error);
            }
        }
        throw new IOException("The server could not resume this download. Retry the update download.");
    }

    private async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellation)
    {
        _config.Destination(request.RequestUri!.AbsoluteUri);
        if (_authorization != null) await _authorization.AuthorizeAsync(request, cancellation);
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
        timeout.CancelAfter(_inactivity);
        return await _client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, timeout.Token);
    }

    private static void RequireDownload(HttpResponseMessage response)
    {
        if (response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden ||
            ((int)response.StatusCode is >= 300 and < 400 && response.Headers.Location is { IsAbsoluteUri: true } location && location.Host.EndsWith(".cloudflareaccess.com", StringComparison.OrdinalIgnoreCase)) ||
            response.Content.Headers.ContentType?.MediaType == "text/html")
            throw new UpdateSignInRequiredException();
        if ((int)response.StatusCode is >= 300 and < 400)
            throw new InvalidDataException("Update delivery redirected to another address. Retry or use a local signed update.");
        response.EnsureSuccessStatusCode();
    }

    private async Task CopyAsync(Stream input, Stream output, long offset, long limit,
        IProgress<UpdateTransferProgress>? progress, CancellationToken cancellation)
    {
        using (input)
        {
            var buffer = new byte[81920];
            var total = offset;
            while (true)
            {
                using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
                timeout.CancelAfter(_inactivity);
                var count = await input.ReadAsync(buffer, timeout.Token);
                if (count == 0) break;
                total = checked(total + count);
                if (total > limit) throw new InvalidDataException("Update download exceeds its declared size.");
                await output.WriteAsync(buffer.AsMemory(0, count), cancellation);
                progress?.Report(new("Downloading", total, limit));
            }
        }
    }

    public void Dispose() => _client.Dispose();
}
