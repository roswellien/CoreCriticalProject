using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using MW3RemasterLauncher.Core;

static class UpdateDownloadChecks
{
    private sealed class Handler(Func<HttpRequestMessage, int, HttpResponseMessage> response) : HttpMessageHandler
    {
        public int Calls;
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellation) =>
            Task.FromResult(response(request, Calls++));
    }

    private sealed class InterruptedStream(byte[] bytes) : MemoryStream(bytes)
    {
        public override ValueTask<int> ReadAsync(Memory<byte> buffer, CancellationToken cancellation = default)
        {
            if (Position >= 4) throw new IOException("Authored interrupted connection");
            return base.ReadAsync(buffer[..Math.Min(4, buffer.Length)], cancellation);
        }
    }

    private sealed class StalledStream : MemoryStream
    {
        public override async ValueTask<int> ReadAsync(Memory<byte> buffer, CancellationToken cancellation = default)
        { await Task.Delay(Timeout.InfiniteTimeSpan, cancellation); return 0; }
    }

    public static async Task Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "CC update transfer " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        var config = new OnlineUpdateConfiguration(1, "https://updates.example.test/catalog.json", "playtest",
            "public-readonly-v1", new[] { "updates.example.test" });
        var bytes = "Authored fixture package"u8.ToArray();
        var artifact = new ReleaseArtifact("https://updates.example.test/mw3/1.0.38.zip", "1.0.38.zip", bytes.Length,
            Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant());
        HttpResponseMessage Response(byte[] body, HttpStatusCode status = HttpStatusCode.OK)
        {
            var value = new HttpResponseMessage(status) { Content = new ByteArrayContent(body) };
            value.Headers.ETag = new EntityTagHeaderValue("\"fixture-object\"");
            return value;
        }
        async Task Reject<T>(Func<Task> action) where T : Exception
        {
            try { await action(); } catch (T) { return; }
            throw new Exception("Unsafe/failed transfer was accepted: " + typeof(T).Name);
        }
        var phases = new List<UpdateTransferProgress>();
        try
        {
            var resumed = new Handler((request, count) =>
            {
                // The downloader must not hold a launch/install gate or installation mutation lock.
                using var gate = GameUpdateGate.Acquire(root);
                if (count == 0)
                    return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(new InterruptedStream(bytes)),
                        Headers = { ETag = new EntityTagHeaderValue("\"fixture-object\"") } };
                if (request.Headers.Range?.ToString() != "bytes=4-" || request.Headers.IfRange?.ToString() != "\"fixture-object\"")
                    throw new Exception("Interrupted download did not send bounded Range/If-Range.");
                var reply = Response(bytes[4..], HttpStatusCode.PartialContent);
                reply.Content.Headers.ContentRange = new ContentRangeHeaderValue(4, bytes.Length - 1, bytes.Length);
                return reply;
            });
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: resumed))
            {
                var file = await downloader.DownloadAsync("mw3", 1, artifact, new InlineProgress(phases));
                if (!File.ReadAllBytes(file).SequenceEqual(bytes) || resumed.Calls != 2 || phases.Last().Phase != "Ready")
                    throw new Exception("Resumed download did not verify the complete artifact.");
                await downloader.DownloadAsync("mw3", 1, artifact);
                if (resumed.Calls != 2) throw new Exception("Verified cache was unnecessarily downloaded again.");
                File.WriteAllBytes(file, new byte[bytes.Length]);
                await Reject<InvalidDataException>(() => downloader.DownloadAsync("mw3", 1, artifact));
            }
            var fullRestart = new Handler((request, count) => count == 0
                ? new(HttpStatusCode.OK) { Content = new StreamContent(new InterruptedStream(bytes)), Headers = { ETag = new("\"fixture-object\"") } }
                : Response(bytes));
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: fullRestart))
                await downloader.DownloadAsync("mw3", 2, artifact); // A server ignoring Range must restart, not append.
            var invalidRange = new Handler((request, count) =>
            {
                if (count == 0) return new(HttpStatusCode.OK) { Content = new StreamContent(new InterruptedStream(bytes)), Headers = { ETag = new("\"fixture-object\"") } };
                var reply = Response(bytes[4..], HttpStatusCode.PartialContent);
                reply.Content.Headers.ContentRange = new ContentRangeHeaderValue(3, bytes.Length - 2, bytes.Length);
                return reply;
            });
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: invalidRange))
                await Reject<InvalidDataException>(() => downloader.DownloadAsync("mw3", 3, artifact));
            var login = new Handler((request, count) => new(HttpStatusCode.Found) { Headers = { Location = new Uri("https://team.cloudflareaccess.com/login") } });
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: login))
            {
                await Reject<UpdateSignInRequiredException>(() => downloader.DownloadAsync("mw3", 4, artifact));
                if (login.Calls != 1) throw new Exception("Access redirect was followed or retried as a package.");
            }
            var html = new Handler((request, count) => new(HttpStatusCode.OK) { Content = new StringContent("<html>Login</html>", System.Text.Encoding.UTF8, "text/html") });
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: html))
                await Reject<UpdateSignInRequiredException>(() => downloader.FetchCatalogAsync());
            var wrong = new Handler((request, count) => Response(new byte[bytes.Length]));
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: wrong))
                await Reject<InvalidDataException>(() => downloader.DownloadAsync("mw3", 5, artifact));
            var tooLarge = new Handler((request, count) => Response(new byte[bytes.Length + 1]));
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: tooLarge))
                await Reject<InvalidDataException>(() => downloader.DownloadAsync("mw3", 6, artifact));
            HttpResponseMessage Stalled()
            {
                var response = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(new StalledStream()) };
                response.Content.Headers.ContentLength = bytes.Length;
                return response;
            }
            var stalled = new Handler((request, count) => Stalled());
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: stalled, inactivityTimeout: TimeSpan.FromMilliseconds(20)))
                await Reject<IOException>(() => downloader.DownloadAsync("mw3", 7, artifact));
            var cancelled = new Handler((request, count) => Stalled());
            using (var downloader = new OnlineUpdateDownloader(root, config, root, handler: cancelled))
            using (var cancel = new CancellationTokenSource(TimeSpan.FromMilliseconds(20)))
            {
                await Reject<OperationCanceledException>(() => downloader.DownloadAsync("mw3", 8, artifact, cancellation: cancel.Token));
                if (cancelled.Calls != 1) throw new Exception("User cancellation retried a network request.");
            }
            using (var first = GameUpdateGate.Acquire(root))
            {
                try { using var second = GameUpdateGate.Acquire(root); throw new Exception("Launch/install gate admitted simultaneous owners."); }
                catch (InvalidOperationException) { }
            }
            using (GameUpdateGate.Acquire(root)) { }
        }
        finally { Directory.Delete(root, true); }
        Console.WriteLine("Update transfer checks passed: byte progress, interrupted Range resume, full-response restart, malformed range, cache tampering, size/hash rejection, Access/HTML detection, inactivity/cancellation and launch/install exclusion.");
    }

    private sealed class InlineProgress(List<UpdateTransferProgress> output) : IProgress<UpdateTransferProgress>
    { public void Report(UpdateTransferProgress value) => output.Add(value); }
}
