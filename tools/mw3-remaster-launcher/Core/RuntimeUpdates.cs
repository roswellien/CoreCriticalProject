using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Nodes;

namespace MW3RemasterLauncher.Core;

public sealed record UpdateFile(long Bytes, string Sha256);
public sealed record RuntimeUpdateManifest(int SchemaVersion, string Version, long Sequence,
    string MinimumLauncherVersion, string PreparationContract, string PackageUrl,
    long PackageBytes, string PackageSha256, string Preparer,
    Dictionary<string, UpdateFile> Files, Dictionary<string, UpdateFile> OriginalInputs,
    string GameId = GameCatalog.Mw3);
public sealed record VerifiedRuntimeUpdate(RuntimeUpdateManifest Manifest, string ManifestSha256, string SignedEnvelope);
public sealed record RuntimeUpdateTrust(string FeedUrl, Dictionary<string, string> PublicKeys);
public sealed record RuntimeUpdateState(string? Active, string? Previous, long HighestSequence);

/// <summary>Signed source/tool updates produce local runtime versions; activation changes one atomic pointer.</summary>
public sealed class RuntimeUpdates
{
    internal static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow };
    private const long MaxPackageBytes = 512L * 1024 * 1024;
    private const long MaxExpandedBytes = 2L * 1024 * 1024 * 1024;
    private readonly string _store;
    private readonly string _application;
    private readonly string _dataRoot;
    private readonly RuntimeUpdateTrust _trust;
    public string Store => _store;

    public RuntimeUpdates(string application, RuntimeUpdateTrust trust, string? dataRoot = null)
    {
        _application = Path.GetFullPath(application);
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
        _trust = trust;
        _store = StoreFor(application, dataRoot);
    }

    public static string StoreFor(string application, string? dataRoot = null)
    {
        var identity = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(
            Path.TrimEndingDirectorySeparator(Path.GetFullPath(application)).ToUpperInvariant())))[..24].ToLowerInvariant();
        return Path.Combine(dataRoot ?? LauncherPaths.DataRoot, "runtime-updates", identity);
    }

    public static RuntimeUpdateTrust ReadTrust(string application)
    {
        var file = Path.Combine(application, "update-trust.json");
        if (!File.Exists(file)) throw new InvalidDataException(
            "Updates are not configured for this launcher yet. A release feed and trusted signing key must be included by the project.");
        PackStorage.EnsureNoLinks(file);
        var trust = JsonSerializer.Deserialize<RuntimeUpdateTrust>(ReadSmall(file), Json)
            ?? throw new InvalidDataException("Empty update configuration.");
        if (trust.PublicKeys == null || trust.PublicKeys.Count == 0) throw new InvalidDataException("No trusted update signing keys.");
        if (!string.IsNullOrEmpty(trust.FeedUrl)) Https(trust.FeedUrl);
        return trust;
    }

    private static byte[] ReadSmall(string path)
    {
        if (new FileInfo(path).Length > 2 * 1024 * 1024) throw new InvalidDataException("Update metadata is too large.");
        return File.ReadAllBytes(path);
    }

    private static Uri Https(string value)
    {
        if (!Uri.TryCreate(value, UriKind.Absolute, out var uri) || uri.Scheme != "https" || !string.IsNullOrEmpty(uri.UserInfo))
            throw new InvalidDataException("Update downloads require HTTPS.");
        return uri;
    }

    public async Task<VerifiedRuntimeUpdate> CheckAsync(CancellationToken cancellation = default)
    {
        if (string.IsNullOrWhiteSpace(_trust.FeedUrl)) throw new InvalidDataException("No update feed is configured. Import a signed update file instead.");
        using var client = Client();
        using var response = await client.GetAsync(Https(_trust.FeedUrl), HttpCompletionOption.ResponseHeadersRead, cancellation);
        response.EnsureSuccessStatusCode();
        using var output = new MemoryStream();
        await CopyBounded(await response.Content.ReadAsStreamAsync(cancellation), output, 2 * 1024 * 1024, cancellation);
        return Verify(output.ToArray());
    }

    private static HttpClient Client() => new(new HttpClientHandler { AllowAutoRedirect = false }) { Timeout = TimeSpan.FromMinutes(30) };

    // Sign the exact decoded payload bytes, never a reserialized JSON representation.
    public VerifiedRuntimeUpdate Verify(byte[] envelope)
    {
        if (envelope.Length > 2 * 1024 * 1024) throw new InvalidDataException("Update metadata is too large.");
        using var document = JsonDocument.Parse(envelope);
        var root = document.RootElement;
        var keyId = root.GetProperty("key_id").GetString() ?? "";
        if (!_trust.PublicKeys.TryGetValue(keyId, out var pem)) throw new InvalidDataException("This update is signed by an untrusted key.");
        var payload = Convert.FromBase64String(root.GetProperty("payload").GetString() ?? "");
        var signature = Convert.FromBase64String(root.GetProperty("signature").GetString() ?? "");
        using var rsa = RSA.Create();
        rsa.ImportFromPem(pem);
        if (rsa.KeySize < 3072 || !rsa.VerifyData(payload, signature, HashAlgorithmName.SHA256, RSASignaturePadding.Pss))
            throw new InvalidDataException("Update signature verification failed.");
        var manifest = JsonSerializer.Deserialize<RuntimeUpdateManifest>(payload, Json)
            ?? throw new InvalidDataException("Empty update manifest.");
        if (GameCatalog.Get(manifest.GameId).Id != GameCatalog.Mw3)
            throw new InvalidDataException("This update targets another game. Only MechWarrior 3 runtime updates are supported yet.");
        if (manifest.SchemaVersion != 1 || manifest.PreparationContract is not ("mw3-local-runtime-v1" or "mw3-source-runtime-v2"))
            throw new InvalidDataException("This update needs an unsupported preparation service. Update the launcher first.");
        PackStorage.ValidateId(manifest.Version);
        if (manifest.Sequence < 1 || !Version.TryParse(manifest.MinimumLauncherVersion, out var minimum) ||
            minimum > typeof(RuntimeUpdates).Assembly.GetName().Version)
            throw new InvalidDataException("This update requires a newer launcher.");
        if (manifest.PackageBytes < 1 || manifest.PackageBytes > MaxPackageBytes) throw new InvalidDataException("Invalid update download size.");
        HashFormat(manifest.PackageSha256);
        if (!string.IsNullOrEmpty(manifest.PackageUrl)) Https(manifest.PackageUrl);
        ValidateFiles(manifest.Files, MaxExpandedBytes);
        ValidateFiles(manifest.OriginalInputs, MaxExpandedBytes);
        if (manifest.PreparationContract == "mw3-source-runtime-v2" &&
            !new HashSet<string>(manifest.OriginalInputs.Keys, StringComparer.OrdinalIgnoreCase).SetEquals(new[] {
                "MECH3.EXE", "MECH3MSG.DLL", "native-inputs/MFC42.DLL", "native-inputs/MSVCRT.DLL",
                "native-inputs/MSVCP50.DLL", "native-inputs/Ir50_32.dll" }))
            throw new InvalidDataException("Source preparation requires the complete admitted original input set.");
        if (!manifest.OriginalInputs.Keys.Any(p => p.Equals("MECH3.EXE", StringComparison.OrdinalIgnoreCase)))
            throw new InvalidDataException("An update must identify its original game executable input.");
        PackStorage.ValidatePath(manifest.Preparer);
        if (!manifest.Preparer.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) || !manifest.Files.ContainsKey(manifest.Preparer))
            throw new InvalidDataException("Missing native preparation tool.");
        return new(manifest, Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant(), Convert.ToBase64String(envelope));
    }

    private static void HashFormat(string value)
    {
        if (value == null || value.Length != 64 || !value.All(Uri.IsHexDigit)) throw new InvalidDataException("Invalid update SHA256.");
    }

    private static void ValidateFiles(Dictionary<string, UpdateFile>? files, long limit)
    {
        if (files == null || files.Count == 0 || files.Count > 20000) throw new InvalidDataException("Invalid update file table.");
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        long total = 0;
        foreach (var (name, pin) in files)
        {
            PackStorage.ValidatePath(name);
            if (!seen.Add(name) || pin == null || pin.Bytes < 0 || pin.Bytes > limit || (total = checked(total + pin.Bytes)) > limit)
                throw new InvalidDataException("Invalid update file size or duplicate path.");
            HashFormat(pin.Sha256);
        }
    }

    internal static void VerifyFile(string path, UpdateFile pin)
    {
        PackStorage.EnsureNoLinks(path);
        using var stream = File.OpenRead(path);
        if (stream.Length != pin.Bytes || !Convert.ToHexString(SHA256.HashData(stream)).Equals(pin.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Update integrity check failed: " + Path.GetFileName(path));
    }

    public RuntimeUpdateState State()
    {
        var path = Path.Combine(_store, "selection.json");
        PackStorage.EnsureNoLinks(path);
        return File.Exists(path) ? JsonSerializer.Deserialize<RuntimeUpdateState>(ReadSmall(path), Json)
            ?? throw new InvalidDataException("Empty runtime selection.") : new(null, null, 0);
    }

    public static string? SelectedRoot(string application, string? dataRoot = null)
    {
        var updates = new RuntimeUpdates(application, new("", new()), dataRoot);
        var active = updates.State().Active;
        // A full installer can replace explicitly retired runtime releases while
        // preserving their files and selection for rollback. Future updates win.
        var bundledManifest = Path.Combine(application, "Runtime", "runtime.json");
        if (active != null && File.Exists(bundledManifest))
        {
            PackStorage.EnsureNoLinks(bundledManifest);
            using var bundled = JsonDocument.Parse(ReadSmall(bundledManifest));
            if (bundled.RootElement.TryGetProperty("supersedes_runtime_versions", out var retired) &&
                retired.EnumerateArray().Any(version => version.GetString() == active))
                return null;
        }
        return active == null ? null : updates.VersionRoot(active);
    }

    private string VersionRoot(string version) => PackStorage.Resolve(_store, "versions/" + PackStorage.ValidateId(version));

    private FileStream MutationLock()
    {
        PackStorage.EnsureNoLinks(_store);
        Directory.CreateDirectory(_store);
        return new FileStream(Path.Combine(_store, ".update-lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }

    private void WriteState(RuntimeUpdateState state)
    {
        var target = PackStorage.Resolve(_store, "selection.json");
        var temporary = PackStorage.Resolve(_store, ".selection-" + Guid.NewGuid().ToString("N"));
        using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        {
            JsonSerializer.Serialize(stream, state, Json);
            stream.Flush(true);
        }
        File.Move(temporary, target, true);
    }

    private static void RequireGameStopped()
    {
        var processes = Process.GetProcessesByName("entry_commandline");
        try { if (processes.Length != 0) throw new InvalidOperationException("Close the game before changing versions."); }
        finally { foreach (var process in processes) process.Dispose(); }
    }

    public async Task PrepareAsync(VerifiedRuntimeUpdate update, string game, string? localPackage,
        IProgress<string>? progress = null, CancellationToken cancellation = default)
    {
        using var gate = GameUpdateGate.Acquire(_dataRoot);
        LauncherUpdates.RequireGamesClosed();
        using var storageLock = MutationLock();
        RequireGameStopped();
        var state = State();
        update = Verify(Convert.FromBase64String(update.SignedEnvelope));
        var manifest = update.Manifest;
        if (manifest.Sequence <= state.HighestSequence) throw new InvalidDataException("This update is already installed or older than a previously installed update.");
        progress?.Report("Verifying original game files…");
        var originalPaths = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var support = manifest.PreparationContract == "mw3-source-runtime-v2"
            ? GameInstallation.FindSupportFiles(game, _dataRoot)
                ?? throw new FileNotFoundException("Original support files are missing. Run Set Up Game and select your ISO.")
            : null;
        foreach (var (name, pin) in manifest.OriginalInputs)
        {
            var path = support != null && name.StartsWith("native-inputs/", StringComparison.OrdinalIgnoreCase)
                ? support[Path.GetFileName(name)] : PackStorage.Resolve(game, name);
            VerifyFile(path, pin);
            originalPaths.Add(name, Path.GetFullPath(path));
        }
        var installed = VersionRoot(manifest.Version);
        if (Directory.Exists(installed))
        {
            // A crash after publishing the directory but before selecting it must be retryable.
            var receipt = PackStorage.Resolve(installed, ".prepared-update.json");
            using var recovery = JsonDocument.Parse(ReadSmall(receipt));
            if (recovery.RootElement.GetProperty("manifest_sha256").GetString() != update.ManifestSha256)
                throw new InvalidDataException("A different update already owns this runtime version.");
            ValidateGeneratedRuntime(installed);
            RequireGameStopped();
            cancellation.ThrowIfCancellationRequested();
            WriteState(new(manifest.Version, state.Active, manifest.Sequence));
            progress?.Report("Previously prepared update activated.");
            return;
        }
        // Keep compiler paths within legacy Windows path limits. The owner
        // receipt below still checks the complete signed manifest identity.
        var work = PackStorage.Resolve(_store, ".preparing-" + update.ManifestSha256[..24]);
        Directory.CreateDirectory(work);
        var owner = Path.Combine(work, "owner.json");
        if (File.Exists(owner))
        {
            using var previousWork = JsonDocument.Parse(ReadSmall(owner));
            if (previousWork.RootElement.GetProperty("manifest_sha256").GetString() != update.ManifestSha256)
                throw new InvalidDataException("A different preparation owns this workspace.");
        }
        else
        {
            if (Directory.EnumerateFileSystemEntries(work).Any())
                throw new InvalidDataException("Unrecognized existing preparation workspace.");
            File.WriteAllText(owner, JsonSerializer.Serialize(new { manifest_sha256 = update.ManifestSha256 }));
        }
        var archive = Path.Combine(work, "source-tools.zip");
        var precompiled = manifest.Files.ContainsKey("Runtime/runtime.json");
        progress?.Report(precompiled ? "Verifying native runtime package…" : "Getting update tools…");
        if (!File.Exists(archive))
        {
            var partial = Path.Combine(work, "source-tools.zip.partial");
            PackStorage.EnsureNoLinks(partial);
            using (var destination = new FileStream(partial, FileMode.Create, FileAccess.Write))
            {
            if (localPackage != null)
            {
                PackStorage.EnsureNoLinks(localPackage);
                using var source = File.OpenRead(localPackage);
                await CopyBounded(source, destination, manifest.PackageBytes, cancellation);
            }
            else
            {
                using var client = Client();
                using var response = await client.GetAsync(Https(manifest.PackageUrl), HttpCompletionOption.ResponseHeadersRead, cancellation);
                response.EnsureSuccessStatusCode();
                await CopyBounded(await response.Content.ReadAsStreamAsync(cancellation), destination, manifest.PackageBytes, cancellation);
            }
            }
            VerifyFile(partial, new(manifest.PackageBytes, manifest.PackageSha256));
            File.Move(partial, archive);
        }
        VerifyFile(archive, new(manifest.PackageBytes, manifest.PackageSha256));
        var tools = Path.Combine(work, "tools");
        Directory.CreateDirectory(tools);
        Extract(archive, tools, manifest.Files);
        void InspectTools(string directory)
        {
            PackStorage.EnsureNoLinks(directory);
            foreach (var path in Directory.EnumerateFiles(directory))
            {
                PackStorage.EnsureNoLinks(path);
                if (!manifest.Files.ContainsKey(Path.GetRelativePath(tools, path).Replace('\\', '/')))
                    throw new InvalidDataException("Unregistered preparation tool file.");
            }
            foreach (var child in Directory.EnumerateDirectories(directory)) InspectTools(child);
        }
        InspectTools(tools);
        cancellation.ThrowIfCancellationRequested();
        progress?.Report(precompiled ? "Installing native runtime. Your current version stays available…" :
            "Preparing this version from your game files. Your current version stays available…");
        var output = Path.Combine(work, "runtime");
        Directory.CreateDirectory(output);
        var info = new ProcessStartInfo(PackStorage.Resolve(tools, manifest.Preparer))
        { UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = tools, RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (var argument in new[] { "--game", Path.GetFullPath(game), "--output", output, "--version", manifest.Version }) info.ArgumentList.Add(argument);
        if (manifest.PreparationContract == "mw3-source-runtime-v2")
        {
            var inputMap = Path.Combine(work, "original-inputs.json");
            File.WriteAllText(inputMap, JsonSerializer.Serialize(originalPaths));
            info.ArgumentList.Add("--original-inputs");
            info.ArgumentList.Add(inputMap);
        }
        var previous = state.Active == null ? Path.Combine(_application, "Runtime") : VersionRoot(state.Active);
        if (Directory.Exists(previous)) { info.ArgumentList.Add("--previous"); info.ArgumentList.Add(previous); }
        using var process = Process.Start(info) ?? throw new IOException("The preparation tool did not start.");
        var attempt = Guid.NewGuid().ToString("N");
        var stdout = Log(process.StandardOutput, Path.Combine(work, "prepare-" + attempt + ".stdout.log"), progress);
        var stderr = Log(process.StandardError, Path.Combine(work, "prepare-" + attempt + ".stderr.log"));
        try { await process.WaitForExitAsync(cancellation); }
        catch (OperationCanceledException)
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            await process.WaitForExitAsync();
            await Task.WhenAll(stdout, stderr);
            throw;
        }
        await Task.WhenAll(stdout, stderr);
        if (process.ExitCode != 0) throw new IOException($"Game preparation failed (exit code {process.ExitCode}). Your current version was kept. Details: " + work);
        cancellation.ThrowIfCancellationRequested();
        ValidateGeneratedRuntime(output);
        // Original inputs are read-only by contract; detect accidental preparation-tool changes.
        foreach (var (name, pin) in manifest.OriginalInputs) VerifyFile(originalPaths[name], pin);
        RequireGameStopped();
        cancellation.ThrowIfCancellationRequested();
        File.WriteAllText(Path.Combine(output, ".prepared-update.json"), JsonSerializer.Serialize(new { manifest_sha256 = update.ManifestSha256 }));
        Directory.CreateDirectory(Path.GetDirectoryName(installed)!);
        Directory.Move(output, installed);
        File.WriteAllText(Path.Combine(work, "update.json"), JsonSerializer.Serialize(new { manifest.Version, update.ManifestSha256 }));
        cancellation.ThrowIfCancellationRequested();
        WriteState(new(manifest.Version, state.Active, manifest.Sequence));
        progress?.Report("Update ready.");
    }

    private static async Task Log(StreamReader reader, string path, IProgress<string>? progress = null)
    {
        // Drain all output without keeping unbounded text in memory or filling the disk.
        using var writer = new StreamWriter(path);
        var buffer = new char[4096];
        long written = 0;
        var pending = new StringBuilder();
        var lastProgress = DateTime.MinValue;
        int count;
        while ((count = await reader.ReadAsync(buffer)) != 0)
        {
            if (written < 4 * 1024 * 1024) await writer.WriteAsync(buffer.AsMemory(0, count));
            written += count;
            if (progress == null) continue;
            for (var index = 0; index < count; index++)
            {
                if (buffer[index] != '\n')
                {
                    if (pending.Length < 4096) pending.Append(buffer[index]);
                    continue;
                }
                var line = pending.ToString().Trim();
                pending.Clear();
                if (line.StartsWith("Preparing ", StringComparison.Ordinal) ||
                    line.StartsWith("Reusing verified native code", StringComparison.Ordinal))
                    progress.Report(line[..Math.Min(line.Length, 200)]);
                else if (line.StartsWith('{') && DateTime.UtcNow - lastProgress >= TimeSpan.FromSeconds(1))
                {
                    try
                    {
                        using var status = JsonDocument.Parse(line);
                        var root = status.RootElement;
                        if (root.TryGetProperty("completed", out var completed) && root.TryGetProperty("total", out var total) &&
                            completed.TryGetInt32(out var done) && total.TryGetInt32(out var all) && done >= 0 && all > 0 && done <= all)
                        {
                            progress.Report($"Preparing native game code: {done:N0} of {all:N0}…");
                            lastProgress = DateTime.UtcNow;
                        }
                    }
                    catch (JsonException) { } // Non-progress child output remains in the bounded log.
                }
            }
        }
    }

    private static async Task CopyBounded(Stream source, Stream destination, long maximum, CancellationToken cancellation)
    {
        var buffer = new byte[81920];
        long total = 0;
        int count;
        while ((count = await source.ReadAsync(buffer, cancellation)) != 0)
        {
            if ((total += count) > maximum) throw new InvalidDataException("Update exceeded its size limit.");
            await destination.WriteAsync(buffer.AsMemory(0, count), cancellation);
        }
    }

    private static void Extract(string archive, string root, Dictionary<string, UpdateFile> files)
    {
        using var zip = ZipFile.OpenRead(archive);
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var entry in zip.Entries)
        {
            if (!seen.Add(entry.FullName) || !files.TryGetValue(entry.FullName, out var pin) || entry.Length != pin.Bytes ||
                ((entry.ExternalAttributes >> 16) & 0xf000) == 0xa000)
                throw new InvalidDataException("Unexpected update archive entry.");
            var path = PackStorage.Resolve(root, entry.FullName);
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            if (File.Exists(path))
            {
                VerifyFile(path, pin);
                continue; // Exact source tools retained for an interrupted preparation.
            }
            using (var source = entry.Open())
            using (var target = new FileStream(path, FileMode.CreateNew, FileAccess.Write))
                CopyBounded(source, target, pin.Bytes, CancellationToken.None).GetAwaiter().GetResult();
            VerifyFile(path, pin);
        }
        if (seen.Count != files.Count) throw new InvalidDataException("Update archive is incomplete.");
    }

    public static void ValidateGeneratedRuntime(string root)
    {
        var manifest = PackStorage.Resolve(root, "runtime.json");
        using var document = JsonDocument.Parse(ReadSmall(manifest));
        var files = JsonSerializer.Deserialize<Dictionary<string, UpdateFile>>(document.RootElement.GetProperty("files"), Json)!;
        ValidateFiles(files, 4L * 1024 * 1024 * 1024);
        foreach (var (name, pin) in files) VerifyFile(PackStorage.Resolve(root, name), pin);
        void Inspect(string directory)
        {
            PackStorage.EnsureNoLinks(directory);
            foreach (var path in Directory.EnumerateFiles(directory))
            {
                PackStorage.EnsureNoLinks(path);
                var relative = Path.GetRelativePath(root, path).Replace('\\', '/');
                if (relative != "runtime.json" && relative != ".prepared-update.json" && !files.ContainsKey(relative))
                    throw new InvalidDataException("Unregistered generated runtime file.");
            }
            foreach (var child in Directory.EnumerateDirectories(directory)) Inspect(child);
        }
        Inspect(root);
        var layout = NativeRuntimeLayout.ReadRoot(root);
        var profileText = File.ReadAllText(layout.Profile);
        RuntimeContentCapabilities.Advertised(JsonNode.Parse(profileText)!["native"]!.AsObject());
        using var profile = JsonDocument.Parse(profileText);
        var native = profile.RootElement.GetProperty("native");
        var executable = native.GetProperty("executable").GetString() ?? "";
        if (!executable.StartsWith("@runtime/", StringComparison.Ordinal) ||
            !files.TryGetValue(executable[9..], out var executablePin) ||
            !executablePin.Sha256.Equals(native.GetProperty("executable_sha256").GetString(), StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The generated game executable must be pinned inside its runtime version.");
        NativeRuntimeLayout.ValidateLaunchExecutable(PackStorage.Resolve(root, executable[9..]));
        if (native.TryGetProperty("translated_module", out var module))
        {
            var name = module.GetString() ?? "";
            if (!name.StartsWith("@runtime/", StringComparison.Ordinal) ||
                !files.TryGetValue(name[9..], out var modulePin) ||
                !modulePin.Sha256.Equals(native.GetProperty("translated_module_sha256").GetString(), StringComparison.OrdinalIgnoreCase) ||
                !document.RootElement.TryGetProperty("native_modules", out var modules) ||
                !modules.EnumerateArray().Any(p => p.GetString() == name[9..]))
                throw new InvalidDataException("The generated game module must be pinned inside its runtime version.");
        }
        NativeRuntimeLayout.ResolveProfile(profileText, root, root);
    }

    public void Rollback()
    {
        using var gate = GameUpdateGate.Acquire(_dataRoot);
        LauncherUpdates.RequireGamesClosed();
        using var storageLock = MutationLock();
        RequireGameStopped();
        var state = State();
        if (state.Active == null) throw new InvalidDataException("No runtime update is active.");
        if (state.Previous != null) ValidateGeneratedRuntime(VersionRoot(state.Previous));
        else NativeRuntimeLayout.ReadRoot(Path.Combine(_application, "Runtime"));
        WriteState(new(state.Previous, state.Active, state.HighestSequence));
    }
}
