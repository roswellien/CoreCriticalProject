using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace MW3RemasterLauncher.Core;

public sealed record CrashReportResult(Uri IssueUrl, bool ExistingIssueUpdated);

/// <summary>Submit user-approved, redacted crash diagnostics to the project support endpoint.</summary>
public sealed class CrashReportService
{
    private static readonly Uri Endpoint = new("https://corecritical.dev/api/crash-reports");
    private static readonly HttpClient SharedClient = CreateClient();
    private readonly HttpClient _client;

    public CrashReportService(HttpClient? client = null)
    {
        _client = client ?? SharedClient;
    }

    private static HttpClient CreateClient()
    {
        var client = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
        client.DefaultRequestHeaders.UserAgent.ParseAdd("CoreCriticalLauncher-CrashReports/1.0");
        client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        return client;
    }

    public async Task<CrashReportResult> SubmitAsync(object report, CancellationToken cancellationToken = default)
    {
        using var response = await _client.PostAsJsonAsync(Endpoint, report, cancellationToken);
        var result = await response.Content.ReadFromJsonAsync<Response>(cancellationToken: cancellationToken);
        if (!response.IsSuccessStatusCode)
            throw new HttpRequestException(result?.Error ?? "The crash report service is unavailable.", null, response.StatusCode);
        if (result?.IssueUrl == null || !Uri.TryCreate(result.IssueUrl, UriKind.Absolute, out var issueUrl) ||
            issueUrl.Scheme != Uri.UriSchemeHttps || issueUrl.Host != "github.com")
            throw new InvalidDataException("The crash report service returned an invalid issue link.");

        return new CrashReportResult(issueUrl, result.Duplicate);
    }

    private sealed record Response(
        [property: JsonPropertyName("issue_url")] string? IssueUrl,
        bool Duplicate,
        string? Error);
}
