using System.Collections.ObjectModel;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core;

/// <summary>A non-executing file-integrity snapshot, not trusted-build or consumer admission.</summary>
public sealed class Mw3ReRuntimeContract
{
    private const long MaxClosureBytes = 4L * 1024 * 1024 * 1024;
    private const int MaxPlanningProfileBytes = 2 * 1024 * 1024;
    private readonly string profileRelativePath;
    private readonly long profileBytes;
    private readonly string profileSha256;

    public string Root { get; }
    public string Executable { get; }
    public string Profile { get; }
    public string SourceCommit { get; }
    public string BuildId { get; }
    public string Builder { get; }
    public IReadOnlyDictionary<string, string> Roles { get; }
    public IReadOnlyList<string> Dependencies { get; }
    public IReadOnlyDictionary<string, IReadOnlyList<int>> Capabilities { get; }

    private Mw3ReRuntimeContract(string root, Dictionary<string, string> roles,
        List<string> dependencies, Dictionary<string, IReadOnlyList<int>> capabilities,
        string sourceCommit, string buildId, string builder, Dictionary<string, string> paths,
        (long Bytes, string Sha256) profilePin)
    {
        Root = root;
        Executable = paths[roles["executable"]];
        Profile = paths[roles["profile"]];
        profileRelativePath = roles["profile"];
        profileBytes = profilePin.Bytes;
        profileSha256 = profilePin.Sha256;
        SourceCommit = sourceCommit;
        BuildId = buildId;
        Builder = builder;
        Roles = new ReadOnlyDictionary<string, string>(new Dictionary<string, string>(roles, StringComparer.Ordinal));
        Dependencies = Array.AsReadOnly(dependencies.ToArray());
        Capabilities = new ReadOnlyDictionary<string, IReadOnlyList<int>>(capabilities.ToDictionary(
            pair => pair.Key, pair => (IReadOnlyList<int>)Array.AsReadOnly(pair.Value.ToArray()), StringComparer.Ordinal));
    }

