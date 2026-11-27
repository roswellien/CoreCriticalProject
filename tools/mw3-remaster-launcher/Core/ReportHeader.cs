using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>
/// The playtest report's setup header: facts reports kept lacking (Vulkan device, video
/// memory heaps, display mode, pack texture sizes, input devices). The keys and types match
/// what the crash-report service keeps (website/functions/_lib/crash-report-header.js).
/// </summary>
/// <remarks>
/// The game prints its facts in mw3.log as lines containing "mw3: header " followed by one of:
/// <code>
/// vulkan_device=&lt;text&gt;
/// vulkan_api_version=&lt;text&gt;
/// vulkan_driver_version=&lt;text&gt;
/// heap index=&lt;n&gt; size_bytes=&lt;n&gt; budget_bytes=&lt;n&gt; device_local=&lt;0|1&gt;
/// resolution=&lt;w&gt;x&lt;h&gt;
/// window_mode=&lt;text&gt;
/// refresh_hz=&lt;n&gt;
/// hdr=&lt;0|1&gt;
/// </code>
/// That format is the contract the game must print. Anything before "mw3: header " (a time
/// or level stamp) is ignored, unknown keys and malformed values are skipped, and a key's
/// first value wins. A game that prints none of these gives a header of launcher facts only.
/// </remarks>
public static class ReportHeader
{
    /// <summary>Only the log's start is scanned: the game prints its header lines at startup.</summary>
    public const int ScannedLogBytes = 64 * 1024;

    /// <summary>Every string is cut to this, per the spec; the service's longer limits are a backstop.</summary>
    public const int MaxTextLength = 80;

    private const string HeaderMarker = "mw3: header ";
    private const int MaxHeaps = 16;
    private const int MaxRefreshHz = 1000;

    private static readonly string[] TextureExtensions = { ".dds", ".png", ".tga", ".bmp", ".ktx2" };
    private static readonly string[] TextKeys = { "vulkan_device", "vulkan_api_version", "vulkan_driver_version", "window_mode" };
    private static readonly Regex Resolution = new(@"\A[0-9]{1,5}x[0-9]{1,5}\z", RegexOptions.CultureInvariant);

    /// <summary>
    /// The header fields found. <paramref name="sessionGameLog"/> is the session's copy of
    /// mw3.log (or null); <paramref name="packs"/> are the session's packs, of which only the
    /// enabled ones with a file list count; <paramref name="inputDevices"/> are the product
    /// names of attached DirectInput devices.
    /// </summary>
    public static Dictionary<string, object> Build(string? sessionGameLog, IEnumerable<PackManifest> packs,
        IReadOnlyList<string> inputDevices, string[] roots)
    {
        var header = new Dictionary<string, object>();
        foreach (var line in ReadScannedLines(sessionGameLog))
            AddGameLine(header, line, roots);

        var packTextures = PackTextureBytes(packs, roots);
        if (packTextures.Count > 0) header["pack_texture_bytes"] = packTextures;

        var devices = inputDevices
            .Where(name => !string.IsNullOrWhiteSpace(name))
            .Select(name => CleanText(name, roots))
            .ToList();
        if (devices.Count > 0) header["input_devices"] = devices;
        return header;
    }

    private static IEnumerable<string> ReadScannedLines(string? path)
    {
        if (string.IsNullOrEmpty(path)) return Array.Empty<string>();
        try
        {
            if (!File.Exists(path)) return Array.Empty<string>();
            PackStorage.EnsureNoLinks(path);
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            var buffer = new byte[(int)Math.Min(ScannedLogBytes, stream.Length)];
            var length = 0;
            int count;
            while (length < buffer.Length && (count = stream.Read(buffer, length, buffer.Length - length)) != 0)
                length += count;
            return Encoding.UTF8.GetString(buffer, 0, length).Split('\n');
        }
        catch
        {
            return Array.Empty<string>();
        }
    }

