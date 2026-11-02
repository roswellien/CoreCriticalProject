using System.IO;
using System.Net;
using System.Net.Http;
using MW3RemasterLauncher.Core;

static class CrashReportServiceChecks
{
    public static async Task RunAsync()
    {
        using (var client = Client(HttpStatusCode.OK, """{"report_id":"ab12cd34","duplicate":false,"overflow":false}"""))
        {
            var result = await new CrashReportService(client).SubmitAsync(new { test = true });
            if (result.ReportId != "ab12cd34") throw new Exception("Valid crash report receipt was rejected.");
        }

        using (var client = Client(HttpStatusCode.Forbidden, "error code: 403"))
        {
            try
            {
                await new CrashReportService(client).SubmitAsync(new { test = true });
                throw new Exception("Non-JSON HTTP failure was accepted.");
            }
            catch (HttpRequestException error) when (error.StatusCode == HttpStatusCode.Forbidden &&
                error.Message.Contains("HTTP 403", StringComparison.Ordinal)) { }
        }

        using (var client = Client(HttpStatusCode.BadRequest, """{"error":"The report is invalid."}"""))
        {
            try
            {
                await new CrashReportService(client).SubmitAsync(new { test = true });
                throw new Exception("JSON HTTP failure was accepted.");
            }
            catch (HttpRequestException error) when (error.StatusCode == HttpStatusCode.BadRequest &&
                error.Message.Contains("The report is invalid.", StringComparison.Ordinal)) { }
        }

        using (var client = Client(HttpStatusCode.OK, "error code: 200"))
        {
            try
            {
                await new CrashReportService(client).SubmitAsync(new { test = true });
                throw new Exception("Malformed success response was accepted.");
            }
            catch (InvalidDataException error) when (error.Message.Contains("invalid JSON", StringComparison.Ordinal)) { }
        }
    }

    private static HttpClient Client(HttpStatusCode status, string body) => new(new StubHandler(status, body));

    private sealed class StubHandler(HttpStatusCode status, string body) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,
            CancellationToken cancellationToken) => Task.FromResult(new HttpResponseMessage(status)
            {
                Content = new StringContent(body),
            });
    }
}