    /// <summary>Read planning text from one bounded snapshot checked against its original raw pin.</summary>
    internal string ReadPinnedPlanningProfile()
    {
        if (profileBytes > MaxPlanningProfileBytes)
            throw new InvalidDataException("Native planning profile is too large.");

        var path = PackStorage.Resolve(Root, profileRelativePath);
        var expectedBytes = (int)profileBytes;
        // One extra byte detects growth without reading an unbounded replacement file.
        var snapshot = new byte[expectedBytes + 1];
        int count = 0;
        using (var file = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            while (count < snapshot.Length)
            {
                var read = file.Read(snapshot, count, snapshot.Length - count);
                if (read == 0) break;
                count += read;
            }
        }
        if (count != expectedBytes)
            throw new InvalidDataException("Native planning profile size mismatch.");
        var bytes = snapshot.AsSpan(0, count);
        if (!Convert.ToHexString(SHA256.HashData(bytes)).Equals(profileSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Native planning profile hash mismatch.");

        // Hash the raw BOM too; decoding must never select another encoding implicitly.
        if ((bytes.Length >= 2 &&
                ((bytes[0] == 0xff && bytes[1] == 0xfe) ||
                 (bytes[0] == 0xfe && bytes[1] == 0xff))) ||
            (bytes.Length >= 4 && bytes[0] == 0 && bytes[1] == 0 &&
                bytes[2] == 0xfe && bytes[3] == 0xff))
            throw new InvalidDataException("Unsupported native planning profile encoding.");
        if (bytes.Length >= 3 && bytes[0] == 0xef && bytes[1] == 0xbb && bytes[2] == 0xbf)
            bytes = bytes[3..];
        try
        {
            return new UTF8Encoding(false, true).GetString(bytes);
        }
        catch (DecoderFallbackException)
        {
            throw new InvalidDataException("Invalid native planning profile encoding.");
        }
    }

    public static Mw3ReRuntimeContract ReadStructure(string runtimeRoot)
    {
        var root = Path.GetFullPath(runtimeRoot);
        var snapshot = NativeRuntimeLayout.ReadJsonSnapshot(PackStorage.Resolve(root, "runtime.json"));
        try
        {
            using var document = JsonDocument.Parse(snapshot, new JsonDocumentOptions { MaxDepth = 64 });
            var descriptor = document.RootElement;
            PackStorage.ValidateUniqueProperties(descriptor);
            RequireFields(descriptor, new[] { "schema_version", "engine", "roles", "dependencies", "files", "provenance", "capabilities" });
            if (Integer(descriptor.GetProperty("schema_version")) != 2 ||
                Text(descriptor.GetProperty("engine")) != "mw3-re")
                throw new InvalidDataException("Unsupported native runtime schema or engine.");

            var roleObject = descriptor.GetProperty("roles");
            RequireFields(roleObject, new[] { "executable", "profile" }, "coordinator", "python");
            var roles = new Dictionary<string, string>(StringComparer.Ordinal);
            var closure = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var role in roleObject.EnumerateObject())
            {
                var relative = Relative(role.Value);
                if (!closure.Add(relative)) throw new InvalidDataException("Duplicate native runtime role path.");
                roles.Add(role.Name, relative);
            }
            if (roles.ContainsKey("coordinator") != roles.ContainsKey("python"))
                throw new InvalidDataException("Native coordinator and Python roles must occur together.");

            var dependencyArray = descriptor.GetProperty("dependencies");
            if (dependencyArray.ValueKind != JsonValueKind.Array || dependencyArray.GetArrayLength() > 20000)
                throw new InvalidDataException("Invalid native dependency table.");
            var dependencies = new List<string>();
            foreach (var dependency in dependencyArray.EnumerateArray())
            {
                var relative = Relative(dependency);
                if (!closure.Add(relative)) throw new InvalidDataException("Duplicate or role-overlapping native dependency.");
                dependencies.Add(relative);
            }

            var fileObject = descriptor.GetProperty("files");
            if (fileObject.ValueKind != JsonValueKind.Object)
                throw new InvalidDataException("Invalid native file table.");
            var entries = fileObject.EnumerateObject().ToArray();
            if (entries.Length is < 1 or > 20000) throw new InvalidDataException("Excessive native file table.");
            var aliases = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var pins = new Dictionary<string, (long Bytes, string Sha256)>(StringComparer.Ordinal);
            long total = 0;
            foreach (var entry in entries)
            {
                PackStorage.ValidatePath(entry.Name);
                if (entry.Name.Equals("runtime.json", StringComparison.OrdinalIgnoreCase) || !aliases.Add(entry.Name))
                    throw new InvalidDataException("Native file table contains a self-pin or path alias.");
                RequireFields(entry.Value, new[] { "bytes", "sha256" });
                var bytes = Integer(entry.Value.GetProperty("bytes"));
                var sha256 = Text(entry.Value.GetProperty("sha256"));
                if (bytes <= 0 || bytes > MaxClosureBytes) throw new InvalidDataException("Invalid native file size.");
                if (!Regex.IsMatch(sha256, @"\A[0-9a-fA-F]{64}\z")) throw new InvalidDataException("Invalid native file hash.");
                total = checked(total + bytes);
                pins.Add(entry.Name, (bytes, sha256));
            }
            if (total > MaxClosureBytes) throw new InvalidDataException("Excessive native closure size.");
            // Exact spelling prevents roles from silently naming a case alias of a registered file.
            var exactClosure = new HashSet<string>(roles.Values.Concat(dependencies), StringComparer.Ordinal);
            if (!exactClosure.SetEquals(pins.Keys)) throw new InvalidDataException("Native file table does not equal its declared closure.");

            var provenance = descriptor.GetProperty("provenance");
            RequireFields(provenance, new[] { "source_commit", "build_id", "builder" });
            var sourceCommit = Text(provenance.GetProperty("source_commit"));
            if (!Regex.IsMatch(sourceCommit, @"\A[0-9a-f]{40}\z")) throw new InvalidDataException("Invalid native source provenance.");
            var buildId = PackStorage.ValidateId(Text(provenance.GetProperty("build_id")));
            var builder = PackStorage.ValidateId(Text(provenance.GetProperty("builder")));
            var capabilityObject = descriptor.GetProperty("capabilities");
            if (capabilityObject.ValueKind != JsonValueKind.Object || capabilityObject.EnumerateObject().Count() > 64)
                throw new InvalidDataException("Invalid native capability table.");
            var capabilities = new Dictionary<string, IReadOnlyList<int>>(StringComparer.Ordinal);
            foreach (var capability in capabilityObject.EnumerateObject())
            {
                PackStorage.ValidateId(capability.Name);
                var versions = capability.Value;
                if (versions.ValueKind != JsonValueKind.Array || versions.GetArrayLength() is < 1 or > 16)
                    throw new InvalidDataException("Invalid native capability versions.");
                var values = new List<int>();
                foreach (var item in versions.EnumerateArray())
                {
                    var version = Integer(item);
                    if (version <= 0 || version > int.MaxValue || values.Contains((int)version))
                        throw new InvalidDataException("Invalid or repeated native capability version.");
                    values.Add((int)version);
                }
                capabilities.Add(capability.Name, values);
            }

            // Admit all metadata/counts/budgets before opening any declared payload member.
            var paths = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (var (relative, pin) in pins)
            {
                var path = PackStorage.Resolve(root, relative);
                using var file = File.OpenRead(path);
                if (file.Length != pin.Bytes) throw new InvalidDataException("Native file size mismatch.");
                if (!Convert.ToHexString(SHA256.HashData(file)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Native file hash mismatch.");
                paths.Add(relative, path);
            }
            NativeRuntimeLayout.ValidateLaunchExecutable(paths[roles["executable"]]);
            return new Mw3ReRuntimeContract(root, roles, dependencies, capabilities, sourceCommit, buildId, builder, paths,
                pins[roles["profile"]]);
        }
        catch (Exception error) when (error is JsonException or InvalidOperationException or OverflowException)
        {
            throw new InvalidDataException("Invalid native runtime descriptor.");
        }
    }

    private static void RequireFields(JsonElement value, string[] required, params string[] optional)
    {
        if (value.ValueKind != JsonValueKind.Object) throw new InvalidDataException("Native descriptor field must be an object.");
        var allowed = new HashSet<string>(required.Concat(optional), StringComparer.Ordinal);
        if (value.EnumerateObject().Any(property => !allowed.Contains(property.Name)) ||
            required.Any(name => !value.TryGetProperty(name, out _)))
            throw new InvalidDataException("Native descriptor has missing or unknown fields.");
    }

    private static string Text(JsonElement value) => value.ValueKind == JsonValueKind.String
        ? value.GetString()! : throw new InvalidDataException("Native descriptor field must be a string.");

    private static long Integer(JsonElement value) => value.ValueKind == JsonValueKind.Number && value.TryGetInt64(out var number)
        ? number : throw new InvalidDataException("Native descriptor field must be an integer.");

    private static string Relative(JsonElement value)
    {
        var relative = Text(value);
        PackStorage.ValidatePath(relative);
        if (relative.Equals("runtime.json", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Native descriptor cannot pin itself.");
        return relative;
    }
}