    private static void AddGameLine(Dictionary<string, object> header, string line, string[] roots)
    {
        var marker = line.IndexOf(HeaderMarker, StringComparison.Ordinal);
        if (marker < 0) return;
        var fact = line[(marker + HeaderMarker.Length)..].Trim();

        if (fact.StartsWith("heap ", StringComparison.Ordinal))
        {
            AddHeap(header, fact["heap ".Length..]);
            return;
        }

        var equals = fact.IndexOf('=');
        if (equals <= 0) return;
        var key = fact[..equals];
        var value = fact[(equals + 1)..].Trim();
        if (value.Length == 0 || header.ContainsKey(key)) return;

        if (TextKeys.Contains(key))
            header[key] = CleanText(value, roots);
        else if (key == "resolution" && Resolution.IsMatch(value))
            header[key] = value;
        else if (key == "refresh_hz" && int.TryParse(value, out var hz) && hz >= 0 && hz <= MaxRefreshHz)
            header[key] = hz;
        else if (key == "hdr" && TryParseFlag(value, out var hdr))
            header[key] = hdr;
    }

    /// <summary>Adds one heap row; a row is only useful with both its size and its budget.</summary>
    private static void AddHeap(Dictionary<string, object> header, string fields)
    {
        var values = new Dictionary<string, string>();
        foreach (var token in fields.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            var equals = token.IndexOf('=');
            if (equals > 0) values.TryAdd(token[..equals], token[(equals + 1)..]);
        }

        long size = -1;
        long budget = -1;
        var hasSize = values.TryGetValue("size_bytes", out var sizeText) && long.TryParse(sizeText, out size);
        var hasBudget = values.TryGetValue("budget_bytes", out var budgetText) && long.TryParse(budgetText, out budget);
        if (!hasSize || !hasBudget || size < 0 || budget < 0) return;

        var heaps = header.TryGetValue("heaps", out var existing) && existing is List<Dictionary<string, object>> list
            ? list
            : new List<Dictionary<string, object>>();
        if (heaps.Count >= MaxHeaps) return;

        var heap = new Dictionary<string, object>();
        if (values.TryGetValue("index", out var indexText) && int.TryParse(indexText, out var index) && index >= 0 && index <= 64)
            heap["index"] = index;
        heap["size_bytes"] = size;
        heap["budget_bytes"] = budget;
        if (values.TryGetValue("device_local", out var localText) && TryParseFlag(localText, out var deviceLocal))
            heap["device_local"] = deviceLocal;
        heaps.Add(heap);
        header["heaps"] = heaps;
    }

    /// <summary>
    /// For each enabled pack with a file list, the bytes of its texture files. This reads the
    /// manifest already in memory, so Export still walks no directories.
    /// </summary>
    private static List<Dictionary<string, object>> PackTextureBytes(IEnumerable<PackManifest> packs, string[] roots)
    {
        var result = new List<Dictionary<string, object>>();
        foreach (var pack in packs)
        {
            if (!pack.IsEnabled || pack.Files == null) continue;
            long textureBytes = 0;
            foreach (var (name, file) in pack.Files)
            {
                var isTexture = TextureExtensions.Any(extension => name.EndsWith(extension, StringComparison.OrdinalIgnoreCase));
                if (isTexture && file.Bytes > 0) textureBytes += file.Bytes;
            }
            result.Add(new Dictionary<string, object> { ["id"] = CleanText(pack.Id, roots), ["bytes"] = textureBytes });
        }
        return result;
    }

    private static bool TryParseFlag(string text, out bool flag)
    {
        flag = text == "1";
        return text is "0" or "1";
    }

    private static string CleanText(string text, string[] roots)
    {
        var redacted = PlaytestDiagnostics.Redact(text.Trim(), roots);
        return redacted.Length <= MaxTextLength ? redacted : redacted[..MaxTextLength];
    }
}
