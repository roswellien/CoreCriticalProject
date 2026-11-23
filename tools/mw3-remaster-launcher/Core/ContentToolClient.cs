using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

/// <summary>The native content tool owns package semantics for every launcher.</summary>
public sealed class ContentToolClient
{
    public string Executable { get; }
    public ContentToolClient(string executable)
    {
        Executable = Path.GetFullPath(executable);
        if (!File.Exists(Executable)) throw new FileNotFoundException("Select the installed mw3content executable.", Executable);
    }

    public async Task<JsonObject> RunAsync(IEnumerable<string> arguments, CancellationToken cancellation = default)
    {
        var start = new ProcessStartInfo(Executable)
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardOutput = true, RedirectStandardError = true,
            WorkingDirectory = Path.GetDirectoryName(Executable)!
        };
        foreach (var argument in arguments) start.ArgumentList.Add(argument);
        using var process = Process.Start(start) ?? throw new IOException("Content tool did not start.");
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
        deadline.CancelAfter(TimeSpan.FromMinutes(2));
        try
        {
            var output = ReadBoundedAsync(process.StandardOutput, 4 * 1024 * 1024, deadline.Token);
            var errors = ReadBoundedAsync(process.StandardError, 64 * 1024, deadline.Token);
            await Task.WhenAll(output, errors, process.WaitForExitAsync(deadline.Token));
            var result = JsonNode.Parse(await output) as JsonObject
                ?? throw new InvalidDataException("Content tool did not return a JSON object.");
            if (process.ExitCode != 0 || result["ok"]?.GetValue<bool>() != true)
                throw new ContentToolException(result, await errors);
            return result;
        }
        finally
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
        }
    }

    private static async Task<string> ReadBoundedAsync(StreamReader reader, int limit, CancellationToken cancellation)
    {
        var result = new StringBuilder();
        var buffer = new char[4096];
        int count;
        while ((count = await reader.ReadAsync(buffer.AsMemory(), cancellation)) != 0)
        {
            if (result.Length + count > limit) throw new InvalidDataException("Content tool output exceeded its limit.");
            result.Append(buffer, 0, count);
        }
        return result.ToString();
    }
}

public sealed class ContentToolException : IOException
{
    public JsonObject Result { get; }
    public ContentToolException(JsonObject result, string stderr)
        : base(Describe(result, stderr)) => Result = result;

    private static string Describe(JsonObject result, string stderr)
    {
        if (result["diagnostics"] is JsonArray diagnostics && diagnostics.Count > 0)
            return string.Join(Environment.NewLine, diagnostics.Select(item =>
                $"{item?["code"]}: {item?["message"]} {item?["package"]} {item?["content"]} {item?["field"]} {item?["other_owner"]}"));
        return "Content tool rejected the request. " + stderr;
    }
}
