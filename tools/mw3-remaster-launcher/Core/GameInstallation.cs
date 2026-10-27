using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Runtime.InteropServices;

namespace MW3RemasterLauncher.Core;

/// <summary>Build a private original-data installation from admitted user media, without executing it.</summary>
public static class GameInstallation
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint QueryDosDevice(string deviceName, StringBuilder target, int capacity);

    private static string MountedIsoDrive(string devicePath)
    {
        // Some Windows storage providers expose the mounted CD-ROM device but
        // omit its Get-Volume association. Match the actual DOS device mappings.
        if (!devicePath.StartsWith(@"\\.\CDROM", StringComparison.OrdinalIgnoreCase)) return "";
        string Target(string name)
        {
            var buffer = new StringBuilder(32768);
            return QueryDosDevice(name, buffer, buffer.Capacity) == 0 ? "" : buffer.ToString();
        }
        var target = Target(devicePath[4..]);
        if (target.Length == 0) return "";
        var matches = DriveInfo.GetDrives().Where(drive => drive.DriveType == DriveType.CDRom &&
            Target(drive.Name[..2]).Equals(target, StringComparison.OrdinalIgnoreCase)).ToArray();
        return matches.Length == 1 ? matches[0].Name[..1] : "";
    }
    public sealed record ContentFile(string Source, string Target, long Bytes, string Sha256);
    private sealed record MediaManifest(string Profile, string BaseCabinet, string BaseHeader,
        string PatchPackage, string PatchCabinet, string PatchHeader, string PatchWrapperCabinet,
        int PatchWrapperOffset, int PatchWrapperBytes, string Unshield, string Zlib, string StaticUnshield,
        ContentFile[] BaseFiles, ContentFile[] PatchFiles, ContentFile[] MediaFiles, ContentFile[] ProviderFiles);

    private static readonly MediaManifest Media = LoadManifest();
    public static void VerifyExtractor(string directory)
    {
        var executable = Path.Combine(directory, "unshield.exe");
        PackStorage.EnsureNoLinks(executable);
        if (new FileInfo(executable).Length > 2 * 1024 * 1024)
            throw new InvalidDataException("The launcher's media extraction tool is damaged. Repair the launcher installation.");
        var bytes = File.ReadAllBytes(executable);
        var hash = Convert.ToHexString(SHA256.HashData(bytes));
        // Pin every unsigned executable byte. Signing may alter only the checksum,
        // security directory and appended certificate records, never code or data.
        if (hash.Equals(Media.StaticUnshield, StringComparison.OrdinalIgnoreCase) ||
            PinnedPeImage.MatchesSignedImage(bytes, 284672, Media.StaticUnshield)) return;
        // Preserve exact legacy development tooling for retained private trials.
        if (!hash.Equals(Media.Unshield, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The launcher's media extraction tool is damaged or incompatible. Repair the launcher installation; this error does not identify an unsupported ISO.");
        VerifyFile(Path.Combine(directory, "zlib1.dll"), Media.Zlib);
    }
    private static MediaManifest LoadManifest()
    {
        using var stream = typeof(GameInstallation).Assembly.GetManifestResourceStream(
            "MW3RemasterLauncher.Core.SupportedMedia.json")
            ?? throw new InvalidOperationException("Supported media metadata is missing.");
        return JsonSerializer.Deserialize<MediaManifest>(stream,
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
            ?? throw new InvalidDataException("Supported media metadata is empty.");
    }

    // The native runtime always selects the hardware renderer (PlayerRegistry), so it
    // never opens the disc's software texture tiers. Retail installs often omit some.
    private static readonly string[] UnusedComponents =
        ["Software_Texture_Best", "Software_Texture_Medium", "Software_Texture_Low", "Mech_Texture_SW"];
    // Retail 1.2 tries soundsH, soundsM and soundsL in turn from the player's preferred
    // bank (0x56fbf0), so an install needs only one of the disc's two sound banks.
    private static readonly string[] SoundComponents = ["Sound_High_Fidelity", "Sound_Low_Fidelity"];

    public static Task VerifyExistingAsync(string directory, Action<string, double>? progress = null)
        => VerifyExistingAsync(directory, Media.BaseFiles, Media.PatchFiles, progress);

    /// <summary>Hash every present file of the closure; only tiers the runtime can do without may be absent.</summary>
    public static async Task VerifyExistingAsync(string directory, ContentFile[] baseFiles, ContentFile[] patchFiles,
        Action<string, double>? progress = null)
    {
        await Task.Run(() =>
        {
            // Check the complete admitted data closure, while allowing unrelated files and saves.
            // A patched target keeps the component of the base file it replaces.
            var entries = baseFiles.Concat(patchFiles).GroupBy(f => f.Target, StringComparer.OrdinalIgnoreCase)
                .Select(g => (File: g.Last(), Component: g.First().Source.Split('/')[0])).ToArray();
            bool Present(ContentFile file)
            {
                var path = PackStorage.Resolve(directory, file.Target);
                PackStorage.EnsureNoLinks(path);
                return File.Exists(path);
            }
            var present = entries.Where(e => Present(e.File)).ToArray();
            var missing = entries.Except(present)
                .Where(e => !UnusedComponents.Contains(e.Component) && !SoundComponents.Contains(e.Component))
                .Select(e => e.File.Target).ToList();
            var sounds = entries.Where(e => SoundComponents.Contains(e.Component)).ToArray();
            if (sounds.Length != 0 && !sounds.Any(present.Contains))
                missing.Add(string.Join(" or ", sounds.Select(e => e.File.Target)));
            // Report every missing file at once, before spending time hashing the rest.
            if (missing.Count == 1)
                throw new FileNotFoundException("Required installation file is missing: " + missing[0]);
            if (missing.Count > 1)
                throw new FileNotFoundException(missing.Count + " required installation files are missing: " +
                    string.Join(", ", missing));
            for (var i = 0; i < present.Length; i++)
            {
                var file = present[i].File;
                VerifyFile(PackStorage.Resolve(directory, file.Target), file.Sha256, file.Bytes);
                progress?.Invoke("Checking original game files: " + file.Target, (i + 1.0) / present.Length);
            }
        });
    }

    /// <summary>Admit the retail eight-megabyte hardware component before advertising it to the game.</summary>
    public static void VerifyHardwareRendererFiles(string directory)
    {
        var files = Media.BaseFiles.Where(f => f.Source.StartsWith("Hardware_Texture_8/", StringComparison.Ordinal))
            .Concat(Media.PatchFiles).GroupBy(f => f.Target, StringComparer.OrdinalIgnoreCase)
            .Where(g => g.Any(f => f.Source.StartsWith("Hardware_Texture_8/", StringComparison.Ordinal)))
            .Select(g => g.Last()).ToArray();
        if (files.Length != 6) throw new InvalidDataException("Hardware renderer component metadata is incomplete.");
        foreach (var file in files)
            VerifyFile(PackStorage.Resolve(directory, file.Target), file.Sha256, file.Bytes);
    }

    /// <summary>The destination must be new. Publish only after every selected file has passed verification.</summary>
    public static async Task InstallDirectoryAsync(string sourceRoot, string patchPath, string destination,
        string extractorDirectory, Action<string, double>? progress = null)
    {
        destination = Path.GetFullPath(destination);
        PackStorage.EnsureNoLinks(destination);
        if (Directory.Exists(destination) || File.Exists(destination))
            throw new IOException("Choose a new game-data folder. Existing installations are never overwritten.");
        var parent = Path.GetDirectoryName(destination) ?? throw new IOException("Choose a game-data subfolder.");
        Directory.CreateDirectory(parent);
        var scratch = Path.Combine(parent, ".mw3-install-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(scratch);
        try
        {
            await Task.Run(async () =>
            {
                progress?.Invoke("Checking the supplied retail disc and 1.2 patch…", .02);
                var extractor = Path.Combine(extractorDirectory, "unshield.exe");
                VerifyExtractor(extractorDirectory);
                var cabinets = Path.Combine(scratch, "base-cabinets");
                Directory.CreateDirectory(cabinets);
                // Copy to private scratch first: the bytes tested are the bytes passed to the extractor.
                CopyVerified(Path.Combine(sourceRoot, "DATA1.CAB"), Path.Combine(cabinets, "data1.cab"), Media.BaseCabinet);
                CopyVerified(Path.Combine(sourceRoot, "DATA1.HDR"), Path.Combine(cabinets, "data1.hdr"), Media.BaseHeader);
                var patch = Path.Combine(scratch, "patch.exe");
                CopyVerified(patchPath, patch, Media.PatchPackage);
                var wrapperCabinet = Path.Combine(scratch, "patch.cab");
                using (var input = File.OpenRead(patch))
                using (var output = File.Create(wrapperCabinet))
                {
                    input.Position = Media.PatchWrapperOffset;
                    var bytes = new byte[Media.PatchWrapperBytes];
                    input.ReadExactly(bytes);
                    output.Write(bytes);
                }
                VerifyFile(wrapperCabinet, Media.PatchWrapperCabinet);
                progress?.Invoke("Extracting original game data…", .15);
                var extractedBase = Path.Combine(scratch, "base");
                await RunAsync(extractor, ["-d", extractedBase, "x", Path.Combine(cabinets, "data1.cab")]);
                var wrapper = Path.Combine(scratch, "patch-wrapper");
                Directory.CreateDirectory(wrapper);
                await RunAsync(Path.Combine(Environment.SystemDirectory, "expand.exe"), ["-F:*", wrapperCabinet, wrapper]);
                var patchCabinet = Path.Combine(wrapper, "Disk1", "data1.cab");
                VerifyFile(patchCabinet, Media.PatchCabinet);
                VerifyFile(Path.Combine(wrapper, "Disk1", "data1.hdr"), Media.PatchHeader);
                progress?.Invoke("Extracting the supplied 1.2 patch…", .35);
                var extractedPatch = Path.Combine(scratch, "patch-files");
                await RunAsync(extractor, ["-d", extractedPatch, "x", patchCabinet]);
                var outputRoot = Path.Combine(scratch, "game");
                Directory.CreateDirectory(outputRoot);
                var sets = new[] { (extractedBase, Media.BaseFiles), (extractedPatch, Media.PatchFiles),
                    (sourceRoot, Media.MediaFiles), (extractedBase, Media.ProviderFiles) };
                var count = sets.Sum(s => s.Item2.Length);
                var done = 0;
                foreach (var (root, files) in sets)
                    foreach (var file in files)
                    {
                        progress?.Invoke("Installing " + file.Target, .45 + .45 * ++done / count);
                        CopyVerified(PackStorage.Resolve(root, file.Source), PackStorage.Resolve(outputRoot, file.Target), file.Sha256, file.Bytes);
                    }
                await VerifyExistingAsync(outputRoot);
                PackStorage.EnsureNoLinks(destination);
                Directory.Move(outputRoot, destination);
            });
            progress?.Invoke("Original MW3 1.2 files installed and verified. Native runtime preparation is separate.", 1);
        }
        finally
        {
            // Only our freshly generated scratch directory; never the selected source or destination.
            PackStorage.EnsureNoLinks(scratch);
            if (Directory.Exists(scratch))
            {
                foreach (var file in Directory.EnumerateFiles(scratch, "*", SearchOption.AllDirectories))
                {
                    PackStorage.EnsureNoLinks(file);
                    File.SetAttributes(file, File.GetAttributes(file) & ~FileAttributes.ReadOnly);
                }
                Directory.Delete(scratch, true);
            }
        }
    }

    public static void VerifyFile(string path, string expectedHash, long? expectedBytes = null)
    {
        PackStorage.EnsureNoLinks(path);
        if (!File.Exists(path)) throw new FileNotFoundException("Required installation file is missing: " + Path.GetFileName(path), path);
        using var input = File.OpenRead(path);
        if (expectedBytes.HasValue && input.Length != expectedBytes.Value ||
            !Convert.ToHexString(SHA256.HashData(input)).Equals(expectedHash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Unsupported or damaged installation file: " + Path.GetFileName(path) +
                ". This installer currently supports the verified U.S. retail disc and cumulative English 1.2 patch.");
    }

    private static void CopyVerified(string source, string destination, string hash, long? bytes = null)
    {
        PackStorage.EnsureNoLinks(source);
        PackStorage.EnsureNoLinks(destination);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        File.Copy(source, destination, true);
        File.SetAttributes(destination, File.GetAttributes(destination) & ~FileAttributes.ReadOnly);
        VerifyFile(destination, hash, bytes);
    }

    private static async Task<string> RunAsync(string executable, IEnumerable<string> arguments,
        string? isoPath = null)
    {
        var start = new ProcessStartInfo(executable) {
            UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true
        };
        foreach (var argument in arguments) start.ArgumentList.Add(argument);
        if (isoPath != null) start.Environment["MW3_INSTALL_ISO"] = isoPath;
        using var process = Process.Start(start) ?? throw new IOException("Could not start " + Path.GetFileName(executable));
        var stdout = process.StandardOutput.ReadToEndAsync();
        var stderr = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        var output = await stdout;
        var error = await stderr;
        if (process.ExitCode != 0)
            throw new IOException(Path.GetFileName(executable) + " failed (" + process.ExitCode + "): " + error + output);
        return output.Trim();
    }

    private static Task<string> DiskImageCommandAsync(string isoPath, string command)
    {
        var encoded = Convert.ToBase64String(Encoding.Unicode.GetBytes("$ErrorActionPreference='Stop'; " + command));
        return RunAsync(Path.Combine(Environment.SystemDirectory, @"WindowsPowerShell\v1.0\powershell.exe"),
            ["-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], Path.GetFullPath(isoPath));
    }

    public static async Task InstallIsoAsync(string isoPath, string patchPath, string destination,
        string extractorDirectory, Action<string, double>? progress = null)
        => await WithIsoAsync(isoPath, drive => InstallDirectoryAsync(drive, patchPath, destination, extractorDirectory, progress));

    public static string? FindProvider(string gameDirectory, string dataRoot)
    {
        return FindOriginalInput(Media.ProviderFiles.Single(p => Path.GetFileName(p.Target) == "MSVCRT.DLL"), gameDirectory, dataRoot);
    }

    private static string? FindOriginalInput(ContentFile pin, string gameDirectory, string dataRoot)
    {
        var name = Path.GetFileName(pin.Target);
        foreach (var path in new[] { PackStorage.Resolve(gameDirectory, pin.Target), Path.Combine(gameDirectory, name),
            PackStorage.Resolve(dataRoot, "original-inputs/" + pin.Sha256 + "/" + name) })
        {
            if (!File.Exists(path)) continue;
            try { VerifyFile(path, pin.Sha256, pin.Bytes); return Path.GetFullPath(path); }
            catch (InvalidDataException) { } // An unrelated modern CRT is not this required original input.
        }
        return null;
    }

    public static Dictionary<string, string>? FindSupportFiles(string gameDirectory, string dataRoot)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var pin in Media.ProviderFiles)
        {
            var path = FindOriginalInput(pin, gameDirectory, dataRoot);
            if (path == null) return null;
            result.Add(Path.GetFileName(pin.Target), path);
        }
        return result;
    }

    public const string RebasedCodecHash = "9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f";

    /// <summary>Prepare only the admitted original decoder in writable user storage.</summary>
    public static Dictionary<string, string> PrepareSupportFiles(string gameDirectory, string dataRoot)
    {
        var inputs = FindSupportFiles(gameDirectory, dataRoot)
            ?? throw new FileNotFoundException("Required original support files are missing. Run Set Up Game and select your MW3 ISO.");
        inputs["Ir50_32.base11000000.dll"] = StoreDerived(dataRoot, "Ir50_32.base11000000.dll",
            PeImageRelocator.Rebase(File.ReadAllBytes(inputs["Ir50_32.dll"]), 0x11000000), RebasedCodecHash);
        inputs["crt.bin"] = StoreDerived(dataRoot, "crt.bin", CrtSourcePack.Build(File.ReadAllBytes(inputs["MSVCRT.DLL"])), CrtSourcePack.Hash);
        return inputs;
    }

    private static string StoreDerived(string dataRoot, string name, byte[] bytes, string expectedHash)
    {
        if (!Convert.ToHexString(SHA256.HashData(bytes)).Equals(expectedHash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Generated original support resource failed its identity check: " + name);
        var output = PackStorage.Resolve(dataRoot, "original-inputs/" + expectedHash + "/" + name);
        Directory.CreateDirectory(Path.GetDirectoryName(output)!);
        bool valid = false;
        if (File.Exists(output))
            try { VerifyFile(output, expectedHash, bytes.Length); valid = true; }
            catch (InvalidDataException) { }
        if (!valid)
        {
            var temporary = output + ".preparing-" + Guid.NewGuid().ToString("N");
            try
            {
                using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write)) stream.Write(bytes);
                PackStorage.EnsureNoLinks(output);
                if (File.Exists(output)) File.Replace(temporary, output, output + ".unreadable-" + Guid.NewGuid().ToString("N"));
                else File.Move(temporary, output);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
        return output;
    }

    public static void BindSupportFiles(JsonObject profile, string gameDirectory, string dataRoot)
    {
        var native = profile["native"]!.AsObject();
        if (native["original_support_versions"] is not JsonArray versions || !versions.Any(v => v!.GetValue<int>() == 1))
            throw new InvalidDataException("This runtime cannot use installed original support files. Update the runtime.");
        var files = PrepareSupportFiles(gameDirectory, dataRoot);
        var environment = native["runtime_environment"]!.AsObject();
        environment["MW34_REQUIRE_USER_PROVIDERS"] = "1";
        environment["MW34_MFC42_IMAGE"] = files["MFC42.DLL"];
        environment["MW34_MSVCP50_IMAGE"] = files["MSVCP50.DLL"];
        environment["MW34_IV50_IMAGE"] = files["Ir50_32.base11000000.dll"];
        native["cinematic_codec_sha256"] = RebasedCodecHash;
        native["launch_inputs"]!["crt_provider"] = files["MSVCRT.DLL"];
        native["launch_inputs"]!["crt_pack"] = files["crt.bin"];
    }

    public static async Task ImportProviderIsoAsync(string isoPath, string dataRoot, string extractorDirectory,
        Action<string, double>? progress = null)
    {
        await WithIsoAsync(isoPath, async drive =>
        {
            var parent = Path.Combine(Path.GetFullPath(dataRoot), "original-inputs");
            PackStorage.EnsureNoLinks(parent);
            Directory.CreateDirectory(parent);
            var scratch = Path.Combine(parent, ".import-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(scratch);
            try
            {
                await Task.Run(async () =>
                {
                    progress?.Invoke("Checking original support files on your disc…", .05);
                    VerifyExtractor(extractorDirectory);
                    CopyVerified(Path.Combine(drive, "DATA1.CAB"), Path.Combine(scratch, "data1.cab"), Media.BaseCabinet);
                    CopyVerified(Path.Combine(drive, "DATA1.HDR"), Path.Combine(scratch, "data1.hdr"), Media.BaseHeader);
                    var extracted = Path.Combine(scratch, "extracted");
                    Directory.CreateDirectory(extracted);
                    foreach (var group in new[] { "Shared DLLs", "Codec DLLs" })
                        await RunAsync(Path.Combine(extractorDirectory, "unshield.exe"),
                            ["-g", group, "-d", extracted, "x", Path.Combine(scratch, "data1.cab")]);
                    // Verify the whole required set before publishing any new cached input.
                    foreach (var pin in Media.ProviderFiles)
                        VerifyFile(PackStorage.Resolve(extracted, pin.Source), pin.Sha256, pin.Bytes);
                    foreach (var pin in Media.ProviderFiles)
                    {
                        var name = Path.GetFileName(pin.Target);
                        var output = PackStorage.Resolve(parent, pin.Sha256 + "/" + name);
                        var staged = Path.Combine(scratch, name);
                        CopyVerified(PackStorage.Resolve(extracted, pin.Source), staged, pin.Sha256, pin.Bytes);
                        Directory.CreateDirectory(Path.GetDirectoryName(output)!);
                        if (File.Exists(output))
                        {
                            try { VerifyFile(output, pin.Sha256, pin.Bytes); }
                            catch (InvalidDataException)
                            { File.Replace(staged, output, output + ".unreadable-" + Guid.NewGuid().ToString("N")); }
                        }
                        else File.Move(staged, output);
                    }
                    PrepareSupportFiles(Path.Combine(scratch, "unused-game-root"), dataRoot);
                    progress?.Invoke("Original support files and movie decoder prepared. Your existing game folder was not changed.", 1);
                });
            }
            finally { PackStorage.DeleteOwnedTree(scratch); }
        });
    }

    private static async Task WithIsoAsync(string isoPath, Func<string, Task> action)
    {
        if (!File.Exists(isoPath)) throw new FileNotFoundException("Select an existing ISO image.", isoPath);
        // Paths travel through the environment, never through executable PowerShell text.
        var mountedHere = false;
        try
        {
            var state = await DiskImageCommandAsync(isoPath,
                "$i=Get-DiskImage -ImagePath $env:MW3_INSTALL_ISO; " +
                "@{attached=[bool]$i.Attached}|ConvertTo-Json -Compress");
            using var initial = JsonDocument.Parse(state);
            if (!initial.RootElement.GetProperty("attached").GetBoolean())
            {
                await DiskImageCommandAsync(isoPath, "Mount-DiskImage -ImagePath $env:MW3_INSTALL_ISO | Out-Null");
                mountedHere = true;
            }
            var volume = await DiskImageCommandAsync(isoPath,
                "$i=Get-DiskImage -ImagePath $env:MW3_INSTALL_ISO; " +
                "@{letter=($i|Get-Volume).DriveLetter;device=$i.DevicePath}|ConvertTo-Json -Compress");
            using var mounted = JsonDocument.Parse(volume);
            var driveLetter = mounted.RootElement.GetProperty("letter");
            var letter = driveLetter.ValueKind == JsonValueKind.String ? driveLetter.GetString() ?? "" : "";
            if (letter.Length != 1)
                letter = MountedIsoDrive(mounted.RootElement.GetProperty("device").GetString() ?? "");
            if (letter.Length != 1 || !char.IsAsciiLetter(letter[0]))
                throw new IOException("The ISO did not expose a single mounted data drive.");
            await action(letter + @":\");
        }
        finally
        {
            if (mountedHere)
                await DiskImageCommandAsync(isoPath, "Dismount-DiskImage -ImagePath $env:MW3_INSTALL_ISO | Out-Null");
        }
    }
}
