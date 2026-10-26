using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace MW3RemasterLauncher.Core;

public sealed record LauncherUpdateManifest(int SchemaVersion, string ProductId, string UpdateType,
    string Version, long Sequence, string MinimumLauncherVersion, long PackageBytes, string PackageSha256,
    UpdateFile Installer);
public sealed record VerifiedLauncherUpdate(LauncherUpdateManifest Manifest, byte[] Envelope);
public sealed record LauncherUpdateJob(string Application, string Metadata, string Installer, int ParentId, long ParentStartedUtc);

/// <summary>Signed launcher-only Inno upgrades. A copied current launcher waits for exit and applies setup.</summary>
public sealed class LauncherUpdates
{
    private const long MaximumPackage = 512L * 1024 * 1024;
    private readonly string _application;
    private readonly RuntimeUpdateTrust _trust;
    private readonly string _dataRoot;
    public string Store { get; }
    public LauncherUpdates(string application, RuntimeUpdateTrust trust, string? dataRoot = null)
    {
        _application = Path.TrimEndingDirectorySeparator(Path.GetFullPath(application));
        _trust = trust;
        _dataRoot = dataRoot ?? LauncherPaths.DataRoot;
        var id = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(_application.ToUpperInvariant())))[..24];
        Store = Path.Combine(dataRoot ?? LauncherPaths.DataRoot, "launcher-updates", id);
    }

    public static byte[] ReadMetadata(string path)
    {
        PackStorage.EnsureNoLinks(path);
        if (new FileInfo(path).Length > 2 * 1024 * 1024) throw new InvalidDataException("Update metadata is too large.");
        return File.ReadAllBytes(path);
    }

    public VerifiedLauncherUpdate Verify(byte[] envelope)
    {
        if (envelope.Length > 2 * 1024 * 1024) throw new InvalidDataException("Update metadata is too large.");
        using var doc = JsonDocument.Parse(envelope);
        var root = doc.RootElement;
        var key = root.GetProperty("key_id").GetString() ?? "";
        if (!_trust.PublicKeys.TryGetValue(key, out var pem)) throw new InvalidDataException("Untrusted launcher update signing key.");
        var payload = Convert.FromBase64String(root.GetProperty("payload").GetString() ?? "");
        using var rsa = RSA.Create(); rsa.ImportFromPem(pem);
        if (rsa.KeySize < 3072 || !rsa.VerifyData(payload, Convert.FromBase64String(root.GetProperty("signature").GetString() ?? ""), HashAlgorithmName.SHA256, RSASignaturePadding.Pss))
            throw new InvalidDataException("Launcher update signature verification failed.");
        var m = JsonSerializer.Deserialize<LauncherUpdateManifest>(payload, RuntimeUpdates.Json) ?? throw new InvalidDataException("Empty launcher update.");
        if (m.SchemaVersion != 1 || m.ProductId != GameCatalog.LauncherId || m.UpdateType != "launcher-inno-v1")
            throw new InvalidDataException("This is not a supported Core Critical launcher update.");
        var current = typeof(LauncherUpdates).Assembly.GetName().Version!;
        if (!Version.TryParse(m.Version, out var version) || version <= current ||
            !Version.TryParse(m.MinimumLauncherVersion, out var minimum) || minimum > current || m.Sequence <= 0)
            throw new InvalidDataException("This launcher update is older, already installed, or requires a newer launcher.");
        ValidatePin(new(m.PackageBytes, m.PackageSha256)); ValidatePin(m.Installer);
        if (m.Sequence <= HighestSequence()) throw new InvalidDataException("This launcher update sequence was already installed.");
        return new(m, envelope.ToArray());
    }

    private static void ValidatePin(UpdateFile? pin)
    {
        if (pin == null || pin.Bytes < 1 || pin.Bytes > MaximumPackage || pin.Sha256 == null ||
            pin.Sha256.Length != 64 || !pin.Sha256.All(Uri.IsHexDigit)) throw new InvalidDataException("Invalid launcher update size or SHA256.");
    }
    private long HighestSequence()
    {
        var file = Path.Combine(Store, "installed-sequence.json");
        return File.Exists(file) ? JsonSerializer.Deserialize<long>(ReadMetadata(file)) : 0;
    }
    public long InstalledSequence => HighestSequence();
    private FileStream Lock()
    {
        PackStorage.EnsureNoLinks(Store); Directory.CreateDirectory(Store);
        return new FileStream(Path.Combine(Store, ".launcher-update-lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }
    public static void RequireGamesClosed()
    {
        foreach (var name in new[] { "entry_commandline", "Mech3", "MW3RemasterNative", "MW4", "MW4Mercs" })
        {
            var processes = Process.GetProcessesByName(name);
            try { if (processes.Length != 0) throw new InvalidOperationException("Close all games before updating Core Critical."); }
            finally { foreach (var p in processes) p.Dispose(); }
        }
    }

    private void RequireApplicationClosed()
    {
        foreach (var name in new[] { "Core Critical Launcher", "MW3RemasterLauncher" })
        {
            var executable = Path.Combine(_application, name + ".exe");
            var processes = Process.GetProcessesByName(name);
            try
            {
                foreach (var process in processes)
                    if (string.Equals(process.MainModule?.FileName, executable, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidOperationException("Another Core Critical window is open. Close it and retry the launcher update.");
            }
            finally { foreach (var process in processes) process.Dispose(); }
        }
    }

    /// <summary>Validate all bytes before preparing the helper. This never closes the caller.</summary>
    public string Stage(VerifiedLauncherUpdate candidate, string package)
    {
        using var gate = GameUpdateGate.Acquire(_dataRoot);
        using var updateLock = Lock(); RequireGamesClosed();
        candidate = Verify(candidate.Envelope);
        var manifest = candidate.Manifest;
        RuntimeUpdates.VerifyFile(package, new(manifest.PackageBytes, manifest.PackageSha256));
        var stage = PackStorage.Resolve(Store, "pending-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(stage);
        // Keep failure evidence in this owned directory; no application files have changed.
        var metadata = Path.Combine(stage, "update.ccupdate"); File.WriteAllBytes(metadata, candidate.Envelope);
        var installer = Path.Combine(stage, "CoreCriticalSetup.exe");
        using (var archive = ZipFile.OpenRead(package))
        {
            if (archive.Entries.Count != 1 || archive.Entries[0].FullName != "CoreCriticalSetup.exe" ||
                archive.Entries[0].Length != manifest.Installer.Bytes ||
                ((archive.Entries[0].ExternalAttributes >> 16) & 0xF000) == 0xA000)
                throw new InvalidDataException("Launcher update ZIP must contain only CoreCriticalSetup.exe.");
            using var input = archive.Entries[0].Open();
            using var output = new FileStream(installer, FileMode.CreateNew);
            var buffer = new byte[81920]; long bytes = 0; int count;
            while ((count = input.Read(buffer)) != 0)
            {
                bytes += count; if (bytes > manifest.Installer.Bytes) throw new InvalidDataException("Installer exceeds declared size.");
                output.Write(buffer, 0, count);
            }
        }
        RuntimeUpdates.VerifyFile(installer, manifest.Installer); WindowsPublisherTrust.Verify(installer);
        if (!File.Exists(Path.Combine(_application, "launcher-installation.json")))
            throw new InvalidOperationException("Install Core Critical through setup before using launcher updates.");
        foreach (var name in new[] { "Core Critical Launcher.exe", "Core Critical Launcher.dll", "Core Critical Launcher.deps.json", "Core Critical Launcher.runtimeconfig.json" })
            if (!File.Exists(Path.Combine(_application, name))) throw new IOException("The installed launcher is incomplete. Run launcher setup to repair it first.");
        var helper = Path.Combine(stage, "helper"); Directory.CreateDirectory(helper);
        // Copy only the current app's top-level executable/framework files, never game data or Preparation.
        var files = Directory.GetFiles(_application).Where(f => new[] { ".exe", ".dll", ".json" }.Contains(Path.GetExtension(f).ToLowerInvariant())).ToArray();
        if (files.Length > 1024 || files.Sum(f => new FileInfo(f).Length) > 1024L * 1024 * 1024) throw new InvalidDataException("Unexpected launcher helper size.");
        foreach (var file in files) { PackStorage.EnsureNoLinks(file); File.Copy(file, Path.Combine(helper, Path.GetFileName(file))); }
        using var parent = Process.GetCurrentProcess();
        File.WriteAllText(Path.Combine(stage, "job.json"), JsonSerializer.Serialize(new LauncherUpdateJob(_application, metadata, installer,
            parent.Id, parent.StartTime.ToUniversalTime().Ticks), RuntimeUpdates.Json));
        return Path.Combine(stage, "job.json");
    }

    public static void StartHelper(string jobFile)
    {
        var info = new ProcessStartInfo(Path.Combine(Path.GetDirectoryName(jobFile)!, "helper", "Core Critical Launcher.exe")) { UseShellExecute = false };
        info.ArgumentList.Add("--apply-ccupdate"); info.ArgumentList.Add(jobFile);
        using var child = Process.Start(info) ?? throw new IOException("The launcher updater could not start.");
    }

    public static async Task ApplyJobAsync(string jobFile)
    {
        var job = JsonSerializer.Deserialize<LauncherUpdateJob>(ReadMetadata(jobFile), RuntimeUpdates.Json) ?? throw new InvalidDataException("Empty update job.");
        var updates = new LauncherUpdates(job.Application, RuntimeUpdates.ReadTrust(job.Application));
        var stage = Path.GetDirectoryName(Path.GetFullPath(jobFile))!;
        if (!stage.StartsWith(Path.GetFullPath(updates.Store) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) ||
            Path.GetDirectoryName(stage) != Path.GetFullPath(updates.Store) ||
            Path.GetFullPath(job.Metadata) != Path.Combine(stage, "update.ccupdate") || Path.GetFullPath(job.Installer) != Path.Combine(stage, "CoreCriticalSetup.exe"))
            throw new InvalidDataException("Update job is outside its owned staging directory.");
        try
        {
            try
            {
                using var parent = Process.GetProcessById(job.ParentId);
                if (parent.StartTime.ToUniversalTime().Ticks != job.ParentStartedUtc) throw new InvalidOperationException("Launcher process identity changed.");
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(90));
                await parent.WaitForExitAsync(timeout.Token);
            }
            catch (ArgumentException) { /* Parent already exited. */ }
            using var gate = GameUpdateGate.Acquire(updates._dataRoot);
            using var updateLock = updates.Lock();
            RequireGamesClosed();
            updates.RequireApplicationClosed();
            var update = updates.Verify(ReadMetadata(job.Metadata));
            // Hold a read-only handle through execution to prevent staged installer replacement.
            using var installerLock = new FileStream(job.Installer, FileMode.Open, FileAccess.Read, FileShare.Read);
            RuntimeUpdates.VerifyFile(job.Installer, update.Manifest.Installer); WindowsPublisherTrust.Verify(job.Installer);
            var info = new ProcessStartInfo(job.Installer) { UseShellExecute = false };
            foreach (var arg in new[] { "/SP-", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/TASKS=", "/DIR=" + job.Application, "/LOG=" + Path.Combine(stage, "setup.log") }) info.ArgumentList.Add(arg);
            using var setup = Process.Start(info) ?? throw new IOException("The launcher installer did not start.");
            await setup.WaitForExitAsync();
            if (setup.ExitCode != 0) throw new IOException("Launcher setup failed with exit code " + setup.ExitCode + ". See setup.log; rerun the signed launcher setup to repair.");
            var installedVersion = FileVersionInfo.GetVersionInfo(Path.Combine(job.Application, "Core Critical Launcher.dll")).FileVersion;
            var expected = Version.Parse(update.Manifest.Version);
            if (!Version.TryParse(installedVersion, out var actual) || actual.Major != expected.Major || actual.Minor != expected.Minor ||
                actual.Build != expected.Build || Math.Max(0, actual.Revision) != Math.Max(0, expected.Revision))
                throw new IOException("Setup finished but the installed launcher version does not match the signed update.");
            var temporary = Path.Combine(updates.Store, ".sequence-" + Guid.NewGuid().ToString("N"));
            File.WriteAllText(temporary, JsonSerializer.Serialize(update.Manifest.Sequence));
            File.Move(temporary, Path.Combine(updates.Store, "installed-sequence.json"), true);
            File.WriteAllText(Path.Combine(stage, "result.txt"), "Core Critical updated to " + update.Manifest.Version);
            using var restarted = Process.Start(new ProcessStartInfo(Path.Combine(job.Application, "Core Critical Launcher.exe")) { UseShellExecute = true, WorkingDirectory = job.Application });
        }
        catch (Exception error)
        {
            File.WriteAllText(Path.Combine(stage, "result.txt"), "Launcher update failed: " + error.Message);
            throw;
        }
    }
}
